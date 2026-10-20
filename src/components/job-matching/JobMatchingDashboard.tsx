import React, { useState, useEffect } from 'react';
import {
  Briefcase,
  FileText,
  User,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Scale,
  RefreshCw,
  Layers,
  ChevronRight,
  Database,
  ArrowRight,
} from 'lucide-react';
import { JobInput, SAMPLE_JOB_PRESETS } from './JobInput';
import { JobRequirements } from './JobRequirements';
import { MatchedSkills } from './MatchedSkills';
import { MissingSkills } from './MissingSkills';
import { SimilarityAnalysis } from './SimilarityAnalysis';
import { ResumeJobComparison } from './ResumeJobComparison';

import {
  listDBResumes,
  getDBResume,
  parseJobDescription,
  matchResumeToJob,
  computeSemanticMatch,
} from '../../services/api';
import { DBResumeSummary, DBResumeDetail } from '../../types/database';
import { JobDescription } from '../../types/job';
import { JobMatchResult } from '../../types/matching';
import { SemanticMatchResult } from '../../types/semantic';
import { Resume } from '../../types/resume';

interface JobMatchingDashboardProps {
  currentResume?: Resume | null;
  currentResumeId?: string | null;
}

type TabType = 'comparison' | 'matched' | 'missing' | 'requirements' | 'semantic';

