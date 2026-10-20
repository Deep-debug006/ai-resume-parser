"""
Unit and integration tests for Phase 6: Resume Section Detection (services/section_detector.py).
Tests cover:
- Standard resume parsing
- Different section heading variations (Work Experience, Professional Experience, Employment History)
- Missing sections handling
- Unusual section ordering
- All-uppercase headings (WORK EXPERIENCE, EDUCATION, TECHNICAL SKILLS)
- Headings decorated with punctuation (colons, dashes, brackets, numbering)
- Preservation of unclassified text
- API endpoint POST /api/resumes/{resume_id}/sections
"""
import io
import pymupdf
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.section_detector import (
    section_detector,
    detect_resume_sections,
    SectionDetectionResult,
)

client = TestClient(app)


def test_standard_resume_sections():
    """Verify section detection on a standard resume with clean canonical sections."""
    text = (
        "ALICE WALKER\n"
        "alice.walker@example.com | +1 (555) 019-2834 | linkedin.com/in/alicewalker\n\n"
        "Summary\n"
        "Accomplished Cloud Solutions Architect with 6+ years in distributed microservices.\n\n"
        "Education\n"
        "B.S. in Software Engineering, University of Washington, 2018 - 2022\n\n"
        "Skills\n"
        "• Languages: Python, Go, TypeScript\n"
        "• Cloud: AWS (EC2, S3, Lambda), GCP\n\n"
        "Experience\n"
        "Senior Cloud Engineer at TechGiant (2022 - Present)\n"
        "• Designed and maintained multi-region Kubernetes clusters.\n\n"
        "Projects\n"
        "Distributed KV Store (Go, Raft Consensus)\n"
        "• Implemented raft protocol supporting fault-tolerant linearizable reads."
    )

    result = detect_resume_sections(text)

    assert "alice.walker@example.com" in result.contact
    assert "Accomplished Cloud Solutions Architect" in result.summary
    assert "University of Washington" in result.education
    assert "Python, Go, TypeScript" in result.skills
    assert "Senior Cloud Engineer at TechGiant" in result.experience
    assert "Distributed KV Store" in result.projects
    assert "education" in result.detected_sections_list
    assert "skills" in result.detected_sections_list
    assert "experience" in result.detected_sections_list
    assert "projects" in result.detected_sections_list


def test_different_section_name_variations():
    """Verify that heading variations all map accurately to their canonical sections."""
    # Test variation 1: 'Professional Experience' and 'Technical Proficiencies'
    text1 = (
        "Professional Experience\n"
        "Backend Developer at CloudCo\n\n"
        "Technical Proficiencies\n"
        "Docker, Kubernetes, Terraform"
    )
    res1 = detect_resume_sections(text1)
    assert "Backend Developer at CloudCo" in res1.experience
    assert "Docker, Kubernetes, Terraform" in res1.skills

    # Test variation 2: 'Work History' and 'Academic Qualifications'
    text2 = (
        "Work History\n"
        "Staff Engineer at Meta\n\n"
        "Academic Qualifications\n"
        "M.S. in Computer Science"
    )
    res2 = detect_resume_sections(text2)
    assert "Staff Engineer at Meta" in res2.experience
    assert "M.S. in Computer Science" in res2.education

    # Test variation 3: 'Employment History' and 'Key Projects'
    text3 = (
        "Employment History\n"
        "Principal Architect at Stripe\n\n"
        "Key Projects\n"
        "Global Payment Gateway Engine"
    )
    res3 = detect_resume_sections(text3)
    assert "Principal Architect at Stripe" in res3.experience
    assert "Global Payment Gateway Engine" in res3.projects


def test_missing_sections():
    """Verify resumes omitting certain sections behave correctly without error."""
    text = (
        "JANE DOE\n"
        "jane@doe.com | 555-1234\n\n"
        "Education\n"
        "B.S. in Mathematics\n\n"
        "Skills\n"
        "Python, R, Statistics"
    )
    res = detect_resume_sections(text)
    assert res.education != ""
    assert res.skills != ""
    # These sections were not provided
    assert res.summary == ""
    assert res.experience == ""
    assert res.projects == ""
    assert res.certifications == ""


