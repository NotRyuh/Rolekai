"""Frozen Core Domain v2 database schema used by its migration and repositories.

Future migrations must not change this versioned definition retroactively.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()


def ident():
    return Column("id", Uuid, primary_key=True)


def owner():
    return Column("owner_id", Uuid, ForeignKey("user.id"), nullable=False)


def timestamp(name, *, default=False, nullable=False):
    return Column(
        name,
        DateTime(timezone=True),
        nullable=nullable,
        server_default=func.now() if default else None,
    )


def enum_column(name, values, default=None):
    choices = ",".join("'" + v + "'" for v in values.split("|"))
    return Column(
        name,
        String(40),
        CheckConstraint(f"{name} IN ({choices})"),
        nullable=False,
        server_default=default,
    )


def job_link():
    return ForeignKeyConstraint(["owner_id", "job_id"], ["job.owner_id", "job.id"])


users = Table("user", metadata, ident(), timestamp("created_at", default=True))
profiles = Table(
    "search_profile",
    metadata,
    owner(),
    Column("id", Uuid, primary_key=True),
    Column("data", JSONB, nullable=False),
    UniqueConstraint("owner_id"),
    timestamp("updated_at", default=True),
)
preferences = Table(
    "profile_preference",
    metadata,
    ident(),
    owner(),
    Column("value", Text, nullable=False),
    enum_column("strength", "mandatory|preferred|informative", "preferred"),
)
evidence = Table(
    "profile_evidence",
    metadata,
    ident(),
    owner(),
    Column("text", Text, nullable=False),
    Column("source", Text, nullable=False),
    Column("evidence_date", Date, nullable=False),
    enum_column("kind", "user_written", "user_written"),
    UniqueConstraint("owner_id", "id"),
    timestamp("created_at", default=True),
)
jobs = Table(
    "job",
    metadata,
    ident(),
    owner(),
    Column("title_raw", Text, nullable=False),
    Column("title_normalized", Text),
    Column("company_display_name", Text),
    Column("company_key", Text),
    Column("canonical_url", Text),
    Column("apply_url", Text),
    enum_column("workplace_type", "remote|hybrid|onsite|unknown", "unknown"),
    enum_column("remote_eligibility", "eligible|ineligible|unknown|needs_review", "unknown"),
    Column("eligibility_reason", Text),
    enum_column("availability_status", "available|unavailable|unknown", "unknown"),
    enum_column(
        "discovery_status",
        "new|imported|normalized|duplicate_candidate|merged|archived|unavailable|unknown_availability",
        "new",
    ),
    enum_column("decision_status", "inbox|saved|dismissed", "inbox"),
    Column("salary", Text),
    Column("country", Text),
    timestamp("posted_at", nullable=True),
    timestamp("discovered_at", default=True),
    timestamp("last_verified_at", nullable=True),
    timestamp("created_at", default=True),
    timestamp("updated_at", default=True),
    UniqueConstraint("owner_id", "id"),
)
Index(
    "uq_job_owner_url",
    jobs.c.owner_id,
    jobs.c.canonical_url,
    unique=True,
    postgresql_where=jobs.c.canonical_url.is_not(None),
)
Index(
    "ix_job_owner_decision_discovery",
    jobs.c.owner_id,
    jobs.c.decision_status,
    jobs.c.discovered_at.desc(),
)
observations = Table(
    "source_observation",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    Column("import_run_id", Uuid),
    enum_column("source_type", "manual|remotive|greenhouse"),
    Column("external_id", Text),
    Column("source_url", Text),
    timestamp("retrieved_at"),
    timestamp("source_updated_at", nullable=True),
    Column("content_hash", Text, nullable=False),
    Column("raw_payload_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("original_description_html", Text),
    Column("original_description_text", Text),
    Column("attribution", Text),
    Column("parser_version", Text, nullable=False),
    UniqueConstraint("owner_id", "job_id", "id"),
)
Index(
    "uq_observation_owner_identity_snapshot",
    observations.c.owner_id,
    observations.c.source_type,
    observations.c.external_id,
    observations.c.content_hash,
    unique=True,
    postgresql_where=observations.c.external_id.is_not(None),
)
Index("ix_observation_history", observations.c.job_id, observations.c.retrieved_at.desc())
provenance = Table(
    "job_field_provenance",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    Column("observation_id", Uuid, nullable=False),
    ForeignKeyConstraint(
        ["owner_id", "job_id", "observation_id"],
        ["source_observation.owner_id", "source_observation.job_id", "source_observation.id"],
    ),
    Column("field_name", Text, nullable=False),
    Column("payload_path", Text),
    Column("citation", Text),
    enum_column("provenance_type", "source|rule|human|llm"),
    Column("confidence", Float, CheckConstraint("confidence BETWEEN 0 AND 1")),
)
requirements = Table(
    "job_requirement",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    Column("text", Text, nullable=False),
    enum_column("priority", "mandatory|preferred|informative"),
    UniqueConstraint("owner_id", "job_id", "id"),
)
merge_candidates = Table(
    "job_merge_candidate",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    Column("candidate_job_id", Uuid, nullable=False),
    ForeignKeyConstraint(["owner_id", "candidate_job_id"], ["job.owner_id", "job.id"]),
    enum_column("status", "pending|merge|do_not_merge", "pending"),
)
evaluations = Table(
    "evaluation",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    Column("job_snapshot_hash", Text, nullable=False),
    Column("profile_snapshot_hash", Text, nullable=False),
    enum_column(
        "status", "not_queued|queued|evaluating|evaluated|needs_review|failed", "not_queued"
    ),
    Column("fit_score_relative", Float, CheckConstraint("fit_score_relative BETWEEN 0 AND 100")),
    Column("score_breakdown_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("summary", Text),
    Column("model_config_data", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("prompt_version", Text, nullable=False),
    timestamp("created_at", default=True),
    timestamp("completed_at", nullable=True),
    UniqueConstraint("owner_id", "job_id", "id"),
)
evaluation_items = Table(
    "evaluation_item",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    Column("evaluation_id", Uuid, nullable=False),
    ForeignKeyConstraint(
        ["owner_id", "job_id", "evaluation_id"],
        ["evaluation.owner_id", "evaluation.job_id", "evaluation.id"],
    ),
    Column("requirement_id", Uuid, nullable=False),
    ForeignKeyConstraint(
        ["owner_id", "job_id", "requirement_id"],
        ["job_requirement.owner_id", "job_requirement.job_id", "job_requirement.id"],
    ),
    Column("classification", Text, nullable=False),
    enum_column("priority", "mandatory|preferred|informative"),
    enum_column("result", "covered|missing|unknown|conflicting"),
    Column("reason", Text, nullable=False),
    Column("confidence", Float, CheckConstraint("confidence BETWEEN 0 AND 1")),
    Column("profile_evidence_id", Uuid),
    ForeignKeyConstraint(
        ["owner_id", "profile_evidence_id"], ["profile_evidence.owner_id", "profile_evidence.id"]
    ),
    CheckConstraint("profile_evidence_id IS NULL OR result = 'covered'"),
    UniqueConstraint("owner_id", "job_id", "id"),
)
evaluation_spans = Table(
    "evaluation_evidence_span",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    Column("item_id", Uuid, nullable=False),
    ForeignKeyConstraint(
        ["owner_id", "job_id", "item_id"],
        ["evaluation_item.owner_id", "evaluation_item.job_id", "evaluation_item.id"],
    ),
    Column("observation_id", Uuid, nullable=False),
    ForeignKeyConstraint(
        ["owner_id", "job_id", "observation_id"],
        ["source_observation.owner_id", "source_observation.job_id", "source_observation.id"],
    ),
    Column("quote", Text, nullable=False),
)
applications = Table(
    "application",
    metadata,
    ident(),
    owner(),
    Column("job_id", Uuid, nullable=False),
    job_link(),
    enum_column("status", "preparing|applied|interviewing|offer|rejected|withdrawn|closed_unknown"),
    timestamp("applied_at", nullable=True),
    Column("channel", Text),
    Column("application_url", Text),
    Column("notes", Text),
    timestamp("created_at", default=True),
    timestamp("updated_at", default=True),
    UniqueConstraint("owner_id", "job_id"),
    UniqueConstraint("owner_id", "id"),
)
Index(
    "ix_application_owner_status_updated",
    applications.c.owner_id,
    applications.c.status,
    applications.c.updated_at.desc(),
)
transitions = Table(
    "application_transition",
    metadata,
    ident(),
    owner(),
    Column("application_id", Uuid, nullable=False),
    ForeignKeyConstraint(
        ["owner_id", "application_id"], ["application.owner_id", "application.id"]
    ),
    Column("from_status", Text),
    Column("to_status", Text, nullable=False),
    timestamp("occurred_at", default=True),
)
activity = Table(
    "activity_event",
    metadata,
    ident(),
    owner(),
    enum_column("subject_type", "job|application|profile|evidence|evaluation"),
    Column("subject_id", Uuid, nullable=False),
    Column("event_type", Text, nullable=False),
    enum_column("actor_type", "human|system"),
    Column("metadata_json", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    timestamp("occurred_at", default=True),
    Column("correlation_id", Uuid, nullable=False),
)
Index("ix_activity_owner_time", activity.c.owner_id, activity.c.occurred_at.desc())
