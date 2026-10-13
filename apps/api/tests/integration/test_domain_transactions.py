import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

ROOT = Path(__file__).resolve().parents[4]
pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def domain_url():
    from sqlalchemy.engine import make_url

    source = os.environ.get("TEST_DATABASE_URL") or dotenv_values(ROOT / ".env").get(
        "TEST_DATABASE_URL"
    )
    assert source and make_url(source).database == "rolekai_foundation_test"
    # A dedicated database, distinct from the baseline-only Foundation test database.
    return SecretStr(
        make_url(source).set(database="rolekai_domain_test").render_as_string(hide_password=False)
    )


@pytest.fixture
def db(domain_url, monkeypatch):
    from rolekai.persistence import metadata, new_engine

    monkeypatch.setenv("DATABASE_URL", domain_url.get_secret_value())
    engine = new_engine(domain_url.get_secret_value())
    config = Config(str(ROOT / "apps/api/alembic.ini"))
    command.upgrade(config, "0002_domains")
    # Only the exact dedicated test DB and known schema may be cleared.
    with engine.begin() as connection:
        assert connection.scalar(text("SELECT current_database()")) == "rolekai_domain_test"
        actual = set(
            connection.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        )
        assert actual <= set(metadata.tables) | {"alembic_version"}
        connection.execute(
            text("TRUNCATE " + ", ".join('"' + t + '"' for t in metadata.tables) + " CASCADE")
        )
    yield engine
    engine.dispose()


@pytest.fixture
def owners(db):
    from rolekai.persistence import users

    ids = (uuid4(), uuid4())
    with db.begin() as c:
        c.execute(users.insert(), [{"id": x} for x in ids])
    return ids


def seed_job(db, owner, *, decision="inbox", url="https://example.com/job"):
    from rolekai.persistence import jobs

    job_id = uuid4()
    with db.begin() as c:
        c.execute(
            jobs.insert().values(
                id=job_id,
                owner_id=owner,
                title_raw="Engineer",
                canonical_url=url,
                decision_status=decision,
            )
        )
    return job_id


def test_canonical_and_source_identity_are_owner_scoped(db, owners):
    from rolekai.persistence import jobs, observations

    left, right = owners
    a, b = seed_job(db, left), seed_job(db, right)
    with pytest.raises(IntegrityError), db.begin() as c:
        c.execute(
            jobs.insert().values(
                id=uuid4(),
                owner_id=left,
                title_raw="Duplicate",
                canonical_url="https://example.com/job",
            )
        )
    for owner, job in ((left, a), (right, b)):
        with db.begin() as c:
            c.execute(
                observations.insert().values(
                    id=uuid4(),
                    owner_id=owner,
                    job_id=job,
                    source_type="remotive",
                    external_id="42",
                    content_hash="v1",
                    parser_version="v1",
                    retrieved_at=datetime.now(UTC),
                    original_description_text="Original",
                )
            )
    with pytest.raises(IntegrityError), db.begin() as c:
        c.execute(
            observations.insert().values(
                id=uuid4(),
                owner_id=left,
                job_id=b,
                source_type="manual",
                content_hash="foreign",
                parser_version="v1",
                retrieved_at=datetime.now(UTC),
            )
        )
    with db.connect() as c:
        assert (
            c.execute(observations.select().where(observations.c.owner_id == left)).one().job_id
            == a
        )


def test_database_rejects_observation_and_activity_mutation(db, owners):
    from rolekai.persistence import activity, observations

    owner = owners[0]
    job = seed_job(db, owner)
    obs, event = uuid4(), uuid4()
    with db.begin() as c:
        c.execute(
            observations.insert().values(
                id=obs,
                owner_id=owner,
                job_id=job,
                source_type="manual",
                content_hash="v1",
                parser_version="v1",
                retrieved_at=datetime.now(UTC),
            )
        )
        c.execute(
            activity.insert().values(
                id=event,
                owner_id=owner,
                subject_type="job",
                subject_id=job,
                event_type="job.created",
                actor_type="system",
                correlation_id=uuid4(),
            )
        )
    for table, row_id in ((observations, obs), (activity, event)):
        for mutation in (
            table.delete().where(table.c.id == row_id),
            table.update().where(table.c.id == row_id).values(owner_id=owner),
        ):
            with pytest.raises(DBAPIError), db.begin() as c:
                c.execute(mutation)


def test_domain_migration_roundtrip_preserves_foundation_baseline(db):
    config = Config(str(ROOT / "apps/api/alembic.ini"))
    command.downgrade(config, "0001_foundation")
    with db.connect() as c:
        assert set(
            c.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public'"))
        ) == {"alembic_version"}
    command.upgrade(config, "0002_domains")
    with db.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == "0002_domains"


