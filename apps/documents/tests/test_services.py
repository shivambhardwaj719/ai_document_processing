import pytest

from apps.documents.prompts.templates import get_prompt_template
from apps.documents.services.llm_service import LLMService, LLMValidationError


class TestLLMService:
    def test_mock_mode_detection(self):
        service = LLMService(api_key="mock-api-key")
        assert service.is_mock_mode() is True

        service_real = LLMService(api_key="sk-proj-real-key-12345")
        assert service_real.is_mock_mode() is False

    def test_analyze_document_mock_mode(self):
        service = LLMService(api_key="mock-api-key")
        text = "This is a sample resume for John Doe. Skills include Python, Django, and Celery."
        res = service.analyze_document(text)
        assert res["title"] is not None
        assert res["document_category"] in ["Resume / CV", "General Document", "Technical Specification"]
        assert "confidence_score" in res
        assert "keywords" in res

    def test_analyze_empty_document_raises_validation_error(self):
        service = LLMService(api_key="mock-api-key")
        with pytest.raises(LLMValidationError):
            service.analyze_document("")

    def test_stream_analyze_document(self):
        service = LLMService(api_key="mock-api-key")
        generator = service.stream_analyze_document("Sample text for streaming test")
        chunks = list(generator)
        assert len(chunks) > 0
        assert any("data: " in chunk for chunk in chunks)

    def test_prompt_template_loader(self):
        default_prompt = get_prompt_template("default")
        assert "Document Intelligence" in default_prompt

        resume_prompt = get_prompt_template("resume")
        assert "candidate skills" in resume_prompt.lower()

        contract_prompt = get_prompt_template("contract")
        assert "legal obligations" in contract_prompt.lower()
