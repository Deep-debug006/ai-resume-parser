import { HealthResponse } from '../types/health';

/**
 * Base API URL derived from environment or relative proxy path.
 */
const BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Fetch health status from FastAPI backend.
 */
export async function checkBackendHealth(): Promise<{ data: HealthResponse; latencyMs: number }> {
  const startTime = performance.now();
  const url = `${BASE_URL}/api/health`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  const latencyMs = Math.round(performance.now() - startTime);

  if (!response.ok) {
    throw new Error(`Backend responded with HTTP status ${response.status} (${response.statusText})`);
  }

  const data: HealthResponse = await response.json();
  return { data, latencyMs };
}

/**
 * Execute Phase 9 AI structured resume parsing for an uploaded PDF.
 */
export async function parseResume(resumeId: string): Promise<import('../types/resume').ResumeParseResponse> {
  const url = `${BASE_URL}/api/resumes/${encodeURIComponent(resumeId)}/parse`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Parsing failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Execute Phase 9 AI structured parsing directly on raw text.
 */
export async function parseDirectText(
  text: string,
  sections?: Record<string, string>,
  provider?: string,
): Promise<import('../types/resume').ResumeParseResponse> {
  const url = `${BASE_URL}/api/resumes/parse-direct`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ text, sections, provider }),
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Direct parsing failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Execute Phase 10 deterministic skill normalization.
 */
export async function normalizeSkills(skills: string[]): Promise<import('../types/skills').NormalizeSkillsResponse> {
  const url = `${BASE_URL}/api/skills/normalize`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ skills }),
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Skill normalization failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Fetch skill dictionary stats and canonical list.
 */
