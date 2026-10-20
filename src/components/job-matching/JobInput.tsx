import React, { useState } from 'react';
import {
  Briefcase,
  FileText,
  Sparkles,
  ArrowRight,
  RotateCcw,
  Building,
  Check,
} from 'lucide-react';
import { JobDescription } from '../../types/job';

interface JobInputProps {
  jobText: string;
  onJobTextChange: (text: string) => void;
  onAnalyze: () => void;
  isLoading: boolean;
  parsedJob?: JobDescription | null;
}

export const SAMPLE_JOB_PRESETS = [
  {
    label: 'Senior Backend Engineer',
    company: 'Apex Cloud Systems',
    text: `Job Title: Senior Backend Engineer
Company: Apex Cloud Systems
Location: San Francisco, CA (Hybrid)
Employment Type: Full-time

Key Responsibilities:
- Design and build high-throughput REST and gRPC microservices in Python.
- Architect transactional database schemas and query optimizations in PostgreSQL.
- Maintain Docker containers and CI/CD deployment pipelines on AWS.

Minimum Qualifications:
- 5+ years of software engineering experience developing distributed backend services.
- Expert proficiency in Python, FastAPI, and PostgreSQL.
- Solid understanding of Docker, REST APIs, and database indexing.
- Bachelor's degree in Computer Science, Software Engineering, or related technical field.

Preferred Qualifications:
- Experience with Redis caching, message queues (Kafka or RabbitMQ), and Kubernetes.
- Familiarity with Terraform and infrastructure-as-code.
- AWS Certified Solutions Architect certification.`,
  },
  {
    label: 'Full-Stack React Engineer',
    company: 'Vanguard Digital',
    text: `Job Title: Senior Full-Stack Engineer
Company: Vanguard Digital
Location: Remote (US)
Employment Type: Full-time

Responsibilities:
- Build reactive, accessible web applications using React, TypeScript, and Tailwind CSS.
- Develop backend services and REST APIs with Node.js and PostgreSQL.
- Collaborate with product designers on component design systems and state management.

Required Skills & Experience:
- 4+ years of professional full-stack development experience.
- Deep expertise in React, TypeScript, JavaScript, HTML5, and CSS/Tailwind.
- Proven experience with Node.js, Express, and SQL databases.
- Bachelor's degree in Computer Science or equivalent practical experience.

Preferred Skills:
- Experience with GraphQL, Next.js, and Jest/Playwright automated testing.
- Cloud deployment on AWS or Google Cloud Platform.`,
  },
  {
    label: 'Machine Learning Engineer',
    company: 'Neural Matrix AI',
    text: `Job Title: Machine Learning Engineer
Company: Neural Matrix AI
Location: Boston, MA
Employment Type: Full-time

Role Overview:
- Develop deep learning models and scalable inference services for NLP applications.
- Build automated data processing and feature engineering pipelines.

Required Qualifications:
- 3+ years of production experience in Machine Learning and Python.
- Hands-on proficiency with PyTorch, TensorFlow, Scikit-Learn, and SQL.
- Strong grounding in linear algebra, statistics, and vector embeddings.
- Master's or Ph.D. in Computer Science, Data Science, or quantitative STEM discipline.

Preferred Qualifications:
- Experience with Hugging Face transformers, PyMuPDF, and LLM orchestration.
- Experience with Docker, Ray, and MLflow model registry.`,
  },
];

export const JobInput: React.FC<JobInputProps> = ({
  jobText,
  onJobTextChange,
  onAnalyze,
  isLoading,
  parsedJob,
}) => {
  const [selectedPresetIndex, setSelectedPresetIndex] = useState<number | null>(null);

  const handleSelectPreset = (index: number) => {
    setSelectedPresetIndex(index);
    onJobTextChange(SAMPLE_JOB_PRESETS[index].text);
  };

  const handleClear = () => {
    setSelectedPresetIndex(null);
    onJobTextChange('');
  };

  const charCount = jobText.trim().length;
  const wordCount = jobText.trim() ? jobText.trim().split(/\s+/).length : 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-slate-700" />
            Job Description Input
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Paste target job description text or select a standard industry benchmark preset.
          </p>
        </div>

        {/* Preset Selector */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-xs text-slate-400 font-medium mr-1">Presets:</span>
          {SAMPLE_JOB_PRESETS.map((preset, idx) => (
            <button
              key={preset.label}
              type="button"
              onClick={() => handleSelectPreset(idx)}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                selectedPresetIndex === idx
                  ? 'bg-slate-900 text-white shadow-xs'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {preset.label}
            </button>
          ))}
          {jobText && (
            <button
              type="button"
              onClick={handleClear}
              className="text-xs px-2 py-1 text-slate-500 hover:text-slate-800 transition-colors flex items-center gap-1"
              title="Clear input"
            >
              <RotateCcw className="w-3 h-3" />
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Textarea */}
      <div className="relative">
        <textarea
          rows={7}
          value={jobText}
          onChange={(e) => {
            setSelectedPresetIndex(null);
            onJobTextChange(e.target.value);
          }}
          placeholder="Paste full job description text here (including job title, company, required skills, experience, education, responsibilities)..."
          className="w-full text-sm font-mono text-slate-800 bg-slate-50/70 border border-slate-200 rounded-lg p-3.5 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-900 focus:border-transparent transition-all leading-relaxed resize-y placeholder:text-slate-400 placeholder:font-sans"
        />

        {/* Live Counters */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-1.5 px-0.5">
          <div className="flex items-center gap-3">
            <span>{charCount.toLocaleString()} characters</span>
            <span aria-hidden="true">·</span>
            <span>{wordCount.toLocaleString()} words</span>
          </div>

          {parsedJob && (
            <div className="flex items-center gap-2 text-emerald-700 font-medium">
              <Check className="w-3.5 h-3.5" />
              <span>Parsed: {parsedJob.job_title}</span>
              {parsedJob.company && (
                <>
                  <span aria-hidden="true" className="text-slate-300">·</span>
                  <span className="text-slate-600 font-normal">{parsedJob.company}</span>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Action Bar */}
      <div className="flex items-center justify-between pt-1">
        <div className="text-xs text-slate-500 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-slate-400" />
          <span>Evaluates exact skill matching and embedding-based semantic similarity</span>
        </div>

        <button
          type="button"
          disabled={isLoading || !jobText.trim()}
          onClick={onAnalyze}
          className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-white transition-all shadow-sm ${
            isLoading || !jobText.trim()
              ? 'bg-slate-300 cursor-not-allowed'
              : 'bg-slate-900 hover:bg-slate-800 active:scale-[0.99] cursor-pointer'
          }`}
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Analyzing Match...</span>
            </>
          ) : (
            <>
              <span>Analyze Requirements Match</span>
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </div>
    </div>
  );
};
