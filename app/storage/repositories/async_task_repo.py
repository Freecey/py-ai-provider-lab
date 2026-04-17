import json
import sqlite3
from datetime import datetime
from typing import Optional

from .base_repo import BaseRepository
from app.models.async_task import AsyncTask


def _row_to_task(row: sqlite3.Row) -> AsyncTask:
    return AsyncTask(
        id=row["id"],
        test_run_id=row["test_run_id"],
        provider_task_id=row["provider_task_id"],
        status=row["status"],
        poll_interval_s=row["poll_interval_s"],
        timeout_s=row["timeout_s"],
        last_polled_at=datetime.fromisoformat(row["last_polled_at"]) if row["last_polled_at"] else None,
        result=json.loads(row["result"] or "{}"),
        error=row["error"],
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
    )


class AsyncTaskRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[AsyncTask]:
        row = self._fetchone("SELECT * FROM async_tasks WHERE id = ?", (id,))
        return _row_to_task(row) if row else None

    def get_by_test_run(self, test_run_id: int) -> Optional[AsyncTask]:
        row = self._fetchone("SELECT * FROM async_tasks WHERE test_run_id = ?", (test_run_id,))
        return _row_to_task(row) if row else None

    def list(self, status: Optional[str] = None) -> list[AsyncTask]:
        if status:
            rows = self._fetchall("SELECT * FROM async_tasks WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            rows = self._fetchall("SELECT * FROM async_tasks ORDER BY created_at DESC")
        return [_row_to_task(r) for r in rows]

    def create(self, t: AsyncTask) -> AsyncTask:
        cur = self._execute(
            """INSERT INTO async_tasks
               (test_run_id, provider_task_id, status, poll_interval_s, timeout_s, result, error)
               VALUES (?,?,?,?,?,?,?)""",
            (t.test_run_id, t.provider_task_id, t.status, t.poll_interval_s,
             t.timeout_s, json.dumps(t.result), t.error),
        )
        t.id = cur.lastrowid
        return t

    def update(self, t: AsyncTask) -> AsyncTask:
        self._execute(
            """UPDATE async_tasks SET
               status=?, last_polled_at=?, result=?, error=?, updated_at=datetime('now')
               WHERE id=?""",
            (t.status,
             t.last_polled_at.isoformat() if t.last_polled_at else None,
             json.dumps(t.result), t.error, t.id),
        )
        return t

    def delete(self, id: int) -> bool:
        cur = self._execute("DELETE FROM async_tasks WHERE id = ?", (id,))
        return cur.rowcount > 0
