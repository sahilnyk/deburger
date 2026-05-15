"""Fix caching with SQLite."""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from deburger.models.error import ErrorInfo
from deburger.models.fix import Fix, CodeChange


class FixCache:
    """SQLite-based cache for successful fixes."""

    def __init__(self, db_path: str = "~/.deburger/cache.db"):
        """
        Initialize cache.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS fixes (
                error_hash TEXT PRIMARY KEY,
                error_type TEXT NOT NULL,
                error_message TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER NOT NULL,
                fix_json TEXT NOT NULL,
                confidence REAL NOT NULL,
                success_rate REAL DEFAULT 1.0,
                times_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_error_type ON fixes(error_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON fixes(file_path)")
        conn.commit()
        conn.close()

    def get(self, error: ErrorInfo) -> Optional[Fix]:
        """
        Get cached fix for error.

        Args:
            error: Error to look up

        Returns:
            Cached fix if exists and has good success rate, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT fix_json, confidence
            FROM fixes
            WHERE error_hash = ? AND success_rate > 0.7
            """,
            (error.error_hash,)
        )
        row = cursor.fetchone()

        if row:
            # Update usage stats
            conn.execute(
                """
                UPDATE fixes
                SET times_used = times_used + 1,
                    last_used_at = ?
                WHERE error_hash = ?
                """,
                (datetime.now(), error.error_hash)
            )
            conn.commit()

            fix = self._deserialize_fix(row[0])
            conn.close()
            return fix

        conn.close()
        return None

    def put(self, error: ErrorInfo, fix: Fix):
        """
        Store fix in cache.

        Args:
            error: Error that was fixed
            fix: The successful fix
        """
        conn = sqlite3.connect(self.db_path)

        fix_json = self._serialize_fix(fix)

        conn.execute(
            """
            INSERT OR REPLACE INTO fixes
            (error_hash, error_type, error_message, file_path, line_number,
             fix_json, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                error.error_hash,
                error.error_type,
                error.message,
                error.file_path,
                error.line_number,
                fix_json,
                fix.confidence,
                datetime.now(),
            )
        )

        conn.commit()
        conn.close()

    def update_success_rate(self, error: ErrorInfo, success: bool):
        """
        Update success rate for a cached fix.

        Uses exponential moving average.

        Args:
            error: Error that was fixed
            success: Whether the fix worked
        """
        conn = sqlite3.connect(self.db_path)

        # Exponential moving average: new_rate = old_rate * 0.9 + result * 0.1
        result = 1.0 if success else 0.0

        conn.execute(
            """
            UPDATE fixes
            SET success_rate = success_rate * 0.9 + ? * 0.1
            WHERE error_hash = ?
            """,
            (result, error.error_hash)
        )

        conn.commit()
        conn.close()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        conn = sqlite3.connect(self.db_path)

        cursor = conn.execute("""
            SELECT
                COUNT(*) as total_fixes,
                AVG(success_rate) as avg_success_rate,
                SUM(times_used) as total_uses,
                COUNT(DISTINCT error_type) as unique_error_types
            FROM fixes
        """)

        row = cursor.fetchone()
        conn.close()

        return {
            "total_fixes": row[0],
            "avg_success_rate": row[1] or 0.0,
            "total_uses": row[2] or 0,
            "unique_error_types": row[3],
        }

    def clear(self):
        """Clear all cached fixes."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM fixes")
        conn.commit()
        conn.close()

    def _serialize_fix(self, fix: Fix) -> str:
        """Serialize fix to JSON."""
        data = {
            "id": fix.id,
            "explanation": fix.explanation,
            "confidence": fix.confidence,
            "reasoning": fix.reasoning,
            "changes": [
                {
                    "file_path": change.file_path,
                    "line_start": change.line_start,
                    "line_end": change.line_end,
                    "old_code": change.old_code,
                    "new_code": change.new_code,
                }
                for change in fix.changes
            ]
        }
        return json.dumps(data)

    def _deserialize_fix(self, fix_json: str) -> Fix:
        """Deserialize fix from JSON."""
        data = json.loads(fix_json)

        changes = [
            CodeChange(
                file_path=change["file_path"],
                line_start=change["line_start"],
                line_end=change["line_end"],
                old_code=change["old_code"],
                new_code=change["new_code"],
            )
            for change in data["changes"]
        ]

        return Fix(
            id=data["id"],
            explanation=data["explanation"],
            changes=changes,
            confidence=data["confidence"],
            reasoning=data["reasoning"],
        )
