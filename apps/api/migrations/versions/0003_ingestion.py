"""Owner-scoped import intents, exact identities and fenced background work."""

from alembic import op
from rolekai.workflows.tables import INGESTION_TABLES, metadata

revision = "0003_ingestion"
down_revision = "0002_domains"
branch_labels = None
depends_on = None


def upgrade():
    metadata.create_all(op.get_bind(), tables=INGESTION_TABLES)
    op.create_foreign_key(
        "fk_observation_import_owner",
        "source_observation",
        "import_run",
        ["owner_id", "import_run_id"],
        ["owner_id", "id"],
    )


def downgrade():
    op.drop_constraint("fk_observation_import_owner", "source_observation", type_="foreignkey")
    metadata.drop_all(op.get_bind(), tables=INGESTION_TABLES)
