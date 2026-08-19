from abc import ABC, abstractmethod


class ExtractionError(Exception):
    """Base exception for document text extraction failures."""

    pass


class EmptyDocumentError(ExtractionError):
    """Raised when extracted document text is completely empty or blank."""

    pass


class CorruptedFileError(ExtractionError):
    """Raised when document file structure is damaged or unreadable."""

    pass


class PasswordProtectedError(ExtractionError):
    """Raised when PDF or DOCX file requires password authorization."""

    pass


class UnsupportedFormatError(ExtractionError):
    """Raised when no extractor is available for the given format."""

    pass


class BaseExtractor(ABC):
    """
    Abstract Base Class for text extractors.
    All format-specific extractors must inherit from this class.
    """

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from file path and return normalized string.

        :param file_path: Absolute path to the local document file.
        :return: Extracted text string.
        :raises ExtractionError: If extraction fails or document is invalid.
        """
        pass
