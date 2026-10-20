"""
Deterministic NLP preprocessing service using spaCy (Phase 8).
Extracts named entities (PERSON, ORG, GPE/LOC, DATE) and structural signals (EMAIL, URL)
to serve as supporting evidence for structured resume extraction.
Does not replace LLM parsing or overwrite user text.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)

# Fallback regexes for reliable email and url capture across text formats
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
URL_REGEX = re.compile(
    r"(?:https?://|www\.)[^\s/$.?#].[^\s]*|"
    r"(?:github\.com|linkedin\.com)/[^\s]+",
    re.IGNORECASE,
)

# Common words/headings that shouldn't be tagged as PERSON
COMMON_HEADINGS = {
    "experience",
    "work experience",
    "education",
    "skills",
    "technical skills",
    "projects",
    "certifications",
    "summary",
    "profile",
    "objective",
}


@dataclass
class NLPExtractionResult:
    """
    Structured outcome of deterministic NLP entity extraction.
    Serves as supporting evidence for downstream structured parsing.
    """
    persons: List[str] = field(default_factory=list)
    organizations: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    entities: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary."""
        return {
            "persons": self.persons,
            "organizations": self.organizations,
            "locations": self.locations,
            "dates": self.dates,
            "emails": self.emails,
            "urls": self.urls,
            "entities": self.entities,
        }


class NLPService:
    """
    Deterministic NLP entity extractor backed by spaCy 'en_core_web_sm'.
    """

    def __init__(self, model_name: str = "en_core_web_sm"):
        self.model_name = model_name
        self._nlp: Optional[Language] = None

    @property
    def nlp(self) -> Language:
        """Lazy-loads the spaCy English language pipeline."""
        if self._nlp is None:
            try:
                self._nlp = spacy.load(self.model_name)
                logger.info("Loaded spaCy model '%s' successfully.", self.model_name)
            except Exception as e:
                logger.error(
                    "Failed to load spaCy model '%s': %s. "
                    "Ensure the model is installed: python3 -m spacy download %s",
                    self.model_name,
                    str(e),
                    self.model_name,
                )
                raise RuntimeError(
                    f"spaCy model '{self.model_name}' could not be loaded: {str(e)}"
                ) from e
        return self._nlp

    def _clean_entity(self, text: str) -> str:
        """Strips surrounding whitespace, newlines, and list bullets."""
        cleaned = text.strip()
        cleaned = re.sub(r"^[\s\•\-\*\–\—\:\,\.\|\(\)]+|[\s\•\-\*\–\—\:\,\.\|\(\)]+$", "", cleaned)
        return cleaned.strip()

    def extract_entities(self, text: str) -> NLPExtractionResult:
        """
        Receives resume text, runs deterministic spaCy NER and token analysis line-by-line,
        and returns classified entities without modifying or overwriting the original text.
        """
        if not text or not text.strip():
            return NLPExtractionResult()

        persons: List[str] = []
        organizations: List[str] = []
        locations: List[str] = []
        dates: List[str] = []
        emails: List[str] = []
        urls: List[str] = []
        raw_entities: List[Dict[str, Any]] = []

        seen_entities = set()

        # Process lines individually to avoid multi-line entity bleeding across unpunctuated resume lines
        current_offset = 0
        lines = text.split("\n")

        for line in lines:
            line_len = len(line)
            stripped_line = line.strip()

            if stripped_line:
                # 1. First run on native line
                doc = self.nlp(stripped_line)
                line_offset_in_text = current_offset + line.find(stripped_line)

                ents_found = list(doc.ents)

                # 2. If line is entirely uppercase (e.g. "ALEXANDER HAMILTON") and no PERSON was found,
                # also test title-cased representation to overcome all-caps NER degradation
                if stripped_line.isupper() and not any(e.label_ == "PERSON" for e in ents_found):
                    title_doc = self.nlp(stripped_line.title())
                    for ent in title_doc.ents:
                        if ent.label_ == "PERSON":
                            # Map back to original line's slice
                            orig_span_text = stripped_line[ent.start_char:ent.end_char]
                            ents_found.append(spacy.tokens.Span(doc, ent.start, ent.end, label="PERSON"))

                for ent in ents_found:
                    cleaned_text = self._clean_entity(ent.text)
                    if not cleaned_text:
                        continue

                    # Skip common headings
                    if cleaned_text.lower() in COMMON_HEADINGS:
                        continue

                    entity_key = (cleaned_text.lower(), ent.label_)
                    if entity_key in seen_entities:
                        continue
                    seen_entities.add(entity_key)

                    abs_start = line_offset_in_text + ent.start_char
                    abs_end = line_offset_in_text + ent.end_char

                    raw_entities.append({
                        "text": cleaned_text,
                        "label": ent.label_,
                        "start_char": abs_start,
                        "end_char": abs_end,
                    })

                    if ent.label_ == "PERSON":
                        if len(cleaned_text) > 1 and not cleaned_text.isdigit() and "@" not in cleaned_text:
                            if cleaned_text not in persons:
                                persons.append(cleaned_text)

                    elif ent.label_ == "ORG":
                        # Note: spaCy classifies both companies and educational institutions (universities) as ORG.
                        # We preserve them as supporting evidence without assuming all ORGs are companies.
                        if len(cleaned_text) > 1 and "@" not in cleaned_text:
                            if cleaned_text not in organizations:
                                organizations.append(cleaned_text)

                    elif ent.label_ in ("GPE", "LOC"):
                        if len(cleaned_text) > 1 and not cleaned_text.isdigit():
                            if cleaned_text not in locations:
                                locations.append(cleaned_text)

                    elif ent.label_ == "DATE":
                        if len(cleaned_text) > 1:
                            if cleaned_text not in dates:
                                dates.append(cleaned_text)

                # Token checks for email & url on stripped line
                for token in doc:
                    if token.like_email:
                        cleaned_email = token.text.strip().lower()
                        if cleaned_email and cleaned_email not in emails:
                            emails.append(cleaned_email)
                    if token.like_url:
                        cleaned_url = token.text.strip()
                        if cleaned_url and cleaned_url not in urls:
                            urls.append(cleaned_url)

            # Move offset to next line (+1 for the newline character)
            current_offset += line_len + 1

        # Global regex passes to guarantee full capture of embedded links and addresses
        for match in EMAIL_REGEX.finditer(text):
            found_email = match.group(0).strip().lower()
            if found_email and found_email not in emails:
                emails.append(found_email)

        for match in URL_REGEX.finditer(text):
            found_url = match.group(0).strip()
            found_url = re.sub(r"[\,\.\;\:\)]+$", "", found_url)
            if found_url and found_url not in urls:
                urls.append(found_url)

        return NLPExtractionResult(
            persons=persons,
            organizations=organizations,
            locations=locations,
            dates=dates,
            emails=emails,
            urls=urls,
            entities=raw_entities,
        )


# Singleton service instance
nlp_service = NLPService()


def extract_resume_nlp_entities(text: str) -> NLPExtractionResult:
    """
    Convenience functional interface for spaCy NLP entity extraction.
    """
    return nlp_service.extract_entities(text)
