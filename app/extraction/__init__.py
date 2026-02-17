"""Document extraction module."""

from app.extraction.exceptions import ExtractionError, UnsupportedFileTypeError
from app.extraction.extractor import extract_text

__all__ = ["extract_text", "ExtractionError", "UnsupportedFileTypeError"]
