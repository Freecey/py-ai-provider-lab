import json
import sqlite3
from datetime import datetime
from typing import Optional

from .base_repo import BaseRepository
from app.models.model import Model, ModelCapability


def _row_to_model(row: sqlite3.Row, capabilities: list[ModelCapability] = None) -> Model:
    return Model(
        id=row["id"],
        provider_id=row["provider_id"],
        technical_name=row["technical_name"],
        display_name=row["display_name"],
        type=row["type"],
        active=bool(row["active"]),
        favorite=bool(row["favorite"]),
        rating=row["rating"],
        context_max=row["context_max"],
        cost_input=row["cost_input"],
        cost_output=row["cost_output"],
        currency=row["currency"],
        rpm_limit=row["rpm_limit"],
        tpm_limit=row["tpm_limit"],
        tags=json.loads(row["tags"] or "[]"),
        notes=row["notes"],
        extra=json.loads(row["extra"] or "{}"),
        capabilities=capabilities or [],
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
    )


class ModelRepository(BaseRepository):
    def _load_capabilities(self, model_id: int) -> list[ModelCapability]:
        rows = self._fetchall("SELECT * FROM model_capabilities WHERE model_id = ?", (model_id,))
        return [ModelCapability(id=r["id"], model_id=r["model_id"], capability=r["capability"]) for r in rows]

    def get_by_id(self, id: int) -> Optional[Model]:
        row = self._fetchone("SELECT * FROM models WHERE id = ?", (id,))
        if not row:
            return None
        return _row_to_model(row, self._load_capabilities(id))

    def list(self, provider_id: Optional[int] = None, type: Optional[str] = None,
             active_only: bool = True) -> list[Model]:
        conditions = []
        params = []
        if active_only:
            conditions.append("active = 1")
        if provider_id is not None:
            conditions.append("provider_id = ?")
            params.append(provider_id)
        if type is not None:
            conditions.append("type = ?")
            params.append(type)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        rows = self._fetchall(f"SELECT * FROM models {where} ORDER BY display_name, technical_name", tuple(params))
        return [_row_to_model(r, self._load_capabilities(r["id"])) for r in rows]

    def create(self, m: Model) -> Model:
        cur = self._execute(
            """INSERT INTO models
               (provider_id, technical_name, display_name, type, active, favorite, rating,
                context_max, cost_input, cost_output, currency, rpm_limit, tpm_limit,
                tags, notes, extra)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (m.provider_id, m.technical_name, m.display_name, m.type, int(m.active),
             int(m.favorite), m.rating, m.context_max, m.cost_input, m.cost_output,
             m.currency, m.rpm_limit, m.tpm_limit, json.dumps(m.tags), m.notes, json.dumps(m.extra)),
        )
        m.id = cur.lastrowid
        self._save_capabilities(m)
        return m

    def update(self, m: Model) -> Model:
        self._execute(
            """UPDATE models SET
               provider_id=?, technical_name=?, display_name=?, type=?, active=?,
               favorite=?, rating=?, context_max=?, cost_input=?, cost_output=?,
               currency=?, rpm_limit=?, tpm_limit=?, tags=?, notes=?, extra=?,
               updated_at=datetime('now')
               WHERE id=?""",
            (m.provider_id, m.technical_name, m.display_name, m.type, int(m.active),
             int(m.favorite), m.rating, m.context_max, m.cost_input, m.cost_output,
             m.currency, m.rpm_limit, m.tpm_limit, json.dumps(m.tags), m.notes,
             json.dumps(m.extra), m.id),
        )
        self._execute("DELETE FROM model_capabilities WHERE model_id = ?", (m.id,))
        self._save_capabilities(m)
        return m

    def delete(self, id: int) -> bool:
        cur = self._execute("DELETE FROM models WHERE id = ?", (id,))
        return cur.rowcount > 0

    def _save_capabilities(self, m: Model) -> None:
        for cap in m.capabilities:
            if isinstance(cap, ModelCapability):
                capability = cap.capability
            else:
                capability = str(cap)
            self.conn.execute(
                "INSERT OR IGNORE INTO model_capabilities (model_id, capability) VALUES (?,?)",
                (m.id, capability),
            )
        self.conn.commit()
