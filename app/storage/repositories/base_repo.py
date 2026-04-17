from __future__ import annotations

import sqlite3
from typing import Any, Optional


class BaseRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_by_id(self, id: int) -> Optional[Any]:
        raise NotImplementedError

    def list(self, **filters) -> list:
        raise NotImplementedError

    def create(self, entity: Any) -> Any:
        raise NotImplementedError

    def update(self, entity: Any) -> Any:
        raise NotImplementedError

    def delete(self, id: int) -> bool:
        raise NotImplementedError

    def _fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchone()

    def _fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur
