import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from pydantic import SecretStr
from sqlalchemy import select, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[4]
pytestmark = pytest.mark.integration


@pytest.fixture
def db(monkeypatch):
    from rolekai.persistence import new_engine
    from rolekai.workflows.tables import metadata

    source = os.environ.get("TEST_DATABASE_URL") or dotenv_values(ROOT / ".env").get(
        "TEST_DATABASE_URL"
    )
    assert source and make_url(source).database == "rolekai_foundation_test"
    url = SecretStr(
        make_url(source)
        .set(database="rolekai_ingestion_test")
        .render_as_string(hide_password=False)
    )
    monkeypatch.setenv("DATABASE_URL", url.get_secret_value())
    engine = new_engine(url.get_secret_value())
    command.upgrade(Config(str(ROOT / "apps/api/alembic.ini")), "head")
    with engine.begin() as c:
        assert c.scalar(text("SELECT current_database()")) == "rolekai_ingestion_test"
        actual = set(c.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public'")))
        assert actual <= set(metadata.tables) | {"alembic_version"}
        c.execute(
            text("TRUNCATE " + ",".join('"' + name + '"' for name in metadata.tables) + " CASCADE")
        )
    yield engine
    engine.dispose()


def raw(
    source="manual",
    *,
    ident=None,
    url="https://example.com/job",
    title="Engineer",
    company="Fixture",
    description="Original",
    extra=None,
):
    from rolekai.api.contracts import RawObservation

    return RawObservation(
        source=source,
        external_id=ident,
        source_url=url,
        retrieved_at=datetime.now(UTC),
        original_description_text=description,
        raw_payload={"title": title, "company_name": company, **(extra or {})},
    )


def persist(db, owner, observation):
    from rolekai.persistence import users
    from rolekai.workflows.imports import persist_observation
    from sqlalchemy.dialects.postgresql import insert

    with db.begin() as c:
        c.execute(insert(users).values(id=owner).on_conflict_do_nothing())
        return persist_observation(c, owner, observation, None, uuid4())


def test_exact_source_url_retry_and_cross_owner_identity(db):
    from rolekai.persistence import activity, jobs, observations

    owner, other = uuid4(), uuid4()
    one = raw("remotive", ident="101")
    first = persist(db, owner, one)
    assert first["outcome"] == "created"
    assert persist(db, owner, one)["outcome"] == "duplicate"
    assert persist(db, other, one)["job_id"] != first["job_id"]
    # Changed canonical URL still resolves through exact source identity.
    changed = raw("remotive", ident="101", url="https://example.com/moved", description="Changed")
    assert persist(db, owner, changed)["job_id"] == first["job_id"]
    with db.connect() as c:
        assert len(c.execute(jobs.select()).all()) == 2
        assert len(c.execute(observations.select()).all()) == 3
        assert len(c.execute(activity.select()).all()) == 3


def test_direct_source_conflicts_keep_originals_preference_and_manual_application(db):
    from rolekai.persistence import applications, jobs, observations, provenance

    owner = uuid4()
    first = persist(
        db,
        owner,
        raw("remotive", ident="101", title="Aggregate title", extra={"salary": "USD 100"}),
    )
    with db.begin() as c:
        c.execute(jobs.update().where(jobs.c.id == first["job_id"]).values(decision_status="saved"))
        c.execute(
            applications.insert().values(
                id=uuid4(), owner_id=owner, job_id=first["job_id"], status="applied"
            )
        )
    direct = raw(
        "greenhouse", ident="fixture:201", title="Direct title", description="Direct original"
    )
    assert persist(db, owner, direct)["job_id"] == first["job_id"]
    persist(
        db,
        owner,
        raw("remotive", ident="101", title="Later aggregate", description="New aggregate"),
    )
    with db.connect() as c:
        job = c.execute(jobs.select()).mappings().one()
        assert job["title_raw"] == "Direct title" and job["salary"] == "USD 100"
        assert job["decision_status"] == "saved"
        assert c.execute(applications.select()).one().status == "applied"
        assert len(c.execute(observations.select()).all()) == 3
        title_link = c.execute(
            select(provenance).where(provenance.c.field_name == "title_raw")
        ).one()
        assert title_link.provenance_type == "source"
        from rolekai.api.routes import summary

        assert summary(c, job)["preferred_source"] == "greenhouse"


def test_similar_distinct_jobs_are_not_merged_and_exact_identity_conflict_is_safe(db):
    from rolekai.connectors.base import ConnectorError
    from rolekai.persistence import jobs

    owner = uuid4()
    a = persist(db, owner, raw("remotive", ident="1", url="https://example.com/a"))
    b = persist(db, owner, raw("greenhouse", ident="fixture:2", url="https://example.com/b"))
    assert a["job_id"] != b["job_id"]
    with pytest.raises(ConnectorError) as error:
        persist(db, owner, raw("remotive", ident="1", url="https://example.com/b"))
    assert error.value.code == "IDENTITY_CONFLICT"
    with db.connect() as c:
        assert len(c.execute(jobs.select()).all()) == 2


def test_snapshot_event_failure_rolls_back_and_retry_creates_once(db):
    from rolekai.persistence import activity, jobs, observations
    from sqlalchemy.exc import DBAPIError

    owner = uuid4()
    with db.begin() as c:
        c.execute(
            text(
                "CREATE FUNCTION test_reject_ingest_event() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN RAISE EXCEPTION 'rejected'; END $$"
            )
        )
        c.execute(
            text(
                "CREATE TRIGGER test_reject_ingest_event BEFORE INSERT ON activity_event "
                "FOR EACH ROW EXECUTE FUNCTION test_reject_ingest_event()"
            )
        )
    try:
        with pytest.raises(DBAPIError):
            persist(db, owner, raw())
        with db.connect() as c:
            assert c.execute(jobs.select()).all() == c.execute(observations.select()).all() == []
    finally:
        with db.begin() as c:
            c.execute(text("DROP TRIGGER test_reject_ingest_event ON activity_event"))
            c.execute(text("DROP FUNCTION test_reject_ingest_event()"))
    assert persist(db, owner, raw())["outcome"] == "created"
    assert persist(db, owner, raw())["outcome"] == "duplicate"
    with db.connect() as c:
        assert len(c.execute(activity.select()).all()) == 1


def client_for(db, owner):
    from fastapi.testclient import TestClient
    from rolekai.main import create_app
    from rolekai.settings import Settings

    return TestClient(
        create_app(
            settings=Settings(
                database_url=SecretStr(
                    db.url.set(drivername="postgresql").render_as_string(hide_password=False)
                ),
                current_owner_id=owner,
                api_access_token="test-local",
                greenhouse_boards=["fixture"],
                _env_file=None,
            )
        ),
        headers={"Authorization": "Bearer test-local"},
    )


def accept(db, owner, source="manual", key="same", data=None):
    from rolekai.api.contracts import ImportRequest
    from rolekai.workflows.imports import accept_import

    return accept_import(
        db,
        owner,
        source,
        ImportRequest(**(data or {"url": "https://example.com/job", "text": "Original"})),
        key,
        uuid4(),
        known_boards=["fixture"],
    )


def test_idempotent_api_same_intent_and_owner_scoped_run_status(db):
    from rolekai.workflows.worker import Worker

    owner = uuid4()
    with client_for(db, owner) as client:
        headers = {"Idempotency-Key": "stable"}
        body = {"url": "https://example.com/job", "text": "Original"}
        first = client.post("/api/v1/imports/url", headers=headers, json=body)
        repeat = client.post("/api/v1/imports/url", headers=headers, json=body)
        assert first.status_code == repeat.status_code == 202
        assert first.json()["run_id"] == repeat.json()["run_id"]
        changed = client.post(
            "/api/v1/imports/url", headers=headers, json={**body, "text": "Changed"}
        )
        assert changed.status_code == 409
        assert (
            client.post(
                "/api/v1/imports/url", headers=headers, json={"url": "http://169.254.169.254/"}
            ).status_code
            == 422
        )
        assert Worker(db).run_once() is True
        run = client.get("/api/v1/import-runs/" + first.json()["run_id"])
        assert run.json()["status"] == "completed" and run.json()["created"] == 1
        assert run.json()["failed"] == 0
    with client_for(db, uuid4()) as client:
        assert client.get("/api/v1/import-runs/" + first.json()["run_id"]).status_code == 404


def test_two_claimers_retry_after_and_crash_fencing(db):
    from concurrent.futures import ThreadPoolExecutor

    from rolekai.workflows.tables import background_jobs
    from rolekai.workflows.worker import Worker

    owner = uuid4()
    accept(db, owner)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims = list(pool.map(lambda _: Worker(db).claim(), range(2)))
    assert sum(c is not None for c in claims) == 1
    old = next(c for c in claims if c is not None)
    with db.begin() as c:
        c.execute(
            background_jobs.update().values(lease_until=datetime.now(UTC) - timedelta(seconds=1))
        )
    worker = Worker(db)
    new = worker.claim()
    assert new["attempts"] == 2 and new["claim_token"] != old["claim_token"]
    assert worker.process(old) is False
    assert worker.process(new) is True


def test_transient_retry_honors_delay_and_permanent_failure_stops(db):
    from rolekai.connectors.base import ConnectorError
    from rolekai.workflows.tables import background_jobs, import_runs
    from rolekai.workflows.worker import Worker

    class Broken:
        errors = []

        def discover(self, request):
            raise ConnectorError("SOURCE_RATE_LIMIT", transient=True, retry_after=300)

    owner = uuid4()
    accept(db, owner)
    worker = Worker(db, connector_factory=lambda *a: Broken())
    assert worker.run_once()
    with db.connect() as c:
        queued = c.execute(background_jobs.select()).mappings().one()
        assert queued["status"] == "queued" and queued["run_after"] > datetime.now(UTC) + timedelta(
            seconds=290
        )

    class Permanent(Broken):
        def discover(self, request):
            raise ConnectorError("SOURCE_AUTH")

    with db.begin() as c:
        c.execute(
            background_jobs.update().values(run_after=datetime.now(UTC) - timedelta(seconds=1))
        )
    assert Worker(db, connector_factory=lambda *a: Permanent()).run_once()
    with db.connect() as c:
        assert c.execute(background_jobs.select()).one().status == "failed"
        assert c.execute(import_runs.select()).one().status == "failed"


def test_remotive_budget_shared_across_owners_and_partial_source_failure_isolated(db):
    from rolekai.connectors.base import ConnectorError
    from rolekai.workflows.imports import reserve_remotive

    reserve_remotive(db)
    with pytest.raises(ConnectorError) as error:
        reserve_remotive(db)
    assert error.value.transient and error.value.retry_after >= 21590
    from rolekai.workflows.worker import Worker

    class Partial:
        errors = [ConnectorError("SOURCE_SCHEMA")]

        def discover(self, request):
            return [raw("greenhouse", ident="fixture:1")]

    owner = uuid4()
    accepted = accept(db, owner, "greenhouse", "board", {"board": "fixture"})
    assert Worker(db, connector_factory=lambda *a: Partial()).run_once()
    from rolekai.workflows.imports import get_run

    result = get_run(db, owner, accepted.run_id)
    assert result["status"] == "completed" and result["created"] == 1 and result["failed"] == 1
    assert result["errors"][0]["code"] == "SOURCE_SCHEMA"


def test_ingestion_migration_roundtrip_preserves_domain_rows(db, monkeypatch):
    from rolekai.persistence import jobs

    owner = uuid4()
    first = persist(db, owner, raw())
    config = Config(str(ROOT / "apps/api/alembic.ini"))
    command.downgrade(config, "0002_domains")
    with db.connect() as c:
        assert c.execute(select(jobs.c.id)).scalar() == first["job_id"]
    command.upgrade(config, "head")
    assert persist(db, owner, raw())["outcome"] == "duplicate"


def test_exhausted_crashed_claim_and_failure_do_not_block_other_source(db):
    from rolekai.workflows.tables import background_jobs, import_runs
    from rolekai.workflows.worker import Worker

    owner = uuid4()
    first = accept(db, owner, "greenhouse", "board", {"board": "fixture"})
    second = accept(db, owner, key="next", data={"url": "https://example.com/next", "text": "Next"})
    with db.begin() as c:
        c.execute(
            background_jobs.update()
            .where(background_jobs.c.run_id == first.run_id)
            .values(
                status="running",
                attempts=3,
                lease_until=datetime.now(UTC) - timedelta(seconds=1),
                claim_token=uuid4(),
            )
        )
    assert Worker(db).run_once()
    with db.connect() as c:
        assert (
            c.execute(select(import_runs.c.status).where(import_runs.c.id == first.run_id)).scalar()
            == "failed"
        )
        assert (
            c.execute(
                select(import_runs.c.status).where(import_runs.c.id == second.run_id)
            ).scalar()
            == "completed"
        )


def test_worker_trace_excludes_raw_body_url_tokens_and_exception_text(db):
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from rolekai.workflows.worker import Worker

    owner = uuid4()
    accept(db, owner, data={"url": "https://example.com/job", "text": "PRIVATE_BODY"})
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    assert Worker(db, tracer_provider=provider).run_once()
    captured = str(
        [(span.name, dict(span.attributes), span.events) for span in exporter.get_finished_spans()]
    )
    assert (
        "PRIVATE_BODY" not in captured
        and "example.com" not in captured
        and "password" not in captured
    )
    assert "request_id" in captured and "workflow_run_id" in captured
    provider.shutdown()


def test_partial_transaction_failure_retry_keeps_one_receipt_job_and_event_per_item(db):
    from rolekai.persistence import activity, jobs
    from rolekai.workflows.imports import get_run
    from rolekai.workflows.tables import background_jobs
    from rolekai.workflows.worker import Worker

    class Batch:
        errors = []

        def discover(self, request):
            return [
                raw(url="https://example.com/first", title="First"),
                raw(url="https://example.com/second", title="Second"),
            ]

    owner = uuid4()
    accepted = accept(db, owner)
    with db.begin() as c:
        c.execute(
            text(
                "CREATE FUNCTION test_partial_ingest() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN IF (SELECT title_raw FROM job WHERE id=NEW.subject_id) = 'Second' THEN "
                "RAISE EXCEPTION 'reject second event'; END IF; RETURN NEW; END $$"
            )
        )
        c.execute(
            text(
                "CREATE TRIGGER test_partial_ingest BEFORE INSERT ON activity_event "
                "FOR EACH ROW EXECUTE FUNCTION test_partial_ingest()"
            )
        )
    try:
        assert Worker(db, connector_factory=lambda *a: Batch()).run_once()
        assert get_run(db, owner, accepted.run_id)["status"] == "queued"
        with db.connect() as c:
            assert len(c.execute(jobs.select()).all()) == 1
    finally:
        with db.begin() as c:
            c.execute(text("DROP TRIGGER test_partial_ingest ON activity_event"))
            c.execute(text("DROP FUNCTION test_partial_ingest()"))
    with db.begin() as c:
        c.execute(
            background_jobs.update().values(run_after=datetime.now(UTC) - timedelta(seconds=1))
        )
    assert Worker(db, connector_factory=lambda *a: Batch()).run_once()
    result = get_run(db, owner, accepted.run_id)
    assert (
        result["status"] == "completed" and result["created"] == 2 and len(result["job_ids"]) == 2
    )
    with db.connect() as c:
        assert len(c.execute(jobs.select()).all()) == 2
        assert len(c.execute(activity.select()).all()) == 2


def test_parallel_accept_same_key_enqueues_only_one_attempt(db):
    from concurrent.futures import ThreadPoolExecutor

    from rolekai.workflows.tables import background_jobs, import_runs

    owner = uuid4()
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: accept(db, owner), range(2)))
    assert responses[0].run_id == responses[1].run_id
    with db.connect() as c:
        assert len(c.execute(import_runs.select()).all()) == 1
        assert len(c.execute(background_jobs.select()).all()) == 1


