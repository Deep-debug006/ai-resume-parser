import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  Database,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Search,
  Sparkles,
  Layers,
  Code2,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Scan,
  ExternalLink,
} from 'lucide-react';
import { processResumeFile, getResumePipelineStatus } from '../services/api';
import { ResumeProcessResponse, ProcessingStatus } from '../types/pipeline';

const PIPELINE_STAGES = [
  { id: 1, label: 'Upload PDF', desc: 'MIME, size & magic bytes validation' },
  { id: 2, label: 'Extract Text', desc: 'PyMuPDF native text stream' },
  { id: 3, label: 'OCR Fallback', desc: 'Tesseract OCR fallback if scanned' },
  { id: 4, label: 'Clean Text', desc: 'Whitespace, ligatures & dehyphenation' },
  { id: 5, label: 'Detect Sections', desc: 'Canonical resume section boundary detection' },
  { id: 6, label: 'NLP Anchors', desc: 'spaCy entities (PERSON, ORG, LOC, DATE)' },
  { id: 7, label: 'LLM Extraction', desc: 'Provider abstraction & prompt grounding' },
  { id: 8, label: 'Pydantic Validation', desc: 'Anti-hallucination & repair loop' },
  { id: 9, label: 'Skill Normalization', desc: 'Taxonomy mapping & alias deduplication' },
  { id: 10, label: 'PostgreSQL Persistence', desc: 'Normalized relational storage' },
];

