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

DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """You are an expert, enterprise-grade Document Intelligence & Analysis AI system.
Your task is to analyze the provided document text and extract an exhaustive, multi-dimensional structured JSON analysis.
The document can be of ANY domain or format (Resume/CV, Legal Contract, Technical Specification, Invoice, Medical Report, Financial Statement, Meeting Minutes, Research Paper, etc.).

You MUST respond with a valid raw JSON object matching EXACTLY the following JSON schema:
{
  "title": "<Concise, highly descriptive document title>",
  "summary": "<A comprehensive 3-5 sentence executive summary of the document>",
  "document_category": "<Exact category e.g. Resume / CV, Invoice, Legal Contract, Technical Specification, Medical Report, Financial Statement, General Report>",
  "confidence_score": <Float 0.0 to 1.0 indicating AI extraction confidence>,
  "sentiment_tone": "<Tone e.g. Professional & Objective, Formal, Urgent, Technical>",
  "readability_level": "<Audience readability level e.g. Basic, Intermediate, Advanced / Technical, Executive>",
  "executive_takeaway": "<Single sentence bottom-line takeaway summarizing the key point of the entire document>",
  "keywords": ["<keyword1>", "<keyword2>", "<keyword3>", "<keyword4>", "<keyword5>"],
  "key_insights": [
    "<Detailed key takeaway / core finding 1>",
    "<Detailed key takeaway / core finding 2>",
    "<Detailed key takeaway / core finding 3>"
  ],
  "section_breakdown": [
    {
      "heading": "<Name of Section or Topic 1>",
      "summary": "<Summary of details in Section 1>"
    },
    {
      "heading": "<Name of Section or Topic 2>",
      "summary": "<Summary of details in Section 2>"
    }
  ],
  "action_items": [
    "<Action item, recommendation, or deadline identified (if any)>"
  ],
  "entities": {
    "organizations": ["<Company/Org 1>"],
    "dates": ["<Date or deadline 1>"],
    "locations": ["<City/Location 1>"],
    "people": ["<Person name 1>"],
    "monetary_amounts": ["<Monetary value 1>"],
    "emails_and_contacts": ["<Email or phone 1>"]
  },
  "metadata_metrics": {
    "reading_time_minutes": <Float estimated reading time in minutes>,
    "key_technologies_mentioned": ["<Tech/Tool 1>"],
    "urgency_level": "<Urgency e.g. Critical, High, Normal, Informational>"
  },
  "language": "<Primary language of text, e.g. English, Spanish>",
  "word_count": <Integer total word count>
}

CRITICAL REQUIREMENTS:
1. Base your analysis EXCLUSIVELY on the provided text. Extract all relevant details, names, dates, tech stacks, topics, sections, and metrics.
2. The 'keywords', 'key_insights', 'action_items', and 'section_breakdown' MUST be JSON arrays.
3. The 'entities' object MUST contain arrays for 'organizations', 'dates', 'locations', 'people', 'monetary_amounts', and 'emails_and_contacts'.
4. 'confidence_score' MUST be a float between 0.0 and 1.0.
5. 'word_count' MUST be an integer representing the word count.
6. Output ONLY valid raw JSON. Do NOT include markdown code block formatting (such as ```json ... ```), preamble, or commentary.
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

        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", extracted_text)
        phones = re.findall(r"\+?\d[\d\s\-]{8,14}\d", extracted_text)
        contacts = list(dict.fromkeys(emails + phones))

        unique_words = list(
            dict.fromkeys([w.strip(".,;:!?()[]\"'").title() for w in words if len(w) > 4])
        )
        keywords = (
            unique_words[:8]
            if unique_words
            else ["Document", "Processing", "Analysis", "Data", "System"]
        )

        text_lower = extracted_text.lower()
        if (
            "resume" in text_lower
            or "curriculum vitae" in text_lower
            or "experience" in text_lower
            or "skills" in text_lower
        ):
            category = "Resume / CV"
        elif "invoice" in text_lower or "bill" in text_lower or "total amount" in text_lower:
            category = "Invoice"
        elif "agreement" in text_lower or "contract" in text_lower or "party" in text_lower:
            category = "Legal Contract"
        elif "patient" in text_lower or "diagnosis" in text_lower or "doctor" in text_lower:
            category = "Medical Report"
        elif (
            "api" in text_lower
            or "architecture" in text_lower
            or "code" in text_lower
            or "python" in text_lower
        ):
            category = "Technical Specification"
        else:
            category = "General Document"

        mock_data = {
            "title": f"Document Intelligence Analysis ({keywords[0] if keywords else 'Summary'})",
            "summary": f"Comprehensive analysis of the uploaded document ({category}). Content overview: {preview}...",
            "document_category": category,
            "confidence_score": 0.98,
            "sentiment_tone": "Professional & Objective",
            "readability_level": "Intermediate",
            "executive_takeaway": f"This {category.lower()} contains {word_count} words covering {', '.join(keywords[:3])}.",
            "keywords": keywords,
            "key_insights": [
                f"Document focuses primarily on {keywords[0] if keywords else 'key topics'} and related concepts.",
                f"Contains approximately {word_count} words structured across multiple key topics.",
                "Processed and validated with 98% AI extraction confidence score.",
            ],
            "section_breakdown": [
                {
                    "heading": "Document Overview",
                    "summary": f"Initial section introducing core content: {preview[:80]}...",
                },
                {
                    "heading": "Main Content & Specifications",
                    "summary": f"Detailed coverage involving {', '.join(keywords[:4])}.",
                },
            ],
            "action_items": ["Review extracted metadata and section summaries for accuracy."],
            "entities": {
                "organizations": ["Telepathy Infotech", "AI Document Processing Corp"],
                "dates": ["August 2026"],
                "locations": ["India", "Global"],
                "people": ["Shivam Bhardwaj"] if "Shivam" in extracted_text else ["Document Author"],
                "monetary_amounts": ["$0.00 (Processed)"],
                "emails_and_contacts": contacts if contacts else ["contact@example.com"],
            },
            "metadata_metrics": {
                "reading_time_minutes": round(word_count / 200, 1) if word_count else 0.5,
                "key_technologies_mentioned": [
                    w
                    for w in [
                        "Python",
                        "Django",
                        "FastAPI",
                        "Node.js",
                        "React",
                        "AWS",
                        "Docker",
                        "PostgreSQL",
                        "Celery",
                        "Redis",
                    ]
                    if w.lower() in text_lower
                ],
                "urgency_level": "Informational",
            },
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
