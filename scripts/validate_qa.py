"""Validate QA pipeline (model load, basic QA, empty context, long context chunking)."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.qa.pipeline import answer


def main() -> int:
    """Run QA validation. Returns 0 on success, 1 on failure."""
    errors = []

    # Basic QA
    ctx = "The contract expires on March 15, 2025. The vendor is Acme Corp."
    ans = answer("When does the contract expire?", ctx)
    if not ans or ("March" not in ans and "15" not in ans and "2025" not in ans):
        errors.append(f"Basic QA: expected date in answer, got {ans!r}")
    else:
        print("OK: Basic QA")

    # Empty context
    ans_empty = answer("What?", "")
    if not ans_empty or ("context" not in ans_empty.lower() and "no" not in ans_empty.lower()):
        errors.append(f"Empty context: expected fallback message, got {ans_empty!r}")
    else:
        print("OK: Empty context handled")

    # Long context (chunking)
    long_ctx = "The contract expires on March 15, 2025. The vendor is Acme Corp. " * 80
    try:
        ans_long = answer("When does the contract expire?", long_ctx)
        if not ans_long:
            errors.append("Long context: returned empty answer")
        elif "March" not in ans_long and "15" not in ans_long and "2025" not in ans_long:
            errors.append(f"Long context: expected relevant answer, got {ans_long!r}")
        else:
            print("OK: Long context (chunking)")
    except Exception as e:
        errors.append(f"Long context: crash - {e}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
