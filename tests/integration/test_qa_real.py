"""Slow integration tests for real QA model."""

import pytest

from app.qa.pipeline import answer


@pytest.mark.slow
def test_basic_qa_returns_relevant_answer() -> None:
    """Basic QA returns answer containing expected date info."""
    ctx = "The contract expires on March 15, 2025. The vendor is Acme Corp."
    ans = answer("When does the contract expire?", ctx)
    assert ans
    assert "March" in ans or "15" in ans or "2025" in ans


@pytest.mark.slow
def test_long_context_no_crash() -> None:
    """Long context is chunked and does not crash."""
    long_ctx = (
        "The contract expires on March 15, 2025. The vendor is Acme Corp. " * 80
    )
    ans = answer("When does the contract expire?", long_ctx)
    assert ans
    assert "March" in ans or "15" in ans or "2025" in ans