export const JobMatchingDashboard: React.FC<JobMatchingDashboardProps> = ({
  currentResume,
  currentResumeId,
}) => {
  // State for resume selection
  const [dbResumes, setDbResumes] = useState<DBResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string>('');
  const [activeResume, setActiveResume] = useState<Resume | null>(currentResume || null);
  const [loadingResumes, setLoadingResumes] = useState<boolean>(false);

  // State for job description
  const [jobText, setJobText] = useState<string>(SAMPLE_JOB_PRESETS[0].text);
  const [parsedJob, setParsedJob] = useState<JobDescription | null>(null);

  // Analysis state
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [matchResult, setMatchResult] = useState<JobMatchResult | null>(null);
  const [semanticResult, setSemanticResult] = useState<SemanticMatchResult | null>(null);

  // Navigation tabs
  const [activeTab, setActiveTab] = useState<TabType>('comparison');

  // Load available resumes from database
  const fetchAvailableResumes = async () => {
    try {
      setLoadingResumes(true);
      const list = await listDBResumes(0, 30);
      setDbResumes(list);
      if (list.length > 0 && !selectedResumeId && !currentResume) {
        setSelectedResumeId(list[0].id);
      }
    } catch (err) {
      console.warn('Could not fetch DB resumes list:', err);
    } finally {
      setLoadingResumes(false);
    }
  };

  useEffect(() => {
    fetchAvailableResumes();
  }, []);

  // When selected resume ID changes, fetch its full structured data
  useEffect(() => {
    if (!selectedResumeId) return;
    let isMounted = true;

    async function loadResumeDetail() {
      try {
        const detail: DBResumeDetail = await getDBResume(selectedResumeId);
        if (isMounted) {
          setActiveResume(detail.resume);
        }
      } catch (err) {
        console.warn('Failed to load selected resume detail:', err);
      }
    }

    loadResumeDetail();
    return () => {
      isMounted = false;
    };
  }, [selectedResumeId]);

  // Handle full analysis trigger
  const handleRunAnalysis = async () => {
    if (!jobText.trim()) {
      setAnalysisError('Please enter or paste a job description.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      // 1. Parse Job Description
      const parseResp = await parseJobDescription(jobText.trim(), true);
      const structuredJob = parseResp.job;
      setParsedJob(structuredJob);

      // 2. Perform Resume-Job Match
      const matchPayload: any = {
        job_description: structuredJob,
        job_text: jobText.trim(),
      };

      if (activeResume) {
        matchPayload.resume = activeResume;
      } else if (selectedResumeId) {
        matchPayload.resume_id = selectedResumeId;
      } else {
        // Fallback to sample resume if none loaded yet
        matchPayload.resume_text = 'Software Engineer with experience in Python, FastAPI, Docker, and PostgreSQL.';
      }

      const matchRes = await matchResumeToJob(matchPayload);
      setMatchResult(matchRes);

      // 3. Perform Dense Semantic Similarity Matching
      try {
        const semanticRes = await computeSemanticMatch({
          job_description: structuredJob,
          resume: activeResume || undefined,
          job_text: jobText.trim(),
          resume_id: selectedResumeId || undefined,
        });
        setSemanticResult(semanticRes);
      } catch (semErr) {
        console.warn('Semantic embedding matching encountered a non-fatal error:', semErr);
      }
    } catch (err: any) {
      setAnalysisError(err.message || 'Failed to complete job match analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Control Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                Phase 19
              </span>
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                Resume-to-Job Matching & Requirement Analysis
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Select a resume and paste a job description to perform deterministic skill verification and semantic alignment.
            </p>
          </div>

          {/* Quick Refresh */}
          <button
            type="button"
            onClick={fetchAvailableResumes}
            disabled={loadingResumes}
            className="text-xs text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingResumes ? 'animate-spin' : ''}`} />
            <span>Reload Resumes</span>
          </button>
        </div>

        {/* Resume Selection Selector */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
          <div className="md:col-span-2 space-y-1.5">
            <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-500" />
              1. Select Candidate Resume from Database
            </label>
            <div className="flex gap-2">
              <select
                value={selectedResumeId}
                onChange={(e) => setSelectedResumeId(e.target.value)}
                className="flex-1 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg p-2.5 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
              >
                {dbResumes.length === 0 ? (
                  <option value="">No stored resumes found in database</option>
                ) : (
                  dbResumes.map((res) => (
                    <option key={res.id} value={res.id}>
                      {res.candidate_name || 'Unnamed Candidate'} ({res.original_filename}) — ID: {res.id.slice(0, 8)}...
                    </option>
                  ))
                )}
              </select>
            </div>
          </div>

          {/* Active Candidate Quick Info */}
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 text-xs space-y-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider block">
              Active Candidate
            </span>
            <p className="font-semibold text-slate-900 truncate">
              {activeResume?.personal_info?.full_name || 'Candidate Loaded'}
            </p>
            <div className="text-[11px] text-slate-500 flex items-center gap-2">
              <span>{activeResume?.skills?.length ?? 0} skills detected</span>
              <span aria-hidden="true">·</span>
              <span>{activeResume?.experience?.length ?? 0} experiences</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Job Input Component */}
      <JobInput
        jobText={jobText}
        onJobTextChange={setJobText}
        onAnalyze={handleRunAnalysis}
        isLoading={isAnalyzing}
        parsedJob={parsedJob}
      />

      {/* Error Message if any */}
      {analysisError && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-red-600" />
          <div>
            <p className="font-semibold text-red-900">Analysis Error</p>
            <p>{analysisError}</p>
          </div>
        </div>
      )}

      {/* Analysis Results View */}
      {matchResult && (
        <div className="space-y-4">
          {/* Segmented Tab Navigation Controls */}
          <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl border border-slate-200 overflow-x-auto">
            <button
              type="button"
              onClick={() => setActiveTab('comparison')}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === 'comparison'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Scale className="w-3.5 h-3.5" />
              <span>Overview & Comparison</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('matched')}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === 'matched'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Matched Skills ({matchResult.matched_skills.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('missing')}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === 'missing'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
              <span>Missing Skills ({matchResult.missing_required_skills.length})</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('requirements')}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === 'requirements'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileText className="w-3.5 h-3.5 text-slate-600" />
              <span>Job Requirements</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('semantic')}
              className={`flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
                activeTab === 'semantic'
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Semantic Similarity</span>
            </button>
          </div>

          {/* Active Tab Panel Content */}
          <div>
            {activeTab === 'comparison' && (
              <ResumeJobComparison
                matchResult={matchResult}
                job={parsedJob}
                resume={activeResume}
              />
            )}

            {activeTab === 'matched' && (
              <MatchedSkills matchResult={matchResult} />
            )}

            {activeTab === 'missing' && (
              <MissingSkills matchResult={matchResult} />
            )}

            {activeTab === 'requirements' && parsedJob && (
              <JobRequirements job={parsedJob} />
            )}

            {activeTab === 'semantic' && (
              <SimilarityAnalysis
                semanticResult={semanticResult}
                isLoading={isAnalyzing}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
