import json
import sqlite3
from datetime import datetime
from typing import Optional

from .base_repo import BaseRepository
from app.models.preset import Preset


def _row_to_preset(row: sqlite3.Row) -> Preset:
    return Preset(
        id=row["id"],
        name=row["name"],
        modality=row["modality"],
        model_id=row["model_id"],
        params=json.loads(row["params"] or "{}"),
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
    )


class PresetRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[Preset]:
        row = self._fetchone("SELECT * FROM presets WHERE id = ?", (id,))
        return _row_to_preset(row) if row else None

    def list(self, modality: Optional[str] = None, model_id: Optional[int] = None) -> list[Preset]:
        conditions, params = [], []
        if modality:
            conditions.append("modality = ?"); params.append(modality)
        if model_id is not None:
            conditions.append("model_id = ?"); params.append(model_id)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._fetchall(f"SELECT * FROM presets {where} ORDER BY name", tuple(params))
        return [_row_to_preset(r) for r in rows]

    def create(self, p: Preset) -> Preset:
        cur = self._execute(
            "INSERT INTO presets (name, modality, model_id, params) VALUES (?,?,?,?)",
            (p.name, p.modality, p.model_id, json.dumps(p.params)),
        )
        p.id = cur.lastrowid
        return p

    def update(self, p: Preset) -> Preset:
        self._execute(
            "UPDATE presets SET name=?, modality=?, model_id=?, params=?, updated_at=datetime('now') WHERE id=?",
            (p.name, p.modality, p.model_id, json.dumps(p.params), p.id),
        )
        return p

    def delete(self, id: int) -> bool:
        cur = self._execute("DELETE FROM presets WHERE id = ?", (id,))
        return cur.rowcount > 0
