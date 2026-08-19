import logging

from pypdf import PdfReader
from pypdf.errors import PyPdfError, WrongPasswordError

from apps.documents.extractors.base import (
    BaseExtractor,
    CorruptedFileError,
    EmptyDocumentError,
    ExtractionError,
    PasswordProtectedError,
)

logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractor):
    """
    Text extractor implementation for PDF documents.
    Uses pypdf.
    """

    def extract_text(self, file_path: str) -> str:
        try:
            reader = PdfReader(file_path)

            if reader.is_encrypted:
                try:
                    decrypted = reader.decrypt("")
                    if not decrypted:
                        raise PasswordProtectedError("PDF document is password protected.")

                except WrongPasswordError:
                    raise PasswordProtectedError("PDF document is password protected.")

                except Exception as e:
                    raise PasswordProtectedError(f"Encrypted PDF access failed: {e}")

            text_content = []

            for i, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        text_content.append(page_text.strip())

                except Exception as page_err:
                    logger.warning(
                        "Page %d text extraction warning in %s: %s", i + 1, file_path, page_err
                    )

            full_text = "\n\n".join(text_content).strip()
            if not full_text:
                raise EmptyDocumentError("PDF document contains no extractable text.")

            return full_text

        except (EmptyDocumentError, PasswordProtectedError):
            raise

        except PyPdfError as pypdf_err:
            logger.error("Corrupted PDF file %s: %s", file_path, pypdf_err)
            raise CorruptedFileError(f"PDF file is damaged or malformed: {pypdf_err}")

        except Exception as exc:
            logger.error("Unexpected PDF extraction error for %s: %s", file_path, exc)
            raise ExtractionError(f"Failed to extract PDF text: {exc}")
