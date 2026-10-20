import React from 'react';
import { GraduationCap, Award, BookOpen, Calendar } from 'lucide-react';
import { Education } from '../../types/resume';

export interface EducationSectionProps {
  education?: Education[] | null;
}

export const EducationSection: React.FC<EducationSectionProps> = ({ education = [] }) => {
  const hasItems = education && education.length > 0;

  return (
    <section
      aria-labelledby="education-heading"
      className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 md:p-8"
    >
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center">
            <GraduationCap className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 id="education-heading" className="text-base font-bold text-slate-900">
              Education
            </h2>
            <p className="text-xs text-slate-500">Academic degrees, institutions &amp; achievements</p>
          </div>
        </div>
        {hasItems && (
          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
            {education.length} {education.length === 1 ? 'entry' : 'entries'}
          </span>
        )}
      </div>

      {!hasItems ? (
        <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
          <GraduationCap className="w-8 h-8 text-slate-300 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-600">No Education Records Found</p>
          <p className="text-xs text-slate-400 mt-1">
            No formal academic history was extracted from this resume.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {education.map((item, idx) => {
            const hasGpa = item.gpa !== null && item.gpa !== undefined;
            const hasHonors = item.honors && item.honors.length > 0;
            const hasCourses = item.courses && item.courses.length > 0;

            return (
              <article
                key={`${item.institution}-${idx}`}
                className="relative pl-6 pb-6 border-l-2 border-indigo-100 last:pb-0 last:border-l-0"
              >
                {/* Timeline node */}
                <div
                  className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-2 border-indigo-600"
                  aria-hidden="true"
                />

                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 mb-1">
                  <h3 className="text-base font-semibold text-slate-900">
                    {item.degree ? `${item.degree} ` : ''}
                    {item.field_of_study ? `in ${item.field_of_study}` : ''}
                    {!item.degree && !item.field_of_study ? item.institution : ''}
                  </h3>

                  {(item.start_date || item.end_date) && (
                    <span className="inline-flex items-center gap-1 text-xs text-slate-500 shrink-0 font-medium">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                      <span>
                        {item.start_date || 'Start'} – {item.end_date || 'Present'}
                      </span>
                    </span>
                  )}
                </div>

                <div className="text-sm font-medium text-indigo-900/80 mb-2">
                  {item.institution}
                </div>

                {/* GPA & Honors */}
                <div className="flex flex-wrap items-center gap-3 my-2 text-xs">
                  {hasGpa && (
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200/80 font-mono font-medium">
                      <span>GPA:</span>
                      <span className="font-bold">{item.gpa}</span>
                      {item.gpa_max ? <span className="opacity-70">/ {item.gpa_max}</span> : null}
                    </span>
                  )}

                  {hasHonors && (
                    <div className="flex items-center gap-1 text-amber-800">
                      <Award className="w-3.5 h-3.5 text-amber-600 shrink-0" aria-hidden="true" />
                      <span className="font-medium">{item.honors.join(' · ')}</span>
                    </div>
                  )}
                </div>

                {/* Coursework */}
                {hasCourses && (
                  <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-600">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5 mb-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                      Key Coursework:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {item.courses.map((course, cIdx) => (
                        <span
                          key={cIdx}
                          className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-[11px]"
                        >
                          {course}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
};
