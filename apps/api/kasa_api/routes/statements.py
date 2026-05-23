from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from kasa_parsers.core import (
    InvalidPdfError,
    PdfDecryptError,
    Statement,
    UnknownStatementError,
    statement_to_delimited,
)
from kasa_parsers.service import parse_statement_pdf

from ..schemas import ApiError, StatementParseResponse
from ..services.parsing import statement_to_response

router = APIRouter(prefix="/api/statements", tags=["statements"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
_COPY_CHUNK_SIZE = 1024 * 1024


@router.post(
    "/parse",
    response_model=StatementParseResponse,
    responses={400: {"model": ApiError}, 413: {"model": ApiError}},
)
async def parse_statement(
    file: Annotated[UploadFile, File()],
    password: Annotated[str | None, Form()] = None,
    parser_name: Annotated[str | None, Form()] = None,
) -> StatementParseResponse:
    source_filename = _validate_pdf_filename(file)
    temp_path: Path | None = None
    try:
        temp_path = _spool_upload(file)
        statement = _parse_pdf(temp_path, password, parser_name)
        return statement_to_response(statement, source_filename=source_filename)
    finally:
        await file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@router.post(
    "/export",
    responses={
        200: {"content": {"text/plain": {}}},
        400: {"model": ApiError},
        413: {"model": ApiError},
    },
)
async def export_statement(
    file: Annotated[UploadFile, File()],
    password: Annotated[str | None, Form()] = None,
    parser_name: Annotated[str | None, Form()] = None,
    format: Annotated[Literal["tsv", "csv"], Query()] = "tsv",
) -> Response:
    """Parse a PDF and return delimited-text export of ALL transactions (no filter)."""
    source_filename = _validate_pdf_filename(file)
    temp_path: Path | None = None
    try:
        temp_path = _spool_upload(file)
        statement = _parse_pdf(temp_path, password, parser_name)
    finally:
        await file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    delimiter = "\t" if format == "tsv" else ","
    body = statement_to_delimited(statement, source_filename, delimiter=delimiter)
    media_type = "text/tab-separated-values" if format == "tsv" else "text/csv"
    download_name = f"{statement.period}_{statement.bank_label}.{format}"
    return Response(
        content=body,
        media_type=f"{media_type}; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


def _validate_pdf_filename(file: UploadFile) -> str:
    source_filename = Path(file.filename or "statement.pdf").name
    if not source_filename.lower().endswith(".pdf"):
        raise _api_error(
            status_code=400,
            code="UNSUPPORTED_FILE",
            message="Upload a PDF statement file.",
        )
    return source_filename


def _spool_upload(file: UploadFile) -> Path:
    """Copy upload to a temp .pdf file. Raises 413 if it exceeds the size limit."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp_path = Path(temp.name)
        try:
            _copy_with_limit(file.file, temp, MAX_UPLOAD_BYTES)
        except _UploadTooLarge as e:
            temp_path.unlink(missing_ok=True)
            raise _api_error(
                status_code=413,
                code="FILE_TOO_LARGE",
                message=f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
            ) from e
    return temp_path


def _parse_pdf(
    temp_path: Path,
    password: str | None,
    parser_name: str | None,
) -> Statement:
    """Parse a PDF, translating parser errors into 400 API errors."""
    try:
        return parse_statement_pdf(
            temp_path,
            password_override=_none_if_blank(password),
            parser_name=_none_if_blank(parser_name),
        )
    except InvalidPdfError as e:
        raise _api_error(
            status_code=400,
            code="INVALID_PDF",
            message="Could not read file as a PDF.",
        ) from e
    except PdfDecryptError as e:
        raise _api_error(
            status_code=400,
            code="PDF_DECRYPT_FAILED",
            message="Wrong or missing password.",
        ) from e
    except UnknownStatementError as e:
        raise _api_error(
            status_code=400,
            code="UNSUPPORTED_STATEMENT",
            message=str(e),
        ) from e
    except ValueError as e:
        raise _api_error(
            status_code=400,
            code="PARSE_FAILED",
            message="Could not extract transactions from this statement.",
        ) from e


class _UploadTooLarge(Exception):
    pass


def _copy_with_limit(src, dst, limit: int) -> None:
    total = 0
    while True:
        chunk = src.read(_COPY_CHUNK_SIZE)
        if not chunk:
            return
        total += len(chunk)
        if total > limit:
            raise _UploadTooLarge()
        dst.write(chunk)


def _none_if_blank(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _api_error(*, status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": code, "message": message})
