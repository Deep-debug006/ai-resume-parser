import React from 'react';
import {
  X,
  FileText,
  Briefcase,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Building,
  User,
  GraduationCap,
  Clock,
  Award,
  Layers,
  Scale,
  Calendar,
} from 'lucide-react';
import { AnalysisHistoryDetail, ResumeHistorySummary, JobHistorySummary } from '../../types/history';

interface HistoryDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  type: 'resume' | 'job' | 'analysis';
  resumeDetail?: any | null;
  jobDetail?: any | null;
  analysisDetail?: AnalysisHistoryDetail | null;
}

export const HistoryDetailModal: React.FC<HistoryDetailModalProps> = ({
  isOpen,
  onClose,
  type,
  resumeDetail,
  jobDetail,
  analysisDetail,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col relative my-8">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white/95 backdrop-blur-xs rounded-t-2xl z-10">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-slate-900 text-white rounded-lg">
              {type === 'resume' && <FileText className="w-5 h-5" />}
              {type === 'job' && <Briefcase className="w-5 h-5" />}
              {type === 'analysis' && <Scale className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">
                {type === 'resume' && 'Resume Record Details'}
                {type === 'job' && 'Job Description Details'}
                {type === 'analysis' && 'Historical Analysis Report'}
              </h3>
              <p className="text-xs text-slate-500">
                {type === 'resume' && (resumeDetail?.original_filename || 'Structured Resume Data')}
                {type === 'job' && (jobDetail?.title || 'Job Requirements')}
                {type === 'analysis' && (analysisDetail?.job_title || 'Resume-to-Job Evaluation')}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-700 flex-1">
          {/* ================= RESUME DETAIL ================= */}
          {type === 'resume' && resumeDetail && (
            <div className="space-y-5">
              {/* Personal Info */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
                <div className="flex items-center gap-2 font-semibold text-slate-900">
                  <User className="w-4 h-4 text-slate-600" />
                  <span>Candidate Profile</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-500 block text-[11px]">Full Name</span>
                    <span className="font-semibold text-slate-900">
                      {resumeDetail.resume?.personal_info?.full_name || 'Not extracted'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Email</span>
                    <span className="font-mono text-slate-800">
                      {resumeDetail.resume?.personal_info?.email || 'None provided'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Processing Status</span>
                    <span className="font-medium text-emerald-700 capitalize">
                      {resumeDetail.processing_status}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[11px]">Uploaded Date</span>
                    <span>{resumeDetail.created_at ? new Date(resumeDetail.created_at).toLocaleString() : '—'}</span>
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-slate-600" />
                  Extracted Skills ({resumeDetail.resume?.skills?.length || 0})
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {resumeDetail.resume?.skills?.map((sk: any, i: number) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 bg-slate-100 text-slate-800 rounded font-medium text-xs border border-slate-200"
                    >
                      {sk.name || sk}
                    </span>
                  ))}
                </div>
              </div>

              {/* Experience */}
              {resumeDetail.resume?.experience?.length > 0 && (
                <div className="space-y-2.5">
                  <h4 className="font-bold text-slate-900 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-slate-600" />
                    Experience History ({resumeDetail.resume.experience.length})
                  </h4>
                  <div className="space-y-2">
                    {resumeDetail.resume.experience.map((exp: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg border border-slate-200 bg-white space-y-1">
                        <div className="flex justify-between font-semibold text-slate-900">
                          <span>{exp.title}</span>
                          <span className="text-slate-500 font-normal">{exp.start_date || '—'} - {exp.end_date || 'Present'}</span>
                        </div>
                        <p className="text-slate-600 font-medium">{exp.company}</p>
                        {exp.description && <p className="text-slate-500 pt-1 leading-relaxed">{exp.description}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ================= JOB DETAIL ================= */}
          {type === 'job' && jobDetail && (
            <div className="space-y-5">
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2">
                <div className="flex justify-between items-baseline">
                  <h4 className="text-base font-bold text-slate-900">{jobDetail.title}</h4>
                  <span className="text-xs text-slate-500">
                    {jobDetail.created_at ? new Date(jobDetail.created_at).toLocaleDateString() : ''}
                  </span>
                </div>
                {jobDetail.company && (
                  <p className="text-xs font-semibold text-slate-700 flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5 text-slate-400" />
                    {jobDetail.company}
                  </p>
                )}
              </div>

              {/* Requirements & Skills */}
              {jobDetail.structured_data?.required_skills?.length > 0 && (
                <div className="space-y-2">
                  <h5 className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                    Required Skills ({jobDetail.structured_data.required_skills.length})
                  </h5>
                  <div className="flex flex-wrap gap-1.5">
                    {jobDetail.structured_data.required_skills.map((s: string, i: number) => (
                      <span key={i} className="px-2.5 py-1 bg-slate-100 text-slate-800 rounded font-medium border border-slate-200">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw Job Description Text */}
              {jobDetail.raw_text && (
                <div className="space-y-2">
                  <h5 className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                    Original Job Description Text
                  </h5>
                  <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 font-mono text-[11px] leading-relaxed whitespace-pre-wrap max-h-60 overflow-y-auto text-slate-800">
                    {jobDetail.raw_text}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ================= ANALYSIS DETAIL ================= */}
          {type === 'analysis' && analysisDetail && (
            <div className="space-y-5">
              {/* Score Banner */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block">
                    Analysis Type: {analysisDetail.analysis_type.replace('_', ' ').toUpperCase()}
                  </span>
                  <h4 className="text-base font-bold text-slate-900">
                    {analysisDetail.job_title || 'Job Requirement Match'}
                  </h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Candidate: {analysisDetail.candidate_name || 'Resume Candidate'} ({analysisDetail.resume_filename})
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-400 block font-medium">Match Rate</span>
                  <span className="text-2xl font-black text-slate-900">
                    {analysisDetail.match_rate !== null && analysisDetail.match_rate !== undefined
                      ? `${Math.round(analysisDetail.match_rate * 100)}%`
                      : analysisDetail.score !== null && analysisDetail.score !== undefined
                      ? `${Math.round(analysisDetail.score * 100)}%`
                      : '—'}
                  </span>
                </div>
              </div>

              {/* Summary Findings */}
              {analysisDetail.summary && (
                <div className="p-3.5 bg-indigo-50/50 border border-indigo-100 rounded-lg text-indigo-950 space-y-1">
                  <p className="font-semibold text-indigo-900">Analysis Summary</p>
                  <p className="leading-relaxed">{analysisDetail.summary}</p>
                </div>
              )}

              {/* Detailed Result Breakdown if present */}
              {analysisDetail.result_data && (
                <div className="space-y-4">
                  {/* Matched & Missing Skills Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Matched */}
                    <div className="p-3.5 rounded-lg border border-emerald-200 bg-emerald-50/40 space-y-2">
                      <div className="flex items-center gap-1.5 font-bold text-emerald-950 text-xs">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        <span>Matched Required Skills</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {(analysisDetail.result_data.matched_skills || []).map((sk: string, i: number) => (
                          <span key={i} className="px-2 py-0.5 bg-white border border-emerald-200 rounded text-[11px] font-medium text-emerald-900">
                            {sk}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Missing */}
                    <div className="p-3.5 rounded-lg border border-amber-200 bg-amber-50/40 space-y-2">
                      <div className="flex items-center gap-1.5 font-bold text-amber-950 text-xs">
                        <AlertCircle className="w-4 h-4 text-amber-600" />
                        <span>Missing Required Skills</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {(analysisDetail.result_data.missing_required_skills || []).map((sk: string, i: number) => (
                          <span key={i} className="px-2 py-0.5 bg-white border border-amber-200 rounded text-[11px] font-medium text-amber-900">
                            {sk}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Experience & Education Alignment */}
                  {analysisDetail.result_data.experience_analysis && (
                    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                      <p className="font-semibold text-slate-800">Experience Alignment Assessment</p>
                      <p className="text-slate-600 leading-relaxed">{analysisDetail.result_data.experience_analysis}</p>
                    </div>
                  )}

                  {analysisDetail.result_data.education_analysis && (
                    <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-lg space-y-1">
                      <p className="font-semibold text-slate-800">Education Requirement Assessment</p>
                      <p className="text-slate-600 leading-relaxed">{analysisDetail.result_data.education_analysis}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Compliance Disclaimer */}
              <div className="p-3 bg-slate-100 rounded-lg text-[11px] text-slate-500 leading-relaxed">
                Objective resume-to-job requirement analysis only. This system performs deterministic qualification verification and does not predict candidate hiring outcomes or make automated employment decisions.
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 flex justify-end bg-slate-50 rounded-b-2xl">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg text-xs transition-colors cursor-pointer"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
};
