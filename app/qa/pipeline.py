"""QA pipeline using Hugging Face Inference API."""

import logging
import time

from huggingface_hub.utils import HfHubHTTPError

from app.config import QA_DEFAULT_MODEL, QA_MODELS
from app.hf_client import get_hf_client

logger = logging.getLogger(__name__)
EMPTY_CONTEXT_FALLBACK = "No context provided."

# Retry config for transient 503/504 from serverless inference (cold start, overload)
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds


def _normalize_context(context: str | list[str]) -> str:
    """Convert context to a single string. Empty list or all-empty strings → empty string."""
    if isinstance(context, str):
        return context.strip()
    if isinstance(context, list):
        parts = [s.strip() for s in context if s and s.strip()]
        return "\n\n".join(parts) if parts else ""
    return ""


def list_models() -> list[dict[str, str]]:
    """Return list of available QA models for the dropdown."""
    return [{"id": m["id"], "name": m["name"]} for m in QA_MODELS]


def answer(question: str, context: str | list[str]) -> str:
    """Answer a question given context from documents (single-turn, default model)."""
    return answer_with_history(question, context, [], QA_DEFAULT_MODEL)


def answer_with_history(
    question: str,
    context: str | list[str],
    history: list[tuple[str, str]],
    model_id: str | None = None,
) -> str:
    """Answer a question given context and last N Q/A pairs as history.

    Args:
        question: The question to answer.
        context: Document texts (string or list).
        history: Last 5 (question, answer) pairs.
        model_id: QA model config id. Defaults to QA_DEFAULT_MODEL.

    Returns:
        The answer string.
    """
    mid = model_id or QA_DEFAULT_MODEL
    ctx = _normalize_context(context)
    if history:
        history_str = "\n".join(f"Q: {q}\nA: {a}" for q, a in history)
        ctx = f"{ctx}\n\n---\nPrevious Q&A:\n{history_str}"
    if not ctx or not ctx.strip():
        return EMPTY_CONTEXT_FALLBACK

    model_config = next((m for m in QA_MODELS if m["id"] == mid), None)
    if model_config is None:
        raise ValueError(f"Unknown model id: {mid}")

    logger.info(
        "inference_start model_id=%s model=%s context_len=%d question_len=%d",
        mid,
        model_config["model"],
        len(ctx),
        len(question),
    )

    client = get_hf_client()
    for attempt in range(MAX_RETRIES):
        try:
            result = client.question_answering(
                question=question,
                context=ctx,
                model=model_config["model"],
                max_seq_len=384,
                doc_stride=128,
                handle_impossible_answer=True,
            )
            break
        except HfHubHTTPError as e:
            if attempt < MAX_RETRIES - 1 and e.response.status_code in (503, 504):
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "inference_retry model_id=%s attempt=%d status=%d wait_s=%d",
                    mid,
                    attempt + 1,
                    e.response.status_code,
                    wait,
                )
                time.sleep(wait)
                continue
            logger.error(
                "inference_failed model_id=%s status=%d error=%s",
                mid,
                e.response.status_code,
                str(e),
            )
            raise

    if not result:
        logger.info("inference_done model_id=%s answer=empty", mid)
        return EMPTY_CONTEXT_FALLBACK
    if isinstance(result, list) and len(result) > 0:
        answer_text = result[0].get("answer", EMPTY_CONTEXT_FALLBACK)
    elif isinstance(result, dict):
        answer_text = result.get("answer", EMPTY_CONTEXT_FALLBACK)
    else:
        answer_text = EMPTY_CONTEXT_FALLBACK

    logger.info(
        "inference_done model_id=%s answer_len=%d",
        mid,
        len(answer_text),
    )
    return answer_text
