import json
import logging
import re
import time
from typing import Any

import httpx
from django.conf import settings
from pydantic import ValidationError as PydanticValidationError

from apps.documents.schemas.llm_response import DocumentAnalysisSchema

logger = logging.getLogger(__name__)

DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """You are an expert Document Analysis AI system.
Your task is to analyze the provided document text and generate a structured JSON analysis.

You MUST respond with a valid raw JSON object matching EXACTLY the following JSON schema:
{
  "title": "<Concise, relevant document title>",
  "summary": "<A 2-4 sentence executive summary of the document content>",
  "keywords": ["<keyword1>", "<keyword2>", "<keyword3>"],
  "language": "<Language of text, e.g. English, French>",
  "word_count": <Integer word count of the document text>
}

CRITICAL REQUIREMENTS:
1. Base your analysis ONLY on the provided text. Do not invent or hallucinate information.
2. The 'keywords' field MUST be a JSON array of relevant strings.
3. The 'word_count' MUST be an integer representing the exact or closely estimated word count of the input.
4. Output ONLY valid raw JSON. Do NOT include markdown code block formatting (such as ```json ... ```), preamble, or commentary.
"""


def build_analysis_user_prompt(text: str, max_chars: int = 50000) -> str:
    truncated_text = text[:max_chars]
    if len(text) > max_chars:
        truncated_text += "\n\n[... Text truncated for context limit ...]"

    return f"Analyze the following document text and produce the structured JSON output:\n\n---\n{truncated_text}\n---"


class LLMServiceError(Exception):
    """Base exception for LLM API integration errors."""

    pass


class LLMAuthError(LLMServiceError):
    """Raised when LLM API key or authentication fails (401/403)."""

    pass


class LLMTimeoutError(LLMServiceError):
    """Raised when LLM API call times out."""

    pass


class LLMValidationError(LLMServiceError):
    """Raised when LLM response fails Pydantic schema validation."""

    pass


class LLMService:
    """
    Production-ready LLM Service handling structured analysis, retries,
    timeout, Pydantic validation, and mock fallbacks.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ):
        self.api_key = api_key or getattr(settings, "LLM_API_KEY", "mock-api-key")
        self.base_url = (
            base_url or getattr(settings, "LLM_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        self.model = model or getattr(settings, "LLM_MODEL", "gpt-4o-mini")
        self.timeout = timeout or getattr(settings, "LLM_TIMEOUT", 30)
        self.max_retries = max_retries or getattr(settings, "LLM_MAX_RETRIES", 3)

    def is_mock_mode(self) -> bool:
        return (
            not self.api_key
            or self.api_key.startswith("mock")
            or self.api_key == "mock-api-key-for-local-testing"
        )

    def _strip_json_fences(self, content: str) -> str:
        """Strip markdown ```json ... ``` code fences from raw LLM output if present."""
        content = content.strip()
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            return match.group(1).strip()

        match_raw = re.search(r"\{.*\}", content, re.DOTALL)

        if match_raw:
            return match_raw.group(0).strip()

        return content

    def generate_mock_analysis(self, extracted_text: str) -> dict[str, Any]:
        """
        Generate a realistic, deterministic mock analysis response when offline or mock key is set.
        """
        words = extracted_text.split()
        word_count = len(words)
        preview = " ".join(words[:40]) if words else "Empty Document"

        unique_words = list(
            dict.fromkeys([w.strip(".,;:!?()[]\"'").title() for w in words if len(w) > 4])
        )
        keywords = unique_words[:5] if unique_words else ["Document", "Processing", "Analysis"]

        mock_data = {
            "title": f"Document Summary ({keywords[0] if keywords else 'Analysis'})",
            "summary": f"This document covers key aspects of {', '.join(keywords[:3])}. Content preview: {preview}...",
            "keywords": keywords,
            "language": "English",
            "word_count": word_count,
        }
        schema_obj = DocumentAnalysisSchema(**mock_data)

        return schema_obj.model_dump()

    def analyze_document(self, extracted_text: str) -> dict[str, Any]:
        """
        Analyze document text and return validated structured JSON object.

        :param extracted_text: Text extracted from PDF/DOCX/TXT file.
        :return: Dict containing title, summary, keywords, language, word_count.
        :raises LLMServiceError: If retries are exhausted or non-retryable error occurs.
        """
        if not extracted_text or not extracted_text.strip():
            raise LLMValidationError("Cannot analyze empty document text.")

        if self.is_mock_mode():
            logger.info("LLMService operating in MOCK mode. Returning mock analysis.")
            return self.generate_mock_analysis(extracted_text)

        system_prompt = DOCUMENT_ANALYSIS_SYSTEM_PROMPT
        user_prompt = build_analysis_user_prompt(extracted_text)

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"
        last_exception = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"LLM API request attempt {attempt}/{self.max_retries} to {url}")

                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, json=payload, headers=headers)

                if response.status_code in (401, 403):
                    logger.error(
                        f"LLM API Authentication failed: {response.status_code} - {response.text}"
                    )
                    raise LLMAuthError(
                        f"LLM API Authentication failed with status {response.status_code}."
                    )

                if response.status_code == 400:
                    logger.error(f"LLM API Bad Request: {response.text}")
                    raise LLMValidationError(f"Invalid request sent to LLM API: {response.text}")

                if response.status_code != 200:
                    err_msg = f"LLM API error status {response.status_code}: {response.text}"
                    logger.warning(err_msg)
                    raise LLMServiceError(err_msg)

                res_data = response.json()
                raw_content = res_data["choices"][0]["message"]["content"]
                clean_json_str = self._strip_json_fences(raw_content)

                try:
                    parsed_json = json.loads(clean_json_str)
                except json.JSONDecodeError as json_err:
                    logger.warning(
                        f"Malformed JSON returned by LLM on attempt {attempt}: {json_err}"
                    )
                    raise LLMValidationError(f"Malformed JSON from LLM: {json_err}")

                validated_obj = DocumentAnalysisSchema(**parsed_json)
                logger.info(
                    f"Successfully generated and validated LLM document analysis on attempt {attempt}"
                )
                return validated_obj.model_dump()

            except LLMAuthError:
                raise

            except httpx.TimeoutException as timeout_err:
                last_exception = LLMTimeoutError(
                    f"LLM request timed out after {self.timeout}s: {timeout_err}"
                )
                logger.warning(f"Attempt {attempt} timed out.")

            except PydanticValidationError as val_err:
                last_exception = LLMValidationError(
                    f"LLM response schema validation failed: {val_err}"
                )
                logger.warning(f"Attempt {attempt} schema validation failed: {val_err}")

            except Exception as exc:
                last_exception = exc
                logger.warning(f"Attempt {attempt} failed with exception: {exc}")

            if attempt < self.max_retries:
                backoff_sec = 2**attempt
                logger.info(f"Retrying LLM call in {backoff_sec} seconds...")
                time.sleep(backoff_sec)

        raise LLMServiceError(
            f"LLM Service failed after {self.max_retries} retries. Last error: {last_exception}"
        )
