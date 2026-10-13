import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def test_remotive_preserves_attribution_unknowns_and_request_endpoint():
    from rolekai.api.contracts import DiscoverRequest
    from rolekai.connectors.remotive import Remotive
    from rolekai.jobs.normalizer import Normalizer

    calls, budgets = [], []

    def fetch(url):
        calls.append(url)
        return json.loads((FIXTURES / "remotive.json").read_text())

    connector = Remotive(fetch_json=fetch, reserve=lambda: budgets.append(True))
    raw = connector.discover(DiscoverRequest(owner_id=uuid4(), source="remotive", query="AI"))
    assert len(raw) == 2 and budgets == [True]
    assert calls == ["https://remotive.com/api/remote-jobs?search=AI"]
    assert (
        raw[0].attribution
        == "Remotive — https://remotive.com/remote-jobs/software-dev/engineer-101"
    )
    job = Normalizer(uuid4()).normalize(raw[0])
    assert job.salary is None and job.posted_at is None and job.country is None
    assert raw[0].raw_payload["freshness_delay_hours"] == 24
    assert raw[0].original_description_html == "<p>Build Python services</p>"


def test_greenhouse_known_board_content_true_and_namespaced_ids():
    from rolekai.api.contracts import DiscoverRequest, SourceReference
    from rolekai.connectors.greenhouse import Greenhouse

    calls = []

    def fetch(url):
        calls.append(url)
        return json.loads((FIXTURES / "greenhouse.json").read_text())

    connector = Greenhouse("fixture", known_boards=["fixture"], fetch_json=fetch)
    rows = connector.discover(DiscoverRequest(owner_id=uuid4(), source="greenhouse"))
    assert rows[0].external_id == "fixture:201"
    assert calls == ["https://boards-api.greenhouse.io/v1/boards/fixture/jobs?content=true"]
    detail = Greenhouse(
        "fixture",
        known_boards=["fixture"],
        fetch_json=lambda url: {
            "id": 201,
            "title": "Engineer",
            "absolute_url": "https://boards.greenhouse.io/fixture/jobs/201",
            "content": "Original",
        },
    ).fetch_detail(SourceReference(source="greenhouse", external_id="fixture:201"))
    assert detail.original_description_html == "Original"
    with pytest.raises(ValueError):
        Greenhouse("../applications", known_boards=["fixture"], fetch_json=fetch)
    with pytest.raises(ValueError):
        Greenhouse("unknown", known_boards=["fixture"], fetch_json=fetch)
    assert all("/applications" not in url for url in calls)


def test_provider_schema_failures_are_permanent_and_partial_items_are_isolated():
    from rolekai.api.contracts import DiscoverRequest
    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.remotive import Remotive

    request = DiscoverRequest(owner_id=uuid4(), source="remotive")
    with pytest.raises(ConnectorError) as failure:
        Remotive(fetch_json=lambda _: {"changed": []}, reserve=lambda: None).discover(request)
    assert failure.value.code == "SOURCE_SCHEMA" and not failure.value.transient
    data = json.loads((FIXTURES / "remotive.json").read_text())
    data["jobs"].append(
        {"id": 999, "title": False, "url": "https://example.com", "description": "bad"}
    )
    connector = Remotive(fetch_json=lambda _: data, reserve=lambda: None)
    assert len(connector.discover(request)) == 2
    assert connector.errors[0].code == "SOURCE_SCHEMA"


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost/a",
        "http://127.0.0.1/a",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/a",
        "http://[::1]/a",
        "http://[::ffff:127.0.0.1]/a",
        "file:///etc/passwd",
        "https://user:password@example.com/a",
        "http://example.com:8000/a",
        "http://example.com\\@127.0.0.1/a",
    ],
)
def test_manual_unsafe_url_rejected_before_transport(url):
    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.manual_url import SafeFetcher

    called = []
    fetcher = SafeFetcher(
        resolver=lambda _: ["93.184.216.34"],
        sender=lambda *a: called.append(a),
        allowed_hosts=["example.com"],
    )
    with pytest.raises(ConnectorError):
        fetcher.fetch(url)
    assert called == []


def test_manual_redirect_private_dns_and_rebinding_are_blocked_or_pinned():
    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.manual_url import HTTPResult, SafeFetcher

    sent = []

    def sender(url, ip, timeout, maximum):
        sent.append((url, ip))
        return HTTPResult(302, {"location": "http://127.0.0.1/private"}, b"")

    fetcher = SafeFetcher(
        resolver=lambda _: ["93.184.216.34"], sender=sender, allowed_hosts=["example.com"]
    )
    with pytest.raises(ConnectorError):
        fetcher.fetch("https://example.com/job")
    assert len(sent) == 1 and sent[0][1] == "93.184.216.34"
    sent.clear()
    with pytest.raises(ConnectorError):
        SafeFetcher(
            resolver=lambda _: ["93.184.216.34", "10.0.0.1"],
            sender=sender,
            allowed_hosts=["example.com"],
        ).fetch("https://example.com/job")
    assert sent == []


