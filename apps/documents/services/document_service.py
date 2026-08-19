import logging
from typing import Any, cast

from django.db import transaction

from apps.documents.models import Document, DocumentStatus
from apps.documents.utils.file_validation import (
    compute_file_hash,
    generate_stored_filename,
    validate_uploaded_file,
)

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service layer for Document database lifecycle, uploads, and query operations.
    """

    @staticmethod
    def create_document_from_upload(uploaded_file: Any) -> Document:
        """
        Validate uploaded file and save Document record to DB.
        """
        # Validate file properties and header magic bytes
        validated_meta = validate_uploaded_file(uploaded_file)

        # Compute content hash for SHA-256 integrity / deduplication tracking
        content_hash = compute_file_hash(uploaded_file)

        original_name = validated_meta["original_filename"]
        stored_name = generate_stored_filename(original_name)
        file_ext = validated_meta["ext"]

        with transaction.atomic():
            document = cast(
                Document,
                Document.objects.create(
                    original_filename=original_name,
                    stored_filename=stored_name,
                    file=uploaded_file,
                    file_type=file_ext,
                    file_size=validated_meta["size"],
                    mime_type=validated_meta["mime_type"],
                    content_hash=content_hash,
                    status=DocumentStatus.PENDING,
                ),
            )

        logger.info(
            f"Created Document ID {document.id} for file '{original_name}' (hash: {content_hash[:8]}...)"
        )
        return document

    @staticmethod
    def get_document_by_id(document_id: Any) -> Document:
        """
        Fetch single document by primary key UUID.
        """
        return cast(Document, Document.objects.get(id=document_id))

    @staticmethod
    def list_documents(status_filter: str | None = None, file_type_filter: str | None = None):
        """
        Query documents queryset with optional filtering and pre-indexed ordering.
        N+1 safe queryset.
        """
        qs = Document.objects.all()

        if status_filter:
            qs = qs.filter(status=status_filter)
        if file_type_filter:
            qs = qs.filter(file_type=file_type_filter)

        return qs.order_by("-created_at")
