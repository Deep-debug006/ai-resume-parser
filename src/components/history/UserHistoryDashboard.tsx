import React, { useState, useEffect } from 'react';
import {
  History,
  Search,
  Filter,
  ArrowUpDown,
  FileText,
  Briefcase,
  Scale,
  Trash2,
  Eye,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
  Building,
  User,
  ShieldCheck,
} from 'lucide-react';
import {
  fetchHistorySummary,
  fetchResumeHistory,
  fetchJobHistory,
  fetchAnalysisHistory,
  fetchAnalysisDetail,
  deleteAnalysisHistoryRecord,
  deleteJobRecord,
  getDBResume,
  deleteDBResume,
  fetchCurrentUser,
} from '../../services/api';
import {
  HistoryOverviewResponse,
  ResumeHistorySummary,
  JobHistorySummary,
  AnalysisHistorySummary,
  AnalysisHistoryDetail,
  PaginatedMeta,
} from '../../types/history';
import { User as UserType } from '../../types/auth';
import { HistoryDetailModal } from './HistoryDetailModal';

type HistoryTab = 'resumes' | 'jobs' | 'analyses';

export const UserHistoryDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<HistoryTab>('resumes');
  const [currentUser, setCurrentUser] = useState<UserType | null>(null);

  // Overview metrics
  const [summary, setSummary] = useState<HistoryOverviewResponse>({
    total_resumes: 0,
    total_jobs: 0,
    total_analyses: 0,
  });

  // Query state
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [analysisTypeFilter, setAnalysisTypeFilter] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Data states
  const [resumes, setResumes] = useState<ResumeHistorySummary[]>([]);
  const [jobs, setJobs] = useState<JobHistorySummary[]>([]);
  const [analyses, setAnalyses] = useState<AnalysisHistorySummary[]>([]);
  const [meta, setMeta] = useState<PaginatedMeta>({
    total: 0,
    page: 1,
    page_size: 10,
    total_pages: 1,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal state
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [detailType, setDetailType] = useState<'resume' | 'job' | 'analysis'>('resume');
  const [selectedResumeDetail, setSelectedResumeDetail] = useState<any | null>(null);
  const [selectedJobDetail, setSelectedJobDetail] = useState<any | null>(null);
  const [selectedAnalysisDetail, setSelectedAnalysisDetail] = useState<AnalysisHistoryDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Delete Confirmation state
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Load user profile on mount
  useEffect(() => {
    async function loadUser() {
      try {
        const u = await fetchCurrentUser();
        setCurrentUser(u);
      } catch {
        setCurrentUser(null);
      }
    }
    loadUser();
  }, []);

  // Fetch summary overview counts
  const loadSummaryStats = async () => {
    try {
      const data = await fetchHistorySummary();
      setSummary(data);
    } catch (err) {
      console.warn('Could not load history summary:', err);
    }
  };

  // Main data loader based on activeTab
  const loadTabContent = async () => {
    setLoading(true);
    setError(null);

    try {
      if (activeTab === 'resumes') {
        const res = await fetchResumeHistory({
          page,
          pageSize,
          search: search.trim() || undefined,
          statusFilter: statusFilter || undefined,
          sortBy,
        });
        setResumes(res.items);
        setMeta(res.meta);
      } else if (activeTab === 'jobs') {
        const res = await fetchJobHistory({
          page,
          pageSize,
          search: search.trim() || undefined,
          sortBy,
        });
        setJobs(res.items);
        setMeta(res.meta);
      } else if (activeTab === 'analyses') {
        const res = await fetchAnalysisHistory({
          page,
          pageSize,
          search: search.trim() || undefined,
          analysisType: analysisTypeFilter || undefined,
          sortBy,
        });
        setAnalyses(res.items);
        setMeta(res.meta);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load history items.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummaryStats();
  }, [activeTab]);

  useEffect(() => {
    loadTabContent();
  }, [activeTab, page, pageSize, search, statusFilter, analysisTypeFilter, sortBy]);

  // Reset page when switching tabs or changing filters
  const handleTabChange = (newTab: HistoryTab) => {
    setActiveTab(newTab);
    setPage(1);
    setSearch('');
    setStatusFilter('');
    setAnalysisTypeFilter('');
    setSortBy('newest');
  };

  // View Record Details
  const handleViewDetails = async (id: string, type: 'resume' | 'job' | 'analysis') => {
    setDetailLoading(true);
    setDetailType(type);
    setSelectedResumeDetail(null);
    setSelectedJobDetail(null);
    setSelectedAnalysisDetail(null);

    try {
      if (type === 'resume') {
        const data = await getDBResume(id);
        setSelectedResumeDetail(data);
        setIsDetailOpen(true);
      } else if (type === 'job') {
        // Find existing or fetch
        const item = jobs.find((j) => j.id === id);
        setSelectedJobDetail(item || { id, title: 'Job Description' });
        setIsDetailOpen(true);
      } else if (type === 'analysis') {
        const detail = await fetchAnalysisDetail(id);
        setSelectedAnalysisDetail(detail);
        setIsDetailOpen(true);
      }
    } catch (err: any) {
      alert(err.message || 'Failed to retrieve record details.');
    } finally {
      setDetailLoading(false);
    }
  };

  // Delete Record
  const handleDelete = async (id: string, type: 'resume' | 'job' | 'analysis') => {
    if (!confirm('Are you sure you want to permanently delete this record?')) return;

    setDeletingId(id);
    try {
      if (type === 'resume') {
        await deleteDBResume(id);
      } else if (type === 'job') {
        await deleteJobRecord(id);
      } else if (type === 'analysis') {
        await deleteAnalysisHistoryRecord(id);
      }
      // Refresh current tab content and counts
      loadTabContent();
      loadSummaryStats();
    } catch (err: any) {
      alert(err.message || 'Failed to delete record. Please check authorization.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 shadow-sm p-6 space-y-6">
      {/* Dashboard Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-900 text-white px-2 py-0.5 rounded">
              Phase 20
            </span>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <History className="w-5 h-5 text-slate-800" />
              User History &amp; Records Archive
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Browse and manage previously uploaded resumes, job descriptions, and comparative match reports with full pagination.
          </p>
        </div>

        {/* User Context & Refresh */}
        <div className="flex items-center gap-2 flex-wrap self-start sm:self-auto">
          {currentUser ? (
            <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-50 border border-emerald-200 rounded-lg text-xs font-medium text-emerald-900">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span className="truncate max-w-[160px]">{currentUser.email}</span>
            </div>
          ) : (
            <div className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1">
              <span>Public / Demo Records</span>
            </div>
          )}

          <button
            type="button"
            onClick={() => {
              loadTabContent();
              loadSummaryStats();
            }}
            disabled={loading}
            className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 hover:text-slate-900 transition-colors cursor-pointer"
            title="Refresh History"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Lightweight Summary Count Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Resumes Count */}
        <div
          onClick={() => handleTabChange('resumes')}
          className={`p-4 rounded-xl border transition-all cursor-pointer ${
            activeTab === 'resumes'
              ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
              : 'bg-slate-50/70 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className={`text-[11px] font-bold uppercase tracking-wider ${activeTab === 'resumes' ? 'text-slate-300' : 'text-slate-500'}`}>
              Resumes Uploaded
            </span>
            <FileText className={`w-4 h-4 ${activeTab === 'resumes' ? 'text-slate-300' : 'text-slate-500'}`} />
          </div>
          <div className="text-2xl font-black mt-2">{summary.total_resumes}</div>
          <span className={`text-xs block mt-0.5 ${activeTab === 'resumes' ? 'text-slate-400' : 'text-slate-500'}`}>
            Track document processing &amp; extractions
          </span>
        </div>

        {/* Jobs Count */}
        <div
          onClick={() => handleTabChange('jobs')}
          className={`p-4 rounded-xl border transition-all cursor-pointer ${
            activeTab === 'jobs'
              ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
              : 'bg-slate-50/70 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className={`text-[11px] font-bold uppercase tracking-wider ${activeTab === 'jobs' ? 'text-slate-300' : 'text-slate-500'}`}>
              Job Descriptions
            </span>
            <Briefcase className={`w-4 h-4 ${activeTab === 'jobs' ? 'text-slate-300' : 'text-slate-500'}`} />
          </div>
          <div className="text-2xl font-black mt-2">{summary.total_jobs}</div>
          <span className={`text-xs block mt-0.5 ${activeTab === 'jobs' ? 'text-slate-400' : 'text-slate-500'}`}>
            Saved criteria &amp; parsed requirements
          </span>
        </div>

        {/* Analyses Count */}
        <div
          onClick={() => handleTabChange('analyses')}
          className={`p-4 rounded-xl border transition-all cursor-pointer ${
            activeTab === 'analyses'
              ? 'bg-slate-900 text-white border-slate-900 shadow-xs'
              : 'bg-slate-50/70 border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className={`text-[11px] font-bold uppercase tracking-wider ${activeTab === 'analyses' ? 'text-slate-300' : 'text-slate-500'}`}>
              Analyses Performed
            </span>
            <Scale className={`w-4 h-4 ${activeTab === 'analyses' ? 'text-slate-300' : 'text-slate-500'}`} />
          </div>
          <div className="text-2xl font-black mt-2">{summary.total_analyses}</div>
          <span className={`text-xs block mt-0.5 ${activeTab === 'analyses' ? 'text-slate-400' : 'text-slate-500'}`}>
            Historical requirement match comparisons
          </span>
        </div>
      </div>

      {/* Primary Tab Navigation Controls */}
      <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl border border-slate-200 overflow-x-auto">
        <button
          type="button"
          onClick={() => handleTabChange('resumes')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
            activeTab === 'resumes' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Resumes Archive ({summary.total_resumes})</span>
        </button>

        <button
          type="button"
          onClick={() => handleTabChange('jobs')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
            activeTab === 'jobs' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Briefcase className="w-3.5 h-3.5" />
          <span>Job Descriptions ({summary.total_jobs})</span>
        </button>

        <button
          type="button"
          onClick={() => handleTabChange('analyses')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
            activeTab === 'analyses' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          <Scale className="w-3.5 h-3.5" />
          <span>Analysis Reports ({summary.total_analyses})</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
        {/* Search Input */}
        <div className="sm:col-span-5 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            placeholder={
              activeTab === 'resumes'
                ? 'Search by filename or candidate name...'
                : activeTab === 'jobs'
                ? 'Search job title, company, or keywords...'
                : 'Search candidate name, job title, or company...'
            }
            className="w-full pl-9 pr-3 py-2 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
          />
        </div>

        {/* Tab-Specific Filters */}
        {activeTab === 'resumes' && (
          <div className="sm:col-span-3">
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
            >
              <option value="">All Processing Statuses</option>
              <option value="processed">Processed</option>
              <option value="completed">Completed</option>
              <option value="uploaded">Uploaded</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        )}

        {activeTab === 'analyses' && (
          <div className="sm:col-span-3">
            <select
              value={analysisTypeFilter}
              onChange={(e) => {
                setAnalysisTypeFilter(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
            >
              <option value="">All Analysis Types</option>
              <option value="job_match">Job Match Analysis</option>
              <option value="semantic_match">Semantic Vector Match</option>
              <option value="resume_quality">Resume Quality Audit</option>
            </select>
          </div>
        )}

        {activeTab === 'jobs' && <div className="sm:col-span-3" />}

        {/* Sorting Dropdown */}
        <div className="sm:col-span-4 flex items-center gap-2">
          <ArrowUpDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <select
            value={sortBy}
            onChange={(e) => {
              setSortBy(e.target.value);
              setPage(1);
            }}
            className="w-full py-2 px-3 text-xs text-slate-800 bg-slate-50 border border-slate-200 rounded-lg focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-900"
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            {activeTab === 'resumes' && (
              <>
                <option value="name_asc">Filename (A-Z)</option>
                <option value="name_desc">Filename (Z-A)</option>
              </>
            )}
            {activeTab === 'jobs' && (
              <>
                <option value="title_asc">Title (A-Z)</option>
                <option value="title_desc">Title (Z-A)</option>
              </>
            )}
            {activeTab === 'analyses' && (
              <>
                <option value="score_desc">Highest Match Score</option>
                <option value="score_asc">Lowest Match Score</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Error Notice */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Content Table / Card List */}
      <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-2xs">
        {loading ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-8 h-8 border-3 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs font-semibold text-slate-700">Loading lightweight history records...</p>
          </div>
        ) : activeTab === 'resumes' ? (
          resumes.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <FileText className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-xs font-medium text-slate-600">No resume documents found</p>
              <p className="text-[11px] text-slate-400">Upload a resume in the pipeline to create your first archive record.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {resumes.map((item) => (
                <div
                  key={item.id}
                  className="p-4 hover:bg-slate-50/70 transition-colors flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900 truncate">
                        {item.original_filename}
                      </span>
                      <span className="px-2 py-0.5 text-[10px] font-medium bg-slate-100 border border-slate-200 text-slate-700 rounded capitalize">
                        {item.processing_status}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-slate-500 text-[11px] flex-wrap">
                      {item.candidate_name && (
                        <span>Candidate: {item.candidate_name}</span>
                      )}
                      {item.candidate_email && (
                        <>
                          <span aria-hidden="true">·</span>
                          <span className="font-mono">{item.candidate_email}</span>
                        </>
                      )}
                      <span aria-hidden="true">·</span>
                      <span>{item.skills_count} skills</span>
                      <span aria-hidden="true">·</span>
                      <span>{item.raw_text_char_count.toLocaleString()} chars</span>
                      <span aria-hidden="true">·</span>
                      <span className="text-slate-400">
                        {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleViewDetails(item.id, 'resume')}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 font-medium transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>View</span>
                    </button>

                    <button
                      type="button"
                      disabled={deletingId === item.id}
                      onClick={() => handleDelete(item.id, 'resume')}
                      className="p-1.5 rounded-lg border border-red-200 hover:bg-red-50 text-red-600 transition-colors cursor-pointer"
                      title="Delete Resume"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : activeTab === 'jobs' ? (
          jobs.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <Briefcase className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-xs font-medium text-slate-600">No job descriptions stored</p>
              <p className="text-[11px] text-slate-400">Save job postings in the Job Matching tab to populate history.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {jobs.map((item) => (
                <div
                  key={item.id}
                  className="p-4 hover:bg-slate-50/70 transition-colors flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900 truncate">
                        {item.title || 'Untitled Role'}
                      </span>
                      {item.company && (
                        <span className="text-slate-500 font-medium">@ {item.company}</span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-slate-500 text-[11px] flex-wrap">
                      <span>{item.required_skills_count} required skills</span>
                      <span aria-hidden="true">·</span>
                      <span>{item.char_count.toLocaleString()} chars</span>
                      <span aria-hidden="true">·</span>
                      <span className="text-slate-400">
                        {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleViewDetails(item.id, 'job')}
                      className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 font-medium transition-colors flex items-center gap-1 cursor-pointer"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>View</span>
                    </button>

                    <button
                      type="button"
                      disabled={deletingId === item.id}
                      onClick={() => handleDelete(item.id, 'job')}
                      className="p-1.5 rounded-lg border border-red-200 hover:bg-red-50 text-red-600 transition-colors cursor-pointer"
                      title="Delete Job"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        ) : (
          analyses.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-2">
              <Scale className="w-8 h-8 mx-auto text-slate-300" />
              <p className="text-xs font-medium text-slate-600">No match analyses found</p>
              <p className="text-[11px] text-slate-400">Run a resume-to-job requirement match to record reports into your archive.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {analyses.map((item) => {
                const matchPct = item.match_rate !== null && item.match_rate !== undefined
                  ? Math.round(item.match_rate * 100)
                  : item.score !== null && item.score !== undefined
                  ? Math.round(item.score * 100)
                  : null;

                return (
                  <div
                    key={item.id}
                    className="p-4 hover:bg-slate-50/70 transition-colors flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-slate-900 truncate">
                          {item.job_title || 'General Requirement Match'}
                        </span>
                        {item.company && (
                          <span className="text-slate-500 font-medium">({item.company})</span>
                        )}
                        <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-indigo-50 border border-indigo-200 text-indigo-800 rounded">
                          {item.analysis_type.replace('_', ' ')}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-slate-500 text-[11px] flex-wrap">
                        {item.candidate_name && <span>Candidate: {item.candidate_name}</span>}
                        {item.resume_filename && (
                          <>
                            <span aria-hidden="true">·</span>
                            <span>{item.resume_filename}</span>
                          </>
                        )}
                        {matchPct !== null && (
                          <>
                            <span aria-hidden="true">·</span>
                            <span className="font-bold text-slate-900">{matchPct}% Match Rate</span>
                          </>
                        )}
                        <span aria-hidden="true">·</span>
                        <span className="text-slate-400">
                          {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => handleViewDetails(item.id, 'analysis')}
                        className="px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 font-medium transition-colors flex items-center gap-1 cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>View</span>
                      </button>

                      <button
                        type="button"
                        disabled={deletingId === item.id}
                        onClick={() => handleDelete(item.id, 'analysis')}
                        className="p-1.5 rounded-lg border border-red-200 hover:bg-red-50 text-red-600 transition-colors cursor-pointer"
                        title="Delete Analysis"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )
        )}
      </div>

      {/* Pagination Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500 pt-2">
        <div className="flex items-center gap-2">
          <span>
            Showing page <strong className="text-slate-800">{meta.page}</strong> of{' '}
            <strong className="text-slate-800">{meta.total_pages}</strong> ({meta.total} total items)
          </span>
          <span aria-hidden="true">·</span>
          <div className="flex items-center gap-1">
            <span>Per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
              className="py-1 px-2 text-xs bg-slate-50 border border-slate-200 rounded focus:outline-none"
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>

        {/* Previous / Next buttons */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            disabled={page <= 1 || loading}
            onClick={() => setPage((prev) => Math.max(1, prev - 1))}
            className={`p-1.5 rounded-lg border flex items-center gap-1 transition-colors ${
              page <= 1 || loading
                ? 'border-slate-200 text-slate-300 cursor-not-allowed'
                : 'border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="text-xs">Prev</span>
          </button>

          <span className="px-2 text-xs font-semibold text-slate-800">
            {meta.page}
          </span>

          <button
            type="button"
            disabled={page >= meta.total_pages || loading}
            onClick={() => setPage((prev) => Math.min(meta.total_pages, prev + 1))}
            className={`p-1.5 rounded-lg border flex items-center gap-1 transition-colors ${
              page >= meta.total_pages || loading
                ? 'border-slate-200 text-slate-300 cursor-not-allowed'
                : 'border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer'
            }`}
          >
            <span className="text-xs">Next</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* History Detail Modal */}
      <HistoryDetailModal
        isOpen={isDetailOpen}
        onClose={() => setIsDetailOpen(false)}
        type={detailType}
        resumeDetail={selectedResumeDetail}
        jobDetail={selectedJobDetail}
        analysisDetail={selectedAnalysisDetail}
      />
    </div>
  );
};
