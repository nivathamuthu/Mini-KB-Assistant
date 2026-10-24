from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings, get_settings
from app.models import Base

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None):
    global _engine, _session_factory
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_async_engine(settings.database_url, pool_pre_ping=True)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    engine = get_engine(settings)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        dim = settings.embedding_dim
        await conn.execute(
            text(
                f"""
                CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
                ON chunks USING hnsw (embedding vector_cosine_ops)
                """
            )
        )


async def close_db() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
