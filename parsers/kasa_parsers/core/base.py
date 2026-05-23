from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .models import Statement


class StatementParser(ABC):
    name: str  # internal id, e.g. "cimb_cc"
    bank_label: str  # used in output filenames, e.g. "CC-CIMB"
    default_password: str | None = None

    @classmethod
    @abstractmethod
    def signature(cls, text: str) -> bool:
        """Return True if `text` looks like a statement this parser handles."""

    @abstractmethod
    def parse(self, pages: list[list[str]], source_path: Path) -> Statement:
        """Parse decrypted page-lines into a Statement."""
