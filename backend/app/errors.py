from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.headers = headers or {}
        super().__init__(message)


class UpstreamTimeoutError(AppError):
    def __init__(self, message: str = "Upstream service timed out.") -> None:
        super().__init__("upstream_timeout", message, status_code=504)


class UpstreamError(AppError):
    def __init__(
        self,
        message: str = "Upstream service error.",
        status_code: int = 502,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__("upstream_error", message, status_code=status_code, headers=headers)


class ServiceUnavailableError(AppError):
    def __init__(
        self,
        message: str = "Service temporarily unavailable.",
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            "service_unavailable",
            message,
            status_code=503,
            headers=headers,
        )


class RateLimitedError(AppError):
    def __init__(self, message: str, retry_after: int) -> None:
        super().__init__(
            "rate_limited",
            message,
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorBody


def error_payload(code: str, message: str, request_id: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "request_id": request_id}}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message, request_id),
        headers=exc.headers,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logging = __import__("logging").getLogger(__name__)
    logging.exception("Unhandled error request_id=%s", request_id)
    return JSONResponse(
        status_code=500,
        content=error_payload(
            "internal_error",
            "An unexpected error occurred.",
            request_id,
        ),
    )
