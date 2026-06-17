from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KbError(Exception):
    """Base exception returned by the CLI as a structured error."""

    message: str
    code: str = "kb_error"
    detail: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "detail": self.detail}


class KbNotFoundError(KbError):
    def __init__(self, message: str = "knowledge base is not initialized", **detail: Any) -> None:
        super().__init__(message, "kb_not_found", detail)


class NotFoundError(KbError):
    def __init__(self, message: str = "record not found", **detail: Any) -> None:
        super().__init__(message, "not_found", detail)


class ValidationError(KbError):
    def __init__(self, message: str = "validation failed", **detail: Any) -> None:
        super().__init__(message, "validation_error", detail)


class ImmutableError(KbError):
    def __init__(self, message: str = "raw content is immutable", **detail: Any) -> None:
        super().__init__(message, "immutable_error", detail)