def client_for(db, owner):
    from fastapi.testclient import TestClient
    from rolekai.main import create_app
    from rolekai.settings import Settings

    settings = Settings(
        database_url=SecretStr(
            db.url.set(drivername="postgresql").render_as_string(hide_password=False)
        ),
        current_owner_id=owner,
        api_access_token="test-local-token",
        _env_file=None,
    )
    return TestClient(
        create_app(settings=settings), headers={"Authorization": "Bearer test-local-token"}
    )


def test_save_does_not_create_application_and_repeated_save_has_one_event(db, owners):
    from rolekai.persistence import activity, applications, jobs

    owner = owners[0]
    job = seed_job(db, owner)
    with client_for(db, owner) as client:
        for _ in range(2):
            response = client.patch(
                f"/api/v1/jobs/{job}/decision", json={"decision_status": "saved"}
            )
            assert response.status_code == 200
    with db.connect() as c:
        assert c.execute(jobs.select()).one().decision_status == "saved"
        assert c.execute(applications.select()).all() == []
        assert len(c.execute(activity.select()).all()) == 1


def test_application_requires_saved_confirmed_owned_job_and_duplicate_is_409(db, owners):
    owner, foreign = owners
    unsaved, saved, other = (
        seed_job(db, owner, url="https://example.com/a"),
        seed_job(db, owner, decision="saved", url="https://example.com/b"),
        seed_job(db, foreign, decision="saved"),
    )
    with client_for(db, owner) as client:
        assert (
            client.post(
                f"/api/v1/jobs/{unsaved}/applications", json={"confirmed": True}
            ).status_code
            == 409
        )
        assert (
            client.post(f"/api/v1/jobs/{saved}/applications", json={"confirmed": False}).status_code
            == 409
        )
        assert (
            client.post(f"/api/v1/jobs/{other}/applications", json={"confirmed": True}).status_code
            == 404
        )
        assert (
            client.post(f"/api/v1/jobs/{saved}/applications", json={"confirmed": True}).status_code
            == 201
        )
        assert (
            client.post(f"/api/v1/jobs/{saved}/applications", json={"confirmed": True}).status_code
            == 409
        )


def test_invalid_or_unconfirmed_transition_has_no_success_event(db, owners):
    from rolekai.persistence import activity

    owner = owners[0]
    job = seed_job(db, owner, decision="saved")
    with client_for(db, owner) as client:
        response = client.post(f"/api/v1/jobs/{job}/applications", json={"confirmed": True})
        app_id = response.json()["id"]
        assert (
            client.patch(f"/api/v1/applications/{app_id}", json={"status": "applied"}).status_code
            == 409
        )
        assert (
            client.patch(
                f"/api/v1/applications/{app_id}", json={"status": "offer", "confirmed": True}
            ).status_code
            == 409
        )
        assert (
            client.patch(
                f"/api/v1/applications/{app_id}", json={"status": "applied", "confirmed": True}
            ).status_code
            == 200
        )
    with db.connect() as c:
        assert len(c.execute(activity.select()).all()) == 2


def test_failed_activity_insert_rolls_back_application_and_decision(db, owners):
    from rolekai.persistence import activity, applications, jobs

    owner = owners[0]
    job = seed_job(db, owner, decision="saved")
    with db.begin() as c:
        c.execute(
            text(
                "CREATE FUNCTION test_reject_activity() RETURNS trigger LANGUAGE plpgsql AS $$ "
                "BEGIN RAISE EXCEPTION 'test event rejection'; END $$"
            )
        )
        c.execute(
            text(
                "CREATE TRIGGER test_reject_activity BEFORE INSERT ON activity_event "
                "FOR EACH ROW EXECUTE FUNCTION test_reject_activity()"
            )
        )
    try:
        with client_for(db, owner) as client:
            assert (
                client.post(
                    f"/api/v1/jobs/{job}/applications", json={"confirmed": True}
                ).status_code
                == 503
            )
            assert (
                client.patch(
                    f"/api/v1/jobs/{job}/decision", json={"decision_status": "dismissed"}
                ).status_code
                == 503
            )
        with db.connect() as c:
            assert c.execute(applications.select()).all() == []
            assert c.execute(activity.select()).all() == []
            assert c.execute(jobs.select()).one().decision_status == "saved"
    finally:
        with db.begin() as c:
            c.execute(text("DROP TRIGGER test_reject_activity ON activity_event"))
            c.execute(text("DROP FUNCTION test_reject_activity()"))


