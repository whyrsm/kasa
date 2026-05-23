from __future__ import annotations

from fastapi import APIRouter
from kasa_parsers.service import get_parser_metadata

from ..schemas import ParserMetadata

router = APIRouter(prefix="/api/parsers", tags=["parsers"])


@router.get("", response_model=list[ParserMetadata])
def list_parsers() -> list[dict[str, object]]:
    return get_parser_metadata()
