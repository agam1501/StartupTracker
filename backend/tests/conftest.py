import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    # SQLite doesn't support gen_random_uuid() or now(), provide fallbacks
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_functions(dbapi_conn, _record):
        import datetime as _dt
        import uuid as _uuid

        dbapi_conn.create_function("gen_random_uuid", 0, lambda: _uuid.uuid4().hex)
        dbapi_conn.create_function("now", 0, lambda: _dt.datetime.now(_dt.UTC).isoformat())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_sess = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_sess() as s:
        yield s

    await engine.dispose()
