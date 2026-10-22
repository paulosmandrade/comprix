import pytest
from sqlalchemy import select

from comprix.models import Usuarios


@pytest.mark.asyncio
async def test_criar_usuario(session):
    usuario = Usuarios(
        nome='Admin', email='admin@comprix.com.br', senha='hash-da-senha'
    )

    session.add(usuario)
    await session.commit()

    resultado = await session.scalar(
        select(Usuarios).where(Usuarios.email == 'admin@comprix.com.br')
    )

    assert resultado.id == 1
    assert resultado.primeiro_acesso is True
    assert resultado.status is True
