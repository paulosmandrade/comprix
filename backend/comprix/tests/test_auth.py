from datetime import datetime, timedelta
from http import HTTPStatus

from freezegun import freeze_time
from jwt import decode

from comprix.settings import Settings

settings = Settings()


# ---------------------------------------------------------------------------
# Rota: Auth
# ---------------------------------------------------------------------------


def test_login_sucesso(client, usuario):
    """Teste de autenticação, passando os parametros da rota"""
    response = client.post(
        '/auth/token',
        data={'username': usuario.email, 'password': usuario.clean_password},
    )

    # Retorna o código 200 - sucesso
    assert response.status_code == HTTPStatus.OK
    # verifica se dentro do json do token tem o 'bearer'
    assert response.json()['token_type'] == 'bearer'
    # verifica se dentro do json tem o token
    assert response.json()['access_token']


def test_token_comtem_email_e_expiracao(client, usuario):
    """Teste que verifica se dentro do token existe as CLAINS sub e exp"""
    # Faz a requisição de autenticação passando os parametros
    response = client.post(
        '/auth/token',
        data={'username': usuario.email, 'password': usuario.clean_password},
    )

    # Guarda o token em um objeto
    token = response.json()['access_token']

    # Utiliza o decode para comparar
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    # verifica se dentro do token o sub e igual o email
    assert payload['sub'] == usuario.email
    # verifica se dentro do token tem o 'exp' de expiração
    assert 'exp' in payload


def test_login_senha_incorreta(client, usuario):
    """Teste que verifica quando o usuário digita a senha inválida"""
    # Faz a requisição de autenticação passando os parametros
    response = client.post(
        '/auth/token',
        data={'username': usuario.email, 'password': 'senha_errada'},
    )

    # verifica se o status code É 401 NÃO AUTORIZADO
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # verifica se a mensagem está correta no json
    assert response.json()['detail'] == 'Email ou senhas incorretos'


def test_login_email_incorreto(client, usuario):
    """Teste que verifica quando o email digito está inválido"""
    # Faz a requisição de autenticação passando os parametros
    response = client.post(
        '/auth/token',
        data={
            'username': 'incorreto@email.com',
            'password': usuario.clean_password,
        },
    )

    # verifica se o status code É 401 NÃO AUTORIZADO
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # verifica se a mensagem está correta no json
    assert response.json()['detail'] == 'Email ou senhas incorretos'


def test_login_sem_campos_digitados(client):
    """Teste quando solicita a autenticação e não digita os email e senha"""
    # Faz a requisição de autenticação passando os parametros
    response = client.post('/auth/token', data={})

    # verifica se o status code É 422 UNPROCESSABLE_ENTITY
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# Rota: Refresh
# ---------------------------------------------------------------------------
def test_refresh_token_sucesso(client, usuario, token):
    """Teste que renova o token com um token válido"""
    # Faz a requisição de autenticação passando os parametros
    response = client.post(
        '/auth/refresh',
        headers={'Authorization': f'Bearer {token}'},
    )

    # Validação se o token esta Ok
    assert response.status_code == HTTPStatus.OK
    assert response.json()['token_type'] == 'bearer'

    # Faz o deconde para saber se o sub e email estão iguais
    payload = decode(
        response.json()['access_token'],
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )

    # Faz a verificação e o sub e email do novo token são iguais
    assert payload['sub'] == usuario.email


def test_refresh_token_sem_token_anterior(client):
    """Teste que tenta renovasr sem enviar o token anterior"""
    # Faz a requisição, mas sem passar o token anterior
    response = client.post('/auth/refresh')

    # verifica se o status code É 401 NÃO AUTORIZADO
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_refresh_token_invalido(client):
    """Teste que tenta renovar com um token falso"""
    # Faz a requisição com o token inválido
    response = client.post(
        '/auth/refresh',
        headers={'Authorization': 'Bearer token-invalido'},
    )

    # verifica se o status code É 401 NÃO AUTORIZADO
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # verifica o aviso para o usuario que as credenciais inválidas
    assert response.json()['detail'] == 'Credencial inválida'


def test_refresh_token_expirado(client, usuario):
    """Teste que tenta renovar com um token já expirado"""
    agora = datetime(2026, 1, 1, 12, 0, 0)

    # Gera o token "no passado" com a biblioteca freezegun(freeze_time)
    # Com esse recurso vamos falar que a hora e da variavel agora
    with freeze_time(agora):
        response = client.post(
            '/auth/token',
            data={
                'username': usuario.email,
                'password': usuario.clean_password,
            },
        )
        token = response.json()['access_token']

    # Avança o relógio para depois da expiração
    depois = agora + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES + 1
    )

    # gerando o refresh com o token explirado.
    with freeze_time(depois):
        response = client.post(
            '/auth/refresh',
            headers={'Authorization': f'Bearer {token}'},
        )

    # verifica se o status code É 401 NÃO AUTORIZADO
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    # verifica o aviso para o usuario que as credenciais inválidas
    assert response.json()['detail'] == 'Credencial inválida'
