import React, { useState, useEffect, useCallback } from 'react';
import { CheckCircle2, XCircle, Loader2, RefreshCw, Zap, Clock, ShieldCheck } from 'lucide-react';
import { checkBackendHealth } from '../services/api';
import { BackendConnectionState } from '../types/health';

export const HealthStatus: React.FC = () => {
  const [state, setState] = useState<BackendConnectionState>({
    isLoading: true,
    isConnected: null,
    latencyMs: null,
    data: null,
    error: null,
    lastChecked: null,
  });

  const runHealthCheck = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));
    try {
      const { data, latencyMs } = await checkBackendHealth();
      setState({
        isLoading: false,
        isConnected: data?.status === 'ok',
        latencyMs,
        data,
        error: null,
        lastChecked: new Date(),
      });
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reach FastAPI backend';
      setState({
        isLoading: false,
        isConnected: false,
        latencyMs: null,
        data: null,
        error: errorMessage,
        lastChecked: new Date(),
      });
    }
  }, []);

  useEffect(() => {
    runHealthCheck();
  }, [runHealthCheck]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 overflow-hidden">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-semibold text-slate-900">
              Backend Connectivity Verification
            </h2>
            <span className="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
              GET /api/health
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Verifies the FastAPI backend server is operational, responding, and CORS/proxy routing is properly configured.
          </p>
        </div>

        <button
          onClick={runHealthCheck}
          disabled={state.isLoading}
          className="inline-flex items-center justify-center gap-2 px-3.5 py-2 text-xs font-medium text-slate-700 bg-slate-50 hover:bg-slate-100 active:bg-slate-200 border border-slate-300 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${state.isLoading ? 'animate-spin text-indigo-600' : ''}`} />
          {state.isLoading ? 'Pinging Backend...' : 'Ping /api/health'}
        </button>
      </div>

      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Status card */}
        <div className="p-4 rounded-xl border bg-slate-50/50 flex flex-col justify-between">
          <div className="text-xs font-medium text-slate-500 flex items-center justify-between">
            <span>SERVICE STATUS</span>
            <ShieldCheck className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-3 flex items-center gap-2.5">
            {state.isLoading ? (
              <>
                <Loader2 className="w-5 h-5 text-indigo-600 animate-spin" />
                <span className="text-sm font-semibold text-slate-700">Connecting...</span>
              </>
            ) : state.isConnected ? (
              <>
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <span className="text-sm font-bold text-emerald-700">ONLINE</span>
                  <span className="ml-2 text-xs font-mono text-emerald-600">status: ok</span>
                </div>
              </>
            ) : (
              <>
                <XCircle className="w-5 h-5 text-rose-600" />
                <span className="text-sm font-bold text-rose-700">UNREACHABLE</span>
              </>
            )}
          </div>
        </div>

        {/* Latency card */}
        <div className="p-4 rounded-xl border bg-slate-50/50 flex flex-col justify-between">
          <div className="text-xs font-medium text-slate-500 flex items-center justify-between">
            <span>ROUND-TRIP LATENCY</span>
            <Zap className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-3">
            {state.latencyMs !== null ? (
              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-bold font-mono text-slate-900">{state.latencyMs}</span>
                <span className="text-xs text-slate-500 font-mono">ms</span>
              </div>
            ) : (
              <span className="text-sm text-slate-400 font-mono">--</span>
            )}
          </div>
        </div>

        {/* Last check time card */}
        <div className="p-4 rounded-xl border bg-slate-50/50 flex flex-col justify-between">
          <div className="text-xs font-medium text-slate-500 flex items-center justify-between">
            <span>LAST VERIFIED</span>
            <Clock className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-3">
            {state.lastChecked ? (
              <span className="text-xs font-mono text-slate-700">
                {state.lastChecked.toLocaleTimeString()}
              </span>
            ) : (
              <span className="text-sm text-slate-400 font-mono">--</span>
            )}
          </div>
        </div>
      </div>

      {/* Response Payload or Error details */}
      <div className="mt-5">
        {state.isConnected && state.data && (
          <div className="p-4 rounded-xl bg-slate-900 text-slate-200 border border-slate-800 font-mono text-xs">
            <div className="flex items-center justify-between text-slate-400 pb-2 mb-2 border-b border-slate-800">
              <span className="font-semibold text-emerald-400">Response Payload (200 OK)</span>
              <span>application/json</span>
            </div>
            <pre className="overflow-x-auto text-emerald-300">
              {JSON.stringify(state.data, null, 2)}
            </pre>
          </div>
        )}

        {state.error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs">
            <div className="font-semibold mb-1 flex items-center gap-1.5 text-rose-900">
              <XCircle className="w-4 h-4" />
              Connection Error
            </div>
            <p className="font-mono">{state.error}</p>
            <p className="mt-2 text-rose-700">
              Ensure the FastAPI backend process is running:
              <code className="ml-1 px-1.5 py-0.5 bg-rose-100 text-rose-900 rounded font-mono">
                uvicorn backend.app.main:app --host 0.0.0.0 --port 8001
              </code>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
