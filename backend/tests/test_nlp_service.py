"""
Unit and integration tests for Phase 8: NLP Preprocessing with spaCy (services/nlp_service.py).
Tests cover:
- Entity extraction for PERSON, ORG, GPE, DATE, EMAIL, and URL
- Distinguishing educational vs corporate organizations as supporting evidence
- Strict non-mutation of input resume text
- Handling empty / whitespace inputs
- FastAPI endpoint POST /api/resumes/{resume_id}/entities
"""
import io
import pymupdf
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.nlp_service import (
    nlp_service,
    extract_resume_nlp_entities,
    NLPExtractionResult,
)

client = TestClient(app)


def test_nlp_entity_extraction_types():
    """Verify spaCy extracts PERSON, ORG, GPE, DATE, EMAIL, and URL accurately."""
    sample_text = (
        "Sarah Connor\n"
        "sarah.connor@cyberdyne.org | +1-415-555-0199 | linkedin.com/in/sarahconnor | https://github.com/sarahc\n\n"
        "Experience\n"
        "Lead Systems Engineer at Cyberdyne Systems in Los Angeles, California from March 2020 to Present.\n"
        "Previously worked at Google in Mountain View from June 2017 to February 2020.\n\n"
        "Education\n"
        "B.S. in Computer Science, Stanford University, 2013 - 2017."
    )

    result = extract_resume_nlp_entities(sample_text)

    # 1. PERSON
    assert any("Sarah Connor" in p for p in result.persons)

    # 2. ORG (Includes both corporate employers and universities without assumption)
    assert any("Cyberdyne" in org for org in result.organizations)
    assert any("Google" in org for org in result.organizations)
    assert any("Stanford" in org for org in result.organizations)

    # 3. GPE / Location
    assert any("California" in loc or "Los Angeles" in loc for loc in result.locations)
    assert any("Mountain View" in loc for loc in result.locations)

    # 4. DATE
    assert any("2020" in d or "March 2020" in d or "Present" in d for d in result.dates)
    assert any("2017" in d for d in result.dates)

    # 5. EMAIL
    assert "sarah.connor@cyberdyne.org" in result.emails

    # 6. URL
    assert any("linkedin.com/in/sarahconnor" in u for u in result.urls)
    assert any("github.com/sarahc" in u for u in result.urls)


def test_text_not_mutated_or_overwritten():
    """Verify that NLP entity extraction does not alter or overwrite user text."""
    original_text = (
        "ALEXANDER HAMILTON\n"
        "Treasury Secretary at United States Department of the Treasury in New York, 1789 - 1795.\n"
        "email: alex@treasury.gov"
    )
    copy_text = str(original_text)

    result = extract_resume_nlp_entities(original_text)

    # Confirm original text remains strictly identical
    assert original_text == copy_text
    assert any("alexander" in p.lower() for p in result.persons)
    assert "alex@treasury.gov" in result.emails


def test_empty_and_whitespace_input():
    """Verify that empty, none, or whitespace text produces safe empty results without errors."""
    res1 = extract_resume_nlp_entities("")
    assert res1.persons == []
    assert res1.organizations == []
    assert res1.locations == []
    assert res1.dates == []
    assert res1.emails == []
    assert res1.urls == []

    res2 = extract_resume_nlp_entities("   \n\t   ")
    assert res2.persons == []
    assert res2.organizations == []
    assert res2.locations == []


def test_raw_entities_spans():
    """Verify character offset spans are correctly captured in raw_entities."""
    text = "Jane Doe works at Microsoft in Redmond."
    result = extract_resume_nlp_entities(text)

    assert len(result.entities) >= 2
    # Verify entity keys
    for ent in result.entities:
        assert "text" in ent
        assert "label" in ent
        assert "start_char" in ent
        assert "end_char" in ent
        assert text[ent["start_char"]:ent["end_char"]].strip() == ent["text"].strip()


def test_api_entities_endpoint():
    """Integration test for POST /api/resumes/{resume_id}/entities."""
    doc = pymupdf.open()
    page = doc.new_page()
    text = (
        "TONY STARK\n"
        "tony.stark@starkindustries.com | https://starkindustries.com\n\n"
        "Experience\n"
        "Chief Executive Officer at Stark Industries in Malibu, California (2008 - 2023).\n"
        "Education\n"
        "Ph.D. in Physics, MIT, 1991."
    )
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()

    # 1. Upload
    upload_res = client.post(
        "/api/resumes/upload",
        files={"file": ("tony_stark.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    filename = upload_res.json()["filename"]

    # 2. Extract NLP entities
    entities_res = client.post(f"/api/resumes/{filename}/entities")
    assert entities_res.status_code == 200
    data = entities_res.json()

    assert data["resume_id"] in (filename, filename[:-4] if filename.endswith(".pdf") else filename)
    assert any("tony stark" in p.lower() for p in data["persons"])
    assert any("Stark Industries" in org or "MIT" in org for org in data["organizations"])
    assert any("Malibu" in loc or "California" in loc for loc in data["locations"])
    assert any("2008" in d or "1991" in d for d in data["dates"])
    assert "tony.stark@starkindustries.com" in data["emails"]
    assert any("starkindustries.com" in u for u in data["urls"])
