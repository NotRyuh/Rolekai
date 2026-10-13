"""Migration environment with current Core Domain metadata."""

from logging.config import fileConfig

from alembic import context
from rolekai.settings import Settings
from rolekai.workflows.tables import metadata
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

if context.config.config_file_name:
    fileConfig(context.config.config_file_name, disable_existing_loggers=False)

settings = Settings()
url = make_url(settings.database_url.get_secret_value()).set(drivername="postgresql+psycopg")

if context.is_offline_mode():
    context.configure(url=url, target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = create_engine(
        url,
        poolclass=pool.NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": settings.database_connect_timeout_seconds},
    )
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
