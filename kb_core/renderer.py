from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from .models import WIKI_DIR, WikiPage
from .raw_store import RawStore
from .wiki_store import WikiStore

try:
    from markdown_it import MarkdownIt  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal local envs
    MarkdownIt = None

try:
    from jinja2 import Template  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal local envs
    Template = None


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
SOURCE_REF_RE = re.compile(r"\[\^((?:src|thought|note)_[A-Za-z0-9_\-]+)\]")


class Renderer:
    def __init__(self, project):
        self.project = project
        self.wiki = WikiStore(project)

    def render_site(self, out_dir: Path | None = None) -> Path:
        out = out_dir or self.project.path("dist")
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "style.css").write_text(self._style(), encoding="utf-8")
        pages = self.wiki.list()
        for page in pages:
            target = out / WIKI_DIR[page.type] / f"{page.slug}.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.render_page(page.id), encoding="utf-8")
        for raw in RawStore(self.project).list(limit=100000):
            target = out / "raw" / f"{raw.id}.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            content = f"<h1>{html.escape(raw.title or raw.id)}</h1><pre>{html.escape(raw.content)}</pre>"
            target.write_text(self._layout(raw.title or raw.id, content, style_href="../style.css"), encoding="utf-8")
        index_html = self._render_index(pages)
        (out / "index.html").write_text(index_html, encoding="utf-8")
        return out / "index.html"

    def render_page(self, page_id: str) -> str:
        page = self.wiki.get(page_id)
        body = self._replace_wikilinks(page.body)
        body = self._replace_source_refs(body)
        content = self._markdown(body)
        return self._layout(page.title, content, style_href="../style.css")

    def _render_index(self, pages: list[WikiPage]) -> str:
        sections: list[str] = ["<h1>知识库索引</h1>", '<input id="filter" placeholder="过滤页面" autofocus>']
        for page_type, label in [("entity", "实体"), ("topic", "主题"), ("summary", "摘要")]:
            sections.append(f"<h2>{label}</h2><ul>")
            for page in pages:
                if page.type == page_type:
                    sections.append(
                        f'<li data-title="{html.escape(page.title.lower())}">'
                        f'<a href="{WIKI_DIR[page.type]}/{page.slug}.html">{html.escape(page.title)}</a> '
                        f"<code>{html.escape(page.id)}</code></li>"
                    )
            sections.append("</ul>")
        sections.append(
            """
<script>
const input = document.getElementById('filter');
input.addEventListener('input', () => {
  const q = input.value.trim().toLowerCase();
  document.querySelectorAll('li[data-title]').forEach((item) => {
    item.hidden = q && !item.dataset.title.includes(q);
  });
});
</script>
"""
        )
        return self._layout("知识库索引", "\n".join(sections), style_href="style.css")

    def _replace_wikilinks(self, body: str) -> str:
        def repl(match: re.Match[str]) -> str:
            label = match.group(1).strip()
            page = self.wiki.find_by_alias(label) or self._find_by_title(label)
            if not page:
                return f'<span class="broken-link">[[{html.escape(label)}]]</span>'
            return f'<a class="wikilink" href="../{WIKI_DIR[page.type]}/{page.slug}.html">{html.escape(label)}</a>'

        return WIKILINK_RE.sub(repl, body)

    def _replace_source_refs(self, body: str) -> str:
        def repl(match: re.Match[str]) -> str:
            raw_id = match.group(1)
            return f'<a class="source-ref" href="../raw/{raw_id}.html">[^{html.escape(raw_id)}]</a>'

        return SOURCE_REF_RE.sub(repl, body)

    def _find_by_title(self, title: str) -> WikiPage | None:
        for page in self.wiki.list():
            if page.title == title or page.slug == title:
                return page
        return None

    def _markdown(self, body: str) -> str:
        if MarkdownIt is not None:
            return MarkdownIt("commonmark", {"html": True}).render(body)
        lines: list[str] = []
        for line in body.splitlines():
            if line.startswith("<!--"):
                continue
            if line.startswith("# "):
                lines.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "):
                lines.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("- "):
                lines.append(f"<p>• {self._inline_html(line[2:])}</p>")
            elif line.strip():
                lines.append(f"<p>{self._inline_html(line)}</p>")
        return "\n".join(lines)

    def _inline_html(self, text: str) -> str:
        if "<a " in text or "<span " in text:
            return text
        return html.escape(text)

    def _layout(self, title: str, content: str, *, style_href: str) -> str:
        template_text = self._template()
        if Template is not None:
            return Template(template_text).render(title=title, content=content, style_href=style_href)
        return (
            template_text.replace("{{ title }}", html.escape(title))
            .replace("{{ content }}", content)
            .replace("{{ style_href }}", style_href)
        )

    def _template(self) -> str:
        path = Path(__file__).parent / "templates" / "base.html"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return "<!doctype html><html><head><title>{{ title }}</title></head><body>{{ content }}</body></html>"

    def _style(self) -> str:
        path = Path(__file__).parent / "templates" / "style.css"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return "body{font-family:system-ui,sans-serif;max-width:960px;margin:40px auto;padding:0 24px;}"
