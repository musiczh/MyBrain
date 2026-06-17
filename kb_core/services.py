from __future__ import annotations

from pathlib import Path
from typing import Any

from .git_repo import GitRepo
from .index_engine import IndexEngine
from .lock import ProjectLock
from .normalizer import Normalizer
from .project import Project
from .raw_store import RawStore
from .schema_store import SchemaStore
from .wiki_store import WikiStore


def init_project(root: Path, name: str, force: bool = False) -> dict[str, Any]:
    project = Project.init(root, name, force=force)
    return {"root": str(project.root), "config": project.config}


def ingest(
    project: Project,
    *,
    raw_type: str,
    text: str,
    title: str | None = None,
    source_url: str | None = None,
    source_path: str | None = None,
    author: str | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    with ProjectLock(project.path(".kb", ".lock")):
        item = Normalizer().build(text, raw_type, title)
        record = RawStore(project).add(
            item,
            source_url=source_url,
            source_path=source_path,
            author=author,
            context=context,
        )
        commit = ""
        if not record.duplicated:
            commit = GitRepo(project.root).commit(f'ingest: add {record.type} {record.id} "{record.title}"', [record.path])
        return {"record": raw_record_to_dict(record), "duplicated": record.duplicated, "commit": commit}


def build_plan(project: Project, raw_id: str, limit: int = 8) -> dict[str, Any]:
    raw = RawStore(project).get(raw_id)
    query = f"{raw.title or ''} {raw.content[:240]}"
    hits = IndexEngine(project).search(query, layer="wiki", limit=limit)
    return {
        "raw": raw_record_to_dict(raw),
        "text": raw.content,
        "schema": SchemaStore(project).all_text(),
        "related_pages": [hit.__dict__ for hit in hits],
    }


def write_summary(project: Project, raw_id: str, text: str) -> dict[str, Any]:
    with ProjectLock(project.path(".kb", ".lock")):
        RawStore(project).get(raw_id)
        page = WikiStore(project).upsert("summary", f"Summary for {raw_id}", text, sources=[raw_id])
        commit = GitRepo(project.root).commit(f"compile: summary for {raw_id}", [project.path("wiki")])
        return {"page": wiki_page_to_dict(page), "commit": commit}


def upsert_page(
    project: Project,
    page_type: str,
    title: str,
    body: str,
    *,
    aliases: list[str] | None = None,
    sources: list[str] | None = None,
    related: list[str] | None = None,
) -> dict[str, Any]:
    with ProjectLock(project.path(".kb", ".lock")):
        page = WikiStore(project).upsert(
            page_type,
            title,
            body,
            aliases=aliases or [],
            sources=sources or [],
            related=related or [],
        )
        commit = GitRepo(project.root).commit(f"compile: upsert {page.type}/{page.slug}", [project.path("wiki")])
        return {"page": wiki_page_to_dict(page), "commit": commit}


def link_pages(project: Project, page_id_a: str, page_id_b: str) -> dict[str, Any]:
    with ProjectLock(project.path(".kb", ".lock")):
        WikiStore(project).link(page_id_a, page_id_b)
        commit = GitRepo(project.root).commit(f"compile: link {page_id_a} {page_id_b}", [project.path("wiki")])
        return {"a": page_id_a, "b": page_id_b, "commit": commit}


def mark_compiled(project: Project, raw_id: str, tags: list[str]) -> dict[str, Any]:
    with ProjectLock(project.path(".kb", ".lock")):
        raw_store = RawStore(project)
        record = raw_store.mark_compiled(raw_id, tags)
        commit = GitRepo(project.root).commit(f"compile: mark {raw_id} compiled", [raw_store.status_path(raw_id)])
        return {"record": raw_record_to_dict(record), "commit": commit}


def raw_record_to_dict(record) -> dict[str, Any]:
    return {
        "id": record.id,
        "type": record.type,
        "title": record.title,
        "path": str(record.path),
        "status": record.status,
        "frontmatter": record.frontmatter,
    }


def wiki_page_to_dict(page) -> dict[str, Any]:
    return {
        "id": page.id,
        "type": page.type,
        "title": page.title,
        "slug": page.slug,
        "path": str(page.path),
        "frontmatter": page.frontmatter,
    }
