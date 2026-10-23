import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from comprix.app import app
from comprix.database import get_session
from comprix.models import Base, Usuarios
from comprix.security import get_password_hash
from comprix.settings import Settings


@pytest.fixture
def settings():
    return Settings()


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        'sqlite+aiosqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def client(session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def usuario(session):
    senha = 'testing_senha'

    usuario = Usuarios(
        nome="usuário teste",
        email='usuario@comprix.com.br',
        senha=get_password_hash(senha)
    )

    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)

    usuario.clean_password = senha  # senha pura, só para testes

    return usuario


@pytest_asyncio.fixture
async def admin(session, settings):
    senha = 'testing_senha'

    admin = Usuarios(
        nome=settings.ADMIN_USER,
        email=settings.ADMIN_EMAIL,
        senha=get_password_hash(settings.ADMIN_SENHA),
    )

    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    admin.clear_password = senha

    return admin


@pytest.fixture
def token(client, usuario):
    response = client.post(
        'auth/token',
        data={'username': usuario.email, 'password': usuario.clean_password},
    )

    return response.json()['access_token']
