import logging
import time

from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from apps.documents.utils.logging import structured_logger

logger = logging.getLogger("apps.documents")


class RequestLoggingMiddleware:
    """
    Middleware to record structured JSON log entries for every HTTP request/response cycle,
    including HTTP method, path, remote IP, status code, and latency in milliseconds.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        client_ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "unknown"))
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        log_data = {
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "latency_ms": duration_ms,
            "client_ip": client_ip,
            "query_params": dict(request.GET.items()),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        }

        if response.status_code >= 500:
            structured_logger.error("http_request_failed", **log_data)
        elif response.status_code >= 400:
            structured_logger.warning("http_request_warning", **log_data)
        else:
            structured_logger.info("http_request_success", **log_data)

        return response


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
