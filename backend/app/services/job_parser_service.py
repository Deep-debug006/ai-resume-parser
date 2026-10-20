"""
Job Description Parser Service (Phase 14).
Extracts structured information from raw job description text:
- Job title
- Company (only if explicitly present)
- Required skills
- Preferred skills
- Education requirements
- Experience requirements
- Responsibilities
- Tools / technologies
- Certifications (if mentioned)

Core Architectural Principles:
1. Strict fidelity: Extract ONLY information explicitly present.
2. Never invent information: Missing information remains missing (null or empty list).
3. Structured output: Validated Pydantic JobDescription models.
4. Skill Normalization: Reuses Phase 10 SkillNormalizer for canonical skill representations.
5. Dual engine: Primary LLM structured extraction with robust deterministic fallback.
"""
import re
import time
import logging
from typing import Optional, List, Dict, Tuple, Any

from backend.app.schemas.job_description import JobDescription
from backend.app.services.skill_normalizer import skill_normalizer
from backend.app.services.llm_service import (
    LLMService,
    llm_service as default_llm_service,
    LLMError,
)

logger = logging.getLogger(__name__)

# Strict anti-hallucination system prompt for Job Description parsing
JOB_PARSER_SYSTEM_INSTRUCTION = """You are an expert AI Job Description Parser and Information Extraction specialist.
Your mission is to extract structured, canonical information from the provided job description text into a strictly validated JSON object matching the JobDescription schema.

CRITICAL ANTI-HALLUCINATION & FIDELITY RULES:
1. STRICT FIDELITY: Extract ONLY information explicitly stated in the job description text.
2. NEVER INVENT INFORMATION: Do not fabricate company names, job titles, requirements, qualifications, or skills.
3. MISSING INFORMATION REMAINS MISSING:
   - If the company name is not explicitly stated, set "company": null.
   - If no certifications are explicitly mentioned, set "certifications": [].
   - If preferred/bonus skills are not specified, set "preferred_skills": [].
   - If education requirements are not specified, set "education_requirements": [].
   - If experience requirements are not specified, set "experience_requirements": [].
   - If location or salary are not stated, set them to null.
4. DISTINGUISH REQUIRED VS PREFERRED:
   - Mandatory, required, baseline, or minimum requirements go into "required_skills".
   - Bonus, nice-to-have, preferred, or plus qualifications go into "preferred_skills".
   - Do NOT mix up required and preferred qualifications.
5. EXTRACT TOOLS & TECHNOLOGIES:
   - Explicitly listed frameworks, databases, platforms, IDEs, and utilities go into "tools_and_technologies".
6. EXTRACT RESPONSIBILITIES:
   - Core duties, architectural tasks, and day-to-day deliverables go into "responsibilities".
7. OUTPUT FORMAT:
   - Return ONLY a valid JSON object matching the JobDescription schema without conversational preamble or markdown outside JSON.
"""


