import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timedelta
from decimal import Decimal


class PricingCache:
    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".deburger" / "cache"

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "pricing.db"
        self._conn = None
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    def _init_db(self):
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pricing_cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires
            ON pricing_cache(expires_at)
        """)
        conn.commit()

    async def get(self, key: str) -> Optional[Dict[str, Decimal]]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT value, expires_at FROM pricing_cache WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()

        if not row:
            return None

        value_json, expires_at = row

        if datetime.now().timestamp() > expires_at:
            conn.execute("DELETE FROM pricing_cache WHERE key = ?", (key,))
            conn.commit()
            return None

        data = json.loads(value_json)
        return {k: Decimal(v) for k, v in data.items()}

    async def set(self, key: str, value: Dict[str, Decimal], ttl: int = 86400):
        expires_at = int((datetime.now() + timedelta(seconds=ttl)).timestamp())
        value_json = json.dumps({k: str(v) for k, v in value.items()})

        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO pricing_cache (key, value, expires_at) VALUES (?, ?, ?)",
            (key, value_json, expires_at)
        )
        conn.commit()

    async def clear_expired(self):
        now = int(datetime.now().timestamp())
        conn = self._get_conn()
        conn.execute("DELETE FROM pricing_cache WHERE expires_at < ?", (now,))
        conn.commit()

    async def clear_all(self):
        conn = self._get_conn()
        conn.execute("DELETE FROM pricing_cache")
        conn.commit()
