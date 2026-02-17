"""Preload models at Docker build time."""

from app.config import QA_MODELS
from app.extraction.ocr import _get_reader
from transformers import pipeline


def preload_all() -> None:
    """Download all QA models and EasyOCR. Called during Docker build."""
    for m in QA_MODELS:
        pipeline("question-answering", model=m["model"])
    _get_reader()
