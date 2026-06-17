from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from .models import SearchHit, load_markdown

try:
    import jieba  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal local envs
    jieba = None


class IndexEngine:
    def __init__(self, project):
        self.project = project
        self.db_path = project.path(".kb", "index.sqlite")

    def build(self) -> int:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            self.db_path.unlink()
        count = 0
        with self._connect() as conn:
            self._ensure_schema(conn)
        for layer, base in [("raw", self.project.path("raw")), ("wiki", self.project.path("wiki"))]:
            for path in sorted(base.rglob("*.md")):
                if ".archive" in path.parts or path.name in {"index.md", "log.md"}:
                    continue
                frontmatter, body = load_markdown(path)
                doc_id = str(frontmatter.get("id") or path.stem)
                doc_type = str(frontmatter.get("type") or path.parent.name.rstrip("s"))
                title = str(frontmatter.get("title") or path.stem)
                content_hash = str(frontmatter.get("content_hash") or "")
                self.upsert(doc_id, layer, doc_type, title, body, path, content_hash=content_hash)
                count += 1
        return count

    def upsert(
        self,
        doc_id: str,
        layer: str,
        type: str,
        title: str,
        body: str,
        path: str | Path,
        content_hash: str = "",
    ) -> None:
        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("DELETE FROM docs WHERE doc_id = ?", (doc_id,))
            conn.execute(
                """
                INSERT INTO docs(doc_id, layer, type, title, body, path, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, layer, type, self._segment(title), self._segment(body), str(path), content_hash),
            )
            conn.commit()

    def remove(self, doc_id: str) -> None:
        with self._connect() as conn:
            self._ensure_schema(conn)
            conn.execute("DELETE FROM docs WHERE doc_id = ?", (doc_id,))
            conn.commit()

    def search(
        self,
        query: str,
        *,
        layer: str | None = None,
        type: str | None = None,
        limit: int = 10,
    ) -> list[SearchHit]:
        match = self._match_query(query)
        if not match:
            return []
        clauses = ["docs MATCH ?"]
        params: list[object] = [match]
        if layer:
            clauses.append("layer = ?")
            params.append(layer)
        if type:
            clauses.append("type = ?")
            params.append(type)
        params.append(limit)
        sql = f"""
            SELECT doc_id, layer, type, title,
                   snippet(docs, 4, '<<', '>>', '…', 12) AS snippet,
                   bm25(docs) AS rank,
                   path
            FROM docs
            WHERE {' AND '.join(clauses)}
            ORDER BY rank
            LIMIT ?
        """
        with self._connect() as conn:
            self._ensure_schema(conn)
            rows = conn.execute(sql, params).fetchall()
        hits: list[SearchHit] = []
        for doc_id, row_layer, row_type, indexed_title, snippet, rank, path in rows:
            title = self._read_title(Path(path), indexed_title)
            weight = 1.0 if row_layer == "wiki" else 0.6
            hits.append(
                SearchHit(
                    layer=row_layer,
                    id=doc_id,
                    type=row_type,
                    title=title,
                    snippet=self._clean_snippet(snippet),
                    score=round(float(-rank) * weight, 6),
                    path=str(path),
                )
            )
        return hits

    def find_by_hash(self, content_hash: str) -> str | None:
        if not content_hash or not self.db_path.exists():
            return None
        with self._connect() as conn:
            self._ensure_schema(conn)
            row = conn.execute("SELECT doc_id FROM docs WHERE content_hash = ? LIMIT 1", (content_hash,)).fetchone()
        return str(row[0]) if row else None

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self, conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
                doc_id UNINDEXED,
                layer UNINDEXED,
                type UNINDEXED,
                title,
                body,
                path UNINDEXED,
                content_hash UNINDEXED,
                tokenize='unicode61 remove_diacritics 2'
            )
            """
        )

    def _segment(self, text: str) -> str:
        if jieba is not None:
            return " ".join(token for token in jieba.cut(text) if token.strip())
        tokens = re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", text)
        return " ".join(tokens) if tokens else text

    def _match_query(self, query: str) -> str:
        segmented = self._segment(query)
        terms = [self._escape_match_term(term) for term in segmented.split() if term.strip()]
        return " OR ".join(terms)

    def _escape_match_term(self, term: str) -> str:
        safe = term.replace('"', '""')
        return f'"{safe}"'

    def _read_title(self, path: Path, fallback: str) -> str:
        if path.exists():
            frontmatter, _ = load_markdown(path)
            return str(frontmatter.get("title") or path.stem)
        return fallback.replace(" ", "")

    def _clean_snippet(self, snippet: str | None) -> str:
        if not snippet:
            return ""
        return re.sub(r"\s+", " ", snippet).strip()
