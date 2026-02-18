"""Validate chat storage (create, add docs, get, add message, etc.)."""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.storage.chat_repository import ChatRepository


async def main() -> int:
    """Run storage validation. Returns 0 on success, 1 on failure."""
    errors = []
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name

    repo = ChatRepository(db_path=path)
    await repo.ensure_init()

    # Create chat and add documents
    chat_id = await repo.create_chat()
    doc_ids = await repo.add_documents(
        chat_id,
        [
            {
                "source_type": "file",
                "source_path_or_url": "doc1.pdf",
                "display_name": "doc1.pdf",
                "extracted_text": "doc1 text",
                "enabled": True,
            },
            {
                "source_type": "file",
                "source_path_or_url": "doc2.pdf",
                "display_name": "doc2.pdf",
                "extracted_text": "doc2 text",
                "enabled": True,
            },
        ],
    )
    if len(doc_ids) != 2:
        errors.append(f"Expected 2 doc ids, got {doc_ids}")
    else:
        print("OK: Add documents returns ids")

    docs = await repo.get_documents(chat_id)
    if len(docs) != 2 or docs[0]["extracted_text"] != "doc1 text":
        errors.append(f"Expected 2 docs with correct text, got {docs}")
    else:
        print("OK: Get documents returns added docs")

    # Add message
    await repo.add_message(chat_id, "Q1", "A1", "tinybert")
    msgs = await repo.get_messages(chat_id)
    if len(msgs) != 1 or msgs[0]["question"] != "Q1":
        errors.append(f"Expected 1 message, got {msgs}")
    else:
        print("OK: Add and get message")

    # Unknown chat returns None
    chat = await repo.get_chat("00000000-0000-0000-0000-000000000000")
    if chat is not None:
        errors.append("Expected None for unknown chat")
    else:
        print("OK: Unknown chat returns None")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("All validations passed.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
