from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class PlatformAPIError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "PLATFORM_ERROR"
    default_detail = "The request could not be processed."

    def __init__(self, message=None, *, code=None, details=None, status_code=None):
        super().__init__(detail=message or self.default_detail, code=code or self.default_code)
        self.message = message or self.default_detail
        self.code = code or self.default_code
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code


class GameAlreadyFinished(PlatformAPIError):
    default_code = "GAME_ALREADY_FINISHED"
    default_detail = "This game session is already finished."


class InvalidGameAnswer(PlatformAPIError):
    default_code = "INVALID_GAME_ANSWER"
    default_detail = "This answer cannot be accepted for the current game state."


def _normalize_code(value):
    return str(value or "ERROR").upper().replace(" ", "_").replace("-", "_")


def _message_from_data(data):
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    if isinstance(data, list) and data:
        return str(data[0])
    if data:
        return "Validation error."
    return "An unexpected error occurred."


def platform_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, PlatformAPIError):
        return Response(
            {
                "code": _normalize_code(exc.code),
                "message": exc.message,
                "details": exc.details,
            },
            status=exc.status_code,
        )

    if response is None:
        if isinstance(exc, Http404):
            return Response(
                {
                    "code": "NOT_FOUND",
                    "message": "The requested resource was not found.",
                    "details": {},
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        return None

    code = getattr(exc, "default_code", None)
    if not code and isinstance(response.data, dict):
        detail = response.data.get("detail")
        code = getattr(detail, "code", None)

    response.data = {
        "code": _normalize_code(code or response.status_code),
        "message": _message_from_data(response.data),
        "details": response.data,
    }
    return response
