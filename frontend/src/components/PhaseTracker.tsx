import React from 'react';
import { CheckCircle2, Lock, ArrowRight, FolderTree } from 'lucide-react';

const PHASES = [
  {
    id: 1,
    title: 'Phase 1: Project Foundation',
    desc: 'Monorepo setup, FastAPI backend, React frontend, CORS, health endpoint verification',
    status: 'completed',
  },
  {
    id: 2,
    title: 'Phase 2: Resume Upload',
    desc: 'Secure PDF upload, extension, MIME, magic signature validation, safe temporary isolation',
    status: 'completed',
  },
  {
    id: 3,
    title: 'Phase 3: PDF Text Extraction',
    desc: 'PyMuPDF extraction pipeline, multi-page parsing, and useful line-break preservation',
    status: 'completed',
  },
  {
    id: 4,
    title: 'Phase 4: OCR Fallback for Scanned Resumes',
    desc: 'Tesseract OCR engine integration, page-level density thresholding, and mixed PDF handling',
    status: 'completed',
  },
  {
    id: 5,
    title: 'Phase 5: Resume Text Preprocessing',
    desc: 'Deterministic pipeline, whitespace collapsing, Unicode normalization, bullet standardization, artifact removal',
    status: 'completed',
  },
  {
    id: 6,
    title: 'Phase 6: Section Segmentation',
    desc: 'Structural heading and boundary detection for resume components, mapping variations to canonical sections',
    status: 'completed',
  },
  {
    id: 7,
    title: 'Phase 7: Structured Resume Schema',
    desc: 'Strict Pydantic domain models for PersonalInfo, Education, SkillSet, Experience, Project, Certification, Achievement, and Resume',
    status: 'completed',
  },
  {
    id: 8,
    title: 'Phase 8: NLP Preprocessing with spaCy',
    desc: 'Deterministic entity extraction for PERSON, ORG, GPE, DATE, EMAIL, and URL as supporting evidence',
    status: 'active',
  },
  {
    id: 9,
    title: 'Phase 9: Structured Information Extraction',
    desc: 'Extracting structured entities into Pydantic models from segmented sections and NLP anchors',
    status: 'pending',
  },
  {
    id: 10,
    title: 'Phase 10: Skill Normalization & Taxonomy',
    desc: 'Standardizing skill nomenclature and canonical representations',
    status: 'pending',
  },
  {
    id: 11,
    title: 'Phase 11: Job Description Matching & Semantic Fit',
    desc: 'Requirement parsing, matched/missing skills matrix, semantic scoring',
    status: 'pending',
  },
];

export const PhaseTracker: React.FC = () => {
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div>
          <h2 className="text-base font-semibold text-slate-900">
            Incremental Development Roadmap
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Strict phased progression. Subsequent phases remain untouched until explicitly requested.
          </p>
        </div>
        <span className="text-xs font-medium px-2.5 py-1 bg-cyan-50 text-cyan-700 border border-cyan-200 rounded-lg">
          Current: Phase 8 Active
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {PHASES.map((phase) => {
          const isActive = phase.status === 'active';
          const isCompleted = phase.status === 'completed';
          return (
            <div
              key={phase.id}
              className={`p-3.5 rounded-xl border transition-all flex items-start justify-between gap-3 ${
                isActive
                  ? 'bg-indigo-50/60 border-indigo-300 ring-1 ring-indigo-300'
                  : isCompleted
                  ? 'bg-emerald-50/40 border-emerald-200'
                  : 'bg-slate-50/50 border-slate-200 opacity-60'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className="mt-0.5">
                  {isCompleted ? (
                    <div className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs shadow-xs">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                  ) : isActive ? (
                    <div className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-xs font-bold shadow-xs">
                      {phase.id}
                    </div>
                  ) : (
                    <div className="w-5 h-5 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center text-xs">
                      <Lock className="w-3 h-3" />
                    </div>
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-semibold ${
                        isActive ? 'text-blue-950' : isCompleted ? 'text-emerald-950' : 'text-slate-600'
                      }`}
                    >
                      {phase.title}
                    </span>
                    {isCompleted && (
                      <span className="px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase bg-emerald-100 text-emerald-800 rounded">
                        COMPLETED
                      </span>
                    )}
                    {isActive && (
                      <span className="px-2 py-0.5 text-[10px] font-bold tracking-wide uppercase bg-blue-100 text-blue-800 rounded animate-pulse">
                        CURRENT PHASE
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{phase.desc}</p>
                </div>
              </div>

              {isActive ? (
                <ArrowRight className="w-4 h-4 text-blue-600 shrink-0 mt-1" />
              ) : isCompleted ? (
                <span className="text-[11px] text-emerald-600 font-semibold shrink-0 mt-1">Verified</span>
              ) : (
                <span className="text-[11px] text-slate-400 font-medium shrink-0 mt-1">Locked</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
