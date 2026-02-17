"""PDF text extraction using PyMuPDF."""

import fitz

from app.extraction.exceptions import ExtractionError


def extract_text_from_pdf(path: str) -> str:
    """Extract text from a PDF file.

    Args:
        path: Path to the PDF file.

    Returns:
        Extracted text from all pages, concatenated.

    Raises:
        ExtractionError: If the file is not found, corrupt, or cannot be read.
    """
    try:
        doc = fitz.open(path)
    except Exception as e:
        raise ExtractionError(f"Failed to open PDF '{path}': {e}") from e

    try:
        parts = []
        for page in doc:
            text = page.get_text()
            if text:
                parts.append(text)
        return "\n".join(parts)
    finally:
        doc.close()
