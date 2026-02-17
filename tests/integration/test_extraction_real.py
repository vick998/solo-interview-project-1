"""Slow integration tests for real PDF and OCR extraction."""

from pathlib import Path

import pytest

from app.extraction.extractor import extract_text
from tests.conftest import TEST_DOCS


@pytest.mark.slow
def test_pdf_extraction_returns_non_empty_text(sample_pdf_path: Path) -> None:
    """PDF extraction returns non-empty text with expected keyword."""
    pdf_text = extract_text(str(sample_pdf_path))
    assert pdf_text
    assert len(pdf_text) > 0
    assert "expected_keyword" in pdf_text.lower()


@pytest.mark.slow
def test_image_extraction_returns_non_empty_text() -> None:
    """Image extraction returns non-empty text."""
    sample_png = TEST_DOCS / "sample.png"
    if not sample_png.exists():
        pytest.skip(
            f"Missing {sample_png}. Run: uv run python scripts/generate_test_docs.py"
        )
    img_text = extract_text(str(sample_png))
    assert img_text
    assert len(img_text) > 0
