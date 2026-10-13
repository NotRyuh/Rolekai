import base64
import binascii
import json
import secrets
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import AwareDatetime
from sqlalchemy import select, tuple_

from rolekai.api.contracts import (
    ActivityPage,
    DecisionChange,
    ErrorResponse,
    EvaluationAccepted,
    EvidencePage,
    ImportAccepted,
    ImportRequest,
    ImportRun,
    JobDetail,
    JobListPage,
    JobSummary,
    PageQuery,
)
from rolekai.api.errors import DomainError
from rolekai.applications.models import Application, ApplicationCreate, ApplicationPatch
from rolekai.applications.service import (
    add_evidence,
    create_application,
    decide,
    owned,
    patch_application,
    put_profile,
)
from rolekai.domain import Eligibility, SourceType
from rolekai.evaluation.models import Evaluation
from rolekai.jobs.models import DecisionStatus
from rolekai.persistence import (
    activity,
    applications,
    evaluation_items,
    evaluation_spans,
    evaluations,
    evidence,
    jobs,
    merge_candidates,
    new_engine,
    observations,
    profiles,
    provenance,
    requirements,
)
from rolekai.profile.models import EvidenceCreate, ProfileEvidence, SearchProfile
from rolekai.workflows.imports import accept_import, get_run

bearer = HTTPBearer(auto_error=False)
router = APIRouter(
    prefix="/api/v1",
    responses={code: {"model": ErrorResponse} for code in (401, 404, 409, 422, 503)},
)


def current_owner(
    request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)]
) -> UUID:
    settings = getattr(request.app.state, "settings", None)
    if settings is None or settings.api_access_token is None:
        raise DomainError(503, "LOCAL_AUTH_NOT_CONFIGURED", "Local API authentication unavailable")
    expected = settings.api_access_token.get_secret_value()
    if (
        not expected
        or credentials is None
        or not secrets.compare_digest(credentials.credentials.encode(), expected.encode())
    ):
        raise DomainError(401, "UNAUTHORIZED", "Authentication required")
    # Owner is server-configured, never taken from user headers or request bodies.
    return settings.current_owner_id


Owner = Annotated[UUID, Depends(current_owner)]


def database(request: Request):
    engine = getattr(request.app.state, "domain_engine", None)
    if engine is None:
        engine = new_engine(request.app.state.settings.database_url.get_secret_value())
        request.app.state.domain_engine = engine
    return engine


Database = Annotated[object, Depends(database)]


def correlation(request):
    return UUID(request.state.request_id)


def page_clause(query, table, cursor):
    time_field = {
        "job": "discovered_at",
        "activity_event": "occurred_at",
        "profile_evidence": "created_at",
    }[table.name]
    time_column = table.c[time_field]
    if cursor:
        try:
            value = json.loads(base64.b64decode(cursor.encode(), altchars=b"-_", validate=True))
            if value["r"] != table.name:
                raise ValueError("Cursor resource mismatch")
            ident = UUID(value["i"])
            timestamp = datetime.fromisoformat(value["t"])
            if timestamp.utcoffset() is None:
                raise ValueError("Cursor timestamp must be aware")
        except ValueError, UnicodeError, binascii.Error, TypeError, KeyError, AttributeError:
            raise DomainError(422, "INVALID_CURSOR", "Invalid pagination cursor") from None
        query = query.where(tuple_(time_column, table.c.id) < tuple_(timestamp, ident))
    return query.order_by(time_column.desc(), table.c.id.desc())


def page(engine, query, table, params):
    with engine.connect() as c:
        rows = (
            c.execute(page_clause(query, table, params.cursor).limit(params.limit + 1))
            .mappings()
            .all()
        )
    items = [dict(row) for row in rows[: params.limit]]
    cursor = None
    if len(rows) > params.limit:
        time_field = {
            "job": "discovered_at",
            "activity_event": "occurred_at",
            "profile_evidence": "created_at",
        }[table.name]
        cursor = base64.urlsafe_b64encode(
            json.dumps(
                {
                    "r": table.name,
                    "i": str(items[-1]["id"]),
                    "t": items[-1][time_field].isoformat(),
                },
                separators=(",", ":"),
            ).encode()
        ).decode()
    return items, cursor


def page_query(
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=200)] = None,
) -> PageQuery:
    return PageQuery(limit=limit, cursor=cursor)


Page = Annotated[PageQuery, Depends(page_query)]


