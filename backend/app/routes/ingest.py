from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.schemas.raw_source import RawSourceResponse
from app.services.crud import create_raw_source, get_raw_source_by_url
from app.services.db import get_session

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    source_url: str
    title: str | None = None
    content: str | None = None


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
