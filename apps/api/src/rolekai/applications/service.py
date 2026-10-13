"""Owner-authorized synchronous writes and events share one transaction."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from rolekai.activity.models import ActivityEvent
from rolekai.api.errors import DomainError
from rolekai.domain import utcnow
from rolekai.persistence import (
    activity,
    applications,
    evidence,
    jobs,
    preferences,
    profiles,
    transitions,
    users,
)

TRANSITIONS = {
    "preparing": {"applied", "withdrawn", "closed_unknown"},
    "applied": {"interviewing", "rejected", "withdrawn", "closed_unknown"},
    "interviewing": {"offer", "rejected", "withdrawn", "closed_unknown"},
    "offer": {"withdrawn", "closed_unknown"},
    "rejected": set(),
    "withdrawn": set(),
    "closed_unknown": set(),
}


def event(connection, owner, subject_type, subject_id, event_type, request_id, metadata=None):
    record = ActivityEvent(
        id=uuid4(),
        owner_id=owner,
        subject_type=subject_type,
        subject_id=subject_id,
        event_type=event_type,
        actor_type="human",
        occurred_at=utcnow(),
        correlation_id=request_id,
        metadata_json=metadata or {},
    )
    connection.execute(activity.insert().values(**record.model_dump()))


def owned(connection, table, owner, ident, *, lock=False):
    query = select(table).where(table.c.owner_id == owner, table.c.id == ident)
    if lock:
        query = query.with_for_update()
    row = connection.execute(query).mappings().first()
    if row is None:
        raise DomainError(404, "NOT_FOUND", "Resource not found")
    return row


def put_profile(engine, owner, profile, request_id):
    data = profile.model_dump(mode="json")
    with engine.begin() as c:
        c.execute(insert(users).values(id=owner).on_conflict_do_nothing())
        # Serialize this owner's mutations, including concurrent first creation.
        c.execute(select(users).where(users.c.id == owner).with_for_update())
        current = c.execute(select(profiles).where(profiles.c.owner_id == owner)).mappings().first()
        if current is not None and current["data"] == data:
            return profile
        ident = current["id"] if current else uuid4()
        statement = insert(profiles).values(id=ident, owner_id=owner, data=data)
        c.execute(
            statement.on_conflict_do_update(
                index_elements=["owner_id"], set_={"data": data, "updated_at": utcnow()}
            )
        )
        c.execute(preferences.delete().where(preferences.c.owner_id == owner))
        for pref in profile.technologies:
            c.execute(
                preferences.insert().values(
                    id=uuid4(), owner_id=owner, value=pref.value, strength=pref.strength
                )
            )
        event(c, owner, "profile", ident, "profile.updated", request_id)
    return profile


def add_evidence(engine, owner, item, request_id):
    with engine.begin() as c:
        c.execute(insert(users).values(id=owner).on_conflict_do_nothing())
        row = (
            c.execute(
                evidence.insert()
                .values(id=uuid4(), owner_id=owner, **item.model_dump())
                .returning(evidence)
            )
            .mappings()
            .one()
        )
        event(c, owner, "evidence", row["id"], "evidence.created", request_id)
        return {k: row[k] for k in ("id", "owner_id", "text", "source", "evidence_date", "kind")}


def decide(engine, owner, job_id, change, request_id):
    with engine.begin() as c:
        job = owned(c, jobs, owner, job_id, lock=True)
        if job["decision_status"] == change.decision_status:
            return dict(job)
        row = (
            c.execute(
                jobs.update()
                .where(jobs.c.id == job_id, jobs.c.owner_id == owner)
                .values(decision_status=change.decision_status, updated_at=utcnow())
                .returning(jobs)
            )
            .mappings()
            .one()
        )
        event(
            c,
            owner,
            "job",
            job_id,
            "job." + change.decision_status,
            request_id,
            {"reason": change.reason} if change.reason is not None else {},
        )
        return dict(row)


def create_application(engine, owner, job_id, data, request_id):
    try:
        with engine.begin() as c:
            job = owned(c, jobs, owner, job_id, lock=True)
            if job["decision_status"] != "saved" or not data.confirmed:
                raise DomainError(
                    409, "APPLICATION_REQUIRES_CONFIRMATION", "Saved job and confirmation required"
                )
            if data.status not in ("preparing", "applied"):
                raise DomainError(409, "INVALID_TRANSITION", "Invalid initial application status")
            if c.execute(
                select(applications.c.id).where(
                    applications.c.owner_id == owner, applications.c.job_id == job_id
                )
            ).first():
                raise DomainError(409, "APPLICATION_EXISTS", "Application already exists")
            row = (
                c.execute(
                    applications.insert()
                    .values(
                        id=uuid4(),
                        owner_id=owner,
                        job_id=job_id,
                        **data.model_dump(exclude={"confirmed"}),
                    )
                    .returning(applications)
                )
                .mappings()
                .one()
            )
            c.execute(
                transitions.insert().values(
                    id=uuid4(),
                    owner_id=owner,
                    application_id=row["id"],
                    from_status=None,
                    to_status=row["status"],
                )
            )
            event(c, owner, "application", row["id"], "application.created", request_id)
            return dict(row)
    except IntegrityError as exc:
        # Only the Application uniqueness violation is a conflict. Other failures
        # (e.g. Activity persistence) remain dependency errors and roll back.
        if getattr(exc.orig, "sqlstate", None) == "23505":
            raise DomainError(409, "APPLICATION_EXISTS", "Application already exists") from None
        raise


def patch_application(engine, owner, app_id, data, request_id):
    with engine.begin() as c:
        current = owned(c, applications, owner, app_id, lock=True)
        fields = data.model_dump(exclude_unset=True, exclude={"confirmed"})
        if "status" in fields and fields["status"] != current["status"]:
            if not data.confirmed or fields["status"] not in TRANSITIONS[current["status"]]:
                raise DomainError(409, "INVALID_TRANSITION", "Confirmed valid transition required")
            c.execute(
                transitions.insert().values(
                    id=uuid4(),
                    owner_id=owner,
                    application_id=app_id,
                    from_status=current["status"],
                    to_status=data.status,
                )
            )
        changed = {key: value for key, value in fields.items() if value != current[key]}
        if not changed:
            return dict(current)
        row = (
            c.execute(
                applications.update()
                .where(applications.c.id == app_id, applications.c.owner_id == owner)
                .values(**changed, updated_at=utcnow())
                .returning(applications)
            )
            .mappings()
            .one()
        )
        event(c, owner, "application", app_id, "application.updated", request_id)
        return dict(row)
