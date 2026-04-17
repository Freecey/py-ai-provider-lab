import sqlite3
from datetime import datetime
from typing import Optional

from .base_repo import BaseRepository
from app.models.credential import Credential
from app.utils.crypto import get_crypto

_ENCRYPTED_FIELDS = [
    "api_key", "bearer_token", "oauth_access_token", "oauth_refresh_token",
    "oauth_client_secret",
]


def _row_to_credential(row: sqlite3.Row) -> Credential:
    crypto = get_crypto()
    return Credential(
        id=row["id"],
        provider_id=row["provider_id"],
        name=row["name"],
        active=bool(row["active"]),
        validity=row["validity"],
        api_key=crypto.decrypt(row["api_key"]),
        bearer_token=crypto.decrypt(row["bearer_token"]),
        oauth_access_token=crypto.decrypt(row["oauth_access_token"]),
        oauth_refresh_token=crypto.decrypt(row["oauth_refresh_token"]),
        oauth_client_id=row["oauth_client_id"],
        oauth_client_secret=crypto.decrypt(row["oauth_client_secret"]),
        oauth_scopes=row["oauth_scopes"],
        oauth_auth_url=row["oauth_auth_url"],
        oauth_token_endpoint=row["oauth_token_endpoint"],
        oauth_expires_at=datetime.fromisoformat(row["oauth_expires_at"]) if row["oauth_expires_at"] else None,
        org_id=row["org_id"],
        project_id=row["project_id"],
        notes=row["notes"],
        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
    )


class CredentialRepository(BaseRepository):
    def get_by_id(self, id: int) -> Optional[Credential]:
        row = self._fetchone("SELECT * FROM credentials WHERE id = ?", (id,))
        return _row_to_credential(row) if row else None

    def list(self, provider_id: Optional[int] = None) -> list[Credential]:
        if provider_id is not None:
            rows = self._fetchall("SELECT * FROM credentials WHERE provider_id = ? ORDER BY name", (provider_id,))
        else:
            rows = self._fetchall("SELECT * FROM credentials ORDER BY name")
        return [_row_to_credential(r) for r in rows]

    def create(self, c: Credential) -> Credential:
        crypto = get_crypto()
        cur = self._execute(
            """INSERT INTO credentials
               (provider_id, name, active, validity, api_key, bearer_token,
                oauth_access_token, oauth_refresh_token, oauth_client_id,
                oauth_client_secret, oauth_scopes, oauth_auth_url,
                oauth_token_endpoint, oauth_expires_at, org_id, project_id, notes)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (c.provider_id, c.name, int(c.active), c.validity,
             crypto.encrypt(c.api_key), crypto.encrypt(c.bearer_token),
             crypto.encrypt(c.oauth_access_token), crypto.encrypt(c.oauth_refresh_token),
             c.oauth_client_id, crypto.encrypt(c.oauth_client_secret),
             c.oauth_scopes, c.oauth_auth_url, c.oauth_token_endpoint,
             c.oauth_expires_at.isoformat() if c.oauth_expires_at else None,
             c.org_id, c.project_id, c.notes),
        )
        c.id = cur.lastrowid
        return c

    def update(self, c: Credential) -> Credential:
        crypto = get_crypto()
        self._execute(
            """UPDATE credentials SET
               provider_id=?, name=?, active=?, validity=?, api_key=?,
               bearer_token=?, oauth_access_token=?, oauth_refresh_token=?,
               oauth_client_id=?, oauth_client_secret=?, oauth_scopes=?,
               oauth_auth_url=?, oauth_token_endpoint=?, oauth_expires_at=?,
               org_id=?, project_id=?, notes=?, updated_at=datetime('now')
               WHERE id=?""",
            (c.provider_id, c.name, int(c.active), c.validity,
             crypto.encrypt(c.api_key), crypto.encrypt(c.bearer_token),
             crypto.encrypt(c.oauth_access_token), crypto.encrypt(c.oauth_refresh_token),
             c.oauth_client_id, crypto.encrypt(c.oauth_client_secret),
             c.oauth_scopes, c.oauth_auth_url, c.oauth_token_endpoint,
             c.oauth_expires_at.isoformat() if c.oauth_expires_at else None,
             c.org_id, c.project_id, c.notes, c.id),
        )
        return c

    def delete(self, id: int) -> bool:
        cur = self._execute("DELETE FROM credentials WHERE id = ?", (id,))
        return cur.rowcount > 0

    def update_validity(self, id: int, validity: str) -> None:
        self._execute(
            "UPDATE credentials SET validity=?, updated_at=datetime('now') WHERE id=?",
            (validity, id),
        )
