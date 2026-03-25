# StartupTracker - Claude Agent Context

## Project Overview
Personal "Crunchbase-like" startup funding tracker. FastAPI backend + Next.js frontend + PostgreSQL (Supabase) + LLM extraction pipeline.

## Repo Structure
```
backend/          # FastAPI app
  app/
    routes/       # API endpoints
    services/     # Business logic (ingestion, llm, dedup, db)
    models/       # SQLAlchemy ORM models
    schemas/      # Pydantic request/response schemas
  alembic/        # DB migrations
  tests/
frontend/         # Next.js app (App Router, TypeScript, Tailwind)
docker-compose.yml  # Local Postgres
```

## CI Pipelines

### Backend CI (`.github/workflows/backend-ci.yml`)
Triggers on pushes/PRs touching `backend/**`.
Steps:
1. `pip install -e ".[dev]"` (Python 3.11)
2. `ruff check .` - linting (rules: E, F, I, N, W, UP; line-length=100)
3. `ruff format --check .` - formatting
4. `pytest -v`

Working directory: `backend/`

### Frontend CI (`.github/workflows/frontend-ci.yml`)
Triggers on pushes/PRs touching `frontend/**`.
Steps: ESLint + typecheck + build.

## Pre-PR Checklist (Backend)
Before pushing a backend branch:
```bash
cd backend
ruff check .          # fix lint errors
ruff format .         # fix formatting
pytest -v             # run tests
```
Common gotchas:
- Line length limit is 100 chars (not 88)
- `ruff format` and `ruff check` are separate CI steps — passing one doesn't mean the other passes
- Alembic migration files ARE linted — keep them clean
- `pyproject.toml` has `[tool.setuptools.packages.find] include = ["app*"]` to exclude alembic from setuptools discovery

## Pre-PR Checklist (Frontend)
```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

## Branch & Merge Conventions
- PRs are stacked in dependency order (see execution plan in `.context/plans/`)
- Each PR has a corresponding GitHub issue
- Merge order matters — downstream PRs rebase onto upstream fixes
- Branch naming: `NN-feature-name` (e.g., `07-db-crud-service`)

## Key Tech Decisions
- Alembic for DB migrations (async with asyncpg)
- rapidfuzz for fuzzy matching/dedup
- trafilatura for article text extraction
- LLM is extractor only (no reasoning), cost-optimized prompts
- Render for backend hosting, Vercel for frontend
- SQLAlchemy async ORM with mapped_column style

## Database
- Local dev: `docker-compose up -d` starts Postgres on port 5432
- 5 tables: companies, funding_rounds, investors, round_investors, raw_sources
- All PKs are UUID with `gen_random_uuid()`
- Indexed: normalized_name (companies, investors), company_id (funding_rounds), source_url (raw_sources, unique)
