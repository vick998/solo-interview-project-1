"""QA pipeline using Hugging Face transformers."""

from transformers import pipeline

from app.config import QA_DEFAULT_MODEL, QA_MODELS

_pipelines: dict[str, pipeline] = {}

EMPTY_CONTEXT_FALLBACK = "No context provided."


def _get_pipeline(model_id: str) -> pipeline:
    """Lazy-load and return the QA pipeline for the given model id."""
    global _pipelines
    if model_id not in _pipelines:
        model_config = next((m for m in QA_MODELS if m["id"] == model_id), None)
        if model_config is None:
            raise ValueError(f"Unknown model id: {model_id}")
        _pipelines[model_id] = pipeline(
            "question-answering",
            model=model_config["model"],
        )
    return _pipelines[model_id]


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

    pipe = _get_pipeline(mid)
    result = pipe(
        question=question,
        context=ctx,
        max_seq_len=384,
        doc_stride=128,
        handle_impossible_answer=True,
    )
    return result.get("answer", EMPTY_CONTEXT_FALLBACK)
