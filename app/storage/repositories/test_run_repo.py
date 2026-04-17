import json
import sqlite3
from datetime import datetime
from typing import Optional

from .base_repo import BaseRepository
from app.models.test_run import TestRun


def _row_to_run(row: sqlite3.Row) -> TestRun:
    return TestRun(
        id=row["id"],
        provider_id=row["provider_id"],
        credential_id=row["credential_id"],
        model_id=row["model_id"],
        modality=row["modality"],
        params=json.loads(row["params"] or "{}"),
        request_payload=json.loads(row["request_payload"] or "{}"),
        response_raw=row["response_raw"],
        response_files=json.loads(row["response_files"] or "[]"),
        latency_ms=row["latency_ms"],
        cost_estimated=row["cost_estimated"],
        currency=row["currency"],
        status=row["status"],
        error_message=row["error_message"],
        rating=row["rating"],
        rating_notes=row["rating_notes"],
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
    )


class TestRunRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[TestRun]:
        row = self._fetchone("SELECT * FROM test_runs WHERE id = ?", (id,))
        return _row_to_run(row) if row else None

    def list(self, provider_id: Optional[int] = None, model_id: Optional[int] = None,
             status: Optional[str] = None, modality: Optional[str] = None,
             limit: int = 100, offset: int = 0) -> list[TestRun]:
        conditions, params = [], []
        if provider_id is not None:
            conditions.append("provider_id = ?"); params.append(provider_id)
        if model_id is not None:
            conditions.append("model_id = ?"); params.append(model_id)
        if status is not None:
            conditions.append("status = ?"); params.append(status)
        if modality is not None:
            conditions.append("modality = ?"); params.append(modality)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        params.extend([limit, offset])
        rows = self._fetchall(
            f"SELECT * FROM test_runs {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            tuple(params),
        )
        return [_row_to_run(r) for r in rows]

    def create(self, r: TestRun) -> TestRun:
        cur = self._execute(
            """INSERT INTO test_runs
               (provider_id, credential_id, model_id, modality, params, request_payload,
                response_raw, response_files, latency_ms, cost_estimated, currency,
                status, error_message, rating, rating_notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (r.provider_id, r.credential_id, r.model_id, r.modality,
             json.dumps(r.params), json.dumps(r.request_payload),
             r.response_raw, json.dumps(r.response_files),
             r.latency_ms, r.cost_estimated, r.currency,
             r.status, r.error_message, r.rating, r.rating_notes),
        )
        r.id = cur.lastrowid
        return r

    def update(self, r: TestRun) -> TestRun:
        self._execute(
            """UPDATE test_runs SET
               response_raw=?, response_files=?, latency_ms=?, cost_estimated=?,
               status=?, error_message=?, rating=?, rating_notes=?
               WHERE id=?""",
            (r.response_raw, json.dumps(r.response_files), r.latency_ms, r.cost_estimated,
             r.status, r.error_message, r.rating, r.rating_notes, r.id),
        )
        return r

    def delete(self, id: int) -> bool:
        cur = self._execute("DELETE FROM test_runs WHERE id = ?", (id,))
        return cur.rowcount > 0

    def update_rating(self, id: int, rating: int, notes: str = "") -> None:
        self._execute(
            "UPDATE test_runs SET rating=?, rating_notes=? WHERE id=?",
            (rating, notes, id),
        )
