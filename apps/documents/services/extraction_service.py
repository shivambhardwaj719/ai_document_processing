import logging
import os

from apps.documents.extractors import ExtractorFactory
from apps.documents.extractors.base import ExtractionError

logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Service responsible for orchestrating document text extraction.
    """

    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> str:
        """
        Extract text from file using ExtractorFactory.

        :param file_path: Absolute path to local file.
        :param file_type: Document extension or format (e.g. pdf, docx, txt).
        :return: Normalized extracted text.
        :raises ExtractionError: If extraction fails or document is empty/corrupted.
        """
        if not os.path.exists(file_path):
            raise ExtractionError(f"File not found on disk at path: {file_path}")

        extractor = ExtractorFactory.get_extractor(file_type)
        logger.info(f"Extracting text from file '{file_path}' using {extractor.__class__.__name__}")
        extracted_text = extractor.extract_text(file_path)
        logger.info(f"Successfully extracted {len(extracted_text)} characters from '{file_path}'")
        return extracted_text
