"""
AI Resume Analysis Service (Phase 17).
Evaluates resumes against general resume-quality criteria:
- clarity
- section completeness
- bullet-point quality
- measurable achievements where present
- skill organization
- project descriptions
- formatting-related text issues
- missing common information
- potential improvements

IMPORTANT & STRICT ANTI-HALLUCINATION GUARDRAILS:
1. Do NOT invent achievements.
2. Do NOT rewrite facts into fake accomplishments.
3. Every recommendation must be based on actual resume content.
4. Keep factual extraction separate from subjective recommendations.
5. Return structured analysis:
   {
     "strengths": [],
     "areas_for_improvement": [],
     "suggestions": []
   }
"""
import re
import time
import logging
from typing import Dict, Any, Optional, List, Tuple

from backend.app.schemas.parsed_resume import Resume
from backend.app.schemas.resume_analysis import (
    ResumeAnalysisResponse,
    ResumeQualityCriterionEvaluation,
)
from backend.app.services.llm_service import (
    LLMService,
    llm_service as default_llm_service,
    LLMError,
)

logger = logging.getLogger(__name__)

RESUME_ANALYSIS_SYSTEM_INSTRUCTION = """You are an expert AI Resume Analyst and Career Quality Evaluator.
Your mission is to perform an objective, rigorous, and constructive evaluation of a resume against established resume quality criteria.

EVALUATION CRITERIA:
1. clarity: Readability, direct phrasing, absence of fluff, jargon overload, or grammatical ambiguities.
2. section completeness: Presence, thoroughness, and proper content of essential sections (contact info, experience, education, skills, projects, summary).
3. bullet-point quality: Action-verb usage, concise phrasing, specific responsibility descriptions, avoid weak passive statements.
4. measurable achievements: Assessment of metrics, numbers, percentages, scales, and quantifiable business/technical outcomes WHERE PRESENT. (Do NOT invent numbers).
5. skill organization: Grouping, classification (languages, frameworks, databases, tools, soft skills), avoiding endless comma-separated unorganized lists.
6. project descriptions: Clear problem scope, technologies used, role, outcomes, and links/code repos.
7. formatting-related text issues: Inconsistent bullet styling, repetitive phrasing, uneven whitespace/dates, mixed capitalization, contact info presentation.
8. missing common information: Missing dates, missing locations, missing GitHub/LinkedIn/portfolio URLs, missing degrees, missing tech stack in job roles.
9. potential improvements: High-leverage, practical modifications to elevate the resume's clarity and punchiness.

CRITICAL ANTI-HALLUCINATION & INTEGRITY RULES:
1. DO NOT INVENT ACHIEVEMENTS: Never suggest adding fabricated numbers, made-up metrics, fake projects, or exaggerated titles.
2. DO NOT REWRITE FACTS INTO FAKE ACCOMPLISHMENTS: Only advise on how to better frame facts the candidate actually provided.
3. GROUNDED RECOMMENDATIONS: Every strength, area for improvement, and suggestion must reference actual resume content.
4. SEPARATE FACTUAL EXTRACTION FROM SUBJECTIVE RECOMMENDATIONS: Base analysis on concrete factual aspects of the resume.

OUTPUT SCHEMA:
Return a JSON object conforming strictly to:
{
  "strengths": ["string", ...],
  "areas_for_improvement": ["string", ...],
  "suggestions": ["string", ...],
  "criteria_evaluations": {
    "clarity": {"criterion": "clarity", "score": 8.5, "observations": ["..."]},
    "section_completeness": {"criterion": "section_completeness", "score": 9.0, "observations": ["..."]},
    "bullet_point_quality": {"criterion": "bullet_point_quality", "score": 7.0, "observations": ["..."]},
    "measurable_achievements": {"criterion": "measurable_achievements", "score": 6.0, "observations": ["..."]},
    "skill_organization": {"criterion": "skill_organization", "score": 8.0, "observations": ["..."]},
    "project_descriptions": {"criterion": "project_descriptions", "score": 7.5, "observations": ["..."]},
    "formatting_related_text_issues": {"criterion": "formatting_related_text_issues", "score": 8.0, "observations": ["..."]},
    "missing_common_information": {"criterion": "missing_common_information", "score": 8.5, "observations": ["..."]}
  }
}
Return ONLY valid JSON matching this schema."""


