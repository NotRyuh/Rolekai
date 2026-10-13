"""FastAPI application factory and minimal importable ASGI entry point."""

from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.sdk.trace import TracerProvider

from rolekai.api.errors import install_error_handlers
from rolekai.api.routes import router
from rolekai.health import health_router, postgres_probe
from rolekai.settings import Settings
from rolekai.telemetry import SafeTelemetryMiddleware, local_tracer_provider


def create_app(
    settings: Settings | None = None,
    database_probe: Callable[[], None] | None = None,
    tracer_provider: TracerProvider | None = None,
) -> FastAPI:
    provider = tracer_provider or local_tracer_provider()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        try:
            # Real API startup validates configuration, but importing app requires no .env.
            if settings is not None or database_probe is None:
                application.state.settings = settings or Settings()
            yield
        finally:
            engine = getattr(application.state, "domain_engine", None)
            if engine is not None:
                engine.dispose()
            if tracer_provider is None:
                provider.shutdown()

    application = FastAPI(title="Rolekai API", version="0.1.0", lifespan=lifespan)
    probe = database_probe or (lambda: postgres_probe(application.state.settings))
    application.include_router(health_router(probe))
    application.include_router(router)
    install_error_handlers(application)
    application.add_middleware(SafeTelemetryMiddleware, provider=provider)
    return application


app = create_app()
