/**
 * Phase 14: Job Description Parsing Interactive Viewer
 * Provides job description input, preset templates, structured extraction results,
 * normalized skill displays, and JSON inspection.
 */
import React, { useState } from 'react';
import {
  Briefcase,
  Building2,
  MapPin,
  Clock,
  DollarSign,
  GraduationCap,
  Award,
  Wrench,
  CheckCircle2,
  Sparkles,
  Layers,
  Copy,
  Check,
  AlertCircle,
  RefreshCw,
  FileText,
} from 'lucide-react';
import { parseJobDescription } from '../services/api';
import { JobDescription, JobParseResponse } from '../types/job';

const SAMPLE_JOBS = [
  {
    title: 'Senior Cloud Backend Engineer',
    company: 'Apex Cloud Systems',
    text: `Job Title: Senior Backend Engineer
Company: Apex Cloud Systems
Location: San Francisco, CA (Hybrid)
Employment Type: Full-time
Salary: $170,000 - $210,000 per year

About Apex Cloud Systems:
Apex Cloud Systems is an enterprise software platform powering next-generation financial cloud infrastructure.

Role Overview:
We are seeking a seasoned Senior Backend Engineer to architect, build, and maintain our high-throughput distributed microservices.

Key Responsibilities:
- Design, build, and deploy low-latency RESTful and gRPC APIs.
- Optimize complex database queries and schema designs on PostgreSQL.
- Partner with product managers and frontend teams to deliver scalable customer features.
- Mentor junior engineers and participate in code reviews.

Minimum Requirements:
- 5+ years of software engineering experience building production systems.
- Strong proficiency in Python, FastAPI, and PostgreSQL.
- Practical experience with Docker and containerization workflows.
- Bachelor's degree in Computer Science or related technical field.

Preferred Qualifications:
- Experience with Kubernetes and Redis caching.
- Familiarity with Terraform and cloud infrastructure.

Certifications:
- AWS Certified Solutions Architect or equivalent cloud credential is a plus.`,
  },
  {
    title: 'Senior Machine Learning Engineer (No Company)',
    company: 'None (Implicit)',
    text: `Position: Senior Machine Learning Engineer
Location: Remote
Employment Type: Full-time

What You'll Do:
- Develop state-of-the-art natural language processing models and recommendation systems.
- Deploy real-time machine learning pipelines handling millions of inference requests daily.
- Collaborate with data engineers to build robust feature pipelines.

Basic Qualifications:
- 4+ years of hands-on experience in machine learning and deep learning.
- Strong proficiency in Python, PyTorch, and SQL.
- Master's or Ph.D. degree in Computer Science, Statistics, or related quantitative discipline.

Nice to Have:
- Hands-on experience with MLflow, Ray, and distributed GPU training.
- Experience with Kafka streaming architectures.`,
  },
  {
    title: 'Lead Frontend Developer (No Certifications)',
    company: 'Horizon Media Labs',
    text: `Job Title: Lead Frontend Developer
Company: Horizon Media Labs
Job Type: Full-time
Location: New York, NY

About Us:
Horizon Media Labs creates interactive visual experiences for top global media publishers.

Responsibilities:
- Lead the architecture of modern web applications using React and TypeScript.
- Build accessible, high-performance UI components with Tailwind CSS.
- Optimize frontend web vitals and client-side rendering performance.

Requirements:
- 6+ years of professional web development experience.
- Deep expertise in JavaScript, TypeScript, and React.
- Solid understanding of web performance, DOM manipulation, and responsive design.
- Bachelor's degree in Web Development, Software Engineering, or equivalent experience.

Preferred Skills:
- Experience with Next.js and GraphQL.
- Familiarity with Cypress end-to-end testing.`,
  },
];

