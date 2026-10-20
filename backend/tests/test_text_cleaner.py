"""
Unit tests for Phase 5: Resume Text Preprocessing (services/text_cleaner.py).
Verifies deterministic cleaning rules:
- Excessive whitespace collapsing
- Repeated blank lines compaction
- Inconsistent line endings (\r\n, \r, \n)
- Repeated and varied bullet points normalization
- Unnecessary spacing around punctuation
- Unicode normalization (NFKC ligatures, non-breaking spaces)
- Extraction artifacts (standalone page numbers, dehyphenation)
- Critical information preservation (emails, URLs, dates, numbers, CGPA, casing)
- Realistic raw resume before/after transformation
"""
import pytest
from backend.app.services.text_cleaner import clean_resume_text, text_cleaner, CleanedTextResult


def test_excessive_whitespace_collapsing():
    """Verify that multiple consecutive spaces and tabs inside lines are collapsed."""
    raw = "John   Doe     Senior    Cloud     Architect"
    res = clean_resume_text(raw)
    assert res.cleaned_text == "John Doe Senior Cloud Architect"
    assert "collapsed_inline_whitespace" in res.transformations_applied


def test_repeated_blank_lines_compaction():
    """Verify that runs of 3 or more newlines are collapsed to a single blank line (\\n\\n)."""
    raw = "Section 1: Experience\n\n\n\n\n\nSenior Software Engineer\n\n\n\nBuilt microservices."
    res = clean_resume_text(raw)
    assert "\n\n\n" not in res.cleaned_text
    assert "Section 1: Experience\n\nSenior Software Engineer\n\nBuilt microservices." == res.cleaned_text
    assert "compacted_blank_lines" in res.transformations_applied


def test_inconsistent_line_endings():
    """Verify that CRLF, CR, and LF line endings are normalized uniformly to \\n."""
    raw = "Line 1\r\nLine 2\rLine 3\nLine 4"
    res = clean_resume_text(raw)
    assert "\r" not in res.cleaned_text
    assert res.cleaned_text == "Line 1\nLine 2\nLine 3\nLine 4"


def test_repeated_and_varied_bullets():
    """Verify that varied unicode bullet characters and duplicates are normalized to standard bullet."""
    # Test duplicate bullets: "• • •", "••", and varied symbols like ■, ▶, ∙
    raw = (
        "• • Bullet with repeated markers\n"
        "▶ Custom triangle bullet point\n"
        "▪ Square bullet point\n"
        "• Standard bullet"
    )
    res = clean_resume_text(raw)
    lines = res.cleaned_text.split('\n')
    for line in lines:
        assert line.startswith("• ")
        assert "• •" not in line


def test_punctuation_spacing():
    """Verify spaces before commas/semicolons and inside parentheses are cleaned."""
    raw = "Skills : Python , FastAPI , Docker ; Kubernetes ( AWS , GCP )"
    res = clean_resume_text(raw)
    assert res.cleaned_text == "Skills: Python, FastAPI, Docker; Kubernetes (AWS, GCP)"
    assert "cleaned_punctuation_spacing" in res.transformations_applied


def test_unicode_normalization_and_ligatures():
    """Verify that NFKC decomposes typographic ligatures like 'fi' and cleans non-breaking spaces."""
    # \ufb01 is 'fi' ligature, \ufb02 is 'fl' ligature, \u00a0 is non-breaking space
    raw = "Proﬁcient in ofﬁce tools and ﬂowcharts\u00a0development"
    res = clean_resume_text(raw)
    assert "Proficient in office tools and flowcharts development" in res.cleaned_text
    assert "\ufb01" not in res.cleaned_text
    assert "\u00a0" not in res.cleaned_text


def test_dehyphenation_of_broken_words():
    """Verify that words split across lines with hyphens are re-joined properly."""
    raw = "exten-\nsive experi-\nence in archi-\ntecture"
    res = clean_resume_text(raw)
    assert "extensive experience in architecture" in res.cleaned_text


def test_removal_of_page_number_artifacts():
    """Verify standalone page number footers/headers are safely removed."""
    raw = (
        "Professional Experience\n"
        "Lead Architect at Acme\n"
        "Page 1 of 2\n"
        "Education\n"
        "B.S. in Computer Science\n"
        "- 2 -"
    )
    res = clean_resume_text(raw)
    assert "Page 1 of 2" not in res.cleaned_text
    assert "- 2 -" not in res.cleaned_text
    assert "Lead Architect at Acme\n\nEducation" in res.cleaned_text


