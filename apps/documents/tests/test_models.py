import pytest

from apps.documents.models import Document, DocumentStatus, FileType


@pytest.mark.django_db
class TestDocumentModel:
    def test_create_document_success(self, dummy_txt_file):
        doc = Document.objects.create(
            file=dummy_txt_file,
            original_filename="sample_resume.txt",
            stored_filename="stored_sample_resume.txt",
            file_size=100,
            file_type=FileType.TXT,
            mime_type="text/plain",
            content_hash="1234567890abcdef" * 4,
        )
        assert doc.id is not None
        assert doc.status == DocumentStatus.PENDING
        assert f"Document({doc.id}" in str(doc)

    def test_document_status_transitions(self, sample_document):
        assert sample_document.status == DocumentStatus.COMPLETED
        sample_document.status = DocumentStatus.FAILED
        sample_document.error_message = "Test error"
        sample_document.save()
        assert sample_document.status == DocumentStatus.FAILED
        assert sample_document.error_message == "Test error"
