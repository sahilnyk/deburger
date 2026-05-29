import hashlib
from typing import Dict, Optional


class FileCache:
    def __init__(self):
        self._cache: Dict[str, tuple[str, str]] = {}

    def get(self, file_path: str) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            current_hash = hashlib.md5(content.encode()).hexdigest()

            if file_path in self._cache:
                cached_hash, cached_content = self._cache[file_path]
                if cached_hash == current_hash:
                    return cached_content

            self._cache[file_path] = (current_hash, content)
            return content

        except Exception:
            return None

    def clear(self):
        self._cache.clear()

    def invalidate(self, file_path: str):
        self._cache.pop(file_path, None)