def test_profile_and_evidence_are_owner_scoped_and_audited(db, owners):
    from rolekai.persistence import activity

    with client_for(db, owners[0]) as client:
        assert (
            client.put(
                "/api/v1/profile/search",
                json={"titles": ["AI Engineer"], "technologies": [{"value": "Python"}]},
            ).status_code
            == 200
        )
        evidence = client.post(
            "/api/v1/profile/evidence",
            json={"text": "Built systems", "source": "Portfolio", "evidence_date": "2026-01-01"},
        )
        assert evidence.status_code == 201
        assert client.get("/api/v1/profile/evidence").json()["items"][0]["text"] == "Built systems"
    with client_for(db, owners[1]) as client:
        assert client.get("/api/v1/profile/evidence").json()["items"] == []
        assert client.get("/api/v1/profile/search").status_code == 404
    with db.connect() as c:
        assert len(c.execute(activity.select()).all()) == 2


def test_protected_reads_pagination_validation_and_owner_spoofing(db, owners):
    left, right = owners
    a = seed_job(db, left)
    seed_job(db, left, url="https://example.com/two")
    b = seed_job(db, right)
    with client_for(db, left) as client:
        page = client.get("/api/v1/jobs?limit=1", headers={"X-Owner-Id": str(right)})
        assert page.status_code == 200
        assert len(page.json()["items"]) == 1 and page.json()["next_cursor"]
        second = client.get(
            "/api/v1/jobs", params={"limit": 1, "cursor": page.json()["next_cursor"]}
        )
        assert len(second.json()["items"]) == 1
        assert second.json()["items"][0]["id"] != page.json()["items"][0]["id"]
        assert str(b) not in [row["id"] for row in page.json()["items"] + second.json()["items"]]
        assert client.get(f"/api/v1/jobs/{b}").status_code == 404
        assert (
            client.patch(
                f"/api/v1/jobs/{b}/decision", json={"decision_status": "saved"}
            ).status_code
            == 404
        )
        assert (
            client.get("/api/v1/jobs", headers={"Authorization": "Bearer wrong"}).status_code == 401
        )
        for query in ("?limit=101", "?limit=0", "?cursor=PRIVATE_CONTENT"):
            response = client.get("/api/v1/jobs" + query)
            assert response.status_code == 422
            assert "PRIVATE_CONTENT" not in response.text
            assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
        response = client.post("/api/v1/profile/evidence", json={"text": "PRIVATE_CONTENT"})
        assert response.status_code == 422 and "PRIVATE_CONTENT" not in response.text
        assert (
            client.patch(
                f"/api/v1/jobs/{a}/decision",
                json={"decision_status": "saved", "owner_id": str(right)},
            ).status_code
            == 422
        )


def test_parallel_duplicate_application_creates_one_application_and_event(db, owners):
    from concurrent.futures import ThreadPoolExecutor

    from rolekai.api.errors import DomainError
    from rolekai.applications.models import ApplicationCreate
    from rolekai.applications.service import create_application
    from rolekai.persistence import activity, applications

    owner = owners[0]
    job = seed_job(db, owner, decision="saved")

    def create(_):
        try:
            create_application(db, owner, job, ApplicationCreate(confirmed=True), uuid4())
            return 201
        except DomainError as exc:
            return exc.status

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(create, range(2))) == [201, 409]
    with db.connect() as c:
        assert len(c.execute(applications.select()).all()) == 1
        assert len(c.execute(activity.select()).all()) == 1


def test_job_detail_preserves_observations_provenance_and_versioned_evaluation_items(db, owners):
    from rolekai.persistence import (
        evaluation_items,
        evaluation_spans,
        evaluations,
        observations,
        provenance,
        requirements,
    )

    owner = owners[0]
    job = seed_job(db, owner)
    obs, evaluation, requirement, item = (uuid4() for _ in range(4))
    with db.begin() as c:
        c.execute(
            observations.insert().values(
                id=obs,
                owner_id=owner,
                job_id=job,
                source_type="manual",
                content_hash="v1",
                parser_version="v1",
                retrieved_at=datetime.now(UTC),
                original_description_text="Python required",
            )
        )
        c.execute(
            provenance.insert().values(
                id=uuid4(),
                owner_id=owner,
                job_id=job,
                observation_id=obs,
                field_name="title_raw",
                citation="Engineer",
                provenance_type="source",
            )
        )
        c.execute(
            evaluations.insert().values(
                id=evaluation,
                owner_id=owner,
                job_id=job,
                job_snapshot_hash="v1",
                profile_snapshot_hash="p1",
                prompt_version="v1",
                status="needs_review",
            )
        )
        c.execute(
            requirements.insert().values(
                id=requirement, owner_id=owner, job_id=job, text="Python", priority="preferred"
            )
        )
        c.execute(
            evaluation_items.insert().values(
                id=item,
                owner_id=owner,
                job_id=job,
                evaluation_id=evaluation,
                requirement_id=requirement,
                classification="skill",
                priority="preferred",
                result="unknown",
                reason="No profile evidence",
            )
        )
        c.execute(
            evaluation_spans.insert().values(
                id=uuid4(),
                owner_id=owner,
                job_id=job,
                item_id=item,
                observation_id=obs,
                quote="Python required",
            )
        )
    with client_for(db, owner) as client:
        detail = client.get(f"/api/v1/jobs/{job}").json()
        assert detail["observations"][0]["original_description_text"] == "Python required"
        assert detail["provenance"][0]["observation_id"] == str(obs)
        assert (
            detail["evaluations"][0]["requirements"][0]["evidence"][0]["quote"] == "Python required"
        )
        assert detail["application"] is None
        result = client.get(f"/api/v1/evaluations/{evaluation}").json()
        assert result["requirements"][0]["result"] == "unknown"
    with client_for(db, owners[1]) as client:
        assert client.get(f"/api/v1/evaluations/{evaluation}").status_code == 404


