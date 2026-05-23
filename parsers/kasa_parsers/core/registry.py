from __future__ import annotations

from .base import StatementParser

_REGISTRY: list[type[StatementParser]] = []


class UnknownStatementError(Exception):
    pass


def register_parser(cls: type[StatementParser]) -> type[StatementParser]:
    """Decorator: register a StatementParser subclass."""
    if cls not in _REGISTRY:
        _REGISTRY.append(cls)
    return cls


def all_parsers() -> list[type[StatementParser]]:
    return list(_REGISTRY)


def resolve_parser(text: str) -> type[StatementParser]:
    """Pick the first registered parser whose signature matches `text`."""
    for cls in _REGISTRY:
        if cls.signature(text):
            return cls
    raise UnknownStatementError(
        "no registered parser matched this statement. "
        f"Tried: {[c.name for c in _REGISTRY]}"
    )
