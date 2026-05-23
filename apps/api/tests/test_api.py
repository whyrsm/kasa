from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from kasa_api.main import app


client = TestClient(app, raise_server_exceptions=False)


def test_health() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parsers_includes_cimb() -> None:
    response = client.get("/api/parsers")

    assert response.status_code == 200
    parsers = response.json()
    assert parsers[0]["name"] == "cimb_cc"
    assert parsers[0]["display_name"] == "CIMB Niaga Sharia Credit Card"


def test_parse_rejects_non_pdf() -> None:
    response = client.post(
        "/api/statements/parse",
        files={"file": ("statement.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": "UNSUPPORTED_FILE",
        "message": "Upload a PDF statement file.",
    }


def test_parse_rejects_invalid_pdf_bytes() -> None:
    response = client.post(
        "/api/statements/parse",
        files={"file": ("statement.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "error": "INVALID_PDF",
        "message": "Could not read file as a PDF.",
    }


def test_export_rejects_non_pdf() -> None:
    response = client.post(
        "/api/statements/export",
        files={"file": ("statement.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "UNSUPPORTED_FILE"


def test_export_rejects_invalid_pdf_bytes() -> None:
    response = client.post(
        "/api/statements/export?format=tsv",
        files={"file": ("statement.pdf", b"not a pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_PDF"


def test_parse_rejects_oversize_upload() -> None:
    from kasa_api.routes.statements import MAX_UPLOAD_BYTES

    oversize = b"%PDF-1.4 " + b"\x00" * (MAX_UPLOAD_BYTES + 1)
    response = client.post(
        "/api/statements/parse",
        files={"file": ("big.pdf", oversize, "application/pdf")},
    )

    assert response.status_code == 413
    body = response.json()
    assert body["error"] == "FILE_TOO_LARGE"


def test_unhandled_exception_returns_500(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bug in parser code must surface as 500 INTERNAL, not a user-facing 400."""
    from kasa_api.routes import statements as statements_route

    def boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("parser exploded")

    monkeypatch.setattr(statements_route, "parse_statement_pdf", boom)

    response = client.post(
        "/api/statements/parse",
        files={"file": ("statement.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )

    assert response.status_code == 500
    assert response.json() == {"error": "INTERNAL", "message": "Internal server error."}
