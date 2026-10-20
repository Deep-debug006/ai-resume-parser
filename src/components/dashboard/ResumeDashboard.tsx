import React, { useState, useEffect, useCallback } from 'react';
import {
  LayoutDashboard,
  Upload,
  RefreshCw,
  AlertCircle,
  FileText,
  Search,
  CheckCircle2,
  Database,
  Download,
  Sparkles,
  ChevronDown,
  Layers,
  FileCheck,
} from 'lucide-react';
import {
  listDBResumes,
  getDBResume,
  processResumeFile,
  seedDB,
} from '../../services/api';
import { StructuredResume } from '../../types/resume';
import { DBResumeSummary, DBResumeDetail } from '../../types/database';
import { ResumeProcessResponse } from '../../types/pipeline';

import { ResumeHeader } from './ResumeHeader';
import { PersonalInfo } from './PersonalInfo';
import { EducationSection } from './EducationSection';
import { SkillsSection } from './SkillsSection';
import { ExperienceSection } from './ExperienceSection';
import { ProjectsSection } from './ProjectsSection';
import { CertificationsSection } from './CertificationsSection';
import { AchievementsSection } from './AchievementsSection';

export interface ResumeDashboardProps {
  initialResumeId?: string;
  onSelectResumeId?: (id: string) => void;
}

