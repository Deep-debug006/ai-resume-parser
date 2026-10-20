import React, { useState } from 'react';
import {
  Layers,
  Briefcase,
  GraduationCap,
  Wrench,
  FolderGit2,
  Award,
  ScrollText,
  User,
  Compass,
  FileQuestion,
  RotateCw,
  Copy,
  Check,
  ChevronRight,
  BookOpen,
  Heart,
  Users,
  ShieldAlert,
} from 'lucide-react';
import { ResumeSectionsResponse, SectionStatus } from '../types/resume';
import { detectResumeSections } from '../services/resumeService';

interface SectionViewerProps {
  resumeId: string;
  originalFilename: string;
}

export const SectionViewer: React.FC<SectionViewerProps> = ({
  resumeId,
  originalFilename,
}) => {
  const [status, setStatus] = useState<SectionStatus>('idle');
  const [data, setData] = useState<ResumeSectionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<string>('');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const handleDetect = async () => {
    setStatus('detecting');
    setError(null);
    try {
      const result = await detectResumeSections(resumeId);
      setData(result);
      setStatus('success');
      // Set initial active section
      const keys = Object.keys(result.sections);
      if (keys.length > 0) {
        setActiveSection(keys[0]);
      } else if (result.unclassified) {
        setActiveSection('unclassified');
      }
    } catch (err: unknown) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to detect sections in resume.');
    }
  };

  const handleCopy = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
    } catch {
      // ignore
    }
  };

  const getSectionIcon = (section: string) => {
    switch (section) {
      case 'contact':
        return <User className="w-4 h-4 text-sky-600" />;
      case 'summary':
      case 'objective':
        return <ScrollText className="w-4 h-4 text-emerald-600" />;
      case 'experience':
        return <Briefcase className="w-4 h-4 text-indigo-600" />;
      case 'education':
        return <GraduationCap className="w-4 h-4 text-amber-600" />;
      case 'skills':
        return <Wrench className="w-4 h-4 text-cyan-600" />;
      case 'projects':
        return <FolderGit2 className="w-4 h-4 text-violet-600" />;
      case 'certifications':
      case 'achievements':
        return <Award className="w-4 h-4 text-rose-600" />;
      case 'publications':
        return <BookOpen className="w-4 h-4 text-blue-600" />;
      case 'positions_of_responsibility':
        return <Users className="w-4 h-4 text-teal-600" />;
      case 'extracurricular':
      case 'interests':
        return <Heart className="w-4 h-4 text-pink-600" />;
      case 'unclassified':
      default:
        return <FileQuestion className="w-4 h-4 text-slate-500" />;
    }
  };

  const formatSectionTitle = (section: string) => {
    return section
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  const sectionKeys = data ? Object.keys(data.sections) : [];
  const hasUnclassified = Boolean(data?.unclassified && data.unclassified.trim().length > 0);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8 mt-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-violet-50 text-violet-700 text-xs font-semibold mb-2">
            <Compass className="w-3.5 h-3.5" />
            Phase 6: Deterministic Section Detection
          </div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight">
            Segmented Resume Sections
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Document: <span className="font-semibold text-slate-700">{originalFilename}</span>
          </p>
        </div>

        {/* Action Button */}
        <div>
          {status === 'idle' ? (
            <button
              type="button"
              onClick={handleDetect}
              className="inline-flex items-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-semibold rounded-xl shadow-xs transition-colors cursor-pointer"
            >
              <Layers className="w-4 h-4" />
              Detect Sections
            </button>
          ) : status === 'detecting' ? (
            <button
              type="button"
              disabled
              className="inline-flex items-center gap-2 px-4 py-2 bg-violet-100 text-violet-500 text-sm font-semibold rounded-xl cursor-wait"
            >
              <RotateCw className="w-4 h-4 animate-spin" />
              Segmenting Sections...
            </button>
          ) : (
            <button
              type="button"
              onClick={handleDetect}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200/70 rounded-lg transition-colors cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5 text-slate-500" />
              Re-segment
            </button>
          )}
        </div>
      </div>

      {/* Body Area */}
      <div className="mt-5">
        {status === 'idle' && (
          <div className="text-center py-10 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
            <Layers className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700">Ready for Section Segmentation</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Click &quot;Detect Sections&quot; to classify cleaned resume text into canonical categories (Contact, Summary, Experience, Education, Skills, Projects, etc.).
            </p>
          </div>
        )}

        {status === 'detecting' && (
          <div className="text-center py-12 bg-violet-50/30 rounded-xl border border-violet-100">
            <RotateCw className="w-8 h-8 text-violet-600 animate-spin mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-violet-950">Deterministic Section Classification</h4>
            <p className="text-xs text-violet-700/80 mt-1">
              Scanning line boundaries, resolving heading variations, and partitioning sections without discarding any unclassified text...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-sm text-rose-800 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-rose-900">Section Segmentation Error</h4>
              <p className="text-rose-700 text-xs mt-0.5">{error}</p>
            </div>
            <button
              type="button"
              onClick={handleDetect}
              className="px-2.5 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-100 rounded-md transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {status === 'success' && data && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Left sidebar: Section Navigation */}
            <div className="md:col-span-4 space-y-1.5">
              <div className="flex items-center justify-between pb-2 mb-1 border-b border-slate-100 text-xs font-semibold text-slate-500">
                <span>Detected Categories</span>
                <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-mono text-[11px]">
                  {sectionKeys.length} {sectionKeys.length === 1 ? 'section' : 'sections'}
                </span>
              </div>

              {sectionKeys.map((key) => {
                const isSelected = activeSection === key;
                const content = data.sections[key];
                const rawHeading = data.raw_headings[key];
                const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setActiveSection(key)}
                    className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between gap-2.5 cursor-pointer ${
                      isSelected
                        ? 'bg-violet-50/70 border-violet-300 text-violet-900 shadow-2xs font-semibold'
                        : 'bg-white border-slate-200/80 text-slate-700 hover:bg-slate-50/80'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="p-1.5 rounded-lg bg-white shadow-2xs shrink-0">
                        {getSectionIcon(key)}
                      </div>
                      <div className="min-w-0">
                        <span className="block text-xs truncate">
                          {formatSectionTitle(key)}
                        </span>
                        {rawHeading && (
                          <span className="block text-[10px] text-slate-400 truncate">
                            Header: &quot;{rawHeading}&quot;
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span className="text-[10px] text-slate-400 font-mono">
                        {wordCount}w
                      </span>
                      <ChevronRight
                        className={`w-3.5 h-3.5 transition-transform ${
                          isSelected ? 'text-violet-600 translate-x-0.5' : 'text-slate-300'
                        }`}
                      />
                    </div>
                  </button>
                );
              })}

              {/* Unclassified Drawer Button */}
              {hasUnclassified && (
                <button
                  type="button"
                  onClick={() => setActiveSection('unclassified')}
                  className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between gap-2.5 cursor-pointer ${
                    activeSection === 'unclassified'
                      ? 'bg-amber-50/80 border-amber-300 text-amber-900 font-semibold shadow-2xs'
                      : 'bg-amber-50/30 border-amber-200/70 text-amber-800 hover:bg-amber-50/60'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="p-1.5 rounded-lg bg-white shadow-2xs shrink-0">
                      <FileQuestion className="w-4 h-4 text-amber-600" />
                    </div>
                    <div className="min-w-0">
                      <span className="block text-xs font-medium">Unclassified Text</span>
                      <span className="block text-[10px] text-amber-600/80">Preserved safely</span>
                    </div>
                  </div>
                  <ChevronRight className="w-3.5 h-3.5 text-amber-500" />
                </button>
              )}
            </div>

            {/* Right Panel: Active Section Content Viewer */}
            <div className="md:col-span-8">
              {activeSection && (
                <div className="bg-slate-50/70 rounded-xl border border-slate-200/80 p-5">
                  <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-200/70">
                    <div className="flex items-center gap-2">
                      {getSectionIcon(activeSection)}
                      <h4 className="text-sm font-bold text-slate-900">
                        {formatSectionTitle(activeSection)}
                      </h4>
                      {data.raw_headings[activeSection] && (
                        <span className="text-[11px] px-2 py-0.5 rounded bg-slate-200/70 text-slate-600 font-mono">
                          Raw: &quot;{data.raw_headings[activeSection]}&quot;
                        </span>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={() => {
                        const contentToCopy =
                          activeSection === 'unclassified'
                            ? data.unclassified
                            : data.sections[activeSection] || '';
                        handleCopy(contentToCopy, activeSection);
                      }}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-2xs cursor-pointer"
                    >
                      {copiedKey === activeSection ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-slate-500" />
                          Copy Section
                        </>
                      )}
                    </button>
                  </div>

                  {/* Section Content */}
                  <div className="relative">
                    <pre className="bg-slate-900 text-slate-100 rounded-lg p-4 text-xs font-mono overflow-x-auto max-h-96 leading-relaxed selection:bg-violet-500 selection:text-white whitespace-pre-wrap break-words">
                      {activeSection === 'unclassified'
                        ? data.unclassified || '(No unclassified text)'
                        : data.sections[activeSection] || '(Empty section)'}
                    </pre>
                  </div>

                  {activeSection === 'unclassified' && (
                    <p className="mt-3 text-[11px] text-amber-700 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                      ℹ This text could not be confidently mapped to a canonical section header and has been preserved separately without loss of information.
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
