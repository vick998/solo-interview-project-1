"""Custom exceptions for document extraction."""


class ExtractionError(Exception):
    """Raised when text extraction fails (file not found, corrupt, etc.)."""

    pass


class UnsupportedFileTypeError(Exception):
    """Raised when the file type is not supported for extraction."""

    pass
