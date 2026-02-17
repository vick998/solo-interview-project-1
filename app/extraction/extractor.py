"""Router that selects PDF or OCR extraction by file type."""

from pathlib import Path

from app.extraction.exceptions import ExtractionError, UnsupportedFileTypeError
from app.extraction.ocr import extract_text_from_image
from app.extraction.pdf import extract_text_from_pdf

PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def extract_text(file_path: str) -> str:
    """Extract text from a file based on its type.

    Args:
        file_path: Path to the file (PDF or image).

    Returns:
        Extracted text from the file.

    Raises:
        UnsupportedFileTypeError: If the file extension is not supported.
        ExtractionError: If extraction fails (propagated from pdf/ocr modules).
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix in PDF_EXTENSIONS:
        return extract_text_from_pdf(file_path)
    if suffix in IMAGE_EXTENSIONS:
        return extract_text_from_image(file_path)

    raise UnsupportedFileTypeError(
        f"Unsupported file type: '{suffix}'. Supported: {PDF_EXTENSIONS | IMAGE_EXTENSIONS}"
    )
