from fastapi.testclient import TestClient
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from psycopg import OperationalError


def test_health_spans_have_correlation_without_sensitive_request_or_error_data():
    from rolekai.main import create_app

    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource({"service.name": "rolekai-test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    def unavailable():
        raise OperationalError("postgresql://secret-user:DB_SECRET@private-host/db")

    app = create_app(database_probe=unavailable, tracer_provider=provider)
    with TestClient(app) as client:
        response = client.get(
            "/health/ready?cv=CV_SECRET",
            headers={"authorization": "Bearer TOKEN_SECRET", "x-request-id": "PII_SECRET"},
        )
        client.post("/unknown-PII_SECRET", json={"cv": "BODY_SECRET"})
    spans = exporter.get_finished_spans()
    assert len(spans) == 2
    assert spans[0].attributes["request_id"] == response.headers["x-request-id"]
    assert spans[0].attributes["http.route"] == "/health/ready"
    assert spans[0].attributes["http.response.status_code"] == 503
    captured = repr(
        [(dict(span.attributes), span.events, span.status.description) for span in spans]
    )
    for secret in ("DB_SECRET", "CV_SECRET", "TOKEN_SECRET", "PII_SECRET", "BODY_SECRET"):
        assert secret not in captured
    provider.shutdown()


def test_unhandled_error_does_not_record_exception_content_in_otel():
    from rolekai.main import create_app

    exporter = InMemorySpanExporter()
    provider = TracerProvider(resource=Resource({"service.name": "rolekai-test"}))
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    app = create_app(database_probe=lambda: None, tracer_provider=provider)

    @app.get("/fault")
    def fault():
        raise RuntimeError("ERROR_SECRET")

    with TestClient(app, raise_server_exceptions=False) as client:
        assert client.get("/fault").status_code == 500
    span = exporter.get_finished_spans()[0]
    assert span.attributes["http.response.status_code"] == 500
    assert not span.events
    assert "ERROR_SECRET" not in repr(span.status)
    provider.shutdown()
