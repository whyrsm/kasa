from __future__ import annotations

from fastapi.testclient import TestClient

from kasa_api.main import app


client = TestClient(app)


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
        "error": "PARSE_FAILED",
        "message": "Could not parse PDF.",
    }
