import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_DIM", "384")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://kb:kb@localhost:5433/kb")

from app.config import get_settings
from app.db import get_db, init_db, close_db
from app.dependencies import clear_provider_cache
from app.main import create_app
from app.models import Base


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    clear_provider_cache()
    yield
    get_settings.cache_clear()
    clear_provider_cache()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    settings = get_settings()
    get_settings.cache_clear()
    clear_provider_cache()
    settings = get_settings()

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await init_db(settings)

    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    await close_db()
    await engine.dispose()

    global _rate_limiter
    import app.rate_limit as rl

    rl._rate_limiter = None
