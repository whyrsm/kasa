from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from kasa_parsers.core import InvalidPdfError, PdfDecryptError, UnknownStatementError

from ..schemas import ApiError, StatementParseResponse
from ..services.parsing import parse_pdf_to_response

router = APIRouter(prefix="/api/statements", tags=["statements"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
_COPY_CHUNK_SIZE = 1024 * 1024


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


@router.post(
    "/parse",
    response_model=StatementParseResponse,
    responses={400: {"model": ApiError}, 413: {"model": ApiError}},
)
async def parse_statement(
    file: UploadFile = File(...),
    password: str | None = Form(default=None),
    parser_name: str | None = Form(default=None),
) -> StatementParseResponse:
    source_filename = Path(file.filename or "statement.pdf").name
    if not source_filename.lower().endswith(".pdf"):
        raise _api_error(
            status_code=400,
            code="UNSUPPORTED_FILE",
            message="Upload a PDF statement file.",
        )

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
            temp_path = Path(temp.name)
            _copy_with_limit(file.file, temp, MAX_UPLOAD_BYTES)

        return parse_pdf_to_response(
            temp_path,
            source_filename=source_filename,
            password=password,
            parser_name=parser_name,
        )
    except _UploadTooLarge as e:
        raise _api_error(
            status_code=413,
            code="FILE_TOO_LARGE",
            message=f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        ) from e
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
    finally:
        await file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _api_error(*, status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": code, "message": message})
