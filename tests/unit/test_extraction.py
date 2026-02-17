"""Unit tests for document extraction (mocked; no real PDF/OCR)."""

from unittest.mock import patch

import pytest

from app.extraction.exceptions import ExtractionError, UnsupportedFileTypeError
from app.extraction.extractor import extract_text


def test_unsupported_file_type_raises() -> None:
    """Unsupported file type (.txt) raises UnsupportedFileTypeError."""
    with pytest.raises(UnsupportedFileTypeError, match="Unsupported file type"):
        extract_text("test_docs/foo.txt")


def test_nonexistent_file_raises() -> None:
    """Nonexistent file raises ExtractionError."""
    with pytest.raises(ExtractionError):
        extract_text("nonexistent.pdf")


def test_file_type_routing_pdf_calls_pdf_extractor() -> None:
    """PDF extension routes to extract_text_from_pdf."""
    with patch("app.extraction.extractor.extract_text_from_pdf") as mock_pdf:
        mock_pdf.return_value = "extracted"
        result = extract_text("/tmp/sample.pdf")
        mock_pdf.assert_called_once_with("/tmp/sample.pdf")
        assert result == "extracted"


def test_file_type_routing_image_calls_ocr_extractor() -> None:
    """Image extension routes to extract_text_from_image."""
    with patch("app.extraction.extractor.extract_text_from_image") as mock_ocr:
        mock_ocr.return_value = "ocr text"
        result = extract_text("/tmp/sample.png")
        mock_ocr.assert_called_once_with("/tmp/sample.png")
        assert result == "ocr text"


def test_file_type_routing_jpg_calls_ocr_extractor() -> None:
    """JPG extension routes to extract_text_from_image."""
    with patch("app.extraction.extractor.extract_text_from_image") as mock_ocr:
        mock_ocr.return_value = "jpg text"
        result = extract_text("/tmp/photo.jpg")
        mock_ocr.assert_called_once_with("/tmp/photo.jpg")
        assert result == "jpg text"
