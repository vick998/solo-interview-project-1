"""SQLite database setup and initialization."""

import os
from pathlib import Path

import aiosqlite

DB_PATH = "./data/chat.db"

INIT_SQL = """
CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    title TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_path_or_url TEXT NOT NULL,
    display_name TEXT NOT NULL,
    extracted_text TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    model_used TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_chat_id ON documents(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
"""


def _ensure_data_dir(path: str | None = None) -> None:
    """Create ./data directory if missing (for local dev). Skip for :memory:."""
    p = path or DB_PATH
    if p.startswith(":memory") or p.startswith("file::memory"):
        return
    data_dir = Path(p).parent
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)


async def get_connection(db_path: str | None = None) -> aiosqlite.Connection:
    """Return an aiosqlite connection to the database."""
    path = db_path or DB_PATH
    _ensure_data_dir(path)
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    return conn


async def init_db(db_path: str | None = None) -> None:
    """Create tables if they do not exist."""
    conn = await get_connection(db_path)
    try:
        await conn.executescript(INIT_SQL)
        await conn.commit()
    finally:
        await conn.close()
