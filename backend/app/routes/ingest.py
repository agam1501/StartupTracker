from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.schemas.raw_source import RawSourceResponse
from app.services.crud import create_raw_source, get_raw_source_by_url
from app.services.db import get_session
from app.services.ingestion import ingest_rss_feed, ingest_url

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    source_url: str
    title: str | None = None
    content: str | None = None


class IngestBatchRequest(BaseModel):
    feed_url: str


@router.post("", response_model=RawSourceResponse, status_code=202)
async def ingest_source(
    body: IngestRequest,
    session: AsyncSession = Depends(get_session),
):
    existing = await get_raw_source_by_url(session, body.source_url)
    if existing:
        return JSONResponse(
            status_code=200,
            content=RawSourceResponse.model_validate(existing).model_dump(mode="json"),
        )

    rs = await create_raw_source(
        session,
        source_url=body.source_url,
        title=body.title,
        content=body.content,
    )
    await session.commit()
    return RawSourceResponse.model_validate(rs)


@router.post("/process")
async def process_source(
    body: IngestRequest,
    session: AsyncSession = Depends(get_session),
):
    """Run full pipeline on a single URL: fetch -> extract -> dedup -> insert."""
    result = await ingest_url(session, body.source_url, title=body.title)
    return result


@router.post("/batch")
async def batch_ingest(
    body: IngestBatchRequest,
    session: AsyncSession = Depends(get_session),
):
    """Parse an RSS feed and run pipeline on all new articles."""
    results = await ingest_rss_feed(session, body.feed_url)
    return {
        "feed_url": body.feed_url,
        "total": len(results),
        "results": results,
    }
