from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comprix.database import get_session
from comprix.models import Usuarios
from comprix.security import (
    create_access_token,
    get_current_user,
    verify_password,
)

router = APIRouter(prefix='/auth', tags=['auth'])
Session = Annotated[AsyncSession, Depends(get_session)]
OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
CurrentUser = Annotated[Usuarios, Depends(get_current_user)]


@router.post('/token')
async def login_for_access_token(form_data: OAuth2Form, session: Session):
    # form_data.username contém o email digitado
    usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == form_data.username)
    )

    if not usuario or not verify_password(form_data.password, usuario.senha):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Email ou senhas incorretos',
        )
    access_token = create_access_token(data={'sub': usuario.email})

    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/refresh')
async def refresh_access_token(usuario: CurrentUser):
    new_access_token = create_access_token(data={'sub': usuario.email})

    return {'access_token': new_access_token, 'token_type': 'bearer'}
