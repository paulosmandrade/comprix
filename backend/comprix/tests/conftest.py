import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from comprix.app import app
from comprix.models import Base


@pytest.fixture
def client(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    monkeypatch.setattr('comprix.database.engine', engine)

    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    await engine.dispose()
