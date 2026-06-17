from __future__ import annotations

import re

from .errors import ValidationError
from .models import NormalizedInput, RAW_TYPES


ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\ufeff]")


class Normalizer:
    """Normalize already-extracted plain text. This module never reads URLs."""

    def normalize(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = ZERO_WIDTH_RE.sub("", text)
        lines = [line.rstrip() for line in text.split("\n")]
        cleaned = "\n".join(lines).strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned

    def build(self, text: str, type: str = "thought", title: str | None = None) -> NormalizedInput:
        if type not in RAW_TYPES:
            raise ValidationError("unsupported raw type", type=type, allowed=sorted(RAW_TYPES))
        normalized = self.normalize(text)
        if not normalized:
            raise ValidationError("text is empty after normalization")
        resolved_title = title.strip() if title and title.strip() else self._first_line_title(normalized)
        return NormalizedInput(type=type, title=resolved_title, text=normalized)

    def _first_line_title(self, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped[:40]
        return "Untitled"
