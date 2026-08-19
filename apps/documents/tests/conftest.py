import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import Document, DocumentStatus, FileType


@pytest.fixture
def dummy_txt_file():
    content = b"Candidate Name: John Doe\nSkills: Python, Django, PostgreSQL, Celery, Docker\nExperience: 5 years software engineer."
    return SimpleUploadedFile("sample_resume.txt", content, content_type="text/plain")


@pytest.fixture
def dummy_pdf_file():
    content = b"%PDF-1.4 sample pdf content for extraction test"
    return SimpleUploadedFile("sample_document.pdf", content, content_type="application/pdf")


@pytest.fixture
def sample_document(db, dummy_txt_file):
    doc = Document.objects.create(
        file=dummy_txt_file,
        original_filename="sample_resume.txt",
        stored_filename="sample_resume_stored.txt",
        file_size=len(dummy_txt_file.read()),
        file_type=FileType.TXT,
        mime_type="text/plain",
        status=DocumentStatus.COMPLETED,
        content_hash="a" * 64,
        llm_response={
            "title": "Document Analysis",
            "summary": "Sample summary",
            "document_category": "Resume / CV",
            "confidence_score": 0.95,
            "sentiment_tone": "Professional",
            "readability_level": "Intermediate",
            "executive_takeaway": "Candidate is qualified.",
            "keywords": ["Python", "Django"],
            "key_insights": ["Insight 1"],
            "section_breakdown": [],
            "action_items": [],
            "entities": {"organizations": ["Tech Corp"]},
            "metadata_metrics": {"reading_time_minutes": 1.0},
            "language": "English",
            "word_count": 20,
        },
    )
    return doc
