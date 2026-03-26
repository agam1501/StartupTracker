from fastapi import FastAPI

from app.routes.companies import router as companies_router
from app.routes.funding_rounds import router as funding_rounds_router
from app.routes.health import router as health_router
from app.routes.ingest import router as ingest_router

app = FastAPI(title="StartupTracker API", version="0.1.0")

app.include_router(health_router)
app.include_router(companies_router)
app.include_router(funding_rounds_router)
app.include_router(ingest_router)
