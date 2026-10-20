"""
Deterministic resume section detection and segmentation service.
Classifies normalized resume text into logical canonical sections:
Contact, Summary, Objective, Education, Skills, Experience, Projects,
Certifications, Achievements, Publications, Positions of Responsibility,
Extracurricular Activities, and Interests.

Preserves all unclassified text in a dedicated 'unclassified' container.
No LLM or machine learning models used.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


# Canonical section identifiers
CANONICAL_SECTIONS = [
    "contact",
    "summary",
    "objective",
    "education",
    "skills",
    "experience",
    "projects",
    "certifications",
    "achievements",
    "publications",
    "positions_of_responsibility",
    "extracurricular",
    "interests",
    "unclassified",
]


# Keyword and regex patterns for heading mapping to canonical sections
SECTION_HEADING_PATTERNS: Dict[str, List[str]] = {
    "summary": [
        r"professional\s+summary",
        r"executive\s+summary",
        r"career\s+summary",
        r"summary\s+of\s+qualifications",
        r"summary",
        r"profile",
        r"personal\s+profile",
        r"professional\s+profile",
        r"about\s+me",
        r"bio",
        r"background",
        r"overview",
    ],
    "objective": [
        r"career\s+objective",
        r"professional\s+objective",
        r"job\s+objective",
        r"objective",
    ],
    "education": [
        r"education(?:al)?(?:\s+(?:background|history|qualifications|details|records))?",
        r"academic\s+(?:background|qualifications|history|records|details|achievements)",
        r"academics",
        r"degrees(?:\s+and\s+diplomas)?",
        r"qualifications",
        r"university\s+education",
    ],
    "skills": [
        r"technical\s+skills",
        r"key\s+skills",
        r"core\s+skills",
        r"core\s+competencies",
        r"skills\s+(&|and)\s+(tools|technologies|proficiencies|abilities)",
        r"technical\s+proficiencies",
        r"technologies(\s+used)?",
        r"tech\s+stack",
        r"tools\s+(&|and)\s+technologies",
        r"programming\s+languages",
        r"areas\s+of\s+expertise",
        r"expertise",
        r"skills",
    ],
    "experience": [
        r"work\s+experience",
        r"professional\s+experience",
        r"employment\s+history",
        r"employment",
        r"work\s+history",
        r"career\s+history",
        r"relevant\s+experience",
        r"industry\s+experience",
        r"experience",
        r"internships?(?:\s+experience)?",
        r"professional\s+background",
        r"practical\s+experience",
    ],
    "projects": [
        r"academic\s+projects",
        r"personal\s+projects",
        r"technical\s+projects",
        r"key\s+projects",
        r"selected\s+projects",
        r"recent\s+projects",
        r"software\s+projects",
        r"projects",
    ],
    "certifications": [
        r"certifications?(?:\s+and\s+licenses)?",
        r"licenses?(?:\s+and\s+certifications)?",
        r"professional\s+certifications?",
        r"certificates?",
        r"courses\s+(&|and)\s+certifications?",
    ],
    "achievements": [
        r"achievements?",
        r"honors?(?:\s+(&|and)\s+awards)?",
        r"awards?(?:\s+(&|and)\s+honors)?",
        r"key\s+achievements?",
        r"accomplishments?",
        r"distinctions?",
    ],
    "publications": [
        r"publications?(?:\s+(&|and)\s+papers)?",
        r"research\s+papers?",
        r"research\s+publications?",
        r"patents?(?:\s+(&|and)\s+publications)?",
        r"papers?",
    ],
    "positions_of_responsibility": [
        r"positions?\s+of\s+responsibility",
        r"leadership(?:\s+(&|and)\s+volunteering)?",
        r"leadership\s+experience",
        r"responsibilities",
        r"roles\s+and\s+responsibilities",
    ],
    "extracurricular": [
        r"extra-?curricular\s+activities",
        r"co-?curricular\s+activities",
        r"volunteer(?:\s+work|\s+experience)?",
        r"community\s+(?:involvement|service)",
        r"activities",
    ],
    "interests": [
        r"interests?",
        r"hobbies?(?:\s+(&|and)\s+interests)?",
        r"personal\s+interests?",
        r"areas\s+of\s+interest",
    ],
    "contact": [
        r"contact(?:\s+information|\s+details)?",
        r"personal\s+(?:information|details)",
    ],
}


@dataclass
class SectionSpan:
    """Represents a classified span of text belonging to a section."""
    section_name: str
    original_heading: str
    content: str
    start_line: int
    end_line: int


@dataclass
class SectionDetectionResult:
    """
    Structured outcome of section detection.
    Provides standard attributes for direct dot/dict access.
    """
    contact: str = ""
    summary: str = ""
    objective: str = ""
    education: str = ""
    skills: str = ""
    experience: str = ""
    projects: str = ""
    certifications: str = ""
    achievements: str = ""
    publications: str = ""
    positions_of_responsibility: str = ""
    extracurricular: str = ""
    interests: str = ""
    unclassified: str = ""
    detected_sections_list: List[str] = field(default_factory=list)
    raw_headings: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Returns structured JSON-serializable dictionary."""
        return {
            "contact": self.contact,
            "summary": self.summary,
            "objective": self.objective,
            "education": self.education,
            "skills": self.skills,
            "experience": self.experience,
            "projects": self.projects,
            "certifications": self.certifications,
            "achievements": self.achievements,
            "publications": self.publications,
            "positions_of_responsibility": self.positions_of_responsibility,
            "extracurricular": self.extracurricular,
            "interests": self.interests,
            "unclassified": self.unclassified,
            "detected_sections_list": self.detected_sections_list,
            "raw_headings": self.raw_headings,
        }


