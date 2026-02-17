"""QA pipeline using Hugging Face transformers."""

from transformers import pipeline

_pipeline = None

EMPTY_CONTEXT_FALLBACK = "No context provided."


def _get_pipeline():
    """Lazy-load and return the QA pipeline."""
    global _pipeline
    if _pipeline is None:
        _pipeline = pipeline(
            "question-answering",
            model="distilbert/distilbert-base-cased-distilled-squad",
        )
    return _pipeline


def _normalize_context(context: str | list[str]) -> str:
    """Convert context to a single string. Empty list or all-empty strings → empty string."""
    if isinstance(context, str):
        return context.strip()
    if isinstance(context, list):
        parts = [s.strip() for s in context if s and s.strip()]
        return "\n\n".join(parts) if parts else ""
    return ""


def answer(question: str, context: str | list[str]) -> str:
    """Answer a question given context from documents.

    Args:
        question: The question to answer.
        context: Either a single context string or a list of document texts
            (e.g. from session store). Will be concatenated if list.

    Returns:
        The answer string, or a fallback message if context is empty.
    """
    ctx = _normalize_context(context)
    if not ctx:
        return EMPTY_CONTEXT_FALLBACK

    pipe = _get_pipeline()
    result = pipe(
        question=question,
        context=ctx,
        max_seq_len=384,
        doc_stride=128,
        handle_impossible_answer=True,
    )
    return result.get("answer", EMPTY_CONTEXT_FALLBACK)
