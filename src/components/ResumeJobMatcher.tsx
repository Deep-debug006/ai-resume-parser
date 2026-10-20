/**
 * Phase 15: Resume-Job Matching Component
 * Deterministic, explainable comparison between structured Resume and Job Description.
 * Strictly informational: no hiring decisions or employment outcome claims.
 */
import React, { useState, useEffect } from 'react';
import {
  Scale,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Briefcase,
  GraduationCap,
  Clock,
  Award,
  Sparkles,
  Info,
  Copy,
  Check,
  RefreshCw,
  ChevronRight,
  Database,
  User,
} from 'lucide-react';
import { matchResumeToJob, listDBResumes } from '../services/api';
import { JobMatchResult } from '../types/matching';
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
- Design and build low-latency RESTful and gRPC APIs.
- Optimize complex database queries on PostgreSQL.

Minimum Requirements:
- 5+ years of software engineering experience building production systems.
- Strong proficiency in Python, FastAPI, and PostgreSQL.
- Experience with Docker and containerization.
- Bachelor's degree in Computer Science or related technical field.

Preferred Qualifications:
- Experience with Kubernetes and Redis caching.
- Familiarity with Terraform.

Certifications:
- AWS Certified Solutions Architect is a plus.`,
  },
  {
    title: 'Machine Learning Engineer',
    company: 'None (Implicit)',
    text: `Position: Machine Learning Engineer
Location: Remote

What You'll Do:
- Develop deep learning models and scalable inference pipelines.

Basic Qualifications:
- 3+ years of experience with Python, PyTorch, and SQL.
- Master's or Ph.D. in Computer Science or quantitative STEM field.

Nice to Have:
- Experience with Ray and MLflow.
- Kubernetes deployment experience.`,
  },
  {
    title: 'Lead Frontend Developer',
    company: 'Horizon Media Labs',
    text: `Job Title: Lead Frontend Developer
Company: Horizon Media Labs

Responsibilities:
- Lead the architecture of modern web apps with React and TypeScript.

Requirements:
- 5+ years of professional web development experience.
- Deep expertise in JavaScript, TypeScript, and React.
- Bachelor's degree in Computer Science or equivalent.

Preferred:
- Experience with Next.js and Tailwind CSS.`,
  },
];

const DEFAULT_RESUME_TEXT = `ALEX R. MERCER
alex.mercer@example.com | (415) 889-1020 | San Francisco, CA
LinkedIn: linkedin.com/in/alexmercer | GitHub: github.com/alexmercer

PROFESSIONAL SUMMARY
Senior Backend and Cloud Software Engineer with 7+ years of experience designing resilient distributed systems.

WORK EXPERIENCE
Nexus Infrastructure - Senior Software Engineer
San Francisco, CA | March 2021 - Present
- Architected asynchronous event pipeline using FastAPI, Python, and Redis.
- Maintained Docker and Kubernetes cluster deployments.

Acrobyte Technologies - Software Engineer
Austin, TX | June 2018 - February 2021
- Developed REST microservices using Python and PostgreSQL.
- Optimized database indexing reducing latency by 35%.

EDUCATION
University of Texas at Austin
Bachelor of Science in Computer Science | 2014 - 2018
GPA: 3.82 / 4.0

TECHNICAL SKILLS
Languages: Python, Go, TypeScript, SQL
Frameworks: FastAPI, React, Docker, Kubernetes, Redis, PostgreSQL
Tools: Git, Linux

