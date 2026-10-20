/**
 * Types for Phase 16: Semantic Similarity Using Embeddings
 * Clearly distinguishes exact skill matches from dense semantic similarity.
 * Informational only - zero hiring probabilities or automated decisions.
 */
export interface RequirementSemanticMatch {
  requirement: string;
  best_matching_resume_chunk: string;
  source_type: string;
  similarity_score: number;
  relevance_tier: 'strong_alignment' | 'moderate_alignment' | 'minimal_alignment' | string;
}

export interface SemanticMatchResult {
  overall_semantic_similarity: number;
  summary_similarity: number | null;
  experience_semantic_alignment: number;
  requirement_matches: RequirementSemanticMatch[];
  exact_matched_skills: string[];
  missing_required_skills: string[];
  exact_skills_match_rate: number;
  semantic_insights: string;
  model_name: string;
  vector_dimension: number;
  disclaimer: string;
}

export interface SemanticMatchPayload {
  resume?: any;
  job_description?: any;
  resume_id?: string;
  resume_text?: string;
  job_text?: string;
  resume_data?: any;
  job_data?: any;
}
