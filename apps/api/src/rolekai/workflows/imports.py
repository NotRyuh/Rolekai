"""Idempotent import intent and exact-dedupe persistence, never submissions."""

import hashlib
import json
import math
import re
from datetime import timedelta
from urllib.parse import urlsplit
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert

from rolekai.activity.models import ActivityEvent
from rolekai.api.contracts import ImportAccepted
from rolekai.api.errors import DomainError
from rolekai.connectors.base import ConnectorError
from rolekai.connectors.manual_url import validate_url
from rolekai.domain import utcnow
from rolekai.jobs.dedupe import DeduplicationService
from rolekai.jobs.normalizer import Normalizer
from rolekai.persistence import (
    activity,
    jobs,
    merge_candidates,
    observations,
    provenance,
    users,
)
from rolekai.workflows.tables import (
    background_jobs,
    import_items,
    import_runs,
    source_identities,
    source_policy,
    url_identities,
)

PARSER_VERSION = "ingestion-v1"
PRIORITY = {"greenhouse": 3, "manual": 2, "remotive": 1}


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def observation_key(raw):
    return digest(raw.model_dump(mode="json", exclude={"retrieved_at"}))


def greenhouse_target(body, known_boards):
    board, job = body.board, None
    if body.url:
        parts = urlsplit(validate_url(body.url))
        match = re.fullmatch(r"/([^/]+)/jobs/([0-9]+)/?", parts.path)
        if parts.hostname not in ("boards.greenhouse.io", "job-boards.greenhouse.io") or not match:
            raise DomainError(422, "INVALID_BOARD", "Known Greenhouse job URL required")
        if board is not None and board != match[1]:
            raise DomainError(422, "INVALID_BOARD", "Board and URL disagree")
        board, job = match[1], match[2]
    if not board or board not in known_boards or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", board):
        raise DomainError(422, "INVALID_BOARD", "Known Greenhouse board required")
    return board, job


def accept_import(engine, owner, source, body, key, request_id, *, known_boards=()):
    if source not in ("manual", "remotive", "greenhouse"):
        raise DomainError(422, "SOURCE_NOT_ALLOWED", "Source not enabled")
    data = body.model_dump(mode="json")
    try:
        if source == "manual":
            if not body.url:
                raise DomainError(422, "URL_REQUIRED", "Manual URL required")
            data["url"] = validate_url(body.url)
        elif source == "greenhouse":
            data["board"], data["job_external_id"] = greenhouse_target(body, known_boards)
    except ConnectorError:
        raise DomainError(422, "UNSAFE_URL", "URL is not permitted") from None
    intention = digest({"source": source, "request": data})
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    with engine.begin() as c:
        c.execute(insert(users).values(id=owner).on_conflict_do_nothing())
        c.execute(select(users.c.id).where(users.c.id == owner).with_for_update())
        prior = (
            c.execute(
                select(import_runs).where(
                    import_runs.c.owner_id == owner, import_runs.c.key_hash == key_hash
                )
            )
            .mappings()
            .first()
        )
        if prior:
            if prior["intent_hash"] != intention:
                raise DomainError(409, "IDEMPOTENCY_CONFLICT", "Key already has another intention")
            return ImportAccepted(
                run_id=prior["id"], source=prior["source"], submitted_at=prior["submitted_at"]
            )
        run_id = uuid4()
        row = (
            c.execute(
                import_runs.insert()
                .values(
                    id=run_id,
                    owner_id=owner,
                    source=source,
                    key_hash=key_hash,
                    intent_hash=intention,
                    request_json=data,
                    correlation_id=request_id,
                )
                .returning(import_runs)
            )
            .mappings()
            .one()
        )
        c.execute(background_jobs.insert().values(id=uuid4(), owner_id=owner, run_id=run_id))
        return ImportAccepted(run_id=run_id, source=source, submitted_at=row["submitted_at"])


def reserve_remotive(engine, *, queries_per_day=4):
    if not 1 <= queries_per_day <= 4:
        raise ValueError("Remotive cap must be between 1 and 4")
    with engine.begin() as c:
        c.execute(text("SELECT pg_advisory_xact_lock(731031)"))
        now = utcnow()
        prior = (
            c.execute(select(source_policy).where(source_policy.c.source == "remotive"))
            .mappings()
            .first()
        )
        if prior and prior["next_allowed_at"] > now:
            raise ConnectorError(
                "SOURCE_RATE_LIMIT",
                transient=True,
                retry_after=math.ceil((prior["next_allowed_at"] - now).total_seconds()),
            )
        statement = insert(source_policy).values(
            source="remotive",
            last_requested_at=now,
            next_allowed_at=now + timedelta(seconds=86400 / queries_per_day),
        )
        c.execute(
            statement.on_conflict_do_update(
                index_elements=["source"],
                set_={
                    "last_requested_at": now,
                    "next_allowed_at": now + timedelta(seconds=86400 / queries_per_day),
                },
            )
        )


