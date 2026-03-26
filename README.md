# StartupTracker

A personal Crunchbase-like startup funding tracker. Automatically ingests funding news from RSS feeds, extracts structured data via LLM, deduplicates entries, and serves everything through a clean API and modern frontend.

## Architecture

```
RSS Feeds → Fetcher → LLM Extractor → Normalizer → Dedup → PostgreSQL
                                                                ↓
                                              FastAPI ← Next.js Frontend
```

**Backend:** FastAPI (Python 3.11) with async SQLAlchemy ORM, Alembic migrations, and PostgreSQL (Supabase).

**Frontend:** Next.js 15 (App Router, TypeScript, Tailwind CSS v4) with shadcn/ui-style components and React Query.

**Ingestion Pipeline:** RSS fetch → article extraction (trafilatura) → LLM structured extraction (OpenAI) → fuzzy dedup (rapidfuzz) → database insert.

## Repo Structure

```
backend/                  # FastAPI app
  app/
    routes/               # API endpoints (companies, funding-rounds, investors, stats, ingest, health)
    services/             # Business logic (ingestion, llm, dedup, normalization, crud, fetcher)
    models/               # SQLAlchemy ORM models
    schemas/              # Pydantic request/response schemas
  alembic/                # Database migrations
  tests/                  # pytest test suite (157 tests, 92% coverage)
frontend/                 # Next.js app
  src/
    app/                  # Pages (companies, funding-rounds, investors, 404)
    components/           # UI components (Nav, SearchBar, Pagination, ui/)
    lib/                  # API client, types, utilities, formatters
  src/__tests__/          # Vitest test suite (37 tests)
.github/workflows/        # CI pipelines (backend-ci, frontend-ci, scheduled ingestion)
docker-compose.yml        # Local PostgreSQL
render.yaml               # Render deployment config
```

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (for local PostgreSQL)

### Backend Setup

```bash
# Start local database
docker-compose up -d

# Set up Python environment
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Copy and configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Start the server
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install

# Copy environment
cp .env.example .env.local

# Start dev server
npm run dev
```

Frontend runs at `http://localhost:3000`.

### Running Tests

```bash
# Backend (from backend/)
pytest -v                                    # run tests
pytest --cov=app --cov-report=term-missing   # with coverage

# Frontend (from frontend/)
npm test                                     # run tests
npm run test:watch                           # watch mode
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/companies` | List companies (search, pagination) |
| GET | `/companies/{id}` | Company detail with funding rounds |
| GET | `/funding-rounds` | List funding rounds (filter by type, company) |
| GET | `/funding-rounds/{id}` | Funding round detail |
| GET | `/investors` | List investors (search, pagination) |
| GET | `/investors/{id}` | Investor detail |
| GET | `/stats` | Dashboard statistics |
| POST | `/ingest` | Submit URL for processing |
| POST | `/ingest/process` | Process single URL through pipeline |
| POST | `/ingest/batch` | Process RSS feed |

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/startuptracker` | Database connection string |
| `OPENAI_API_KEY` | (none) | OpenAI API key for LLM extraction |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |
| `FEED_URLS` | (none) | Comma-separated RSS feed URLs for cron ingestion |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

## Deployment

### Backend (Render)
- Uses `render.yaml` blueprint
- Build command runs Alembic migrations automatically
- Health check at `/health`

### Frontend (Vercel)
- Root directory: `frontend`
- Set `NEXT_PUBLIC_API_URL` to your Render backend URL

### Database (Supabase)
- Create a Supabase project
- Use the connection string as `DATABASE_URL` (format: `postgresql+asyncpg://...`)

## CI Pipelines

- **Backend CI:** Ruff lint + format check → pytest with 85% coverage minimum
- **Frontend CI:** ESLint → TypeScript check → Vitest → Next.js build
- **Scheduled Ingestion:** GitHub Actions cron for RSS feed processing

## Database Schema

5 tables: `companies`, `funding_rounds`, `investors`, `round_investors`, `raw_sources`

- All primary keys are UUIDs with `gen_random_uuid()`
- Indexed: `normalized_name` (companies, investors), `company_id` (funding_rounds), `source_url` (raw_sources, unique)
