import React, { useState } from 'react';
import {
  FileText,
  Calendar,
  Layers,
  Download,
  Printer,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  Share2,
  Copy,
  Check,
} from 'lucide-react';

export interface ResumeHeaderProps {
  candidateName?: string | null;
  summary?: string | null;
  objective?: string | null;
  originalFilename?: string | null;
  status?: string | null;
  extractionMethod?: string | null;
  rawTextCharCount?: number | null;
  createdAt?: string | null;
  onExportJson?: () => void;
  onPrint?: () => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export const ResumeHeader: React.FC<ResumeHeaderProps> = ({
  candidateName,
  summary,
  objective,
  originalFilename,
  status = 'completed',
  extractionMethod,
  rawTextCharCount,
  createdAt,
  onExportJson,
  onPrint,
  onRefresh,
  isRefreshing = false,
}) => {
  const [copied, setCopied] = useState(false);

  const formattedDate = createdAt
    ? new Date(createdAt).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  const displayName = candidateName || 'Candidate Resume';

  const handleCopySummary = () => {
    const textToCopy = summary || objective || displayName;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = () => {
    const st = (status || '').toLowerCase();
    if (st === 'completed' || st === 'processed') {
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-emerald-800 bg-emerald-50 border border-emerald-200/80 rounded-full"
          role="status"
          aria-label="Processing status: Completed"
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
          Completed
        </span>
      );
    }
    if (st === 'processing') {
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-blue-800 bg-blue-50 border border-blue-200/80 rounded-full"
          role="status"
          aria-label="Processing status: In progress"
        >
          <RefreshCw className="w-3.5 h-3.5 text-blue-600 animate-spin" aria-hidden="true" />
          Processing
        </span>
      );
    }
    if (st === 'failed') {
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-rose-800 bg-rose-50 border border-rose-200/80 rounded-full"
          role="status"
          aria-label="Processing status: Failed"
        >
          <AlertCircle className="w-3.5 h-3.5 text-rose-600" aria-hidden="true" />
          Failed
        </span>
      );
    }
    return (
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium text-slate-700 bg-slate-100 border border-slate-200 rounded-full"
        role="status"
      >
        <Clock className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
        {status || 'Uploaded'}
      </span>
    );
  };

  return (
    <header className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 md:p-8">
      {/* Top Metadata Row & Action Buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-100 gap-4">
        {/* Left: Document info */}
        <div className="flex items-center flex-wrap gap-2 text-xs text-slate-500">
          {getStatusBadge()}

          {originalFilename && (
            <>
              <span aria-hidden="true" className="text-slate-300">·</span>
              <span className="inline-flex items-center gap-1 font-mono text-slate-600">
                <FileText className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                <span className="truncate max-w-[200px]" title={originalFilename}>
                  {originalFilename}
                </span>
              </span>
            </>
          )}

          {extractionMethod && (
            <>
              <span aria-hidden="true" className="text-slate-300">·</span>
              <span className="capitalize text-slate-600">
                {extractionMethod.replace('_', ' ')}
              </span>
            </>
          )}

          {rawTextCharCount ? (
            <>
              <span aria-hidden="true" className="text-slate-300">·</span>
              <span className="font-mono text-slate-600">
                {rawTextCharCount.toLocaleString()} chars
              </span>
            </>
          ) : null}

          {formattedDate && (
            <>
              <span aria-hidden="true" className="text-slate-300">·</span>
              <span className="inline-flex items-center gap-1 text-slate-500">
                <Calendar className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                {formattedDate}
              </span>
            </>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2 flex-wrap">
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              disabled={isRefreshing}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 rounded-lg shadow-2xs transition-colors disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-emerald-600"
              title="Refresh resume data"
              aria-label="Refresh resume data"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
              <span>Refresh</span>
            </button>
          )}

          {onExportJson && (
            <button
              type="button"
              onClick={onExportJson}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 rounded-lg shadow-2xs transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600"
              title="Export resume as JSON"
              aria-label="Export resume as JSON"
            >
              <Download className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
              <span>Export JSON</span>
            </button>
          )}

          {onPrint && (
            <button
              type="button"
              onClick={onPrint}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 active:bg-slate-100 border border-slate-200 rounded-lg shadow-2xs transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600"
              title="Print resume preview"
              aria-label="Print resume preview"
            >
              <Printer className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
              <span>Print</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Candidate Heading & Summary */}
      <div className="mt-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
              {displayName}
            </h1>
            <p className="text-xs uppercase tracking-wider font-semibold text-emerald-700 mt-1">
              Parsed &amp; Validated Resume Document
            </p>
          </div>

          {(summary || objective) && (
            <button
              type="button"
              onClick={handleCopySummary}
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-emerald-600"
              title="Copy professional summary"
              aria-label="Copy professional summary"
            >
              {copied ? (
                <Check className="w-4 h-4 text-emerald-600" aria-hidden="true" />
              ) : (
                <Copy className="w-4 h-4" aria-hidden="true" />
              )}
            </button>
          )}
        </div>

        {/* Summary or Objective */}
        {summary ? (
          <div className="mt-4 p-4 rounded-xl bg-slate-50/80 border border-slate-200/60 text-slate-700 text-sm leading-relaxed">
            <span className="font-semibold text-slate-900 block mb-1 text-xs uppercase tracking-wider text-slate-500">
              Professional Summary
            </span>
            <p>{summary}</p>
          </div>
        ) : objective ? (
          <div className="mt-4 p-4 rounded-xl bg-slate-50/80 border border-slate-200/60 text-slate-700 text-sm leading-relaxed">
            <span className="font-semibold text-slate-900 block mb-1 text-xs uppercase tracking-wider text-slate-500">
              Career Objective
            </span>
            <p>{objective}</p>
          </div>
        ) : null}
      </div>
    </header>
  );
};
