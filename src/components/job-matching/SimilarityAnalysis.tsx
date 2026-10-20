import React, { useState } from 'react';
import {
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
  Cpu,
  Info,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { SemanticMatchResult, RequirementSemanticMatch } from '../../types/semantic';

interface SimilarityAnalysisProps {
  semanticResult?: SemanticMatchResult | null;
  isLoading?: boolean;
}

export const SimilarityAnalysis: React.FC<SimilarityAnalysisProps> = ({
  semanticResult,
  isLoading,
}) => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center space-y-3">
        <div className="w-8 h-8 border-3 border-slate-900 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm font-semibold text-slate-800">Generating dense embeddings & computing cosine similarities...</p>
        <p className="text-xs text-slate-500">Vectorizing resume sections and comparing with 768-dimensional job criteria</p>
      </div>
    );
  }

  if (!semanticResult) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 text-center text-slate-500 space-y-2">
        <Sparkles className="w-6 h-6 mx-auto text-slate-400" />
        <p className="text-sm font-medium text-slate-700">Semantic Embedding Analysis Not Generated</p>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          Run the full job match analysis to compute dense vector embeddings and semantic similarity scores.
        </p>
      </div>
    );
  }

  const overallScore = Math.round(semanticResult.overall_semantic_similarity * 100);
  const expScore = Math.round(semanticResult.experience_semantic_alignment * 100);
  const summaryScore = semanticResult.summary_similarity !== null
    ? Math.round(semanticResult.summary_similarity * 100)
    : null;

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case 'strong_alignment':
        return { label: 'Strong Alignment', color: 'text-emerald-800 bg-emerald-50 border-emerald-200' };
      case 'moderate_alignment':
        return { label: 'Moderate Alignment', color: 'text-blue-800 bg-blue-50 border-blue-200' };
      default:
        return { label: 'Minimal Alignment', color: 'text-slate-700 bg-slate-100 border-slate-200' };
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            Dense Embedding Semantic Similarity
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Vectorized cosine similarity using 768-dimensional dense representations ({semanticResult.model_name}).
          </p>
        </div>

        {/* Model Spec */}
        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5">
          <Cpu className="w-3.5 h-3.5 text-slate-600" />
          <span className="font-mono text-slate-700">{semanticResult.model_name}</span>
          <span aria-hidden="true">·</span>
          <span>{semanticResult.vector_dimension}d vectors</span>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Overall Semantic Alignment */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
            Overall Similarity
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900">{overallScore}%</span>
            <span className="text-xs text-slate-500">dense vector match</span>
          </div>
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                overallScore >= 75 ? 'bg-emerald-600' : overallScore >= 55 ? 'bg-indigo-600' : 'bg-slate-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, overallScore))}%` }}
            />
          </div>
        </div>

        {/* Experience Semantic Alignment */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
            Experience Alignment
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900">{expScore}%</span>
            <span className="text-xs text-slate-500">work history match</span>
          </div>
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-indigo-600 transition-all duration-500"
              style={{ width: `${Math.min(100, Math.max(0, expScore))}%` }}
            />
          </div>
        </div>

        {/* Summary Alignment */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/90 space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">
            Summary / Objective
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-900">
              {summaryScore !== null ? `${summaryScore}%` : 'N/A'}
            </span>
            <span className="text-xs text-slate-500">profile statement</span>
          </div>
          <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full bg-slate-600 transition-all duration-500"
              style={{ width: `${summaryScore !== null ? Math.min(100, Math.max(0, summaryScore)) : 0}%` }}
            />
          </div>
        </div>
      </div>

      {/* Semantic Insights Text */}
      {semanticResult.semantic_insights && (
        <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-100 text-xs text-indigo-950 space-y-1">
          <div className="flex items-center gap-1.5 font-semibold text-indigo-900">
            <Info className="w-3.5 h-3.5 text-indigo-600" />
            <span>Semantic Context Insights</span>
          </div>
          <p className="leading-relaxed text-indigo-900/90">{semanticResult.semantic_insights}</p>
        </div>
      )}

      {/* Requirement-by-Requirement Semantic Breakdown */}
      {semanticResult.requirement_matches && semanticResult.requirement_matches.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-slate-700" />
              Requirement Vector Alignments ({semanticResult.requirement_matches.length})
            </h4>
            <span className="text-xs text-slate-500">
              Evaluates contextual alignment beyond exact keyword matches
            </span>
          </div>

          <div className="space-y-2">
            {semanticResult.requirement_matches.map((item, idx) => {
              const scorePct = Math.round(item.similarity_score * 100);
              const tierInfo = getTierBadge(item.relevance_tier);
              const isExpanded = expandedIndex === idx;

              return (
                <div
                  key={idx}
                  className="rounded-lg border border-slate-200 hover:border-slate-300 transition-all bg-white overflow-hidden text-xs"
                >
                  <div
                    onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    className="p-3 flex items-center justify-between gap-3 cursor-pointer hover:bg-slate-50/70"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-slate-900 truncate">
                        {item.requirement}
                      </p>
                      <div className="flex items-center gap-2 text-slate-500 text-[11px] mt-0.5">
                        <span>Source: {item.source_type || 'Experience'}</span>
                        <span aria-hidden="true">·</span>
                        <span className="font-mono">{scorePct}% cosine similarity</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-[11px] font-medium border px-2 py-0.5 rounded ${tierInfo.color}`}>
                        {tierInfo.label}
                      </span>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="p-3 bg-slate-50 border-t border-slate-100 space-y-2">
                      <div>
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block mb-1">
                          Closest Resume Evidence:
                        </span>
                        <blockquote className="italic text-slate-700 bg-white p-2.5 rounded border border-slate-200 text-xs leading-relaxed">
                          "{item.best_matching_resume_chunk || 'No detailed evidence chunk isolated.'}"
                        </blockquote>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Exact vs Semantic Disclaimer */}
      <div className="text-[11px] text-slate-500 border-t border-slate-100 pt-3 flex items-start gap-2">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
        <p>
          Semantic similarity measures linguistic and domain proximity between resume experiences and job requirements. Unlike keyword matching, it credits conceptually related technologies and responsibilities.
        </p>
      </div>
    </div>
  );
};
