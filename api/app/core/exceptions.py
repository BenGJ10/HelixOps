from __future__ import annotations
import traceback
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from .logging import get_logger

logger = get_logger(__name__)

def _problem_response(
    status: int,
    title: str,
    detail: str,
    instance: str | None = None,
    **extra: object,
) -> JSONResponse:
    """Return an RFC 7807 problem+json response."""
    body: dict[str, object] = {
        "type": f"https://helixops.io/errors/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    body.update(extra)
    return JSONResponse(
        status_code=status,
        content=body,
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return _problem_response(
            status=exc.status_code,
            title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            detail=str(exc.detail),
            instance=str(request.url),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return _problem_response(
            status=422,
            title="Validation Error",
            detail="One or more fields failed validation.",
            instance=str(request.url),
            errors=errors,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled exception",
            path=str(request.url),
            method=request.method,
            error=str(exc),
            traceback=traceback.format_exc(),
        )
        return _problem_response(
            status=500,
            title="Internal Server Error",
            detail="An unexpected error occurred. Please try again later.",
            instance=str(request.url),
        )
