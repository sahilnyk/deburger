"""Pricing cache - keeps pricing data fresh without hammering APIs."""

import json
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal


class PricingCache:
    """Cache for cloud provider pricing data."""

    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            cache_dir = Path.home() / ".deburger" / "cache"

        cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = cache_dir / "pricing.db"
        self._init_db()

    def _init_db(self):
        """Initialize cache database."""
        with sqlite3.connect(self.db_path) as conn:
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

    async def get(self, key: str) -> Optional[Dict[str, Decimal]]:
        """Get cached pricing data if not expired."""
        with sqlite3.connect(self.db_path) as conn:
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
                return None

            data = json.loads(value_json)
            return {k: Decimal(v) for k, v in data.items()}

    async def set(self, key: str, value: Dict[str, Decimal], ttl: int = 86400):
        """Cache pricing data with TTL (default 24 hours)."""
        expires_at = int((datetime.now() + timedelta(seconds=ttl)).timestamp())

        value_json = json.dumps({k: str(v) for k, v in value.items()})

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO pricing_cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value_json, expires_at)
            )

    async def clear_expired(self):
        """Remove expired entries."""
        now = int(datetime.now().timestamp())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM pricing_cache WHERE expires_at < ?", (now,))

    async def clear_all(self):
        """Clear entire cache."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM pricing_cache")
