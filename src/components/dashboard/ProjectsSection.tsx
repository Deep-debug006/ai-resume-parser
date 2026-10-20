import React from 'react';
import { FolderGit2, ExternalLink, Calendar, Tag, CheckCircle2 } from 'lucide-react';
import { Project } from '../../types/resume';

export interface ProjectsSectionProps {
  projects?: Project[] | null;
}

export const ProjectsSection: React.FC<ProjectsSectionProps> = ({ projects = [] }) => {
  const hasItems = projects && projects.length > 0;

  return (
    <section
      aria-labelledby="projects-heading"
      className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 md:p-8"
    >
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center">
            <FolderGit2 className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 id="projects-heading" className="text-base font-bold text-slate-900">
              Projects &amp; Initiatives
            </h2>
            <p className="text-xs text-slate-500">Key engineering initiatives, open source &amp; products</p>
          </div>
        </div>
        {hasItems && (
          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
            {projects.length} {projects.length === 1 ? 'project' : 'projects'}
          </span>
        )}
      </div>

      {!hasItems ? (
        <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
          <FolderGit2 className="w-8 h-8 text-slate-300 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-600">No Projects Found</p>
          <p className="text-xs text-slate-400 mt-1">
            No dedicated project showcase records were extracted from this resume.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((proj, idx) => {
            const hasTech = proj.technologies && proj.technologies.length > 0;
            const hasHighlights = proj.highlights && proj.highlights.length > 0;

            return (
              <article
                key={`${proj.name}-${idx}`}
                className="p-5 rounded-xl bg-slate-50/70 border border-slate-200/80 flex flex-col justify-between hover:bg-slate-100/50 transition-colors"
              >
                <div>
                  {/* Title & Link */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-sm font-bold text-slate-900">{proj.name}</h3>

                    {proj.url && (
                      <a
                        href={proj.url.startsWith('http') ? proj.url : `https://${proj.url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-teal-700 hover:text-teal-900 inline-flex items-center gap-1 font-medium transition-colors shrink-0 focus-visible:outline-2 focus-visible:outline-emerald-600"
                        title="View project URL"
                        aria-label={`View ${proj.name} project URL`}
                      >
                        <span>Link</span>
                        <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
                      </a>
                    )}
                  </div>

                  {/* Dates */}
                  {(proj.start_date || proj.end_date) && (
                    <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-1">
                      <Calendar className="w-3 h-3" aria-hidden="true" />
                      <span>
                        {proj.start_date || ''} {proj.start_date && proj.end_date ? '–' : ''} {proj.end_date || ''}
                      </span>
                    </div>
                  )}

                  {/* Description */}
                  {proj.description && (
                    <p className="text-xs text-slate-600 mb-3 leading-relaxed">
                      {proj.description}
                    </p>
                  )}

                  {/* Highlights */}
                  {hasHighlights && (
                    <ul className="space-y-1 mb-3 text-xs text-slate-600">
                      {proj.highlights.map((hl, hIdx) => (
                        <li key={hIdx} className="flex items-start gap-1.5">
                          <CheckCircle2 className="w-3 h-3 text-teal-600 mt-0.5 shrink-0" aria-hidden="true" />
                          <span>{hl}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Technologies */}
                {hasTech && (
                  <div className="pt-3 border-t border-slate-200/60 flex items-center flex-wrap gap-1 mt-2">
                    {proj.technologies.map((tech, tIdx) => (
                      <span
                        key={tIdx}
                        className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-700 text-[10px] font-mono"
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
