import React from 'react';
import { Briefcase, Calendar, MapPin, CheckCircle2, Tag } from 'lucide-react';
import { Experience } from '../../types/resume';

export interface ExperienceSectionProps {
  experience?: Experience[] | null;
}

export const ExperienceSection: React.FC<ExperienceSectionProps> = ({ experience = [] }) => {
  const hasItems = experience && experience.length > 0;

  return (
    <section
      aria-labelledby="experience-heading"
      className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 md:p-8"
    >
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center">
            <Briefcase className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 id="experience-heading" className="text-base font-bold text-slate-900">
              Work Experience
            </h2>
            <p className="text-xs text-slate-500">Employment history, career progression &amp; impact</p>
          </div>
        </div>
        {hasItems && (
          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
            {experience.length} {experience.length === 1 ? 'role' : 'roles'}
          </span>
        )}
      </div>

      {!hasItems ? (
        <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
          <Briefcase className="w-8 h-8 text-slate-300 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-600">No Experience Records Found</p>
          <p className="text-xs text-slate-400 mt-1">
            No work history or professional roles were parsed from the document.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {experience.map((item, idx) => {
            const hasHighlights = item.highlights && item.highlights.length > 0;
            const hasTech = item.technologies && item.technologies.length > 0;

            return (
              <article
                key={`${item.company}-${item.title}-${idx}`}
                className="relative pl-6 pb-6 border-l-2 border-blue-100 last:pb-0 last:border-l-0"
              >
                {/* Timeline node */}
                <div
                  className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 bg-white ${
                    item.is_current ? 'border-emerald-500 ring-2 ring-emerald-100' : 'border-blue-600'
                  }`}
                  aria-hidden="true"
                />

                {/* Job Title & Date Row */}
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 mb-1">
                  <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                    <span>{item.title}</span>
                    {item.is_current && (
                      <span className="px-2 py-0.5 text-[10px] uppercase font-bold text-emerald-800 bg-emerald-50 border border-emerald-200/80 rounded-full">
                        Current
                      </span>
                    )}
                  </h3>

                  {(item.start_date || item.end_date) && (
                    <span className="inline-flex items-center gap-1 text-xs text-slate-500 shrink-0 font-medium">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                      <span>
                        {item.start_date || 'Start'} – {item.is_current ? 'Present' : item.end_date || 'End'}
                      </span>
                    </span>
                  )}
                </div>

                {/* Company & Location */}
                <div className="flex items-center gap-2 text-sm text-slate-600 mb-3">
                  <span className="font-medium text-slate-900">{item.company}</span>
                  {item.location && (
                    <>
                      <span aria-hidden="true" className="text-slate-300">·</span>
                      <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                        <MapPin className="w-3 h-3 text-slate-400" aria-hidden="true" />
                        {item.location}
                      </span>
                    </>
                  )}
                </div>

                {/* Bulleted Highlights */}
                {hasHighlights && (
                  <ul className="space-y-1.5 my-3 text-xs text-slate-700 leading-relaxed">
                    {item.highlights.map((hl, hIdx) => (
                      <li key={hIdx} className="flex items-start gap-2">
                        <span
                          className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"
                          aria-hidden="true"
                        />
                        <span>{hl}</span>
                      </li>
                    ))}
                  </ul>
                )}

                {/* Technologies */}
                {hasTech && (
                  <div className="mt-3 pt-3 border-t border-slate-100 flex items-center flex-wrap gap-1.5">
                    <span className="text-[11px] font-semibold text-slate-400 mr-1 flex items-center gap-1">
                      <Tag className="w-3 h-3" aria-hidden="true" />
                      Stack:
                    </span>
                    {item.technologies.map((tech, tIdx) => (
                      <span
                        key={tIdx}
                        className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-mono"
                      >
                        {tech}
                      </span>
                    ))}
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