@router.get("/profile/search", response_model=SearchProfile)
def get_profile(owner: Owner, db: Database):
    with db.connect() as c:
        row = c.execute(select(profiles).where(profiles.c.owner_id == owner)).mappings().first()
        if row is None:
            raise DomainError(404, "NOT_FOUND", "Profile not found")
        return row["data"]


@router.put("/profile/search", response_model=SearchProfile)
def edit_profile(body: SearchProfile, request: Request, owner: Owner, db: Database):
    return put_profile(db, owner, body, correlation(request))


@router.post("/profile/evidence", response_model=ProfileEvidence, status_code=201)
def post_evidence(body: EvidenceCreate, request: Request, owner: Owner, db: Database):
    return add_evidence(db, owner, body, correlation(request))


@router.get("/profile/evidence", response_model=EvidencePage)
def list_evidence(owner: Owner, db: Database, params: Page):
    items, cursor = page(db, select(evidence).where(evidence.c.owner_id == owner), evidence, params)
    keys = {"id", "owner_id", "text", "source", "evidence_date", "kind"}
    return {
        "items": [{k: v for k, v in row.items() if k in keys} for row in items],
        "next_cursor": cursor,
    }


@router.patch("/jobs/{job_id}/decision", response_model=JobSummary)
def decision(job_id: UUID, body: DecisionChange, request: Request, owner: Owner, db: Database):
    row = decide(db, owner, job_id, body, correlation(request))
    with db.connect() as connection:
        return summary(connection, row)


def summary(connection, row):
    source = connection.execute(
        select(observations.c.source_type)
        .where(observations.c.owner_id == row["owner_id"], observations.c.job_id == row["id"])
        .order_by(observations.c.retrieved_at.desc(), observations.c.id)
        .limit(1)
    ).scalar()
    latest = (
        connection.execute(
            select(evaluations)
            .where(evaluations.c.owner_id == row["owner_id"], evaluations.c.job_id == row["id"])
            .order_by(evaluations.c.created_at.desc(), evaluations.c.id)
            .limit(1)
        )
        .mappings()
        .first()
    )
    return {
        **dict(row),
        "preferred_source": source,
        "latest_evaluation": {
            "id": latest["id"],
            "status": latest["status"],
            "fit_score_relative": latest["fit_score_relative"],
        }
        if latest
        else None,
    }


def evaluation_detail(connection, row):
    result = dict(row)
    query = (
        select(evaluation_items, requirements.c.text.label("requirement"))
        .join(
            requirements,
            (requirements.c.id == evaluation_items.c.requirement_id)
            & (requirements.c.owner_id == evaluation_items.c.owner_id)
            & (requirements.c.job_id == evaluation_items.c.job_id),
        )
        .where(
            evaluation_items.c.owner_id == row["owner_id"],
            evaluation_items.c.evaluation_id == row["id"],
        )
    )
    items = []
    all_spans = []
    for item in connection.execute(query).mappings():
        spans = [
            {"observation_id": span["observation_id"], "quote": span["quote"]}
            for span in connection.execute(
                select(evaluation_spans).where(
                    evaluation_spans.c.owner_id == row["owner_id"],
                    evaluation_spans.c.item_id == item["id"],
                )
            ).mappings()
        ]
        items.append(
            {
                key: item[key]
                for key in (
                    "requirement",
                    "classification",
                    "priority",
                    "result",
                    "reason",
                    "confidence",
                    "profile_evidence_id",
                )
            }
            | {"evidence": spans}
        )
        all_spans.extend(spans)
    result["requirements"] = items
    result["evidence"] = all_spans
    result["unknowns"] = [item["requirement"] for item in items if item["result"] == "unknown"]
    return result


@router.get("/jobs", response_model=JobListPage)
def list_jobs(
    owner: Owner,
    db: Database,
    params: Page,
    decision_status: DecisionStatus | None = None,
    source: SourceType | None = None,
    remote_eligibility: Eligibility | None = None,
    posted_after: AwareDatetime | None = None,
    posted_before: AwareDatetime | None = None,
):
    query = select(jobs).where(jobs.c.owner_id == owner)
    if decision_status:
        query = query.where(jobs.c.decision_status == decision_status)
    if remote_eligibility:
        query = query.where(jobs.c.remote_eligibility == remote_eligibility)
    if posted_after:
        query = query.where(jobs.c.posted_at >= posted_after)
    if posted_before:
        query = query.where(jobs.c.posted_at <= posted_before)
    if source:
        query = query.where(
            select(observations.c.id)
            .where(
                observations.c.owner_id == owner,
                observations.c.job_id == jobs.c.id,
                observations.c.source_type == source,
            )
            .exists()
        )
    items, cursor = page(db, query, jobs, params)
    with db.connect() as c:
        return {"items": [summary(c, row) for row in items], "next_cursor": cursor}


