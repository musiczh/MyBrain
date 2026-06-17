from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime

from .models import LintIssue, ensure_list, slugify
from .raw_store import RawStore
from .wiki_store import WikiStore


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


class Maintainer:
    def __init__(self, project):
        self.project = project
        self.wiki = WikiStore(project)
        self.raw = RawStore(project)

    def lint(self, checks: list[str] | None = None) -> list[LintIssue]:
        requested = set(checks or ["orphan", "broken_link", "missing_backlink", "duplicate_concept", "stale"])
        issues: list[LintIssue] = []
        if "orphan" in requested:
            issues.extend(self._orphan_issues())
        if "broken_link" in requested:
            issues.extend(self._broken_link_issues())
        if "missing_backlink" in requested:
            issues.extend(self._missing_backlink_issues())
        if "duplicate_concept" in requested:
            issues.extend(self._duplicate_concept_issues())
        if "stale" in requested:
            issues.extend(self._stale_issues())
        return issues

    def fix_missing_backlinks(self) -> list[LintIssue]:
        fixed: list[LintIssue] = []
        for issue in self._missing_backlink_issues():
            source = str(issue.detail.get("source"))
            target = str(issue.detail.get("target"))
            if source and target:
                self.wiki.link(source, target)
                fixed.append(issue)
        return fixed

    def _orphan_issues(self) -> list[LintIssue]:
        incoming: dict[str, int] = defaultdict(int)
        pages = self.wiki.list()
        for page in pages:
            for related in ensure_list(page.frontmatter.get("related")):
                incoming[str(related)] += 1
            for title in WIKILINK_RE.findall(page.body):
                target = self.wiki.find_by_alias(title) or self._find_by_title(title)
                if target:
                    incoming[target.id] += 1
        return [
            LintIssue("orphan", page.id, f"{page.title} 没有入链", "link_or_archive", {"page": page.id})
            for page in pages
            if incoming.get(page.id, 0) == 0 and page.type != "summary"
        ]

    def _broken_link_issues(self) -> list[LintIssue]:
        issues: list[LintIssue] = []
        for page in self.wiki.list():
            for related in ensure_list(page.frontmatter.get("related")):
                try:
                    self.wiki.get(str(related))
                except Exception:
                    issues.append(
                        LintIssue(
                            "broken_link",
                            page.id,
                            f"{page.title} 的 related 指向不存在页面 {related}",
                            "remove_or_create",
                            {"target": related},
                        )
                    )
            for title in WIKILINK_RE.findall(page.body):
                if not (self.wiki.find_by_alias(title) or self._find_by_title(title)):
                    issues.append(
                        LintIssue(
                            "broken_link",
                            page.id,
                            f"{page.title} 正文链接 [[{title}]] 无目标页面",
                            "create_page_or_rename_link",
                            {"target": title},
                        )
                    )
        return issues

    def _missing_backlink_issues(self) -> list[LintIssue]:
        issues: list[LintIssue] = []
        for page in self.wiki.list():
            for related_id in ensure_list(page.frontmatter.get("related")):
                try:
                    target = self.wiki.get(str(related_id))
                except Exception:
                    continue
                if page.id not in ensure_list(target.frontmatter.get("related")):
                    issues.append(
                        LintIssue(
                            "missing_backlink",
                            target.id,
                            f"{target.title} 缺少指回 {page.title} 的 backlink",
                            "kb link can fix",
                            {"source": page.id, "target": target.id},
                        )
                    )
        return issues

    def _duplicate_concept_issues(self) -> list[LintIssue]:
        buckets: dict[str, list[str]] = defaultdict(list)
        for page in self.wiki.list():
            buckets[slugify(page.title)].append(page.id)
            for alias in ensure_list(page.frontmatter.get("aliases")):
                buckets[slugify(str(alias))].append(page.id)
        issues: list[LintIssue] = []
        for concept, ids in buckets.items():
            unique_ids = sorted(set(ids))
            if concept and len(unique_ids) > 1:
                issues.append(
                    LintIssue(
                        "duplicate_concept",
                        unique_ids[0],
                        f"概念 {concept} 同时出现在多个页面",
                        "merge_or_add_alias",
                        {"pages": unique_ids},
                    )
                )
        return issues

    def _stale_issues(self) -> list[LintIssue]:
        issues: list[LintIssue] = []
        for page in self.wiki.list():
            updated = self._parse_time(page.frontmatter.get("updated_at"))
            for raw_id in ensure_list(page.frontmatter.get("sources")):
                try:
                    raw = self.raw.get(str(raw_id))
                except Exception:
                    continue
                ingested = self._parse_time(raw.frontmatter.get("ingested_at"))
                if updated and ingested and ingested > updated:
                    issues.append(
                        LintIssue(
                            "stale",
                            page.id,
                            f"{page.title} 早于来源 {raw_id} 的写入时间",
                            "review_page_against_source",
                            {"source": raw_id},
                        )
                    )
        return issues

    def _find_by_title(self, title: str):
        needle = slugify(title)
        for page in self.wiki.list():
            if slugify(page.title) == needle or page.slug == needle:
                return page
        return None

    def _parse_time(self, value) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None
