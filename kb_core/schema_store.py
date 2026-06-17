from __future__ import annotations

from .errors import NotFoundError


class SchemaStore:
    def __init__(self, project):
        self.project = project

    def read(self, name: str) -> str:
        path = self.project.path("schema", f"{name}.md")
        if not path.exists():
            raise NotFoundError("schema file not found", name=name)
        return path.read_text(encoding="utf-8")

    def all_text(self) -> str:
        chunks: list[str] = []
        for path in sorted(self.project.path("schema").glob("*.md")):
            chunks.append(f"\n<!-- schema:{path.name} -->\n{path.read_text(encoding='utf-8')}")
        return "\n".join(chunks).strip()
