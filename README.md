# AI Resume Parser & Job Matcher

> A production-grade, privacy-conscious full-stack platform for deterministic resume parsing, OCR fallback, structured entity extraction, skill normalization, and explainable job requirement matching.

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/Frontend-React_19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_16_with_pgvector-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Container-Docker_Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-161_Passing_(100%25)-brightgreen.svg)]()

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [Features](#3-features)
4. [Architecture (Deep Dive for Technical Interviews)](#4-architecture)
5. [Tech Stack](#5-tech-stack)
6. [System Workflow](#6-system-workflow)
7. [AI & NLP Pipeline](#7-ai--nlp-pipeline)
8. [Database Design](#8-database-design)
9. [API Endpoints Reference](#9-api-endpoints-reference)
10. [Folder Structure](#10-folder-structure)
11. [Installation](#11-installation)
12. [Environment Variables](#12-environment-variables)
13. [Local Development](#13-local-development)
14. [Docker Setup](#14-docker-setup)
15. [Testing Strategy](#15-testing-strategy)
16. [Security Considerations](#16-security-considerations)
17. [Limitations](#17-limitations)
18. [Future Improvements](#18-future-improvements)
19. [Screenshots & UI Placeholders](#19-screenshots--ui-placeholders)
20. [Author Section](#20-author-section)

---

## 1. Project Overview

**AI Resume Parser & Job Matcher** is an end-to-end engineering solution designed to process unstructured resume documents (PDF format, digital or scanned), transform them into validated canonical schema models, and deliver transparent, explainable alignment analyses against employer job descriptions.

Unlike opaque "black box" resume screening tools, this application enforces strict **anti-hallucination guardrails**:
- The model extracts only factual information explicitly verified in the text.
- Missing credentials, metrics, or employers are recorded as `null` or empty collections rather than fabricated.
- Matching outputs differentiate between deterministic lexical skill overlap and dense semantic proximity.
- All scoring outputs are explicitly framed as informational comparison metrics rather than automated hiring predictions.

---

## 2. Problem Statement

Automated Applicant Tracking Systems (ATS) and resume parsers routinely fail or produce skewed results due to three foundational engineering flaws:

1. **Brittle Document Ingestion**: Standard PDF extractors fail when encountering multi-column text, ligature characters (`fi`, `fl`), broken hyphens across line breaks, or scanned document images, resulting in unreadable gibberish.
2. **Generative LLM Hallucinations**: Standard LLM integrations frequently invent missing degrees, inflate candidate tenures, or fabricate quantifiable achievements to satisfy rigid prompt structures.
3. **Opaque & Biased Scoring**: Arbitrary "fit percentages" often conflate exact keyword presence with conceptual capability while offering zero audit trail or explainability to human recruiters and candidates.

This project addresses these challenges through a **hybrid multi-stage pipeline**: combining high-throughput deterministic text cleaning, local named entity recognition (spaCy), schema-enforced LLM repair loops (Pydantic v2), relational normalization, and transparent vector similarity using `pgvector`.

---

## 3. Features

* **Multi-Format PDF Extraction**: Native multi-page digital parsing with PyMuPDF preserving line boundaries and column structure.
* **Intelligent OCR Fallback**: Automated detection of scanned or image-only pages triggering Tesseract OCR with configurable character-density thresholds (`< 50 chars/page`).
* **Deterministic Text Normalization**: NFKC Unicode conversion, ligature resolution, cross-line dehyphenation, and whitespace normalization while preserving emails, phone numbers, URLs, numbers, and casing.
* **Canonical Section Segmentation**: Robust boundary detection mapping 13 standard sections (Contact, Summary, Education, Skills, Experience, Projects, Certifications, Achievements, Publications, etc.).
* **Linguistic NER Anchoring**: Non-destructive entity recognition (spaCy) isolating candidate names, organizations, locations, dates, and links as factual reference points.
* **Schema-Enforced LLM Extraction**: Strongly-typed extraction into Pydantic models with automated schema validation and controlled prompt repair retries.
* **Deterministic Skill Normalization**: Tri-gram and alias dictionary resolution mapping non-standard technological aliases (e.g., `React.js` $\to$ `React`, `k8s` $\to$ `Kubernetes`, `Postgres` $\to$ `PostgreSQL`).
* **Relational Storage & Cascading Deletion**: Fully normalized 3NF PostgreSQL tables with child relations for education, experience, skills, projects, and credentials.
* **Explainable Resume-Job Matching**:
  - *Deterministic Skill Match*: Direct overlap of required vs. preferred competencies.
  - *Dense Semantic Similarity*: 768-dimensional vector representations (`text-embedding-004`) computed via cosine distance with content-hash caching.
  - *Experience & Education Alignment*: Explainable tenure and degree comparisons.
* **Objective AI Resume Quality Analysis**: Evaluates clarity, bullet point impact, quantifiable results, and completeness without fabricating facts or metrics.
* **Authentication & Multi-Tenant Isolation**: Secure JWT Bearer authentication with password hashing (bcrypt), enforcing strict cross-user resource isolation.
* **Pagination & Lightweight History**: Filterable, paginated history summaries preventing large binary or JSON payload bloat over the wire.
* **Full Docker Orchestration**: Production-ready `docker-compose` topology with persistent PostgreSQL volume, Nginx reverse proxy, and health checks.

---

## 4. Architecture

### System Architecture Diagram

```
                             ┌───────────────────────────────────────┐
                             │       Web Browser (Client)            │
                             │       React 19 + Tailwind CSS         │
                             └──────────────────┬────────────────────┘
                                                │ Port 3000 (HTTP / REST)
                                                ▼
                             ┌───────────────────────────────────────┐
                             │       Nginx Reverse Proxy             │
                             │   (Static Assets & /api routing)      │
                             └──────────────────┬────────────────────┘
                                                │ Port 8001
                                                ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 FastAPI Backend (Port 8001)                            │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              API Routing Layer                                 │   │
│   │   /api/auth   •   /api/resumes   •   /api/jobs   •   /api/skills   •   /api/history│   │
│   └──────┬──────────────────────┬─────────────────────────┬────────────────────────┘   │
│          │                      │                         │                            │
│          ▼                      ▼                         ▼                            │
│   ┌──────────────┐      ┌──────────────┐          ┌──────────────┐                     │
│   │ Auth Service │      │ Ingestion &  │          │ Matching &   │                     │
│   │ (JWT/bcrypt) │      │ OCR Service  │          │ Vector Search│                     │
│   └──────────────┘      └──────┬───────┘          └──────┬───────┘                     │
│                                │                         │                             │
│                                ▼                         │                             │
│                         ┌──────────────┐                 │                             │
│                         │ Preprocessor │                 │                             │
│                         │ (Clean+spaCy)│                 │                             │
│                         └──────┬───────┘                 │                             │
│                                │                         │                             │
│                                ▼                         │                             │
│                         ┌──────────────┐                 │                             │
│                         │ LLM Service  │                 │                             │
│                         │(Repair Loop) │                 │                             │
│                         └──────┬───────┘                 │                             │
│                                │                         │                             │
│                                ▼                         ▼                             │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                       SQLAlchemy ORM & Repository Layer                        │   │
│   └────────────────────────────────────┬───────────────────────────────────────────┘   │
└────────────────────────────────────────┼───────────────────────────────────────────────┘
                                         │ TCP Port 5432
                                         ▼
                 ┌──────────────────────────────────────────────┐
                 │          PostgreSQL 16 Database              │
                 │   - 3NF Normalized Entities                  │
                 │   - pgvector (768-dim embeddings)            │
                 │   - Persistent Volume (postgres_data)        │
                 └──────────────────────────────────────────────┘
```

### Architectural Principles for Technical Interviews

1. **Separation of Determinism and Heuristics**:
   - File validation, PDF character extraction, text cleansing, section boundary detection, and skill normalization are **100% deterministic**. They do not rely on LLM unpredictability.
   - LLMs are reserved strictly for high-dimensional semantic structuring into strict JSON schemas.

2. **Guaranteed Output Conformity (The Controlled Repair Loop)**:
   - When an LLM produces output, it is immediately parsed and validated against the Pydantic v2 `Resume` schema.
   - If validation fails (e.g., malformed email or missing required fields), the system does not crash or return a 500 error. Instead, it extracts the exact field paths and error messages, constructs a targeted repair prompt, and re-invokes the provider (up to a configurable maximum of 2 retries).
   - If provider connectivity fails completely, the engine gracefully falls back to a deterministic rule-based extractor.

3. **Multi-User Resource Isolation**:
   - Resumes, job descriptions, and analysis history records maintain foreign key references to `users.id`.
   - The dependency injection layer (`get_current_user`) verifies JWT signatures, and database queries automatically filter records to the authenticated caller (`WHERE user_id = current_user.id`).
   - Cross-user access attempts trigger immediate `403 Forbidden` responses.

4. **Zero Cloud Lock-in / Multi-Provider Abstraction**:
   - All AI interactions pass through the `LLMProvider` abstract base class.
   - Swapping between Gemini, OpenAI, Claude, or local mock fixtures requires changing a single environment variable (`LLM_PROVIDER=gemini` vs `LLM_PROVIDER=mock`) without altering business logic.

---

## 5. Tech Stack

### Backend
- **Language**: Python 3.11
- **Web Framework**: FastAPI (high-concurrency ASGI)
- **Data Validation & Schemas**: Pydantic v2 & `pydantic-settings`
- **Database & ORM**: PostgreSQL 16, SQLAlchemy 2.0, Alembic migrations
- **Vector Extensions**: `pgvector` (cosine distance indexing)
- **Document Processing**: PyMuPDF (`pymupdf`), Pillow
- **OCR Engine**: Tesseract OCR 5.3 (`pytesseract`)
- **NLP & Linguistics**: spaCy (`en_core_web_sm`)
- **Authentication**: Python-Jose (JWT), Passlib / Bcrypt

### Frontend
- **Framework**: React 19 SPA
- **Build Tooling**: Vite 8 with Rollup
- **Styling**: Tailwind CSS v4
- **Iconography**: Lucide React
- **HTTP Client**: Native Fetch API with custom auth & Bearer interceptors

### DevOps & Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server & Reverse Proxy**: Nginx Alpine
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient

---

## 6. System Workflow

```
[1. Upload PDF] ──> [2. Validate Magic Bytes (%PDF-)]
                            │
                            ▼
                    [3. PyMuPDF Extract] 
                            │
              (Chars < 50/page?) ──Yes──> [4. Tesseract OCR Fallback]
                            │                     │
                            └──No─────────────────┘
                            │
                            ▼
                    [5. Text Preprocessing]
                    - NFKC Unicode Normalization
                    - Dehyphenation & Ligatures
                    - Whitespace Compaction
                            │
                            ▼
                    [6. Section Detection]
                    - Split into 13 Canonical Buckets
                            │
                            ▼
                    [7. spaCy Linguistic NER]
                    - Extract PERSON, ORG, LOC, DATE
                            │
                            ▼
                    [8. LLM Extraction & Validation]
                    - JSON schema generation
                    - Pydantic validation
                    - Controlled repair loop on error
                            │
                            ▼
                    [9. Skill Normalization]
                    - Alias canonicalization (k8s -> Kubernetes)
                            │
                            ▼
                    [10. PostgreSQL 3NF Persistence]
                            │
                            ├──────────────────────────┐
                            ▼                          ▼
               [11A. Exact Skill Match]   [11B. 768-dim Vector Similarity]
                            │                          │
                            └──────────┬───────────────┘
                                       ▼
                       [12. Unified Matching Report]
                       - Matched vs Missing Skills
                       - Explainable Experience Analysis
                       - Cosine Proximity Score
```

---

## 7. AI & NLP Pipeline

The platform uses a layered pipeline designed to balance speed, cost, and absolute accuracy:

### Stage 1: Document Extraction & Quality Assessment
- **Digital Extraction**: PyMuPDF processes the document, extracting text runs and preserving line breaks.
- **Density Heuristic**: The character density per page is calculated. If the density falls below 50 characters, the page is flagged as scanned or rasterized.
- **OCR Engine**: Tesseract OCR renders raster pages at 200 DPI, performing optical character recognition with image contrast enhancement.

### Stage 2: Linguistic Normalization (spaCy)
- **Unicode Resolution**: Converts composite characters into standard NFKC representations.
- **Ligature Mapping**: Replaces typographic ligatures (`ﬁ` $\to$ `fi`, `ﬂ` $\to$ `fl`, `ﬀ` $\to$ `ff`).
- **Dehyphenation**: Identifies word fragments split by line-ending hyphens (`micro-\nservices` $\to$ `microservices`).
- **Named Entity Recognition**: Identifies linguistic entities without modifying source text. Organizations, institutions, and candidate names serve as factual grounding anchors.

### Stage 3: Generative Extraction with Anti-Hallucination Controls
- **System Instruction**: Explicitly forbids fabricating details, inventing dates, or generating fake metrics.
- **Pydantic Validation**: Responses are validated against the strict canonical `Resume` schema.
- **Controlled Repair**: Validation failures trigger targeted re-prompts pointing to exact field paths.

### Stage 4: Semantic Embeddings & Matching
- **Dense Vectorization**: Generates 768-dimensional normalized vectors via Google's `text-embedding-004` (or deterministic mock in offline test environments).
- **Content-Hash Caching**: Computes SHA-256 hashes of input texts before generating vectors to avoid redundant API charges and latency.
- **Cosine Similarity**: Vector comparison operates on normalized vector spaces ($[-1.0, 1.0] \to [0.0, 1.0]$).

---

## 8. Database Design

The relational schema is normalized into Third Normal Form (3NF) to avoid data redundancy and maintain referential integrity.

```
┌───────────────────────────┐         ┌───────────────────────────┐
│          users            │         │     job_descriptions      │
├───────────────────────────┤         ├───────────────────────────┤
│ id (UUID, PK)             │1       *│ id (UUID, PK)             │
│ email (VARCHAR, Unique)   ├─────────┤ user_id (UUID, FK)        │
│ hashed_password (VARCHAR) │         │ title (VARCHAR)           │
│ full_name (VARCHAR)       │         │ company (VARCHAR)         │
│ created_at (TIMESTAMP)    │         │ required_skills (JSONB)   │
└─────────────┬─────────────┘         │ preferred_skills (JSONB)  │
              │1                      │ raw_text (TEXT)           │
              │                       └───────────────────────────┘
              │*
┌─────────────┴─────────────┐         ┌───────────────────────────┐
│          resumes          │         │    analysis_history       │
├───────────────────────────┤         ├───────────────────────────┤
│ id (UUID, PK)             │1       *│ id (UUID, PK)             │
│ user_id (UUID, FK)        ├─────────┤ user_id (UUID, FK)        │
│ original_filename         │         │ resume_id (UUID, FK)      │
│ file_identifier           │         │ job_id (UUID, FK)         │
│ processing_status         │         │ match_rate (FLOAT)        │
│ extraction_method         │         │ result_data (JSONB)       │
│ raw_text_char_count       │         └───────────────────────────┘
└─────────────┬─────────────┘
              │1
              ├─────────────────────────┬─────────────────────────┬─────────────────────────┐
              │*                        │*                        │*                        │*
┌─────────────┴─────────────┐ ┌─────────┴───────────┐ ┌───────────┴─────────┐ ┌─────────────┴─────────┐
│    resume_personal_info   │ │      education      │ │     experience      │ │      resume_skills      │
├───────────────────────────┤ ├─────────────────────┤ ├─────────────────────┤ ├─────────────────────────┤
│ id (UUID, PK)             │ │ id (UUID, PK)       │ │ id (UUID, PK)       │ │ id (UUID, PK)           │
│ resume_id (UUID, FK)      │ │ resume_id (UUID, FK)│ │ resume_id (UUID, FK)│ │ resume_id (UUID, FK)    │
│ full_name (VARCHAR)       │ │ institution         │ │ company (VARCHAR)   │ │ skill_id (UUID, FK)     │
│ email (VARCHAR)           │ │ degree (VARCHAR)    │ │ title (VARCHAR)     │ │ normalized_name         │
│ phone, location           │ │ gpa, gpa_max (FLOAT)│ │ start_date, end_date│ │ category (VARCHAR)      │
│ linkedin_url, github_url  │ │ honors, courses     │ │ highlights (JSONB)  │ └────────────┬────────────┘
└───────────────────────────┘ └─────────────────────┘ └─────────────────────┘              │*
                                                                                           │
                                                                              ┌────────────┴────────────┐
                                                                              │         skills          │
                                                                              ├─────────────────────────┤
                                                                              │ id (UUID, PK)           │
                                                                              │ canonical_name (Unique) │
                                                                              │ category (VARCHAR)      │
                                                                              └─────────────────────────┘
```

### Vector Embeddings Table (`pgvector`)
```sql
CREATE TABLE vector_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    embedding vector(768) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_vector_embeddings_hash ON vector_embeddings(content_hash);
```

---

## 9. API Endpoints Reference

### Authentication (`/api/auth`)
| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new user account | No |
| `POST` | `/api/auth/login` | Login and obtain JWT Bearer access token | No |
| `GET` | `/api/auth/me` | Fetch currently authenticated user profile | Yes |

### Resume Ingestion & Processing (`/api/resumes`)
| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/resumes/upload` | Upload PDF file; validates MIME and magic bytes | No |
| `POST` | `/api/resumes/{id}/extract-text` | Extract raw text using PyMuPDF + OCR fallback | No |
| `POST` | `/api/resumes/{id}/sections` | Detect canonical section segments | No |
| `POST` | `/api/resumes/{id}/entities` | Extract linguistic Named Entities (spaCy) | No |
| `POST` | `/api/resumes/{id}/parse` | Structured extraction with Pydantic repair | No |
| `POST` | `/api/resumes/process` | End-to-end processing pipeline execution | No |
| `GET` | `/api/resumes/{id}/status` | Query pipeline processing lifecycle state | No |
| `GET` | `/api/resumes/schema` | Export canonical OpenAPI JSON schema specification | No |

### Relational Persistence (`/api/resumes/db`)
| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/resumes/db` | List persisted resumes (user-scoped if logged in) | Optional |
| `POST` | `/api/resumes/db` | Persist full structured resume into PostgreSQL | Optional |
| `GET` | `/api/resumes/db/{id}` | Retrieve complete resume with all child relations | Optional |
| `PUT` | `/api/resumes/db/{id}` | Update existing persisted resume | Yes |
| `DELETE` | `/api/resumes/db/{id}` | Delete resume with cascading foreign keys | Yes |
| `GET` | `/api/resumes/db/stats` | Retrieve database persistence counts & metrics | No |

### Skill Normalization (`/api/skills`)
| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/skills/normalize` | Normalize raw skill strings to canonical names | No |
| `GET` | `/api/skills/dictionary/stats` | View loaded aliases and categories | No |
| `POST` | `/api/skills/aliases` | Dynamically register new custom skill aliases | No |

### Job Descriptions & Matching (`/api/jobs`)
| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/jobs/parse` | Parse raw job description text into structured model | No |
| `POST` | `/api/jobs` | Save and persist structured job description | Optional |
| `GET` | `/api/jobs/{id}` | Fetch persisted job description | Optional |
| `POST` | `/api/jobs/match` | Deterministic keyword and qualification comparison | No |
| `POST` | `/api/jobs/semantic-match` | Dense 768-dim vector embedding similarity search | No |

### History & Auditing (`/api/history`)
| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/history/resumes` | Paginated lightweight resume summaries | Optional |
| `GET` | `/api/history/jobs` | Paginated job description history | Optional |
| `GET` | `/api/history/analyses` | Paginated matching and audit history | Optional |
| `GET` | `/api/history/summary` | Global aggregate record statistics | Optional |

---

## 10. Folder Structure

```
ai-resume-parser/
├── alembic.ini                      # Database migration configuration
├── docker-compose.yml               # Multi-container orchestration (DB, API, Web)
├── .dockerignore                    # Build context exclusions
├── .env.example                     # Environment template (zero secrets)
├── package.json                     # Frontend dependencies & scripts
├── vite.config.ts                   # Vite configuration & backend proxy
├── pytest.ini                       # Automated test configuration
├── index.html                       # SPA HTML entry point
│
├── backend/                         # FastAPI Python Application
│   ├── Dockerfile                   # Python 3.11 + OCR + spaCy container
│   ├── entrypoint.sh                # Container readiness and migration script
│   ├── requirements.txt             # Python dependencies
│   ├── alembic/                     # Database migration revisions
│   │   ├── env.py                   # Migration environment setup
│   │   └── versions/                # Versioned SQL migrations
│   │
│   ├── app/
│   │   ├── main.py                  # FastAPI application factory & lifespan
│   │   ├── core/                    # Security, auth dependencies, and settings
│   │   ├── db/                      # SQLAlchemy session, engine, and seed data
│   │   ├── models/                  # Declarative ORM models (3NF + pgvector)
│   │   ├── schemas/                 # Canonical Pydantic v2 domain schemas
│   │   ├── repositories/            # Data access layer (CRUD)
│   │   ├── routes/                  # API endpoints and route controllers
│   │   └── services/                # Business logic:
│   │       ├── storage_service.py   # Secure file uploads and validation
│   │       ├── pdf_parser.py        # PyMuPDF native document extraction
│   │       ├── ocr_service.py       # Tesseract OCR fallback
│   │       ├── text_cleaner.py      # Unicode, dehyphenation, formatting
│   │       ├── section_detector.py  # Canonical 13-section segmentation
│   │       ├── nlp_service.py       # Linguistic NER extraction (spaCy)
│   │       ├── llm_service.py       # Multi-provider abstraction & repair loops
│   │       ├── skill_normalizer.py  # Alias mapping and taxonomy resolver
│   │       ├── job_matcher.py       # Deterministic qualification comparison
│   │       └── semantic_matcher.py  # Dense vector embedding similarity
│   │
│   └── tests/                       # Complete automated test suite (161 tests)
│       ├── conftest.py              # Mock providers & isolated test fixtures
│       ├── test_upload.py           # Upload & security tests
│       ├── test_pdf_parser.py       # PDF extraction tests
│       ├── test_ocr_service.py      # OCR fallback tests
│       ├── test_text_cleaner.py     # Deterministic text cleaning tests
│       ├── test_section_detector.py # Section detection tests
│       ├── test_nlp_service.py      # spaCy NER tests
│       ├── test_resume_schema.py    # Schema validation tests
│       ├── test_llm_service.py      # LLM provider & repair tests
│       ├── test_skill_normalizer.py # Skill normalization tests
│       ├── test_database_persistence.py # Relational database CRUD tests
│       ├── test_job_description_parser.py # Job parsing tests
│       ├── test_job_matcher.py      # Deterministic matching tests
│       ├── test_semantic_embeddings.py # Vector embedding tests
│       ├── test_resume_analysis.py  # Resume feedback analysis tests
│       ├── test_auth.py             # Authentication & isolation tests
│       ├── test_history.py          # Paginated history tests
│       └── test_comprehensive_integration.py # End-to-end integration tests
│
├── frontend/                        # React SPA (Alternative Subdirectory)
│   ├── Dockerfile                   # Multi-stage Node 22 + Nginx container
│   ├── nginx.conf                   # Reverse proxy configuration
│   └── src/                         # React components, pages, and hooks
│
├── docs/
│   └── DOCKER.md                    # Comprehensive Docker operations manual
└── src/                             # Active React SPA Source Code
    ├── components/                  # UI components (Header, Upload, Tabs, etc.)
    ├── types/                       # TypeScript interfaces
    └── App.tsx                      # Root application layout
```

---

## 11. Installation

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 20+ (with npm)
- **Tesseract OCR**: 5.0+ (optional locally, automatically installed in Docker)
- **PostgreSQL**: 16+ (optional locally, automatically installed in Docker)

---

## 12. Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `POSTGRES_USER` | `postgres` | Database superuser |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `ai_resume_parser` | Relational database name |
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL |
| `DATABASE_URL` | `postgresql+psycopg2://...` | Connection URI for SQLAlchemy |
| `BACKEND_PORT` | `8001` | Host port for FastAPI API server |
| `FRONTEND_PORT` | `3000` | Host port for React frontend |
| `LLM_PROVIDER` | `gemini` | LLM backend: `gemini` or `mock` |
| `GEMINI_API_KEY` | *(empty)* | Optional Gemini API key |
| `EMBEDDING_PROVIDER`| `auto` | Vector provider: `auto`, `gemini`, `mock` |
| `JWT_SECRET_KEY` | *(secure default)* | 256-bit symmetric key for auth tokens |

---

## 13. Local Development

### 1. Backend Setup
```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Install spaCy model
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# 3. Launch FastAPI server with auto-reload
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```
API Documentation will be live at `http://localhost:8001/docs`.

### 2. Frontend Setup
```bash
# 1. Install Node packages
npm install

# 2. Launch Vite development server
npm run dev
```
The application will be live at `http://localhost:3000`.

---

## 14. Docker Setup

The entire application can be launched in one command without installing Python, Node, or PostgreSQL locally.

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and launch all containers
docker compose up --build -d
```

- **Web Application**: `http://localhost:3000`
- **FastAPI Documentation**: `http://localhost:8001/docs`
- **PostgreSQL Database**: `localhost:5432`

### Operational Commands
- **Stop application**: `docker compose down`
- **Reset database completely**: `docker compose down -v && docker compose up -d`
- **View live logs**: `docker compose logs -f backend`

*Refer to [`docs/DOCKER.md`](docs/DOCKER.md) for full Docker details.*

---

## 15. Testing Strategy

The test suite contains **161 automated tests** covering unit components, provider mocks, and end-to-end integration flows.

### Running the Test Suite
```bash
python3 -m pytest backend/tests/ -v
```

### Test Coverage Breakdown
- **Unit Tests**:
  - `test_upload.py`: Magic bytes verification, size boundaries, extension whitelist.
  - `test_pdf_parser.py`: Multi-page extraction, whitespace consistency, layout preservation.
  - `test_ocr_service.py`: Scanned page detection, Tesseract fallback, threshold triggers.
  - `test_text_cleaner.py`: Unicode normalization, ligature stripping, dehyphenation.
  - `test_section_detector.py`: Canonical 13-section segmentation and unclassified capture.
  - `test_skill_normalizer.py`: Alias resolution, category classification, dictionary extension.
  - `test_resume_schema.py`: Pydantic model validation and boundary constraints.
  - `test_job_matcher.py`: Deterministic qualification matching and rank comparisons.
- **Integration Tests**:
  - `test_comprehensive_integration.py`: End-to-end testing of the 4 core flows:
    1. Upload $\to$ Ingestion Processing
    2. Processing $\to$ Relational Persistence
    3. Authentication $\to$ Protected Endpoints & Multi-User Isolation
    4. Resume $\to$ Job Requirement Matching
  - `test_database_persistence.py`: Full CRUD lifecycle and cascading foreign keys.
  - `test_auth.py`: JWT generation, password hashing, and cross-user privacy enforcement.

*Zero tests depend on paid or live external APIs. All LLM and embedding calls are mocked during tests for fast, deterministic, reproducible execution.*

---

## 16. Security Considerations

1. **Defense-in-Depth File Validation**:
   - File uploads are validated through a 3-point check: filename extension, Content-Type header, and raw byte signature inspection (`%PDF-` header and `%%EOF` trailer).
   - Filenames are sanitized with UUIDs to prevent path traversal attacks (`../../etc/passwd`).

2. **No Secret Leaks**:
   - Environment configurations strictly adhere to Twelve-Factor App principles.
   - Secret keys are excluded from Git via `.gitignore` and `.dockerignore`.

3. **Authentication & Password Security**:
   - Passwords are encrypted using salted `bcrypt` hashes.
   - API endpoints enforce JWT expiration timestamps and validate symmetric signatures.

4. **Multi-Tenant Data Isolation**:
   - Strict database query scoping ensures users can only view or mutate their own records.
   - Cross-user data requests automatically reject with `403 Forbidden`.

5. **Rate Limiting & Safe JSON Parsing**:
   - Ingestion routes restrict upload body size to 10MB to prevent memory exhaustion (DoS).
   - JSON extraction enforces strict boundary parsing with regex blocks to eliminate prompt-injection syntax breaking.

---

## 17. Limitations

- **Complex Graphic Layouts**: Multi-column magazine-style resumes with non-standard text flow may require manual section verification.
- **Non-Latin Typography in Scanned Resumes**: OCR accuracy on scanned image PDFs depends on Tesseract language packs (default container includes English).
- **Embedded Fonts & Non-Standard Ligatures**: Extremely rare custom font encodings may cause PyMuPDF to extract Unicode replacement glyphs (`\ufffd`).

---

## 18. Future Improvements

- [ ] **Multi-Language OCR**: Support for German, French, Spanish, and Mandarin language packs in Tesseract.
- [ ] **DOCX / RTF Ingestion**: Native Microsoft Word document ingestion support.
- [ ] **Asynchronous Task Queue**: Celery or Redis worker queue for high-volume batch resume processing.
- [ ] **Interactive Visual Annotation**: Side-by-side PDF preview with visual bounding box highlights over extracted sections.
- [ ] **Candidate Comparison Matrices**: Multi-resume side-by-side qualification tables for recruiters.

---

## 19. Screenshots & UI Placeholders

| Section | Preview |
| :--- | :--- |
| **Interactive Resume Upload & Parsing** | ![Upload Interface Placeholder](https://placehold.co/800x450/1e293b/38bdf8?text=1.+Resume+Upload+%26+Live+Parsing) |
| **Canonical Structured Profile View** | ![Structured Data View](https://placehold.co/800x450/1e293b/38bdf8?text=2.+Extracted+Structured+Profile) |
| **Job Description Matching & Gap Analysis** | ![Matching Matrix](https://placehold.co/800x450/1e293b/38bdf8?text=3.+Skill+Overlap+%26+Gap+Analysis) |
| **Objective Quality Feedback** | ![Quality Suggestions](https://placehold.co/800x450/1e293b/38bdf8?text=4.+Explainable+Quality+Feedback) |

---

## 20. Author Section

**AI Resume Parser & Job Matcher Platform**

- **Project Lead & Architecture**: Software Engineering Team
- **Repository**: [GitHub Repository](https://github.com/Deep-debug006/ai-resume-parser)
- **License**: MIT Open Source License

*Engineered with strict non-evaluative principles: Designed to empower recruiters and candidates with explainable transparency, factual accuracy, and deterministic precision.*
