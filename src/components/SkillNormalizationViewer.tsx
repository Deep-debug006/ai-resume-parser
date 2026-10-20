import React, { useState, useEffect } from 'react';
import {
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  RefreshCw,
  Search,
  BookOpen,
  Filter,
  Check,
  Copy,
  Info,
  AlertTriangle,
} from 'lucide-react';
import { NormalizeSkillsResponse, SkillDictionaryStatsResponse } from '../types/skills';
import { normalizeSkills, getSkillDictionary } from '../services/api';

const PRESETS = [
  {
    name: 'Prompt Requirements',
    skills: 'JS, Javascript, ReactJS, React.js, Node, Mongo',
    desc: 'Exact examples from requirements specification',
  },
  {
    name: 'Modern Full-Stack Stack',
    skills: 'ReactJS, react.js, ts, JS, node, nodejs, mongo, postgres, psql, docker, k8s, aws, tailwind, fastapi, ProprietaryEngineV2',
    desc: 'Heavy aliases, duplicates, and unknown custom technology',
  },
  {
    name: 'Collision Guard Check',
    skills: 'Java, JavaScript, C, C++, C#, SQL, NoSQL, PostgreSQL, MySQL, Git, GitHub',
    desc: 'Verifies unrelated technologies are NEVER accidentally merged',
  },
];

