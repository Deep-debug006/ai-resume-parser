/**
 * Types for Phase 15: Resume-Job Matching
 */
import { Resume } from './resume';
import { JobDescription } from './job';

export interface JobMatchResult {
  matched_skills: string[];
  missing_required_skills: string[];
  matched_preferred_skills: string[];
  missing_preferred_skills: string[];
  experience_analysis: string;
  education_analysis: string;
  experience_alignment: 'meets_requirements' | 'exceeds_requirements' | 'below_requirements' | 'partially_meets' | 'not_specified' | string;
  education_alignment: 'meets_requirements' | 'exceeds_requirements' | 'below_requirements' | 'not_specified' | string;
  candidate_years_experience: number | null;
  required_years_experience: number | null;
  matched_certifications: string[];
  missing_certifications: string[];
  required_skills_match_rate: number;
  preferred_skills_match_rate: number;
  disclaimer: string;
}

export interface MatchPayload {
  resume?: Resume;
  job_description?: JobDescription;
  resume_id?: string;
  resume_text?: string;
  job_text?: string;
}
