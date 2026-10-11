"""Standard API  success/error shape."""

from rest_framework import status
from rest_framework.response import Response


def success_response(data=None, message="Success", status_code=status.HTTP_200_OK):
    """
    {
        "success": true,
        "message": "...",
        "data": { ... }
    }
    """
    return Response(
        {"success": True, "message": message, "data": data},
        status=status_code,
    )


def error_response(
    message="Error",
    code="error",
    details=None,
    status_code=status.HTTP_400_BAD_REQUEST,
):
    """
    {
        "success": false,
        "error": {"code": "...", "message": "...", "details": ...}
    }
    """
    return Response(
        {
            "success": False,
            "error": {"code": code, "message": message, "details": details},
        },
        status=status_code,
    )
