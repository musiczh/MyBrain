from __future__ import annotations

import hashlib
import re
import secrets
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal local envs
    yaml = None


RAW_TYPES = {"article", "thought", "note"}
WIKI_TYPES = {"entity", "topic", "summary"}
RAW_PREFIX = {"article": "src", "thought": "thought", "note": "note"}
RAW_DIR = {"article": "articles", "thought": "thoughts", "note": "notes"}
WIKI_DIR = {"entity": "entities", "topic": "topics", "summary": "summaries"}


@dataclass
class NormalizedInput:
    type: str
    title: str
    text: str


@dataclass
class RawRecord:
    id: str
    type: str
    title: str | None
    path: Path
    frontmatter: dict[str, Any]
    content: str
    status: str
    duplicated: bool = False


@dataclass
class WikiPage:
    id: str
    type: str
    title: str
    slug: str
    path: Path
    frontmatter: dict[str, Any]
    body: str


@dataclass
class SearchHit:
    layer: str
    id: str
    type: str
    title: str
    snippet: str
    score: float
    path: str


@dataclass
class LintIssue:
    check: str
    page_id: str
    message: str
    suggestion: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def today_compact() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y%m%d")


def generate_raw_id(raw_type: str) -> str:
    if raw_type not in RAW_TYPES:
        raise ValueError(f"unsupported raw type: {raw_type}")
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    suffix = "".join(alphabet[secrets.randbelow(len(alphabet))] for _ in range(6))
    return f"{RAW_PREFIX[raw_type]}_{today_compact()}_{suffix}"


def sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-_")
    return normalized or "page"


def wiki_page_id(page_type: str, slug: str, source_id: str | None = None) -> str:
    if page_type == "summary":
        if not source_id:
            raise ValueError("summary page requires source_id")
        return f"summary_{source_id}"
    return f"{page_type}_{slug}"


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def merge_unique(*items: list[Any] | tuple[Any, ...]) -> list[Any]:
    result: list[Any] = []
    seen: set[str] = set()
    for group in items:
        for item in group:
            key = str(item)
            if key and key not in seen:
                result.append(item)
                seen.add(key)
    return result


def split_markdown(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip()
    body = text[end + 4 :].lstrip("\n")
    return load_yaml(raw), body


def compose_markdown(frontmatter: dict[str, Any], body: str) -> str:
    return f"---\n{dump_yaml(frontmatter)}---\n\n{body.rstrip()}\n"


def load_markdown(path: Path) -> tuple[dict[str, Any], str]:
    return split_markdown(path.read_text(encoding="utf-8"))


def write_markdown(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(compose_markdown(frontmatter, body), encoding="utf-8")


def load_yaml(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    if yaml is not None:
        data = yaml.safe_load(text)
        return data or {}
    return _load_yaml_minimal(text)


def dump_yaml(data: dict[str, Any]) -> str:
    if yaml is not None:
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    return _dump_yaml_minimal(data)


def _load_yaml_minimal(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    current_map: dict[str, Any] | None = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        if line.startswith("  ") and current_map is not None:
            key, raw_value = line.strip().split(":", 1)
            current_map[key.strip()] = _parse_scalar(raw_value.strip())
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value == "":
            nested: dict[str, Any] = {}
            result[key.strip()] = nested
            current_map = nested
        else:
            result[key.strip()] = _parse_scalar(value)
            current_map = None
    return result


def _parse_scalar(value: str) -> Any:
    if value in {"", "null", "None", "~"}:
        return None
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(part.strip()) for part in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def _dump_yaml_minimal(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for child_key, child_value in value.items():
                lines.append(f"  {child_key}: {_format_scalar(child_value)}")
            continue
        lines.append(f"{key}: {_format_scalar(value)}")
    return "\n".join(lines) + "\n"


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(_format_scalar(item) for item in value) + "]"
    text = str(value)
    if not text or any(ch in text for ch in [":", "#", "[", "]", "{", "}", ","]) or text.strip() != text:
        return '"' + text.replace('"', '\\"') + '"'
    return text
