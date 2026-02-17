"""Validate session storage (add, get, isolation, SessionNotFoundError)."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.storage.exceptions import SessionNotFoundError
from app.storage.session_store import SessionStore


def main() -> int:
    """Run storage validation. Returns 0 on success, 1 on failure."""
    errors = []

    store = SessionStore()

    # Add and retrieve
    store.add_documents("s1", ["doc1 text", "doc2 text"])
    docs = store.get_documents("s1")
    if docs != ["doc1 text", "doc2 text"]:
        errors.append(f"Expected ['doc1 text', 'doc2 text'], got {docs}")
    else:
        print("OK: Add and retrieve documents")

    # Append behavior
    store.add_documents("s1", ["doc3 text"])
    docs = store.get_documents("s1")
    if docs != ["doc1 text", "doc2 text", "doc3 text"]:
        errors.append(f"Expected append, got {docs}")
    else:
        print("OK: Append behavior")

    # Session isolation
    store.add_documents("s2", ["only in s2"])
    s1_docs = store.get_documents("s1")
    s2_docs = store.get_documents("s2")
    if "only in s2" in s1_docs:
        errors.append("s2 docs visible in s1 (isolation broken)")
    elif s2_docs != ["only in s2"]:
        errors.append(f"s2 expected ['only in s2'], got {s2_docs}")
    else:
        print("OK: Session isolation")

    # Unknown session raises SessionNotFoundError
    try:
        store.get_documents("nonexistent")
        errors.append("Expected SessionNotFoundError for unknown session")
    except SessionNotFoundError:
        print("OK: Unknown session raises SessionNotFoundError")
    except Exception as e:
        errors.append(f"Wrong exception for unknown session: {e}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
