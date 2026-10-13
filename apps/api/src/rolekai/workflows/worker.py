"""Explicit PostgreSQL worker: fenced leases, bounded attempts, no scheduler."""

import random
from datetime import timedelta
from uuid import uuid4

from opentelemetry.trace import Status, StatusCode
from pydantic import ValidationError
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from rolekai.api.contracts import DiscoverRequest, RawObservation, SourceReference
from rolekai.connectors.base import ConnectorError
from rolekai.connectors.greenhouse import Greenhouse
from rolekai.connectors.manual_url import ManualURL, SafeFetcher
from rolekai.connectors.remotive import Remotive
from rolekai.domain import utcnow
from rolekai.settings import Settings
from rolekai.telemetry import local_tracer_provider
from rolekai.workflows.imports import (
    digest,
    observation_key,
    persist_observation,
    reserve_remotive,
)
from rolekai.workflows.tables import background_jobs, import_items, import_runs

LEASE_SECONDS = 120


class LostClaim(Exception):
    pass


class Worker:
    def __init__(self, engine, *, connector_factory=None, settings=None, tracer_provider=None):
        self.engine = engine
        self.settings = settings or Settings(
            database_url=engine.url.set(drivername="postgresql").render_as_string(
                hide_password=False
            )
        )
        self.connector_factory = connector_factory or self.connector
        self.provider = tracer_provider or local_tracer_provider()
        self.tracer = self.provider.get_tracer("rolekai.ingestion", "0.1.0")

    def connector(self, source, data, owner):
        if source == "manual":
            hosts = self.settings.manual_fetch_hosts
            fetcher = SafeFetcher(allowed_hosts=hosts) if hosts else None
            return ManualURL(fetcher)
        if source == "greenhouse":
            return Greenhouse(data["board"], known_boards=self.settings.greenhouse_boards)
        return Remotive(
            reserve=lambda: reserve_remotive(
                self.engine, queries_per_day=self.settings.remotive_queries_per_day
            )
        )

    def claim(self):
        now = utcnow()
        with self.engine.begin() as c:
            expired = (
                c.execute(
                    select(background_jobs)
                    .where(
                        background_jobs.c.status == "running",
                        background_jobs.c.lease_until <= now,
                        background_jobs.c.attempts >= background_jobs.c.max_attempts,
                    )
                    .with_for_update(skip_locked=True)
                )
                .mappings()
                .all()
            )
            for row in expired:
                self.fail(c, row, ConnectorError("ATTEMPTS_EXHAUSTED"), now)
            query = (
                select(background_jobs)
                .where(
                    background_jobs.c.attempts < background_jobs.c.max_attempts,
                    or_(
                        and_(
                            background_jobs.c.status == "queued", background_jobs.c.run_after <= now
                        ),
                        and_(
                            background_jobs.c.status == "running",
                            background_jobs.c.lease_until <= now,
                        ),
                    ),
                )
                .order_by(background_jobs.c.run_after, background_jobs.c.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            row = c.execute(query).mappings().first()
            if row is None:
                return None
            token = uuid4()
            claimed = (
                c.execute(
                    background_jobs.update()
                    .where(background_jobs.c.id == row["id"])
                    .values(
                        status="running",
                        attempts=row["attempts"] + 1,
                        claim_token=token,
                        lease_until=now + timedelta(seconds=LEASE_SECONDS),
                    )
                    .returning(background_jobs)
                )
                .mappings()
                .one()
            )
            c.execute(
                import_runs.update()
                .where(import_runs.c.id == row["run_id"], import_runs.c.owner_id == row["owner_id"])
                .values(status="running")
            )
            return dict(claimed)

    def fenced(self, c, claim):
        row = (
            c.execute(
                select(background_jobs)
                .where(
                    background_jobs.c.id == claim["id"],
                    background_jobs.c.owner_id == claim["owner_id"],
                    background_jobs.c.claim_token == claim["claim_token"],
                    background_jobs.c.status == "running",
                    background_jobs.c.lease_until > utcnow(),
                )
                .with_for_update()
            )
            .mappings()
            .first()
        )
        if row is None:
            raise LostClaim()
        return row

    def fail(self, c, claim, error, now):
        retry = error.transient and claim["attempts"] < claim["max_attempts"]
        delay = max(
            min(3600, 30 * 2 ** max(0, claim["attempts"] - 1)) + random.randint(0, 10),
            error.retry_after,
        )
        c.execute(
            background_jobs.update()
            .where(background_jobs.c.id == claim["id"])
            .values(
                status="queued" if retry else "failed",
                run_after=now + timedelta(seconds=delay),
                claim_token=None,
                lease_until=None,
                last_error=error.code,
            )
        )
        run = (
            c.execute(
                select(import_runs).where(
                    import_runs.c.id == claim["run_id"], import_runs.c.owner_id == claim["owner_id"]
                )
            )
            .mappings()
            .one()
        )
        safe = {
            "code": error.code,
            "message": "Import attempt unavailable",
            "details": [],
            "request_id": str(run["correlation_id"]),
        }
        c.execute(
            import_runs.update()
            .where(import_runs.c.id == run["id"])
            .values(status="queued" if retry else "failed", errors_json=[safe])
        )
        if not retry:
            c.execute(
                import_items.insert().values(
                    id=uuid4(),
                    owner_id=claim["owner_id"],
                    run_id=run["id"],
                    item_key=digest("terminal-attempt"),
                    outcome="failed",
                )
            )

    def item(self, claim, run, raw):
        with self.engine.begin() as c:
            self.fenced(c, claim)
            key = observation_key(raw)
            if c.execute(
                select(import_items.c.id).where(
                    import_items.c.owner_id == run["owner_id"],
                    import_items.c.run_id == run["id"],
                    import_items.c.item_key == key,
                )
            ).first():
                return
            result = persist_observation(c, run["owner_id"], raw, run["id"], run["correlation_id"])
            c.execute(
                import_items.insert().values(
                    id=uuid4(), owner_id=run["owner_id"], run_id=run["id"], item_key=key, **result
                )
            )
            c.execute(
                background_jobs.update()
                .where(background_jobs.c.id == claim["id"])
                .values(lease_until=utcnow() + timedelta(seconds=LEASE_SECONDS))
            )

    def item_error(self, claim, run, key, error):
        from sqlalchemy.dialects.postgresql import insert

        with self.engine.begin() as c:
            self.fenced(c, claim)
            c.execute(
                insert(import_items)
                .values(
                    id=uuid4(),
                    owner_id=run["owner_id"],
                    run_id=run["id"],
                    item_key=key,
                    outcome="failed",
                    error_code=error.code,
                    needs_review=error.code == "IDENTITY_CONFLICT",
                )
                .on_conflict_do_nothing()
            )

    def process(self, claim):
        try:
            with self.engine.begin() as c:
                self.fenced(c, claim)
                run = dict(
                    c.execute(
                        select(import_runs).where(
                            import_runs.c.id == claim["run_id"],
                            import_runs.c.owner_id == claim["owner_id"],
                        )
                    )
                    .mappings()
                    .one()
                )
        except LostClaim:
            return False
        with self.tracer.start_as_current_span(
            "ingestion.attempt", record_exception=False, set_status_on_exception=False
        ) as span:
            span.set_attribute("request_id", str(run["correlation_id"]))
            span.set_attribute("source", run["source"])
            span.set_attribute("workflow_run_id", str(run["id"]))
            span.set_attribute("attempt", claim["attempts"])
            try:
                data = run["request_json"]
                connector = self.connector_factory(run["source"], data, run["owner_id"])
                request = DiscoverRequest(
                    owner_id=run["owner_id"],
                    source=run["source"],
                    query=data.get("query"),
                    url=data.get("url"),
                    text=data.get("text"),
                    board=data.get("board"),
                )
                with self.tracer.start_as_current_span(
                    "ingestion.fetch", record_exception=False, set_status_on_exception=False
                ):
                    if run["source"] == "greenhouse" and data.get("job_external_id"):
                        values = [
                            connector.fetch_detail(
                                SourceReference(
                                    source="greenhouse",
                                    external_id=data["board"] + ":" + data["job_external_id"],
                                )
                            )
                        ]
                    else:
                        values = connector.discover(request)
                for index, value in enumerate(values):
                    try:
                        raw = RawObservation.model_validate(value)
                        self.item(claim, run, raw)
                    except ValidationError, ValueError:
                        self.item_error(
                            claim, run, digest(["invalid", index]), ConnectorError("SOURCE_SCHEMA")
                        )
                    except ConnectorError as error:
                        self.item_error(claim, run, observation_key(raw), error)
                for index, error in enumerate(connector.errors):
                    self.item_error(claim, run, digest(["source-error", index, error.code]), error)
                with self.engine.begin() as c:
                    self.fenced(c, claim)
                    successes = c.execute(
                        select(import_items.c.id).where(
                            import_items.c.run_id == run["id"],
                            import_items.c.owner_id == run["owner_id"],
                            import_items.c.outcome != "failed",
                        )
                    ).first()
                    errors = c.execute(
                        select(import_items.c.id).where(
                            import_items.c.run_id == run["id"],
                            import_items.c.owner_id == run["owner_id"],
                            import_items.c.outcome == "failed",
                        )
                    ).first()
                    status = "failed" if errors and not successes else "completed"
                    c.execute(
                        import_runs.update()
                        .where(
                            import_runs.c.id == run["id"], import_runs.c.owner_id == run["owner_id"]
                        )
                        .values(status=status, errors_json=[])
                    )
                    c.execute(
                        background_jobs.update()
                        .where(background_jobs.c.id == claim["id"])
                        .values(
                            status="failed" if status == "failed" else "succeeded",
                            lease_until=None,
                            claim_token=None,
                            last_error=None,
                        )
                    )
                span.set_attribute("result", status)
                return True
            except LostClaim:
                span.set_attribute("result", "lost_claim")
                return False
            except Exception as exc:
                error = (
                    exc
                    if isinstance(exc, ConnectorError)
                    else ConnectorError(
                        "DATABASE_UNAVAILABLE"
                        if isinstance(exc, SQLAlchemyError)
                        else "IMPORT_INTERNAL",
                        transient=isinstance(exc, SQLAlchemyError),
                    )
                )
                span.set_attribute("error.code", error.code)
                span.set_status(Status(StatusCode.ERROR))
                try:
                    with self.engine.begin() as c:
                        row = self.fenced(c, claim)
                        self.fail(c, row, error, utcnow())
                except LostClaim:
                    return False
                return True

    def run_once(self):
        claim = self.claim()
        return self.process(claim) if claim else False


if __name__ == "__main__":
    from rolekai.persistence import new_engine

    settings = Settings()
    engine = new_engine(settings.database_url.get_secret_value())
    worker = Worker(engine, settings=settings)
    try:
        print("Processed one due import attempt" if worker.run_once() else "No due import attempt")
    finally:
        worker.provider.shutdown()
        engine.dispose()
