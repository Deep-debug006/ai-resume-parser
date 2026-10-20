/**
 * Types and interfaces for Resume Upload, Extraction, Preprocessing, Section Detection,
 * Structured Schema, and Phase 8 spaCy NLP Entities.
 */

export interface ResumeUploadResponse {
  success: boolean;
  filename: string;
  original_filename: string;
  size_bytes: number;
  message: string;
  uploaded_at: string;
}

export interface ResumeExtractTextResponse {
  resume_id: string;
  text: string;
  page_count: number;
  extraction_method?: 'pdf_text' | 'ocr' | 'mixed' | string;
  original_char_count?: number;
  cleaned_char_count?: number;
  transformations_applied?: string[];
}

export interface ResumeSectionsResponse {
  resume_id: string;
  sections: Record<string, string>;
  detected_sections_list: string[];
  raw_headings: Record<string, string>;
  unclassified: string;
}

// Phase 8: spaCy NLP Entities
export interface NLPEntitySpan {
  text: string;
  label: string;
  start_char: number;
  end_char: number;
}

export interface ResumeNLPEntitiesResponse {
  resume_id: string;
  persons: string[];
  organizations: string[];
  locations: string[];
  dates: string[];
  emails: string[];
  urls: string[];
  entities: NLPEntitySpan[];
}

// Phase 7: Structured Resume Domain Model
export interface PersonalInfo {
  full_name: string;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  linkedin_url?: string | null;
  github_url?: string | null;
  portfolio_url?: string | null;
}

export interface Education {
  institution: string;
  degree?: string | null;
  field_of_study?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  gpa?: number | null;
  gpa_max?: number | null;
  honors: string[];
  courses: string[];
}

export interface SkillSet {
  technical_skills: string[];
  programming_languages: string[];
  frameworks_and_libraries: string[];
  databases: string[];
  cloud_and_devops: string[];
  soft_skills: string[];
  tools: string[];
}

export interface Experience {
  company: string;
  title: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  highlights: string[];
  technologies: string[];
}

export interface Project {
  name: string;
  description?: string | null;
  url?: string | null;
  highlights: string[];
  technologies: string[];
  start_date?: string | null;
  end_date?: string | null;
}

export interface Certification {
  name: string;
  issuer?: string | null;
  issue_date?: string | null;
  expiration_date?: string | null;
  credential_id?: string | null;
  url?: string | null;
}

export interface Achievement {
  title: string;
  issuer?: string | null;
  date?: string | null;
  description?: string | null;
}

export interface StructuredResume {
  personal_info: PersonalInfo;
  summary?: string | null;
  objective?: string | null;
  education: Education[];
  skills: SkillSet;
  experience: Experience[];
  projects: Project[];
  certifications: Certification[];
  achievements: Achievement[];
  languages: string[];
  interests: string[];
}

export interface UploadError {
  message: string;
  detail?: string;
  statusCode?: number;
}

export type UploadStatus = 'idle' | 'dragging' | 'uploading' | 'success' | 'error';
export type ExtractionStatus = 'idle' | 'extracting' | 'success' | 'error';
export type SectionStatus = 'idle' | 'detecting' | 'success' | 'error';
export type NLPStatus = 'idle' | 'extracting' | 'success' | 'error';
