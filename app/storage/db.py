import sqlite3
import os
from pathlib import Path
from typing import Optional

from app.config.settings import get_settings
from app.config.constants import DB_FILENAME
from app.utils.logger import get_logger

logger = get_logger("storage.db")

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


class Database:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            settings = get_settings()
            data_dir = Path(settings.data_dir)
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / DB_FILENAME)
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._run_migrations()
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_current_version(self, conn: sqlite3.Connection) -> int:
        try:
            row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
            return row[0] or 0
        except sqlite3.OperationalError:
            return 0

    def _run_migrations(self) -> None:
        conn = self._conn
        current = self._get_current_version(conn)
        migration_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
        for mf in migration_files:
            version = int(mf.stem.split("_")[0])
            if version > current:
                logger.info(f"Applying migration {mf.name}")
                sql = mf.read_text()
                conn.executescript(sql)
                conn.commit()
                current = version


_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
        _db.connect()
    return _db


def get_conn() -> sqlite3.Connection:
    return get_db().connect()
