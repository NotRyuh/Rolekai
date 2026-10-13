"""Core Domain ownership, independent states and immutable snapshots.

Revision ID: 0002_domains
Revises: 0001_foundation
"""

from alembic import op
from rolekai.schema_v2 import metadata
from sqlalchemy import text

revision = "0002_domains"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    metadata.create_all(bind)
    bind.execute(
        text("""
        CREATE FUNCTION rolekai_reject_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'Immutable record' USING ERRCODE = '23514'; END $$
    """)
    )
    for table in ("source_observation", "activity_event", "application_transition"):
        bind.execute(
            text(
                f"CREATE TRIGGER immutable_{table} BEFORE UPDATE OR DELETE ON {table} "
                "FOR EACH ROW EXECUTE FUNCTION rolekai_reject_mutation()"
            )
        )


def downgrade():
    bind = op.get_bind()
    metadata.drop_all(bind)
    bind.execute(text("DROP FUNCTION rolekai_reject_mutation()"))
