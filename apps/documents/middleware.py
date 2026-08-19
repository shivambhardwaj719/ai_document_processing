import logging

from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger("apps.documents")





def custom_exception_handler(exc, context):

    response = exception_handler(exc, context)

    if response is not None:
        error_code = "VALIDATION_ERROR" if isinstance(exc, ValidationError) else "API_ERROR"
        if hasattr(exc, "default_code"):
            error_code = str(exc.default_code).upper()

        message = response.data
        if isinstance(response.data, dict):

            if "detail" in response.data:
                message = response.data["detail"]

            elif "file" in response.data:
                file_err = response.data["file"]
                message = file_err[0] if isinstance(file_err, list) else str(file_err)

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
            },
        }
        return response

    logger.exception("Unhandled server error: %s", exc)
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again later.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