export const ResumeDashboard: React.FC<ResumeDashboardProps> = ({
  initialResumeId,
  onSelectResumeId,
}) => {
  const [resumesList, setResumesList] = useState<DBResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(initialResumeId || null);
  const [activeResumeDetail, setActiveResumeDetail] = useState<DBResumeDetail | null>(null);

  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isProcessingNew, setIsProcessingNew] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeNavTab, setActiveNavTab] = useState<string>('all');

  // Load available resumes list from PostgreSQL API
  const fetchResumesList = useCallback(async (selectFirstIfNone = false) => {
    setIsLoadingList(true);
    setError(null);
    try {
      const list = await listDBResumes();
      setResumesList(list);

      if (list.length > 0) {
        if (selectFirstIfNone && !selectedResumeId) {
          setSelectedResumeId(list[0].id);
        }
      }
    } catch (err: any) {
      setError(err.message || 'Failed to retrieve resumes from PostgreSQL.');
    } finally {
      setIsLoadingList(false);
    }
  }, [selectedResumeId]);

  // Load specific resume detail from PostgreSQL API
  const fetchResumeDetail = useCallback(async (resumeId: string) => {
    setIsLoadingDetail(true);
    setError(null);
    try {
      const detail = await getDBResume(resumeId);
      setActiveResumeDetail(detail);
      if (onSelectResumeId) {
        onSelectResumeId(resumeId);
      }
    } catch (err: any) {
      setError(err.message || `Failed to fetch resume '${resumeId}'.`);
    } finally {
      setIsLoadingDetail(false);
    }
  }, [onSelectResumeId]);

  // Initial load
  useEffect(() => {
    fetchResumesList(true);
  }, []);

  // When selectedResumeId changes, fetch detail
  useEffect(() => {
    if (selectedResumeId) {
      fetchResumeDetail(selectedResumeId);
    }
  }, [selectedResumeId, fetchResumeDetail]);

  // Quick Seed Handler
  const handleSeedDatabase = async () => {
    setIsLoadingDetail(true);
    setError(null);
    try {
      const seeded = await seedDB();
      await fetchResumesList(false);
      setSelectedResumeId(seeded.id);
      setActiveResumeDetail(seeded);
    } catch (err: any) {
      setError(err.message || 'Failed to seed sample resume.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  // Upload & Process New Resume Handler
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];

    setIsProcessingNew(true);
    setError(null);
    try {
      const res: ResumeProcessResponse = await processResumeFile(file);
      await fetchResumesList(false);
      setSelectedResumeId(res.resume_id);
    } catch (err: any) {
      setError(err.message || 'Pipeline failed to process uploaded file.');
    } finally {
      setIsProcessingNew(false);
    }
  };

  // Export JSON Handler
  const handleExportJson = () => {
    if (!activeResumeDetail) return;
    const jsonStr = JSON.stringify(activeResumeDetail, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${activeResumeDetail.resume.personal_info.full_name.replace(/\s+/g, '_')}_resume.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Print Preview
  const handlePrint = () => {
    window.print();
  };

  // Filter list of resumes by candidate name or filename
  const filteredList = resumesList.filter((r) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      r.candidate_name.toLowerCase().includes(q) ||
      r.original_filename.toLowerCase().includes(q)
    );
  });

  const parsedResume: StructuredResume | undefined = activeResumeDetail?.resume;

  return (
    <div className="space-y-6">
      {/* Dashboard Top Control Bar */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-4 sm:p-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          {/* Title & Stats */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-900 text-white flex items-center justify-center shrink-0 shadow-sm">
              <LayoutDashboard className="w-5 h-5 text-emerald-400" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">
                  Resume Dashboard
                </h2>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Phase 13
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Visual presentation of parsed, normalized &amp; persisted resume records
              </p>
            </div>
          </div>

          {/* Right Action Tools: Resume Selector + Upload */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
            {/* Resume Selector Dropdown */}
            <div className="relative min-w-[220px]">
              <select
                value={selectedResumeId || ''}
                onChange={(e) => setSelectedResumeId(e.target.value)}
                disabled={isLoadingList || resumesList.length === 0}
                className="w-full text-xs font-medium bg-slate-50 border border-slate-200 text-slate-800 rounded-lg pl-3 pr-8 py-2 appearance-none focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 disabled:opacity-50"
                aria-label="Select resume to display"
              >
                {resumesList.length === 0 ? (
                  <option value="">No resumes found</option>
                ) : (
                  resumesList.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.candidate_name} ({r.original_filename})
                    </option>
                  ))
                )}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" aria-hidden="true" />
            </div>

            {/* Quick Upload Button */}
            <label className="inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg cursor-pointer transition-colors shadow-2xs shrink-0">
              <Upload className="w-3.5 h-3.5" aria-hidden="true" />
              <span>{isProcessingNew ? 'Processing...' : 'Upload New PDF'}</span>
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileUpload}
                disabled={isProcessingNew}
                className="hidden"
              />
            </label>

            {/* Seed Sample Resume if list is empty */}
            {resumesList.length === 0 && (
              <button
                type="button"
                onClick={handleSeedDatabase}
                disabled={isLoadingDetail}
                className="inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors shrink-0"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
                <span>Load Demo Resume</span>
              </button>
            )}
          </div>
        </div>

        {/* Section Jump Nav Tabs (when resume is loaded) */}
        {parsedResume && (
          <nav
            aria-label="Resume sections"
            className="mt-4 pt-4 border-t border-slate-100 flex items-center gap-1 overflow-x-auto text-xs pb-1"
          >
            {[
              { id: 'all', label: 'All Sections' },
              { id: 'experience', label: `Experience (${parsedResume.experience?.length || 0})` },
              { id: 'education', label: `Education (${parsedResume.education?.length || 0})` },
              { id: 'skills', label: 'Skills & Tech' },
              { id: 'projects', label: `Projects (${parsedResume.projects?.length || 0})` },
              { id: 'certifications', label: `Certifications (${parsedResume.certifications?.length || 0})` },
              { id: 'achievements', label: `Achievements (${parsedResume.achievements?.length || 0})` },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveNavTab(tab.id)}
                className={`px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600 ${
                  activeNavTab === tab.id
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        )}
      </div>

      {/* Global Error Banner */}
      {error && (
        <div
          role="alert"
          className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3 text-xs"
        >
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" aria-hidden="true" />
          <div className="flex-1">
            <span className="font-semibold block">Dashboard Notice:</span>
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => fetchResumesList(false)}
            className="text-xs font-semibold underline hover:no-underline text-rose-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeletons */}
      {isLoadingDetail && (
        <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading resume data">
          {/* Header skeleton */}
          <div className="h-44 bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
            <div className="h-6 w-1/3 bg-slate-200 rounded"></div>
            <div className="h-4 w-1/4 bg-slate-100 rounded"></div>
            <div className="h-16 w-full bg-slate-50 rounded"></div>
          </div>
          {/* Content skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-64 bg-white rounded-2xl border border-slate-200 p-6 space-y-3">
              <div className="h-5 w-1/4 bg-slate-200 rounded"></div>
              <div className="h-4 w-full bg-slate-100 rounded"></div>
              <div className="h-4 w-3/4 bg-slate-100 rounded"></div>
            </div>
            <div className="h-64 bg-white rounded-2xl border border-slate-200 p-6 space-y-3">
              <div className="h-5 w-1/4 bg-slate-200 rounded"></div>
              <div className="h-4 w-full bg-slate-100 rounded"></div>
              <div className="h-4 w-3/4 bg-slate-100 rounded"></div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State: No Resumes in PostgreSQL */}
      {!isLoadingDetail && !activeResumeDetail && resumesList.length === 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-4 border border-emerald-100">
            <FileText className="w-7 h-7" aria-hidden="true" />
          </div>
          <h3 className="text-lg font-bold text-slate-900 mb-1">
            No Resumes Persisted Yet
          </h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto mb-6">
            Upload a PDF resume to process it through the complete 10-stage pipeline, or seed sample data to preview the dashboard.
          </p>

          <div className="flex items-center justify-center gap-3">
            <label className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold cursor-pointer shadow-sm transition">
              <Upload className="w-4 h-4" />
              <span>Upload PDF Resume</span>
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
            <button
              type="button"
              onClick={handleSeedDatabase}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition"
            >
              <Sparkles className="w-4 h-4 text-amber-600" />
              <span>Load Demo Resume</span>
            </button>
          </div>
        </div>
      )}

      {/* Populated Resume Dashboard Views */}
      {!isLoadingDetail && activeResumeDetail && parsedResume && (
        <div className="space-y-6">
          {/* 1. ResumeHeader Component */}
          <ResumeHeader
            candidateName={parsedResume.personal_info?.full_name}
            summary={parsedResume.summary}
            objective={parsedResume.objective}
            originalFilename={activeResumeDetail.original_filename}
            status={activeResumeDetail.processing_status}
            extractionMethod={activeResumeDetail.extraction_method}
            rawTextCharCount={activeResumeDetail.raw_text_char_count}
            createdAt={activeResumeDetail.created_at}
            onExportJson={handleExportJson}
            onPrint={handlePrint}
            onRefresh={() => fetchResumeDetail(activeResumeDetail.id)}
            isRefreshing={isLoadingDetail}
          />

          {/* 2. PersonalInfo Component */}
          {(activeNavTab === 'all' || activeNavTab === 'overview') && (
            <PersonalInfo info={parsedResume.personal_info} />
          )}

          {/* 3. ExperienceSection Component */}
          {(activeNavTab === 'all' || activeNavTab === 'experience') && (
            <ExperienceSection experience={parsedResume.experience} />
          )}

          {/* 4. EducationSection Component */}
          {(activeNavTab === 'all' || activeNavTab === 'education') && (
            <EducationSection education={parsedResume.education} />
          )}

          {/* 5. SkillsSection Component */}
          {(activeNavTab === 'all' || activeNavTab === 'skills') && (
            <SkillsSection skills={parsedResume.skills} />
          )}

          {/* 6. ProjectsSection Component */}
          {(activeNavTab === 'all' || activeNavTab === 'projects') && (
            <ProjectsSection projects={parsedResume.projects} />
          )}

          {/* 7. CertificationsSection Component */}
          {(activeNavTab === 'all' || activeNavTab === 'certifications') && (
            <CertificationsSection certifications={parsedResume.certifications} />
          )}

          {/* 8. AchievementsSection Component */}
          {(activeNavTab === 'all' || activeNavTab === 'achievements') && (
            <AchievementsSection achievements={parsedResume.achievements} />
          )}
        </div>
      )}
    </div>
  );
};
