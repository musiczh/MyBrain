from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import NotFoundError, ValidationError
from .index_engine import IndexEngine
from .models import (
    RAW_DIR,
    RAW_TYPES,
    NormalizedInput,
    RawRecord,
    dump_yaml,
    generate_raw_id,
    load_yaml,
    load_markdown,
    now_iso,
    sha256_text,
    write_markdown,
)


class RawStore:
    def __init__(self, project):
        self.project = project
        self.index = IndexEngine(project)

    def add(
        self,
        item: NormalizedInput,
        *,
        source_url: str | None = None,
        source_path: str | None = None,
        author: str | None = None,
        context: str | None = None,
    ) -> RawRecord:
        if item.type not in RAW_TYPES:
            raise ValidationError("unsupported raw type", type=item.type)
        content_hash = sha256_text(item.text)
        duplicate_id = self.index.find_by_hash(content_hash) or self._find_id_by_hash(content_hash)
        if duplicate_id:
            record = self.get(duplicate_id)
            record.duplicated = True
            return record
        raw_id = self._new_id(item.type)
        now = now_iso()
        frontmatter: dict[str, Any] = {
            "id": raw_id,
            "type": item.type,
            "title": item.title,
            "created_at": now,
            "ingested_at": now,
            "content_hash": content_hash,
        }
        if source_url:
            frontmatter["source_url"] = source_url
        if source_path:
            frontmatter["source_path"] = source_path
        if author:
            frontmatter["author"] = author
        if context:
            frontmatter["context"] = context
        path = self.project.path("raw", RAW_DIR[item.type], f"{raw_id}.md")
        write_markdown(path, frontmatter, item.text)
        self.index.upsert(raw_id, "raw", item.type, item.title, item.text, path, content_hash=content_hash)
        return self._record_from(path, duplicated=False)

    def get(self, raw_id: str) -> RawRecord:
        path = self._path_for_id(raw_id)
        if path is None:
            raise NotFoundError("raw record not found", raw_id=raw_id)
        return self._record_from(path)

    def list(self, type: str | None = None, status: str | None = None, limit: int = 50) -> list[RawRecord]:
        if type and type not in RAW_TYPES:
            raise ValidationError("unsupported raw type", type=type)
        records: list[RawRecord] = []
        dirs = [RAW_DIR[type]] if type else RAW_DIR.values()
        for dirname in dirs:
            for path in sorted(self.project.path("raw", dirname).glob("*.md"), reverse=True):
                record = self._record_from(path)
                if status and record.status != status:
                    continue
                records.append(record)
                if len(records) >= limit:
                    return records
        return records

    def mark_compiled(self, raw_id: str, tags: list[str]) -> RawRecord:
        path = self._path_for_id(raw_id)
        if path is None:
            raise NotFoundError("raw record not found", raw_id=raw_id)
        status_path = self._status_path(raw_id)
        status = self._status_for(raw_id)
        current_tags = status.get("tags") if isinstance(status.get("tags"), list) else []
        merged_tags = [*current_tags]
        for tag in tags:
            if tag not in merged_tags:
                merged_tags.append(tag)
        status_path.parent.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            dump_yaml(
                {
                    "raw_id": raw_id,
                    "status": "compiled",
                    "compiled_at": now_iso(),
                    "tags": merged_tags,
                }
            ),
            encoding="utf-8",
        )
        return self._record_from(path)

    def status_path(self, raw_id: str) -> Path:
        return self._status_path(raw_id)

    def _new_id(self, raw_type: str) -> str:
        for _ in range(20):
            raw_id = generate_raw_id(raw_type)
            if self._path_for_id(raw_id) is None:
                return raw_id
        raise ValidationError("failed to generate unique raw id", type=raw_type)

    def _find_id_by_hash(self, content_hash: str) -> str | None:
        for dirname in RAW_DIR.values():
            for path in self.project.path("raw", dirname).glob("*.md"):
                frontmatter, _ = load_markdown(path)
                if frontmatter.get("content_hash") == content_hash:
                    return str(frontmatter.get("id"))
        return None

    def _path_for_id(self, raw_id: str) -> Path | None:
        for dirname in RAW_DIR.values():
            path = self.project.path("raw", dirname, f"{raw_id}.md")
            if path.exists():
                return path
        return None

    def _status_path(self, raw_id: str) -> Path:
        return self.project.path(".kb", "raw-status", f"{raw_id}.yaml")

    def _status_for(self, raw_id: str) -> dict[str, Any]:
        path = self._status_path(raw_id)
        if not path.exists():
            return {}
        return load_yaml(path.read_text(encoding="utf-8"))

    def _record_from(self, path: Path, duplicated: bool = False) -> RawRecord:
        frontmatter, body = load_markdown(path)
        raw_id = str(frontmatter.get("id") or path.stem)
        raw_type = str(frontmatter.get("type") or path.parent.name.rstrip("s"))
        status = self._status_for(raw_id)
        return RawRecord(
            id=raw_id,
            type=raw_type,
            title=frontmatter.get("title"),
            path=path,
            frontmatter=frontmatter,
            content=body,
            status=str(status.get("status") or frontmatter.get("status") or "ingested"),
            duplicated=duplicated,
        )
