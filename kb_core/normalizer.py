from __future__ import annotations

import re

from .errors import ValidationError
from .models import NormalizedInput, RAW_TYPES


ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\ufeff]")


class Normalizer:
    """Validate already-extracted plain text and derive display metadata.

    The raw layer is the source of truth, so build() preserves the input text
    exactly as received from the caller. This module never reads URLs.
    """

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
        if not text.strip():
            raise ValidationError("text is empty")
        resolved_title = title.strip() if title and title.strip() else self._first_line_title(text)
        return NormalizedInput(type=type, title=resolved_title, text=text)

    def _first_line_title(self, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip().lstrip("#").strip()
            if stripped:
                return stripped[:40]
        return "Untitled"
