"""Database connections and Core Domain table facade."""

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from rolekai.schema_v2 import (  # noqa: F401
    activity,
    applications,
    evaluation_items,
    evaluation_spans,
    evaluations,
    evidence,
    jobs,
    merge_candidates,
    metadata,
    observations,
    preferences,
    profiles,
    provenance,
    requirements,
    transitions,
    users,
)


def new_engine(database_url: str):
    return create_engine(
        make_url(database_url).set(drivername="postgresql+psycopg"),
        hide_parameters=True,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 2, "options": "-c statement_timeout=5000"},
    )
