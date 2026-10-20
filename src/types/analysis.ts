/**
 * Types for Phase 17: AI Resume Quality Analysis
 * Evaluates resumes against general quality criteria:
 * - clarity
 * - section completeness
 * - bullet-point quality
 * - measurable achievements where present
 * - skill organization
 * - project descriptions
 * - formatting-related text issues
 * - missing common information
 * - potential improvements
 *
 * Strict anti-hallucination: No fake accomplishments or invented facts.
 */

export interface ResumeQualityCriterionEvaluation {
  criterion: string;
  score?: number | null;
  observations: string[];
}

export interface ResumeAnalysisResponse {
  strengths: string[];
  areas_for_improvement: string[];
  suggestions: string[];
  criteria_evaluations?: Record<string, ResumeQualityCriterionEvaluation>;
  factual_summary?: {
    sections_present?: string[];
    total_experience_entries?: number;
    total_education_entries?: number;
    total_projects?: number;
    total_skills_count?: number;
    has_contact_email?: boolean;
    has_contact_phone?: boolean;
    has_linkedin?: boolean;
    has_github?: boolean;
    has_portfolio?: boolean;
    has_summary?: boolean;
    bullet_points_count?: number;
    measurable_metrics_detected?: string[];
    action_verbs_detected?: string[];
  };
  llm_provider?: string;
  llm_model?: string;
  analysis_duration_ms?: number;
}

export interface ResumeAnalysisPayload {
  resume_id?: string;
  text?: string;
  resume?: any;
}
