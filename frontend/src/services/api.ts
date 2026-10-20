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
