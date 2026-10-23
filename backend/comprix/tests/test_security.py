from datetime import datetime, timedelta
from http import HTTPStatus
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from jwt import decode, encode

from comprix.security import (
    create_access_token,
    get_current_admin,
    get_current_user,
    get_password_hash,
    verify_password,
)

# ---------------------------------------------------------------------------
# Hash de senha
# ---------------------------------------------------------------------------


def test_hash_nao_e_a_senha_em_texto_puro():
    senha_hash = get_password_hash('minha_senha')
    # senha_hash e diferente de texto puro (verdadeiro)
    assert senha_hash != 'minha_senha'
    # senha_hash no começo $argon2 (verdadeiro)
    assert senha_hash.startswith('$argon2')


def test_hash_da_mesma_senha_muda_a_cada_requisicao():
    assert get_password_hash('abc') != get_password_hash('abc')


def test_verify_password_senha_correta():
    senha_hash = get_password_hash('minha_senha')
    # Retornará true, comparando com a função verify_password
    assert verify_password('minha_senha', senha_hash)


def test_verify_password_senha_errada():
    senha_hash = get_password_hash('minha_senha')
    # Retornará false, comparando com a função verify_password
    assert not verify_password('outra_senha', senha_hash)


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------
def agora():
    return datetime.now(tz=ZoneInfo('UTC'))


def token_manual(settings, payload: dict, chave: str | None = None) -> str:
    """Monta um token com qualquer payload, para simular ataques e erros."""
    return encode(
        payload,
        chave or settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


async def espera_401(session, token: str):
    with pytest.raises(HTTPException) as exc:
        await get_current_user(session=session, token=token)

    assert exc.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.value.headers == {'WWW-Authenticate': 'Bearer'}


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------
def test_token_contem_sub_e_exp(settings):
    token = create_access_token({'sub': 'teste@comprix.com.br'})
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    assert payload['sub'] == 'teste@comprix.com.br'
    assert 'exp' in payload


def test_token_expira_no_tempo_configurado(settings):
    diferenca_segundos = 5
    inicio = agora().timestamp()
    token = create_access_token({'sub': 'teste@comprix.com.br'})
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    esperado = inicio + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    assert abs(payload['exp'] - esperado) < diferenca_segundos


def test_usuario_comum_nao_recebe_is_admin(settings):
    token = create_access_token({'sub': 'teste@comprix.com.br'})
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert 'is_admin' not in payload


def test_admin_recebe_is_admin(settings):
    token = create_access_token({'sub': settings.ADMIN_EMAIL})
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    assert payload['is_admin'] is True


def test_nao_altera_o_dicionario_original():
    data = {'sub': 'teste@comprix.com.br'}
    create_access_token(data)
    assert data == {'sub': 'teste@comprix.com.br'}


# ---------------------------------------------------------------------------
# get_current_user com o banco em memória
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_token_valido_retorna_o_usurio_do_banco(session, usuario):
    token = create_access_token({'sub': usuario.email})

    resultado = await get_current_user(session=session, token=token)

    assert resultado.id == usuario.id
    assert resultado.email == usuario.email


@pytest.mark.asyncio
async def test_token_malformado(session):
    await espera_401(session, 'iso_nao_e_um_jwt')


@pytest.mark.asyncio
async def test_token_expirado(session, settings, usuario):
    token = token_manual(
        settings,
        {
            'sub': usuario.email,
            'exp': agora() - timedelta(minutes=1),
        },
    )
    await espera_401(session, token)


@pytest.mark.asyncio
async def test_token_assinado_com_outra_chave(session, settings, usuario):
    token = token_manual(
        settings,
        {'sub': usuario.email, 'exp': agora() + timedelta(minutes=5)},
        chave='chave-de-um-atacante',
    )
    await espera_401(session, token)


@pytest.mark.asyncio
async def test_token_sem_sub(session, settings):
    token = token_manual(settings, {'exp': agora() + timedelta(minutes=5)})
    await espera_401(session, token)


@pytest.mark.asyncio
async def test_token_de_email_que_nao_existe(session):
    token = create_access_token({'sub': 'fantasma@comprix.com'})
    await espera_401(session, token)


@pytest.mark.asyncio
async def test_usuario_apagado_depois_do_login(session, usuario):
    token = create_access_token({'sub': usuario.email})

    await session.delete(usuario)
    await session.commit()

    await espera_401(session, token)


# ---------------------------------------------------------------------------
# get_current_admin
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_current_admin_com_usuario_admin(usuario_admin):
    """Usuário admin passa pela verificação e é retornado"""
    resultado = await get_current_admin(usuario=usuario_admin)

    # Retorna o mesmo usuário recebido
    assert resultado.id == usuario_admin.id
    assert resultado.admin is True


@pytest.mark.asyncio
async def test_get_current_admin_com_usuario_comum(usuario):
    """Usuário comum é barrado com 403"""
    with pytest.raises(HTTPException) as exc:
        await get_current_admin(usuario=usuario)

    # Verifica se o status code é 403 PROIBIDO
    assert exc.value.status_code == HTTPStatus.FORBIDDEN

    # Verifica a mensagem de erro
    assert exc.value.detail == (
        'Acesso permitido somente para administradores'
    )
