import React, { useState, useEffect } from 'react';
import {
  FileCode,
  CheckCircle2,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  Code2,
  Layers,
  Sparkles,
  BookOpen,
  User,
  GraduationCap,
  Wrench,
  Briefcase,
  FolderGit2,
  Award,
} from 'lucide-react';
import { fetchResumeSchema } from '../services/resumeService';

interface SchemaField {
  name: string;
  type: string;
  required: boolean;
  description: string;
  validation?: string;
}

interface ModelSpec {
  name: string;
  icon: React.ReactNode;
  description: string;
  fields: SchemaField[];
}

const MODELS_SPEC: ModelSpec[] = [
  {
    name: 'PersonalInfo',
    icon: <User className="w-4 h-4 text-sky-600" />,
    description: "Candidate contact information and online profiles.",
    fields: [
      { name: 'full_name', type: 'string', required: true, description: "Candidate's legal or professional name", validation: 'Non-empty, trimmed' },
      { name: 'email', type: 'string | null', required: false, description: 'Email address', validation: 'RFC email regex format' },
      { name: 'phone', type: 'string | null', required: false, description: 'Phone / mobile contact number' },
      { name: 'location', type: 'string | null', required: false, description: 'City, state, or country of residence' },
      { name: 'linkedin_url', type: 'string | null', required: false, description: 'LinkedIn profile URL' },
      { name: 'github_url', type: 'string | null', required: false, description: 'GitHub profile URL' },
      { name: 'portfolio_url', type: 'string | null', required: false, description: 'Personal website or portfolio URL' },
    ],
  },
  {
    name: 'Education',
    icon: <GraduationCap className="w-4 h-4 text-amber-600" />,
    description: 'Degree, university, coursework, and honors.',
    fields: [
      { name: 'institution', type: 'string', required: true, description: 'University or college name', validation: 'Non-empty string' },
      { name: 'degree', type: 'string | null', required: false, description: 'Degree earned, e.g. B.S., M.S., Ph.D.' },
      { name: 'field_of_study', type: 'string | null', required: false, description: 'Major, concentration, or specialization' },
      { name: 'start_date', type: 'string | null', required: false, description: 'Inception date or year' },
      { name: 'end_date', type: 'string | null', required: false, description: 'Graduation date or Present' },
      { name: 'gpa', type: 'float | null', required: false, description: 'Numeric GPA score', validation: '0.0 <= gpa <= 10.0' },
      { name: 'gpa_max', type: 'float | null', required: false, description: 'Maximum scale value for GPA', validation: 'gpa <= gpa_max, gpa_max > 0' },
      { name: 'honors', type: 'string[]', required: false, description: 'Academic honors, distinctions, dean list' },
      { name: 'courses', type: 'string[]', required: false, description: 'Relevant coursework completed' },
    ],
  },
  {
    name: 'SkillSet',
    icon: <Wrench className="w-4 h-4 text-cyan-600" />,
    description: 'Categorized inventory of hard and soft capabilities.',
    fields: [
      { name: 'technical_skills', type: 'string[]', required: false, description: 'General technical competencies' },
      { name: 'programming_languages', type: 'string[]', required: false, description: 'Programming languages (Python, Go, etc.)' },
      { name: 'frameworks_and_libraries', type: 'string[]', required: false, description: 'Frameworks and libraries (FastAPI, React)' },
      { name: 'databases', type: 'string[]', required: false, description: 'Databases and caches (PostgreSQL, Redis)' },
      { name: 'cloud_and_devops', type: 'string[]', required: false, description: 'Cloud infrastructure (AWS, Docker, K8s)' },
      { name: 'soft_skills', type: 'string[]', required: false, description: 'Leadership and interpersonal skills' },
      { name: 'tools', type: 'string[]', required: false, description: 'Developer tools, IDEs, and utilities' },
    ],
  },
  {
    name: 'Experience',
    icon: <Briefcase className="w-4 h-4 text-indigo-600" />,
    description: 'Employment records, roles, responsibilities, and achievements.',
    fields: [
      { name: 'company', type: 'string', required: true, description: 'Employer or organization name', validation: 'Non-empty string' },
      { name: 'title', type: 'string', required: true, description: 'Position or job title', validation: 'Non-empty string' },
      { name: 'location', type: 'string | null', required: false, description: 'Job location or Remote' },
      { name: 'start_date', type: 'string | null', required: false, description: 'Start date or year' },
      { name: 'end_date', type: 'string | null', required: false, description: 'End date or Present' },
      { name: 'is_current', type: 'boolean', required: false, description: 'True if currently working here' },
      { name: 'highlights', type: 'string[]', required: false, description: 'Quantifiable achievements and responsibilities' },
      { name: 'technologies', type: 'string[]', required: false, description: 'Tools and tech used in role' },
    ],
  },
  {
    name: 'Project',
    icon: <FolderGit2 className="w-4 h-4 text-violet-600" />,
    description: 'Notable technical, academic, or open-source software projects.',
    fields: [
      { name: 'name', type: 'string', required: true, description: 'Project title', validation: 'Non-empty string' },
      { name: 'description', type: 'string | null', required: false, description: 'Brief summary of scope' },
      { name: 'url', type: 'string | null', required: false, description: 'Source code or demo link' },
      { name: 'highlights', type: 'string[]', required: false, description: 'Features and metric impacts' },
      { name: 'technologies', type: 'string[]', required: false, description: 'Stack and frameworks utilized' },
      { name: 'start_date', type: 'string | null', required: false, description: 'Project start date' },
      { name: 'end_date', type: 'string | null', required: false, description: 'Project completion date' },
    ],
  },
  {
    name: 'Certification',
    icon: <Award className="w-4 h-4 text-rose-600" />,
    description: 'Accredited professional certifications and licenses.',
    fields: [
      { name: 'name', type: 'string', required: true, description: 'Credential title', validation: 'Non-empty string' },
      { name: 'issuer', type: 'string | null', required: false, description: 'Issuing organization (AWS, Coursera, etc.)' },
      { name: 'issue_date', type: 'string | null', required: false, description: 'Date or year issued' },
      { name: 'expiration_date', type: 'string | null', required: false, description: 'Expiration date if applicable' },
      { name: 'credential_id', type: 'string | null', required: false, description: 'License verification identifier' },
      { name: 'url', type: 'string | null', required: false, description: 'Verification hyperlink' },
    ],
  },
  {
    name: 'Achievement',
    icon: <Sparkles className="w-4 h-4 text-amber-500" />,
    description: 'Awards, competition prizes, and distinguished honors.',
    fields: [
      { name: 'title', type: 'string', required: true, description: 'Honor or award title', validation: 'Non-empty string' },
      { name: 'issuer', type: 'string | null', required: false, description: 'Granting authority or competition' },
      { name: 'date', type: 'string | null', required: false, description: 'Award date or year' },
      { name: 'description', type: 'string | null', required: false, description: 'Context and criteria' },
    ],
  },
  {
    name: 'Resume (Root)',
    icon: <Layers className="w-4 h-4 text-emerald-600" />,
    description: 'Root container uniting all parsed resume components.',
    fields: [
      { name: 'personal_info', type: 'PersonalInfo', required: true, description: 'Candidate identity and contact info' },
      { name: 'summary', type: 'string | null', required: false, description: 'Executive or career summary paragraph' },
      { name: 'objective', type: 'string | null', required: false, description: 'Career objective statement' },
      { name: 'education', type: 'Education[]', required: false, description: 'List of educational degrees' },
      { name: 'skills', type: 'SkillSet', required: false, description: 'Categorized technical & soft skill set' },
      { name: 'experience', type: 'Experience[]', required: false, description: 'Employment and internship history' },
      { name: 'projects', type: 'Project[]', required: false, description: 'Technical portfolio projects' },
      { name: 'certifications', type: 'Certification[]', required: false, description: 'Professional certifications' },
      { name: 'achievements', type: 'Achievement[]', required: false, description: 'Awards and honors' },
      { name: 'languages', type: 'string[]', required: false, description: 'Spoken language proficiencies' },
      { name: 'interests', type: 'string[]', required: false, description: 'Personal hobbies and interests' },
    ],
  },
];

