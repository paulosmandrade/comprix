import secrets
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from jwt import DecodeError, ExpiredSignatureError, decode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comprix.database import get_session
from comprix.email import enviar_email_definir_senha
from comprix.models import Usuarios
from comprix.schemas import DefinirSenhaSchema, UsuarioPublico, UsuarioSchema
from comprix.security import (
    create_definir_senha_token,
    get_current_admin,
    get_password_hash,
)
from comprix.settings import Settings

router = APIRouter(prefix='/usuarios', tags=['Cadastro de usuários'])
Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUserAdmin = Annotated[Usuarios, Depends(get_current_admin)]
settings = Settings()


async def criar_admin(session: AsyncSession) -> None:
    """Cria o usuário admin, caso ainda não exista."""
    existe = await session.scalar(
        select(Usuarios).where(Usuarios.email == settings.ADMIN_EMAIL)
    )

    if existe:
        return

    admin = Usuarios(
        nome=settings.ADMIN_USER,
        email=settings.ADMIN_EMAIL,
        senha=get_password_hash(settings.ADMIN_SENHA),
        admin=True,
        primeiro_acesso=False,
    )

    session.add(admin)
    await session.commit()


@router.post(
    '/',
    status_code=HTTPStatus.CREATED,
    response_model=UsuarioPublico,
)
async def criar_usuarios(
    user: UsuarioSchema,
    session: Session,
    current_user: CurrentUserAdmin,
    background_tasks: BackgroundTasks,
):
    db_usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == user.email)
    )

    if db_usuario:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail='Email já existente'
        )

    novo_usuario = Usuarios(
        nome=user.nome,
        email=user.email,
        # Senha aleatória: ninguém conhece, então ninguém loga ainda
        senha=get_password_hash(secrets.token_urlsafe(32)),
    )

    session.add(novo_usuario)
    await session.commit()
    await session.refresh(novo_usuario)

    # Gera o token do link e agenda o e-mail para depois da resposta
    token = create_definir_senha_token(novo_usuario.email)
    background_tasks.add_task(
        enviar_email_definir_senha,
        novo_usuario.nome,
        novo_usuario.email,
        token,
    )

    return novo_usuario


@router.post('/definir-senha', status_code=HTTPStatus.NO_CONTENT)
async def definir_senha(dados: DefinirSenhaSchema, session: Session):
    erro = HTTPException(
        status_code=HTTPStatus.BAD_REQUEST, detail='Link inválido ou expirado'
    )

    try:
        payload = decode(
            dados.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except DecodeError, ExpiredSignatureError:
        raise erro

    # Só aceita o token do link, nunca um token de acesso
    if payload.get('tipo') != 'definir_senha':
        raise erro

    usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == payload.get('sub'))
    )

    # primeiro_acesso=False significa que o link já foi usado
    if not usuario or not usuario.primeiro_acesso:
        raise erro

    usuario.senha = get_password_hash(dados.nova_senha)
    usuario.primeiro_acesso = False
    await session.commit()
