from fastapi.testclient import TestClient
from psycopg import OperationalError


def test_foundation_health_paths_remain_available_and_declare_readiness_failure():
    from rolekai.main import create_app

    schema = create_app(database_probe=lambda: None).openapi()
    assert {p for p in schema["paths"] if p.startswith("/health/")} == {
        "/health/live",
        "/health/ready",
    }
    assert "503" in schema["paths"]["/health/ready"]["get"]["responses"]


def test_liveness_never_calls_the_database():
    from rolekai.main import create_app

    def forbidden_probe():
        raise AssertionError("liveness must not call a database")

    with TestClient(create_app(database_probe=forbidden_probe)) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}
    assert response.headers["x-request-id"]


def test_readiness_requires_a_successful_probe():
    from rolekai.main import create_app

    calls = []
    with TestClient(create_app(database_probe=lambda: calls.append(True))) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert calls == [True]


def test_readiness_failure_is_safe_and_liveness_stays_available():
    from rolekai.main import create_app

    def unavailable():
        raise OperationalError("password=DO_NOT_EXPOSE hostname=private-host")

    with TestClient(create_app(database_probe=unavailable)) as client:
        response = client.get("/health/ready")
        assert client.get("/health/live").status_code == 200
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert response.json()["error"]["request_id"] == response.headers["x-request-id"]
    assert "DO_NOT_EXPOSE" not in response.text
    assert "private-host" not in response.text
