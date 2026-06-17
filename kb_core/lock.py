from __future__ import annotations

from pathlib import Path


class ProjectLock:
    """Advisory write lock for a single local knowledge base."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self._handle = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.lock_path.open("w", encoding="utf-8")
        try:
            import fcntl

            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        return self

    def __exit__(self, exc_type, exc, tb):
        if self._handle is None:
            return False
        try:
            import fcntl

            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        except (ImportError, OSError):
            pass
        self._handle.close()
        self._handle = None
        return False
