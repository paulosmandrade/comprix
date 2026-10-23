from datetime import datetime, timedelta
from http import HTTPStatus

import pytest
import pytest_asyncio
from freezegun import freeze_time
from jwt import decode
from sqlalchemy import func, select

from comprix.models import Usuarios
from comprix.routers.usuarios import criar_admin
from comprix.security import (
    create_access_token,
    create_definir_senha_token,
    get_password_hash,
    verify_password,
)


# ---------------------------------------------------------------------------
# Fixtures locais
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def usuario_novo(session):
    """Usuário recém-cadastrado, que ainda não definiu a senha"""
    usuario = Usuarios(
        nome='Usuário Novo',
        email='usuario_novo@comprix.com.br',
        senha=get_password_hash('senha_aleatoria_desconhecida'),
        primeiro_acesso=True,
    )
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario


# ---------------------------------------------------------------------------
# Rota: POST /usuarios/
# ---------------------------------------------------------------------------
def test_usuario_admin_criando_novo_usuario_CREATED(client, token_admin):
    """Teste onde o usuario Admin tem permissão para criar novos usuarios"""
    # Realizando o post com o token do admin
    response = client.post(
        '/usuarios/',
        headers={'Authorization': f'Bearer {token_admin}'},
        json={
            'nome': 'Novo Usuário',
            'email': 'novo@comprix.com.br',
        },
    )

    # Confirma o retorno do status code 201 - CRIADO
    assert response.status_code == HTTPStatus.CREATED
    # Compara o email do json com o do cadastro
    assert response.json()['email'] == 'novo@comprix.com.br'


def test_usuario_comun_nao_cria_novo_usuario_FORBIDDEN(client, token):
    """
    Teste onde o usuario comum não tem permissão para criar novos usuarios
    """
    # Realizando o post com o token de usuario comum
    response = client.post(
        '/usuarios/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'nome': 'Novo Usuário teste',
            'email': 'usuario_comun@comprix.com.br',
        },
    )

    # Confirma o retorno do status code 403 - PROIBIDO
    assert response.status_code == HTTPStatus.FORBIDDEN

    # Confirma a mensagem para o usuario sem permissão
    assert response.json()['detail'] == (
        'Acesso permitido somente para administradores'
    )


def test_criar_novo_usuario_sem_token_UNAUTHORIZED(client):
    """Teste para tentar criar usuario sem token NÃO AUTORIZADO"""
    # Realizando a requisição sem o HEADERS e token
    response = client.post(
        '/usuarios/',
        json={
            'nome': 'Novo Usuário',
            'email': 'usuario@comprix.com.br',
        },
    )

    # Confirma o retorno do status code 401 - NÃO AUTORIZADO
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_criar_novo_usuario_email_ja_existente_CONFLICT(
    client, usuario, token_admin
):
    """Teste para tentar criar usuario com o email ja existente no banco"""
    # Realizando a requisição com os mesmos dados do usuario do CONFTEST
    response = client.post(
        '/usuarios/',
        headers={'Authorization': f'Bearer {token_admin}'},
        json={
            'nome': usuario.nome,
            'email': usuario.email,
        },
    )

    # Confirma o retorno do status code 409 - CONFLICT
    assert response.status_code == HTTPStatus.CONFLICT

    # Confirma mensagem para o usuario na API
    assert response.json()['detail'] == 'Email já existente'


