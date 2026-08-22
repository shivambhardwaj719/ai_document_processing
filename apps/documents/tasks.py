import logging

from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from django.db import OperationalError

from apps.documents.models import Document
from apps.documents.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="apps.documents.tasks.process_document_task",
)
def process_document_task(self, document_id: str):
    """
    Celery background task for asynchronous document extraction and LLM analysis.
    """
    task_id = self.request.id
    logger.info(f"Celery task {task_id} starting execution for Document ID: {document_id}")

    try:
        doc = Document.objects.get(id=document_id)

    except ObjectDoesNotExist:
        logger.error(f"Task {task_id} aborted: Document {document_id} not found in DB.")
        return

    if self.request.retries > 0:
        doc.retry_count = self.request.retries
        doc.save(update_fields=["retry_count"])

    try:
        # Call ProcessingService to handle the entire document processing pipeline
        ProcessingService.process_document(document_id, task_id=task_id)

    except OperationalError as db_err:
        logger.warning(f"Transient DB error on task {task_id}: {db_err}. Retrying...")
        raise self.retry(exc=db_err, countdown=2**self.request.retries * 5)

    except Exception as exc:
        logger.exception(
            f"Unhandled error in Celery task {task_id} for Document {document_id}: {exc}"
        )
