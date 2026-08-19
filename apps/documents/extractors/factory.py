import os

from apps.documents.extractors.base import BaseExtractor, UnsupportedFormatError
from apps.documents.extractors.docx import DOCXExtractor
from apps.documents.extractors.pdf import PDFExtractor
from apps.documents.extractors.txt import TXTExtractor


class ExtractorFactory:
    """
    Factory pattern for creating format-specific extractors.
    """

    _EXTRACTORS = {
        "pdf": PDFExtractor,
        ".pdf": PDFExtractor,
        "docx": DOCXExtractor,
        ".docx": DOCXExtractor,
        "txt": TXTExtractor,
        ".txt": TXTExtractor,
    }

    @classmethod
    def get_extractor(cls, file_type_or_extension: str) -> BaseExtractor:
        key = file_type_or_extension.lower()
        extractor_cls = cls._EXTRACTORS.get(key)
        if not extractor_cls:
            raise UnsupportedFormatError(
                f"No extractor registered for document type/extension: {file_type_or_extension}"
            )
        return extractor_cls()

    @classmethod
    def get_extractor_for_file(cls, file_path: str) -> BaseExtractor:
        ext = os.path.splitext(file_path)[1].lower()
        return cls.get_extractor(ext)
