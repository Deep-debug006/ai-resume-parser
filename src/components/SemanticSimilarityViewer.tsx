/**
 * Phase 16: Semantic Similarity Using Embeddings Component
 * Dense vector embeddings (768d, text-embedding-004) stored in PostgreSQL with pgvector.
 * Clearly distinguishes exact skill matches from dense semantic similarity.
 * Informational only - zero hiring probabilities or automated decision claims.
 */
import React, { useState, useEffect } from 'react';
import {
  BrainCircuit,
  Binary,
  Layers,
  Sparkles,
  Info,
  CheckCircle2,
  XCircle,
  Database,
  ArrowRight,
  TrendingUp,
  FileText,
  User,
  ShieldCheck,
  RefreshCw,
  Copy,
  Check,
  Zap,
} from 'lucide-react';
import { computeSemanticMatch, listDBResumes } from '../services/api';
import { SemanticMatchResult } from '../types/semantic';
import { DBResumeSummary } from '../types/database';

const SAMPLE_JOB_PRESETS = [
  {
    title: 'Senior Cloud Backend Engineer',
    company: 'Apex Cloud Systems',
    text: `Job Title: Senior Backend Engineer
Company: Apex Cloud Systems
Location: San Francisco, CA (Hybrid)
Employment Type: Full-time

Key Responsibilities:
- Design and build low-latency RESTful and gRPC APIs with Python and FastAPI.
- Optimize complex database queries and transactional consistency on PostgreSQL.
- Maintain Docker container orchestration and distributed caching.

Requirements:
- 5+ years of software engineering experience building production systems.
- Strong proficiency in Python, FastAPI, and PostgreSQL.
- Experience with Docker and containerization.
- Experience with Apache Kafka or message queues.

Preferred Qualifications:
- Experience with Kubernetes and Redis caching.
- Bachelor's degree in Computer Science or related field.`,
  },
  {
    title: 'Machine Learning Engineer',
    company: 'Nexus AI Labs',
    text: `Job Title: Machine Learning Engineer
Company: Nexus AI Labs
Location: Remote

Responsibilities:
- Build scalable model training and evaluation pipelines.
- Deploy deep neural networks to low-latency production endpoints.

Requirements:
- 3+ years experience with Python, PyTorch, and vector databases.
- Strong mathematical background in linear algebra and embeddings.
- Experience with distributed computing and cloud APIs.`,
  },
];

