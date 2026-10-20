"""
Deterministic Resume-Job Matching Service (Phase 15).
Compares a structured Resume against a structured JobDescription.

Core Architectural Principles:
1. Deterministic & Explainable: Every match and gap is backed by explicit evidence.
2. Skill Normalization: Leverages canonical skill aliases (Phase 10) for robust matching.
3. Informational Comparison Only:
   - Does NOT make hiring decisions.
   - Does NOT predict candidate selection or candidate success.
   - Strictly reports alignment and discrepancies across skills, experience, and education.
4. Missing Information Fidelity:
   - Evaluates only stated criteria without hallucinations or ungrounded assumptions.
"""
import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Set, Tuple, Any

from backend.app.schemas.parsed_resume import Resume, Education, Experience
from backend.app.schemas.job_description import JobDescription
from backend.app.schemas.job_matcher import JobMatchResult, INFORMATIONAL_DISCLAIMER
from backend.app.services.skill_normalizer import skill_normalizer

logger = logging.getLogger(__name__)


# Degree hierarchy rank for deterministic comparisons
DEGREE_RANKS = {
    "doctorate": 4,
    "phd": 4,
    "ph.d": 4,
    "ph.d.": 4,
    "master": 3,
    "masters": 3,
    "master's": 3,
    "m.s.": 3,
    "ms": 3,
    "m.a.": 3,
    "ma": 3,
    "bachelor": 2,
    "bachelors": 2,
    "bachelor's": 2,
    "b.s.": 2,
    "bs": 2,
    "b.a.": 2,
    "ba": 2,
    "associate": 1,
    "associates": 1,
    "associate's": 1,
    "a.s.": 1,
    "a.a.": 1,
}