# ---------------------------------------------------------------------------
# Envio do e-mail no cadastro
# ---------------------------------------------------------------------------
def test_criar_usuario_envia_email_com_token(
    client, token_admin, emails_enviados, settings
):
    """Ao cadastrar, um e-mail com o token de definir senha é enviado"""
    client.post(
        '/usuarios/',
        headers={'Authorization': f'Bearer {token_admin}'},
        json={'nome': 'Novo Usuário', 'email': 'novo@comprix.com.br'},
    )

    # Confirma que um único e-mail foi enviado, para o usuário cadastrado
    assert len(emails_enviados) == 1
    assert emails_enviados[0]['email'] == 'novo@comprix.com.br'
    assert emails_enviados[0]['nome'] == 'Novo Usuário'

    # Confirma que o token enviado é do tipo certo e pertence ao usuário
    payload = decode(
        emails_enviados[0]['token'],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    assert payload['sub'] == 'novo@comprix.com.br'
    assert payload['tipo'] == 'definir_senha'


def test_cadastro_recusado_nao_envia_email(
    client, usuario, token_admin, emails_enviados
):
    """Se o cadastro falha (email repetido), nenhum e-mail é enviado"""
    client.post(
        '/usuarios/',
        headers={'Authorization': f'Bearer {token_admin}'},
        json={'nome': usuario.nome, 'email': usuario.email},
    )

    # Confirma que nenhum e-mail foi enviado
    assert emails_enviados == []


# ---------------------------------------------------------------------------
# Rota: POST /usuarios/definir-senha
# ---------------------------------------------------------------------------
def test_definir_senha_sucesso(client, usuario_novo):
    """Com um token válido, a senha é definida e o login funciona"""
    token = create_definir_senha_token(usuario_novo.email)

    response = client.post(
        '/usuarios/definir-senha',
        json={'token': token, 'nova_senha': 'MinhaSenha123'},
    )

    # Confirma o retorno do status code 204 - SEM CONTEÚDO
    assert response.status_code == HTTPStatus.NO_CONTENT

    # Confirma que o login funciona com a nova senha
    login = client.post(
        '/auth/token',
        data={'username': usuario_novo.email, 'password': 'MinhaSenha123'},
    )
    assert login.status_code == HTTPStatus.OK


def test_definir_senha_link_ja_usado(client, usuario_novo):
    """O mesmo link não pode ser usado duas vezes"""
    token = create_definir_senha_token(usuario_novo.email)

    # Primeiro uso do link
    client.post(
        '/usuarios/definir-senha',
        json={'token': token, 'nova_senha': 'MinhaSenha123'},
    )

    # Segundo uso do mesmo link
    response = client.post(
        '/usuarios/definir-senha',
        json={'token': token, 'nova_senha': 'OutraSenha456'},
    )

    # Confirma o retorno do status code 400 - REQUISIÇÃO INVÁLIDA
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()['detail'] == 'Link inválido ou expirado'


def test_definir_senha_token_expirado(client, usuario_novo):
    """Depois de 24 horas, o link não vale mais"""
    agora = datetime(2026, 1, 1, 12, 0, 0)

    # Gera o token "no passado"
    with freeze_time(agora):
        token = create_definir_senha_token(usuario_novo.email)

    # Tenta usar o link 25 horas depois
    with freeze_time(agora + timedelta(hours=25)):
        response = client.post(
            '/usuarios/definir-senha',
            json={'token': token, 'nova_senha': 'MinhaSenha123'},
        )

    # Confirma o retorno do status code 400 - REQUISIÇÃO INVÁLIDA
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json()['detail'] == 'Link inválido ou expirado'


def test_definir_senha_com_token_de_acesso(client, usuario_novo):
    """Um token de acesso (login) não serve para definir senha"""
    token = create_access_token({'sub': usuario_novo.email})

    response = client.post(
        '/usuarios/definir-senha',
        json={'token': token, 'nova_senha': 'MinhaSenha123'},
    )

    # Confirma o retorno do status code 400 - REQUISIÇÃO INVÁLIDA
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_definir_senha_token_invalido(client):
    """Um texto qualquer no lugar do token é recusado"""
    response = client.post(
        '/usuarios/definir-senha',
        json={'token': 'isso-nao-e-um-token', 'nova_senha': 'MinhaSenha123'},
    )

    # Confirma o retorno do status code 400 - REQUISIÇÃO INVÁLIDA
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_definir_senha_curta(client, usuario_novo):
    """Senha com menos de 8 caracteres é recusada pelo schema"""
    token = create_definir_senha_token(usuario_novo.email)

    response = client.post(
        '/usuarios/definir-senha',
        json={'token': token, 'nova_senha': '123'},
    )

    # Confirma o retorno do status code 422 - DADOS INVÁLIDOS
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Função: criar_admin
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_criar_usuario_admin_quando_nao_existir(session, settings):
    """Criando o usuario admin com os dados do .env"""
    # Executa a função com o banco de testes vazio
    await criar_admin(session)

    # Consulta o usuario pelo email na base de dados
    admin = await session.scalar(
        select(Usuarios).where(Usuarios.email == settings.ADMIN_EMAIL)
    )

    # Verifica se o admin foi criado com os dados do .env
    assert admin is not None
    assert admin.nome == settings.ADMIN_USER
    assert admin.admin is True
    assert admin.primeiro_acesso is False

    # Verifica se a senha foi salva com hash, e não em texto puro
    assert admin.senha != settings.ADMIN_SENHA
    # Verifica se a senha confere com o hash
    assert verify_password(settings.ADMIN_SENHA, admin.senha)


@pytest.mark.asyncio
async def test_criar_admin_nao_duplica(session, settings):
    """Chamar a função duas vezes não cria dois admins"""
    # Simula a API subindo duas vezes
    await criar_admin(session)
    await criar_admin(session)

    # Conta quantos usuários existem com o email do admin
    total = await session.scalar(
        select(func.count())
        .select_from(Usuarios)
        .where(Usuarios.email == settings.ADMIN_EMAIL)
    )

    # Verifica se existe apenas um admin
    assert total == 1


@pytest.mark.asyncio
async def test_criar_admin_nao_altera_usuario_existente(session, settings):
    """Se o email do admin já existe, a função não mexe no registro"""
    # Cadastra antes um usuário com o mesmo email do admin
    existente = Usuarios(
        nome='Nome Original',
        email=settings.ADMIN_EMAIL,
        senha=get_password_hash('senha_original'),
    )
    session.add(existente)
    await session.commit()

    # Executa a função
    await criar_admin(session)

    # Busca o usuário novamente
    admin = await session.scalar(
        select(Usuarios).where(Usuarios.email == settings.ADMIN_EMAIL)
    )

    # Verifica se o registro continua como estava
    assert admin.nome == 'Nome Original'
    assert verify_password('senha_original', admin.senha)
