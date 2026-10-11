"""API errors that never include a traceback in the response body."""

import logging

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler as drf_exception_handler

from common.responses import error_response

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Expected failure with a client-safe message."""

    def __init__(self, message, code="error", status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


def _flatten_validation(data):
    if isinstance(data, list):
        return "; ".join(str(item) for item in data)
    if isinstance(data, dict):
        parts = []
        for key, value in data.items():
            text = _flatten_validation(value)
            if key in {"non_field_errors", "detail"}:
                parts.append(text)
            else:
                parts.append(f"{key}: {text}")
        return "; ".join(parts)
    return str(data)


def api_exception_handler(exc, context):
    """Map exceptions to the error envelope. Stack traces stay in server logs."""
    if isinstance(exc, AppError):
        logger.info("app error code=%s status=%s", exc.code, exc.status_code)
        return error_response(
            message=exc.message,
            code=exc.code,
            details=exc.details,
            status_code=exc.status_code,
        )

    if isinstance(exc, ValidationError):
        message = _flatten_validation(exc.detail)
        logger.info("validation error: %s", message)
        return error_response(
            message=message or "Invalid request.",
            code="validation_error",
            details=exc.detail,
            status_code=400,
        )

    response = drf_exception_handler(exc, context)
    if response is not None:
        message = _flatten_validation(response.data)
        return error_response(
            message=message or "Request failed.",
            code="request_error",
            details=response.data,
            status_code=response.status_code,
        )

    logger.exception("unhandled error")
    return error_response(
        message="An unexpected error occurred.",
        code="server_error",
        status_code=500,
    )
