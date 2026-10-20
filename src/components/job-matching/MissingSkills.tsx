import React from 'react';
import {
  AlertCircle,
  HelpCircle,
  Award,
  Layers,
  ArrowUpRight,
  Info,
} from 'lucide-react';
import { JobMatchResult } from '../../types/matching';

interface MissingSkillsProps {
  matchResult: JobMatchResult;
}

export const MissingSkills: React.FC<MissingSkillsProps> = ({ matchResult }) => {
  const missingReq = matchResult.missing_required_skills || [];
  const missingPref = matchResult.missing_preferred_skills || [];
  const missingCert = matchResult.missing_certifications || [];

  const totalMissing = missingReq.length + missingPref.length + missingCert.length;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            Unmatched Requirements & Skills Gaps
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Skills specified in the job posting that were not explicitly detected in the resume text.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="font-semibold text-slate-800">{missingReq.length}</span> required
          <span aria-hidden="true">·</span>
          <span className="font-semibold text-slate-800">{missingPref.length}</span> preferred
        </div>
      </div>

      {totalMissing === 0 ? (
        <div className="p-6 bg-emerald-50/50 rounded-xl border border-emerald-200 text-center space-y-2">
          <h4 className="text-sm font-semibold text-emerald-900">
            Comprehensive Skill Coverage
          </h4>
          <p className="text-xs text-emerald-700 max-w-md mx-auto">
            All documented required and preferred skills from the job description are represented in this candidate's resume.
          </p>
        </div>
      ) : (
        <div className="space-y-5">
          {/* Missing Required Skills */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                Missing Required Skills ({missingReq.length})
              </h4>
              {missingReq.length > 0 && (
                <span className="text-[11px] font-medium text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                  High Priority
                </span>
              )}
            </div>

            {missingReq.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {missingReq.map((skill, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-amber-50/40 border border-amber-200/70 text-xs font-medium text-slate-800 flex items-center justify-between group"
                  >
                    <span className="truncate">{skill}</span>
                    <span className="text-[10px] text-amber-700 font-mono opacity-80">Req</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3 bg-emerald-50/40 border border-emerald-100 rounded-lg text-xs text-emerald-800 font-medium flex items-center gap-2">
                <span>All required skills are documented in the resume.</span>
              </div>
            )}
          </div>

          {/* Missing Preferred Skills */}
          {missingPref.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-500" />
                Missing Preferred Skills ({missingPref.length})
              </h4>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {missingPref.map((skill, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-slate-50 border border-slate-200/80 text-xs text-slate-700 truncate"
                  >
                    {skill}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing Certifications */}
          {missingCert.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-slate-500" />
                Certifications Requested But Missing ({missingCert.length})
              </h4>

              <div className="flex flex-wrap gap-2">
                {missingCert.map((cert, idx) => (
                  <div
                    key={idx}
                    className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-700"
                  >
                    {cert}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations Box */}
          <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 flex items-start gap-2.5">
            <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-slate-800 mb-0.5">Resume Refinement Tip</p>
              <p>
                If the candidate possesses experience with any of these technologies, ensure they are explicitly named in bullet points or the technical skills section using standard industry keywords.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
