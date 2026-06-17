from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from .errors import NotFoundError, ValidationError
from .index_engine import IndexEngine
from .models import (
    WIKI_DIR,
    WIKI_TYPES,
    WikiPage,
    ensure_list,
    load_markdown,
    merge_unique,
    now_iso,
    slugify,
    wiki_page_id,
    write_markdown,
)


RELATED_START = "<!-- kb:related:start -->"
RELATED_END = "<!-- kb:related:end -->"


class WikiStore:
    def __init__(self, project):
        self.project = project
        self.index = IndexEngine(project)

    def get(self, page_id: str) -> WikiPage:
        path = self._path_for_page_id(page_id)
        if path is None:
            raise NotFoundError("wiki page not found", page_id=page_id)
        return self._page_from(path)

    def get_by_slug(self, type: str, slug: str) -> WikiPage | None:
        if type not in WIKI_TYPES:
            raise ValidationError("unsupported wiki type", type=type)
        path = self.project.path("wiki", WIKI_DIR[type], f"{slug}.md")
        return self._page_from(path) if path.exists() else None

    def list(self, type: str | None = None) -> list[WikiPage]:
        if type and type not in WIKI_TYPES:
            raise ValidationError("unsupported wiki type", type=type)
        pages: list[WikiPage] = []
        dirs = [WIKI_DIR[type]] if type else WIKI_DIR.values()
        for dirname in dirs:
            for path in sorted(self.project.path("wiki", dirname).glob("*.md")):
                pages.append(self._page_from(path))
        return pages

    def find_by_alias(self, name: str) -> WikiPage | None:
        needle = self._normalize_alias(name)
        for page in self.list("entity"):
            aliases = ensure_list(page.frontmatter.get("aliases"))
            candidates = [page.title, page.slug, *map(str, aliases)]
            if any(self._normalize_alias(candidate) == needle for candidate in candidates):
                return page
        return None

    def upsert(
        self,
        type: str,
        title: str,
        body: str,
        *,
        aliases: list[str] | tuple[str, ...] = (),
        sources: list[str] | tuple[str, ...] = (),
        related: list[str] | tuple[str, ...] = (),
    ) -> WikiPage:
        if type not in WIKI_TYPES:
            raise ValidationError("unsupported wiki type", type=type)
        if not title.strip():
            raise ValidationError("title is required")
        source_list = [item for item in sources if item]
        related_list = [item for item in related if item]
        slug = self._slug_for(type, title, source_list)
        path = self.project.path("wiki", WIKI_DIR[type], f"{slug}.md")
        now = now_iso()
        if path.exists():
            frontmatter, _ = load_markdown(path)
            created_at = frontmatter.get("created_at") or now
            page_id = str(frontmatter.get("id") or self._page_id(type, slug, source_list))
            old_aliases = ensure_list(frontmatter.get("aliases"))
            old_sources = ensure_list(frontmatter.get("sources"))
            old_related = ensure_list(frontmatter.get("related"))
        else:
            created_at = now
            page_id = self._page_id(type, slug, source_list)
            old_aliases = []
            old_sources = []
            old_related = []
        frontmatter = {
            "id": page_id,
            "type": type,
            "title": title.strip(),
            "slug": slug,
            "aliases": merge_unique(old_aliases, list(aliases)),
            "created_at": created_at,
            "updated_at": now,
            "sources": merge_unique(old_sources, source_list),
            "related": merge_unique(old_related, related_list),
        }
        final_body = self._ensure_title(title, body)
        final_body = self._sync_related_block(final_body, frontmatter["related"])
        write_markdown(path, frontmatter, final_body)
        self.index.upsert(page_id, "wiki", type, title, final_body, path)
        page = self._page_from(path)
        self._sync_backlinks(page)
        self._update_index_doc()
        self._append_log(f"- {now} | upsert {type} | {page.id} | {page.title}\n")
        return self._page_from(path)

    def append_section(self, page_id: str, section_md: str) -> WikiPage:
        page = self.get(page_id)
        frontmatter, body = load_markdown(page.path)
        body_without_related = self._strip_related_block(body).rstrip()
        next_body = f"{body_without_related}\n\n{section_md.strip()}\n"
        next_body = self._sync_related_block(next_body, ensure_list(frontmatter.get("related")))
        frontmatter["updated_at"] = now_iso()
        write_markdown(page.path, frontmatter, next_body)
        self.index.upsert(page.id, "wiki", page.type, page.title, next_body, page.path)
        self._update_index_doc()
        self._append_log(f"- {frontmatter['updated_at']} | append | {page.id} | {page.title}\n")
        return self._page_from(page.path)

    def link(self, page_id_a: str, page_id_b: str) -> None:
        if page_id_a == page_id_b:
            raise ValidationError("cannot link page to itself", page_id=page_id_a)
        page_a = self.get(page_id_a)
        page_b = self.get(page_id_b)
        self._add_related(page_a, page_b.id)
        self._add_related(page_b, page_a.id)
        self._update_index_doc()
        self._append_log(f"- {now_iso()} | link | {page_a.id} <-> {page_b.id}\n")

    def archive(self, page_id: str, reason: str) -> None:
        page = self.get(page_id)
        archive_dir = self.project.path("wiki", ".archive", page.type)
        archive_dir.mkdir(parents=True, exist_ok=True)
        target = archive_dir / page.path.name
        shutil.move(str(page.path), target)
        self.index.remove(page.id)
        for other in self.list():
            related = [item for item in ensure_list(other.frontmatter.get("related")) if item != page.id]
            if related != ensure_list(other.frontmatter.get("related")):
                self._rewrite_related(other, related)
        self._update_index_doc()
        self._append_log(f"- {now_iso()} | archive | {page.id} | {reason}\n")

    def _add_related(self, page: WikiPage, related_id: str) -> None:
        related = merge_unique(ensure_list(page.frontmatter.get("related")), [related_id])
        self._rewrite_related(page, related)

    def _rewrite_related(self, page: WikiPage, related: list[str]) -> None:
        frontmatter, body = load_markdown(page.path)
        frontmatter["related"] = related
        frontmatter["updated_at"] = now_iso()
        body = self._sync_related_block(self._strip_related_block(body), related)
        write_markdown(page.path, frontmatter, body)
        self.index.upsert(page.id, "wiki", page.type, page.title, body, page.path)

    def _sync_backlinks(self, page: WikiPage) -> None:
        for related_id in ensure_list(page.frontmatter.get("related")):
            try:
                related_page = self.get(str(related_id))
            except NotFoundError:
                continue
            related_values = ensure_list(related_page.frontmatter.get("related"))
            if page.id not in related_values:
                self._add_related(related_page, page.id)

    def _slug_for(self, type: str, title: str, sources: list[str]) -> str:
        if type == "summary":
            if not sources:
                raise ValidationError("summary page requires a source id")
            return sources[0]
        base = slugify(title)
        slug = base
        index = 2
        while True:
            path = self.project.path("wiki", WIKI_DIR[type], f"{slug}.md")
            if not path.exists():
                return slug
            frontmatter, _ = load_markdown(path)
            if slugify(str(frontmatter.get("title") or "")) == base:
                return slug
            slug = f"{base}-{index}"
            index += 1

    def _page_id(self, type: str, slug: str, sources: list[str]) -> str:
        return wiki_page_id(type, slug, source_id=sources[0] if type == "summary" else None)

    def _path_for_page_id(self, page_id: str) -> Path | None:
        for dirname in WIKI_DIR.values():
            for path in self.project.path("wiki", dirname).glob("*.md"):
                frontmatter, _ = load_markdown(path)
                if frontmatter.get("id") == page_id:
                    return path
        return None

    def _page_from(self, path: Path) -> WikiPage:
        frontmatter, body = load_markdown(path)
        page_type = str(frontmatter.get("type") or path.parent.name.rstrip("s"))
        slug = str(frontmatter.get("slug") or path.stem)
        title = str(frontmatter.get("title") or slug)
        page_id = str(frontmatter.get("id") or self._page_id(page_type, slug, ensure_list(frontmatter.get("sources"))))
        return WikiPage(page_id, page_type, title, slug, path, frontmatter, body)

    def _ensure_title(self, title: str, body: str) -> str:
        stripped = body.strip()
        if stripped.startswith("# "):
            return stripped + "\n"
        return f"# {title.strip()}\n\n{stripped}\n"

    def _sync_related_block(self, body: str, related_ids: list[str]) -> str:
        body = self._strip_related_block(body).rstrip()
        if not related_ids:
            return body + "\n"
        lines = [RELATED_START, "## 关联"]
        for related_id in related_ids:
            title = self._title_for_related(related_id)
            lines.append(f"- [[{title}]]")
        lines.append(RELATED_END)
        return f"{body}\n\n" + "\n".join(lines) + "\n"

    def _strip_related_block(self, body: str) -> str:
        pattern = re.compile(rf"\n?{re.escape(RELATED_START)}.*?{re.escape(RELATED_END)}\n?", re.DOTALL)
        return pattern.sub("\n", body).strip()

    def _title_for_related(self, related_id: str) -> str:
        try:
            return self.get(related_id).title
        except NotFoundError:
            return related_id

    def _update_index_doc(self) -> None:
        lines = ["# 知识库索引", ""]
        for page_type, heading in [("entity", "实体"), ("topic", "主题"), ("summary", "摘要")]:
            pages = self.list(page_type)
            lines.append(f"## {heading}")
            if not pages:
                lines.append("")
                lines.append("暂无。")
            else:
                for page in pages:
                    rel = page.path.relative_to(self.project.path("wiki"))
                    lines.append(f"- [{page.title}]({rel.as_posix()}) - `{page.id}`")
            lines.append("")
        self.project.path("wiki", "index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def _append_log(self, line: str) -> None:
        log_path = self.project.path("wiki", "log.md")
        if not log_path.exists():
            log_path.write_text("# 编译日志\n\n", encoding="utf-8")
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(line)

    def _normalize_alias(self, value: str) -> str:
        return slugify(value).replace("-", "")
