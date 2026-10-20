import React, { useState } from 'react';
import {
  FileText,
  Copy,
  Check,
  RotateCw,
  Layers,
  Sparkles,
  AlignLeft,
  FileCode,
  AlertTriangle,
  ScanText,
  Cpu,
  CheckCircle2,
  Wand2,
  ShieldCheck,
} from 'lucide-react';
import { ResumeExtractTextResponse, ExtractionStatus } from '../types/resume';
import { extractResumeText } from '../services/resumeService';

interface TextExtractionViewerProps {
  resumeId: string;
  originalFilename: string;
  onExtracted?: (result: ResumeExtractTextResponse) => void;
}

export const TextExtractionViewer: React.FC<TextExtractionViewerProps> = ({
  resumeId,
  originalFilename,
  onExtracted,
}) => {
  const [status, setStatus] = useState<ExtractionStatus>('idle');
  const [data, setData] = useState<ResumeExtractTextResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const handleExtract = async () => {
    setStatus('extracting');
    setError(null);
    try {
      const result = await extractResumeText(resumeId);
      setData(result);
      setStatus('success');
      if (onExtracted) {
        onExtracted(result);
      }
    } catch (err: unknown) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to extract text from resume.');
    }
  };

  const handleCopy = async () => {
    if (!data?.text) return;
    try {
      await navigator.clipboard.writeText(data.text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  const lineCount = data?.text ? data.text.split('\n').filter((l) => l.trim().length > 0).length : 0;
  const wordCount = data?.text ? data.text.trim().split(/\s+/).filter(Boolean).length : 0;

  const renderMethodBadge = (method?: string) => {
    switch (method) {
      case 'ocr':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200">
            <ScanText className="w-3.5 h-3.5 text-amber-700" />
            Tesseract OCR
          </span>
        );
      case 'mixed':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-800 border border-purple-200">
            <Cpu className="w-3.5 h-3.5 text-purple-700" />
            Hybrid (Native + OCR)
          </span>
        );
      case 'pdf_text':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
            Direct Native Text
          </span>
        );
    }
  };

  const formatTransformationName = (key: string): string => {
    switch (key) {
      case 'normalized_line_endings_and_control_chars':
        return 'Line Endings & Controls';
      case 'unicode_nfkc_normalization':
        return 'Unicode NFKC & Ligatures';
      case 'removed_page_number_artifacts':
        return 'Page Number Artifacts';
      case 'dehyphenated_linebreaks':
        return 'De-hyphenated Words';
      case 'standardized_bullets':
        return 'Standardized Bullets';
      case 'collapsed_inline_whitespace':
        return 'Collapsed Whitespace';
      case 'cleaned_punctuation_spacing':
        return 'Punctuation Spacing';
      case 'compacted_blank_lines':
        return 'Compacted Blank Lines';
      default:
        return key.replace(/_/g, ' ');
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8 mt-6">
      {/* Title bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold mb-2">
            <Wand2 className="w-3.5 h-3.5" />
            Phase 5: Deterministic Text Preprocessing
          </div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight">
            Cleaned Resume Text Content
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
              onClick={handleExtract}
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-xs transition-colors cursor-pointer"
            >
              <FileText className="w-4 h-4" />
              Extract &amp; Preprocess Text
            </button>
          ) : status === 'extracting' ? (
            <button
              type="button"
              disabled
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 text-indigo-500 text-sm font-semibold rounded-xl cursor-wait"
            >
              <RotateCw className="w-4 h-4 animate-spin" />
              Cleaning &amp; Normalizing...
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleCopy}
                disabled={!data?.text}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg shadow-2xs transition-colors cursor-pointer"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-slate-500" />
                    Copy Text
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleExtract}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200/70 rounded-lg transition-colors cursor-pointer"
              >
                <RotateCw className="w-3.5 h-3.5 text-slate-500" />
                Re-process
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Body Area */}
      <div className="mt-5">
        {status === 'idle' && (
          <div className="text-center py-10 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
            <AlignLeft className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <h4 className="text-sm font-semibold text-slate-700">Ready for Extraction &amp; Preprocessing</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              Click &quot;Extract &amp; Preprocess Text&quot; to run PyMuPDF/OCR followed by deterministic text normalization (ligature resolution, dehyphenation, bullet formatting).
            </p>
          </div>
        )}

        {status === 'extracting' && (
          <div className="text-center py-12 bg-indigo-50/30 rounded-xl border border-indigo-100">
            <RotateCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-indigo-950">Deterministic Preprocessing Pipeline</h4>
            <p className="text-xs text-indigo-700/80 mt-1">
              Extracting raw stream → Resolving Unicode ligatures → De-hyphenating line breaks → Standardizing bullets → Preserving all dates, numbers &amp; casing...
            </p>
          </div>
        )}

        {status === 'error' && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-sm text-rose-800 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="font-semibold text-rose-900">Text Extraction Error</h4>
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
          <div>
            {/* Extraction metadata bar */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4 text-xs">
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/70">
                <span className="text-slate-400 block font-medium">Pipeline Source</span>
                <div className="mt-1">
                  {renderMethodBadge(data.extraction_method)}
                </div>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/70">
                <span className="text-slate-400 block font-medium">Page Count</span>
                <span className="font-bold text-slate-800 text-sm flex items-center gap-1.5 mt-0.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-500" />
                  {data.page_count} {data.page_count === 1 ? 'Page' : 'Pages'}
                </span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/70">
                <span className="text-slate-400 block font-medium">Cleaned Chars</span>
                <span className="font-bold text-slate-800 text-sm mt-0.5 block">
                  {data.text.length.toLocaleString()}
                  {data.original_char_count && data.original_char_count > data.text.length && (
                    <span className="text-slate-400 text-[10px] font-normal block">
                      from {data.original_char_count.toLocaleString()} raw
                    </span>
                  )}
                </span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/70">
                <span className="text-slate-400 block font-medium">Total Words</span>
                <span className="font-bold text-slate-800 text-sm mt-0.5 block">
                  {wordCount.toLocaleString()}
                </span>
              </div>
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/70">
                <span className="text-slate-400 block font-medium">Normalized Lines</span>
                <span className="font-bold text-slate-800 text-sm mt-0.5 block">
                  {lineCount.toLocaleString()}
                </span>
              </div>
            </div>

            {/* Applied Transformations Chips */}
            {data.transformations_applied && data.transformations_applied.length > 0 && (
              <div className="mb-4 p-3 bg-slate-50/80 rounded-xl border border-slate-200/70 text-xs">
                <div className="flex items-center gap-1.5 font-semibold text-slate-700 mb-2">
                  <ShieldCheck className="w-4 h-4 text-indigo-600" />
                  <span>Applied Cleaning Operations:</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {data.transformations_applied.map((t) => (
                    <span
                      key={t}
                      className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600 text-[11px] font-medium shadow-2xs"
                    >
                      ✓ {formatTransformationName(t)}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted & Cleaned Text Box */}
            <div className="relative">
              <pre className="bg-slate-900 text-slate-100 rounded-xl p-4 sm:p-5 text-xs font-mono overflow-x-auto max-h-96 leading-relaxed selection:bg-indigo-500 selection:text-white whitespace-pre-wrap break-words">
                {data.text || '(No text extracted - document is blank or unreadable)'}
              </pre>
            </div>

            {/* Information Preservation Assurance Notice */}
            <div className="mt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] text-slate-500 gap-2">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 inline" />
                Information Preserved: Emails, URLs, dates, numbers, CGPAs, phone numbers &amp; casing intact.
              </span>
              <span className="font-semibold text-slate-400">Deterministic pipeline • No LLM in Phase 5</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
