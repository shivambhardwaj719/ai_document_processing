import pytest

from apps.documents.extractors.base import UnsupportedFormatError
from apps.documents.extractors.docx import DOCXExtractor
from apps.documents.extractors.factory import ExtractorFactory
from apps.documents.extractors.pdf import PDFExtractor
from apps.documents.extractors.txt import TXTExtractor
from apps.documents.models import FileType


class TestExtractors:
    def test_factory_get_txt_extractor(self):
        extractor = ExtractorFactory.get_extractor(FileType.TXT)
        assert isinstance(extractor, TXTExtractor)

    def test_factory_get_pdf_extractor(self):
        extractor = ExtractorFactory.get_extractor(FileType.PDF)
        assert isinstance(extractor, PDFExtractor)

    def test_factory_get_docx_extractor(self):
        extractor = ExtractorFactory.get_extractor(FileType.DOCX)
        assert isinstance(extractor, DOCXExtractor)

    def test_factory_invalid_file_type(self):
        with pytest.raises(UnsupportedFormatError):
            ExtractorFactory.get_extractor("invalid_type")

    def test_txt_extractor_extract_text(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World! This is a test document text.", encoding="utf-8")
        extractor = TXTExtractor()
        extracted = extractor.extract_text(str(test_file))
        assert "Hello World!" in extracted