def test_activity_timeline_cursor_orders_time_then_uuid_without_skipping_ties(db, owners):
    from uuid import UUID

    from rolekai.persistence import activity

    owner = owners[0]
    job = seed_job(db, owner)
    events = [
        (UUID(int=1), datetime(2026, 1, 1, 9, tzinfo=UTC)),
        (UUID(int=2), datetime(2026, 1, 1, 11, tzinfo=UTC)),
        (UUID(int=3), datetime(2026, 1, 1, 10, tzinfo=UTC)),
        (UUID(int=4), datetime(2026, 1, 1, 11, tzinfo=UTC)),
    ]
    with db.begin() as c:
        for ident, timestamp in events:
            c.execute(
                activity.insert().values(
                    id=ident,
                    owner_id=owner,
                    subject_type="job",
                    subject_id=job,
                    event_type="job.created",
                    actor_type="system",
                    correlation_id=uuid4(),
                    occurred_at=timestamp,
                )
            )
    with client_for(db, owner) as client:
        cursor, seen = None, []
        for _ in range(4):
            params = {"limit": 1}
            if cursor:
                params["cursor"] = cursor
            response = client.get("/api/v1/activity", params=params)
            assert response.status_code == 200
            seen.extend(row["id"] for row in response.json()["items"])
            cursor = response.json()["next_cursor"]
        assert seen == [str(events[i][0]) for i in (3, 1, 2, 0)]
        assert cursor is None


def test_decision_reason_is_retained_in_its_atomic_activity(db, owners):
    owner = owners[0]
    job = seed_job(db, owner)
    with client_for(db, owner) as client:
        assert (
            client.patch(
                f"/api/v1/jobs/{job}/decision",
                json={"decision_status": "dismissed", "reason": "Requires relocation"},
            ).status_code
            == 200
        )
        events = client.get("/api/v1/activity").json()["items"]
        assert len(events) == 1
        assert events[0]["metadata_json"]["reason"] == "Requires relocation"


def test_decision_response_preserves_source_and_latest_evaluation(db, owners):
    from rolekai.persistence import evaluations, observations

    owner = owners[0]
    job = seed_job(db, owner)
    evaluation = uuid4()
    with db.begin() as c:
        c.execute(
            observations.insert().values(
                id=uuid4(),
                owner_id=owner,
                job_id=job,
                source_type="remotive",
                content_hash="v1",
                parser_version="v1",
                retrieved_at=datetime.now(UTC),
            )
        )
        c.execute(
            evaluations.insert().values(
                id=evaluation,
                owner_id=owner,
                job_id=job,
                job_snapshot_hash="v1",
                profile_snapshot_hash="v1",
                prompt_version="v1",
            )
        )
    with client_for(db, owner) as client:
        result = client.patch(f"/api/v1/jobs/{job}/decision", json={"decision_status": "saved"})
        assert result.status_code == 200
        assert result.json()["preferred_source"] == "remotive"
        assert result.json()["latest_evaluation"]["id"] == str(evaluation)


def test_jobs_posted_date_filter_keeps_unknown_dates_unknown(db, owners):
    from rolekai.persistence import jobs

    owner = owners[0]
    unknown = seed_job(db, owner)
    dated = seed_job(db, owner, url="https://example.com/dated")
    with db.begin() as c:
        c.execute(
            jobs.update()
            .where(jobs.c.id == dated)
            .values(posted_at=datetime(2026, 5, 1, tzinfo=UTC))
        )
    with client_for(db, owner) as client:
        result = client.get("/api/v1/jobs", params={"posted_after": "2026-04-01T00:00:00Z"})
        assert result.status_code == 200
        assert [row["id"] for row in result.json()["items"]] == [str(dated)]
        assert client.get(f"/api/v1/jobs/{unknown}").json()["posted_at"] is None
