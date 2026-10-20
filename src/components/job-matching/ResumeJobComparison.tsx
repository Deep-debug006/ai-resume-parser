import React from 'react';
import {
  Scale,
  Briefcase,
  GraduationCap,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ShieldCheck,
  FileCheck,
  Info,
} from 'lucide-react';
import { JobMatchResult } from '../../types/matching';
import { JobDescription } from '../../types/job';
import { Resume } from '../../types/resume';

interface ResumeJobComparisonProps {
  matchResult: JobMatchResult;
  job?: JobDescription | null;
  resume?: Resume | null;
}

export const ResumeJobComparison: React.FC<ResumeJobComparisonProps> = ({
  matchResult,
  job,
  resume,
}) => {
  const reqRate = Math.round(matchResult.required_skills_match_rate * 100);
  const prefRate = Math.round(matchResult.preferred_skills_match_rate * 100);

  const getAlignmentBadge = (status: string) => {
    switch (status) {
      case 'meets_requirements':
        return { label: 'Meets Criteria', color: 'text-emerald-800 bg-emerald-50 border-emerald-200' };
      case 'exceeds_requirements':
        return { label: 'Exceeds Criteria', color: 'text-blue-800 bg-blue-50 border-blue-200' };
      case 'partially_meets':
        return { label: 'Partially Meets', color: 'text-amber-800 bg-amber-50 border-amber-200' };
      case 'below_requirements':
        return { label: 'Below Stated Threshold', color: 'text-slate-800 bg-slate-100 border-slate-300' };
      default:
        return { label: 'Unspecified in Posting', color: 'text-slate-600 bg-slate-50 border-slate-200' };
    }
  };

  const expBadge = getAlignmentBadge(matchResult.experience_alignment);
  const eduBadge = getAlignmentBadge(matchResult.education_alignment);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <Scale className="w-4 h-4 text-slate-700" />
            Resume-to-Job Requirement Analysis
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Objective, document-grounded comparison between extracted candidate qualifications and job criteria.
          </p>
        </div>

        {/* Status Pill */}
        <div className="flex items-center gap-2 text-xs font-medium text-slate-600 bg-slate-100/80 px-3 py-1.5 rounded-lg border border-slate-200">
          <ShieldCheck className="w-3.5 h-3.5 text-slate-600" />
          <span>Non-Predictive Requirement Audit</span>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Required Skills Match */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
            Required Skills
          </span>
          <div className="text-2xl font-black text-slate-900">{reqRate}%</div>
          <span className="text-xs text-slate-500 block">
            {matchResult.matched_skills.length} matched / {matchResult.missing_required_skills.length} missing
          </span>
        </div>

        {/* Preferred Skills Match */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
            Preferred Skills
          </span>
          <div className="text-2xl font-black text-slate-900">{prefRate}%</div>
          <span className="text-xs text-slate-500 block">
            {matchResult.matched_preferred_skills.length} matched / {matchResult.missing_preferred_skills.length} missing
          </span>
        </div>

        {/* Experience Alignment */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
            Experience Alignment
          </span>
          <div className="pt-0.5">
            <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded border ${expBadge.color}`}>
              {expBadge.label}
            </span>
          </div>
          <span className="text-xs text-slate-500 block pt-0.5">
            Candidate: {matchResult.candidate_years_experience ?? '—'} yrs | Req: {matchResult.required_years_experience ?? '—'} yrs
          </span>
        </div>

        {/* Education Alignment */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-1">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
            Education Alignment
          </span>
          <div className="pt-0.5">
            <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded border ${eduBadge.color}`}>
              {eduBadge.label}
            </span>
          </div>
          <span className="text-xs text-slate-500 block pt-0.5">
            Degree requirements review
          </span>
        </div>
      </div>

      {/* Narrative Explanation of Comparison */}
      <div className="space-y-4">
        <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
          <FileCheck className="w-3.5 h-3.5 text-slate-700" />
          Comparative Analysis & Findings
        </h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Experience Narrative */}
          <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-semibold text-xs text-slate-900">
              <Briefcase className="w-3.5 h-3.5 text-slate-700" />
              <span>Experience Requirement Review</span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {matchResult.experience_analysis || 'No detailed experience tenure requirement was specified in the job posting.'}
            </p>
          </div>

          {/* Education Narrative */}
          <div className="p-4 rounded-xl bg-slate-50/70 border border-slate-200 space-y-2">
            <div className="flex items-center gap-2 font-semibold text-xs text-slate-900">
              <GraduationCap className="w-3.5 h-3.5 text-slate-700" />
              <span>Education Requirement Review</span>
            </div>
            <p className="text-xs text-slate-700 leading-relaxed">
              {matchResult.education_analysis || 'No mandatory academic degree prerequisite was detected in the job posting.'}
            </p>
          </div>
        </div>
      </div>

      {/* Mandatory Neutral Non-Predictive Disclaimer Banner */}
      <div className="p-4 rounded-xl bg-slate-100/70 border border-slate-200 text-slate-700 text-xs leading-relaxed space-y-1">
        <div className="flex items-center gap-2 font-semibold text-slate-900">
          <Info className="w-4 h-4 text-slate-600 shrink-0" />
          <span>Requirement Analysis Standard Disclaimer</span>
        </div>
        <p className="text-slate-600">
          {matchResult.disclaimer ||
            'This analysis evaluates the presence of documented qualifications against explicit job posting criteria. It is designed to assist candidates and recruiters in identifying requirements alignment and should not be used as an automated hiring decision or predictive hiring metric.'}
        </p>
      </div>
    </div>
  );
};