def test_unusual_section_ordering():
    """Verify sections are detected regardless of their order in the document."""
    text = (
        "Technical Skills\n"
        "Rust, C++, WebAssembly\n\n"
        "Projects\n"
        "High Performance Parser in Rust\n\n"
        "Certifications\n"
        "AWS Certified Solutions Architect Professional\n\n"
        "Education\n"
        "B.Tech in Information Technology\n\n"
        "Work Experience\n"
        "Systems Engineer at FastTech"
    )
    res = detect_resume_sections(text)
    assert "Rust, C++" in res.skills
    assert "High Performance Parser" in res.projects
    assert "AWS Certified" in res.certifications
    assert "B.Tech" in res.education
    assert "Systems Engineer at FastTech" in res.experience
    # Order in detected_sections_list reflects document flow
    assert res.detected_sections_list == ["skills", "projects", "certifications", "education", "experience"]


def test_all_uppercase_headings():
    """Verify uppercase heading variants are recognized properly."""
    text = (
        "PROFESSIONAL SUMMARY\n"
        "Seasoned engineering lead with demonstrated history of delivery.\n\n"
        "WORK EXPERIENCE\n"
        "Lead Architect at Global Logistics\n\n"
        "EDUCATION\n"
        "Bachelor of Science in Computer Engineering\n\n"
        "TECHNICAL SKILLS\n"
        "Python, PostgreSQL, Redis, Apache Kafka"
    )
    res = detect_resume_sections(text)
    assert "Seasoned engineering lead" in res.summary
    assert "Lead Architect at Global Logistics" in res.experience
    assert "Bachelor of Science" in res.education
    assert "Python, PostgreSQL" in res.skills


def test_headings_with_punctuation_and_numbering():
    """Verify headings decorated with colons, dashes, brackets, and numbering are handled."""
    text = (
        "1. SUMMARY:\n"
        "Dedicated DevOps and Platform Engineer.\n\n"
        "--- 2. WORK EXPERIENCE --- \n"
        "DevOps Engineer at Netflix\n\n"
        "[3. TECHNICAL SKILLS]\n"
        "Kubernetes, Helm, Terraform, Datadog\n\n"
        "### 4. PROJECTS:\n"
        "Automated Multi-Cluster Canary Deployment Controller"
    )
    res = detect_resume_sections(text)
    assert "Dedicated DevOps" in res.summary
    assert "DevOps Engineer at Netflix" in res.experience
    assert "Kubernetes, Helm" in res.skills
    assert "Automated Multi-Cluster" in res.projects


def test_unclassified_text_preservation():
    """Verify that non-contact unclassifiable text is stored in 'unclassified' without loss."""
    text = (
        "Random preliminary note or quote without contact info\n"
        "Second line of preamble\n\n"
        "Skills\n"
        "Python, Docker"
    )
    res = detect_resume_sections(text)
    assert "Python, Docker" in res.skills
    assert "Random preliminary note" in res.unclassified
    assert "Second line of preamble" in res.unclassified


def test_api_sections_endpoint():
    """Integration test for POST /api/resumes/{resume_id}/sections endpoint."""
    doc = pymupdf.open()
    page = doc.new_page()
    resume_content = (
        "CLARK KENT\n"
        "clark.kent@dailyplanet.com | Metropolis\n\n"
        "Summary\n"
        "Investigative Journalist and Crisis Response Specialist.\n\n"
        "Skills\n"
        "• Investigative Reporting, Speed Reading, Global Awareness\n\n"
        "Experience\n"
        "Senior Reporter at Daily Planet (2018 - Present)\n"
        "• Covered breaking international news under tight deadlines."
    )
    page.insert_text((72, 72), resume_content)
    pdf_bytes = doc.tobytes()
    doc.close()

    # 1. Upload
    upload_res = client.post(
        "/api/resumes/upload",
        files={"file": ("clark_kent.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert upload_res.status_code == 200
    filename = upload_res.json()["filename"]

    # 2. Call sections endpoint
    sections_res = client.post(f"/api/resumes/{filename}/sections")
    assert sections_res.status_code == 200
    data = sections_res.json()

    assert data["resume_id"] in (filename, filename[:-4] if filename.endswith(".pdf") else filename)
    assert "clark.kent@dailyplanet.com" in data["sections"]["contact"]
    assert "Investigative Journalist" in data["sections"]["summary"]
    assert "Investigative Reporting" in data["sections"]["skills"]
    assert "Senior Reporter at Daily Planet" in data["sections"]["experience"]
    assert "summary" in data["detected_sections_list"]
    assert "skills" in data["detected_sections_list"]
    assert "experience" in data["detected_sections_list"]