class SectionDetector:
    """
    Deterministic rule-based resume section segmenter.
    """

    def __init__(self):
        # Compile heading patterns for efficient matching
        self._compiled_patterns: List[Tuple[str, re.Pattern]] = []
        prefix = r"^(?:[\d\.\-\–\—\*\#\:\s\|\[\]\(\)\{\}\>\<\~\=]*)(?:"
        suffix = r")(?:[\:\s\-\–\—\|\.\[\]\(\)\{\}\>\<\~\=]*)$"
        for canonical, patterns in SECTION_HEADING_PATTERNS.items():
            for p in patterns:
                # Matches heading as a standalone line or with standard numbering/decorators
                pattern_str = prefix + p + suffix
                regex = re.compile(pattern_str, re.IGNORECASE)
                self._compiled_patterns.append((canonical, regex))

    def _clean_heading_candidate(self, line: str) -> str:
        """Strips surrounding markup, punctuation, numbering, and Markdown artifacts."""
        cleaned = line.strip()
        # Remove markdown headers: ### Header
        cleaned = re.sub(r"^#+\s*", "", cleaned)
        # Remove list markers or numbering: "1. ", "I. ", "- ", "• "
        cleaned = re.sub(r"^(?:[0-9]+|[a-zA-Z]|[ivxIVX]+)[\.\)\-\:\s]+\s*", "", cleaned)
        # Remove bounding symbols: [Skills], (Education), --- Experience ---, **Projects**
        cleaned = re.sub(r"^[\*\_\-\=\~\|\:\#\s\[\]\(\)\{\}\<\>]+|[\*\_\-\=\~\|\:\#\s\[\]\(\)\{\}\<\>]+$", "", cleaned)
        return cleaned.strip()

    def _match_heading(self, line: str) -> Optional[str]:
        """
        Determines whether a line qualifies as a section heading.
        Returns the canonical section name or None.
        """
        stripped = line.strip()
        if not stripped:
            return None

        # Headings are short phrases, typically <= 6 words and <= 50 characters
        words = stripped.split()
        if len(words) > 7 or len(stripped) > 55:
            return None

        # Negative checks: bullets, sentences ending in full stop, or email/url lines are not headings
        if stripped.startswith("•") or stripped.startswith("- ") or stripped.startswith("* "):
            return None
        if "@" in stripped or "http://" in stripped or "https://" in stripped or "www." in stripped:
            return None
        if stripped.endswith(".") and len(words) > 3:
            return None

        # Clean punctuation and numbering artifacts
        candidate = self._clean_heading_candidate(stripped)
        if not candidate:
            return None

        # Exact / Regex pattern matching against canonical categories
        for canonical, regex in self._compiled_patterns:
            if regex.match(stripped) or regex.match(candidate):
                return canonical

        return None

    def detect_sections(self, text: str) -> SectionDetectionResult:
        """
        Segments normalized resume text into classified sections.
        """
        if not text or not text.strip():
            return SectionDetectionResult()

        lines = text.split("\n")
        # Identify heading lines: (line_index, canonical_section, raw_heading_line)
        headings: List[Tuple[int, str, str]] = []

        for idx, line in enumerate(lines):
            canonical = self._match_heading(line)
            if canonical:
                headings.append((idx, canonical, line.strip()))

        result = SectionDetectionResult()

        # If no section headings detected at all, store everything in unclassified
        if not headings:
            result.unclassified = text.strip()
            return result

        # Text before the first heading is either contact/header info or unclassified
        first_heading_idx = headings[0][0]
        header_text = "\n".join(lines[:first_heading_idx]).strip()

        if header_text:
            # Check if header contains contact signals (email, phone, urls) or candidate name
            has_contact_signal = (
                "@" in header_text
                or "linkedin" in header_text.lower()
                or "github" in header_text.lower()
                or any(char.isdigit() for char in header_text)
            )
            if has_contact_signal:
                result.contact = header_text
                result.detected_sections_list.append("contact")
                result.raw_headings["contact"] = "Header / Contact Info"
            else:
                result.unclassified = header_text

        # Extract content between subsequent headings
        section_accumulator: Dict[str, List[str]] = {s: [] for s in CANONICAL_SECTIONS}

        for i, (start_idx, canonical, raw_heading) in enumerate(headings):
            # Content starts on the line following the heading
            content_start = start_idx + 1
            # Content ends on the line before the next heading (or end of document)
            content_end = headings[i + 1][0] if i + 1 < len(headings) else len(lines)
            
            section_content = "\n".join(lines[content_start:content_end]).strip()

            if section_content:
                section_accumulator[canonical].append(section_content)

            if canonical not in result.detected_sections_list:
                result.detected_sections_list.append(canonical)
                result.raw_headings[canonical] = raw_heading

        # Populate SectionDetectionResult attributes
        for canonical, contents in section_accumulator.items():
            if contents:
                combined_content = "\n\n".join(contents).strip()
                if hasattr(result, canonical):
                    # If contact already had header text, append explicit contact section if any
                    if canonical == "contact" and result.contact:
                        result.contact = f"{result.contact}\n\n{combined_content}".strip()
                    else:
                        setattr(result, canonical, combined_content)

        return result


# Singleton instance
section_detector = SectionDetector()


def detect_resume_sections(text: str) -> SectionDetectionResult:
    """
    Convenience function for resume section detection.
    """
    return section_detector.detect_sections(text)
