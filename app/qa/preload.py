"""Preload models at Docker build time."""

from app.extraction.ocr import _get_reader


def preload_all() -> None:
    """Download EasyOCR model. Called during Docker build.

    QA models are no longer preloaded; they run via the HF Inference API.
    """
    _get_reader()
