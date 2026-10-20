# AI Resume Parser & Job Matcher - Frontend

React + TypeScript + Tailwind CSS frontend interface for the AI Resume Parser & Job Matcher.

## Directory Structure

```text
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Header.tsx      # Application header & metadata
│   │   ├── HealthStatus.tsx# Live backend connectivity checker
│   │   ├── ArchitectureView.tsx # Visual architectural breakdown
│   │   └── PhaseTracker.tsx# Incremental phase status
│   ├── services/           # API interaction layer
│   │   └── api.ts          # Backend /api/health client
│   ├── types/              # TypeScript definitions
│   │   └── health.ts       # Health response and connection state
│   ├── App.tsx             # Root dashboard page
│   ├── index.css           # Tailwind CSS imports
│   └── main.tsx            # React 19 bootstrap entry
├── package.json            # Node dependencies and scripts
├── tsconfig.json           # TypeScript configuration
├── vite.config.ts          # Vite build & reverse-proxy configuration
├── .env.example            # Environment variables template
└── README.md
```

## Running Frontend

```bash
# Install dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend runs on `http://localhost:3000` and proxies `/api` calls directly to the FastAPI backend running on port 8001.
