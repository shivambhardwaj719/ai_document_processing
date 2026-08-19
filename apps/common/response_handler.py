import logging
from typing import Any

from rest_framework import status
from rest_framework.response import Response

from apps.common.messages import ResponseMessages

logger = logging.getLogger(__name__)


class HttpResponseCode:
    OK = status.HTTP_200_OK
    ACCEPTED = status.HTTP_202_ACCEPTED
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    NOT_FOUND = status.HTTP_404_NOT_FOUND


class ResponseHandler:
    @staticmethod
    def log_response(success: bool, message: str, status_code: int):
        logger.debug(
            f"HTTP_RESPONSE :: success: {success}, code: {status_code}, message: {message}"
        )

    @staticmethod
    def success(
        data: Any = None,
        message: str = ResponseMessages.SUCCESS,
        status_code: int = HttpResponseCode.OK,
    ) -> Response:
        ResponseHandler.log_response(success=True, message=message, status_code=status_code)
        return Response(
            {
                "success": True,
                "data": data,
                "message": message,
            },
            status=status_code,
        )

    @staticmethod
    def accepted(
        data: Any = None,
        message: str = ResponseMessages.DOCUMENT_UPLOAD_SUCCESS,
    ) -> Response:
        return ResponseHandler.success(
            data=data, message=message, status_code=HttpResponseCode.ACCEPTED
        )

    @staticmethod
    def paginated_success(
        data: Any,
        count: int,
        next_link: str | None = None,
        previous_link: str | None = None,
        message: str = ResponseMessages.DOCUMENT_LIST_SUCCESS,
    ) -> Response:
        ResponseHandler.log_response(success=True, message=message, status_code=HttpResponseCode.OK)
        return Response(
            {
                "success": True,
                "count": count,
                "next": next_link,
                "previous": previous_link,
                "data": data,
                "message": message,
            },
            status=HttpResponseCode.OK,
        )

    @staticmethod
    def error(
        code: str = "BAD_REQUEST",
        message: str = ResponseMessages.BAD_REQUEST,
        status_code: int = HttpResponseCode.BAD_REQUEST,
        details: Any = None,
    ) -> Response:
        ResponseHandler.log_response(success=False, message=message, status_code=status_code)
        err_payload = {
            "code": code,
            "message": message,
        }
        if details is not None:
            err_payload["details"] = details
        return Response(
            {
                "success": False,
                "error": err_payload,
            },
            status=status_code,
        )

    @staticmethod
    def not_found(
        message: str = ResponseMessages.DOCUMENT_NOT_FOUND,
        code: str = "NOT_FOUND",
    ) -> Response:
        return ResponseHandler.error(
            code=code, message=message, status_code=HttpResponseCode.NOT_FOUND
        )
