import React, { useState } from 'react';
import {
  Sparkles,
  User,
  Building2,
  MapPin,
  Calendar,
  Mail,
  Globe,
  RotateCw,
  Copy,
  Check,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
  Info,
  Terminal,
} from 'lucide-react';
import { ResumeNLPEntitiesResponse, NLPStatus } from '../types/resume';
import { extractResumeNLPEntities } from '../services/resumeService';

interface NLPViewerProps {
  resumeId: string;
  originalFilename: string;
}

export const NLPViewer: React.FC<NLPViewerProps> = ({
  resumeId,
  originalFilename,
}) => {
  const [status, setStatus] = useState<NLPStatus>('idle');
  const [data, setData] = useState<ResumeNLPEntitiesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [showRawEntities, setShowRawEntities] = useState<boolean>(false);

  const handleExtract = async () => {
    setStatus('extracting');
    setError(null);
    try {
      const result = await extractResumeNLPEntities(resumeId);
      setData(result);
      setStatus('success');
    } catch (err: unknown) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to extract NLP entities.');
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8 mt-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-50 text-cyan-700 text-xs font-semibold mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            Phase 8: spaCy NLP Preprocessing
          </div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight">
            Deterministic Named Entity Evidence
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Extracts PERSON, ORG, GPE, DATE, EMAIL, and URL spans to anchor structured entity extraction.
          </p>
        </div>

        {/* Action Button */}
        <div>
          {status === 'idle' ? (
            <button
              type="button"
              onClick={handleExtract}
              className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-sm font-semibold rounded-xl shadow-xs transition-colors cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              Extract NLP Entities
            </button>
          ) : status === 'extracting' ? (
            <button
              type="button"
              disabled
              className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-100 text-cyan-500 text-sm font-semibold rounded-xl cursor-wait"
            >
              <RotateCw className="w-4 h-4 animate-spin" />
              Extracting with spaCy...
            </button>
          ) : (
            <button
              type="button"
              onClick={handleExtract}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200/70 rounded-lg transition-colors cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5 text-slate-500" />
              Re-run NLP
            </button>
          )}
        </div>
      </div>

      {/* Body Area */}
      <div className="mt-5">
        {status === 'idle' && (
          <div className="text-center py-10 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
            <Sparkles className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700">Ready for NLP Entity Extraction</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto mt-1">
              Click &quot;Extract NLP Entities&quot; to parse candidate names, organizations, geographic locations, dates, and contact links using deterministic spaCy models.
            </p>
          </div>
        )}

        {status === 'extracting' && (
          <div className="text-center py-12 bg-cyan-50/30 rounded-xl border border-cyan-100">
            <RotateCw className="w-8 h-8 text-cyan-600 animate-spin mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-cyan-950">Running spaCy en_core_web_sm Pipeline</h4>
            <p className="text-xs text-cyan-700/80 mt-1">
              Evaluating linguistic tags, identifying named entity boundaries, and extracting structural tokens...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-sm text-rose-800 flex items-start gap-3">
            <div className="flex-1">
              <h4 className="font-semibold text-rose-900">NLP Extraction Failure</h4>
              <p className="text-rose-700 text-xs mt-0.5">{error}</p>
            </div>
            <button
              type="button"
              onClick={handleExtract}
              className="px-2.5 py-1 text-xs font-semibold text-rose-700 hover:bg-rose-100 rounded-md transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {status === 'success' && data && (
          <div className="space-y-6">
            {/* Supporting Evidence Callout */}
            <div className="p-3.5 rounded-xl bg-sky-50 border border-sky-100 flex items-start gap-2.5 text-xs text-sky-900">
              <Info className="w-4 h-4 text-sky-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Supporting Evidence Philosophy:</span> These entities serve as high-confidence anchors for downstream LLM parsing. Organizations (<span className="font-mono text-sky-800 font-semibold">ORG</span>) include companies, universities, and institutions and are never blindly assumed to be employers.
              </div>
            </div>

            {/* Entity Summary Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Persons */}
              <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-sky-600" />
                    <span className="text-xs font-bold text-slate-800">Persons (PERSON)</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 font-semibold">
                    {data.persons.length}
                  </span>
                </div>
                {data.persons.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {data.persons.map((p, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-800 shadow-2xs">
                        {p}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No person entities detected</p>
                )}
              </div>

              {/* Organizations */}
              <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-indigo-600" />
                    <span className="text-xs font-bold text-slate-800">Organizations (ORG)</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-semibold">
                    {data.organizations.length}
                  </span>
                </div>
                {data.organizations.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                    {data.organizations.map((org, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-800 shadow-2xs">
                        {org}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No organization entities detected</p>
                )}
              </div>

              {/* Locations */}
              <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-bold text-slate-800">Locations (GPE/LOC)</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold">
                    {data.locations.length}
                  </span>
                </div>
                {data.locations.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                    {data.locations.map((loc, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-800 shadow-2xs">
                        {loc}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No location entities detected</p>
                )}
              </div>

              {/* Dates */}
              <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-amber-600" />
                    <span className="text-xs font-bold text-slate-800">Dates &amp; Durations (DATE)</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-semibold">
                    {data.dates.length}
                  </span>
                </div>
                {data.dates.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                    {data.dates.map((d, idx) => (
                      <span key={idx} className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-medium text-slate-800 shadow-2xs">
                        {d}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No date entities detected</p>
                )}
              </div>

              {/* Emails */}
              <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-violet-600" />
                    <span className="text-xs font-bold text-slate-800">Emails</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-violet-100 text-violet-800 font-semibold">
                    {data.emails.length}
                  </span>
                </div>
                {data.emails.length > 0 ? (
                  <div className="space-y-1">
                    {data.emails.map((email, idx) => (
                      <div key={idx} className="text-xs font-mono text-slate-700 bg-white p-2 rounded-lg border border-slate-200 break-all shadow-2xs">
                        {email}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No emails found</p>
                )}
              </div>

              {/* URLs */}
              <div className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
                  <div className="flex items-center gap-2">
                    <Globe className="w-4 h-4 text-rose-600" />
                    <span className="text-xs font-bold text-slate-800">URLs &amp; Links</span>
                  </div>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-semibold">
                    {data.urls.length}
                  </span>
                </div>
                {data.urls.length > 0 ? (
                  <div className="space-y-1 max-h-36 overflow-y-auto">
                    {data.urls.map((url, idx) => (
                      <div key={idx} className="text-xs font-mono text-slate-700 bg-white p-2 rounded-lg border border-slate-200 break-all shadow-2xs truncate">
                        {url}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No links found</p>
                )}
              </div>
            </div>

            {/* Toggleable Raw Entity Spans */}
            <div className="border-t border-slate-100 pt-4">
              <button
                type="button"
                onClick={() => setShowRawEntities(!showRawEntities)}
                className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 cursor-pointer"
              >
                {showRawEntities ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                <span>Raw spaCy Spans ({data.entities.length} detected)</span>
              </button>

              {showRawEntities && (
                <div className="mt-3 relative">
                  <div className="flex justify-end mb-2">
                    <button
                      type="button"
                      onClick={() => handleCopy(JSON.stringify(data.entities, null, 2), 'raw')}
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg shadow-2xs cursor-pointer"
                    >
                      {copiedKey === 'raw' ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
                      {copiedKey === 'raw' ? 'Copied' : 'Copy JSON'}
                    </button>
                  </div>
                  <pre className="bg-slate-900 text-slate-100 rounded-xl p-4 text-xs font-mono overflow-x-auto max-h-64 leading-relaxed selection:bg-cyan-500 selection:text-white">
                    {JSON.stringify(data.entities, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
