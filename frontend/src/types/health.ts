export interface HealthResponse {
  status: string;
  [key: string]: unknown;
}

export interface BackendConnectionState {
  isLoading: boolean;
  isConnected: boolean | null;
  latencyMs: number | null;
  data: HealthResponse | null;
  error: string | null;
  lastChecked: Date | null;
}