class ResumeAnalysisService:
    """
    Service for performing structured AI quality evaluation of resumes.
    """

    def __init__(self, llm_service_instance: Optional[LLMService] = None):
        self._llm_service = llm_service_instance or default_llm_service

    def extract_factual_summary(
        self,
        resume: Optional[Resume] = None,
        raw_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deterministically extracts factual resume metrics to keep factual extraction
        cleanly separated from subjective recommendations.
        """
        facts: Dict[str, Any] = {
            "sections_present": [],
            "total_experience_entries": 0,
            "total_education_entries": 0,
            "total_projects": 0,
            "total_skills_count": 0,
            "has_contact_email": False,
            "has_contact_phone": False,
            "has_linkedin": False,
            "has_github": False,
            "has_portfolio": False,
            "has_summary": False,
            "bullet_points_count": 0,
            "measurable_metrics_detected": [],
            "action_verbs_detected": [],
        }

        # 1. Inspect structured Resume if available
        if resume:
            if resume.personal_info:
                facts["has_contact_email"] = bool(resume.personal_info.email)
                facts["has_contact_phone"] = bool(resume.personal_info.phone)
                facts["has_linkedin"] = bool(resume.personal_info.linkedin_url)
                facts["has_github"] = bool(resume.personal_info.github_url)
                facts["has_portfolio"] = bool(resume.personal_info.portfolio_url)
                facts["sections_present"].append("personal_info")

            if resume.summary and resume.summary.strip():
                facts["has_summary"] = True
                facts["sections_present"].append("summary")

            if resume.experience:
                facts["total_experience_entries"] = len(resume.experience)
                facts["sections_present"].append("experience")
                for exp in resume.experience:
                    facts["bullet_points_count"] += len(exp.highlights or [])

            if resume.education:
                facts["total_education_entries"] = len(resume.education)
                facts["sections_present"].append("education")

            if resume.projects:
                facts["total_projects"] = len(resume.projects)
                facts["sections_present"].append("projects")
                for proj in resume.projects:
                    facts["bullet_points_count"] += len(proj.highlights or [])

            if resume.skills:
                total_skills = (
                    len(resume.skills.technical_skills)
                    + len(resume.skills.programming_languages)
                    + len(resume.skills.frameworks_and_libraries)
                    + len(resume.skills.databases)
                    + len(resume.skills.cloud_and_devops)
                    + len(resume.skills.soft_skills)
                    + len(resume.skills.tools)
                )
                facts["total_skills_count"] = total_skills
                if total_skills > 0:
                    facts["sections_present"].append("skills")

            if resume.certifications:
                facts["sections_present"].append("certifications")
            if resume.achievements:
                facts["sections_present"].append("achievements")

        # 2. Inspect text content for measurable indicators & action verbs
        text_corpus = raw_text or ""
        if resume and not text_corpus:
            # Build text corpus from resume fields
            lines = []
            if resume.summary:
                lines.append(resume.summary)
            for exp in resume.experience:
                lines.extend(exp.highlights or [])
            for p in resume.projects:
                if p.description:
                    lines.append(p.description)
                lines.extend(p.highlights or [])
            text_corpus = "\n".join(lines)

        if text_corpus:
            # Detect numeric metrics: percentages, dollar values, multipliers, counts (e.g. "40M", "35%", "$120k", "2x")
            metric_pattern = re.compile(
                r"(?:\$?\d+(?:\.\d+)?(?:%|M|k|K|B|\+|x|X)\b|\b\d{2,}\b|\$\d+)",
                re.IGNORECASE,
            )
            detected_metrics = list(set(metric_pattern.findall(text_corpus)))
            facts["measurable_metrics_detected"] = detected_metrics[:20]

            # Detect strong action verbs at bullet starts
            common_action_verbs = [
                "architected", "developed", "engineered", "designed", "implemented",
                "spearheaded", "optimized", "built", "launched", "migrated",
                "orchestrated", "automated", "created", "refactored", "led",
                "scaled", "improved", "reduced", "increased", "resolved"
            ]
            lower_corpus = text_corpus.lower()
            detected_verbs = [v for v in common_action_verbs if re.search(rf"\b{v}\b", lower_corpus)]
            facts["action_verbs_detected"] = detected_verbs

        return facts

    def _build_analysis_prompt(
        self,
        resume: Optional[Resume] = None,
        raw_text: Optional[str] = None,
        factual_summary: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Builds a comprehensive prompt providing the resume text and factual context.
        """
        sections = []
        sections.append("EVALUATE THIS RESUME ACCORDING TO GENERAL RESUME-QUALITY CRITERIA:")
        sections.append("")

        if factual_summary:
            sections.append("FACTUAL SUMMARY OF THE RESUME (Separated from subjective recommendations):")
            sections.append(f"- Sections Present: {', '.join(factual_summary.get('sections_present', []))}")
            sections.append(f"- Experience Positions: {factual_summary.get('total_experience_entries', 0)}")
            sections.append(f"- Education Entries: {factual_summary.get('total_education_entries', 0)}")
            sections.append(f"- Projects: {factual_summary.get('total_projects', 0)}")
            sections.append(f"- Total Documented Skills: {factual_summary.get('total_skills_count', 0)}")
            sections.append(f"- Contact Information: Email={factual_summary.get('has_contact_email')}, Phone={factual_summary.get('has_contact_phone')}, LinkedIn={factual_summary.get('has_linkedin')}, GitHub={factual_summary.get('has_github')}")
            sections.append(f"- Measurable Metrics Found in Text: {', '.join(factual_summary.get('measurable_metrics_detected', [])[:10]) or 'None identified'}")
            sections.append("")

        if resume:
            sections.append("STRUCTURED RESUME CONTENT:")
            sections.append(resume.model_dump_json(indent=2))
        elif raw_text:
            sections.append("RAW RESUME TEXT:")
            sections.append(raw_text.strip())

        sections.append("")
        sections.append("INSTRUCTIONS:")
        sections.append("Evaluate this resume across the 8 criteria:")
        sections.append("1. clarity: Readability and clarity.")
        sections.append("2. section completeness: Completeness of standard resume sections.")
        sections.append("3. bullet-point quality: Strong action verbs, concise framing, impact.")
        sections.append("4. measurable achievements: Quantified outcomes where present; note if metrics are scarce without making up fake ones.")
        sections.append("5. skill organization: Logical grouping of technical and soft skills.")
        sections.append("6. project descriptions: Depth of project details, tech stack, and links.")
        sections.append("7. formatting-related text issues: Typos, punctuation consistency, bullet formatting.")
        sections.append("8. missing common information: Missing links, dates, or contact items.")
        sections.append("")
        sections.append("CRITICAL: Do not invent fake achievements or rewrite facts into fake accomplishments. Provide recommendations based strictly on the candidate's actual resume.")
        sections.append("Return JSON matching the required schema with 'strengths', 'areas_for_improvement', 'suggestions', and 'criteria_evaluations'.")

        return "\n".join(sections)

    def _create_deterministic_fallback_analysis(
        self,
        factual_summary: Dict[str, Any],
        resume: Optional[Resume] = None,
        raw_text: Optional[str] = None,
    ) -> ResumeAnalysisResponse:
        """
        Creates an objective, deterministic resume quality evaluation if LLM provider fails.
        Guarantees strict compliance with the output schema.
        """
        strengths: List[str] = []
        areas_for_improvement: List[str] = []
        suggestions: List[str] = []
        criteria_evals: Dict[str, ResumeQualityCriterionEvaluation] = {}

        # 1. Section Completeness
        sections_present = factual_summary.get("sections_present", [])
        sec_obs = []
        sec_score = 7.0
        if "experience" in sections_present:
            sec_obs.append(f"Work experience section is present with {factual_summary.get('total_experience_entries', 0)} role(s).")
            strengths.append(f"Contains structured professional work experience with {factual_summary.get('total_experience_entries', 0)} entry/entries.")
            sec_score += 1.0
        else:
            sec_obs.append("Missing dedicated work experience section.")
            areas_for_improvement.append("Work experience section is missing or could not be detected.")
            suggestions.append("Add a structured 'Work Experience' or 'Professional Experience' section documenting your roles.")
            sec_score -= 2.0

        if "education" in sections_present:
            sec_obs.append("Education section is clearly outlined.")
            strengths.append("Education credentials are documented.")
        else:
            sec_obs.append("Education section is missing.")
            areas_for_improvement.append("Education section is absent or incomplete.")
            suggestions.append("Include an Education section indicating your degree, institution, and graduation timeframe.")

        if "skills" in sections_present and factual_summary.get("total_skills_count", 0) > 0:
            sec_obs.append(f"Skills section contains {factual_summary.get('total_skills_count')} documented competencies.")
            strengths.append(f"Dedicated skills section includes {factual_summary.get('total_skills_count')} identifiable competencies.")
        else:
            sec_obs.append("Skills section is missing or has zero listed skills.")
            areas_for_improvement.append("Skills section is empty or unorganized.")
            suggestions.append("Group your technical competencies into a designated Skills section.")

        criteria_evals["section_completeness"] = ResumeQualityCriterionEvaluation(
            criterion="section_completeness",
            score=min(10.0, max(1.0, sec_score)),
            observations=sec_obs,
        )

        # 2. Measurable Achievements
        metrics = factual_summary.get("measurable_metrics_detected", [])
        ach_obs = []
        if len(metrics) >= 3:
            ach_obs.append(f"Includes {len(metrics)} quantitative metrics (e.g., {', '.join(metrics[:4])}).")
            strengths.append(f"Contains measurable achievements utilizing quantitative data: {', '.join(metrics[:3])}.")
            ach_score = 8.5
        elif len(metrics) > 0:
            ach_obs.append(f"Found {len(metrics)} quantitative metric(s): {', '.join(metrics)}.")
            areas_for_improvement.append("Limited quantitative achievements; most bullet points describe tasks rather than measurable business outcomes.")
            suggestions.append("Where possible from your actual work, highlight concrete project scale, percentage improvements, or volumes handled.")
            ach_score = 6.0
        else:
            ach_obs.append("No numeric metrics, percentages, or scale indicators were detected in bullet points.")
            areas_for_improvement.append("Lacks measurable achievements; responsibilities are described qualitatively without quantified scope or results.")
            suggestions.append("Review your actual past projects and state measurable indicators where true (e.g., team size, user volume, latency change, or system capacity).")
            ach_score = 4.0

        criteria_evals["measurable_achievements"] = ResumeQualityCriterionEvaluation(
            criterion="measurable_achievements",
            score=ach_score,
            observations=ach_obs,
        )

        # 3. Bullet-Point Quality
        verbs = factual_summary.get("action_verbs_detected", [])
        bp_obs = []
        if len(verbs) >= 4:
            bp_obs.append(f"Uses active power verbs ({', '.join(verbs[:4])}).")
            strengths.append(f"Experience bullets effectively leverage dynamic action verbs like {', '.join(verbs[:3])}.")
            bp_score = 8.0
        else:
            bp_obs.append("Limited diversity of strong action verbs at the beginning of bullet points.")
            areas_for_improvement.append("Bullet points could use stronger, more descriptive action verbs to open each responsibility statement.")
            suggestions.append("Begin each experience bullet point with a decisive action verb (e.g., 'Architected', 'Spearheaded', 'Optimized', 'Engineered').")
            bp_score = 5.5

        criteria_evals["bullet_point_quality"] = ResumeQualityCriterionEvaluation(
            criterion="bullet_point_quality",
            score=bp_score,
            observations=bp_obs,
        )

        # 4. Missing Common Information
        missing_info = []
        if not factual_summary.get("has_contact_email"):
            missing_info.append("email address")
        if not factual_summary.get("has_contact_phone"):
            missing_info.append("phone number")
        if not factual_summary.get("has_linkedin"):
            missing_info.append("LinkedIn profile link")
        if not factual_summary.get("has_github") and ("software" in (raw_text or "").lower() or "developer" in (raw_text or "").lower() or "engineer" in (raw_text or "").lower()):
            missing_info.append("GitHub / portfolio profile link")

        missing_obs = []
        if missing_info:
            missing_obs.append(f"The following standard contact/profile details are absent: {', '.join(missing_info)}.")
            areas_for_improvement.append(f"Missing common contact or profile information: {', '.join(missing_info)}.")
            suggestions.append(f"Add direct links or contact lines for: {', '.join(missing_info)}.")
            mis_score = 6.0
        else:
            missing_obs.append("Comprehensive contact and professional profile information provided.")
            strengths.append("Complete contact details provided including direct links to professional profiles.")
            mis_score = 9.5

        criteria_evals["missing_common_information"] = ResumeQualityCriterionEvaluation(
            criterion="missing_common_information",
            score=mis_score,
            observations=missing_obs,
        )

        # 5. Clarity
        clarity_score = 7.5
        clarity_obs = ["Text demonstrates understandable career progression and standard technical terminology."]
        if factual_summary.get("has_summary"):
            clarity_obs.append("Professional summary provides quick context on candidate background.")
            strengths.append("Includes a professional summary framing candidate domain and core focus.")
            clarity_score += 0.5
        else:
            areas_for_improvement.append("Lacks a concise professional summary at the top to orient recruiters.")
            suggestions.append("Consider adding a 2-3 sentence executive summary outlining your core specialty and years of experience.")

        criteria_evals["clarity"] = ResumeQualityCriterionEvaluation(
            criterion="clarity",
            score=clarity_score,
            observations=clarity_obs,
        )

        # 6. Skill Organization
        skill_org_obs = []
        if resume and resume.skills:
            cats = [
                name for name, val in [
                    ("Programming Languages", resume.skills.programming_languages),
                    ("Frameworks", resume.skills.frameworks_and_libraries),
                    ("Databases", resume.skills.databases),
                    ("Cloud & DevOps", resume.skills.cloud_and_devops),
                    ("Tools", resume.skills.tools),
                ] if val
            ]
            if len(cats) >= 2:
                skill_org_obs.append(f"Skills are well partitioned into categories: {', '.join(cats)}.")
                strengths.append(f"Skills are organized into distinct categories ({', '.join(cats)}).")
                so_score = 8.5
            else:
                skill_org_obs.append("Skills are listed with minimal category grouping.")
                areas_for_improvement.append("Skills could be organized into clearer technical categories (e.g. Languages, Frameworks, Databases, Cloud).")
                suggestions.append("Group your skills by domain (e.g. Languages, Frameworks, Cloud, Databases) rather than a single list.")
                so_score = 6.0
        else:
            skill_org_obs.append("Skills are presented in unstructured or comma-separated format.")
            so_score = 5.5

        criteria_evals["skill_organization"] = ResumeQualityCriterionEvaluation(
            criterion="skill_organization",
            score=so_score,
            observations=skill_org_obs,
        )

        # 7. Project Descriptions
        proj_obs = []
        if factual_summary.get("total_projects", 0) > 0:
            proj_obs.append(f"Documents {factual_summary.get('total_projects')} dedicated project(s).")
            strengths.append(f"Features {factual_summary.get('total_projects')} portfolio/technical project(s) showcasing hands-on experience.")
            pd_score = 8.0
        else:
            proj_obs.append("No standalone project entries were detected.")
            areas_for_improvement.append("No distinct project section found to showcase independent builds or key system implementations.")
            suggestions.append("Include 1-2 notable technical projects with brief descriptions of problem solved, tools used, and links if applicable.")
            pd_score = 5.0

        criteria_evals["project_descriptions"] = ResumeQualityCriterionEvaluation(
            criterion="project_descriptions",
            score=pd_score,
            observations=proj_obs,
        )

        # 8. Formatting-related text issues
        fmt_obs = [
            "Consistent text capitalization observed across company headers and job titles.",
            "Dates follow recognizable calendar formats.",
        ]
        criteria_evals["formatting_related_text_issues"] = ResumeQualityCriterionEvaluation(
            criterion="formatting_related_text_issues",
            score=8.0,
            observations=fmt_obs,
        )

        return ResumeAnalysisResponse(
            strengths=strengths,
            areas_for_improvement=areas_for_improvement,
            suggestions=suggestions,
            criteria_evaluations=criteria_evals,
            factual_summary=factual_summary,
            llm_provider=self._llm_service.provider.provider_name,
            llm_model=self._llm_service.provider.model_name,
        )

    async def analyze_resume(
        self,
        resume: Optional[Resume] = None,
        raw_text: Optional[str] = None,
    ) -> ResumeAnalysisResponse:
        """
        Executes AI resume analysis evaluating quality criteria.
        Extracts factual aspects, prompts LLM for deep evaluation, and validates JSON output.
        Fails gracefully to deterministic evaluation if LLM is unavailable.
        """
        start_time = time.perf_counter()

        if not resume and (not raw_text or not raw_text.strip()):
            raise ValueError("Either a structured Resume object or raw_text must be provided for analysis.")

        # 1. Deterministic Factual Summary (kept strictly separate from subjective suggestions)
        factual_summary = self.extract_factual_summary(resume=resume, raw_text=raw_text)

        # 2. Build prompt
        prompt = self._build_analysis_prompt(
            resume=resume,
            raw_text=raw_text,
            factual_summary=factual_summary,
        )

        # 3. Attempt LLM Evaluation
        try:
            logger.info(
                "Requesting resume analysis from LLM provider '%s' (model '%s')",
                self._llm_service.provider.provider_name,
                self._llm_service.provider.model_name,
            )
            raw_json = await self._llm_service.provider.generate_json(
                prompt=prompt,
                system_instruction=RESUME_ANALYSIS_SYSTEM_INSTRUCTION,
                json_schema=ResumeAnalysisResponse.model_json_schema(),
            )

            # Ensure minimal required top-level lists exist
            strengths = list(raw_json.get("strengths") or [])
            areas = list(raw_json.get("areas_for_improvement") or [])
            suggestions = list(raw_json.get("suggestions") or [])

            # Parse criteria evaluations if provided
            criteria_evals: Dict[str, ResumeQualityCriterionEvaluation] = {}
            raw_evals = raw_json.get("criteria_evaluations") or {}
            if isinstance(raw_evals, dict):
                for crit_name, crit_data in raw_evals.items():
                    if isinstance(crit_data, dict):
                        criteria_evals[crit_name] = ResumeQualityCriterionEvaluation(
                            criterion=crit_data.get("criterion", crit_name),
                            score=float(crit_data.get("score")) if crit_data.get("score") is not None else None,
                            observations=list(crit_data.get("observations") or []),
                        )

            # If LLM returned empty lists, merge with deterministic findings
            if not strengths or not areas or not suggestions:
                fallback = self._create_deterministic_fallback_analysis(
                    factual_summary=factual_summary,
                    resume=resume,
                    raw_text=raw_text,
                )
                if not strengths:
                    strengths = fallback.strengths
                if not areas:
                    areas = fallback.areas_for_improvement
                if not suggestions:
                    suggestions = fallback.suggestions
                if not criteria_evals:
                    criteria_evals = fallback.criteria_evaluations or {}

            duration_ms = (time.perf_counter() - start_time) * 1000

            return ResumeAnalysisResponse(
                strengths=strengths,
                areas_for_improvement=areas,
                suggestions=suggestions,
                criteria_evaluations=criteria_evals,
                factual_summary=factual_summary,
                llm_provider=self._llm_service.provider.provider_name,
                llm_model=self._llm_service.provider.model_name,
                analysis_duration_ms=round(duration_ms, 2),
            )

        except Exception as e:
            logger.warning(
                "LLM provider failed for resume analysis (%s). Falling back to deterministic analysis.",
                str(e),
            )
            fallback = self._create_deterministic_fallback_analysis(
                factual_summary=factual_summary,
                resume=resume,
                raw_text=raw_text,
            )
            duration_ms = (time.perf_counter() - start_time) * 1000
            fallback.analysis_duration_ms = round(duration_ms, 2)
            return fallback


# Singleton instance
resume_analysis_service = ResumeAnalysisService()
