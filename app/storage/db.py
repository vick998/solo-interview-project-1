"""SQLite database setup and initialization."""

from pathlib import Path

import aiosqlite

from app.config import DB_PATH

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
    inference_time REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

CREATE INDEX IF NOT EXISTS idx_documents_chat_id ON documents(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
"""


def _ensure_data_dir(path: str | None = None) -> None:
    """Create data directory if missing (for local dev). Skip for :memory:."""
    p = path if path is not None else DB_PATH
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
        # Migration: add inference_time to existing messages tables
        try:
            await conn.execute("ALTER TABLE messages ADD COLUMN inference_time REAL")
            await conn.commit()
        except Exception:
            pass  # Column already exists
        # Migration: add entities to existing documents tables
        try:
            await conn.execute("ALTER TABLE documents ADD COLUMN entities TEXT")
            await conn.commit()
        except Exception:
            pass  # Column already exists
    finally:
        await conn.close()
