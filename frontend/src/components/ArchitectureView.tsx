import React from 'react';
import { FolderTree, Server, Layers, Code2 } from 'lucide-react';

export const ArchitectureView: React.FC = () => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
      <div className="flex items-center gap-2 pb-4 border-b border-slate-100">
        <FolderTree className="w-5 h-5 text-indigo-600" />
        <div>
          <h2 className="text-base font-semibold text-slate-900">
            Monorepo Architecture (ai-resume-parser)
          </h2>
          <p className="text-xs text-slate-500">
            Clean separation of concerns with modular Python FastAPI backend and React frontend.
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Backend Box */}
        <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
          <div className="flex items-center gap-2 mb-3 text-slate-900 font-semibold text-sm">
            <Server className="w-4 h-4 text-emerald-600" />
            <span>backend/ (FastAPI + Pydantic)</span>
          </div>
          <pre className="text-xs font-mono text-slate-600 space-y-1 bg-white p-3 rounded-lg border border-slate-200 overflow-x-auto">
{`backend/
├── app/
│   ├── main.py            # FastAPI entry & CORS
│   ├── core/config.py     # Pydantic Settings
│   ├── routes/health.py   # GET /api/health
│   ├── schemas/health.py  # HealthResponse schema
│   ├── services/          # Business logic
│   ├── models/            # Domain entities
│   ├── repositories/      # Data access layer
│   └── utils/             # Helper utilities
├── tests/
│   └── test_health.py     # pytest suite
├── requirements.txt       # Dependencies
└── .env.example           # Config template`}
          </pre>
        </div>

        {/* Frontend Box */}
        <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/50">
          <div className="flex items-center gap-2 mb-3 text-slate-900 font-semibold text-sm">
            <Layers className="w-4 h-4 text-indigo-600" />
            <span>frontend/ (React + TypeScript + Tailwind)</span>
          </div>
          <pre className="text-xs font-mono text-slate-600 space-y-1 bg-white p-3 rounded-lg border border-slate-200 overflow-x-auto">
{`frontend/ (and root src/)
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── Header.tsx
│   │   ├── HealthStatus.tsx
│   │   └── PhaseTracker.tsx
│   ├── services/
│   │   └── api.ts         # Backend API client
│   ├── types/
│   │   └── health.ts      # TypeScript interfaces
│   ├── App.tsx            # Main application view
│   ├── index.css          # Tailwind CSS v4
│   └── main.tsx           # React 19 root
├── vite.config.ts         # Proxy /api -> :8000
└── .env.example           # Client env config`}
          </pre>
        </div>
      </div>
    </div>
  );
};
