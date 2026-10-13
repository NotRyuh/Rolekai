"""Versioned ingestion schema; copies frozen v2 metadata for FK resolution."""

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
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

from rolekai.schema_v2 import metadata as domain_metadata

metadata = MetaData()
for table in domain_metadata.sorted_tables:
    table.to_metadata(metadata)


def owner(primary=False):
    return Column("owner_id", Uuid, ForeignKey("user.id"), nullable=False, primary_key=primary)


def time_column(name, *, nullable=False, default=False):
    return Column(
        name,
        DateTime(timezone=True),
        nullable=nullable,
        server_default=func.now() if default else None,
    )


import_runs = Table(
    "import_run",
    metadata,
    Column("id", Uuid, primary_key=True),
    owner(),
    Column("source", String(30), nullable=False),
    CheckConstraint("source IN ('manual','remotive','greenhouse')"),
    Column("key_hash", String(64), nullable=False),
    Column("intent_hash", String(64), nullable=False),
    Column("request_json", JSONB, nullable=False),
    Column("status", String(20), nullable=False, server_default="queued"),
    CheckConstraint("status IN ('queued','running','completed','failed')"),
    Column("errors_json", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("correlation_id", Uuid, nullable=False),
    time_column("submitted_at", default=True),
    UniqueConstraint("owner_id", "key_hash"),
    UniqueConstraint("owner_id", "id"),
)
background_jobs = Table(
    "background_job",
    metadata,
    Column("id", Uuid, primary_key=True),
    owner(),
    Column("run_id", Uuid, nullable=False, unique=True),
    ForeignKeyConstraint(["owner_id", "run_id"], ["import_run.owner_id", "import_run.id"]),
    Column("status", String(20), nullable=False, server_default="queued"),
    CheckConstraint("status IN ('queued','running','succeeded','failed')"),
    Column("attempts", Integer, nullable=False, server_default="0"),
    CheckConstraint("attempts >= 0"),
    Column("max_attempts", Integer, nullable=False, server_default="3"),
    CheckConstraint("max_attempts BETWEEN 1 AND 3"),
    time_column("run_after", default=True),
    time_column("lease_until", nullable=True),
    Column("claim_token", Uuid),
    Column("last_error", String(60)),
)
Index("ix_background_due", background_jobs.c.status, background_jobs.c.run_after)
source_identities = Table(
    "source_identity",
    metadata,
    owner(True),
    Column("source", String(30), primary_key=True),
    Column("external_id", Text, primary_key=True),
    Column("job_id", Uuid, nullable=False),
    ForeignKeyConstraint(["owner_id", "job_id"], ["job.owner_id", "job.id"]),
    UniqueConstraint("owner_id", "source", "external_id"),
)
url_identities = Table(
    "job_url_identity",
    metadata,
    owner(True),
    Column("url", Text, primary_key=True),
    Column("job_id", Uuid, nullable=False),
    ForeignKeyConstraint(["owner_id", "job_id"], ["job.owner_id", "job.id"]),
    UniqueConstraint("owner_id", "url"),
)
import_items = Table(
    "import_item",
    metadata,
    Column("id", Uuid, primary_key=True),
    owner(),
    Column("run_id", Uuid, nullable=False),
    ForeignKeyConstraint(["owner_id", "run_id"], ["import_run.owner_id", "import_run.id"]),
    Column("item_key", String(64), nullable=False),
    Column("job_id", Uuid),
    ForeignKeyConstraint(["owner_id", "job_id"], ["job.owner_id", "job.id"]),
    Column("outcome", String(20), nullable=False),
    CheckConstraint("outcome IN ('created','updated','duplicate','failed')"),
    Column("needs_review", Boolean, nullable=False, server_default="false"),
    Column("error_code", String(60)),
    UniqueConstraint("owner_id", "run_id", "item_key"),
)
source_policy = Table(
    "connector_config",
    metadata,
    Column("source", String(30), primary_key=True),
    time_column("next_allowed_at"),
    time_column("last_requested_at"),
)
INGESTION_TABLES = [
    import_runs,
    background_jobs,
    source_identities,
    url_identities,
    import_items,
    source_policy,
]