class JobMatcher:
    """
    Orchestrates deterministic matching between a parsed Resume and a parsed JobDescription.
    """

    def __init__(self):
        self.normalizer = skill_normalizer

    def collect_candidate_skills(self, resume: Resume) -> Tuple[List[str], Set[str]]:
        """
        Extracts all skills from resume skill categories, work history, projects, and credentials.
        Returns:
            Tuple of (list_of_canonical_skills, set_of_lowercased_canonical_skills)
        """
        raw_skills: List[str] = []

        # 1. From categorized SkillSet
        if resume.skills:
            raw_skills.extend(resume.skills.technical_skills)
            raw_skills.extend(resume.skills.programming_languages)
            raw_skills.extend(resume.skills.frameworks_and_libraries)
            raw_skills.extend(resume.skills.databases)
            raw_skills.extend(resume.skills.cloud_and_devops)
            raw_skills.extend(resume.skills.tools)
            raw_skills.extend(resume.skills.soft_skills)

        # 2. From experience technologies
        for exp in resume.experience:
            if exp.technologies:
                raw_skills.extend(exp.technologies)

        # 3. From project technologies
        for proj in resume.projects:
            if proj.technologies:
                raw_skills.extend(proj.technologies)

        # Normalize all collected candidate skills
        norm_result = self.normalizer.normalize_skills(raw_skills)
        canonical_list = norm_result.normalized_skills
        lowercased_set = {s.lower() for s in canonical_list}

        return canonical_list, lowercased_set

    def match_skill_collection(
        self,
        job_skills: List[str],
        candidate_skills_lower: Set[str],
    ) -> Tuple[List[str], List[str]]:
        """
        Compares a list of job skills against candidate skills.
        Returns:
            Tuple of (matched_skills, missing_skills)
        """
        matched: List[str] = []
        missing: List[str] = []

        # First normalize the job skills to canonical form
        norm_job = self.normalizer.normalize_skills(job_skills)

        for canonical_skill in norm_job.normalized_skills:
            if not canonical_skill:
                continue

            target_lower = canonical_skill.lower()
            is_matched = False

            # Direct match
            if target_lower in candidate_skills_lower:
                is_matched = True
            else:
                # Check known aliases
                if target_lower in self.normalizer._alias_to_canonical:
                    mapped = self.normalizer._alias_to_canonical[target_lower].lower()
                    if mapped in candidate_skills_lower:
                        is_matched = True

            if is_matched:
                if canonical_skill not in matched:
                    matched.append(canonical_skill)
            else:
                if canonical_skill not in missing:
                    missing.append(canonical_skill)

        return matched, missing

    def estimate_candidate_years_experience(self, resume: Resume) -> float:
        """
        Estimates candidate total professional experience in years
        by parsing date ranges from resume.experience entries.
        """
        total_months = 0.0
        current_year = 2026  # Baseline from environment runtime

        year_pattern = re.compile(r"\b(19\d\d|20\d\d)\b")
        month_names = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }

        def parse_date_point(d_str: Optional[str], default_is_present: bool = False) -> Optional[Tuple[int, int]]:
            if not d_str or not d_str.strip():
                return (current_year, 1) if default_is_present else None

            s = d_str.strip().lower()
            if "present" in s or "current" in s or "now" in s:
                return (current_year, 1)

            years = year_pattern.findall(s)
            if not years:
                return None
            y = int(years[-1])

            # Month detection
            m = 6  # Mid-year default
            for m_name, m_val in month_names.items():
                if m_name in s:
                    m = m_val
                    break

            return (y, m)

        parsed_ranges: List[Tuple[float, float]] = []

        for exp in resume.experience:
            start_pt = parse_date_point(exp.start_date, default_is_present=False)
            end_pt = parse_date_point(exp.end_date, default_is_present=exp.is_current)

            if start_pt and end_pt:
                start_decimal = start_pt[0] + (start_pt[1] - 1) / 12.0
                end_decimal = end_pt[0] + (end_pt[1] - 1) / 12.0
                if end_decimal >= start_decimal:
                    parsed_ranges.append((start_decimal, end_decimal))
            elif start_pt and not end_pt:
                # If current position
                end_decimal = current_year if exp.is_current else start_pt[0] + 1.0
                start_decimal = start_pt[0] + (start_pt[1] - 1) / 12.0
                parsed_ranges.append((start_decimal, end_decimal))

        if not parsed_ranges:
            # If dates couldn't be parsed, estimate based on roles count (approx 1.5 yrs per role)
            return round(len(resume.experience) * 1.5, 1)

        # Merge overlapping ranges to prevent double-counting parallel roles
        parsed_ranges.sort(key=lambda x: x[0])
        merged: List[Tuple[float, float]] = []

        for r in parsed_ranges:
            if not merged:
                merged.append(r)
            else:
                last_start, last_end = merged[-1]
                if r[0] <= last_end:
                    merged[-1] = (last_start, max(last_end, r[1]))
                else:
                    merged.append(r)

        total_years = sum(end - start for start, end in merged)
        return round(max(total_years, 0.5), 1)

    def extract_required_years_experience(self, job: JobDescription) -> Optional[float]:
        """
        Extracts minimum years of experience required from the job description.
        """
        all_req_text = " ".join(job.experience_requirements + job.required_skills)
        match = re.search(
            r"(\d+(?:\.\d+)?)\s*\+?\s*(?:to|-)?\s*(?:\d+)?\s*(?:years?|yrs?)",
            all_req_text,
            re.IGNORECASE,
        )
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def analyze_experience(
        self,
        resume: Resume,
        job: JobDescription,
    ) -> Tuple[str, str, float, Optional[float]]:
        """
        Produces explainable experience alignment and narrative analysis.
        Returns:
            Tuple of (experience_analysis_narrative, experience_alignment, candidate_years, required_years)
        """
        candidate_years = self.estimate_candidate_years_experience(resume)
        required_years = self.extract_required_years_experience(job)

        roles_count = len(resume.experience)
        role_summaries = []
        for exp in resume.experience[:3]:
            role_summaries.append(f"{exp.title} at {exp.company}")

        roles_clause = f" across {roles_count} role(s)" if roles_count > 0 else " with no formal work history listed"
        if role_summaries:
            roles_clause += f" (including {', '.join(role_summaries)})"

        if required_years is not None:
            if candidate_years >= required_years + 2.0:
                alignment = "exceeds_requirements"
                analysis = (
                    f"Candidate presents approximately {candidate_years:.1f} years of professional experience{roles_clause}, "
                    f"comfortably exceeding the stated minimum requirement of {required_years:.1f}+ years."
                )
            elif candidate_years >= required_years:
                alignment = "meets_requirements"
                analysis = (
                    f"Candidate presents approximately {candidate_years:.1f} years of professional experience{roles_clause}, "
                    f"meeting the stated requirement of {required_years:.1f}+ years."
                )
            else:
                alignment = "below_requirements"
                diff = round(required_years - candidate_years, 1)
                analysis = (
                    f"Candidate presents approximately {candidate_years:.1f} years of professional experience{roles_clause}. "
                    f"The job explicitly specifies {required_years:.1f}+ years of experience ({diff} year(s) variance)."
                )
        else:
            if job.experience_requirements:
                alignment = "meets_requirements" if candidate_years >= 2.0 else "partially_meets"
                analysis = (
                    f"The job description specifies qualitative experience criteria: "
                    f"'{'; '.join(job.experience_requirements[:2])}'. "
                    f"Candidate brings approximately {candidate_years:.1f} years of professional experience{roles_clause}."
                )
            else:
                alignment = "not_specified"
                analysis = (
                    f"The job description does not explicitly specify a minimum years of experience requirement. "
                    f"Candidate presents approximately {candidate_years:.1f} years of professional history{roles_clause}."
                )

        return analysis, alignment, candidate_years, required_years

    def analyze_education(
        self,
        resume: Resume,
        job: JobDescription,
    ) -> Tuple[str, str]:
        """
        Produces explainable education alignment and narrative analysis.
        Returns:
            Tuple of (education_analysis_narrative, education_alignment)
        """
        candidate_degrees = resume.education
        job_edu_reqs = job.education_requirements

        if not job_edu_reqs:
            if candidate_degrees:
                degs = [f"{e.degree or 'Degree'} in {e.field_of_study or 'General Studies'} from {e.institution}" for e in candidate_degrees]
                analysis = (
                    f"The job description does not explicitly mandate a specific degree requirement. "
                    f"Candidate holds: {'; '.join(degs)}."
                )
                return analysis, "not_specified"
            else:
                analysis = "Neither the job description nor candidate profile specifies formal educational degree criteria."
                return analysis, "not_specified"

        job_req_blob = " ".join(job_edu_reqs).lower()

        # Determine highest degree requested by job
        highest_job_rank = 0
        req_degree_name = "College Degree"
        for kw, rank in DEGREE_RANKS.items():
            if re.search(rf"\b{re.escape(kw)}\b", job_req_blob):
                if rank > highest_job_rank:
                    highest_job_rank = rank
                    req_degree_name = kw.capitalize()

        # Determine candidate's highest degree
        highest_cand_rank = 0
        best_edu: Optional[Education] = None
        for edu in candidate_degrees:
            deg_blob = f"{edu.degree or ''} {edu.field_of_study or ''}".lower()
            for kw, rank in DEGREE_RANKS.items():
                if re.search(rf"\b{re.escape(kw)}\b", deg_blob):
                    if rank > highest_cand_rank:
                        highest_cand_rank = rank
                        best_edu = edu

        if not best_edu and candidate_degrees:
            best_edu = candidate_degrees[0]
            highest_cand_rank = 2  # assume Bachelor if unspecified

        if not candidate_degrees:
            alignment = "below_requirements"
            analysis = (
                f"The job description specifies educational requirements: '{'; '.join(job_edu_reqs)}'. "
                f"No formal education credentials were found on the candidate's resume."
            )
            return analysis, alignment

        cand_degree_desc = f"{best_edu.degree or 'Degree'} in {best_edu.field_of_study or 'related field'} from {best_edu.institution}"

        # Field of study match check (CS, Engineering, etc.)
        stem_keywords = ["computer", "software", "engineering", "information", "data", "math", "science", "statistics"]
        job_wants_stem = any(kw in job_req_blob for kw in stem_keywords)
        cand_is_stem = any(kw in (best_edu.field_of_study or "").lower() for kw in stem_keywords)

        if highest_cand_rank > highest_job_rank and highest_job_rank > 0:
            alignment = "exceeds_requirements"
            analysis = (
                f"Candidate holds an advanced degree ({cand_degree_desc}), exceeding the stated requirement "
                f"for a {req_degree_name} degree."
            )
        elif highest_cand_rank == highest_job_rank or highest_job_rank == 0:
            alignment = "meets_requirements"
            field_note = " in an aligned field" if (job_wants_stem and cand_is_stem) else ""
            analysis = (
                f"Candidate holds a {cand_degree_desc}{field_note}, fulfilling the stated educational criteria: "
                f"'{'; '.join(job_edu_reqs)}'."
            )
        else:
            alignment = "below_requirements"
            analysis = (
                f"Candidate lists a {cand_degree_desc}. The job description specifies a requirement for a "
                f"{req_degree_name} or equivalent degree."
            )

        return analysis, alignment

    def match_certifications(
        self,
        resume: Resume,
        job: JobDescription,
    ) -> Tuple[List[str], List[str]]:
        """
        Compares job certifications with candidate certifications.
        """
        if not job.certifications:
            return [], []

        matched_certs: List[str] = []
        missing_certs: List[str] = []

        cand_cert_names = [c.name.lower() for c in resume.certifications]

        for req_cert in job.certifications:
            clean_req = req_cert.strip()
            req_lower = clean_req.lower()

            is_matched = False
            for cand_c in cand_cert_names:
                if req_lower in cand_c or cand_c in req_lower:
                    is_matched = True
                    break

            if is_matched:
                matched_certs.append(clean_req)
            else:
                missing_certs.append(clean_req)

        return matched_certs, missing_certs

    def match(
        self,
        resume: Resume,
        job: JobDescription,
    ) -> JobMatchResult:
        """
        Executes complete deterministic matching between Resume and JobDescription.
        """
        # 1. Collect candidate skills
        _, candidate_skills_lower = self.collect_candidate_skills(resume)

        # 2. Match Required Skills
        matched_required, missing_required = self.match_skill_collection(
            job.required_skills,
            candidate_skills_lower,
        )

        # 3. Match Preferred Skills
        matched_preferred, missing_preferred = self.match_skill_collection(
            job.preferred_skills,
            candidate_skills_lower,
        )

        # 4. Analyze Experience
        exp_analysis, exp_align, cand_years, req_years = self.analyze_experience(resume, job)

        # 5. Analyze Education
        edu_analysis, edu_align = self.analyze_education(resume, job)

        # 6. Certifications
        matched_certs, missing_certs = self.match_certifications(resume, job)

        # 7. Match rates (purely informational proportion, not score/grade)
        req_match_rate = (
            round(len(matched_required) / len(job.required_skills), 2)
            if job.required_skills
            else 1.0
        )
        pref_match_rate = (
            round(len(matched_preferred) / len(job.preferred_skills), 2)
            if job.preferred_skills
            else 1.0
        )

        logger.info(
            "Job matching computed: required_matched=%d/%d, preferred_matched=%d/%d, exp_alignment=%s, edu_alignment=%s",
            len(matched_required),
            len(job.required_skills),
            len(matched_preferred),
            len(job.preferred_skills),
            exp_align,
            edu_align,
        )

        return JobMatchResult(
            matched_skills=matched_required,
            missing_required_skills=missing_required,
            matched_preferred_skills=matched_preferred,
            missing_preferred_skills=missing_preferred,
            experience_analysis=exp_analysis,
            education_analysis=edu_analysis,
            experience_alignment=exp_align,
            education_alignment=edu_align,
            candidate_years_experience=cand_years,
            required_years_experience=req_years,
            matched_certifications=matched_certs,
            missing_certifications=missing_certs,
            required_skills_match_rate=req_match_rate,
            preferred_skills_match_rate=pref_match_rate,
            disclaimer=INFORMATIONAL_DISCLAIMER,
        )


# Global singleton instance
job_matcher = JobMatcher()