CERTIFICATIONS
AWS Certified Solutions Architect`;

export const ResumeJobMatcher: React.FC = () => {
  const [dbResumes, setDbResumes] = useState<DBResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('text_mode');
  const [resumeText, setResumeText] = useState<string>(DEFAULT_RESUME_TEXT);
  const [jobText, setJobText] = useState<string>(SAMPLE_JOB_PRESETS[0].text);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [matchResult, setMatchResult] = useState<JobMatchResult | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    loadDatabaseResumes();
  }, []);

  const loadDatabaseResumes = async () => {
    try {
      const resumes = await listDBResumes();
      setDbResumes(resumes);
      if (resumes.length > 0) {
        setSelectedResumeId(resumes[0].id);
      }
    } catch {
      // Keep text mode if DB list fails
    }
  };

  const handleMatch = async () => {
    setLoading(true);
    setError(null);

    try {
      const payload: {
        resume_id?: string;
        resume_text?: string;
        job_text: string;
      } = {
        job_text: jobText,
      };

      if (selectedResumeId === 'text_mode') {
        if (!resumeText.trim()) {
          throw new Error('Please provide resume text to compare.');
        }
        payload.resume_text = resumeText;
      } else {
        payload.resume_id = selectedResumeId;
      }

      if (!jobText.trim()) {
        throw new Error('Please provide a job description to compare against.');
      }

      const res = await matchResumeToJob(payload);
      setMatchResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Comparison failed.');
      setMatchResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyJson = () => {
    if (!matchResult) return;
    navigator.clipboard.writeText(JSON.stringify(matchResult, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getAlignmentBadge = (alignment: string) => {
    switch (alignment) {
      case 'exceeds_requirements':
        return (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold border border-emerald-200">
            Exceeds Criteria
          </span>
        );
      case 'meets_requirements':
        return (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
            Meets Criteria
          </span>
        );
      case 'below_requirements':
        return (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 font-semibold border border-amber-200">
            Variance Noted
          </span>
        );
      default:
        return (
          <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold border border-slate-200">
            Not Specified
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-200 bg-slate-50/70 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-teal-50 border border-teal-100 text-teal-600">
            <Scale className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-900">Resume-Job Requirement Matching</h2>
              <span className="text-xs px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 font-semibold uppercase tracking-wider">
                Phase 15
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Deterministic skill and criteria comparison. Informational only — zero automated hiring decisions.
            </p>
          </div>
        </div>

        <button
          onClick={handleMatch}
          disabled={loading}
          className="text-xs font-semibold px-4 py-2 rounded-lg bg-teal-600 hover:bg-teal-700 text-white transition-colors flex items-center gap-2 disabled:opacity-50 shadow-sm"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Comparing Requirements...
            </>
          ) : (
            <>
              <Scale className="w-4 h-4" />
              Compare Requirements
            </>
          )}
        </button>
      </div>

      <div className="p-6 space-y-6">
        {/* Informational Non-Evaluative Notice */}
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-600 text-xs flex items-start gap-2.5">
          <Info className="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" />
          <div>
            <strong className="text-slate-800">Informational Skill & Criteria Comparison Only:</strong> This feature
            provides an objective, explainable mapping between parsed resume evidence and job description criteria.
            It strictly does not make hiring recommendations, predict interview invitations, or replace human review.
          </div>
        </div>

        {/* Input Configuration Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Candidate Resume Source */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <User className="w-4 h-4 text-teal-600" />
                Candidate Resume Evidence
              </label>

              {dbResumes.length > 0 && (
                <div className="flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-slate-400" />
                  <select
                    value={selectedResumeId}
                    onChange={(e) => setSelectedResumeId(e.target.value)}
                    className="text-xs py-1 px-2 border border-slate-200 rounded-md bg-white text-slate-700 focus:outline-none"
                  >
                    {dbResumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.candidate_name || r.original_filename} (DB)
                      </option>
                    ))}
                    <option value="text_mode">Custom Text Input</option>
                  </select>
                </div>
              )}
            </div>

            {selectedResumeId === 'text_mode' ? (
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                rows={7}
                placeholder="Paste candidate resume text..."
                className="w-full text-xs font-mono p-3 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-teal-500/20 focus:border-teal-500 text-slate-800 bg-slate-50/50"
              />
            ) : (
              <div className="p-4 rounded-lg border border-slate-200 bg-slate-50/70 text-xs text-slate-600 space-y-1">
                <p className="font-semibold text-slate-800">
                  Using Database Profile:{' '}
                  {dbResumes.find((r) => r.id === selectedResumeId)?.candidate_name || selectedResumeId}
                </p>
                <p className="text-slate-500">
                  Filename: {dbResumes.find((r) => r.id === selectedResumeId)?.original_filename}
                </p>
                <p className="text-slate-500">
                  Status: {dbResumes.find((r) => r.id === selectedResumeId)?.processing_status}
                </p>
              </div>
            )}
          </div>

          {/* Job Description Target */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                <Briefcase className="w-4 h-4 text-indigo-600" />
                Target Job Description
              </label>

              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-400">Presets:</span>
                {SAMPLE_JOB_PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => setJobText(p.text)}
                    className="text-xs px-2 py-0.5 rounded bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 font-medium"
                  >
                    {p.title.split(' ')[0]}
                  </button>
                ))}
              </div>
            </div>

            <textarea
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
              rows={7}
              placeholder="Paste target job requirements..."
              className="w-full text-xs font-mono p-3 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 bg-slate-50/50"
            />
          </div>
        </div>

        {/* Error notification */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-2.5 text-xs">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-500 mt-0.5" />
            <div>
              <p className="font-semibold">Matching Comparison Failed</p>
              <p className="mt-0.5 text-red-600">{error}</p>
            </div>
          </div>
        )}

        {/* Match Results Display */}
        {matchResult && (
          <div className="space-y-6 pt-4 border-t border-slate-200">
            {/* Top Metrics Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Required Skills Match */}
              <div className="p-4 rounded-xl border border-emerald-100 bg-emerald-50/40 space-y-1">
                <div className="flex items-center justify-between text-xs text-emerald-800 font-semibold">
                  <span>Required Skills</span>
                  <span>{Math.round(matchResult.required_skills_match_rate * 100)}%</span>
                </div>
                <div className="text-2xl font-bold text-emerald-900">
                  {matchResult.matched_skills.length} /{' '}
                  {matchResult.matched_skills.length + matchResult.missing_required_skills.length}
                </div>
                <p className="text-2xs text-emerald-700">Essential baseline skills detected</p>
              </div>

              {/* Preferred Skills Match */}
              <div className="p-4 rounded-xl border border-blue-100 bg-blue-50/40 space-y-1">
                <div className="flex items-center justify-between text-xs text-blue-800 font-semibold">
                  <span>Preferred Skills</span>
                  <span>{Math.round(matchResult.preferred_skills_match_rate * 100)}%</span>
                </div>
                <div className="text-2xl font-bold text-blue-900">
                  {matchResult.matched_preferred_skills.length} /{' '}
                  {matchResult.matched_preferred_skills.length + matchResult.missing_preferred_skills.length}
                </div>
                <p className="text-2xs text-blue-700">Secondary / nice-to-have skills</p>
              </div>

              {/* Experience Alignment */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-1">
                <div className="text-xs text-slate-600 font-semibold">Experience Criteria</div>
                <div className="pt-0.5">{getAlignmentBadge(matchResult.experience_alignment)}</div>
                <p className="text-2xs text-slate-500 pt-1">
                  Candidate: ~{matchResult.candidate_years_experience ?? 'N/A'} yrs | Stated:{' '}
                  {matchResult.required_years_experience ? `${matchResult.required_years_experience}+ yrs` : 'Unstated'}
                </p>
              </div>

              {/* Education Alignment */}
              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-1">
                <div className="text-xs text-slate-600 font-semibold">Education Criteria</div>
                <div className="pt-0.5">{getAlignmentBadge(matchResult.education_alignment)}</div>
                <p className="text-2xs text-slate-500 pt-1">Academic degree criteria alignment</p>
              </div>
            </div>

            {/* Detailed Skills Comparison Columns */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Matched Required Skills */}
              <div className="p-4 rounded-xl border border-emerald-200 bg-white space-y-3">
                <div className="flex items-center justify-between border-b border-emerald-100 pb-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Matched Required Skills
                  </h4>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200">
                    {matchResult.matched_skills.length}
                  </span>
                </div>
                {matchResult.matched_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {matchResult.matched_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium flex items-center gap-1"
                      >
                        <Check className="w-3 h-3 text-emerald-600" />
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No required skills matched.</p>
                )}
              </div>

              {/* Missing Required Skills */}
              <div className="p-4 rounded-xl border border-amber-200 bg-white space-y-3">
                <div className="flex items-center justify-between border-b border-amber-100 pb-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <XCircle className="w-4 h-4 text-amber-600" />
                    Missing Required Skills
                  </h4>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 font-semibold border border-amber-200">
                    {matchResult.missing_required_skills.length}
                  </span>
                </div>
                {matchResult.missing_required_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {matchResult.missing_required_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-emerald-700 font-medium">All stated required skills matched!</p>
                )}
              </div>
            </div>

            {/* Preferred Skills Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Matched Preferred */}
              <div className="p-4 rounded-xl border border-blue-200 bg-white space-y-2.5">
                <div className="flex items-center justify-between border-b border-blue-100 pb-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-blue-500" />
                    Matched Preferred Skills
                  </h4>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                    {matchResult.matched_preferred_skills.length}
                  </span>
                </div>
                {matchResult.matched_preferred_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {matchResult.matched_preferred_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2.5 py-1 rounded-md bg-blue-50 text-blue-800 border border-blue-200 font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">None matched.</p>
                )}
              </div>

              {/* Missing Preferred */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2.5">
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Briefcase className="w-4 h-4 text-slate-400" />
                    Unmatched Preferred Skills
                  </h4>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold border border-slate-200">
                    {matchResult.missing_preferred_skills.length}
                  </span>
                </div>
                {matchResult.missing_preferred_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {matchResult.missing_preferred_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2.5 py-1 rounded-md bg-slate-50 text-slate-700 border border-slate-200 font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">None unmatched.</p>
                )}
              </div>
            </div>

            {/* Explainable Analyses (Experience & Education) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Experience Analysis */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-blue-500" />
                    Experience Analysis
                  </h4>
                  {getAlignmentBadge(matchResult.experience_alignment)}
                </div>
                <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                  {matchResult.experience_analysis}
                </p>
              </div>

              {/* Education Analysis */}
              <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <GraduationCap className="w-4 h-4 text-purple-500" />
                    Education Analysis
                  </h4>
                  {getAlignmentBadge(matchResult.education_alignment)}
                </div>
                <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-100">
                  {matchResult.education_analysis}
                </p>
              </div>
            </div>

            {/* Certifications Comparison */}
            {(matchResult.matched_certifications.length > 0 || matchResult.missing_certifications.length > 0) && (
              <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-amber-500" />
                  Certifications Comparison
                </h4>
                <div className="flex flex-wrap gap-2 text-xs">
                  {matchResult.matched_certifications.map((c, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium flex items-center gap-1"
                    >
                      <Check className="w-3 h-3 text-emerald-600" />
                      {c} (Held)
                    </span>
                  ))}
                  {matchResult.missing_certifications.map((c, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200 font-medium"
                    >
                      {c} (Not on resume)
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Actions Bar & Disclaimer */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2 text-xs text-slate-500 border-t border-slate-100">
              <p className="italic">
                {matchResult.disclaimer}
              </p>
              <button
                onClick={handleCopyJson}
                className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 flex items-center gap-1.5 flex-shrink-0 transition-colors font-medium shadow-2xs"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Export JSON Report'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