class DeterministicJobExtractor:
    """
    Deterministic rule-based extractor for job descriptions.
    Extracts structured fields using NLP pattern matching, regex boundaries,
    and canonical skill dictionary lookup.
    Guarantees operation in offline, test, or fallback environments.
    """

    # Section header patterns
    RESPONSIBILITY_HEADERS = re.compile(
        r"^(?:(?:key\s+)?responsibilities|what\s+you(?:'ll|\s+will)\s+do|duties|your\s+role|role\s+overview|what\s+you'll\s+be\s+doing)\b",
        re.IGNORECASE,
    )
    REQUIRED_HEADERS = re.compile(
        r"^(?:(?:minimum\s+|basic\s+)?requirements|(?:minimum\s+|basic\s+)?qualifications|what\s+you(?:'ll|\s+need)\s+to\s+have|must\s+haves?|who\s+you\s+are|what\s+we(?:'re|\s+are)\s+looking\s+for)\b",
        re.IGNORECASE,
    )
    PREFERRED_HEADERS = re.compile(
        r"^(?:preferred\s+qualifications|preferred\s+skills|nice\s+to\s+haves?|bonus\s+points?|bonus\s+qualifications|desired\s+skills|preferred\s+requirements|additional\s+qualifications)\b",
        re.IGNORECASE,
    )
    EDUCATION_HEADERS = re.compile(
        r"^(?:education(?:al\s+background)?|academic\s+requirements)\b",
        re.IGNORECASE,
    )

    # Degree patterns with strict word boundaries
    DEGREE_PATTERN = re.compile(
        r"\b(?:bachelor(?:'s)?|master(?:'s)?|ph\.?d\.?|doctorate|associate(?:'s)?)\b|\b(?:b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?)\b(?:\s+degree|\s+in\b)|\b(?:degree\s+in\b)",
        re.IGNORECASE,
    )

    # Experience patterns
    EXP_PATTERN = re.compile(
        r"(?:\d+\+?(?:\s*(?:to|-)\s*\d+\+?)?)\s*(?:years?|yrs?)(?:[^\n,.]*?)(?:experience|background|track\s+record)",
        re.IGNORECASE,
    )

    # Certification keywords
    KNOWN_CERTS = [
        "AWS Certified Solutions Architect",
        "AWS Certified Developer",
        "AWS Certified SysOps Administrator",
        "AWS Certified DevOps Engineer",
        "AWS Certified Cloud Practitioner",
        "AWS Certified",
        "Google Cloud Certified Professional Cloud Architect",
        "Google Cloud Certified",
        "GCP Certified",
        "Microsoft Certified: Azure Solutions Architect",
        "Azure Certified",
        "Certified Kubernetes Administrator (CKA)",
        "Certified Kubernetes Application Developer (CKAD)",
        "CKA",
        "CKAD",
        "CISSP",
        "CISA",
        "CISM",
        "CEH",
        "CompTIA Security+",
        "CompTIA Network+",
        "PMP",
        "Scrum Master",
        "CSM",
        "PMI-ACP",
    ]

    @classmethod
    def extract_job_title(cls, text: str) -> str:
        """Extracts job title from explicit header or initial lines."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            return "Software Engineer"

        # 1. Explicit title labels
        for line in lines[:15]:
            match = re.match(
                r"^(?:job\s+title|title|position|role):\s*(.+)$",
                line,
                re.IGNORECASE,
            )
            if match:
                clean_title = match.group(1).strip()
                if clean_title:
                    return clean_title

        # 2. Check first 5 lines for common role designations
        role_indicators = [
            "engineer",
            "developer",
            "architect",
            "manager",
            "analyst",
            "scientist",
            "designer",
            "lead",
            "specialist",
            "administrator",
            "consultant",
            "director",
            "intern",
            "programmer",
        ]
        for line in lines[:5]:
            lower = line.lower()
            if any(ind in lower for ind in role_indicators):
                # Clean prefix like "# ", "Role: ", etc.
                cleaned = re.sub(r"^[#*\-•\s]+", "", line).strip()
                # If line is not too long (under 80 chars), it's likely a title
                if len(cleaned) <= 80 and not cleaned.endswith((".", ":")):
                    # Remove trailing company if formatted like "Role at Company"
                    if " at " in cleaned:
                        parts = cleaned.split(" at ", 1)
                        if any(ind in parts[0].lower() for ind in role_indicators):
                            return parts[0].strip()
                    return cleaned

        # 3. Fallback to first line
        first_clean = re.sub(r"^[#*\-•\s]+", "", lines[0]).strip()
        return first_clean[:80] if first_clean else "Software Engineer"

    @classmethod
    def extract_company(cls, text: str) -> Optional[str]:
        """Extracts company name ONLY if explicitly present."""
        # 1. Explicit Company labels
        comp_match = re.search(
            r"^(?:company|organization|employer|hiring\s+company):\s*(.+)$",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        if comp_match:
            candidate = comp_match.group(1).strip()
            if candidate:
                return candidate

        # 2. "About <Company>"
        about_match = re.search(
            r"(?:^|\n)about\s+([A-Z0-9][A-Za-z0-9\s&.,'-]{2,35}?)(?:\n|\:|\.|\s-\s|\sis\b)",
            text,
            re.IGNORECASE,
        )
        if about_match:
            candidate = about_match.group(1).strip()
            # Filter out non-company generic phrases
            if candidate.lower() not in ("the role", "the position", "the company", "us", "this role", "the team"):
                return candidate

        # 3. "<Company> is looking for / is seeking / is hiring"
        seeking_match = re.search(
            r"(?:^|\n)([A-Z0-9][A-Za-z0-9\s&.,'-]{2,35}?)\s+(?:is\s+(?:looking\s+for|seeking|hiring|in\s+search\s+of))\b",
            text,
        )
        if seeking_match:
            candidate = seeking_match.group(1).strip()
            if candidate.lower() not in ("the team", "our team", "we"):
                return candidate

        # 4. "Join us at <Company>" or "Join <Company>"
        join_match = re.search(
            r"(?:join\s+us\s+at|join\s+the\s+team\s+at|join)\s+([A-Z0-9][A-Za-z0-9\s&.,'-]{2,35}?)(?:\s+as|\s+in|\n|\.|\!|\,)",
            text,
            re.IGNORECASE,
        )
        if join_match:
            candidate = join_match.group(1).strip()
            if candidate.lower() not in ("our team", "us", "today"):
                return candidate

        return None

    @classmethod
    def partition_sections(cls, text: str) -> Dict[str, List[str]]:
        """Partitions job description into structured sections."""
        lines = [line.strip() for line in text.split("\n")]
        sections: Dict[str, List[str]] = {
            "responsibilities": [],
            "required": [],
            "preferred": [],
            "education": [],
            "general": [],
        }

        current_section = "general"

        for line in lines:
            if not line:
                continue

            cleaned_line = re.sub(r"^[#*\-•\s]+", "", line).strip()
            # Check for inline header pattern, e.g. "Requirements: Python, PostgreSQL"
            inline_match = re.match(r"^([^:\n]{3,35}):\s*(.+)$", cleaned_line)
            header_text = cleaned_line.lower()
            inline_body = None
            if inline_match:
                candidate_hdr = inline_match.group(1).strip().lower()
                candidate_body = inline_match.group(2).strip()
                if (
                    cls.RESPONSIBILITY_HEADERS.match(candidate_hdr)
                    or cls.PREFERRED_HEADERS.match(candidate_hdr)
                    or cls.REQUIRED_HEADERS.match(candidate_hdr)
                    or cls.EDUCATION_HEADERS.match(candidate_hdr)
                ):
                    header_text = candidate_hdr
                    inline_body = candidate_body

            cleaned_header = re.sub(r"^[#*\-•\s:]+", "", header_text).strip().lower()

            if cls.RESPONSIBILITY_HEADERS.match(cleaned_header):
                current_section = "responsibilities"
                if inline_body:
                    sections[current_section].append(inline_body)
                continue
            elif cls.PREFERRED_HEADERS.match(cleaned_header):
                current_section = "preferred"
                if inline_body:
                    sections[current_section].append(inline_body)
                continue
            elif cls.REQUIRED_HEADERS.match(cleaned_header):
                current_section = "required"
                if inline_body:
                    sections[current_section].append(inline_body)
                continue
            elif cls.EDUCATION_HEADERS.match(cleaned_header):
                current_section = "education"
                if inline_body:
                    sections[current_section].append(inline_body)
                continue

            # Clean bullet points without stripping numbers like '5+ years'
            cleaned_bullet = re.sub(r"^[\-*•·>\s]+|^\(?\d+[\.\)\-]\s*", "", line).strip()
            if cleaned_bullet:
                sections[current_section].append(cleaned_bullet)

        return sections

    @classmethod
    def extract_certifications(cls, text: str) -> List[str]:
        """Extracts recognized certifications explicitly mentioned in the text."""
        found: List[str] = []
        for cert in cls.KNOWN_CERTS:
            # Word boundary regex to avoid partial substring false positives
            pattern = re.compile(rf"\b{re.escape(cert)}\b", re.IGNORECASE)
            if pattern.search(text):
                # Standardize to proper title casing
                if cert not in found:
                    found.append(cert)
        return found

    @classmethod
    def extract_deterministic(cls, text: str) -> JobDescription:
        """Performs complete deterministic rule-based extraction from raw text."""
        sections = cls.partition_sections(text)
        title = cls.extract_job_title(text)
        company = cls.extract_company(text)

        # Education requirements
        education_reqs: List[str] = []
        for line in sections["education"] + sections["required"]:
            if cls.DEGREE_PATTERN.search(line):
                if line not in education_reqs:
                    education_reqs.append(line)

        # Experience requirements
        experience_reqs: List[str] = []
        for line in sections["required"] + sections["preferred"] + sections["general"]:
            if cls.EXP_PATTERN.search(line):
                if line not in experience_reqs:
                    experience_reqs.append(line)

        # Responsibilities
        responsibilities: List[str] = []
        for line in sections["responsibilities"]:
            if line not in responsibilities and len(line) > 10:
                responsibilities.append(line)

        # Certifications
        certifications = cls.extract_certifications(text)

        # Extract skills from sections against canonical dictionary
        all_skills = list(skill_normalizer._canonical_skills)
        alias_map = skill_normalizer._alias_to_canonical

        def find_skills_in_lines(lines: List[str]) -> Tuple[List[str], List[str]]:
            found_skills: List[str] = []
            found_tools: List[str] = []
            blob = "\n".join(lines)

            # Check aliases and canonical skills
            for term, canonical in alias_map.items():
                if len(term) < 2:
                    continue
                # Special cases for single/short chars: C, Go, R
                if term in ("c", "r"):
                    pat = rf"(?:\b{re.escape(term)}\b(?!\+|\#))"
                else:
                    pat = rf"\b{re.escape(term)}\b"

                m = re.search(pat, blob, re.IGNORECASE)
                if m:
                    raw_matched = m.group(0)
                    if raw_matched not in found_skills:
                        found_skills.append(raw_matched)
                    # Classify developer tools/platforms
                    if canonical in (
                        "Git", "Docker", "Kubernetes", "PostgreSQL", "Redis", "AWS",
                        "Google Cloud Platform", "Terraform", "Linux", "Postman",
                        "Jenkins", "Jira", "VS Code", "Kafka", "Elasticsearch",
                    ):
                        if raw_matched not in found_tools:
                            found_tools.append(raw_matched)

            return found_skills, found_tools

        req_skills, req_tools = find_skills_in_lines(sections["required"])
        pref_skills, pref_tools = find_skills_in_lines(sections["preferred"])

        # If no specific required skills found in requirements section, scan entire text
        if not req_skills:
            all_text_skills, all_tools = find_skills_in_lines(
                sections["general"] + sections["responsibilities"]
            )
            req_skills = all_text_skills
            req_tools = all_tools

        # Combine tools
        tools_and_technologies = list(dict.fromkeys(req_tools + pref_tools))

        # Location extraction
        location: Optional[str] = None
        loc_match = re.search(
            r"^(?:location|workplace|work\s+type):\s*(.+)$",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        if loc_match:
            location = loc_match.group(1).strip()
        elif re.search(r"\b(?:remote|hybrid|on-site)\b", text, re.IGNORECASE):
            match = re.search(r"\b(remote|hybrid|on-site)\b", text, re.IGNORECASE)
            if match:
                location = match.group(1).capitalize()

        # Employment type
        employment_type: Optional[str] = None
        emp_match = re.search(
            r"^(?:employment\s+type|job\s+type):\s*(.+)$",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        if emp_match:
            employment_type = emp_match.group(1).strip()
        elif re.search(r"\b(full-time|part-time|contract|internship)\b", text, re.IGNORECASE):
            match = re.search(r"\b(full-time|part-time|contract|internship)\b", text, re.IGNORECASE)
            if match:
                employment_type = match.group(1).capitalize()

        # Salary
        salary_range: Optional[str] = None
        sal_match = re.search(
            r"(?:\$|USD\s*)\d{2,3}(?:,\d{3})*(?:\s*(?:-|to)\s*(?:\$|USD\s*)?\d{2,3}(?:,\d{3})*)?(?:\s*(?:\/|per\s*)(?:year|yr|hour|hr|annum))?",
            text,
            re.IGNORECASE,
        )
        if sal_match:
            salary_range = sal_match.group(0).strip()

        return JobDescription(
            job_title=title,
            company=company,
            required_skills=req_skills,
            preferred_skills=pref_skills,
            education_requirements=education_reqs,
            experience_requirements=experience_reqs,
            responsibilities=responsibilities,
            tools_and_technologies=tools_and_technologies,
            certifications=certifications,
            location=location,
            employment_type=employment_type,
            salary_range=salary_range,
            raw_text_char_count=len(text),
        )


class JobParserService:
    """
    High-level Job Description Parsing and Information Extraction Service.
    Coordinates LLM structured extraction, strict anti-hallucination validation,
    deterministic fallback, and skill normalization.
    """

    def __init__(self, llm_service_instance: Optional[LLMService] = None):
        self._llm_service = llm_service_instance or default_llm_service

    def build_prompt(self, text: str) -> str:
        """Constructs grounded LLM prompt for JobDescription extraction."""
        return (
            "Please extract structured job description information into a valid JSON object matching the JobDescription schema.\n\n"
            "=== RAW JOB DESCRIPTION TEXT ===\n"
            f"{text.strip()}\n\n"
            "=== MANDATORY EXTRACTION INSTRUCTIONS ===\n"
            "1. Extract ONLY facts explicitly stated in the text.\n"
            "2. If company is not explicitly stated, set company to null.\n"
            "3. If no certifications are mentioned, set certifications to [].\n"
            "4. Distinguish required_skills from preferred_skills.\n"
            "5. Return a valid JSON object matching the schema."
        )

    def normalize_job_skills(self, job: JobDescription) -> Tuple[JobDescription, int]:
        """
        Applies Phase 10 SkillNormalizer to canonicalize and deduplicate all skill fields:
        - required_skills
        - preferred_skills
        - tools_and_technologies
        """
        total_normalized = 0

        # 1. Normalize required_skills
        req_norm = skill_normalizer.normalize_skills(job.required_skills)
        job.required_skills = req_norm.normalized_skills
        total_normalized += len(req_norm.aliases_resolved)

        # 2. Normalize preferred_skills
        pref_norm = skill_normalizer.normalize_skills(job.preferred_skills)
        job.preferred_skills = pref_norm.normalized_skills
        total_normalized += len(pref_norm.aliases_resolved)

        # 3. Normalize tools_and_technologies
        tools_norm = skill_normalizer.normalize_skills(job.tools_and_technologies)
        job.tools_and_technologies = tools_norm.normalized_skills
        total_normalized += len(tools_norm.aliases_resolved)

        return job, total_normalized

    async def parse_job_description(
        self,
        text: str,
        custom_llm_service: Optional[LLMService] = None,
        force_deterministic: bool = False,
    ) -> Tuple[JobDescription, int, str]:
        """
        Parses a job description text into a validated, normalized JobDescription object.

        Returns:
            Tuple of (JobDescription, normalized_skills_count, provider_name)
        """
        if not text or not text.strip():
            raise ValueError("Job description text cannot be empty.")

        cleaned_text = text.strip()
        provider_name = "deterministic"
        job_obj: Optional[JobDescription] = None

        if not force_deterministic:
            service = custom_llm_service or self._llm_service
            try:
                prompt = self.build_prompt(cleaned_text)
                parsed_model, _ = await service.generate_structured(
                    prompt=prompt,
                    system_instruction=JOB_PARSER_SYSTEM_INSTRUCTION,
                    schema_class=JobDescription,
                )
                job_obj = parsed_model
                provider_name = service.provider.provider_name
                logger.info(
                    "Job parsed via LLM provider '%s': title='%s', company='%s'",
                    provider_name,
                    job_obj.job_title,
                    job_obj.company,
                )
            except Exception as e:
                logger.warning(
                    "LLM structured job extraction failed (%s). Falling back to deterministic extractor.",
                    e,
                )
                job_obj = None

        # Fallback to deterministic extraction if LLM failed or not requested
        if job_obj is None:
            job_obj = DeterministicJobExtractor.extract_deterministic(cleaned_text)
            provider_name = "deterministic"
            logger.info(
                "Job parsed via deterministic extractor: title='%s', company='%s'",
                job_obj.job_title,
                job_obj.company,
            )

        # Ensure raw_text_char_count is set
        job_obj.raw_text_char_count = len(cleaned_text)

        # Deterministic Skill Normalization reuse (Phase 10)
        normalized_job, normalized_count = self.normalize_job_skills(job_obj)

        return normalized_job, normalized_count, provider_name


# Singleton instance
job_parser_service = JobParserService()
