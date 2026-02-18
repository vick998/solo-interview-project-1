"""NER pipeline using Hugging Face Inference API."""

import logging
import time

from huggingface_hub.utils import HfHubHTTPError

from app.config import NER_MODEL
from app.hf_client import get_hf_client

logger = logging.getLogger(__name__)

# Retry config for transient 503/504 (same as QA)
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds
CHUNK_SIZE = 2000  # chars (~512 tokens at 4 chars/token)

ENTITY_LABELS = ("PER", "ORG", "LOC", "MISC")


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks of roughly chunk_size characters."""
    if not text or len(text) <= chunk_size:
        return [text] if text and text.strip() else []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Try to break at word boundary
        if end < len(text):
            last_space = text.rfind(" ", start, end + 1)
            if last_space > start:
                end = last_space + 1
        chunks.append(text[start:end].strip())
        start = end
    return [c for c in chunks if c]


def extract_entities(text: str) -> dict[str, list[str]] | None:
    """Extract named entities from text. Returns dict grouped by entity type, or None on failure.

    Entity types: PER, ORG, LOC, MISC. Long text is chunked and results merged/deduplicated.
    """
    if not text or not text.strip():
        return {}

    chunks = _chunk_text(text.strip())
    if not chunks:
        return {}

    grouped: dict[str, set[str]] = {label: set() for label in ENTITY_LABELS}
    client = get_hf_client()

    for chunk in chunks:
        result = None
        for attempt in range(MAX_RETRIES):
            try:
                result = client.token_classification(
                    chunk,
                    model=NER_MODEL,
                    aggregation_strategy="simple",
                )
                break
            except HfHubHTTPError as e:
                if attempt < MAX_RETRIES - 1 and e.response.status_code in (503, 504):
                    wait = RETRY_BACKOFF_BASE**attempt
                    logger.warning(
                        "ner_retry attempt=%d status=%d wait_s=%d",
                        attempt + 1,
                        e.response.status_code,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                logger.error(
                    "ner_failed status=%d error=%s",
                    e.response.status_code,
                    str(e),
                )
                return None
            except Exception as e:
                logger.exception("ner_failed error=%s", str(e))
                return None

        # Merge results: group by entity_group, collect word, dedupe (case-insensitive)
        for item in result or []:
            label = item.get("entity_group") or item.get("entity")
            if not label:
                continue
            label = str(label).upper()
            if label not in grouped:
                grouped[label] = set()
            word = (item.get("word") or "").strip()
            if word:
                grouped[label].add(word)

    # Convert to dict[str, list[str]], dedupe case-insensitively, sort for stability
    out: dict[str, list[str]] = {}
    labels_order = list(ENTITY_LABELS) + sorted(
        k for k in grouped if k not in ENTITY_LABELS
    )
    for label in labels_order:
        words = grouped.get(label, set())
        seen_lower: set[str] = set()
        unique: list[str] = []
        for w in sorted(words, key=str.lower):
            if w.lower() not in seen_lower:
                seen_lower.add(w.lower())
                unique.append(w)
        if unique:
            out[label] = unique
    return out if out else {}