export async function getSkillDictionary(): Promise<import('../types/skills').SkillDictionaryStatsResponse> {
  const url = `${BASE_URL}/api/skills/dictionary`;

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to load skill dictionary (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * List persisted resumes from PostgreSQL (Phase 11).
 */
export async function listDBResumes(): Promise<import('../types/database').DBResumeSummary[]> {
  const url = `${BASE_URL}/api/resumes/db`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to list persisted resumes (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * Retrieve a full persisted resume by ID (Phase 11).
 */
export async function getDBResume(id: string): Promise<import('../types/database').DBResumeDetail> {
  const url = `${BASE_URL}/api/resumes/db/${encodeURIComponent(id)}`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to get persisted resume (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * Save a structured resume into PostgreSQL (Phase 11).
 */
export async function saveResumeToDB(payload: {
  resume: any;
  original_filename: string;
  user_id?: string;
  file_identifier?: string;
  extraction_method?: string;
  raw_text_char_count?: number;
}): Promise<import('../types/database').DBResumeDetail> {
  const url = `${BASE_URL}/api/resumes/db`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Failed to persist resume (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * Delete a persisted resume by ID (Phase 11).
 */
export async function deleteDBResume(id: string): Promise<{ status: string; id: string }> {
  const url = `${BASE_URL}/api/resumes/db/${encodeURIComponent(id)}`;

  const response = await fetch(url, {
    method: 'DELETE',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to delete resume (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * Trigger database seed data generation (Phase 11).
 */
export async function seedDB(): Promise<import('../types/database').DBResumeDetail> {
  const url = `${BASE_URL}/api/resumes/db/seed`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to seed database (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * Get PostgreSQL persistence metrics (Phase 11).
 */
export async function getDBStats(): Promise<import('../types/database').DBStats> {
  const url = `${BASE_URL}/api/resumes/db/stats`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch database stats (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * Execute Phase 12 Complete Resume Processing Pipeline for an uploaded file.
 * Upload PDF -> Extract text -> OCR fallback -> Clean -> Sections -> NLP -> LLM -> Pydantic -> Skill normalization -> PostgreSQL.
 */
export async function processResumeFile(
  file: File,
  userId?: string,
): Promise<import('../types/pipeline').ResumeProcessResponse> {
  const url = `${BASE_URL}/api/resumes/process`;
  const formData = new FormData();
  formData.append('file', file);
  if (userId) {
    formData.append('user_id', userId);
  }

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Pipeline execution failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Execute Phase 12 Complete Pipeline from an existing uploaded file ID.
 */
export async function processResumeById(
  fileId: string,
  userId?: string,
): Promise<import('../types/pipeline').ResumeProcessResponse> {
  const url = `${BASE_URL}/api/resumes/process`;
  const formData = new FormData();
  formData.append('file_id', fileId);
  if (userId) {
    formData.append('user_id', userId);
  }

  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Pipeline execution failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Fetch current processing status of a resume (Phase 12).
 */
export async function getResumePipelineStatus(
  resumeId: string,
): Promise<import('../types/pipeline').ResumeStatusResponse> {
  const url = `${BASE_URL}/api/resumes/${encodeURIComponent(resumeId)}/status`;

  const response = await fetch(url, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch status (HTTP ${response.status})`);
  }

  return response.json();
}

/**
 * Execute Phase 14 Job Description Parsing: POST /api/jobs/parse
 */
export async function parseJobDescription(
  text: string,
  envelope: boolean = true
): Promise<import('../types/job').JobParseResponse> {
  const url = `${BASE_URL}/api/jobs/parse?envelope=${envelope}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Job parsing failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Execute Phase 15 Resume-Job Matching: POST /api/jobs/match
 */
export async function matchResumeToJob(
  payload: import('../types/matching').MatchPayload
): Promise<import('../types/matching').JobMatchResult> {
  const url = `${BASE_URL}/api/jobs/match`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Resume-job matching failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Execute Phase 16 Semantic Similarity Using Embeddings: POST /api/jobs/semantic-match
 */
export async function computeSemanticMatch(
  payload: import('../types/semantic').SemanticMatchPayload
): Promise<import('../types/semantic').SemanticMatchResult> {
  const url = `${BASE_URL}/api/jobs/semantic-match`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  return response.json();
}

/**
 * Execute Phase 17 AI Resume Quality Analysis: POST /api/resumes/analyze
 */
export async function analyzeResume(
  payload: import('../types/analysis').ResumeAnalysisPayload
): Promise<import('../types/analysis').ResumeAnalysisResponse> {
  const url = `${BASE_URL}/api/resumes/analyze`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Resume analysis failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Execute Phase 17 AI Resume Quality Analysis by Resume ID: POST /api/resumes/{resume_id}/analyze
 */
export async function analyzeSavedResume(
  resumeId: string
): Promise<import('../types/analysis').ResumeAnalysisResponse> {
  const url = `${BASE_URL}/api/resumes/${encodeURIComponent(resumeId)}/analyze`;

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let errDetail = response.statusText;
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail || `Saved resume analysis failed with HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * JWT Authentication Helpers (Phase 18)
 */
export function getStoredAuthToken(): string | null {
  return localStorage.getItem('ai_resume_access_token');
}

export function setStoredAuthToken(token: string): void {
  localStorage.setItem('ai_resume_access_token', token);
}

export function removeStoredAuthToken(): void {
  localStorage.removeItem('ai_resume_access_token');
}

export function getAuthHeaders(): Record<string, string> {
  const token = getStoredAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function registerUser(payload: import('../types/auth').RegisterPayload): Promise<import('../types/auth').AuthResponse> {
  const response = await fetch(`${BASE_URL}/api/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errDetail = 'Registration failed';
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail);
  }

  const data: import('../types/auth').AuthResponse = await response.json();
  if (data.access_token) {
    setStoredAuthToken(data.access_token);
  }
  return data;
}

export async function loginUser(payload: import('../types/auth').LoginPayload): Promise<import('../types/auth').AuthResponse> {
  const response = await fetch(`${BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errDetail = 'Invalid credentials';
    try {
      const errJson = await response.json();
      errDetail = errJson.detail || errDetail;
    } catch {
      // fallback
    }
    throw new Error(errDetail);
  }

  const data: import('../types/auth').AuthResponse = await response.json();
  if (data.access_token) {
    setStoredAuthToken(data.access_token);
  }
  return data;
}

export async function fetchCurrentUser(): Promise<import('../types/auth').User | null> {
  const token = getStoredAuthToken();
  if (!token) return null;

  const response = await fetch(`${BASE_URL}/api/auth/me`, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    removeStoredAuthToken();
    return null;
  }

  return response.json();
}

/**
 * Phase 20: User History APIs
 */
export async function fetchHistorySummary(): Promise<import('../types/history').HistoryOverviewResponse> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/history/summary`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to load history summary');
  }

  return response.json();
}

export async function fetchResumeHistory(params: {
  page?: number;
  pageSize?: number;
  search?: string;
  statusFilter?: string;
  sortBy?: string;
}): Promise<import('../types/history').PaginatedResumesResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', params.page.toString());
  if (params.pageSize) query.set('page_size', params.pageSize.toString());
  if (params.search) query.set('search', params.search);
  if (params.statusFilter) query.set('status_filter', params.statusFilter);
  if (params.sortBy) query.set('sort_by', params.sortBy);

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/history/resumes?${query.toString()}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to load resume history');
  }

  return response.json();
}

export async function fetchJobHistory(params: {
  page?: number;
  pageSize?: number;
  search?: string;
  sortBy?: string;
}): Promise<import('../types/history').PaginatedJobsResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', params.page.toString());
  if (params.pageSize) query.set('page_size', params.pageSize.toString());
  if (params.search) query.set('search', params.search);
  if (params.sortBy) query.set('sort_by', params.sortBy);

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/history/jobs?${query.toString()}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to load job description history');
  }

  return response.json();
}

export async function fetchAnalysisHistory(params: {
  page?: number;
  pageSize?: number;
  search?: string;
  analysisType?: string;
  sortBy?: string;
}): Promise<import('../types/history').PaginatedAnalysesResponse> {
  const query = new URLSearchParams();
  if (params.page) query.set('page', params.page.toString());
  if (params.pageSize) query.set('page_size', params.pageSize.toString());
  if (params.search) query.set('search', params.search);
  if (params.analysisType) query.set('analysis_type', params.analysisType);
  if (params.sortBy) query.set('sort_by', params.sortBy);

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/history/analyses?${query.toString()}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to load analysis history');
  }

  return response.json();
}

export async function fetchAnalysisDetail(analysisId: string): Promise<import('../types/history').AnalysisHistoryDetail> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/history/analyses/${encodeURIComponent(analysisId)}`, {
    method: 'GET',
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to load analysis details');
  }

  return response.json();
}

export async function recordAnalysisHistory(payload: any): Promise<import('../types/history').AnalysisHistorySummary> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/history/analyses`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error('Failed to record analysis history');
  }

  return response.json();
}

export async function deleteAnalysisHistoryRecord(analysisId: string): Promise<void> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/history/analyses/${encodeURIComponent(analysisId)}`, {
    method: 'DELETE',
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to delete analysis record');
  }
}

export async function deleteJobRecord(jobId: string): Promise<void> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...getAuthHeaders(),
  };

  const response = await fetch(`${BASE_URL}/api/jobs/${encodeURIComponent(jobId)}`, {
    method: 'DELETE',
    headers,
  });

  if (!response.ok) {
    throw new Error('Failed to delete job description');
  }
}
