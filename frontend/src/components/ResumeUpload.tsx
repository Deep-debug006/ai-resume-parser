import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import {
  UploadCloud,
  FileCheck2,
  AlertCircle,
  CheckCircle2,
  FileText,
  RotateCcw,
  ShieldCheck,
  HardDrive,
  FileWarning,
  Sparkles,
} from 'lucide-react';
import { ResumeUploadResponse, UploadStatus, UploadError } from '../types/resume';
import { uploadResumeFile, generateSampleResumePdf } from '../services/resumeService';

interface ResumeUploadProps {
  onUploadSuccess?: (result: ResumeUploadResponse) => void;
}

export const ResumeUpload: React.FC<ResumeUploadProps> = ({ onUploadSuccess }) => {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<UploadError | null>(null);
  const [successData, setSuccessData] = useState<ResumeUploadResponse | null>(null);
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle Drag Events
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (status !== 'uploading') {
      setStatus('dragging');
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (status === 'dragging') {
      setStatus('idle');
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (status === 'uploading') return;

    setStatus('idle');
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      processUpload(files[0]);
    }
  };

  // Handle Browse Click
  const handleBrowseClick = () => {
    if (status === 'uploading') return;
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      processUpload(files[0]);
    }
    // Reset file input value to allow selecting same file again if retrying
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Upload Logic
  const processUpload = async (file: File) => {
    setError(null);
    setSelectedFileName(file.name);
    setStatus('uploading');
    setProgress(10);

    try {
      const response = await uploadResumeFile(file, (pct) => {
        setProgress(pct);
      });

      setSuccessData(response);
      setStatus('success');
      if (onUploadSuccess) {
        onUploadSuccess(response);
      }
    } catch (err: unknown) {
      setStatus('error');
      const uploadErr = err as UploadError;
      setError({
        message: uploadErr?.message || 'An unexpected error occurred during upload.',
        detail: uploadErr?.detail,
        statusCode: uploadErr?.statusCode,
      });
    }
  };

  // Quick Action: Sample PDF
  const handleUploadSample = () => {
    const samplePdf = generateSampleResumePdf();
    processUpload(samplePdf);
  };

  // Quick Action: Test Non-PDF Rejection
  const handleTestInvalidFile = () => {
    const fakeFile = new File(['Hello plain text'], 'document.txt', { type: 'text/plain' });
    processUpload(fakeFile);
  };

  // Reset Component
  const handleReset = () => {
    setStatus('idle');
    setProgress(0);
    setError(null);
    setSuccessData(null);
    setSelectedFileName(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            Phase 2: Secure Resume Ingestion
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Upload Candidate Resume</h2>
          <p className="text-sm text-slate-500 mt-1">
            Accepts verified PDF documents up to 10MB. Validates headers, MIME, and magic signatures with temporary local isolation.
          </p>
        </div>

        {/* Quick test buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleUploadSample}
            disabled={status === 'uploading'}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200/80 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            title="Upload an in-memory genuine PDF sample"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
            Upload Sample PDF
          </button>
          <button
            type="button"
            onClick={handleTestInvalidFile}
            disabled={status === 'uploading'}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-rose-700 bg-rose-50 hover:bg-rose-100 rounded-lg transition-colors disabled:opacity-50 cursor-pointer"
            title="Test rejection of non-PDF extension"
          >
            <FileWarning className="w-3.5 h-3.5 text-rose-500" />
            Test Rejection (.txt)
          </button>
        </div>
      </div>

      {/* Main Upload Zone */}
      <div className="mt-6">
        {status === 'success' && successData ? (
          /* SUCCESS STATE */
          <div className="bg-emerald-50/70 border border-emerald-200 rounded-xl p-6 transition-all">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                <FileCheck2 className="w-6 h-6" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Uploaded Successfully
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    {new Date(successData.uploaded_at).toLocaleTimeString()}
                  </span>
                </div>

                <h3 className="text-base font-semibold text-slate-900 mt-2 truncate">
                  {successData.original_filename}
                </h3>

                {/* File details list */}
                <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="bg-white/80 p-3 rounded-lg border border-emerald-100">
                    <span className="text-slate-500 block font-medium">Safe Server Identifier</span>
                    <span className="font-mono text-slate-800 break-all select-all font-semibold">
                      {successData.filename}
                    </span>
                  </div>
                  <div className="bg-white/80 p-3 rounded-lg border border-emerald-100">
                    <span className="text-slate-500 block font-medium">Document File Size</span>
                    <span className="font-semibold text-slate-800">
                      {formatFileSize(successData.size_bytes)} ({successData.size_bytes.toLocaleString()} bytes)
                    </span>
                  </div>
                </div>

                {/* Storage architecture reminder */}
                <div className="mt-4 flex items-center gap-2 text-xs text-emerald-800 bg-white/60 p-3 rounded-lg border border-emerald-100/60">
                  <HardDrive className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>
                    Stored temporarily in local storage. Not saved to database. Ready for Phase 3 text extraction.
                  </span>
                </div>

                {/* Actions */}
                <div className="mt-5 flex items-center gap-3">
                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 hover:bg-slate-50 rounded-lg shadow-sm transition-colors cursor-pointer"
                  >
                    <RotateCcw className="w-4 h-4 text-slate-500" />
                    Upload Another Resume
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* IDLE / DRAGGING / UPLOADING / ERROR STATE */
          <div>
            {/* Hidden native input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />

            {/* Dropzone Container */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={handleBrowseClick}
              className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all cursor-pointer select-none ${
                status === 'dragging'
                  ? 'border-blue-500 bg-blue-50/70 ring-4 ring-blue-100 scale-[1.005]'
                  : status === 'uploading'
                  ? 'border-slate-300 bg-slate-50/60 cursor-wait'
                  : 'border-slate-300 hover:border-slate-400 bg-slate-50/40 hover:bg-slate-50/80'
              }`}
            >
              <div className="flex flex-col items-center justify-center max-w-md mx-auto">
                <div
                  className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-4 transition-colors ${
                    status === 'dragging'
                      ? 'bg-blue-600 text-white'
                      : status === 'uploading'
                      ? 'bg-blue-100 text-blue-600 animate-pulse'
                      : 'bg-slate-100 text-slate-600 group-hover:bg-slate-200'
                  }`}
                >
                  {status === 'uploading' ? (
                    <UploadCloud className="w-8 h-8 animate-bounce" />
                  ) : (
                    <UploadCloud className="w-8 h-8" />
                  )}
                </div>

                <h3 className="text-base font-semibold text-slate-900">
                  {status === 'dragging'
                    ? 'Release file to upload PDF'
                    : status === 'uploading'
                    ? `Uploading ${selectedFileName || 'document'}...`
                    : 'Drag & drop candidate resume here'}
                </h3>

                <p className="text-sm text-slate-500 mt-1">
                  or{' '}
                  <span className="font-semibold text-blue-600 hover:text-blue-700 underline underline-offset-2">
                    browse from your computer
                  </span>
                </p>

                {/* Upload Progress Bar */}
                {status === 'uploading' && (
                  <div className="w-full mt-6 space-y-2">
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex justify-between items-center text-xs text-slate-500 font-mono">
                      <span>Validating binary headers & magic bytes...</span>
                      <span className="font-semibold">{progress}%</span>
                    </div>
                  </div>
                )}

                {/* Validation badges */}
                {status !== 'uploading' && (
                  <div className="flex flex-wrap items-center justify-center gap-2 mt-5 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white border border-slate-200 font-mono">
                      <FileText className="w-3.5 h-3.5 text-blue-500" />
                      .PDF Only
                    </span>
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white border border-slate-200 font-mono">
                      <HardDrive className="w-3.5 h-3.5 text-slate-400" />
                      Max 10 MB
                    </span>
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white border border-slate-200 font-mono">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                      Magic Header Verification
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Error Notification Banner */}
            {status === 'error' && error && (
              <div className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                <div className="flex-1 text-sm">
                  <h4 className="font-semibold text-rose-900">Upload Validation Error</h4>
                  <p className="text-rose-700 mt-0.5">{error.message}</p>
                  {error.statusCode && (
                    <span className="inline-block mt-1 font-mono text-xs text-rose-500">
                      HTTP Status: {error.statusCode}
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-3 py-1 text-xs font-medium text-rose-700 hover:bg-rose-100 rounded-md transition-colors cursor-pointer"
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Security and Integrity Checklist */}
      <div className="mt-8 pt-6 border-t border-slate-100">
        <h4 className="text-xs font-bold tracking-wider text-slate-400 uppercase mb-3">
          Phase 2 Security & Validation Pipeline
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs text-slate-600">
          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-slate-800 block">Strict Extension & MIME</span>
              <span>Rejects executables, archives, and spoofed extensions.</span>
            </div>
          </div>
          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-slate-800 block">Magic Bytes & Structure</span>
              <span>Inspects %PDF- header and %%EOF end marker.</span>
            </div>
          </div>
          <div className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-medium text-slate-800 block">Safe Temporary Isolation</span>
              <span>UUID naming prevents collisions and path traversal.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
