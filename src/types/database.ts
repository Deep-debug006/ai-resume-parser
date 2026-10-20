/**
 * Types for Phase 11: PostgreSQL Database Persistence.
 */
import { StructuredResume } from './resume';

export interface DBResumeSummary {
  id: string;
  original_filename: string;
  candidate_name: string;
  candidate_email?: string | null;
  processing_status: string;
  extraction_method?: string | null;
  raw_text_char_count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface DBResumeDetail {
  id: string;
  user_id?: string | null;
  original_filename: string;
  file_identifier?: string | null;
  processing_status: string;
  extraction_method?: string | null;
  raw_text_char_count: number;
  created_at?: string | null;
  updated_at?: string | null;
  resume: StructuredResume;
}

export interface DBStats {
  status: string;
  database_name: string;
  total_resumes: number;
  total_skills: number;
  total_users: number;
}
