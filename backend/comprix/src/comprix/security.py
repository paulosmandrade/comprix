import secrets

from datetime import datetime, timedelta
from http import HTTPStatus
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, ExpiredSignatureError, decode, encode
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comprix.database import get_session
from comprix.models import Usuarios
from comprix.settings import Settings

pwd_context = PasswordHash.recommended()
settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='auth/token', refreshUrl='auth/refresh'
)

CODIGO_EXPIRA_MINUTOS = 15
CODIGO_MAX_TENTATIVAS = 5

# Criptograda a senha
def get_password_hash(senha: str):
    return pwd_context.hash(senha)


# Verifica senha
def verify_password(senha: str, hashed_password: str):
    return pwd_context.verify(senha, hashed_password)


# Criando o Token
def create_access_token(data: dict):
    to_encode = data.copy()

    # Acrescenta minutos no tempo atual, para validade do token
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Dentro do dicionário adiciona a CLAIN que tem a expiração do Token
    to_encode.update({'exp': expire})

    # Claim is_admin
    if to_encode.get('sub') == settings.ADMIN_EMAIL:
        to_encode.update({'is_admin': True})

    # Agora vamos criar o TOKEN com jwt encode
    encode_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encode_jwt


# Validando token de usuarios
async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Credencial inválida',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject_email = payload.get('sub')

        if not subject_email:
            raise credentials_exception

    except DecodeError:
        raise credentials_exception

    except ExpiredSignatureError:
        raise credentials_exception

    usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == subject_email)
    )

    if not usuario:
        raise credentials_exception

    return usuario


async def get_current_admin(
    usuario: Usuarios = Depends(get_current_user),
):
    if not usuario.admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Acesso permitido somente para administradores',
        )

    return usuario


# Criando o token do link de definir senha
def create_definir_senha_token(email: str) -> str:
    """Cria o token do link de definir senha, válido por 24 horas."""
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(hours=24)

    return encode(
        {'sub': email, 'tipo': 'definir_senha', 'exp': expire},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