def test_provenance_paths_resolve_to_original_fields(db):
    from rolekai.persistence import provenance

    owner = uuid4()
    payload = {"salary": "USD 100", "publication_date": "2026-10-01T12:00:00Z"}
    item = raw("remotive", ident="101", extra=payload)
    persist(db, owner, item)
    expected = {
        "title_raw": "title",
        "title_normalized": "title",
        "company_display_name": "company_name",
        "company_key": "company_name",
        "salary": "salary",
        "posted_at": "publication_date",
    }
    with db.connect() as c:
        rows = c.execute(provenance.select()).mappings().all()
        assert {r["field_name"]: r["payload_path"] for r in rows} == expected
        assert all(r["payload_path"] in item.raw_payload for r in rows)


def test_source_refresh_preserves_human_field_correction_and_evidence(db):
    from rolekai.persistence import jobs, observations, provenance

    owner = uuid4()
    first = persist(db, owner, raw("remotive", ident="101"))
    with db.begin() as c:
        c.execute(jobs.update().where(jobs.c.id == first["job_id"]).values(salary="Human value"))
        observation = c.scalar(select(observations.c.id))
        correction = uuid4()
        c.execute(
            provenance.insert().values(
                id=correction,
                owner_id=owner,
                job_id=first["job_id"],
                observation_id=observation,
                field_name="salary",
                provenance_type="human",
                citation="Verified manually",
            )
        )
    refresh = persist(
        db, owner, raw("greenhouse", ident="fixture:201", extra={"salary": "Source value"})
    )
    assert refresh["job_id"] == first["job_id"] and refresh["needs_review"]
    with db.connect() as c:
        assert c.scalar(select(jobs.c.salary)) == "Human value"
        row = c.execute(select(provenance).where(provenance.c.field_name == "salary")).one()
        assert row.id == correction and row.provenance_type == "human"
        assert len(c.execute(observations.select()).all()) == 2
