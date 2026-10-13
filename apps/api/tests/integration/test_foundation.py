import os
from pathlib import Path
from urllib.parse import urlsplit

import psycopg
import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[4]
pytestmark = pytest.mark.integration


@pytest.fixture
def database_url():
    value = os.environ.get("TEST_DATABASE_URL") or dotenv_values(ROOT / ".env").get(
        "TEST_DATABASE_URL"
    )
    if not value:
        pytest.fail("TEST_DATABASE_URL is required for real Foundation integration tests")
    if urlsplit(value).path != "/rolekai_foundation_test":
        pytest.fail("Only the isolated rolekai_foundation_test database may be mutated")
    return value


def test_postgresql_readiness_uses_a_real_select_one(database_url):
    from rolekai.main import create_app
    from rolekai.settings import Settings

    with psycopg.connect(database_url, connect_timeout=2) as connection:
        assert connection.execute("SELECT 1").fetchone() == (1,)
    app = create_app(settings=Settings(database_url=database_url, _env_file=None))
    with TestClient(app) as client:
        assert client.get("/health/ready").status_code == 200


def test_upgrade_downgrade_upgrade_has_only_the_alembic_version_table(database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(ROOT / "apps/api/alembic.ini"))
    with psycopg.connect(database_url, connect_timeout=2) as connection:
        tables = connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall()
        assert {row[0] for row in tables} <= {"alembic_version"}, "Refuse nonempty domain DB"
    command.upgrade(config, "0001_foundation")
    command.downgrade(config, "base")
    command.upgrade(config, "0001_foundation")
    with psycopg.connect(database_url, connect_timeout=2) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == (
            "0001_foundation",
        )
        tables = connection.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ).fetchall()
        assert {row[0] for row in tables} == {"alembic_version"}


def test_connection_refusal_produces_503_but_keeps_liveness():
    from rolekai.main import create_app
    from rolekai.settings import Settings

    # Port 1 is not this project's Postgres port; test connection refusal, not a mocked probe.
    settings = Settings(database_url="postgresql://invalid:private@127.0.0.1:1/rolekai")
    with TestClient(create_app(settings=settings)) as client:
        assert client.get("/health/live").status_code == 200
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert "private" not in response.text
