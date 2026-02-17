"""SQLite-backed chat repository."""

import uuid
from datetime import datetime, timezone
from typing import Any

import aiosqlite

from app.storage.db import get_connection, init_db
from app.storage.exceptions import ChatNotFoundError


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


class ChatRepository:
    """Repository for chats, documents, and messages backed by SQLite."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path

    async def _conn(self) -> aiosqlite.Connection:
        return await get_connection(self._db_path)

    async def ensure_init(self) -> None:
        """Create tables if they do not exist."""
        await init_db(self._db_path)

    async def create_chat(self, title: str | None = None) -> str:
        """Create a new chat. Returns chat_id."""
        chat_id = _uuid()
        now = _now()
        conn = await self._conn()
        try:
            await conn.execute(
                "INSERT INTO chats (id, created_at, updated_at, title) VALUES (?, ?, ?, ?)",
                (chat_id, now, now, title),
            )
            await conn.commit()
        finally:
            await conn.close()
        return chat_id

    async def get_chat(self, chat_id: str) -> dict[str, Any] | None:
        """Return chat by id, or None if not found."""
        conn = await self._conn()
        try:
            cursor = await conn.execute(
                "SELECT id, created_at, updated_at, title FROM chats WHERE id = ?",
                (chat_id,),
            )
            row = await cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "title": row[3],
            }
        finally:
            await conn.close()

    async def list_chats(self) -> list[dict[str, Any]]:
        """List chats sorted by updated_at desc."""
        conn = await self._conn()
        try:
            cursor = await conn.execute(
                "SELECT id, created_at, updated_at, title FROM chats ORDER BY updated_at DESC"
            )
            rows = await cursor.fetchall()
            return [
                {"id": r[0], "created_at": r[1], "updated_at": r[2], "title": r[3]}
                for r in rows
            ]
        finally:
            await conn.close()

    async def update_chat_title(self, chat_id: str, title: str) -> None:
        """Update chat title. Raises ChatNotFoundError if chat does not exist."""
        conn = await self._conn()
        try:
            cursor = await conn.execute(
                "UPDATE chats SET title = ?, updated_at = ? WHERE id = ?",
                (title, _now(), chat_id),
            )
            await conn.commit()
            if cursor.rowcount == 0:
                raise ChatNotFoundError(f"Chat not found: {chat_id}")
        finally:
            await conn.close()

    async def add_documents(
        self,
        chat_id: str,
        documents: list[dict[str, Any]],
    ) -> list[str]:
        """Add documents to a chat. Returns list of document ids."""
        conn = await self._conn()
        doc_ids: list[str] = []
        try:
            for doc in documents:
                doc_id = _uuid()
                doc_ids.append(doc_id)
                await conn.execute(
                    """INSERT INTO documents
                       (id, chat_id, source_type, source_path_or_url, display_name,
                        extracted_text, enabled, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        doc_id,
                        chat_id,
                        doc["source_type"],
                        doc["source_path_or_url"],
                        doc["display_name"],
                        doc["extracted_text"],
                        1 if doc.get("enabled", True) else 0,
                        _now(),
                    ),
                )
            await conn.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ?",
                (_now(), chat_id),
            )
            await conn.commit()
        finally:
            await conn.close()
        return doc_ids

    async def get_documents(
        self,
        chat_id: str,
        enabled_only: bool = False,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return documents for chat. Optionally filter by enabled or document_ids."""
        conn = await self._conn()
        try:
            if document_ids:
                placeholders = ",".join("?" * len(document_ids))
                sql = f"""SELECT id, chat_id, source_type, source_path_or_url, display_name,
                         extracted_text, enabled, created_at
                         FROM documents WHERE chat_id = ? AND id IN ({placeholders})"""
                cursor = await conn.execute(sql, [chat_id, *document_ids])
            elif enabled_only:
                cursor = await conn.execute(
                    """SELECT id, chat_id, source_type, source_path_or_url, display_name,
                       extracted_text, enabled, created_at
                       FROM documents WHERE chat_id = ? AND enabled = 1""",
                    (chat_id,),
                )
            else:
                cursor = await conn.execute(
                    """SELECT id, chat_id, source_type, source_path_or_url, display_name,
                       extracted_text, enabled, created_at
                       FROM documents WHERE chat_id = ?""",
                    (chat_id,),
                )
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "chat_id": r[1],
                    "source_type": r[2],
                    "source_path_or_url": r[3],
                    "display_name": r[4],
                    "extracted_text": r[5],
                    "enabled": bool(r[6]),
                    "created_at": r[7],
                }
                for r in rows
            ]
        finally:
            await conn.close()

    async def set_document_enabled(
        self,
        chat_id: str,
        document_id: str,
        enabled: bool,
    ) -> None:
        """Toggle document enabled state. Raises ChatNotFoundError if chat/doc not found."""
        conn = await self._conn()
        try:
            cursor = await conn.execute(
                "UPDATE documents SET enabled = ? WHERE chat_id = ? AND id = ?",
                (1 if enabled else 0, chat_id, document_id),
            )
            await conn.commit()
            if cursor.rowcount == 0:
                raise ChatNotFoundError(f"Document not found: {document_id}")
        finally:
            await conn.close()

    async def add_message(
        self,
        chat_id: str,
        question: str,
        answer: str,
        model_used: str,
    ) -> str:
        """Add a message. Returns message id."""
        msg_id = _uuid()
        now = _now()
        conn = await self._conn()
        try:
            await conn.execute(
                """INSERT INTO messages (id, chat_id, question, answer, model_used, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (msg_id, chat_id, question, answer, model_used, now),
            )
            await conn.execute(
                "UPDATE chats SET updated_at = ? WHERE id = ?",
                (now, chat_id),
            )
            await conn.commit()
        finally:
            await conn.close()
        return msg_id

    async def get_messages(
        self,
        chat_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return messages for chat, ordered by created_at asc. Optionally limit to last N."""
        conn = await self._conn()
        try:
            if limit:
                cursor = await conn.execute(
                    """SELECT id, chat_id, question, answer, model_used, created_at
                       FROM (
                         SELECT id, chat_id, question, answer, model_used, created_at
                         FROM messages WHERE chat_id = ?
                         ORDER BY created_at DESC LIMIT ?
                       ) ORDER BY created_at ASC""",
                    (chat_id, limit),
                )
            else:
                cursor = await conn.execute(
                    """SELECT id, chat_id, question, answer, model_used, created_at
                       FROM messages WHERE chat_id = ?
                       ORDER BY created_at ASC""",
                    (chat_id,),
                )
            rows = await cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "chat_id": r[1],
                    "question": r[2],
                    "answer": r[3],
                    "model_used": r[4],
                    "created_at": r[5],
                }
                for r in rows
            ]
        finally:
            await conn.close()

    async def get_chat_with_documents_and_messages(
        self,
        chat_id: str,
    ) -> dict[str, Any] | None:
        """Return chat with documents and messages."""
        chat = await self.get_chat(chat_id)
        if chat is None:
            return None
        chat["documents"] = await self.get_documents(chat_id)
        chat["messages"] = await self.get_messages(chat_id)
        return chat
