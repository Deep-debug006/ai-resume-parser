/**
 * TypeScript types for Phase 14: Job Description Parsing
 */

export interface JobDescription {
  job_title: string;
  company: string | null;
  required_skills: string[];
  preferred_skills: string[];
  education_requirements: string[];
  experience_requirements: string[];
  responsibilities: string[];
  tools_and_technologies: string[];
  certifications: string[];
  location?: string | null;
  employment_type?: string | null;
  salary_range?: string | null;
  raw_text_char_count?: number | null;
}

export interface JobParseRequest {
  text?: string;
  job_description?: string;
}

export interface JobParseResponse {
  success: boolean;
  job: JobDescription;
  normalized_skills_count: number;
  duration_ms: number;
  provider?: string;
}
