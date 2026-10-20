import React from 'react';
import {
  CheckCircle2,
  Award,
  Layers,
  Sparkles,
  Check,
} from 'lucide-react';
import { JobMatchResult } from '../../types/matching';

interface MatchedSkillsProps {
  matchResult: JobMatchResult;
}

export const MatchedSkills: React.FC<MatchedSkillsProps> = ({ matchResult }) => {
  const reqMatched = matchResult.matched_skills || [];
  const prefMatched = matchResult.matched_preferred_skills || [];
  const certMatched = matchResult.matched_certifications || [];

  const reqRate = Math.round(matchResult.required_skills_match_rate * 100);
  const prefRate = Math.round(matchResult.preferred_skills_match_rate * 100);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            Matched Skills & Qualifications
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Verified skills extracted from candidate resume that satisfy documented job requirements.
          </p>
        </div>

        {/* Match Rates */}
        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="text-right">
            <span className="text-slate-400 block text-[11px]">Required Match</span>
            <span className="text-sm font-bold text-slate-900">{reqRate}%</span>
          </div>
          <div className="w-px h-7 bg-slate-200" />
          <div className="text-right">
            <span className="text-slate-400 block text-[11px]">Preferred Match</span>
            <span className="text-sm font-bold text-slate-900">{prefRate}%</span>
          </div>
        </div>
      </div>

      <div className="space-y-5">
        {/* Matched Required Skills */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              Required Skills Matched ({reqMatched.length})
            </h4>
            <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded">
              {reqRate}% of required skills
            </span>
          </div>

          {reqMatched.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {reqMatched.map((skill, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 p-2 rounded-lg bg-emerald-50/50 border border-emerald-200/80 text-xs font-medium text-emerald-950"
                >
                  <Check className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                  <span className="truncate">{skill}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-500 italic">
              No exact required skill matches detected.
            </div>
          )}
        </div>

        {/* Matched Preferred Skills */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-600" />
              Preferred Skills Matched ({prefMatched.length})
            </h4>
            <span className="text-xs text-slate-700 font-medium bg-slate-100 px-2 py-0.5 rounded">
              {prefRate}% of preferred
            </span>
          </div>

          {prefMatched.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {prefMatched.map((skill, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-200 text-xs font-medium text-slate-800"
                >
                  <Check className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  <span className="truncate">{skill}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-500 italic">
              No preferred skill matches identified.
            </div>
          )}
        </div>

        {/* Matched Certifications */}
        {certMatched.length > 0 && (
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-amber-600" />
              Certifications Matched ({certMatched.length})
            </h4>

            <div className="flex flex-wrap gap-2">
              {certMatched.map((cert, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50/70 border border-amber-200 text-xs font-medium text-amber-950"
                >
                  <Check className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                  <span>{cert}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
