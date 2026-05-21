from typing import Dict, Optional
from pathlib import Path
import hashlib


class FileCache:
    """cache file contents to avoid re-reading"""

    def __init__(self):
        self._cache: Dict[str, tuple[str, str]] = {}  # path -> (hash, content)

    def get(self, file_path: str) -> Optional[str]:
        # check if file changed
        try:
            with open(file_path, 'rb') as f:
                current_hash = hashlib.md5(f.read()).hexdigest()

            if file_path in self._cache:
                cached_hash, cached_content = self._cache[file_path]
                if cached_hash == current_hash:
                    return cached_content

            # cache miss or changed, read and cache
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self._cache[file_path] = (current_hash, content)
            return content

        except Exception:
            return None

    def clear(self):
        self._cache.clear()

    def invalidate(self, file_path: str):
        if file_path in self._cache:
            del self._cache[file_path]
