# Embedding Model Architecture & Selection (Phase 16)

## 1. Selected Model: `text-embedding-004`

For semantic similarity between parsed resumes and job descriptions, the system utilizes **Google's `text-embedding-004`** model via the `@google/genai` Python SDK, with native fallback to an in-memory deterministic projection engine for offline testing and rate-limited environments.

### Technical Specifications
- **Model Name**: `text-embedding-004`
- **Output Dimensionality**: `768` dimensions
- **Vector Metric**: Cosine Similarity ($\cos(\theta) = \frac{A \cdot B}{\|A\| \|B\|}$)
- **Distance Operator in pgvector**: `<=>` (Cosine Distance, where $\text{similarity} = 1.0 - \text{distance}$)
- **Database Storage**: PostgreSQL 15 with `pgvector` 0.8.0 extension and HNSW indexing (`vector_cosine_ops`)

---

## 2. Why `text-embedding-004` Was Selected

### A. Optimal Dimensionality (768 vs. 1536 / 3072)
- High-dimensional models (1536 or 3072 dims) double or quadruple the RAM footprint of HNSW graph indexes in PostgreSQL and increase query latency.
- 768 dimensions provide the ideal sweet spot: preserving dense semantic nuance across technical terminology, libraries, frameworks, and job responsibilities while remaining lightweight and fast to search.

### B. Specialized Asymmetric Retrieval & Dense Matching
- Resume-to-job matching is fundamentally an asymmetric retrieval problem: concise job requirements (e.g. *"5+ years building scalable microservices in Python"*) must match detailed, multi-sentence experience descriptions (e.g. *"Architected event-driven distributed pipeline processing 25k req/s using Python FastAPI and Redis"*).
- `text-embedding-004` is pretrained on extensive semantic retrieval tasks, allowing it to capture contextual equivalents that exact keyword matching misses (such as recognizing that *"microservices architecture"* is semantically aligned with *"REST API development with FastAPI"*).

### C. Normalization & Cosine Fidelity
- Embeddings produced by `text-embedding-004` are unit-normalized ($L_2$ norm = 1.0), meaning dot product equals cosine similarity, simplifying database computation and accelerating query speeds.

---

## 3. Storage Efficiency & Redundancy Prevention

### A. Content Hashing (SHA-256 Caching)
To satisfy the strict requirement **"Avoid regenerating embeddings unnecessarily when content has not changed"**:
- Every embedded text chunk is normalized and hashed using **SHA-256** prior to generation.
- The `vector_embeddings` table stores `content_hash VARCHAR(64)` with a B-tree index.
- If a candidate's resume or a job posting has not changed, the system retrieves the vector directly from PostgreSQL without calling the embedding API.
- If only one section or experience item is updated, only the modified chunk generates a new vector; all other unchanged chunks are reused.

### B. PostgreSQL + pgvector Schema
```sql
CREATE TABLE vector_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL, -- resume_summary, resume_experience, resume_project, job_description, job_requirement
    entity_id VARCHAR(64) NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content_hash VARCHAR(64) NOT NULL,
    content_text TEXT NOT NULL,
    embedding VECTOR(768) NOT NULL,
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-004',
    dimensions INTEGER NOT NULL DEFAULT 768,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cosine Distance HNSW Index
CREATE INDEX idx_vec_embedding_cosine ON vector_embeddings 
USING hnsw (embedding vector_cosine_ops);
```

---

## 4. Clear Distinction: Exact Match vs. Semantic Similarity

The application explicitly separates and contrasts two distinct analytical signals:

| Dimension | Exact Keyword Matching (Phase 15) | Semantic Similarity (Phase 16) |
| :--- | :--- | :--- |
| **Method** | Canonical skill alias resolution & dictionary normalization | Dense 768-d vector cosine similarity |
| **Output** | Boolean presence: `matched_skills`, `missing_required_skills` | Continuous score (0.0 to 1.0) & relevance tier |
| **Scope** | Hard skills, tools, frameworks, certifications | Contextual responsibilities, domain experience, project scope |
| **Limitation** | Fails on paraphrasing or unlisted synonyms | Cannot guarantee exact certification or tool proficiency |

---

## 5. Ethical AI Boundaries: No Automated Hiring Decisions

In accordance with ethical AI guidelines and non-evaluative design:
- **Semantic similarity is NOT a hiring probability**: A similarity score of `0.85` means high textual and semantic alignment between descriptions; it does **not** indicate an 85% probability of hiring.
- The system includes a mandatory disclaimer across all API responses and UI components stating that semantic similarity is purely an informational, mathematical comparison and must never replace human review or constitute an automated employment decision.
