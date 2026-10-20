# AI Resume Parser & Job Matcher - Backend

FastAPI backend service for resume parsing, text extraction, validation, and semantic job matching.

## Architecture

```text
backend/
├── app/
│   ├── main.py             # FastAPI app initialization and middleware
│   ├── core/               # App configuration, settings, security
│   ├── routes/             # API endpoint definitions (e.g., health, upload)
│   ├── services/           # Core business logic and file processing
│   ├── schemas/            # Pydantic request/response validation schemas
│   ├── models/             # Database and ORM models
│   ├── repositories/       # Data persistence abstractions
│   └── utils/              # Helper utilities
├── tests/                  # Automated pytest test suites
├── requirements.txt        # Python dependency manifest
├── .env.example            # Environment configuration template
└── README.md
```

## Setup & Running

### 1. Install dependencies
```bash
python3 -m pip install -r backend/requirements.txt
```

### 2. Configure environment
```bash
cp backend/.env.example backend/.env
```

### 3. Run development server
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. Run tests
```bash
pytest backend/tests
```

### 5. API Documentation
Once running, interactive documentation is available at:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`
