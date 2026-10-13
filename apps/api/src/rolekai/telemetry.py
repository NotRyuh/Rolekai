"""Allowlisted OTel request spans; no headers, URLs, bodies or exception text."""

from uuid import uuid4

from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import SpanKind, Status, StatusCode
from starlette.types import ASGIApp, Message, Receive, Scope, Send


def local_tracer_provider() -> TracerProvider:
    # No environment/resource detectors or exporters: Foundation sends no telemetry externally.
    return TracerProvider(resource=Resource({"service.name": "rolekai-api"}))


class SafeTelemetryMiddleware:
    def __init__(self, app: ASGIApp, provider: TracerProvider) -> None:
        self.app = app
        self.tracer = provider.get_tracer("rolekai.foundation", "0.1.0")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = str(uuid4())  # Do not trust incoming correlation values containing user text.
        scope.setdefault("state", {})["request_id"] = request_id
        with self.tracer.start_as_current_span(
            "HTTP request",
            kind=SpanKind.SERVER,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            span.set_attribute("request_id", request_id)
            span.set_attribute("http.request.method", scope["method"])

            async def safe_send(message: Message) -> None:
                if message["type"] == "http.response.start":
                    code = message["status"]
                    span.set_attribute("http.response.status_code", code)
                    route = scope.get("route")
                    span.set_attribute("http.route", getattr(route, "path", "unmatched"))
                    if code >= 500:
                        span.set_status(Status(StatusCode.ERROR))
                    message = {
                        **message,
                        "headers": [
                            *message.get("headers", []),
                            (b"x-request-id", request_id.encode()),
                        ],
                    }
                await send(message)

            try:
                await self.app(scope, receive, safe_send)
            except Exception:
                span.set_status(Status(StatusCode.ERROR))
                span.set_attribute("http.response.status_code", 500)
                raise
