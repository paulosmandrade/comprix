from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from comprix.models import Base
from comprix.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL, echo=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from comprix.routers.usuarios import criar_admin  # noqa: PLC0415

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await criar_admin()
    yield
    await engine.dispose()


async def get_session():  # pragma: no cover
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            if session.is_active:
                await session.rollback()
            raise
