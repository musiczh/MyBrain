from __future__ import annotations

import subprocess
from pathlib import Path

from .errors import KbError


class GitRepo:
    def __init__(self, root: Path):
        self.root = root

    def init(self) -> None:
        if (self.root / ".git").exists():
            return
        self._run(["git", "init"])

    def commit(self, message: str, paths: list[Path] | None = None) -> str:
        self.init()
        add_paths = [self._relative(path) for path in paths] if paths else ["."]
        self._run(["git", "add", *add_paths])
        if not self._has_changes():
            return ""
        result = self._run(
            [
                "git",
                "-c",
                "user.name=Knowledge Base",
                "-c",
                "user.email=knowledge-base@example.local",
                "commit",
                "-m",
                message,
            ]
        )
        return self._parse_commit_hash(result.stdout)

    def diff(self, ref: str = "HEAD") -> str:
        result = self._run(["git", "diff", ref], check=False)
        return result.stdout

    def log(self, limit: int = 20) -> list[dict[str, str]]:
        result = self._run(
            ["git", "log", f"-n{limit}", "--pretty=format:%H%x09%ad%x09%s", "--date=iso-strict"],
            check=False,
        )
        if result.returncode != 0:
            return []
        entries: list[dict[str, str]] = []
        for line in result.stdout.splitlines():
            commit, date, subject = (line.split("\t", 2) + ["", "", ""])[:3]
            entries.append({"commit": commit, "date": date, "subject": subject})
        return entries

    def _has_changes(self) -> bool:
        result = self._run(["git", "status", "--porcelain"], check=False)
        return bool(result.stdout.strip())

    def _relative(self, path: Path) -> str:
        path = path if path.is_absolute() else self.root / path
        try:
            return str(path.resolve().relative_to(self.root.resolve()))
        except ValueError as exc:
            raise KbError("path is outside git repository", code="path_outside_repo", detail={"path": str(path)}) from exc

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(args, cwd=self.root, text=True, capture_output=True)
        if check and result.returncode != 0:
            raise KbError(
                f"git command failed: {' '.join(args)}",
                code="git_error",
                detail={"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode},
            )
        return result

    def _parse_commit_hash(self, stdout: str) -> str:
        for token in stdout.replace("[", " ").replace("]", " ").split():
            if len(token) >= 7 and all(ch in "0123456789abcdef" for ch in token.lower()):
                return token
        result = self._run(["git", "rev-parse", "HEAD"], check=False)
        return result.stdout.strip() if result.returncode == 0 else ""