export const SkillNormalizationViewer: React.FC = () => {
  const [inputText, setInputText] = useState(PRESETS[0].skills);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NormalizeSkillsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dictStats, setDictStats] = useState<SkillDictionaryStatsResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDictionary, setShowDictionary] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Initial fetch of dictionary stats
    getSkillDictionary()
      .then(setDictStats)
      .catch((err) => console.error('Failed to load dictionary stats:', err));

    // Run initial normalization with default preset
    handleNormalize(PRESETS[0].skills);
  }, []);

  const handleNormalize = async (customText?: string) => {
    const textToProcess = customText !== undefined ? customText : inputText;
    const rawTokens = textToProcess
      .split(/[,\n]/)
      .map((s) => s.trim())
      .filter(Boolean);

    if (rawTokens.length === 0) {
      setError('Please provide at least one skill to normalize.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await normalizeSkills(rawTokens);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Failed to normalize skills.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result.normalized_skills.join(', '));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const filteredCanonical = dictStats?.canonical_skills.filter((sk) =>
    sk.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="bg-white rounded-2xl border border-teal-200/80 shadow-xs p-6 transition-all">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-teal-100 text-teal-800 rounded-lg">
              <Layers className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-slate-900">
              Phase 10: Deterministic Skill Normalization &amp; Taxonomy
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-teal-50 text-teal-700 border border-teal-200 rounded uppercase">
              Canonical Dictionary
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Standardizes disparate acronyms, abbreviations, and informal spellings into canonical tech entities without calling external LLMs.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {dictStats && (
            <button
              onClick={() => setShowDictionary(!showDictionary)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-xl border border-slate-200 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5 text-teal-600" />
              {showDictionary ? 'Hide Taxonomy' : `Browse Taxonomy (${dictStats.canonical_count})`}
            </button>
          )}

          <button
            onClick={() => handleNormalize()}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-300 text-white text-xs font-semibold rounded-xl shadow-xs transition-all shrink-0"
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Normalizing...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                Normalize Skills
              </>
            )}
          </button>
        </div>
      </div>

      {/* Preset Selector */}
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-slate-600 flex items-center gap-1">
          <Filter className="w-3 h-3 text-slate-400" />
          Test Presets:
        </span>
        {PRESETS.map((preset, idx) => (
          <button
            key={idx}
            onClick={() => {
              setInputText(preset.skills);
              handleNormalize(preset.skills);
            }}
            className="px-2.5 py-1 text-xs bg-slate-50 hover:bg-teal-50 text-slate-700 hover:text-teal-800 border border-slate-200 hover:border-teal-300 rounded-lg transition-all"
            title={preset.desc}
          >
            {preset.name}
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="mt-3">
        <label className="block text-xs font-medium text-slate-700 mb-1">
          Input Raw Skills (comma-separated or line-separated):
        </label>
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          rows={2}
          className="w-full text-xs font-mono p-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
          placeholder="JS, ReactJS, Node, Mongo, Python 3..."
        />
      </div>

      {/* Error Banner */}
      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-xl text-xs text-red-700">
          {error}
        </div>
      )}

      {/* Dictionary Drawer */}
      {showDictionary && dictStats && (
        <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-200/80">
            <div>
              <h4 className="text-xs font-bold text-slate-900">
                Version-Controlled Skill Taxonomy ({dictStats.canonical_count} Canonical Technologies, {dictStats.aliases_count} Aliases)
              </h4>
              <p className="text-[11px] text-slate-500">
                Configured in <code className="font-mono bg-white px-1 py-0.5 rounded border border-slate-200">data/skill_aliases.json</code>
              </p>
            </div>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search canonical skills..."
                className="pl-8 pr-3 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-teal-500"
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5 mt-3 max-h-48 overflow-y-auto p-1">
            {filteredCanonical.map((canonical, i) => (
              <span
                key={i}
                className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 text-[11px] font-medium rounded-md shadow-2xs"
              >
                {canonical}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="mt-5 space-y-4">
          {/* Metric Stats Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
              <span className="text-[11px] text-slate-500 font-semibold uppercase">Raw Input Count</span>
              <div className="text-base font-bold text-slate-900 mt-0.5 font-mono">{result.original_count}</div>
            </div>

            <div className="p-3 bg-teal-50/60 border border-teal-200 rounded-xl">
              <span className="text-[11px] text-teal-700 font-semibold uppercase">Canonical Count</span>
              <div className="text-base font-bold text-teal-900 mt-0.5 font-mono">{result.normalized_count}</div>
            </div>

            <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-xl">
              <span className="text-[11px] text-amber-700 font-semibold uppercase">Duplicates Removed</span>
              <div className="text-base font-bold text-amber-900 mt-0.5 font-mono">{result.duplicates_removed.length}</div>
            </div>

            <div className="p-3 bg-indigo-50/60 border border-indigo-200 rounded-xl">
              <span className="text-[11px] text-indigo-700 font-semibold uppercase">Aliases Standardized</span>
              <div className="text-base font-bold text-indigo-900 mt-0.5 font-mono">{Object.keys(result.aliases_resolved).length}</div>
            </div>
          </div>

          {/* Normalized Output Badges */}
          <div className="p-4 bg-slate-50/60 border border-slate-200 rounded-xl">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200/60">
              <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Normalized Canonical Skill Set ({result.normalized_skills.length})
              </span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1 text-[11px] text-slate-600 hover:text-slate-900 font-medium transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 text-emerald-600" />
                    <span className="text-emerald-600 font-bold">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3" />
                    <span>Copy Skills</span>
                  </>
                )}
              </button>
            </div>

            <div className="flex flex-wrap gap-2 mt-2">
              {result.normalized_skills.map((skill, idx) => {
                const isUnrecognized = result.unrecognized_skills.includes(skill);
                return (
                  <span
                    key={idx}
                    className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-medium border shadow-2xs transition-all ${
                      isUnrecognized
                        ? 'bg-blue-50 text-blue-800 border-blue-200'
                        : 'bg-white text-slate-900 border-slate-200'
                    }`}
                  >
                    {isUnrecognized ? (
                      <span title="Preserved unknown skill">
                        <Info className="w-3 h-3 text-blue-500" />
                      </span>
                    ) : (
                      <Check className="w-3 h-3 text-teal-600" />
                    )}
                    {skill}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Resolved Aliases Mapping Table */}
          {Object.keys(result.aliases_resolved).length > 0 && (
            <div className="p-4 bg-white border border-slate-200 rounded-xl">
              <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <ArrowRight className="w-3.5 h-3.5 text-indigo-600" />
                Detected Aliases &amp; Canonical Resolutions
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                {Object.entries(result.aliases_resolved).map(([raw, canonical], i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200 text-xs"
                  >
                    <span className="font-mono text-slate-600 truncate max-w-[120px]">{raw}</span>
                    <ArrowRight className="w-3 h-3 text-slate-400 shrink-0 mx-1" />
                    <span className="font-semibold text-teal-800 font-mono">{canonical}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Preserved Unknown Skills */}
          {result.unrecognized_skills.length > 0 && (
            <div className="p-3 bg-blue-50/50 border border-blue-200 rounded-xl text-xs">
              <div className="flex items-center gap-1.5 font-bold text-blue-900 mb-1">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                Preserved Non-Dictionary Skills ({result.unrecognized_skills.length})
              </div>
              <p className="text-[11px] text-blue-700 mb-2">
                These technologies were safely retained with proper casing rather than dropped:
              </p>
              <div className="flex flex-wrap gap-1.5">
                {result.unrecognized_skills.map((usk, i) => (
                  <span key={i} className="px-2 py-0.5 bg-white border border-blue-200 text-blue-800 rounded font-mono text-[11px]">
                    {usk}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Technology Collision Guard Verification */}
          <div className="p-3 bg-emerald-50/60 border border-emerald-200 rounded-xl flex items-start gap-2.5 text-xs text-emerald-900">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Collision Guards Active:</span>
              <p className="text-[11px] text-emerald-800 mt-0.5">
                Strict boundaries prevent accidental mergers of similar names (e.g. <code>Java</code> is never merged with <code>JavaScript</code>, <code>C</code> is separated from <code>C++</code> and <code>C#</code>, and <code>SQL</code> is kept distinct from <code>NoSQL</code>).
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
