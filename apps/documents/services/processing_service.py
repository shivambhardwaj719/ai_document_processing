import logging
from typing import cast

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from apps.documents.extractors.base import ExtractionError
from apps.documents.models import Document, DocumentStatus
from apps.documents.services.extraction_service import ExtractionService
from apps.documents.services.llm_service import LLMService, LLMServiceError
from apps.documents.utils.logging import structured_logger

logger = logging.getLogger(__name__)


class ProcessingService:
    """
    Orchestrates full document processing flow:
    1. Update status to PROCESSING
    2. Extract text via ExtractionService
    3. Perform structured analysis via LLMService
    4. Save results and update status to COMPLETED (or FAILED on error)
    """

    @classmethod
    def process_document(cls, document_id: str, task_id: str | None = None) -> Document:
        try:
            doc = cast(Document, Document.objects.get(id=document_id))
        except ObjectDoesNotExist:
            logger.error(f"Processing failed: Document ID {document_id} not found.")
            raise ValueError(f"Document ID {document_id} does not exist.")

        doc.status = DocumentStatus.PROCESSING
        doc.processing_started_at = timezone.now()
        if task_id:
            doc.task_id = task_id
        doc.save(update_fields=["status", "processing_started_at", "task_id", "updated_at"])

        structured_logger.info(
            "processing_started",
            document_id=str(doc.id),
            task_id=task_id,
            filename=doc.original_filename,
            file_type=doc.file_type,
        )

        try:
            file_path = doc.file.path
            extracted_text = ExtractionService.extract_text_from_file(file_path, doc.file_type)

            doc.extracted_text = extracted_text
            doc.save(update_fields=["extracted_text", "updated_at"])

            structured_logger.info(
                "text_extracted",
                document_id=str(doc.id),
                char_count=len(extracted_text),
            )

            llm_service = LLMService()
            structured_logger.info("llm_request_started", document_id=str(doc.id))

            analysis_result = llm_service.analyze_document(extracted_text)

            doc.llm_response = analysis_result
            doc.status = DocumentStatus.COMPLETED
            doc.error_message = None
            doc.processing_completed_at = timezone.now()
            doc.save(
                update_fields=[
                    "llm_response",
                    "status",
                    "error_message",
                    "processing_completed_at",
                    "updated_at",
                ]
            )

            duration = (
                (doc.processing_completed_at - doc.processing_started_at).total_seconds()
                if doc.processing_started_at
                else 0
            )

            structured_logger.info(
                "processing_completed",
                document_id=str(doc.id),
                task_id=task_id,
                duration_seconds=round(duration, 2),
                status=doc.status,
            )
            return doc

        except (ExtractionError, LLMServiceError, Exception) as exc:
            error_msg = str(exc)
            logger.exception(f"Document processing failed for ID {doc.id}: {error_msg}")

            doc.status = DocumentStatus.FAILED
            doc.error_message = error_msg
            doc.processing_completed_at = timezone.now()
            doc.save(
                update_fields=[
                    "status",
                    "error_message",
                    "processing_completed_at",
                    "updated_at",
                ]
            )

            structured_logger.error(
                "processing_failed",
                document_id=str(doc.id),
                task_id=task_id,
                error=error_msg,
            )
            return doc