export const SemanticSimilarityViewer: React.FC = () => {
  const [dbResumes, setDbResumes] = useState<DBResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [resumeText, setResumeText] = useState<string>(
    `Morgan Vance\nSenior Backend Software Engineer\nEmail: morgan.vance@example.com\n\nSummary:\nSenior Backend Software Engineer with 6+ years building distributed Python microservices, PostgreSQL architectures, and cloud APIs.\n\nExperience:\nSenior Backend Engineer at Nexus Infrastructure (2021 - Present)\n- Engineered low-latency REST endpoints handling 10k req/sec with FastAPI and async PostgreSQL\n- Maintained Docker container orchestration and Redis cache clusters\n- Integrated Apache Kafka event messaging pipeline for high-throughput metrics\n\nSkills:\nPython, FastAPI, PostgreSQL, Redis, Docker, Git, Linux`
  );
  const [jobText, setJobText] = useState<string>(SAMPLE_JOB_PRESETS[0].text);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SemanticMatchResult | null>(null);
  const [copiedJson, setCopiedJson] = useState<boolean>(false);

  useEffect(() => {
    loadDatabaseResumes();
  }, []);

  const loadDatabaseResumes = async () => {
    try {
      const data = await listDBResumes();
      setDbResumes(data);
      if (data.length > 0 && !selectedResumeId) {
        setSelectedResumeId(data[0].id);
      }
    } catch {
      // Non-blocking if DB empty
    }
  };

  const handleComputeSemanticMatch = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: any = {};
      if (selectedResumeId && selectedResumeId !== 'custom') {
        payload.resume_id = selectedResumeId;
      } else {
        payload.resume_text = resumeText;
      }
      payload.job_text = jobText;

      const data = await computeSemanticMatch(payload);
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to compute semantic match.');
    } finally {
      setLoading(false);
    }
  };

  const copyJsonToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'strong_alignment':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
            Strong Alignment (≥0.75)
          </span>
        );
      case 'moderate_alignment':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300">
            Moderate Alignment (≥0.55)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300">
            Minimal Alignment (&lt;0.55)
          </span>
        );
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-violet-100 text-violet-800 dark:bg-violet-900/50 dark:text-violet-300 border border-violet-200 dark:border-violet-700">
              Phase 16
            </span>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <BrainCircuit className="h-6 w-6 text-violet-600 dark:text-violet-400" />
              Semantic Similarity Using Dense Embeddings
            </h2>
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
            Beyond keyword matching: Generates 768-dimensional embeddings via Google{' '}
            <code className="text-xs bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded font-mono text-violet-600 dark:text-violet-400">text-embedding-004</code>{' '}
            stored in PostgreSQL + <span className="font-semibold text-slate-700 dark:text-slate-300">pgvector</span> with cosine distance (<code className="text-xs">&lt;=&gt;</code>) search.
          </p>
        </div>

        {/* Clear Distinction Pill */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
          <Binary className="h-4 w-4 text-violet-500" />
          <span>Strict Separation: Exact Skill Match vs. Dense Similarity</span>
        </div>
      </div>

      {/* Prominent Ethical AI Disclaimer */}
      <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 rounded-lg p-4 flex items-start gap-3 text-amber-900 dark:text-amber-200 text-sm">
        <ShieldCheck className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-xs uppercase tracking-wider text-amber-800 dark:text-amber-300">
            Ethical AI & Non-Evaluative Principle Notice
          </p>
          <p className="text-xs leading-relaxed">
            Semantic similarity is an informational metric reflecting mathematical proximity between text embeddings (vector cosine similarity). It does <strong>NOT</strong> represent candidate qualification, interview readiness, or hiring probability, and must never be interpreted as an automated employment decision.
          </p>
        </div>
      </div>

      {/* Input Selection Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Candidate Resume Source */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <User className="h-4 w-4 text-violet-500" />
              Candidate Resume Source
            </label>
            {dbResumes.length > 0 && (
              <span className="text-xs text-slate-500">
                {dbResumes.length} saved in PostgreSQL
              </span>
            )}
          </div>

          <div className="flex gap-2">
            <select
              value={selectedResumeId}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              className="flex-1 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 text-sm focus:ring-2 focus:ring-violet-500"
            >
              <option value="custom">-- Custom Resume Text --</option>
              {dbResumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.candidate_name || 'Anonymous'} ({r.original_filename})
                </option>
              ))}
            </select>
          </div>

          {(selectedResumeId === 'custom' || !selectedResumeId) && (
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              rows={8}
              placeholder="Paste candidate resume text here..."
              className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3 text-xs font-mono text-slate-900 dark:text-slate-200 focus:ring-2 focus:ring-violet-500"
            />
          )}

          {selectedResumeId && selectedResumeId !== 'custom' && (
            <div className="p-3 bg-violet-50/50 dark:bg-violet-950/20 border border-violet-200 dark:border-violet-900/40 rounded-lg text-xs space-y-1">
              <p className="font-semibold text-violet-900 dark:text-violet-300 flex items-center gap-1.5">
                <Database className="h-3.5 w-3.5" />
                PostgreSQL Database Resume Selected:
              </p>
              <p className="text-slate-600 dark:text-slate-400">
                ID: <code className="font-mono">{selectedResumeId}</code>
              </p>
              <p className="text-slate-500 text-[11px]">
                Pre-parsed structured resume will be loaded directly from database and vectorized with content-hash caching.
              </p>
            </div>
          )}
        </div>

        {/* Right: Job Description Source */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2">
              <FileText className="h-4 w-4 text-violet-500" />
              Target Job Description
            </label>
            <div className="flex gap-1.5">
              {SAMPLE_JOB_PRESETS.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setJobText(preset.text)}
                  className="text-[11px] px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-colors"
                >
                  Preset {idx + 1}
                </button>
              ))}
            </div>
          </div>

          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            rows={8}
            placeholder="Paste job description requirements and responsibilities here..."
            className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-3 text-xs font-mono text-slate-900 dark:text-slate-200 focus:ring-2 focus:ring-violet-500"
          />
        </div>
      </div>

      {/* Action Button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Zap className="h-4 w-4 text-violet-500" />
          <span>
            Storage: <code className="font-mono">vector_embeddings</code> table with SHA-256 deduplication
          </span>
        </div>

        <button
          onClick={handleComputeSemanticMatch}
          disabled={loading}
          className="w-full sm:w-auto px-6 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white font-medium text-sm rounded-lg shadow-sm flex items-center justify-center gap-2 transition-all cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Generating Embeddings & Computing Similarities...</span>
            </>
          ) : (
            <>
              <BrainCircuit className="h-4 w-4" />
              <span>Compute Semantic Similarity (Phase 16)</span>
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-lg text-sm text-red-800 dark:text-red-300 flex items-center gap-2">
          <XCircle className="h-4 w-4 shrink-0 text-red-600 dark:text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="mt-8 pt-6 border-t border-slate-200 dark:border-slate-800 space-y-6">
          {/* Top Metric Overview Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Metric 1: Overall Semantic Similarity */}
            <div className="p-4 bg-violet-50 dark:bg-violet-950/20 border border-violet-200 dark:border-violet-900/50 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-violet-700 dark:text-violet-300">
                  Overall Semantic Similarity
                </span>
                <BrainCircuit className="h-4 w-4 text-violet-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-violet-950 dark:text-violet-100">
                  {(result.overall_semantic_similarity * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  (score: {result.overall_semantic_similarity.toFixed(4)})
                </span>
              </div>
              <div className="w-full bg-violet-200 dark:bg-violet-900/50 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-violet-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, result.overall_semantic_similarity * 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500">
                Dense cosine similarity between aggregated profile and job overview.
              </p>
            </div>

            {/* Metric 2: Experience Semantic Alignment */}
            <div className="p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900/50 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-blue-700 dark:text-blue-300">
                  Experience Alignment
                </span>
                <TrendingUp className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-3xl font-extrabold text-blue-950 dark:text-blue-100">
                  {(result.experience_semantic_alignment * 100).toFixed(1)}%
                </span>
                <span className="text-xs text-slate-500 font-mono">
                  (score: {result.experience_semantic_alignment.toFixed(4)})
                </span>
              </div>
              <div className="w-full bg-blue-200 dark:bg-blue-900/50 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, result.experience_semantic_alignment * 100)}%` }}
                />
              </div>
              <p className="text-[11px] text-slate-500">
                Average semantic similarity across individual requirement items.
              </p>
            </div>

            {/* Metric 3: Model & Vector Specs */}
            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                  Vector Engine Specs
                </span>
                <Database className="h-4 w-4 text-slate-500" />
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Model:</span>
                  <span className="font-mono font-medium text-slate-900 dark:text-white">
                    {result.model_name}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Dimensions:</span>
                  <span className="font-mono font-medium text-slate-900 dark:text-white">
                    {result.vector_dimension}d (normalized)
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Storage:</span>
                  <span className="font-mono font-medium text-slate-900 dark:text-white">
                    PostgreSQL 15 + pgvector
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Index:</span>
                  <span className="font-mono font-medium text-slate-900 dark:text-white">
                    HNSW (vector_cosine_ops)
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* CRITICAL: Side-by-Side Separation of Exact Match vs. Semantic Similarity */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Box A: Exact Keyword Match (Phase 15) */}
            <div className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/40 dark:bg-emerald-950/20 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    1. Exact Skill Match (Phase 15)
                  </h3>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
                  {Math.round(result.exact_skills_match_rate * 100)}% Rate
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Deterministic canonical verification based on explicit keyword presence in the candidate resume.
              </p>

              <div>
                <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Confirmed Skills ({result.exact_matched_skills.length}):
                </span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {result.exact_matched_skills.length > 0 ? (
                    result.exact_matched_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300 font-medium"
                      >
                        <Check className="h-3 w-3" />
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400 italic">None detected</span>
                  )}
                </div>
              </div>

              {result.missing_required_skills.length > 0 && (
                <div>
                  <span className="text-xs font-semibold text-amber-700 dark:text-amber-400">
                    Unmatched Required Skills ({result.missing_required_skills.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {result.missing_required_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300 font-medium"
                      >
                        <XCircle className="h-3 w-3 text-amber-600" />
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Box B: Semantic Similarity (Phase 16) */}
            <div className="p-4 rounded-xl border border-violet-200 dark:border-violet-900/50 bg-violet-50/40 dark:bg-violet-950/20 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <BrainCircuit className="h-4 w-4 text-violet-600 dark:text-violet-400" />
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    2. Dense Semantic Similarity (Phase 16)
                  </h3>
                </div>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-violet-100 text-violet-800 dark:bg-violet-900/50 dark:text-violet-300">
                  {(result.overall_semantic_similarity * 100).toFixed(1)}% Similarity
                </span>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Dense vector comparison capturing contextual phrasing, adjacent technologies, and descriptive overlap.
              </p>

              <div className="space-y-2 text-xs">
                <div className="flex justify-between items-center py-1 border-b border-violet-100 dark:border-violet-900/30">
                  <span className="text-slate-600 dark:text-slate-400">Summary Similarity:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {result.summary_similarity !== null
                      ? `${(result.summary_similarity * 100).toFixed(1)}%`
                      : 'N/A (No summary)'}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1 border-b border-violet-100 dark:border-violet-900/30">
                  <span className="text-slate-600 dark:text-slate-400">Experience Alignment:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {(result.experience_semantic_alignment * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-600 dark:text-slate-400">Requirements Analyzed:</span>
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {result.requirement_matches.length} items
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Explainable Insights Narrative */}
          <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-xl border border-slate-200 dark:border-slate-700 space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Sparkles className="h-4 w-4 text-violet-500" />
              Explainable Semantic Analysis
            </h4>
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
              {result.semantic_insights}
            </p>
          </div>

          {/* Requirement-by-Requirement Semantic Breakdown Table */}
          {result.requirement_matches.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                  <Layers className="h-4 w-4 text-violet-500" />
                  Requirement-to-Experience Semantic Alignment ({result.requirement_matches.length})
                </h4>
                <span className="text-xs text-slate-500">
                  Ranked by closest cosine proximity
                </span>
              </div>

              <div className="space-y-3">
                {result.requirement_matches.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-xs space-y-2.5"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                          #{idx + 1}
                        </span>
                        <span className="text-xs font-bold text-slate-900 dark:text-white">
                          {item.requirement}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 self-start sm:self-auto">
                        {getTierBadge(item.relevance_tier)}
                        <span className="text-xs font-mono font-bold text-violet-600 dark:text-violet-400">
                          {(item.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    <div className="p-2.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between text-[11px] text-slate-500">
                        <span className="font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                          Best Matching Resume Evidence ({item.source_type}):
                        </span>
                      </div>
                      <p className="text-slate-800 dark:text-slate-200 font-mono whitespace-pre-wrap leading-relaxed text-[11px]">
                        {item.best_matching_resume_chunk}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Row: Copy JSON */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={copyJsonToClipboard}
              className="px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-xs font-medium text-slate-700 dark:text-slate-300 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {copiedJson ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-500" />
                  <span>Copied JSON!</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Export JSON Result</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
