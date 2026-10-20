import React from 'react';
import { Trophy, Calendar, Award } from 'lucide-react';
import { Achievement } from '../../types/resume';

export interface AchievementsSectionProps {
  achievements?: Achievement[] | null;
}

export const AchievementsSection: React.FC<AchievementsSectionProps> = ({
  achievements = [],
}) => {
  const hasItems = achievements && achievements.length > 0;

  return (
    <section
      aria-labelledby="achievements-heading"
      className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 md:p-8"
    >
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-yellow-50 text-yellow-700 flex items-center justify-center">
            <Trophy className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 id="achievements-heading" className="text-base font-bold text-slate-900">
              Honors &amp; Achievements
            </h2>
            <p className="text-xs text-slate-500">Awards, hackathons, publications &amp; recognition</p>
          </div>
        </div>
        {hasItems && (
          <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full">
            {achievements.length} {achievements.length === 1 ? 'award' : 'awards'}
          </span>
        )}
      </div>

      {!hasItems ? (
        <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
          <Trophy className="w-8 h-8 text-slate-300 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-600">No Honors Recorded</p>
          <p className="text-xs text-slate-400 mt-1">
            No specific awards or competitive achievements were identified.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {achievements.map((item, idx) => (
            <article
              key={`${item.title}-${idx}`}
              className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-yellow-600 shrink-0" aria-hidden="true" />
                    <span>{item.title}</span>
                  </h3>
                  {item.date && (
                    <span className="text-[11px] text-slate-400 font-medium shrink-0 flex items-center gap-1">
                      <Calendar className="w-3 h-3" aria-hidden="true" />
                      <span>{item.date}</span>
                    </span>
                  )}
                </div>

                {item.issuer && (
                  <div className="text-xs font-medium text-slate-600 mb-2 pl-5">
                    {item.issuer}
                  </div>
                )}

                {item.description && (
                  <p className="text-xs text-slate-600 mt-1 pl-5 leading-relaxed">
                    {item.description}
                  </p>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
};
