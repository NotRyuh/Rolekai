from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException


class DomainError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def safe_error(request: Request, status: int, code: str, message: str):
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": [],
                "request_id": request.state.request_id,
            }
        },
    )


def install_error_handlers(app):
    @app.exception_handler(DomainError)
    async def domain_error(request, exc):
        return safe_error(request, exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        # Do not serialize Pydantic input/ctx or provider/body values.
        return safe_error(request, 422, "VALIDATION_ERROR", "Request data is invalid")

    @app.exception_handler(SQLAlchemyError)
    async def unavailable(request, exc):
        return safe_error(request, 503, "DATABASE_UNAVAILABLE", "Database operation unavailable")

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return safe_error(request, exc.status_code, "HTTP_ERROR", "Request could not be completed")