def persist_observation(c, owner, raw, run_id, request_id):
    c.execute(select(users.c.id).where(users.c.id == owner).with_for_update())
    candidate = Normalizer(owner).normalize(raw)
    resolution = DeduplicationService(c, owner).resolve(candidate)
    key = observation_key(raw)
    job_id = resolution.job_id or uuid4()
    prior = c.execute(
        select(observations.c.id).where(
            observations.c.owner_id == owner,
            observations.c.job_id == job_id,
            observations.c.source_type == raw.source,
            observations.c.external_id == raw.external_id,
            observations.c.content_hash == key,
        )
    ).first()
    if prior:
        return {"outcome": "duplicate", "job_id": job_id, "needs_review": False}
    values = candidate.model_dump(exclude={"owner_id", "observations"}, mode="python")
    values["title_normalized"] = " ".join(candidate.title_raw.casefold().split())
    values["company_key"] = (candidate.company_display_name or "").casefold() or None
    new = resolution.job_id is None
    needs_review = bool(raw.raw_payload.get("needs_review")) or bool(resolution.candidate_ids)
    if new:
        c.execute(
            jobs.insert().values(
                id=job_id,
                owner_id=owner,
                **values,
                discovery_status="duplicate_candidate" if needs_review else "normalized",
            )
        )
    current = (
        c.execute(select(jobs).where(jobs.c.id == job_id, jobs.c.owner_id == owner))
        .mappings()
        .one()
    )
    obs_id = uuid4()
    c.execute(
        observations.insert().values(
            id=obs_id,
            owner_id=owner,
            job_id=job_id,
            import_run_id=run_id,
            source_type=raw.source,
            external_id=raw.external_id,
            source_url=raw.source_url,
            retrieved_at=raw.retrieved_at,
            source_updated_at=raw.source_updated_at,
            content_hash=key,
            raw_payload_json=raw.raw_payload,
            parser_version=PARSER_VERSION,
            original_description_html=raw.original_description_html,
            original_description_text=raw.original_description_text,
            attribution=raw.attribution,
        )
    )
    changes, conflicts = {}, []
    fields = [
        "title_raw",
        "title_normalized",
        "company_display_name",
        "company_key",
        "salary",
        "posted_at",
        "country",
    ]
    for field in fields:
        value = values[field]
        if value is None or field.startswith("title") and not raw.raw_payload.get("title"):
            continue
        existing = (
            c.execute(
                select(provenance, observations.c.source_type)
                .join(observations, provenance.c.observation_id == observations.c.id)
                .where(
                    provenance.c.owner_id == owner,
                    provenance.c.job_id == job_id,
                    provenance.c.field_name == field,
                )
            )
            .mappings()
            .first()
        )
        rank = PRIORITY[existing["source_type"]] if existing else 0
        if not new and current[field] is not None and current[field] != value:
            conflicts.append(field)
        if PRIORITY[raw.source] >= rank:
            changes[field] = value
            c.execute(
                provenance.delete().where(
                    provenance.c.owner_id == owner,
                    provenance.c.job_id == job_id,
                    provenance.c.field_name == field,
                )
            )
            c.execute(
                provenance.insert().values(
                    id=uuid4(),
                    owner_id=owner,
                    job_id=job_id,
                    observation_id=obs_id,
                    field_name=field,
                    payload_path=field,
                    provenance_type="source",
                )
            )
    if conflicts:
        needs_review = True
    if not new:
        changes["updated_at"] = utcnow()
        if needs_review:
            changes["discovery_status"] = "duplicate_candidate"
        c.execute(
            jobs.update().where(jobs.c.id == job_id, jobs.c.owner_id == owner).values(**changes)
        )
    if raw.external_id:
        c.execute(
            insert(source_identities)
            .values(owner_id=owner, source=raw.source, external_id=raw.external_id, job_id=job_id)
            .on_conflict_do_nothing()
        )
    if candidate.canonical_url:
        c.execute(
            insert(url_identities)
            .values(owner_id=owner, url=candidate.canonical_url, job_id=job_id)
            .on_conflict_do_nothing()
        )
    for other in resolution.candidate_ids:
        c.execute(
            merge_candidates.insert().values(
                id=uuid4(), owner_id=owner, job_id=job_id, candidate_job_id=other, status="pending"
            )
        )
    record = ActivityEvent(
        id=uuid4(),
        owner_id=owner,
        subject_type="job",
        subject_id=job_id,
        event_type="job.discovered" if new else "job.observed_change",
        actor_type="system",
        occurred_at=utcnow(),
        correlation_id=request_id,
        metadata_json={"fields": list(changes), "conflicts": conflicts, "source": raw.source},
    )
    c.execute(activity.insert().values(**record.model_dump()))
    return {
        "outcome": "created" if new else "updated",
        "job_id": job_id,
        "needs_review": needs_review,
    }


def run_result(c, run):
    rows = (
        c.execute(
            select(import_items).where(
                import_items.c.owner_id == run["owner_id"], import_items.c.run_id == run["id"]
            )
        )
        .mappings()
        .all()
    )
    counts = {
        name: sum(row["outcome"] == name for row in rows)
        for name in ("created", "updated", "duplicate", "failed")
    }
    errors = list(run["errors_json"])
    errors.extend(
        {
            "code": r["error_code"],
            "message": "Source item could not be imported",
            "details": [],
            "request_id": run["correlation_id"],
        }
        for r in rows
        if r["error_code"]
    )
    return {
        "run_id": run["id"],
        "status": run["status"],
        "source": run["source"],
        **counts,
        "needs_review": sum(r["needs_review"] for r in rows),
        "errors": errors,
        "job_ids": sorted({r["job_id"] for r in rows if r["job_id"]}, key=str),
    }


def get_run(engine, owner, run_id):
    with engine.connect() as c:
        run = (
            c.execute(
                select(import_runs).where(
                    import_runs.c.id == run_id, import_runs.c.owner_id == owner
                )
            )
            .mappings()
            .first()
        )
        if run is None:
            raise DomainError(404, "NOT_FOUND", "Import run not found")
        return run_result(c, run)
