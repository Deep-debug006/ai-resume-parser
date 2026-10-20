import React, { useState, useEffect } from 'react';
import {
  Database,
  Server,
  RefreshCw,
  PlusCircle,
  Trash2,
  Eye,
  CheckCircle2,
  Clock,
  User,
  Mail,
  FileText,
  Briefcase,
  GraduationCap,
  Wrench,
  Award,
  Layers,
  Sparkles,
  ShieldCheck,
  Check,
} from 'lucide-react';
import { DBResumeSummary, DBResumeDetail, DBStats } from '../types/database';
import {
  listDBResumes,
  getDBResume,
  deleteDBResume,
  seedDB,
  getDBStats,
} from '../services/api';

export const DatabasePersistenceViewer: React.FC = () => {
  const [resumes, setResumes] = useState<DBResumeSummary[]>([]);
  const [stats, setStats] = useState<DBStats | null>(null);
  const [selectedResume, setSelectedResume] = useState<DBResumeDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [resumesData, statsData] = await Promise.all([
        listDBResumes(),
        getDBStats().catch(() => null),
      ]);
      setResumes(resumesData);
      if (statsData) setStats(statsData);
    } catch (err: any) {
      setError(err.message || 'Failed to communicate with PostgreSQL database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeed = async () => {
    setSeeding(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const seeded = await seedDB();
      setSuccessMsg(`Seeded sample resume for ${seeded.resume.personal_info.full_name}!`);
      await fetchData();
      setSelectedResume(seeded);
    } catch (err: any) {
      setError(err.message || 'Failed to seed sample data.');
    } finally {
      setSeeding(false);
    }
  };

  const handleSelect = async (id: string) => {
    try {
      const detail = await getDBResume(id);
      setSelectedResume(detail);
    } catch (err: any) {
      setError(err.message || 'Failed to load resume details.');
    }
  };

  const handleDelete = async (id: string) => {
    setDeletingId(id);
    try {
      await deleteDBResume(id);
      if (selectedResume?.id === id) {
        setSelectedResume(null);
      }
      await fetchData();
      setSuccessMsg('Resume and all cascaded relations successfully removed from database.');
    } catch (err: any) {
      setError(err.message || 'Failed to delete resume.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-sky-200/80 shadow-xs p-6 transition-all">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-100 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-1.5 bg-sky-100 text-sky-800 rounded-lg">
              <Database className="w-4 h-4" />
            </div>
            <h2 className="text-base font-semibold text-slate-900">
              Phase 11: PostgreSQL Database Persistence
            </h2>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-sky-50 text-sky-700 border border-sky-200 rounded uppercase">
              SQLAlchemy &amp; Alembic
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Normalized relational database storage for users, resumes, personal info, education, skills, experience, projects, certs, and achievements.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-xl border border-slate-200 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleSeed}
            disabled={seeding}
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 disabled:bg-sky-300 text-white text-xs font-semibold rounded-xl shadow-xs transition-all"
          >
            {seeding ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Seeding...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                Seed Sample Resume
              </>
            )}
          </button>
        </div>
      </div>

      {/* Metrics Bar */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-[11px] text-slate-500 font-semibold uppercase">Engine</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Server className="w-3.5 h-3.5 text-sky-600" />
              <span className="text-xs font-bold text-slate-800">PostgreSQL 15</span>
            </div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-[11px] text-slate-500 font-semibold uppercase">Persisted Resumes</span>
            <div className="text-base font-bold text-sky-900 font-mono mt-0.5">{stats.total_resumes}</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-[11px] text-slate-500 font-semibold uppercase">Skills Indexed</span>
            <div className="text-base font-bold text-emerald-900 font-mono mt-0.5">{stats.total_skills}</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <span className="text-[11px] text-slate-500 font-semibold uppercase">Registered Users</span>
            <div className="text-base font-bold text-indigo-900 font-mono mt-0.5">{stats.total_users}</div>
          </div>
        </div>
      )}

      {/* Messages */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 text-xs text-red-700 rounded-xl">
          {error}
        </div>
      )}

      {successMsg && (
        <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 rounded-xl flex items-center justify-between">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            {successMsg}
          </span>
          <button onClick={() => setSuccessMsg(null)} className="text-xs text-slate-400 hover:text-slate-600">
            Dismiss
          </button>
        </div>
      )}

      {/* Main Grid: Resumes Table & Detail Pane */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mt-5">
        {/* Resumes List Column */}
        <div className={selectedResume ? 'lg:col-span-5' : 'lg:col-span-12'}>
          <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                PostgreSQL Resumes ({resumes.length})
              </span>
              <span className="text-[11px] text-slate-500">Alembic Migrations Applied</span>
            </div>

            {resumes.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs">
                No resumes currently saved in PostgreSQL.
                <div className="mt-2">
                  <button
                    onClick={handleSeed}
                    className="text-sky-600 font-semibold hover:underline inline-flex items-center gap-1"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    Load Sample Resume Data
                  </button>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
                {resumes.map((r) => {
                  const isSelected = selectedResume?.id === r.id;
                  return (
                    <div
                      key={r.id}
                      className={`p-3.5 transition-colors flex items-center justify-between gap-3 ${
                        isSelected ? 'bg-sky-50/80 border-l-4 border-sky-600' : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-900 truncate">
                            {r.candidate_name}
                          </span>
                          <span className="px-1.5 py-0.2 bg-emerald-100 text-emerald-800 text-[10px] font-bold rounded uppercase">
                            {r.processing_status}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-500 truncate mt-0.5 flex items-center gap-2">
                          <span>{r.original_filename}</span>
                          <span>•</span>
                          <span>{r.raw_text_char_count} chars</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1.5 shrink-0">
                        <button
                          onClick={() => handleSelect(r.id)}
                          className="p-1.5 bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-lg text-xs"
                          title="View Details"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDelete(r.id)}
                          disabled={deletingId === r.id}
                          className="p-1.5 bg-white hover:bg-red-50 text-red-600 border border-slate-200 hover:border-red-200 rounded-lg text-xs transition-colors"
                          title="Delete from PostgreSQL"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Selected Resume Detail Column */}
        {selectedResume && (
          <div className="lg:col-span-7">
            <div className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-4">
              {/* Header Bar */}
              <div className="flex items-start justify-between pb-3 border-b border-slate-200/80 gap-3">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <User className="w-4 h-4 text-sky-600" />
                    {selectedResume.resume.personal_info.full_name}
                  </h3>
                  <div className="flex flex-wrap items-center gap-x-3 text-xs text-slate-500 mt-1">
                    {selectedResume.resume.personal_info.email && (
                      <span className="flex items-center gap-1">
                        <Mail className="w-3 h-3" />
                        {selectedResume.resume.personal_info.email}
                      </span>
                    )}
                    <span>ID: <code className="font-mono text-[10px] bg-white px-1 py-0.5 rounded border border-slate-200">{selectedResume.id.slice(0, 8)}...</code></span>
                  </div>
                </div>

                <button
                  onClick={() => setSelectedResume(null)}
                  className="text-xs text-slate-400 hover:text-slate-600"
                >
                  Close ✕
                </button>
              </div>

              {/* Summary */}
              {selectedResume.resume.summary && (
                <div className="text-xs text-slate-700 bg-white p-3 rounded-lg border border-slate-200">
                  <span className="font-semibold text-slate-900 block mb-0.5">Summary:</span>
                  {selectedResume.resume.summary}
                </div>
              )}

              {/* Relational Tables Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {/* Work Experience */}
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <span className="font-bold text-slate-800 flex items-center gap-1 mb-2">
                    <Briefcase className="w-3.5 h-3.5 text-sky-600" />
                    Experience ({selectedResume.resume.experience?.length || 0})
                  </span>
                  <div className="space-y-2">
                    {selectedResume.resume.experience?.map((exp, i) => (
                      <div key={i} className="border-l-2 border-sky-400 pl-2">
                        <span className="font-semibold block text-slate-900">{exp.title}</span>
                        <span className="text-slate-500 text-[11px]">{exp.company} • {exp.start_date} - {exp.end_date || 'Present'}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Education */}
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <span className="font-bold text-slate-800 flex items-center gap-1 mb-2">
                    <GraduationCap className="w-3.5 h-3.5 text-sky-600" />
                    Education ({selectedResume.resume.education?.length || 0})
                  </span>
                  <div className="space-y-2">
                    {selectedResume.resume.education?.map((edu, i) => (
                      <div key={i} className="border-l-2 border-indigo-400 pl-2">
                        <span className="font-semibold block text-slate-900">{edu.institution}</span>
                        <span className="text-slate-500 text-[11px]">{edu.degree} in {edu.field_of_study}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Skills Normalized Relational View */}
              {selectedResume.resume.skills && (
                <div className="p-3 bg-white border border-slate-200 rounded-lg">
                  <span className="font-bold text-slate-800 flex items-center gap-1 mb-2 text-xs">
                    <Wrench className="w-3.5 h-3.5 text-sky-600" />
                    Linked Relational Skills (resume_skills table)
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(selectedResume.resume.skills).flatMap(([cat, list]) =>
                      (list as string[]).map((sk, idx) => (
                        <span
                          key={`${cat}-${idx}`}
                          className="px-2 py-0.5 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-800 font-mono"
                        >
                          {sk}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
