from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from kasa_parsers.core import PdfDecryptError, UnknownStatementError

from ..schemas import ApiError, StatementParseResponse
from ..services.parsing import parse_pdf_to_response

router = APIRouter(prefix="/api/statements", tags=["statements"])


@router.post(
    "/parse",
    response_model=StatementParseResponse,
    responses={400: {"model": ApiError}},
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
            shutil.copyfileobj(file.file, temp)

        return parse_pdf_to_response(
            temp_path,
            source_filename=source_filename,
            password=password,
            parser_name=parser_name,
        )
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
            message=str(e),
        ) from e
    except Exception as e:
        raise _api_error(
            status_code=400,
            code="PARSE_FAILED",
            message="Could not parse PDF.",
        ) from e
    finally:
        await file.close()
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _api_error(*, status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": code, "message": message})