def test_manual_fetch_size_type_redirect_bound_and_inert_html():
    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.manual_url import HTTPResult, SafeFetcher, safe_text

    assert safe_text('<script>secret()</script><p>Python</p><img onerror="attack()">') == "Python"
    for response in (
        HTTPResult(200, {"content-type": "application/octet-stream"}, b"bad"),
        HTTPResult(200, {"content-type": "text/html"}, b"x" * 33),
        HTTPResult(302, {"location": "https://example.com/loop"}, b""),
    ):
        with pytest.raises(ConnectorError):
            SafeFetcher(
                resolver=lambda _: ["93.184.216.34"],
                sender=lambda *a, result=response: result,
                allowed_hosts=["example.com"],
                max_bytes=32,
            ).fetch("https://example.com/job")


def test_manual_pasted_and_url_only_fallback_keep_url_time_and_text_without_fetch():
    from rolekai.api.contracts import SourceReference
    from rolekai.connectors.manual_url import ManualURL

    ref = SourceReference(source="manual", url="https://example.com/job")
    connector = ManualURL()
    pasted = connector.fetch_detail(ref, text="Original pasted description")
    assert (
        pasted.source_url == ref.url
        and pasted.original_description_text == "Original pasted description"
    )
    assert pasted.retrieved_at.tzinfo is not None
    url_only = connector.fetch_detail(ref)
    assert url_only.original_description_text is None
    assert url_only.raw_payload["needs_review"] is True


def test_normalization_is_conservative_and_preserves_distinct_urls():
    from rolekai.api.contracts import RawObservation
    from rolekai.jobs.normalizer import Normalizer, canonical_url

    assert (
        canonical_url("https://example.com/a?job=1&utm_source=test#top")
        == "https://example.com/a?job=1"
    )
    assert canonical_url("https://example.com/a?job=1") != canonical_url(
        "https://example.com/a?job=2"
    )
    raw = RawObservation(
        source="manual",
        source_url="https://example.com/job",
        retrieved_at=datetime.now(UTC),
        original_description_text="remote AI role",
    )
    result = Normalizer(uuid4()).normalize(raw)
    assert result.remote_eligibility == "unknown" and result.workplace_type == "unknown"


@pytest.mark.parametrize(
    "url",
    [
        "http://2130706433/a",
        "http://0177.0.0.1/a",
        "http://0x7f000001/a",
        "https://example.com/a?api_key=private",
    ],
)
def test_alternate_private_ip_forms_and_credential_queries_are_rejected(url):
    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.manual_url import validate_url

    with pytest.raises(ConnectorError):
        validate_url(url)


def test_source_updated_timestamp_and_detail_identity_are_validated():
    from rolekai.api.contracts import DiscoverRequest, SourceReference
    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.greenhouse import Greenhouse

    data = json.loads((FIXTURES / "greenhouse.json").read_text())
    connector = Greenhouse("fixture", known_boards=["fixture"], fetch_json=lambda _: data)
    rows = connector.discover(DiscoverRequest(owner_id=uuid4(), source="greenhouse"))
    assert rows[0].source_updated_at == datetime(2026, 1, 2, 12, tzinfo=UTC)
    with pytest.raises(ConnectorError):
        Greenhouse(
            "fixture", known_boards=["fixture"], fetch_json=lambda _: data["jobs"][0]
        ).fetch_detail(SourceReference(source="greenhouse", external_id="fixture:999"))


def test_manual_network_timeout_has_recoverable_url_only_fallback():
    from rolekai.api.contracts import SourceReference
    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.manual_url import ManualURL

    class Unavailable:
        def fetch(self, url):
            raise ConnectorError("SOURCE_TIMEOUT", transient=True)

    value = ManualURL(Unavailable()).fetch_detail(
        SourceReference(source="manual", url="https://example.com/job")
    )
    assert value.source_url == "https://example.com/job"
    assert value.raw_payload["fetch_error"] == "SOURCE_TIMEOUT"
    assert value.raw_payload["needs_review"]


def test_real_pinned_http_preserves_host_and_bounds_slow_body(monkeypatch):
    import threading
    import time
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from rolekai.connectors.base import ConnectorError
    from rolekai.connectors.manual_url import pinned_get

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            payload = self.headers["Host"].encode() if self.path == "/host" else b"x" * 100
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            try:
                if self.path == "/host":
                    self.wfile.write(payload)
                else:
                    for byte in payload:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.02)
            except BrokenPipeError, ConnectionResetError:
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    try:
        value = pinned_get(f"http://fixture.invalid:{port}/host", "127.0.0.1", 1, 1024)
        assert value.body == f"fixture.invalid:{port}".encode()
        start = time.monotonic()
        with pytest.raises(ConnectorError):
            pinned_get(f"http://fixture.invalid:{port}/slow", "127.0.0.1", 0.15, 1024)
        assert time.monotonic() - start < 1
    finally:
        server.shutdown()
        server.server_close()
