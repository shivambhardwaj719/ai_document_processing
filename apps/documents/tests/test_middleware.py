from django.http import HttpResponse
from django.test import RequestFactory
from rest_framework.exceptions import ValidationError

from apps.documents.middleware import RequestLoggingMiddleware, custom_exception_handler


class TestMiddleware:
    def test_request_logging_middleware_success(self):
        factory = RequestFactory()
        request = factory.get("/api/v1/documents/")
        middleware = RequestLoggingMiddleware(lambda req: HttpResponse("OK", status=200))
        response = middleware(request)
        assert response.status_code == 200

    def test_custom_exception_handler_validation_error(self):
        exc = ValidationError({"file": ["Unsupported file format."]})
        response = custom_exception_handler(exc, context={})
        assert response.status_code == 400
        assert response.data["success"] is False
        assert "code" in response.data["error"]
