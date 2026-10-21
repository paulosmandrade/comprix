from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comprix.database import engine, get_session
from comprix.models import Usuarios
from comprix.schemas import UsuarioPublico, UsuarioSchema
from comprix.security import get_password_hash
from comprix.settings import Settings

router = APIRouter(prefix='/usuarios', tags=['Cadastro de usuários'])

Session = Annotated[AsyncSession, Depends(get_session)]


async def criar_admin() -> None:
    """Cria o usuário admin, caso ainda não exista."""
    async with AsyncSession(engine, expire_on_commit=True) as session:
        existe = await session.scalar(
            select(Usuarios).where(Usuarios.email == Settings().ADMIN_EMAIL)
        )

        if existe:
            return

        admin = Usuarios(
            nome=Settings().ADMIN_USER,
            email=Settings().ADMIN_EMAIL,
            senha=get_password_hash(Settings().ADMIN_SENHA),
            admin=True,
            primeiro_acesso=False,
        )
        session.add(admin)
        await session.commit()


@router.post(
    '/', status_code=HTTPStatus.CREATED, response_model=UsuarioPublico
)
async def criar_usuarios(user: UsuarioSchema, session: Session):
    db_usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == user.email)
    )

    if db_usuario:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Email já existente'
        )

    novo_usuario = Usuarios(
        nome=user.nome, email=user.email, senha=get_password_hash(user.senha)
    )

    session.add(novo_usuario)
    await session.commit()
    await session.refresh(novo_usuario)

    return novo_usuario
