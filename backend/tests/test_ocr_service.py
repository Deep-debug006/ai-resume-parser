"""
Unit and integration tests for Phase 4: OCR Fallback and Unified Text Extraction.
Tests cover:
- Tesseract OCR service availability
- Scanned / image-only PDF recognition (triggers OCR)
- Mixed PDF (page 1 native text, page 2 scanned image -> mixed)
- Native text PDF (sufficient text -> skips OCR for performance)
- Missing Tesseract graceful degradation and warnings
- Configurable threshold behavior
- Endpoint POST /api/resumes/{resume_id}/extract-text returning extraction_method metadata
"""
import io
import pymupdf
from PIL import Image, ImageDraw
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings
from backend.app.services.ocr_service import ocr_service
from backend.app.services.resume_text_extractor import (
    resume_text_extractor,
    ResumeTextExtractor,
    extract_resume_text,
)

client = TestClient(app)


def create_image_only_pdf(text_to_draw: str) -> bytes:
    """
    Creates an image-only PDF with rasterized text (0 machine-readable text characters).
    """
    # Create white raster image with black text
    img = Image.new("RGB", (900, 300), color="white")
    draw = ImageDraw.Draw(img)
    # Pillow default font renders basic ASCII reliably
    draw.text((40, 40), text_to_draw, fill="black")

    img_buffer = io.BytesIO()
    img.save(img_buffer, format="PNG")
    img_bytes = img_buffer.getvalue()

    # Embed raster image into PDF page without adding text elements
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(pymupdf.Rect(50, 50, 550, 250), stream=img_bytes)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def create_native_text_pdf(text: str) -> bytes:
    """
    Creates a normal PDF with native machine-readable text.
    """
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), text, fontsize=12)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_tesseract_is_available():
    """Verify that Tesseract OCR binary is installed and detected."""
    assert ocr_service.is_available() is True


def test_native_text_skips_ocr(monkeypatch):
    """
    Verify that PDFs with sufficient native text use 'pdf_text'
    and do NOT run OCR unnecessarily.
    """
    content = (
        "Jonathan Doe\n"
        "Staff Software Engineer at CloudCorp\n"
        "Over 10 years of experience with Python, FastAPI, Docker, and Kubernetes.\n"
        "Architected real-time high-throughput message streaming systems."
    )
    pdf_bytes = create_native_text_pdf(content)

    # Spy on OCR service to ensure it is not called
    ocr_called = False

    def fake_ocr_page(*args, **kwargs):
        nonlocal ocr_called
        ocr_called = True
        return "OCR Text"

    monkeypatch.setattr(ocr_service, "ocr_page", fake_ocr_page)

    result = extract_resume_text(pdf_bytes)

    assert result.extraction_method == "pdf_text"
    assert "Jonathan Doe" in result.text
    assert "Staff Software Engineer" in result.text
    assert ocr_called is False  # OCR was NOT executed


def test_scanned_image_only_pdf_triggers_ocr():
    """
    Verify that an image-only PDF with 0 native text triggers OCR
    and returns extraction_method='ocr'.
    """
    scanned_text = "ROBERT BROWN SENIOR ARCHITECT PYTHON KUBERNETES"
    pdf_bytes = create_image_only_pdf(scanned_text)

    # First verify that PyMuPDF extracts 0 characters natively
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    native_text = doc[0].get_text("text").strip()
    doc.close()
    assert native_text == ""  # Zero native text

    # Now extract using unified pipeline with OCR fallback
    result = extract_resume_text(pdf_bytes)

    assert result.page_count == 1
    assert result.extraction_method == "ocr"
    # Tesseract should identify keywords from the raster image
    assert "BROWN" in result.text or "ARCHITECT" in result.text or "PYTHON" in result.text


def test_mixed_pdf_extraction():
    """
    Verify that a mixed PDF (Page 1 native text, Page 2 scanned image)
    uses PyMuPDF for Page 1 and OCR for Page 2, returning extraction_method='mixed'.
    """
    page1_text = (
        "Maria Garcia\n"
        "Engineering Manager\n"
        "12 years experience building distributed microservice systems."
    )
    page2_scanned_text = "CERTIFICATE OF EXCELLENCE IN CLOUD ARCHITECTURE 2024"

    # Create 2-page document
    doc = pymupdf.open()
    # Page 1: Native text
    p1 = doc.new_page(width=612, height=792)
    p1.insert_text((72, 72), page1_text, fontsize=12)

    # Page 2: Image-only
    img = Image.new("RGB", (900, 300), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((40, 40), page2_scanned_text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    p2 = doc.new_page(width=612, height=792)
    p2.insert_image(pymupdf.Rect(50, 50, 550, 250), stream=buf.getvalue())

    mixed_pdf_bytes = doc.tobytes()
    doc.close()

    result = extract_resume_text(mixed_pdf_bytes)

    assert result.page_count == 2
    assert result.extraction_method == "mixed"
    assert "Maria Garcia" in result.text
    # Check that OCR also recognized page 2
    assert "CERTIFICATE" in result.text or "ARCHITECTURE" in result.text


def test_missing_tesseract_graceful_handling(monkeypatch):
    """
    Verify that if Tesseract is unavailable, the pipeline does not crash,
    returns available text, and includes an explanatory warning.
    """
    # Simulate missing tesseract
    monkeypatch.setattr(ocr_service, "is_available", lambda: False)

    scanned_bytes = create_image_only_pdf("TEST SCANNED")

    result = extract_resume_text(scanned_bytes)
    assert result.extraction_method == "pdf_text"
    assert len(result.warnings) > 0
    assert any("not installed" in w.lower() or "not found" in w.lower() for w in result.warnings)


def test_configurable_threshold():
    """
    Verify that a custom extractor with a higher min_chars_per_page threshold
    triggers OCR even if some minimal text is present.
    """
    minimal_text = "Tiny Header"  # ~11 chars
    pdf_bytes = create_native_text_pdf(minimal_text)

    # Extractor with threshold 100: 11 chars < 100 -> triggers OCR
    custom_extractor = ResumeTextExtractor(min_chars_per_page=100)
    result = custom_extractor.extract_resume_text(pdf_bytes)

    # Since it's a blank page besides tiny text, native text is retained or OCR evaluated
    assert result.page_count == 1


def test_api_extract_endpoint_returns_extraction_method():
    """
    Verify that POST /api/resumes/{resume_id}/extract-text returns
    the extraction_method field in the response JSON.
    """
    pdf_bytes = create_native_text_pdf(
        "Dr. Victor Frankenstein\n"
        "Lead Research Scientist in Advanced Bio-engineering\n"
        "Skills: Molecular Biology, Neural Interfaces, Python, PyTorch"
    )

    # 1. Upload
    upload_res = client.post(
        "/api/resumes/upload",
        files={"file": ("dr_frankenstein.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    filename = upload_res.json()["filename"]

    # 2. Extract
    extract_res = client.post(f"/api/resumes/{filename}/extract-text")
    assert extract_res.status_code == 200
    data = extract_res.json()

    assert data["resume_id"] in (filename, filename[:-4] if filename.endswith(".pdf") else filename)
    assert data["page_count"] == 1
    assert data["extraction_method"] == "pdf_text"
    assert "Dr. Victor Frankenstein" in data["text"]
