import React, { useState, useMemo } from 'react';
import {
  Wrench,
  Search,
  Code2,
  Boxes,
  Database,
  Cloud,
  Cpu,
  Layers,
  HeartHandshake,
  Check,
  Filter,
} from 'lucide-react';
import { SkillSet } from '../../types/resume';

export interface SkillsSectionProps {
  skills?: SkillSet | null;
}

interface CategoryConfig {
  key: keyof SkillSet;
  label: string;
  icon: React.ElementType;
  badgeBg: string;
  badgeText: string;
}

const CATEGORIES: CategoryConfig[] = [
  {
    key: 'programming_languages',
    label: 'Programming Languages',
    icon: Code2,
    badgeBg: 'bg-indigo-50 border-indigo-200/80',
    badgeText: 'text-indigo-800',
  },
  {
    key: 'frameworks_and_libraries',
    label: 'Frameworks & Libraries',
    icon: Boxes,
    badgeBg: 'bg-sky-50 border-sky-200/80',
    badgeText: 'text-sky-800',
  },
  {
    key: 'databases',
    label: 'Databases & Storage',
    icon: Database,
    badgeBg: 'bg-emerald-50 border-emerald-200/80',
    badgeText: 'text-emerald-800',
  },
  {
    key: 'cloud_and_devops',
    label: 'Cloud & DevOps',
    icon: Cloud,
    badgeBg: 'bg-amber-50 border-amber-200/80',
    badgeText: 'text-amber-800',
  },
  {
    key: 'technical_skills',
    label: 'Technical Concepts',
    icon: Cpu,
    badgeBg: 'bg-purple-50 border-purple-200/80',
    badgeText: 'text-purple-800',
  },
  {
    key: 'tools',
    label: 'Developer Tools',
    icon: Layers,
    badgeBg: 'bg-slate-100 border-slate-200',
    badgeText: 'text-slate-800',
  },
  {
    key: 'soft_skills',
    label: 'Soft Skills & Leadership',
    icon: HeartHandshake,
    badgeBg: 'bg-rose-50 border-rose-200/80',
    badgeText: 'text-rose-800',
  },
];

export const SkillsSection: React.FC<SkillsSectionProps> = ({ skills }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const totalSkillsCount = useMemo(() => {
    if (!skills) return 0;
    return Object.values(skills).reduce((acc, curr) => acc + (Array.isArray(curr) ? curr.length : 0), 0);
  }, [skills]);

  const filteredCategories = useMemo(() => {
    if (!skills) return [];

    return CATEGORIES.map((cat) => {
      const items = (skills[cat.key] as string[]) || [];
      const filteredItems = items.filter((sk) =>
        sk.toLowerCase().includes(searchQuery.toLowerCase().trim())
      );
      return {
        ...cat,
        items: filteredItems,
        totalInCat: items.length,
      };
    }).filter((cat) => {
      if (selectedCategory !== 'all' && cat.key !== selectedCategory) {
        return false;
      }
      return cat.items.length > 0;
    });
  }, [skills, searchQuery, selectedCategory]);

  const hasAnySkills = totalSkillsCount > 0;

  return (
    <section
      aria-labelledby="skills-heading"
      className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 md:p-8"
    >
      {/* Header and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-100 mb-6 gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center">
            <Wrench className="w-4 h-4" aria-hidden="true" />
          </div>
          <div>
            <h2 id="skills-heading" className="text-base font-bold text-slate-900">
              Skills &amp; Competencies
            </h2>
            <p className="text-xs text-slate-500">
              Deterministic normalized taxonomy &amp; categorized competencies
            </p>
          </div>
        </div>

        {hasAnySkills && (
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/80">
              {totalSkillsCount} Skills Extracted
            </span>
          </div>
        )}
      </div>

      {!hasAnySkills ? (
        <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-200 text-center">
          <Wrench className="w-8 h-8 text-slate-300 mx-auto mb-2" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-600">No Skills Detected</p>
          <p className="text-xs text-slate-400 mt-1">
            No technical or soft competencies were found in the resume.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Controls: Search and Filter Tabs */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            {/* Search Input */}
            <div className="relative flex-1 max-w-sm">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" aria-hidden="true" />
              <input
                type="text"
                placeholder="Search extracted skills..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                aria-label="Search skills"
              />
            </div>

            {/* Category Select Buttons */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 text-xs">
              <button
                type="button"
                onClick={() => setSelectedCategory('all')}
                className={`px-2.5 py-1 rounded-lg font-medium transition-colors shrink-0 focus-visible:outline-2 focus-visible:outline-emerald-600 ${
                  selectedCategory === 'all'
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600 hover:text-slate-900'
                }`}
              >
                All ({totalSkillsCount})
              </button>
              {CATEGORIES.map((cat) => {
                const count = ((skills?.[cat.key] as string[]) || []).length;
                if (count === 0) return null;
                return (
                  <button
                    key={cat.key}
                    type="button"
                    onClick={() => setSelectedCategory(cat.key)}
                    className={`px-2.5 py-1 rounded-lg font-medium transition-colors shrink-0 focus-visible:outline-2 focus-visible:outline-emerald-600 ${
                      selectedCategory === cat.key
                        ? 'bg-slate-900 text-white'
                        : 'bg-slate-100 text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {cat.label.split(' ')[0]} ({count})
                  </button>
                );
              })}
            </div>
          </div>

          {/* Categorized Skills Grid */}
          {filteredCategories.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-xl">
              No skills match &quot;{searchQuery}&quot;
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredCategories.map((cat) => {
                const IconComponent = cat.icon;
                return (
                  <div
                    key={cat.key}
                    className="p-4 rounded-xl bg-slate-50/60 border border-slate-200/80 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <IconComponent className="w-4 h-4 text-slate-500" aria-hidden="true" />
                          <h3 className="text-xs font-semibold text-slate-900">{cat.label}</h3>
                        </div>
                        <span className="text-[11px] font-mono text-slate-400">
                          {cat.items.length} {cat.items.length === 1 ? 'skill' : 'skills'}
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-1.5">
                        {cat.items.map((skill, sIdx) => (
                          <span
                            key={sIdx}
                            className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${cat.badgeBg} ${cat.badgeText}`}
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </section>
  );
};
