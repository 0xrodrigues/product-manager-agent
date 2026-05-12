import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "task_management.db"


def _slugify(title: str) -> str:
    slug = unicodedata.normalize("NFKD", title.lower())
    slug = slug.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    return slug


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                started_at  DATETIME NOT NULL,
                updated_at  DATETIME NOT NULL,
                status      TEXT NOT NULL DEFAULT 'PLANNED',
                description TEXT NOT NULL
            )
        """)


def create_task(title: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "id": str(uuid.uuid4()),
        "title": title,
        "started_at": now,
        "updated_at": now,
        "status": "PLANNED",
        "description": f"docs/tasks/{_slugify(title)}/task.md",
    }
    with _get_connection() as conn:
        conn.execute(
            "INSERT INTO tasks VALUES (:id, :title, :started_at, :updated_at, :status, :description)",
            task,
        )
    return task


def update_task(task_id: str, status: str | None = None, title: str | None = None) -> dict | None:
    task = get_task(task_id)
    if task is None:
        return None

    valid_statuses = {"PLANNED", "COMPLETED", "CANCELED"}
    if status and status not in valid_statuses:
        raise ValueError(f"status must be one of {valid_statuses}")

    new_title = title or task["title"]
    new_status = status or task["status"]
    updated_at = datetime.now(timezone.utc).isoformat()
    description = f"docs/tasks/{_slugify(new_title)}/task.md"

    with _get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET title=?, status=?, updated_at=?, description=? WHERE id=?",
            (new_title, new_status, updated_at, description, task_id),
        )

    return get_task(task_id)


def get_task(task_id: str) -> dict | None:
    with _get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return dict(row) if row else None


def list_tasks() -> list[dict]:
    with _get_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY started_at DESC").fetchall()
    return [dict(r) for r in rows]


init_db()
