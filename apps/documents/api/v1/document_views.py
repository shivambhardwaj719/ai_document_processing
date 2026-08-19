import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import parsers
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from apps.common import HttpResponseCode, ResponseHandler, ResponseMessages
from apps.documents.api.v1.document_serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
)
from apps.documents.models import DocumentStatus, FileType
from apps.documents.services.document_service import DocumentService
from apps.documents.tasks import process_document_task

logger = logging.getLogger(__name__)


class DocumentListUploadView(APIView):
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)

    def get(self, request):
        status_param = request.query_params.get("status")
        file_type_param = request.query_params.get("file_type")

        if status_param and status_param not in DocumentStatus.values:
            return ResponseHandler.error(
                code="INVALID_FILTER",
                message=ResponseMessages.INVALID_STATUS_FILTER,
                status_code=HttpResponseCode.BAD_REQUEST,
            )

        if file_type_param and file_type_param not in FileType.values:
            return ResponseHandler.error(
                code="INVALID_FILTER",
                message=ResponseMessages.INVALID_FILE_TYPE_FILTER,
                status_code=HttpResponseCode.BAD_REQUEST,
            )

        queryset = DocumentService.list_documents(
            status_filter=status_param, file_type_filter=file_type_param
        )

        paginator = PageNumberPagination()
        page_size = request.query_params.get("page_size")

        if page_size and page_size.isdigit():
            paginator.page_size = min(int(page_size), 100)

        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = DocumentListSerializer(page, many=True)

            return ResponseHandler.paginated_success(
                data=serializer.data,
                count=paginator.page.paginator.count,
                next_link=paginator.get_next_link(),
                previous_link=paginator.get_previous_link(),
                message=ResponseMessages.DOCUMENT_LIST_SUCCESS,
            )

        serializer = DocumentListSerializer(queryset, many=True)

        return ResponseHandler.success(
            data=serializer.data,
            message=ResponseMessages.DOCUMENT_LIST_SUCCESS,
        )

    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data["file"]
        document = DocumentService.create_document_from_upload(uploaded_file)

        task_id = None
        try:
            task_result = process_document_task.delay(str(document.id))
            task_id = task_result.id
            document.task_id = task_id
            document.save(update_fields=["task_id"])
            logger.info(f"Queued Celery task {task_id} for Document {document.id}")

        except Exception as celery_err:
            logger.warning(
                f"Celery broker dispatch failed for Document {document.id}: {celery_err}. Executing synchronously."
            )
            try:
                process_document_task(str(document.id))
                document.refresh_from_db()
            except Exception as sync_err:
                logger.error(f"Synchronous document processing failed: {sync_err}")

        response_data = DocumentDetailSerializer(document).data

        return ResponseHandler.accepted(
            data=response_data,
            message=ResponseMessages.DOCUMENT_UPLOAD_SUCCESS,
        )


class DocumentDetailView(APIView):
    def get(self, request, pk):
        try:
            document = DocumentService.get_document_by_id(pk)

        except (ObjectDoesNotExist, ValueError):
            return ResponseHandler.not_found(
                message=ResponseMessages.DOCUMENT_NOT_FOUND,
            )

        serializer = DocumentDetailSerializer(document)

        return ResponseHandler.success(
            data=serializer.data,
            message=ResponseMessages.DOCUMENT_DETAIL_SUCCESS,
        )
