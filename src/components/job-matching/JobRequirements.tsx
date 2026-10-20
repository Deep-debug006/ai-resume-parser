import React from 'react';
import {
  Briefcase,
  GraduationCap,
  Clock,
  Layers,
  Wrench,
  Award,
  CheckCircle2,
  Building,
  MapPin,
  Banknote,
} from 'lucide-react';
import { JobDescription } from '../../types/job';

interface JobRequirementsProps {
  job: JobDescription;
}

export const JobRequirements: React.FC<JobRequirementsProps> = ({ job }) => {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-6">
      {/* Header Info */}
      <div className="border-b border-slate-100 pb-4">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2">
          <div>
            <h3 className="text-lg font-bold text-slate-900 tracking-tight">
              {job.job_title}
            </h3>
            {job.company && (
              <div className="flex items-center gap-1.5 text-sm font-medium text-slate-700 mt-1">
                <Building className="w-3.5 h-3.5 text-slate-400" />
                <span>{job.company}</span>
              </div>
            )}
          </div>

          {/* Metadata Row */}
          <div className="flex items-center gap-3 text-xs text-slate-500 flex-wrap">
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                {job.location}
              </span>
            )}
            {job.employment_type && (
              <>
                <span aria-hidden="true" className="text-slate-300">·</span>
                <span>{job.employment_type}</span>
              </>
            )}
            {job.salary_range && (
              <>
                <span aria-hidden="true" className="text-slate-300">·</span>
                <span className="flex items-center gap-1 text-slate-700 font-medium">
                  <Banknote className="w-3.5 h-3.5 text-emerald-600" />
                  {job.salary_range}
                </span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Grid of Requirements */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Required Skills */}
        <div className="p-4 bg-slate-50/70 rounded-lg border border-slate-200/80 space-y-2.5">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-slate-700" />
              Required Skills ({job.required_skills.length})
            </h4>
          </div>
          {job.required_skills.length > 0 ? (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {job.required_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="text-xs font-medium text-slate-800 bg-white border border-slate-200/90 rounded px-2.5 py-1"
                >
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No specific required skills extracted.</p>
          )}
        </div>

        {/* Preferred Skills */}
        <div className="p-4 bg-slate-50/70 rounded-lg border border-slate-200/80 space-y-2.5">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-700" />
              Preferred Skills ({job.preferred_skills.length})
            </h4>
          </div>
          {job.preferred_skills.length > 0 ? (
            <div className="flex flex-wrap gap-1.5 pt-1">
              {job.preferred_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="text-xs font-medium text-slate-700 bg-white border border-slate-200/90 rounded px-2.5 py-1"
                >
                  {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No preferred skills listed.</p>
          )}
        </div>

        {/* Experience Requirements */}
        <div className="p-4 bg-slate-50/70 rounded-lg border border-slate-200/80 space-y-2.5">
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-700" />
            Experience Requirements
          </h4>
          {job.experience_requirements.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-slate-700">
              {job.experience_requirements.map((exp, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-slate-400 select-none">•</span>
                  <span>{exp}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400 italic">No specific tenure requirements extracted.</p>
          )}
        </div>

        {/* Education Requirements */}
        <div className="p-4 bg-slate-50/70 rounded-lg border border-slate-200/80 space-y-2.5">
          <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
            <GraduationCap className="w-3.5 h-3.5 text-slate-700" />
            Education Requirements
          </h4>
          {job.education_requirements.length > 0 ? (
            <ul className="space-y-1.5 text-xs text-slate-700">
              {job.education_requirements.map((edu, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-slate-400 select-none">•</span>
                  <span>{edu}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-400 italic">No degree requirements specified.</p>
          )}
        </div>
      </div>

      {/* Responsibilities & Tools */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-2">
        {/* Responsibilities */}
        {job.responsibilities && job.responsibilities.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5 text-slate-700" />
              Core Responsibilities
            </h4>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {job.responsibilities.map((resp, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-slate-400 select-none">•</span>
                  <span>{resp}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Tools and Certifications */}
        <div className="space-y-4">
          {job.tools_and_technologies && job.tools_and_technologies.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Wrench className="w-3.5 h-3.5 text-slate-700" />
                Tools & Technologies
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {job.tools_and_technologies.map((tool, idx) => (
                  <span
                    key={idx}
                    className="text-xs font-mono text-slate-700 bg-slate-100 rounded px-2 py-0.5"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          )}

          {job.certifications && job.certifications.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                <Award className="w-3.5 h-3.5 text-slate-700" />
                Certifications Requested
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {job.certifications.map((cert, idx) => (
                  <span
                    key={idx}
                    className="text-xs font-medium text-slate-700 bg-amber-50 border border-amber-200 rounded px-2 py-0.5"
                  >
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
