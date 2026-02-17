"""Image text extraction using EasyOCR."""

import easyocr

from app.extraction.exceptions import ExtractionError

_reader: easyocr.Reader | None = None


def _get_reader() -> easyocr.Reader:
    """Lazy-initialize EasyOCR reader (downloads model on first call)."""
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"])
    return _reader


def extract_text_from_image(path: str) -> str:
    """Extract text from an image file (PNG, JPG, JPEG).

    Args:
        path: Path to the image file.

    Returns:
        Extracted text from the image.

    Raises:
        ExtractionError: If the file is not found, corrupt, or cannot be read.
    """
    try:
        reader = _get_reader()
        results = reader.readtext(path)
    except Exception as e:
        raise ExtractionError(f"Failed to extract text from image '{path}': {e}") from e

    parts = [item[1] for item in results if item[1]]
    return "\n".join(parts)
