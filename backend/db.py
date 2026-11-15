import datetime
import sqlite3
from typing import Optional

DB_FILE = "runs.db"


def get_connection(db_path: str = DB_FILE) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DB_FILE) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                repo TEXT,
                issue_title TEXT,
                issue_body TEXT,
                status TEXT,
                attempts INTEGER DEFAULT 0,
                diff TEXT DEFAULT '',
                test_output TEXT DEFAULT '',
                review_notes TEXT DEFAULT '',
                pr_url TEXT DEFAULT '',
                tokens_used INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0.0,
                created_at TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def create_run_record(run_id: str, repo: str, title: str, body: str, db_path: str = DB_FILE) -> None:
    init_db(db_path)
    conn = get_connection(db_path)
    now = datetime.datetime.utcnow().isoformat()
    try:
        conn.execute(
            "INSERT INTO runs (id, repo, issue_title, issue_body, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, repo, title, body, "running", now)
        )
        conn.commit()
    finally:
        conn.close()


def update_run_record(run_id: str, db_path: str = DB_FILE, **kwargs) -> None:
    if not kwargs:
        return
    conn = get_connection(db_path)
    cols = ", ".join(f"{k} = ?" for k in kwargs.keys())
    vals = list(kwargs.values()) + [run_id]
    try:
        conn.execute(f"UPDATE runs SET {cols} WHERE id = ?", vals)
        conn.commit()
    finally:
        conn.close()


def get_run(run_id: str, db_path: str = DB_FILE) -> Optional[dict]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_runs(db_path: str = DB_FILE) -> list[dict]:
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        cur = conn.execute("SELECT * FROM runs ORDER BY created_at DESC")
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()

