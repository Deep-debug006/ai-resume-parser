"""
Unit tests for the resume upload endpoint and validation pipeline.
"""
import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)

# Helper valid minimal PDF byte sequence
VALID_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n"
    b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF\n"
)


def test_upload_valid_pdf_success():
    """Verify that a genuine PDF file uploads successfully and generates safe metadata."""
    file_content = io.BytesIO(VALID_PDF_BYTES)
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("candidate_john_doe.pdf", file_content, "application/pdf")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Resume uploaded successfully"
    assert data["original_filename"] == "candidate_john_doe.pdf"
    assert data["filename"].endswith(".pdf")
    assert "candidate" in data["filename"]
    assert data["size_bytes"] == len(VALID_PDF_BYTES)
    assert "uploaded_at" in data


def test_upload_non_pdf_extension_rejected():
    """Verify that non-PDF extensions (e.g. .docx, .png, .sh) are rejected."""
    file_content = io.BytesIO(b"Hello world document")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.docx", file_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


def test_upload_empty_pdf_rejected():
    """Verify that an empty (0 byte) PDF is rejected."""
    file_content = io.BytesIO(b"")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("empty.pdf", file_content, "application/pdf")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_corrupt_pdf_missing_magic_bytes_rejected():
    """Verify that a file renamed to .pdf without %PDF- magic bytes is rejected."""
    fake_pdf = io.BytesIO(b"This is just arbitrary text pretending to be a PDF document.")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("fake_resume.pdf", fake_pdf, "application/pdf")},
    )

    assert response.status_code == 400
    assert "Invalid PDF signature" in response.json()["detail"]


def test_upload_corrupt_pdf_truncated_no_eof_rejected():
    """Verify that a truncated PDF missing %%EOF trailer is rejected."""
    truncated_pdf = io.BytesIO(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n")
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("truncated.pdf", truncated_pdf, "application/pdf")},
    )

    assert response.status_code == 400
    assert "missing the required '%%EOF'" in response.json()["detail"]


def test_upload_oversized_file_rejected(monkeypatch):
    """Verify that files exceeding the maximum size limit are rejected with 413."""
    # Temporarily set limit to 100 bytes for test
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0.0001)  # ~104 bytes

    oversized_data = VALID_PDF_BYTES + (b"A" * 500) + b"\n%%EOF"
    file_content = io.BytesIO(oversized_data)

    response = client.post(
        "/api/resumes/upload",
        files={"file": ("huge_resume.pdf", file_content, "application/pdf")},
    )

    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_upload_missing_file_rejected():
    """Verify that calling the endpoint without a file field returns 422 Unprocessable Entity."""
    response = client.post("/api/resumes/upload", data={})
    assert response.status_code == 422