def test_preservation_of_emails_and_urls():
    """CRITICAL: Ensure emails and URLs are NOT altered or corrupted by cleaning."""
    raw = (
        "Contact: alex.turner@deep-engineering.org\n"
        "Portfolio: https://alexturner.dev/projects?id=42&view=full\n"
        "LinkedIn: https://www.linkedin.com/in/alex-turner-89b\n"
        "GitHub: https://github.com/alex-turner"
    )
    res = clean_resume_text(raw)
    assert "alex.turner@deep-engineering.org" in res.cleaned_text
    assert "https://alexturner.dev/projects?id=42&view=full" in res.cleaned_text
    assert "https://www.linkedin.com/in/alex-turner-89b" in res.cleaned_text
    assert "https://github.com/alex-turner" in res.cleaned_text


def test_preservation_of_numbers_dates_and_cgpa():
    """CRITICAL: Ensure dates, percentages, phone numbers, and CGPA are fully intact."""
    raw = (
        "Phone: +1 (555) 321-7890\n"
        "Graduation Date: 05/2023 | High School: 2015 - 2019\n"
        "Academic Standing: CGPA: 3.94 / 4.0 (Top 2.5% of class)\n"
        "Increased system throughput by 45.8% and reduced latency from 120ms to 18ms."
    )
    res = clean_resume_text(raw)
    assert "+1 (555) 321-7890" in res.cleaned_text
    assert "05/2023" in res.cleaned_text
    assert "2015 - 2019" in res.cleaned_text
    assert "CGPA: 3.94 / 4.0" in res.cleaned_text
    assert "Top 2.5%" in res.cleaned_text
    assert "45.8%" in res.cleaned_text
    assert "120ms to 18ms" in res.cleaned_text


def test_preservation_of_letter_casing():
    """CRITICAL: Ensure casing is NOT lowercased (preserving acronyms, titles, and NER signals)."""
    raw = "CHIEF TECHNOLOGY OFFICER at AWS & GCP Partner, specializing in REST APIs, GraphQL & PostgreSQL."
    res = clean_resume_text(raw)
    assert "CHIEF TECHNOLOGY OFFICER" in res.cleaned_text
    assert "AWS & GCP" in res.cleaned_text
    assert "REST APIs" in res.cleaned_text
    assert "PostgreSQL" in res.cleaned_text


def test_realistic_raw_resume_before_after_cleaning():
    """
    Realistic end-to-end test comparing a messy raw PDF extraction with its cleaned output.
    """
    raw_resume = (
        "   SAMUEL R. VANCE   \r\n"
        "   samuel.vance@techcorp.io   |   +1-555-876-5432   |   github.com/svance   \r\n\r\n\r\n\n"
        "   PROFESSIONAL SUMMARY   \r\n"
        "Experienced full-stack engineer with 7+ years of exper-\r\n"
        "tise in distrib-\r\n"
        "uted systems , cloud infra ( AWS , GCP ) , and high-load web applications.\r\n\r\n"
        "Page 1 of 3\r\n"
        "   TECHNICAL SKILLS   \r\n"
        "• • Languages : Python , TypeScript , Go , SQL\r\n"
        "■ Frameworks : FastAPI , React 19 , Django , Node.js\r\n"
        "▶ Databases : PostgreSQL ( 14+ ) , Redis 7.0 , MongoDB\r\n\r\n\r\n"
        "   EDUCATION   \r\n"
        "M.S. in Computer Science | MIT ( 2017 - 2019 )\r\n"
        "CGPA : 3.89 / 4.00 ( Magna Cum Laude , 95.4% )\r\n"
    )

    result = clean_resume_text(raw_resume)
    cleaned = result.cleaned_text

    # Assertions on cleaned output
    assert "SAMUEL R. VANCE" in cleaned
    assert "samuel.vance@techcorp.io | +1-555-876-5432 | github.com/svance" in cleaned
    assert "expertise in distributed systems, cloud infra (AWS, GCP), and high-load" in cleaned
    assert "Page 1 of 3" not in cleaned
    assert "• Languages: Python, TypeScript, Go, SQL" in cleaned
    assert "• Frameworks: FastAPI, React 19, Django, Node.js" in cleaned
    assert "• Databases: PostgreSQL (14+), Redis 7.0, MongoDB" in cleaned
    assert "CGPA: 3.89 / 4.00 (Magna Cum Laude, 95.4%)" in cleaned

    # Verify metrics
    assert result.original_char_count > result.cleaned_char_count
    assert result.reduction_pct > 0.0
    assert len(result.transformations_applied) >= 4
