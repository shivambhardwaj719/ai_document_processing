import logging

from apps.documents.extractors.base import (
    BaseExtractor,
    CorruptedFileError,
    EmptyDocumentError,
)

logger = logging.getLogger(__name__)


class TXTExtractor(BaseExtractor):
    """
    Text extractor implementation for plain text (.txt) documents.
    Handles multiple encodings (UTF-8, UTF-8-SIG, Latin-1, CP1252).
    """

    def extract_text(self, file_path: str) -> str:
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None
        last_error = None

        for enc in encodings:
            try:
                with open(file_path, encoding=enc) as f:
                    content = f.read()
                    break

            except (UnicodeDecodeError, UnicodeError) as err:
                last_error = err
                continue

            except Exception as exc:
                logger.error("Failed opening text file %s: %s", file_path, exc)
                raise CorruptedFileError(f"Cannot read text file: {exc}")

        if content is None:
            raise CorruptedFileError(
                f"Could not decode text file with standard encodings: {last_error}"
            )

        content = content.replace("\x00", "").strip()
        if not content:
            raise EmptyDocumentError("TXT file is empty or contains only whitespace.")

        return content
