"""Lightweight SQLite logger for bot usage.

Stores events so a dashboard can visualize usage without external services.
"""
import hashlib
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

DB_PATH = Path(os.getenv("USAGE_DB_PATH", "usage_metrics.sqlite")).resolve()
_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=5)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            persona TEXT,
            query_type TEXT,
            success INTEGER,
            latency_ms REAL,
            user_hash TEXT,
            username TEXT,
            error TEXT,
            raw_query TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_persona ON events(persona);")
    return conn


def _hash_user(user_id: Any) -> str:
    if user_id is None:
        return "anon"
    try:
        raw = str(user_id).encode()
    except Exception:
        raw = b"anon"
    return hashlib.sha256(raw).hexdigest()[:12]


def log_event(
    user_id: Any,
    username: str,
    query: str,
    query_type: str,
    persona: str,
    response_time_ms: float,
    success: bool,
    error: str = None,
):
    ts = datetime.utcnow().isoformat(timespec="seconds")
    hashed_user = _hash_user(user_id)
    clean_query = (query or "")[:200]
    clean_error = (error or "")[:200]
    with _lock:
        try:
            conn = _get_conn()
            conn.execute(
                """
                INSERT INTO events (ts, persona, query_type, success, latency_ms, user_hash, username, error, raw_query)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ts,
                    persona or "unknown",
                    query_type or "unknown",
                    1 if success else 0,
                    float(response_time_ms) if response_time_ms is not None else None,
                    hashed_user,
                    (username or "")[:80],
                    clean_error,
                    clean_query,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def log_error(endpoint: str, error: str, user_id: Any = None):
    ts = datetime.utcnow().isoformat(timespec="seconds")
    hashed_user = _hash_user(user_id)
    clean_error = (error or "")[:200]
    with _lock:
        try:
            conn = _get_conn()
            conn.execute(
                """
                INSERT INTO events (ts, persona, query_type, success, latency_ms, user_hash, username, error, raw_query)
                VALUES (?, ?, ?, 0, NULL, ?, '', ?, '')
                """,
                (
                    ts,
                    "api",
                    endpoint or "error",
                    hashed_user,
                    clean_error,
                ),
            )
            conn.commit()
        finally:
            conn.close()


def load_recent(limit: int = 1000) -> List[Dict[str, Any]]:
    if not DB_PATH.exists():
        return []
    conn = _get_conn()
    try:
        cur = conn.execute(
            "SELECT id, ts, persona, query_type, success, latency_ms, user_hash, username, error, raw_query FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def db_path() -> Path:
    return DB_PATH
