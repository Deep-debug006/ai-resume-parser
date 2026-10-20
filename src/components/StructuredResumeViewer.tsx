import React, { useState } from 'react';
import {
  Sparkles,
  Bot,
  User,
  Mail,
  Phone,
  MapPin,
  Linkedin,
  Github,
  Globe,
  Briefcase,
  GraduationCap,
  Wrench,
  FolderGit2,
  Award,
  CheckCircle2,
  AlertCircle,
  Copy,
  Check,
  RefreshCw,
  Code2,
  Clock,
  ShieldCheck,
} from 'lucide-react';
import { ResumeParseResponse, ParsingStatus } from '../types/resume';
import { parseResume } from '../services/api';

interface StructuredResumeViewerProps {
  resumeId: string;
  originalFilename: string;
}

export const StructuredResumeViewer: React.FC<StructuredResumeViewerProps> = ({
  resumeId,
  originalFilename,
}) => {
  const [status, setStatus] = useState<ParsingStatus>('idle');
  const [data, setData] = useState<ResumeParseResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'visual' | 'json'>('visual');
  const [copied, setCopied] = useState(false);

  const handleParse = async () => {
    setStatus('parsing');
    setErrorMessage(null);
    try {
      const response = await parseResume(resumeId);
      setData(response);
      setStatus('success');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to parse resume with LLM.');
      setStatus('error');
    }
  };

  const handleCopyJson = () => {
    if (data?.resume) {
      navigator.clipboard.writeText(JSON.stringify(data.resume, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const resume = data?.resume;

  return (
    <div className="bg-white rounded-2xl border border-indigo-200/80 shadow-xs p-6 mt-6 transition-all">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-indigo-100 text-indigo-700 rounded-lg">
              <Sparkles className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-slate-900">
              Phase 9: AI Structured Information Extraction
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded uppercase">
              LLM Schema Alignment
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Grounds cleaned text, canonical sections, and spaCy NLP anchors into the strict Pydantic Resume model with anti-hallucination guarantees.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {status === 'success' && (
            <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
              <button
                onClick={() => setActiveTab('visual')}
                className={`px-3 py-1 font-medium rounded-md transition-all ${
                  activeTab === 'visual'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Structured UI
              </button>
              <button
                onClick={() => setActiveTab('json')}
                className={`px-3 py-1 font-medium rounded-md transition-all flex items-center gap-1 ${
                  activeTab === 'json'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Code2 className="w-3.5 h-3.5" />
                Schema JSON
              </button>
            </div>
          )}

          <button
            onClick={handleParse}
            disabled={status === 'parsing'}
            className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white text-xs font-semibold rounded-xl shadow-xs transition-all shrink-0"
          >
            {status === 'parsing' ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Parsing with LLM...
              </>
            ) : status === 'success' ? (
              <>
                <RefreshCw className="w-3.5 h-3.5" />
                Re-Parse
              </>
            ) : (
              <>
                <Bot className="w-3.5 h-3.5" />
                Extract Structured Resume
              </>
            )}
          </button>
        </div>
      </div>

      {/* Target File Info */}
      <div className="flex items-center justify-between mt-3 text-xs text-slate-500 bg-slate-50 px-3.5 py-2 rounded-xl border border-slate-200/60">
        <span>Target Document: <strong className="text-slate-700 font-medium">{originalFilename}</strong> ({resumeId})</span>
        <span className="flex items-center gap-1 text-emerald-700 font-medium">
          <ShieldCheck className="w-3.5 h-3.5" />
          Strict Anti-Hallucination &amp; Zero-Invention Rules Active
        </span>
      </div>

      {/* Error Banner */}
      {status === 'error' && (
        <div className="mt-4 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-600 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900">LLM Structured Extraction Failed</p>
            <p className="mt-0.5 text-red-700">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {status === 'parsing' && (
        <div className="mt-6 p-8 border-2 border-dashed border-indigo-200 rounded-2xl bg-indigo-50/30 text-center">
          <div className="w-10 h-10 mx-auto rounded-xl bg-indigo-600/10 text-indigo-600 flex items-center justify-center animate-pulse mb-3">
            <Sparkles className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">Running LLM Structured Parser Pipeline</h3>
          <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
            Grounded synthesis across extracted text, sections, and NLP anchors with Pydantic validation and schema repair loops...
          </p>
        </div>
      )}

      {/* Results View */}
      {status === 'success' && data && resume && (
        <div className="mt-5 space-y-5">
          {/* Metadata Badges */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold">LLM Provider</span>
              <div className="flex items-center gap-1.5 mt-1">
                <Bot className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-slate-800 capitalize">{data.llm_provider}</span>
                <span className="text-[10px] text-slate-400 font-mono">({data.llm_model})</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold">Pipeline Latency</span>
              <div className="flex items-center gap-1.5 mt-1">
                <Clock className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-slate-800">{data.parsing_duration_ms} ms</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold">Repair Attempts</span>
              <div className="flex items-center gap-1.5 mt-1">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span className="text-xs font-bold text-slate-800">
                  {data.repair_attempts === 0 ? '0 (Clean 1st Pass)' : `${data.repair_attempts} Repaired`}
                </span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
              <span className="text-[11px] text-slate-500 uppercase font-semibold">Sections Mapped</span>
              <div className="flex items-center gap-1.5 mt-1">
                <ShieldCheck className="w-4 h-4 text-indigo-600" />
                <span className="text-xs font-bold text-slate-800">{data.sections_detected.length} Sections</span>
              </div>
            </div>
          </div>

          {activeTab === 'json' ? (
            /* JSON View */
            <div className="relative">
              <div className="flex items-center justify-between bg-slate-900 text-slate-300 px-4 py-2 rounded-t-xl text-xs font-mono">
                <span>Canonical Pydantic Resume Model</span>
                <button
                  onClick={handleCopyJson}
                  className="flex items-center gap-1 hover:text-white transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy JSON</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="bg-slate-950 text-indigo-300 font-mono text-xs p-4 rounded-b-xl overflow-x-auto max-h-[500px] border border-slate-800">
                {JSON.stringify(resume, null, 2)}
              </pre>
            </div>
          ) : (
            /* Structured Visual View */
            <div className="space-y-6">
              {/* Personal Information Card */}
              <div className="p-5 rounded-2xl bg-gradient-to-r from-indigo-50/50 via-slate-50 to-white border border-indigo-100">
                <div className="flex items-start justify-between flex-wrap gap-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                      <User className="w-5 h-5 text-indigo-600" />
                      {resume.personal_info.full_name}
                    </h3>
                    <div className="flex flex-wrap items-center gap-y-1.5 gap-x-4 mt-2 text-xs text-slate-600">
                      {resume.personal_info.email && (
                        <a
                          href={`mailto:${resume.personal_info.email}`}
                          className="flex items-center gap-1 text-indigo-600 hover:underline"
                        >
                          <Mail className="w-3.5 h-3.5" />
                          {resume.personal_info.email}
                        </a>
                      )}
                      {resume.personal_info.phone && (
                        <span className="flex items-center gap-1">
                          <Phone className="w-3.5 h-3.5 text-slate-400" />
                          {resume.personal_info.phone}
                        </span>
                      )}
                      {resume.personal_info.location && (
                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-400" />
                          {resume.personal_info.location}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Profile Links */}
                  <div className="flex items-center gap-2">
                    {resume.personal_info.linkedin_url && (
                      <a
                        href={resume.personal_info.linkedin_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1.5 bg-white border border-slate-200 rounded-lg text-blue-600 hover:bg-blue-50 transition-colors"
                        title="LinkedIn Profile"
                      >
                        <Linkedin className="w-4 h-4" />
                      </a>
                    )}
                    {resume.personal_info.github_url && (
                      <a
                        href={resume.personal_info.github_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-800 hover:bg-slate-100 transition-colors"
                        title="GitHub Profile"
                      >
                        <Github className="w-4 h-4" />
                      </a>
                    )}
                    {resume.personal_info.portfolio_url && (
                      <a
                        href={resume.personal_info.portfolio_url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1.5 bg-white border border-slate-200 rounded-lg text-indigo-600 hover:bg-indigo-50 transition-colors"
                        title="Personal Portfolio"
                      >
                        <Globe className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>

                {/* Summary / Objective */}
                {resume.summary && (
                  <div className="mt-4 pt-3 border-t border-slate-200/60 text-xs text-slate-700 leading-relaxed">
                    <strong className="text-slate-900 font-semibold block mb-1">Professional Summary:</strong>
                    {resume.summary}
                  </div>
                )}
              </div>

              {/* Work Experience */}
              {resume.experience && resume.experience.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Briefcase className="w-4 h-4 text-indigo-600" />
                    Work Experience ({resume.experience.length})
                  </h4>
                  <div className="space-y-3">
                    {resume.experience.map((exp, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all shadow-2xs"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                          <div>
                            <span className="text-sm font-bold text-slate-900">{exp.title}</span>
                            <span className="text-xs text-slate-600 ml-2">@ <strong>{exp.company}</strong></span>
                            {exp.location && (
                              <span className="text-[11px] text-slate-400 ml-2">• {exp.location}</span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-slate-500 font-mono">
                            <span>{exp.start_date || 'N/A'} — {exp.end_date || (exp.is_current ? 'Present' : 'N/A')}</span>
                            {exp.is_current && (
                              <span className="px-1.5 py-0.2 bg-emerald-100 text-emerald-800 font-bold text-[10px] rounded uppercase">
                                Current
                              </span>
                            )}
                          </div>
                        </div>

                        {exp.highlights && exp.highlights.length > 0 && (
                          <ul className="mt-2.5 space-y-1 text-xs text-slate-600 list-disc list-inside">
                            {exp.highlights.map((hl, hidx) => (
                              <li key={hidx} className="leading-relaxed">{hl}</li>
                            ))}
                          </ul>
                        )}

                        {exp.technologies && exp.technologies.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-3 pt-2 border-t border-slate-100">
                            {exp.technologies.map((tech, tidx) => (
                              <span
                                key={tidx}
                                className="px-2 py-0.5 bg-slate-100 text-slate-700 text-[10px] font-medium rounded-md"
                              >
                                {tech}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Education */}
              {resume.education && resume.education.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <GraduationCap className="w-4 h-4 text-indigo-600" />
                    Education ({resume.education.length})
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {resume.education.map((edu, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-all shadow-2xs"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <span className="text-xs font-bold text-slate-900 block">{edu.institution}</span>
                            <span className="text-xs text-indigo-700 font-medium">
                              {edu.degree || 'Degree'} {edu.field_of_study ? `in ${edu.field_of_study}` : ''}
                            </span>
                          </div>
                          {(edu.start_date || edu.end_date) && (
                            <span className="text-[11px] text-slate-500 font-mono">
                              {edu.start_date ? `${edu.start_date} - ` : ''}{edu.end_date || 'N/A'}
                            </span>
                          )}
                        </div>

                        {edu.gpa !== null && edu.gpa !== undefined && (
                          <div className="mt-2 text-xs text-slate-600">
                            GPA: <strong className="text-slate-800 font-mono">{edu.gpa}</strong>
                            {edu.gpa_max ? ` / ${edu.gpa_max}` : ''}
                          </div>
                        )}

                        {edu.honors && edu.honors.length > 0 && (
                          <div className="mt-2 text-[11px] text-slate-500">
                            Honors: {edu.honors.join(', ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Categorized Skills */}
              {resume.skills && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Wrench className="w-4 h-4 text-indigo-600" />
                    Categorized Competencies &amp; Skills
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                    {resume.skills.programming_languages?.length > 0 && (
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-700 block mb-1.5">Programming Languages</span>
                        <div className="flex flex-wrap gap-1">
                          {resume.skills.programming_languages.map((sk, i) => (
                            <span key={i} className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 rounded text-[11px] font-mono">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {resume.skills.frameworks_and_libraries?.length > 0 && (
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-700 block mb-1.5">Frameworks &amp; Libraries</span>
                        <div className="flex flex-wrap gap-1">
                          {resume.skills.frameworks_and_libraries.map((sk, i) => (
                            <span key={i} className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 rounded text-[11px]">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {resume.skills.databases?.length > 0 && (
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-700 block mb-1.5">Databases &amp; Storage</span>
                        <div className="flex flex-wrap gap-1">
                          {resume.skills.databases.map((sk, i) => (
                            <span key={i} className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 rounded text-[11px]">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {resume.skills.cloud_and_devops?.length > 0 && (
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-700 block mb-1.5">Cloud &amp; DevOps</span>
                        <div className="flex flex-wrap gap-1">
                          {resume.skills.cloud_and_devops.map((sk, i) => (
                            <span key={i} className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 rounded text-[11px]">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {resume.skills.technical_skills?.length > 0 && (
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-700 block mb-1.5">Technical &amp; Architecture</span>
                        <div className="flex flex-wrap gap-1">
                          {resume.skills.technical_skills.map((sk, i) => (
                            <span key={i} className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 rounded text-[11px]">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {resume.skills.tools?.length > 0 && (
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <span className="text-[11px] font-bold text-slate-700 block mb-1.5">Tools &amp; Utilities</span>
                        <div className="flex flex-wrap gap-1">
                          {resume.skills.tools.map((sk, i) => (
                            <span key={i} className="px-2 py-0.5 bg-white border border-slate-200 text-slate-800 rounded text-[11px]">
                              {sk}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Projects & Certifications Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Projects */}
                {resume.projects && resume.projects.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <FolderGit2 className="w-4 h-4 text-indigo-600" />
                      Projects ({resume.projects.length})
                    </h4>
                    <div className="space-y-2">
                      {resume.projects.map((proj, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-900">{proj.name}</span>
                            {proj.url && (
                              <a
                                href={proj.url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-[10px] text-indigo-600 hover:underline"
                              >
                                Link ↗
                              </a>
                            )}
                          </div>
                          {proj.description && (
                            <p className="text-[11px] text-slate-600 mt-1">{proj.description}</p>
                          )}
                          {proj.technologies?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {proj.technologies.map((t, ti) => (
                                <span key={ti} className="px-1.5 py-0.2 bg-white border border-slate-200 text-slate-600 text-[10px] rounded">
                                  {t}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Certifications */}
                {resume.certifications && resume.certifications.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Award className="w-4 h-4 text-amber-600" />
                      Certifications ({resume.certifications.length})
                    </h4>
                    <div className="space-y-2">
                      {resume.certifications.map((cert, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                          <span className="text-xs font-bold text-slate-900 block">{cert.name}</span>
                          <span className="text-[11px] text-slate-500">
                            {cert.issuer ? `${cert.issuer}` : ''}
                            {cert.issue_date ? ` • ${cert.issue_date}` : ''}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
