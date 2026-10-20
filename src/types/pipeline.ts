import { Resume } from './resume';

export type ProcessingStatus = 'uploaded' | 'processing' | 'completed' | 'failed';

export interface ResumeProcessResponse {
  resume_id: string;
  processing_status: ProcessingStatus;
  resume?: Resume | null;
  structured_resume_data?: Resume | null;
  original_filename: string;
  extraction_method?: string | null;
  raw_text_char_count?: number;
  sections_detected?: string[];
  nlp_entities_count?: Record<string, number>;
  llm_provider?: string | null;
  llm_model?: string | null;
  repair_attempts?: number;
  processing_duration_ms?: number;
  error?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface ResumeStatusResponse {
  resume_id: string;
  original_filename: string;
  processing_status: ProcessingStatus;
  extraction_method?: string | null;
  raw_text_char_count?: number;
  error?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}