export const SchemaViewer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'models' | 'json' | 'sample'>('models');
  const [selectedModel, setSelectedModel] = useState<string>('Resume (Root)');
  const [rawSchema, setRawSchema] = useState<Record<string, unknown> | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    fetchResumeSchema()
      .then((schema) => setRawSchema(schema))
      .catch(() => {
        // Fallback gracefully
      });
  }, []);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const currentSpec = MODELS_SPEC.find((m) => m.name === selectedModel) || MODELS_SPEC[0];

  const sampleJson = {
    personal_info: {
      full_name: "Maya Lin",
      email: "maya.lin@domain.org",
      phone: "+1 (555) 432-8765",
      location: "Seattle, WA",
      linkedin_url: "https://linkedin.com/in/mayalin",
      github_url: "https://github.com/mayalin",
      portfolio_url: "https://mayalin.dev"
    },
    summary: "Senior Distributed Systems Engineer with 8 years of experience building resilient cloud infrastructure.",
    objective: "To lead high-impact infrastructure teams scaling planetary-scale platforms.",
    education: [
      {
        institution: "University of Washington",
        degree: "B.S.",
        field_of_study: "Computer Science",
        start_date: "2014",
        end_date: "2018",
        gpa: 3.92,
        gpa_max: 4.0,
        honors: ["Summa Cum Laude", "Dean's List"],
        courses: ["Operating Systems", "Distributed Systems", "Algorithms"]
      }
    ],
    skills: {
      technical_skills: ["Microservices", "System Design", "Observability"],
      programming_languages: ["Go", "Rust", "Python", "SQL"],
      frameworks_and_libraries: ["FastAPI", "Tokio", "gRPC"],
      databases: ["PostgreSQL", "Redis", "CockroachDB"],
      cloud_and_devops: ["AWS", "Kubernetes", "Terraform", "Docker"],
      soft_skills: ["Mentorship", "Technical Writing"],
      tools: ["Git", "Prometheus", "Grafana"]
    },
    experience: [
      {
        company: "CloudNative Systems",
        title: "Principal Infrastructure Engineer",
        location: "Seattle, WA (Hybrid)",
        start_date: "2021-03",
        end_date: "Present",
        is_current: true,
        highlights: [
          "Led zero-downtime migration of 140+ microservices to Kubernetes.",
          "Reduced 99th percentile API latency from 450ms to 42ms."
        ],
        technologies: ["Go", "Kubernetes", "Envoy", "Terraform"]
      }
    ],
    projects: [
      {
        name: "HyperSync Raft",
        description: "Fault-tolerant consensus module implemented in Rust.",
        url: "https://github.com/mayalin/hypersync-raft",
        highlights: ["Achieved 120,000 replicated ops/sec across 5-node cluster."],
        technologies: ["Rust", "Tokio"],
        start_date: "2023-01",
        end_date: "2023-06"
      }
    ],
    certifications: [
      {
        name: "AWS Certified Solutions Architect - Professional",
        issuer: "Amazon Web Services",
        issue_date: "2022-09",
        expiration_date: "2025-09",
        credential_id: "AWS-PSA-894719",
        url: "https://aws.amazon.com/verification"
      }
    ],
    achievements: [
      {
        title: "Best Innovation Award 2023",
        issuer: "CloudNative Systems Annual Summit",
        date: "2023-11",
        description: "Awarded for autonomous cluster auto-scaler reducing cloud costs by 35%."
      }
    ],
    languages: ["English (Native)", "Mandarin (Professional)"],
    interests: ["Mountaineering", "Open Source Contributing"]
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm p-6 sm:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-100">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-semibold mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            Phase 7: Structured Resume Schema
          </div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight">
            Pydantic Domain Models
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Strict type validation, sensible optionality, and canonical schema for LLM extraction.
          </p>
        </div>

        {/* Tab switchers */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab('models')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeTab === 'models'
                ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Models Explorer
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('json')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeTab === 'json'
                ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            OpenAPI Schema
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('sample')}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeTab === 'sample'
                ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Sample Resume JSON
          </button>
        </div>
      </div>

      {/* Main Body */}
      <div className="mt-6">
        {activeTab === 'models' && (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Model Selector Sidebar */}
            <div className="md:col-span-4 space-y-1.5">
              <span className="text-xs font-semibold text-slate-400 block px-1 mb-2">
                Pydantic Models ({MODELS_SPEC.length})
              </span>
              {MODELS_SPEC.map((spec) => {
                const isSelected = selectedModel === spec.name;
                return (
                  <button
                    key={spec.name}
                    type="button"
                    onClick={() => setSelectedModel(spec.name)}
                    className={`w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between gap-3 cursor-pointer ${
                      isSelected
                        ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950 font-semibold shadow-2xs'
                        : 'bg-white border-slate-200/80 text-slate-700 hover:bg-slate-50/80'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className="p-1.5 rounded-lg bg-white shadow-2xs shrink-0">
                        {spec.icon}
                      </div>
                      <div className="min-w-0">
                        <span className="block text-xs font-mono font-semibold truncate">
                          {spec.name}
                        </span>
                        <span className="block text-[11px] text-slate-400 truncate">
                          {spec.fields.length} attributes
                        </span>
                      </div>
                    </div>
                    <ChevronRight
                      className={`w-3.5 h-3.5 ${
                        isSelected ? 'text-emerald-600 translate-x-0.5' : 'text-slate-300'
                      }`}
                    />
                  </button>
                );
              })}
            </div>

            {/* Model Field Table */}
            <div className="md:col-span-8 bg-slate-50/70 rounded-xl border border-slate-200/80 p-5">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  {currentSpec.icon}
                  <h4 className="text-sm font-bold text-slate-900 font-mono">
                    {currentSpec.name}
                  </h4>
                </div>
                <span className="text-xs text-slate-500">
                  {currentSpec.description}
                </span>
              </div>

              {/* Fields Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 font-semibold">
                      <th className="pb-2">Field Name</th>
                      <th className="pb-2">Type</th>
                      <th className="pb-2">Required</th>
                      <th className="pb-2">Description &amp; Validation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 font-mono">
                    {currentSpec.fields.map((field) => (
                      <tr key={field.name} className="hover:bg-white/80 transition-colors">
                        <td className="py-2.5 font-bold text-slate-800">
                          {field.name}
                        </td>
                        <td className="py-2.5 text-indigo-600 text-[11px]">
                          {field.type}
                        </td>
                        <td className="py-2.5">
                          {field.required ? (
                            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 text-[10px] font-semibold">
                              Required
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 text-[10px]">
                              Optional
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 font-sans text-slate-600 text-[11px]">
                          <div>{field.description}</div>
                          {field.validation && (
                            <div className="text-[10px] text-emerald-700 mt-0.5 font-mono">
                              Rule: {field.validation}
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'json' && (
          <div className="relative">
            <div className="flex items-center justify-between pb-3 mb-2">
              <span className="text-xs text-slate-500 flex items-center gap-1.5">
                <FileCode className="w-4 h-4 text-emerald-600" />
                Live JSON Schema Specification from FastAPI (`/api/resumes/schema`)
              </span>
              <button
                type="button"
                onClick={() => handleCopy(JSON.stringify(rawSchema, null, 2))}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 shadow-2xs cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
                {copied ? 'Copied' : 'Copy JSON'}
              </button>
            </div>
            <pre className="bg-slate-900 text-slate-100 rounded-xl p-5 text-xs font-mono overflow-x-auto max-h-[480px] leading-relaxed selection:bg-emerald-500 selection:text-white">
              {rawSchema ? JSON.stringify(rawSchema, null, 2) : 'Loading OpenAPI schema...'}
            </pre>
          </div>
        )}

        {activeTab === 'sample' && (
          <div className="relative">
            <div className="flex items-center justify-between pb-3 mb-2">
              <span className="text-xs text-slate-500 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Sample Valid Resume Instance (Tested against Pydantic validation suite)
              </span>
              <button
                type="button"
                onClick={() => handleCopy(JSON.stringify(sampleJson, null, 2))}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 shadow-2xs cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
                {copied ? 'Copied' : 'Copy JSON'}
              </button>
            </div>
            <pre className="bg-slate-900 text-slate-100 rounded-xl p-5 text-xs font-mono overflow-x-auto max-h-[480px] leading-relaxed selection:bg-emerald-500 selection:text-white">
              {JSON.stringify(sampleJson, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
