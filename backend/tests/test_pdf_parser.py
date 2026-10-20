"""
Unit and integration tests for Phase 3: PDF text extraction using PyMuPDF.
Tests cover:
- Normal single-page PDF
- Multi-page PDF
- Empty / blank PDF
- Malformed PDF
- Endpoint POST /api/resumes/{resume_id}/extract-text
"""
import io
import pymupdf
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.pdf_parser import pdf_parser_service, CorruptPDFError, clean_page_lines
from backend.app.services.storage_service import storage_service

client = TestClient(app)


def create_sample_pdf(pages_text: list[str]) -> bytes:
    """Helper to generate a valid in-memory PDF with specified text per page using PyMuPDF."""
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page(width=612, height=792)
        page.insert_text((72, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_clean_page_lines():
    """Verify that text cleaning preserves line breaks and collapses excessive blanks."""
    raw = "Line 1\r\n\n\n\n\nLine 2   \u00a0\n\nLine 3"
    cleaned = clean_page_lines(raw)
    assert "Line 1" in cleaned
    assert "Line 2" in cleaned
    assert "Line 3" in cleaned
    # Ensure no runaway blank lines
    assert "\n\n\n" not in cleaned


def test_extract_text_normal_pdf():
    """Verify clean extraction from a standard single-page PDF resume."""
    text_content = (
        "Alice Walker\n"
        "Staff Software Engineer\n"
        "Skills: Python, FastAPI, Docker, PostgreSQL\n"
        "Experience: 8 years building scalable distributed backends."
    )
    pdf_bytes = create_sample_pdf([text_content])

    extracted_text, page_count = pdf_parser_service.extract_text(pdf_bytes)

    assert page_count == 1
    assert "Alice Walker" in extracted_text
    assert "Staff Software Engineer" in extracted_text
    assert "Python, FastAPI, Docker, PostgreSQL" in extracted_text
    # Line breaks preserved
    assert "\n" in extracted_text


def test_extract_text_multi_page_pdf():
    """Verify multi-page PDF extraction maintains page continuity without duplicates."""
    page_1 = "David Kim - Resume\nEducation: B.S. Computer Science\nSkills: Go, Kubernetes, Cloud"
    page_2 = "Professional Experience:\nLead Systems Architect at Acme Corp (2020 - Present)"

    pdf_bytes = create_sample_pdf([page_1, page_2])

    extracted_text, page_count = pdf_parser_service.extract_text(pdf_bytes)

    assert page_count == 2
    assert "David Kim - Resume" in extracted_text
    assert "Professional Experience:" in extracted_text
    assert "Lead Systems Architect" in extracted_text
    # Check that text is separated cleanly
    assert extracted_text.count("David Kim - Resume") == 1
    assert extracted_text.count("Acme Corp") == 1


def test_extract_text_empty_pdf():
    """Verify handling of completely empty or textless PDF documents."""
    # Test 1: Completely empty bytes
    text, pages = pdf_parser_service.extract_text(b"")
    assert text == ""
    assert pages == 0

    # Test 2: PDF with a blank page containing zero text
    blank_doc = pymupdf.open()
    blank_doc.new_page()
    blank_bytes = blank_doc.tobytes()
    blank_doc.close()

    text_blank, pages_blank = pdf_parser_service.extract_text(blank_bytes)
    assert text_blank == ""
    assert pages_blank == 1


def test_extract_text_malformed_pdf():
    """Verify that corrupt or malformed PDF data raises CorruptPDFError gracefully."""
    corrupt_bytes = b"%PDF-1.4\n<< INVALID UNREADABLE HEADER OBJECT 999 0 >> GARBAGE STREAM"

    with pytest.raises(CorruptPDFError):
        pdf_parser_service.extract_text(corrupt_bytes)


def test_api_extract_text_endpoint_success():
    """Integration test: Upload a PDF and call POST /api/resumes/{resume_id}/extract-text."""
    resume_content = (
        "Elena Rostova\n"
        "Machine Learning Engineer\n"
        "Expertise in Deep Learning, PyTorch, Transformers, NLP"
    )
    pdf_bytes = create_sample_pdf([resume_content])

    # 1. Upload the resume first
    upload_res = client.post(
        "/api/resumes/upload",
        files={"file": ("elena_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    filename = upload_data["filename"]

    # 2. Call text extraction endpoint
    extract_res = client.post(f"/api/resumes/{filename}/extract-text")
    assert extract_res.status_code == 200
    extract_data = extract_res.json()

    assert extract_data["resume_id"] in (filename, filename[:-4] if filename.endswith(".pdf") else filename)
    assert extract_data["page_count"] == 1
    assert "Elena Rostova" in extract_data["text"]
    assert "Machine Learning Engineer" in extract_data["text"]
    assert "PyTorch" in extract_data["text"]


def test_api_extract_text_endpoint_not_found():
    """Verify that requesting extraction for non-existent resume returns 404."""
    response = client.post("/api/resumes/non_existent_file_99999.pdf/extract-text")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_extract_text_empty_id():
    """Verify that whitespace or blank ID returns 400 or 404."""
    response = client.post("/api/resumes/%20/extract-text")
    assert response.status_code in (400, 404)
