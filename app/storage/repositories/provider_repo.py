import json
import sqlite3
from datetime import datetime
from typing import Optional

from .base_repo import BaseRepository
from app.models.provider import Provider


def _row_to_provider(row: sqlite3.Row) -> Provider:
    return Provider(
        id=row["id"],
        name=row["name"],
        slug=row["slug"],
        active=bool(row["active"]),
        base_url=row["base_url"],
        endpoints=json.loads(row["endpoints"] or "{}"),
        api_version=row["api_version"],
        auth_type=row["auth_type"],
        custom_headers=json.loads(row["custom_headers"] or "{}"),
        timeout_global=row["timeout_global"],
        timeout_per_modality=json.loads(row["timeout_per_modality"] or "{}"),
        retry_count=row["retry_count"],
        retry_delay=row["retry_delay"],
        retry_backoff=row["retry_backoff"],
        proxy=row["proxy"],
        notes=row["notes"],
        extra_fields=json.loads(row["extra_fields"] or "{}"),
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
    )


class ProviderRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[Provider]:
        row = self._fetchone("SELECT * FROM providers WHERE id = ?", (id,))
        return _row_to_provider(row) if row else None

    def get_by_slug(self, slug: str) -> Optional[Provider]:
        row = self._fetchone("SELECT * FROM providers WHERE slug = ?", (slug,))
        return _row_to_provider(row) if row else None

    def list(self, active_only: bool = False) -> list[Provider]:
        if active_only:
            rows = self._fetchall("SELECT * FROM providers WHERE active = 1 ORDER BY name")
        else:
            rows = self._fetchall("SELECT * FROM providers ORDER BY name")
        return [_row_to_provider(r) for r in rows]

    def create(self, p: Provider) -> Provider:
        cur = self._execute(
            """INSERT INTO providers
               (name, slug, active, base_url, endpoints, api_version, auth_type,
                custom_headers, timeout_global, timeout_per_modality, retry_count,
                retry_delay, retry_backoff, proxy, notes, extra_fields)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (p.name, p.slug, int(p.active), p.base_url, json.dumps(p.endpoints),
             p.api_version, p.auth_type, json.dumps(p.custom_headers),
             p.timeout_global, json.dumps(p.timeout_per_modality),
             p.retry_count, p.retry_delay, p.retry_backoff,
             p.proxy, p.notes, json.dumps(p.extra_fields)),
        )
        p.id = cur.lastrowid
        return p

    def update(self, p: Provider) -> Provider:
        self._execute(
            """UPDATE providers SET
               name=?, slug=?, active=?, base_url=?, endpoints=?, api_version=?,
               auth_type=?, custom_headers=?, timeout_global=?, timeout_per_modality=?,
               retry_count=?, retry_delay=?, retry_backoff=?, proxy=?, notes=?,
               extra_fields=?, updated_at=datetime('now')
               WHERE id=?""",
            (p.name, p.slug, int(p.active), p.base_url, json.dumps(p.endpoints),
             p.api_version, p.auth_type, json.dumps(p.custom_headers),
             p.timeout_global, json.dumps(p.timeout_per_modality),
             p.retry_count, p.retry_delay, p.retry_backoff,
             p.proxy, p.notes, json.dumps(p.extra_fields), p.id),
        )
        return p

    def delete(self, id: int) -> bool:
        cur = self._execute("DELETE FROM providers WHERE id = ?", (id,))
        return cur.rowcount > 0
