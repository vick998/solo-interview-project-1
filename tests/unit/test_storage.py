"""Unit tests for ChatRepository."""

import tempfile

import pytest

from app.storage.chat_repository import ChatRepository
from app.storage.exceptions import ChatNotFoundError


@pytest.fixture
def repo() -> ChatRepository:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    return ChatRepository(db_path=path)


@pytest.mark.asyncio
async def test_create_chat_returns_id(repo: ChatRepository) -> None:
    """create_chat returns a UUID string."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    assert chat_id
    assert len(chat_id) == 36
    assert chat_id.count("-") == 4


@pytest.mark.asyncio
async def test_create_chat_with_title(repo: ChatRepository) -> None:
    """create_chat with title stores it."""
    await repo.ensure_init()
    chat_id = await repo.create_chat(title="My Chat")
    chat = await repo.get_chat(chat_id)
    assert chat is not None
    assert chat["title"] == "My Chat"


@pytest.mark.asyncio
async def test_add_documents_returns_ids(repo: ChatRepository) -> None:
    """add_documents returns document ids."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    docs = await repo.add_documents(
        chat_id,
        [
            {
                "source_type": "file",
                "source_path_or_url": "test.pdf",
                "display_name": "test.pdf",
                "extracted_text": "Hello world",
                "enabled": True,
            }
        ],
    )
    assert len(docs) == 1
    assert len(docs[0]) == 36


@pytest.mark.asyncio
async def test_add_documents_with_entities_stores_and_retrieves(repo: ChatRepository) -> None:
    """add_documents with entities stores them; get_documents returns entities."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    entities = {"PER": ["John Smith"], "ORG": ["Acme Corp"]}
    await repo.add_documents(
        chat_id,
        [
            {
                "source_type": "file",
                "source_path_or_url": "report.pdf",
                "display_name": "report.pdf",
                "extracted_text": "John Smith works at Acme Corp.",
                "enabled": True,
                "entities": entities,
            }
        ],
    )
    docs = await repo.get_documents(chat_id)
    assert len(docs) == 1
    assert docs[0]["entities"] == entities


@pytest.mark.asyncio
async def test_get_documents_returns_added(repo: ChatRepository) -> None:
    """get_documents returns added documents."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    await repo.add_documents(
        chat_id,
        [
            {
                "source_type": "file",
                "source_path_or_url": "a.pdf",
                "display_name": "a.pdf",
                "extracted_text": "Doc A",
                "enabled": True,
            },
            {
                "source_type": "url",
                "source_path_or_url": "https://example.com/b.pdf",
                "display_name": "https://example.com/b.pdf",
                "extracted_text": "Doc B",
                "enabled": True,
            },
        ],
    )
    docs = await repo.get_documents(chat_id)
    assert len(docs) == 2
    assert docs[0]["display_name"] == "a.pdf"
    assert docs[0]["extracted_text"] == "Doc A"
    assert docs[1]["display_name"] == "https://example.com/b.pdf"


@pytest.mark.asyncio
async def test_add_message_stores_and_retrieves(repo: ChatRepository) -> None:
    """add_message stores message and get_messages returns it."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    await repo.add_message(chat_id, "Q1", "A1", "distilbert")
    msgs = await repo.get_messages(chat_id)
    assert len(msgs) == 1
    assert msgs[0]["question"] == "Q1"
    assert msgs[0]["answer"] == "A1"
    assert msgs[0]["model_used"] == "distilbert"


@pytest.mark.asyncio
async def test_get_messages_limit_returns_last_n(repo: ChatRepository) -> None:
    """get_messages with limit returns last N."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    for i in range(7):
        await repo.add_message(chat_id, f"Q{i}", f"A{i}", "distilbert")
    msgs = await repo.get_messages(chat_id, limit=5)
    assert len(msgs) == 5
    assert msgs[0]["question"] == "Q2"
    assert msgs[-1]["question"] == "Q6"


@pytest.mark.asyncio
async def test_set_document_enabled(repo: ChatRepository) -> None:
    """set_document_enabled toggles enabled state."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    doc_ids = await repo.add_documents(
        chat_id,
        [
            {
                "source_type": "file",
                "source_path_or_url": "x.pdf",
                "display_name": "x.pdf",
                "extracted_text": "X",
                "enabled": True,
            }
        ],
    )
    await repo.set_document_enabled(chat_id, doc_ids[0], False)
    docs = await repo.get_documents(chat_id)
    assert docs[0]["enabled"] is False


@pytest.mark.asyncio
async def test_update_chat_title(repo: ChatRepository) -> None:
    """update_chat_title updates title."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    await repo.update_chat_title(chat_id, "New Title")
    chat = await repo.get_chat(chat_id)
    assert chat["title"] == "New Title"


@pytest.mark.asyncio
async def test_get_chat_nonexistent_returns_none(repo: ChatRepository) -> None:
    """get_chat for nonexistent id returns None."""
    await repo.ensure_init()
    chat = await repo.get_chat("00000000-0000-0000-0000-000000000000")
    assert chat is None


@pytest.mark.asyncio
async def test_set_document_enabled_nonexistent_raises(repo: ChatRepository) -> None:
    """set_document_enabled for nonexistent doc raises ChatNotFoundError."""
    await repo.ensure_init()
    chat_id = await repo.create_chat()
    with pytest.raises(ChatNotFoundError, match="Document not found"):
        await repo.set_document_enabled(chat_id, "00000000-0000-0000-0000-000000000000", True)
