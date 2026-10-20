/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Header } from './components/Header';
import { ResumeUpload } from './components/ResumeUpload';
import { TextExtractionViewer } from './components/TextExtractionViewer';
import { SectionViewer } from './components/SectionViewer';
import { NLPViewer } from './components/NLPViewer';
import { StructuredResumeViewer } from './components/StructuredResumeViewer';
import { SkillNormalizationViewer } from './components/SkillNormalizationViewer';
import { DatabasePersistenceViewer } from './components/DatabasePersistenceViewer';
import { ResumePipelineViewer } from './components/ResumePipelineViewer';
import { ResumeDashboard } from './components/dashboard';
import { JobMatchingDashboard } from './components/job-matching';
import { UserHistoryDashboard } from './components/history';
import { JobDescriptionViewer } from './components/JobDescriptionViewer';
import { ResumeJobMatcher } from './components/ResumeJobMatcher';
import { SemanticSimilarityViewer } from './components/SemanticSimilarityViewer';
import { ResumeAnalysisViewer } from './components/ResumeAnalysisViewer';
import { SchemaViewer } from './components/SchemaViewer';
import { HealthStatus } from './components/HealthStatus';
import { ArchitectureView } from './components/ArchitectureView';
import { PhaseTracker } from './components/PhaseTracker';
import { ResumeUploadResponse } from './types/resume';

export default function App() {
  const [lastUploaded, setLastUploaded] = useState<ResumeUploadResponse | null>(null);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans flex flex-col">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Phase 20: User History & Records Archive */}
        <section>
          <UserHistoryDashboard />
        </section>

        {/* Phase 19: Job Matching UI Dashboard */}
        <section>
          <JobMatchingDashboard
            currentResumeId={lastUploaded?.filename}
          />
        </section>

        {/* Phase 13: Resume Dashboard (Reusable Components) */}
        <section>
          <ResumeDashboard />
        </section>

        {/* Phase 14: Job Description Parsing */}
        <section>
          <JobDescriptionViewer />
        </section>

        {/* Phase 15: Resume-Job Requirement Matching */}
        <section>
          <ResumeJobMatcher />
        </section>

        {/* Phase 16: Semantic Similarity Using Dense Embeddings */}
        <section>
          <SemanticSimilarityViewer />
        </section>

        {/* Phase 17: AI Resume Quality Analysis */}
        <section>
          <ResumeAnalysisViewer
            resumeId={lastUploaded?.filename}
          />
        </section>

        {/* Phase 12: Complete Resume Processing Pipeline Orchestrator */}
        <section>
          <ResumePipelineViewer />
        </section>

        {/* Phase 2: Resume Upload Component */}
        <section>
          <ResumeUpload onUploadSuccess={(res) => setLastUploaded(res)} />

          {/* Phase 3, 4, 5: Text Extraction & Preprocessing Viewer */}
          {lastUploaded && (
            <TextExtractionViewer
              resumeId={lastUploaded.filename}
              originalFilename={lastUploaded.original_filename}
            />
          )}

          {/* Phase 6: Resume Section Detection Viewer */}
          {lastUploaded && (
            <SectionViewer
              resumeId={lastUploaded.filename}
              originalFilename={lastUploaded.original_filename}
            />
          )}

          {/* Phase 8: spaCy NLP Preprocessing Viewer */}
          {lastUploaded && (
            <NLPViewer
              resumeId={lastUploaded.filename}
              originalFilename={lastUploaded.original_filename}
            />
          )}

          {/* Phase 9: AI Structured Resume Parser Viewer */}
          {lastUploaded && (
            <StructuredResumeViewer
              resumeId={lastUploaded.filename}
              originalFilename={lastUploaded.original_filename}
            />
          )}
        </section>

        {/* Phase 10: Skill Normalization & Taxonomy */}
        <section>
          <SkillNormalizationViewer />
        </section>

        {/* Phase 11: PostgreSQL Database Persistence */}
        <section>
          <DatabasePersistenceViewer />
        </section>

        {/* Phase 7: Structured Resume Schema Viewer */}
        <section>
          <SchemaViewer />
        </section>

        {/* Backend health check card */}
        <section>
          <HealthStatus />
        </section>

        {/* Monorepo Architecture Overview */}
        <section>
          <ArchitectureView />
        </section>

        {/* Phase Tracker */}
        <section>
          <PhaseTracker />
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
          <span>AI Resume Parser &amp; Job Matcher • Phase 16: Semantic Similarity Using Embeddings</span>
          <span>FastAPI • PostgreSQL • SQLAlchemy • React + TypeScript • Accessible &amp; Responsive Component Library</span>
        </div>
      </footer>
    </div>
  );
}
