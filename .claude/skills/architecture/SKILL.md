---
name: architecture
description: System architecture reference for StartupTracker. Use when making design decisions or understanding how components connect.
---

# StartupTracker Architecture

## System Overview
```
[News Sources / RSS] --> [Ingestion Pipeline] --> [PostgreSQL]
                              |                       |
                         [LLM Extract]           [FastAPI API]
                         [Normalize]                  |
                         [Dedup]              [Next.js Frontend]
```

## Database Schema (5 tables)

### companies
- id (uuid pk), name, normalized_name (indexed), website, created_at

### funding_rounds
- id (uuid pk), company_id (fk -> companies, indexed), round_type, amount_usd, valuation_usd, announced_date, source_url, created_at

### investors
- id (uuid pk), name, normalized_name (indexed)

### round_investors (join table)
- round_id (fk -> funding_rounds), investor_id (fk -> investors) — composite PK

### raw_sources
- id (uuid pk), source_url (unique indexed), title, content, processed (bool), created_at

## Backend Services (app/services/)
- `db.py` - async DB session factory (exists)
- `crud.py` - CRUD helpers (PR 7)
- `ingestion.py` - full pipeline orchestrator (PR 17)
- `llm.py` - LLM extraction with caching (PR 12)
- `normalization.py` - name/date/currency normalization (PR 13)
- `fetcher.py` - article/RSS fetching with trafilatura (PR 14)
- `dedup.py` - company/round/investor dedup with rapidfuzz (PRs 15-16)
- `batch.py` - batch RSS processing (PR 18)

## API Endpoints (app/routes/)
- `GET /health` - health check (exists)
- `GET /companies` - search + paginated list (PR 8)
- `GET /companies/{id}` - detail with rounds + investors (PR 9)
- `GET /funding-rounds` - filtered/sorted list (PR 10)
- `POST /ingest` - single article ingestion (PR 11/17)
- `POST /ingest/batch` - RSS feed batch ingestion (PR 18)

## Frontend Pages (frontend/)
- `/` - company search + list (PR 20)
- `/companies/[id]` - company detail + timeline (PR 21)
- `/funding-rounds` - filterable table (PR 22)

## Data Flow: Article Ingestion
1. Fetch article URL or RSS feed
2. Extract text with trafilatura
3. Store in raw_sources (idempotent via unique source_url)
4. Send to LLM for structured extraction (JSON)
5. Validate + normalize output
6. Deduplicate company (normalized name + fuzzy match)
7. Deduplicate round (company + type + date window)
8. Insert/update structured tables
9. Mark raw_source as processed

## Dedup Strategy
- **Companies**: normalized name exact match, then Levenshtein (rapidfuzz) > threshold
- **Rounds**: same company + same round_type + within 7 days + similar amount
- **Investors**: normalized name + fuzzy match
