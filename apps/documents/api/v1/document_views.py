import logging

from django.core.exceptions import ObjectDoesNotExist
from django.http import StreamingHttpResponse
from rest_framework import parsers, renderers
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
from apps.documents.services.llm_service import LLMService
from apps.documents.tasks import process_document_task

logger = logging.getLogger(__name__)


class SSERenderer(renderers.BaseRenderer):
    media_type = "text/event-stream"
    format = "event-stream"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data



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

        document.refresh_from_db()
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


class DocumentStreamView(APIView):

    renderer_classes = (SSERenderer, renderers.JSONRenderer)

    def perform_content_negotiation(self, request, force=False):
        return (SSERenderer(), "text/event-stream")

    def get(self, request, pk):

        try:
            document = DocumentService.get_document_by_id(pk)
        except (ObjectDoesNotExist, ValueError):
            return ResponseHandler.not_found(
                message=ResponseMessages.DOCUMENT_NOT_FOUND,
            )

        try:
            if document.extracted_text and document.extracted_text.strip():
                extracted_text = document.extracted_text
            else:
                from apps.documents.services.extraction_service import ExtractionService
                extracted_text = ExtractionService.extract_text_from_file(
                    document.file.path, document.file_type
                )
        except Exception as exc:
            return ResponseHandler.error(
                code="EXTRACTION_FAILED",
                message=f"Failed to extract document text for streaming: {exc}",
                status_code=HttpResponseCode.BAD_REQUEST,
            )

        template_name = request.query_params.get("template", "default")
        llm_service = LLMService()

        response = StreamingHttpResponse(
            llm_service.stream_analyze_document(extracted_text, template_name=template_name),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

