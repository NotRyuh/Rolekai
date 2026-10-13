import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]


def test_pagination_limits_and_errors_do_not_echo_sensitive_input():
    from rolekai.main import create_app

    with TestClient(create_app(database_probe=lambda: None)) as client:
        response = client.get("/api/v1/jobs?limit=101&cursor=PRIVATE_CONTENT")
        assert response.status_code in (401, 503)
        assert "PRIVATE_CONTENT" not in response.text
        assert response.json()["error"]["request_id"] == response.headers["x-request-id"]


def test_page_limit_and_cursor_contract_reject_invalid_values():
    from rolekai.api.contracts import PageQuery

    assert PageQuery(limit=100).limit == 100
    for value in (0, 101):
        with pytest.raises(ValidationError):
            PageQuery(limit=value)


def test_openapi_sync_statuses_and_async_accepted_models_are_honest():
    from rolekai.main import create_app

    schema = create_app(database_probe=lambda: None).openapi()
    paths = schema["paths"]
    assert "201" in paths["/api/v1/jobs/{job_id}/applications"]["post"]["responses"]
    assert "409" in paths["/api/v1/jobs/{job_id}/applications"]["post"]["responses"]
    assert "422" in paths["/api/v1/profile/evidence"]["post"]["responses"]
    for route in ("/api/v1/imports/remotive", "/api/v1/imports/greenhouse", "/api/v1/imports/url"):
        operation = paths[route]["post"]
        assert "202" in operation["responses"] and "503" in operation["responses"]
        assert any(p["name"] == "Idempotency-Key" for p in operation["parameters"])
    accepted = schema["components"]["schemas"]["ImportAccepted"]
    assert accepted["properties"]["status"]["const"] == "queued"
    assert "run_id" in accepted["required"] and "job_run_id" not in accepted["properties"]
    assert "API_ACCESS_TOKEN" not in json.dumps(schema)


def test_internal_candidates_validate_unknowns_and_do_not_allow_state_injection():
    from rolekai.api.contracts import NormalizedJobCandidate, RawObservation

    raw = RawObservation(
        source="manual",
        source_url="https://example.com/job",
        retrieved_at="2026-01-01T00:00:00Z",
        original_description_text="Original",
    )
    candidate = NormalizedJobCandidate(owner_id=uuid4(), title_raw="Engineer", observations=[raw])
    assert candidate.salary is None and candidate.country is None and candidate.posted_at is None
    with pytest.raises(ValidationError):
        NormalizedJobCandidate(
            owner_id=uuid4(), title_raw="Engineer", observations=[raw], application_status="applied"
        )


def test_contract_drift_check_rejects_changed_snapshot_without_rewriting(tmp_path):
    snapshot = tmp_path / "openapi.json"
    snapshot.write_text('{"changed":true}', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check-openapi.py"), "--snapshot", str(snapshot)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "drift" in result.stdout.lower()
    assert snapshot.read_text() == '{"changed":true}'