@router.get("/jobs/{job_id}", response_model=JobDetail)
def job_detail(job_id: UUID, owner: Owner, db: Database):
    with db.connect() as c:
        row = owned(c, jobs, owner, job_id)
        result = summary(c, row)
        for name, table in (
            ("observations", observations),
            ("provenance", provenance),
            ("evaluations", evaluations),
        ):
            rows = (
                c.execute(select(table).where(table.c.owner_id == owner, table.c.job_id == job_id))
                .mappings()
                .all()
            )
            # DTO validates the public shape rather than returning internal columns.
            if name == "provenance":
                rows = [{k: v for k, v in r.items() if k != "owner_id"} for r in rows]
            if name == "evaluations":
                rows = [evaluation_detail(c, r) for r in rows]
            result[name] = [dict(r) for r in rows]
        app = (
            c.execute(
                select(applications).where(
                    applications.c.owner_id == owner, applications.c.job_id == job_id
                )
            )
            .mappings()
            .first()
        )
        result["application"] = dict(app) if app else None
        result["merge_candidate_ids"] = list(
            c.scalars(
                select(merge_candidates.c.candidate_job_id).where(
                    merge_candidates.c.owner_id == owner, merge_candidates.c.job_id == job_id
                )
            )
        )
        return result


@router.post("/jobs/{job_id}/applications", response_model=Application, status_code=201)
def post_application(
    job_id: UUID, body: ApplicationCreate, request: Request, owner: Owner, db: Database
):
    return create_application(db, owner, job_id, body, correlation(request))


@router.patch("/applications/{app_id}", response_model=Application)
def edit_application(
    app_id: UUID, body: ApplicationPatch, request: Request, owner: Owner, db: Database
):
    return patch_application(db, owner, app_id, body, correlation(request))


@router.get("/activity", response_model=ActivityPage)
def list_activity(
    owner: Owner,
    db: Database,
    params: Page,
    subject_id: UUID | None = None,
    event_type: str | None = None,
):
    query = select(activity).where(activity.c.owner_id == owner)
    if subject_id:
        query = query.where(activity.c.subject_id == subject_id)
    if event_type:
        query = query.where(activity.c.event_type == event_type)
    items, cursor = page(db, query, activity, params)
    return {"items": items, "next_cursor": cursor}


Key = Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=200)]


def pending_async():
    raise DomainError(503, "FEATURE_NOT_ENABLED", "Asynchronous execution is not enabled")


@router.post(
    "/imports/remotive",
    response_model=ImportAccepted,
    status_code=202,
    description=("The same owner/key/intent returns the same run_id; changed intent is 409."),
)
def import_remotive(body: ImportRequest, key: Key, owner: Owner, db: Database, request: Request):
    return accept_import(db, owner, "remotive", body, key, correlation(request))


@router.post(
    "/imports/greenhouse",
    response_model=ImportAccepted,
    status_code=202,
    description="Known Greenhouse boards only. Same owner/key/intent repeats run_id.",
)
def import_greenhouse(body: ImportRequest, key: Key, owner: Owner, db: Database, request: Request):
    return accept_import(
        db,
        owner,
        "greenhouse",
        body,
        key,
        correlation(request),
        known_boards=request.app.state.settings.greenhouse_boards,
    )


@router.post(
    "/imports/url",
    response_model=ImportAccepted,
    status_code=202,
    description=(
        "Manual URL/text capture. HTTP fetch requires authorized host configuration. "
        "Same intention repeats run_id."
    ),
)
def import_url(body: ImportRequest, key: Key, owner: Owner, db: Database, request: Request):
    return accept_import(db, owner, "manual", body, key, correlation(request))


@router.get(
    "/import-runs/{run_id}",
    response_model=ImportRun,
    description="Owner-scoped durable import status and aggregate outcomes.",
)
def get_import_run(run_id: UUID, owner: Owner, db: Database):
    return get_run(db, owner, run_id)


@router.post(
    "/jobs/{job_id}/evaluations",
    response_model=EvaluationAccepted,
    status_code=202,
    description="Contract only; evaluator execution is implemented in Phase 4.",
)
def request_evaluation(job_id: UUID, key: Key, owner: Owner):
    return pending_async()


@router.get("/evaluations/{evaluation_id}", response_model=Evaluation)
def get_evaluation(evaluation_id: UUID, owner: Owner, db: Database):
    with db.connect() as c:
        return evaluation_detail(c, owned(c, evaluations, owner, evaluation_id))
