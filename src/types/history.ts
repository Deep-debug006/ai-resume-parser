/**
 * TypeScript types for Phase 20: User History
 */

export interface PaginatedMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ResumeHistorySummary {
  id: string;
  user_id?: string | null;
  original_filename: string;
  candidate_name?: string | null;
  candidate_email?: string | null;
  processing_status: string;
  extraction_method?: string | null;
  raw_text_char_count: number;
  skills_count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface JobHistorySummary {
  id: string;
  user_id?: string | null;
  title?: string | null;
  company?: string | null;
  char_count: number;
  required_skills_count: number;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AnalysisHistorySummary {
  id: string;
  user_id?: string | null;
  resume_id?: string | null;
  candidate_name?: string | null;
  resume_filename?: string | null;
  job_id?: string | null;
  job_title?: string | null;
  company?: string | null;
  analysis_type: string;
  score?: number | null;
  match_rate?: number | null;
  summary?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AnalysisHistoryDetail {
  id: string;
  user_id?: string | null;
  resume_id?: string | null;
  candidate_name?: string | null;
  resume_filename?: string | null;
  job_id?: string | null;
  job_title?: string | null;
  company?: string | null;
  analysis_type: string;
  score?: number | null;
  match_rate?: number | null;
  summary?: string | null;
  result_data?: Record<string, any> | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginatedResumesResponse {
  items: ResumeHistorySummary[];
  meta: PaginatedMeta;
}

export interface PaginatedJobsResponse {
  items: JobHistorySummary[];
  meta: PaginatedMeta;
}

export interface PaginatedAnalysesResponse {
  items: AnalysisHistorySummary[];
  meta: PaginatedMeta;
}

export interface HistoryOverviewResponse {
  total_resumes: number;
  total_jobs: number;
  total_analyses: number;
}
