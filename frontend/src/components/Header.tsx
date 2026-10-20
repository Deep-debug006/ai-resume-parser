import React from 'react';
import { FileText, Cpu, Terminal } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="border-b border-slate-200 bg-white shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-600 text-white rounded-xl shadow-sm flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                  AI Resume Parser &amp; Job Matcher
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-cyan-50 text-cyan-700 border border-cyan-200 rounded-full">
                  Phase 8 spaCy NLP
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                FastAPI + React TypeScript + Pydantic Architecture
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-600 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 font-mono">
            <Cpu className="w-3.5 h-3.5 text-slate-500" />
            <span>FastAPI: 8001</span>
            <span className="text-slate-300">|</span>
            <Terminal className="w-3.5 h-3.5 text-slate-500" />
            <span>Vite: 3000</span>
          </div>
        </div>
      </div>
    </header>
  );
};
