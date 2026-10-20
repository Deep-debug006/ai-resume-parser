"""
Deterministic resume text preprocessing and normalization service.
Cleans raw text extracted from PyMuPDF and OCR pipelines without removing
critical information (emails, URLs, dates, numbers, phone numbers, or casing).
"""
import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class CleanedTextResult:
    """
    Metadata container for cleaned text and transformation metrics.
    """
    cleaned_text: str
    original_char_count: int
    cleaned_char_count: int
    line_count: int
    word_count: int
    reduction_pct: float
    transformations_applied: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cleaned_text": self.cleaned_text,
            "original_char_count": self.original_char_count,
            "cleaned_char_count": self.cleaned_char_count,
            "line_count": self.line_count,
            "word_count": self.word_count,
            "reduction_pct": self.reduction_pct,
            "transformations_applied": self.transformations_applied,
        }


class TextCleaner:
    """
    Deterministic rule-based preprocessing pipeline for resume text.
    Executes in a controlled order of operations:
    1. Line-ending & control character normalization
    2. Unicode normalization (NFKC) & typographic ligature resolution
    3. Removal of PDF/OCR extraction artifacts
    4. Dehyphenation of line-broken words
    5. Bullet point & list marker standardization
    6. Horizontal whitespace normalization
    7. Punctuation spacing correction (preserving URLs, emails, numbers)
    8. Paragraph & vertical whitespace compaction
    """

    # Common unicode bullets to normalize into standard bullet '• '
    BULLET_CHARS_PATTERN = re.compile(
        r'[\u2022\u2023\u25cf\u25cb\u25a0\u25a1\u25aa\u25ab\u25b6\u25b8\u25ba\u25c6\u25c7\u25e6\u2043\u2219\u27a4\u2713\u2714\uf0b7]'
    )

    # Standalone page number artifacts like "Page 1 of 2", "Page 2/3", "- 2 -", "1 | Page"
    PAGE_ARTIFACT_PATTERN = re.compile(
        r'(?im)^[ \t]*(?:page\s+\d+(?:\s*(?:of|/)\s*\d+)?|\d+\s*(?:of|/)\s*\d+\s*pages?|[-–—]\s*\d+\s*[-–—]|\d+\s*\|\s*page)[ \t]*$',
    )

    # De-hyphenation across line breaks: e.g. "experi-\nence" -> "experience"
    # Matches words with at least 2 chars on each side, lowercased continuation
    DEHYPHENATION_PATTERN = re.compile(
        r'([a-zA-Z]{2,})-\n[ \t]*([a-z]{2,})'
    )

    def clean(self, raw_text: str) -> CleanedTextResult:
        """
        Executes full deterministic cleaning pipeline on raw resume text.
        """
        if not raw_text:
            return CleanedTextResult(
                cleaned_text="",
                original_char_count=0,
                cleaned_char_count=0,
                line_count=0,
                word_count=0,
                reduction_pct=0.0,
                transformations_applied=[],
            )

        original_char_count = len(raw_text)
        transformations: List[str] = []
        text = raw_text

        # 1. Normalize line endings & strip null/control bytes
        # Preserves \n, strips \x00, normalizes \r\n and \r
        text_before = text
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Form feed (\x0c) common in PDF page breaks -> double newline
        text = text.replace('\x0c', '\n\n')
        # Remove null bytes and non-printable control characters except \n and \t
        text = re.sub(r'[\x00-\x08\x0b\x0e-\x1f\x7f]', '', text)
        if text != text_before:
            transformations.append("normalized_line_endings_and_control_chars")

        # 2. Unicode normalization (NFKC)
        # Converts ligatures like 'fi' (\ufb01) -> 'fi', full-width ASCII -> standard ASCII
        text_before = text
        text = unicodedata.normalize('NFKC', text)
        # Replace non-breaking spaces (\u00a0) and zero-width spaces (\u200b)
        text = text.replace('\u00a0', ' ').replace('\u200b', '').replace('\ufeff', '')
        if text != text_before:
            transformations.append("unicode_nfkc_normalization")

        # 3. Strip standalone page headers / footers / page number artifacts
        text_before = text
        text = self.PAGE_ARTIFACT_PATTERN.sub('', text)
        if text != text_before:
            transformations.append("removed_page_number_artifacts")

        # 4. De-hyphenate words broken across line breaks
        text_before = text
        text = self.DEHYPHENATION_PATTERN.sub(r'\1\2', text)
        if text != text_before:
            transformations.append("dehyphenated_linebreaks")

        # 5. Standardize bullet characters and resolve duplicate bullets
        text_before = text
        # Replace varied bullet symbols with standard bullet '•'
        text = self.BULLET_CHARS_PATTERN.sub('•', text)
        # Collapse multiple repeated bullet characters (e.g., "• • •", "••") to single "•"
        text = re.sub(r'(?:[ \t]*•){2,}', ' •', text)
        # Ensure standard space after bullet when followed by alphanumeric
        text = re.sub(r'(?m)^[ \t]*•[ \t]*', '• ', text)
        # Also clean inline bullet spaces
        text = re.sub(r'[ \t]+•[ \t]*', ' • ', text)
        if text != text_before:
            transformations.append("standardized_bullets")

        # 6. Normalize horizontal whitespace within lines
        text_before = text
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                cleaned_lines.append("")
                continue
            collapsed = re.sub(r'[ \t]{2,}', ' ', stripped)
            if collapsed.startswith('•'):
                rest = collapsed[1:].lstrip()
                cleaned_lines.append(f"• {rest}")
            else:
                cleaned_lines.append(collapsed)
        text = '\n'.join(cleaned_lines)
        if text != text_before:
            transformations.append("collapsed_inline_whitespace")

        # 7. Normalize unnecessary spaces around punctuation while preserving emails, numbers, and URLs
        text_before = text
        # Remove space before comma or semicolon: "Python , FastAPI" -> "Python, FastAPI"
        text = re.sub(r'[ \t]+([,;])', r'\1', text)
        # Ensure single space after comma or semicolon if immediately followed by letters/words (avoiding decimals/URLs)
        text = re.sub(r'([,;])([a-zA-Z])', r'\1 \2', text)
        # Fix spaced colons in headers (e.g., "Skills : Python" -> "Skills: Python")
        text = re.sub(r'([a-zA-Z0-9])[ \t]+:([ \t]*)', r'\1:\2', text)
        # Fix spaces inside parentheses: "( Python )" -> "(Python)"
        text = re.sub(r'\([ \t]+', '(', text)
        text = re.sub(r'[ \t]+\)', ')', text)
        if text != text_before:
            transformations.append("cleaned_punctuation_spacing")

        # 8. Collapse repeated blank lines
        text_before = text
        # Collapse 3 or more newlines into 2 (one blank line between paragraphs)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Trim leading/trailing whitespace of the entire document
        text = text.strip()
        if text != text_before:
            transformations.append("compacted_blank_lines")

        cleaned_char_count = len(text)
        reduction_chars = original_char_count - cleaned_char_count
        reduction_pct = round((reduction_chars / original_char_count * 100), 2) if original_char_count > 0 else 0.0

        line_count = len([l for l in text.split('\n') if l.strip()])
        word_count = len(text.split())

        return CleanedTextResult(
            cleaned_text=text,
            original_char_count=original_char_count,
            cleaned_char_count=cleaned_char_count,
            line_count=line_count,
            word_count=word_count,
            reduction_pct=reduction_pct,
            transformations_applied=transformations,
        )


# Singleton instance
text_cleaner = TextCleaner()


def clean_resume_text(text: str) -> CleanedTextResult:
    """
    Convenience function for deterministic resume text cleaning.
    """
    return text_cleaner.clean(raw_text=text)
