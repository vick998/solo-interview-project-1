"""URL download for document ingestion."""

import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.extraction.exceptions import ExtractionError

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
}
MAX_SIZE = 10 * 1024 * 1024  # 10MB
TIMEOUT = 30.0


def _get_extension_from_url(url: str) -> str | None:
    """Extract file extension from URL path."""
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    return suffix if suffix in ALLOWED_EXTENSIONS else None


def _get_extension_from_content_type(content_type: str | None) -> str | None:
    """Map Content-Type to extension."""
    if not content_type:
        return None
    ct = content_type.split(";")[0].strip().lower()
    mapping = {
        "application/pdf": ".pdf",
        "image/png": ".png",
        "image/jpeg": ".jpeg",
        "image/jpg": ".jpg",
    }
    return mapping.get(ct)


def download_from_url(url: str) -> tuple[str, str]:
    """Download file from URL to temp file. Returns (temp_path, display_name).

    Raises:
        ExtractionError: If URL is invalid, download fails, or content is rejected.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ExtractionError(f"Invalid URL scheme: {parsed.scheme}. Use http or https.")

    with httpx.Client(follow_redirects=True, timeout=TIMEOUT) as client:
        response = client.get(url)
        response.raise_for_status()

        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_SIZE:
            raise ExtractionError(f"File too large: {content_length} bytes. Max: {MAX_SIZE}.")

        content = response.content
        if len(content) > MAX_SIZE:
            raise ExtractionError(f"File too large: {len(content)} bytes. Max: {MAX_SIZE}.")

        content_type = response.headers.get("content-type")
        ext = _get_extension_from_url(url) or _get_extension_from_content_type(content_type)
        if ext is None:
            raise ExtractionError(
                f"Unsupported content. URL or Content-Type must indicate PDF or image. "
                f"Got: {content_type or 'unknown'}"
            )

        suffix = ext
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            return tmp.name, url
