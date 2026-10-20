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
    status: 'completed',
  },
  {
    id: 9,
    title: 'Phase 9: AI Structured Resume Parsing',
    desc: 'LLM provider abstraction (Gemini, OpenAI, Mock), prompt grounding, Pydantic validation, and controlled schema repair loop',
    status: 'completed',
  },
  {
    id: 10,
    title: 'Phase 10: Skill Normalization & Taxonomy',
    desc: 'Deterministic alias mapping (data/skill_aliases.json), deduplication, collision guards, and unknown skill preservation',
    status: 'completed',
  },
  {
    id: 11,
    title: 'Phase 11: PostgreSQL Database Persistence',
    desc: 'Normalized relational schema (SQLAlchemy & Alembic) for users, resumes, personal info, education, skills, experience, projects, certs, and achievements',
    status: 'completed',
  },
  {
    id: 12,
    title: 'Phase 12: Complete Resume Processing Pipeline',
    desc: 'End-to-end orchestration connecting PDF upload, OCR fallback, cleaning, section detection, NLP, LLM extraction, Pydantic validation, skill normalization, and PostgreSQL persistence with status tracking',
    status: 'completed',
  },
  {
    id: 13,
    title: 'Phase 13: Resume Dashboard',
    desc: 'Visual display of personal info, summary, education, skills, experience, projects, certifications, and achievements with responsive, accessible components',
    status: 'completed',
  },
  {
    id: 14,
    title: 'Phase 14: Job Description Parsing',
    desc: 'Extract structured job title, company, required & preferred skills, education, experience, responsibilities, tools, and certifications with skill normalization reuse and anti-hallucination',
    status: 'completed',
  },
  {
    id: 15,
    title: 'Phase 15: Resume-Job Matching',
    desc: 'Deterministic, explainable comparison of candidate background against job requirements: matched skills, missing required/preferred skills, experience alignment, education alignment, and non-evaluative reporting',
    status: 'completed',
  },
  {
    id: 16,
    title: 'Phase 16: Semantic Similarity Using Embeddings',
    desc: 'Dense 768d vector embeddings (text-embedding-004) stored in PostgreSQL + pgvector, cosine distance (<=>) search, content-hash caching, and strict separation between exact skill matching and semantic similarity',
    status: 'completed',
  },
  {
    id: 17,
    title: 'Phase 17: AI Resume Quality Analysis',
    desc: 'Comprehensive resume evaluation across clarity, completeness, bullet-point quality, measurable achievements, skill organization, and formatting with strict anti-hallucination and factual isolation',
    status: 'completed',
  },
  {
    id: 18,
    title: 'Phase 18: Authentication & Ownership',
    desc: 'JWT-based authentication, bcrypt password hashing, POST /api/auth/register, POST /api/auth/login, GET /api/auth/me, and strict multi-user resume and job ownership isolation',
    status: 'completed',
  },
  {
    id: 19,
    title: 'Phase 19: Job Matching UI',
    desc: 'Interactive dashboard for candidate resume selection, pasting job descriptions, structured requirements parsing, matched skills, missing skills, semantic similarity, and comparative analysis',
    status: 'completed',
  },
  {
    id: 20,
    title: 'Phase 20: User History & Archive',
    desc: 'Browse previously uploaded resumes, processing statuses, saved job descriptions, and comparative analysis history with search, status/type filters, sorting, pagination, and deletion',
    status: 'completed',
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
        <span className="text-xs font-medium px-2.5 py-1 bg-teal-50 text-teal-800 border border-teal-200 rounded-lg">
          Current: Phase 20 Active
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
