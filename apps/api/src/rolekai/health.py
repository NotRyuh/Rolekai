"""Foundation health probes. No business data or product endpoints."""

from collections.abc import Callable

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from rolekai.settings import Settings


def postgres_probe(settings: Settings) -> None:
    timeout = settings.database_connect_timeout_seconds
    with psycopg.connect(
        settings.database_url.get_secret_value(),
        connect_timeout=timeout,
        options=f"-c statement_timeout={timeout * 1000}",
        autocommit=True,
    ) as connection:
        if connection.execute("SELECT 1").fetchone() != (1,):
            raise psycopg.OperationalError("Readiness probe failed")


def health_router(probe: Callable[[], None]) -> APIRouter:
    router = APIRouter(prefix="/health", tags=["health"])

    @router.get("/live")
    def live() -> dict[str, str]:
        return {"status": "alive"}

    @router.get("/ready", responses={503: {"description": "PostgreSQL unavailable"}})
    def ready(request: Request) -> JSONResponse:
        try:
            probe()
        except psycopg.Error:
            # Do not log/return exception text: connection errors may contain a DSN or PII.
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "error": {
                        "code": "DATABASE_UNAVAILABLE",
                        "message": "Database readiness check failed.",
                        "request_id": request.state.request_id,
                    },
                },
            )
        return JSONResponse(content={"status": "ready"})

    return router
