import React, { useState } from 'react';
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  FileText,
  BarChart3,
  RefreshCw,
  Search,
  BookOpen,
  Target,
  ListOrdered,
  Layers,
  HelpCircle,
} from 'lucide-react';
import { ResumeAnalysisResponse } from '../types/analysis';
import { StructuredResume } from '../types/resume';
import { analyzeResume } from '../services/api';

interface ResumeAnalysisViewerProps {
  structuredResume?: StructuredResume | null;
  resumeText?: string | null;
  resumeId?: string | null;
}

export const ResumeAnalysisViewer: React.FC<ResumeAnalysisViewerProps> = ({
  structuredResume,
  resumeText,
  resumeId,
}) => {
  const [analysis, setAnalysis] = useState<ResumeAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'criteria' | 'factual'>('overview');

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload: { resume?: any; text?: string; resume_id?: string } = {};
      if (structuredResume) {
        payload.resume = structuredResume;
      } else if (resumeId) {
        payload.resume_id = resumeId;
      } else if (resumeText && resumeText.trim()) {
        payload.text = resumeText;
      } else {
        throw new Error('Please upload or parse a resume first to evaluate quality.');
      }

      const result = await analyzeResume(payload);
      setAnalysis(result);
    } catch (err: any) {
      setError(err?.message || 'Failed to analyze resume quality');
    } finally {
      setLoading(false);
    }
  };

  const getScoreBadge = (score?: number | null) => {
    if (score == null) return null;
    let color = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    if (score < 6) {
      color = 'bg-rose-50 text-rose-700 border-rose-200';
    } else if (score < 8) {
      color = 'bg-amber-50 text-amber-700 border-amber-200';
    }
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${color}`}>
        {score.toFixed(1)} / 10
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
              <Sparkles className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-bold text-slate-800">
              Phase 17: AI Resume Quality Analysis
            </h2>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Evaluates clarity, section completeness, bullet-point quality, measurable achievements,
            skill organization, project depth, and formatting.
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={loading || (!structuredResume && !resumeText && !resumeId)}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white font-medium rounded-lg shadow-sm transition-all text-sm cursor-pointer disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Analyzing Quality...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>{analysis ? 'Re-Analyze Resume' : 'Analyze Resume Quality'}</span>
            </>
          )}
        </button>
      </div>

      {/* Anti-Hallucination Disclaimer Banner */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs text-slate-600 flex items-start gap-2">
        <BookOpen className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-slate-700 font-semibold">Strict Anti-Hallucination Guardrail:</strong>{' '}
          This analysis service never fabricates achievements, invents metrics, or writes fake facts.
          Factual extraction (detected metrics, sections, contact details) is strictly isolated from
          subjective advice. Every recommendation is grounded solely in the candidate's actual resume content.
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 text-sm text-rose-700 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold">Analysis Encountered an Issue</div>
            <div className="text-rose-600 text-xs mt-0.5">{error}</div>
          </div>
        </div>
      )}

      {/* No analysis yet */}
      {!analysis && !loading && (
        <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50/50">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-700">No Quality Analysis Performed Yet</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto mt-1 mb-4">
            Upload or select a resume and click "Analyze Resume Quality" to inspect its strengths,
            areas for improvement, and actionable suggestions.
          </p>
          <button
            onClick={handleRunAnalysis}
            disabled={!structuredResume && !resumeText && !resumeId}
            className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            Analyze Current Resume
          </button>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && (
        <div className="space-y-6">
          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-200 gap-6 text-sm">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-3 font-medium transition-colors border-b-2 -mb-px cursor-pointer ${
                activeTab === 'overview'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Overview (Strengths & Areas)
            </button>
            <button
              onClick={() => setActiveTab('criteria')}
              className={`pb-3 font-medium transition-colors border-b-2 -mb-px cursor-pointer ${
                activeTab === 'criteria'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              8 Quality Criteria Breakdown
            </button>
            <button
              onClick={() => setActiveTab('factual')}
              className={`pb-3 font-medium transition-colors border-b-2 -mb-px cursor-pointer ${
                activeTab === 'factual'
                  ? 'border-indigo-600 text-indigo-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              Factual Extraction Audit
            </button>
          </div>

          {/* Tab 1: Overview */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Strengths */}
              <div className="bg-emerald-50/50 border border-emerald-200/80 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Strengths ({analysis.strengths?.length || 0})</span>
                </div>
                <div className="space-y-2">
                  {analysis.strengths?.map((str, idx) => (
                    <div
                      key={idx}
                      className="bg-white p-3 rounded-lg border border-emerald-100 shadow-xs text-xs text-slate-700 leading-relaxed"
                    >
                      {str}
                    </div>
                  ))}
                  {(!analysis.strengths || analysis.strengths.length === 0) && (
                    <div className="text-xs text-slate-400 italic">No specific strengths identified.</div>
                  )}
                </div>
              </div>

              {/* Areas for Improvement */}
              <div className="bg-amber-50/50 border border-amber-200/80 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-amber-800 font-bold text-sm">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>Areas for Improvement ({analysis.areas_for_improvement?.length || 0})</span>
                </div>
                <div className="space-y-2">
                  {analysis.areas_for_improvement?.map((area, idx) => (
                    <div
                      key={idx}
                      className="bg-white p-3 rounded-lg border border-amber-100 shadow-xs text-xs text-slate-700 leading-relaxed"
                    >
                      {area}
                    </div>
                  ))}
                  {(!analysis.areas_for_improvement || analysis.areas_for_improvement.length === 0) && (
                    <div className="text-xs text-slate-400 italic">No critical areas for improvement flagged.</div>
                  )}
                </div>
              </div>

              {/* Suggestions */}
              <div className="bg-indigo-50/50 border border-indigo-200/80 rounded-xl p-5 space-y-3">
                <div className="flex items-center gap-2 text-indigo-800 font-bold text-sm">
                  <Lightbulb className="w-4 h-4 text-indigo-600 shrink-0" />
                  <span>Suggestions ({analysis.suggestions?.length || 0})</span>
                </div>
                <div className="space-y-2">
                  {analysis.suggestions?.map((sug, idx) => (
                    <div
                      key={idx}
                      className="bg-white p-3 rounded-lg border border-indigo-100 shadow-xs text-xs text-slate-700 leading-relaxed"
                    >
                      {sug}
                    </div>
                  ))}
                  {(!analysis.suggestions || analysis.suggestions.length === 0) && (
                    <div className="text-xs text-slate-400 italic">No suggestions provided.</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: 8 Quality Criteria Breakdown */}
          {activeTab === 'criteria' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {analysis.criteria_evaluations &&
                  Object.entries(analysis.criteria_evaluations).map(([key, item]) => (
                    <div
                      key={key}
                      className="border border-slate-200 rounded-xl p-4 bg-slate-50/30 space-y-2.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm text-slate-800 capitalize">
                          {key.replace(/_/g, ' ')}
                        </span>
                        {getScoreBadge(item.score)}
                      </div>
                      <div className="space-y-1.5">
                        {item.observations?.map((obs, oIdx) => (
                          <div key={oIdx} className="text-xs text-slate-600 flex items-start gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0 mt-1.5" />
                            <span>{obs}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Tab 3: Factual Extraction Audit */}
          {activeTab === 'factual' && (
            <div className="bg-slate-50 rounded-xl p-5 border border-slate-200 space-y-4">
              <div className="flex items-center gap-2 font-semibold text-sm text-slate-700">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                <span>Deterministic Evidence Isolated from Subjective Analysis</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div className="bg-white p-3 rounded-lg border border-slate-200">
                  <div className="text-slate-400 font-medium">Sections Detected</div>
                  <div className="text-slate-800 font-bold mt-1">
                    {analysis.factual_summary?.sections_present?.length || 0}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    {analysis.factual_summary?.sections_present?.join(', ') || 'None'}
                  </div>
                </div>

                <div className="bg-white p-3 rounded-lg border border-slate-200">
                  <div className="text-slate-400 font-medium">Experience Roles</div>
                  <div className="text-slate-800 font-bold mt-1">
                    {analysis.factual_summary?.total_experience_entries || 0}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    {analysis.factual_summary?.bullet_points_count || 0} total bullet points
                  </div>
                </div>

                <div className="bg-white p-3 rounded-lg border border-slate-200">
                  <div className="text-slate-400 font-medium">Documented Skills</div>
                  <div className="text-slate-800 font-bold mt-1">
                    {analysis.factual_summary?.total_skills_count || 0}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Across classified groups</div>
                </div>

                <div className="bg-white p-3 rounded-lg border border-slate-200">
                  <div className="text-slate-400 font-medium">Contact Complete</div>
                  <div className="text-slate-800 font-bold mt-1">
                    {analysis.factual_summary?.has_contact_email && analysis.factual_summary?.has_contact_phone
                      ? 'Email & Phone Present'
                      : 'Partial / Incomplete'}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    LinkedIn: {analysis.factual_summary?.has_linkedin ? 'Yes' : 'No'} | GitHub:{' '}
                    {analysis.factual_summary?.has_github ? 'Yes' : 'No'}
                  </div>
                </div>
              </div>

              {/* Measurable Metrics Highlight */}
              {analysis.factual_summary?.measurable_metrics_detected &&
                analysis.factual_summary.measurable_metrics_detected.length > 0 && (
                  <div className="bg-white p-3.5 rounded-lg border border-slate-200 space-y-1.5">
                    <div className="text-xs font-semibold text-slate-700">
                      Actual Measurable Metrics Detected in Text:
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.factual_summary.measurable_metrics_detected.map((met, mIdx) => (
                        <span
                          key={mIdx}
                          className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded text-xs font-medium border border-indigo-100"
                        >
                          {met}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          )}

          {/* Audit Footer */}
          <div className="flex flex-wrap items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 pt-3 gap-2">
            <div>
              LLM Provider: <span className="font-medium text-slate-600">{analysis.llm_provider || 'N/A'}</span> (Model:{' '}
              <span className="font-medium text-slate-600">{analysis.llm_model || 'N/A'}</span>)
            </div>
            {analysis.analysis_duration_ms && (
              <div>Evaluation Latency: {analysis.analysis_duration_ms.toFixed(0)}ms</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
