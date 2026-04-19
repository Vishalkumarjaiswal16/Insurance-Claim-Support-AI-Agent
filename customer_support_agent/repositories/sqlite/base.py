from __future__ import annotations

import sqlite3
import threading
from typing import Any

from customer_support_agent.core.settings import ensure_directories, get_settings

_DB_INIT_LOCK = threading.Lock()
_DB_INITIALIZED = False

def _connect_raw() -> sqlite3.Connection:
    settings = get_settings()
    ensure_directories(settings)
    
    conn = sqlite3.connect(str(settings.db_file), timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn

def connect() -> sqlite3.Connection:
    init_db()
    return _connect_raw()

def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)

def init_db() -> None:
    global _DB_INITIALIZED
    if _DB_INITIALIZED:
        return

    with _DB_INIT_LOCK:
        if _DB_INITIALIZED:
            return

        with _connect_raw() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    company TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER REFERENCES customers(id),
                    subject TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    priority TEXT DEFAULT 'medium',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id INTEGER REFERENCES tickets(id),
                    content TEXT NOT NULL,
                    context_used TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TRIGGER IF NOT EXISTS tickets_updated_at_trigger
                AFTER UPDATE ON tickets
                FOR EACH ROW
                WHEN NEW.updated_at = OLD.updated_at
                BEGIN
                    UPDATE tickets
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = OLD.id;
                END;
                """ 
            )
        _DB_INITIALIZED = True