export const JobDescriptionViewer: React.FC = () => {
  const [jobText, setJobText] = useState<string>(SAMPLE_JOBS[0].text);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<JobParseResponse | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  const handleParse = async () => {
    if (!jobText.trim()) {
      setError('Please provide or paste a job description text to parse.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await parseJobDescription(jobText, true);
      setResult(response);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to parse job description');
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyJson = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result.job, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const job = result?.job;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-200 bg-slate-50/70 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-600">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-900">Job Description Parsing</h2>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700 font-semibold uppercase tracking-wider">
                Phase 14
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Extract structured requirements, skills, education, and credentials with strict anti-hallucination.
            </p>
          </div>
        </div>

        {/* Preset Selectors */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-500">Load sample:</span>
          {SAMPLE_JOBS.map((sample, idx) => (
            <button
              key={idx}
              onClick={() => {
                setJobText(sample.text);
                setResult(null);
                setError(null);
              }}
              className="text-xs px-2.5 py-1 rounded-md bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 transition-colors font-medium"
            >
              {sample.title.split(' ')[0]} {sample.title.split(' ')[1]}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Input Area */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <label className="font-semibold text-slate-700 flex items-center gap-1.5">
              <FileText className="w-4 h-4 text-slate-400" />
              Raw Job Description Text
            </label>
            <span>{jobText.length} characters</span>
          </div>

          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            rows={8}
            placeholder="Paste raw job description text here (Job Title, Requirements, Responsibilities, etc.)..."
            className="w-full text-xs font-mono p-3.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-slate-800 bg-slate-50/50"
          />

          <div className="flex justify-end gap-3 pt-1">
            <button
              onClick={() => {
                setJobText('');
                setResult(null);
                setError(null);
              }}
              disabled={loading || !jobText}
              className="text-xs px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors disabled:opacity-50"
            >
              Clear
            </button>
            <button
              onClick={handleParse}
              disabled={loading || !jobText.trim()}
              className="text-xs font-medium px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white transition-colors flex items-center gap-2 disabled:opacity-50 shadow-sm"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Parsing Job Description...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Parse Job Description
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error notification */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-start gap-3 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-500 mt-0.5" />
            <div>
              <p className="font-semibold">Parsing Failed</p>
              <p className="text-xs text-red-600 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Extraction Results */}
        {result && job && (
          <div className="space-y-6 pt-2 border-t border-slate-200">
            {/* Metadata Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs">
              <div className="flex flex-wrap items-center gap-4 text-slate-600">
                <span className="flex items-center gap-1.5 font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Extracted Successfully
                </span>
                <span>
                  Duration: <strong className="text-slate-800">{result.duration_ms} ms</strong>
                </span>
                <span>
                  Normalized Skills: <strong className="text-slate-800">{result.normalized_skills_count}</strong>
                </span>
                {result.provider && (
                  <span>
                    Engine: <strong className="text-slate-800 uppercase">{result.provider}</strong>
                  </span>
                )}
              </div>

              <button
                onClick={handleCopyJson}
                className="text-xs px-2.5 py-1 rounded bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 flex items-center gap-1.5 transition-colors font-medium shadow-2xs"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied' : 'Copy JSON'}
              </button>
            </div>

            {/* Structured Card */}
            <div className="p-6 rounded-xl border border-indigo-100 bg-gradient-to-b from-indigo-50/30 to-white space-y-6">
              {/* Header: Title & Company */}
              <div>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-xl font-bold text-slate-900">{job.job_title}</h3>
                  {job.employment_type && (
                    <span className="text-xs px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-semibold border border-slate-200">
                      {job.employment_type}
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mt-2 text-xs text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <Building2 className="w-4 h-4 text-indigo-500" />
                    {job.company ? (
                      <span className="font-semibold text-slate-800">{job.company}</span>
                    ) : (
                      <span className="italic text-slate-400">Company not explicitly stated</span>
                    )}
                  </div>

                  {job.location && (
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-4 h-4 text-slate-400" />
                      <span>{job.location}</span>
                    </div>
                  )}

                  {job.salary_range && (
                    <div className="flex items-center gap-1.5">
                      <DollarSign className="w-4 h-4 text-emerald-600" />
                      <span className="font-medium text-emerald-700">{job.salary_range}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Grid: Required Skills vs Preferred Skills */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Required Skills */}
                <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      Required Skills
                    </h4>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      {job.required_skills.length}
                    </span>
                  </div>

                  {job.required_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {job.required_skills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="text-xs px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">No explicit required skills found.</p>
                  )}
                </div>

                {/* Preferred Skills */}
                <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="w-4 h-4 text-amber-500" />
                      Preferred Skills & Bonus
                    </h4>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                      {job.preferred_skills.length}
                    </span>
                  </div>

                  {job.preferred_skills.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {job.preferred_skills.map((skill, idx) => (
                        <span
                          key={idx}
                          className="text-xs px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-medium"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">None specified in posting.</p>
                  )}
                </div>
              </div>

              {/* Tools & Technologies */}
              {job.tools_and_technologies.length > 0 && (
                <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Wrench className="w-4 h-4 text-indigo-500" />
                      Tools & Technologies
                    </h4>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                      {job.tools_and_technologies.length}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {job.tools_and_technologies.map((tool, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-800 border border-indigo-200 font-medium"
                      >
                        {tool}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Experience & Education Requirements */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Experience */}
                <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Clock className="w-4 h-4 text-blue-500" />
                    Experience Criteria
                  </h4>
                  {job.experience_requirements.length > 0 ? (
                    <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside">
                      {job.experience_requirements.map((exp, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {exp}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-400 italic">Not explicitly specified.</p>
                  )}
                </div>

                {/* Education */}
                <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <GraduationCap className="w-4 h-4 text-purple-500" />
                    Education Requirements
                  </h4>
                  {job.education_requirements.length > 0 ? (
                    <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside">
                      {job.education_requirements.map((edu, idx) => (
                        <li key={idx} className="leading-relaxed">
                          {edu}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-slate-400 italic">Not explicitly specified.</p>
                  )}
                </div>
              </div>

              {/* Responsibilities */}
              {job.responsibilities.length > 0 && (
                <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="w-4 h-4 text-slate-600" />
                    Key Responsibilities
                  </h4>
                  <ul className="space-y-1.5 text-xs text-slate-700">
                    {job.responsibilities.map((resp, idx) => (
                      <li key={idx} className="flex items-start gap-2 leading-relaxed">
                        <span className="text-indigo-500 font-bold mt-0.5">•</span>
                        <span>{resp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Certifications */}
              <div className="p-4 rounded-lg bg-white border border-slate-200 space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-amber-500" />
                  Certifications Mentioned
                </h4>
                {job.certifications.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {job.certifications.map((cert, idx) => (
                      <span
                        key={idx}
                        className="text-xs px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-semibold"
                      >
                        {cert}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">None mentioned in job posting.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
