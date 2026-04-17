import json
import sqlite3
from datetime import datetime
from typing import Optional

from .base_repo import BaseRepository
from app.models.prompt_template import PromptTemplate


def _row_to_template(row: sqlite3.Row) -> PromptTemplate:
    return PromptTemplate(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        modality=row["modality"],
        category=row["category"],
        tags=json.loads(row["tags"] or "[]"),
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
    )


class PromptTemplateRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[PromptTemplate]:
        row = self._fetchone("SELECT * FROM prompt_templates WHERE id = ?", (id,))
        return _row_to_template(row) if row else None

    def list(self, modality: Optional[str] = None, category: Optional[str] = None) -> list[PromptTemplate]:
        conditions, params = [], []
        if modality:
            conditions.append("modality = ?"); params.append(modality)
        if category:
            conditions.append("category = ?"); params.append(category)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._fetchall(f"SELECT * FROM prompt_templates {where} ORDER BY title", tuple(params))
        return [_row_to_template(r) for r in rows]

    def create(self, t: PromptTemplate) -> PromptTemplate:
        cur = self._execute(
            "INSERT INTO prompt_templates (title, content, modality, category, tags) VALUES (?,?,?,?,?)",
            (t.title, t.content, t.modality, t.category, json.dumps(t.tags)),
        )
        t.id = cur.lastrowid
        return t

    def update(self, t: PromptTemplate) -> PromptTemplate:
        self._execute(
            "UPDATE prompt_templates SET title=?, content=?, modality=?, category=?, tags=?, updated_at=datetime('now') WHERE id=?",
            (t.title, t.content, t.modality, t.category, json.dumps(t.tags), t.id),
        )
        return t

    def delete(self, id: int) -> bool:
        cur = self._execute("DELETE FROM prompt_templates WHERE id = ?", (id,))
        return cur.rowcount > 0
