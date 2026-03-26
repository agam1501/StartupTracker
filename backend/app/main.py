import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.acquisitions import router as acquisitions_router
from app.routes.companies import router as companies_router
from app.routes.funding_rounds import router as funding_rounds_router
from app.routes.health import router as health_router
from app.routes.ingest import router as ingest_router
from app.routes.investors import router as investors_router
from app.routes.stats import router as stats_router

app = FastAPI(title="StartupTracker API", version="0.1.0")

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(acquisitions_router)
app.include_router(companies_router)
app.include_router(funding_rounds_router)
app.include_router(ingest_router)
app.include_router(investors_router)
app.include_router(stats_router)
