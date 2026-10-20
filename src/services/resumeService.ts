/**
 * Resume upload API client with progress tracking and validation.
 */
import {
  ResumeUploadResponse,
  UploadError,
  ResumeExtractTextResponse,
  ResumeSectionsResponse,
  ResumeNLPEntitiesResponse,
} from '../types/resume';

const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

export class ClientValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ClientValidationError';
  }
}

/**
 * Validates file on client side prior to transmission.
 */
export function validateResumeFile(file: File): void {
  if (!file) {
    throw new ClientValidationError('Please select a file to upload.');
  }

  // Check file extension
  const fileNameLower = file.name.toLowerCase();
  if (!fileNameLower.endsWith('.pdf')) {
    throw new ClientValidationError(
      `Invalid file format: "${file.name}". Only PDF documents (.pdf) are permitted.`
    );
  }

  // Check empty file
  if (file.size === 0) {
    throw new ClientValidationError('The selected PDF file is empty (0 bytes).');
  }

  // Check maximum file size
  if (file.size > MAX_FILE_SIZE_BYTES) {
    const sizeInMB = (file.size / (1024 * 1024)).toFixed(1);
    throw new ClientValidationError(
      `File size (${sizeInMB}MB) exceeds the maximum allowed limit of ${MAX_FILE_SIZE_MB}MB.`
    );
  }
}

/**
 * Uploads a resume PDF to the backend POST /api/resumes/upload
 * with native progress tracking.
 */
export function uploadResumeFile(
  file: File,
  onProgress?: (progressPercent: number) => void
): Promise<ResumeUploadResponse> {
  return new Promise((resolve, reject) => {
    // 1. Client-side pre-validation
    try {
      validateResumeFile(file);
    } catch (err: unknown) {
      if (err instanceof Error) {
        return reject({
          message: err.message,
          statusCode: 400,
        } as UploadError);
      }
      return reject({
        message: 'Invalid file selection',
        statusCode: 400,
      } as UploadError);
    }

    const formData = new FormData();
    formData.append('file', file, file.name);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/resumes/upload', true);

    // Track upload progress
    if (xhr.upload && onProgress) {
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          const percent = Math.min(100, Math.round((event.loaded / event.total) * 100));
          onProgress(percent);
        }
      };
    }

    xhr.onload = () => {
      let responseBody: any = null;
      try {
        responseBody = JSON.parse(xhr.responseText);
      } catch {
        responseBody = { detail: xhr.responseText || 'Unknown server response' };
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(responseBody as ResumeUploadResponse);
      } else {
        const errorMessage =
          responseBody?.detail ||
          responseBody?.error ||
          responseBody?.message ||
          `Upload failed with status code ${xhr.status}`;

        reject({
          message: typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage),
          detail: responseBody?.detail,
          statusCode: xhr.status,
        } as UploadError);
      }
    };

    xhr.onerror = () => {
      reject({
        message: 'Network error: Failed to connect to upload server. Is the FastAPI backend running on port 8001?',
        statusCode: 0,
      } as UploadError);
    };

    xhr.ontimeout = () => {
      reject({
        message: 'Upload timed out. Please check your network connection and try again.',
        statusCode: 408,
      } as UploadError);
    };

    xhr.send(formData);
  });
}

/**
 * Creates a valid test PDF in-memory for testing purposes without needing a local file.
 */
export function generateSampleResumePdf(): File {
  const pdfString = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 124 >>
stream
BT
/F1 14 Tf
72 720 Td
(Alex Morgan - Senior Full Stack Engineer) Tj
0 -24 Td
(Experience: Python, FastAPI, React, TypeScript, Docker) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000202 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
377
%%EOF
`;
  const blob = new Blob([pdfString], { type: 'application/pdf' });
  return new File([blob], 'alex_morgan_resume.pdf', { type: 'application/pdf' });
}

/**
 * Calls POST /api/resumes/{resume_id}/extract-text to extract plain text via PyMuPDF.
 */
export async function extractResumeText(resumeId: string): Promise<ResumeExtractTextResponse> {
  const response = await fetch(`/api/resumes/${encodeURIComponent(resumeId)}/extract-text`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    let errorDetail = 'Failed to extract text from PDF document';
    try {
      const data = await response.json();
      errorDetail = data.detail || data.error || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Calls POST /api/resumes/{resume_id}/sections to detect and segment logical sections.
 */
export async function detectResumeSections(resumeId: string): Promise<ResumeSectionsResponse> {
  const response = await fetch(`/api/resumes/${encodeURIComponent(resumeId)}/sections`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    let errorDetail = 'Failed to detect sections in resume';
    try {
      const data = await response.json();
      errorDetail = data.detail || data.error || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Calls GET /api/resumes/schema to retrieve the canonical Pydantic JSON schema (Phase 7).
 */
export async function fetchResumeSchema(): Promise<Record<string, unknown>> {
  const response = await fetch('/api/resumes/schema', {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    let errorDetail = 'Failed to fetch resume schema specification';
    try {
      const data = await response.json();
      errorDetail = data.detail || data.error || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

/**
 * Calls POST /api/resumes/{resume_id}/entities to run deterministic spaCy NLP entity extraction (Phase 8).
 */
export async function extractResumeNLPEntities(resumeId: string): Promise<ResumeNLPEntitiesResponse> {
  const response = await fetch(`/api/resumes/${encodeURIComponent(resumeId)}/entities`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    let errorDetail = 'Failed to extract NLP entities with spaCy';
    try {
      const data = await response.json();
      errorDetail = data.detail || data.error || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json();
}