export const ResumePipelineViewer: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStep, setActiveStep] = useState<number>(0);
  const [result, setResult] = useState<ResumeProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState(false);
  const [showJson, setShowJson] = useState(false);
  const [statusLookupId, setStatusLookupId] = useState('');
  const [statusLookupResult, setStatusLookupResult] = useState<any>(null);
  const [isLookingUpStatus, setIsLookingUpStatus] = useState(false);

  // Generate synthetic sample PDF for immediate browser testing
  const createSampleFile = (name: string, contentText: string): File => {
    // Generate simple PDF format stream
    const header = "%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n";
    const pages = "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n";
    const textStream = `BT /F1 12 Tf 50 700 Td (${contentText.replace(/[\n\r]+/g, ' ')}) Tj ET`;
    const page = `3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n`;
    const contents = `4 0 obj\n<< /Length ${textStream.length} >>\nstream\n${textStream}\nendstream\nendobj\n`;
    const font = `5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n`;
    const xref = `xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000118 00000 n \n0000000234 00000 n \n0000000300 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n370\n%%EOF`;
    const rawPdf = header + pages + page + contents + font + xref;
    const blob = new Blob([rawPdf], { type: 'application/pdf' });
    return new File([blob], name, { type: 'application/pdf' });
  };

  const handleSelectSample = (formatType: 'swe' | 'ai' | 'exec') => {
    if (formatType === 'swe') {
      const file = createSampleFile(
        'Jordan_Smith_Software_Engineer.pdf',
        'JORDAN SMITH | jordan.smith@devmail.org | (555) 234-5678 | Seattle, WA\n\nSUMMARY: Backend Engineer with 5 years experience in distributed systems.\n\nEXPERIENCE:\nCloudScale Systems - Software Engineer (Jan 2021 - Present)\nDesigned high-throughput data processing microservices handling 15,000 req/sec using FastAPI and PostgreSQL.\n\nEDUCATION:\nUniversity of Washington - B.S. Computer Science (2015 - 2019)\n\nSKILLS:\nPython, JS, Go, SQL, Docker, K8s, Postgres, Redis'
      );
      setSelectedFile(file);
    } else if (formatType === 'ai') {
      const file = createSampleFile(
        'Dr_Elena_Rostova_AI_Researcher.pdf',
        'DR. ELENA ROSTOVA | elena.rostova@ailab.edu | +1-415-990-1122 | San Francisco, CA\n\nOBJECTIVE: Principal Machine Learning Researcher deploying state-of-the-art transformers.\n\nEDUCATION:\nStanford University - Ph.D. Computer Science AI (2017 - 2021) GPA: 3.96\nCarnegie Mellon - B.S. Mathematics & CS (2013 - 2017)\n\nEXPERIENCE:\nDeepThought AI - Senior Research Scientist (2021 - Present)\nTrained 7B parameter foundation models.\n\nSKILLS:\nPyTorch, TensorFlow, Scikit-Learn, Transformers, MongoDB, VectorDB, AWS'
      );
      setSelectedFile(file);
    } else {
      const file = createSampleFile(
        'Marcus_Aurelius_VP_Engineering.pdf',
        'MARCUS V. AURELIUS | marcus.aurelius@leadership.co | New York, NY\n\nSUMMARY: VP of Engineering with 16+ years scaling teams from Series A to IPO.\n\nEXPERIENCE:\nVanguard FinTech - VP Engineering (2019 - Present)\nScaled engineering department to 140 members.\n\nEDUCATION:\nMIT - M.S. Engineering Management\n\nCERTIFICATIONS:\nCISSP | (ISC)2'
      );
      setSelectedFile(file);
    }
    setResult(null);
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleRunPipeline = async () => {
    if (!selectedFile) {
      setError('Please choose or generate a PDF file first.');
      return;
    }

    setIsProcessing(true);
    setError(null);
    setActiveStep(1);

    // Simulate animated step progression through pipeline stages
    const stepInterval = setInterval(() => {
      setActiveStep((prev) => (prev < 9 ? prev + 1 : prev));
    }, 400);

    try {
      const res = await processResumeFile(selectedFile);
      clearInterval(stepInterval);
      setActiveStep(10);
      setResult(res);

      if (res.processing_status === 'failed') {
        setError(res.error || 'Pipeline execution marked as failed by server.');
      }
    } catch (err: any) {
      clearInterval(stepInterval);
      setError(err.message || 'Pipeline execution failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  const handleLookupStatus = async () => {
    if (!statusLookupId.trim()) return;
    setIsLookingUpStatus(true);
    setStatusLookupResult(null);
    try {
      const statusRes = await getResumePipelineStatus(statusLookupId.trim());
      setStatusLookupResult(statusRes);
    } catch (err: any) {
      setStatusLookupResult({ error: err.message || 'Not found' });
    } finally {
      setIsLookingUpStatus(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl text-slate-100">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="bg-emerald-500/10 text-emerald-400 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-emerald-500/20">
              Phase 12
            </span>
            <span className="text-xs text-slate-400 font-mono">POST /api/resumes/process</span>
          </div>
          <h2 className="text-xl font-bold flex items-center gap-2 text-white">
            <Cpu className="w-5 h-5 text-emerald-400" />
            Complete Resume Processing Pipeline
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            End-to-end orchestration connecting upload, PyMuPDF, OCR fallback, section detection, spaCy NLP, LLM extraction, Pydantic validation, skill normalization, and PostgreSQL persistence.
          </p>
        </div>

        {/* Quick sample buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-slate-400">Quick Samples:</span>
          <button
            onClick={() => handleSelectSample('swe')}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition"
          >
            Software Engineer
          </button>
          <button
            onClick={() => handleSelectSample('ai')}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition"
          >
            AI Researcher
          </button>
          <button
            onClick={() => handleSelectSample('exec')}
            className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition"
          >
            VP Engineering
          </button>
        </div>
      </div>

      {/* Pipeline Stages Diagram */}
      <div className="my-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          10-Stage Orchestrated Workflow
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {PIPELINE_STAGES.map((stg) => {
            const isCompleted = result && result.processing_status === 'completed';
            const isActive = isProcessing && activeStep === stg.id;
            const isPast = isProcessing && activeStep > stg.id;

            return (
              <div
                key={stg.id}
                className={`p-2.5 rounded-lg border text-left transition-all ${
                  isCompleted
                    ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
                    : isActive
                    ? 'bg-blue-950/40 border-blue-500/60 ring-2 ring-blue-500/20 text-blue-200'
                    : isPast
                    ? 'bg-slate-800/80 border-slate-700 text-slate-300'
                    : 'bg-slate-800/40 border-slate-800 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-mono opacity-70">0{stg.id}</span>
                  {isCompleted ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : isActive ? (
                    <RefreshCw className="w-3.5 h-3.5 text-blue-400 animate-spin" />
                  ) : null}
                </div>
                <div className="text-xs font-semibold truncate">{stg.label}</div>
                <div className="text-[10px] opacity-75 truncate">{stg.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Upload & Action Area */}
      <div className="bg-slate-800/50 border border-slate-700/60 rounded-xl p-5 mb-6">
        <div className="flex flex-col md:flex-row items-center gap-4">
          <div className="flex-1 w-full">
            <label className="block text-xs font-medium text-slate-400 mb-2">
              Select or Drop PDF Resume Document:
            </label>
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-600 cursor-pointer text-sm font-medium transition">
                <Upload className="w-4 h-4 text-emerald-400" />
                <span>Browse PDF</span>
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              <div className="flex-1 truncate text-sm text-slate-300 bg-slate-900/80 px-3 py-2 rounded-lg border border-slate-800 font-mono">
                {selectedFile ? selectedFile.name : 'No file selected yet'}
              </div>
            </div>
          </div>

          <div className="w-full md:w-auto flex items-end">
            <button
              onClick={handleRunPipeline}
              disabled={!selectedFile || isProcessing}
              className={`w-full md:w-auto px-6 py-2.5 rounded-lg font-semibold flex items-center justify-center gap-2 text-sm shadow-md transition ${
                !selectedFile || isProcessing
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30'
              }`}
            >
              {isProcessing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Orchestrating...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Execute Full Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-950/40 border border-red-500/30 rounded-lg flex items-start gap-2.5 text-red-300 text-xs">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Pipeline Execution Error:</span> {error}
            </div>
          </div>
        )}
      </div>

      {/* Execution Results View */}
      {result && (
        <div className="space-y-6">
          {/* Status summary banner */}
          <div
            className={`p-4 rounded-xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
              result.processing_status === 'completed'
                ? 'bg-emerald-950/20 border-emerald-500/30'
                : 'bg-red-950/20 border-red-500/30'
            }`}
          >
            <div className="flex items-center gap-3">
              {result.processing_status === 'completed' ? (
                <div className="w-10 h-10 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
              ) : (
                <div className="w-10 h-10 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center text-red-400">
                  <AlertCircle className="w-5 h-5" />
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-base font-bold text-white">
                    {result.processing_status === 'completed'
                      ? 'Pipeline Completed & Persisted to PostgreSQL'
                      : 'Pipeline Execution Status: ' + result.processing_status}
                  </h4>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-semibold uppercase ${
                      result.processing_status === 'completed'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}
                  >
                    {result.processing_status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-0.5">
                  Original Document: <span className="text-slate-200 font-mono">{result.original_filename}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800 text-xs font-mono flex items-center gap-2">
                <span className="text-slate-500">ID:</span>
                <span className="text-emerald-400 font-bold">{result.resume_id}</span>
                <button
                  onClick={() => copyToClipboard(result.resume_id)}
                  className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
                  title="Copy resume_id"
                >
                  {copiedId ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            </div>
          </div>

          {/* Metric cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-xs">Extraction Technique</span>
              <div className="text-sm font-semibold text-white mt-1 capitalize flex items-center gap-1.5">
                <Scan className="w-3.5 h-3.5 text-blue-400" />
                {result.extraction_method || 'PyMuPDF Native'}
              </div>
            </div>

            <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-xs">Cleaned Text Size</span>
              <div className="text-sm font-semibold text-white mt-1 font-mono">
                {result.raw_text_char_count?.toLocaleString()} chars
              </div>
            </div>

            <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-xs">Sections Recognized</span>
              <div className="text-sm font-semibold text-white mt-1">
                {result.sections_detected?.length || 0} Canonical Sections
              </div>
            </div>

            <div className="bg-slate-800/40 p-3 rounded-lg border border-slate-800">
              <span className="text-slate-400 text-xs">End-to-End Latency</span>
              <div className="text-sm font-semibold text-emerald-400 mt-1 font-mono">
                {result.processing_duration_ms} ms
              </div>
            </div>
          </div>

          {/* Structured candidate information */}
          {result.resume && (
            <div className="bg-slate-800/30 border border-slate-700/60 rounded-xl p-5">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <FileCheck className="w-5 h-5 text-emerald-400" />
                  <h3 className="text-base font-bold text-white">
                    {result.resume.personal_info?.full_name || 'Structured Resume Record'}
                  </h3>
                </div>
                <button
                  onClick={() => setShowJson(!showJson)}
                  className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 flex items-center gap-1.5"
                >
                  <Code2 className="w-3.5 h-3.5 text-blue-400" />
                  <span>{showJson ? 'Hide JSON' : 'Inspect Database JSON'}</span>
                  {showJson ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                </button>
              </div>

              {/* Personal info contact row */}
              <div className="flex flex-wrap gap-4 text-xs text-slate-300 pb-4 border-b border-slate-800">
                {result.resume.personal_info?.email && (
                  <div>
                    <span className="text-slate-500">Email:</span>{' '}
                    <span className="text-white font-medium">{result.resume.personal_info.email}</span>
                  </div>
                )}
                {result.resume.personal_info?.phone && (
                  <div>
                    <span className="text-slate-500">Phone:</span>{' '}
                    <span className="text-white font-medium">{result.resume.personal_info.phone}</span>
                  </div>
                )}
                {result.resume.personal_info?.location && (
                  <div>
                    <span className="text-slate-500">Location:</span>{' '}
                    <span className="text-white font-medium">{result.resume.personal_info.location}</span>
                  </div>
                )}
              </div>

              {/* Normalized Skills Badges */}
              {result.resume.skills && (
                <div className="mt-4">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 block">
                    Normalized & Deduplicated Skills (Phase 10 & 11)
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(result.resume.skills).flatMap(([cat, skills]) =>
                      (Array.isArray(skills) ? skills : []).map((sk: string, i: number) => (
                        <span
                          key={`${cat}-${sk}-${i}`}
                          className="px-2 py-0.5 bg-emerald-950/40 text-emerald-300 border border-emerald-500/30 rounded text-xs"
                        >
                          {sk}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              )}

              {/* Experience and Education breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5">
                {/* Experience */}
                <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                    Experience Records ({result.resume.experience?.length || 0})
                  </span>
                  {result.resume.experience && result.resume.experience.length > 0 ? (
                    <div className="space-y-3">
                      {result.resume.experience.map((exp: any, idx: number) => (
                        <div key={idx} className="border-l-2 border-emerald-500/50 pl-2.5 py-0.5">
                          <div className="text-xs font-semibold text-white">{exp.title}</div>
                          <div className="text-[11px] text-slate-400">{exp.company} | {exp.location || 'Remote'}</div>
                          {exp.highlights && exp.highlights[0] && (
                            <div className="text-[11px] text-slate-300 mt-1 line-clamp-2">
                              • {exp.highlights[0]}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500">No experience records extracted.</div>
                  )}
                </div>

                {/* Education */}
                <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                    Education Records ({result.resume.education?.length || 0})
                  </span>
                  {result.resume.education && result.resume.education.length > 0 ? (
                    <div className="space-y-3">
                      {result.resume.education.map((edu: any, idx: number) => (
                        <div key={idx} className="border-l-2 border-blue-500/50 pl-2.5 py-0.5">
                          <div className="text-xs font-semibold text-white">{edu.institution}</div>
                          <div className="text-[11px] text-slate-400">
                            {edu.degree} {edu.field_of_study ? `in ${edu.field_of_study}` : ''}
                          </div>
                          {edu.gpa && (
                            <div className="text-[11px] text-emerald-400 mt-0.5 font-mono">
                              GPA: {edu.gpa} / {edu.gpa_max || 4.0}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-slate-500">No education records extracted.</div>
                  )}
                </div>
              </div>

              {/* JSON preview */}
              {showJson && (
                <div className="mt-4 pt-4 border-t border-slate-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-slate-400 font-mono">PostgreSQL Stored Entity JSON:</span>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(result, null, 2))}
                      className="text-xs text-slate-400 hover:text-white flex items-center gap-1"
                    >
                      <Copy className="w-3 h-3" />
                      <span>Copy Full JSON</span>
                    </button>
                  </div>
                  <pre className="bg-slate-950 p-3 rounded-lg text-xs font-mono text-emerald-400 overflow-x-auto max-h-80 border border-slate-800">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Lifecycle Status Inspector tool */}
      <div className="mt-8 pt-6 border-t border-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          Resume Lifecycle Status Inspector
        </h3>
        <p className="text-xs text-slate-400 mb-3">
          Check live database processing status (<code className="text-emerald-400">uploaded</code>, <code className="text-blue-400">processing</code>, <code className="text-emerald-400">completed</code>, <code className="text-red-400">failed</code>) for any resume UUID.
        </p>

        <div className="flex gap-2 max-w-lg">
          <input
            type="text"
            placeholder="Enter Resume UUID..."
            value={statusLookupId}
            onChange={(e) => setStatusLookupId(e.target.value)}
            className="flex-1 bg-slate-900 border border-slate-700 px-3 py-1.5 rounded-lg text-xs text-slate-200 font-mono focus:outline-none focus:border-emerald-500"
          />
          <button
            onClick={handleLookupStatus}
            disabled={isLookingUpStatus || !statusLookupId.trim()}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs rounded-lg border border-slate-700 transition flex items-center gap-1.5 disabled:opacity-50"
          >
            {isLookingUpStatus ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
            <span>Lookup</span>
          </button>
        </div>

        {statusLookupResult && (
          <div className="mt-3 p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono">
            {statusLookupResult.error ? (
              <span className="text-red-400">{statusLookupResult.error}</span>
            ) : (
              <div className="space-y-1 text-slate-300">
                <div>Status: <span className="text-emerald-400 font-bold uppercase">{statusLookupResult.processing_status}</span></div>
                <div>Filename: <span className="text-white">{statusLookupResult.original_filename}</span></div>
                <div>Extraction: <span className="text-white">{statusLookupResult.extraction_method || 'none'}</span></div>
                <div>Created: <span className="text-slate-400">{statusLookupResult.created_at}</span></div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
