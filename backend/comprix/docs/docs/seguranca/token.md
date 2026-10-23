---
icon: lucide/fingerprint-pattern
title: Token
---

# :lucide-fingerprint-pattern: Token

## 🎟️ Token de acesso (JWT) na prática

Com as senhas protegidas pelo hash, falta resolver outro problema: **como a
API sabe quem está fazendo cada requisição?**

Pedir e-mail e senha a cada chamada seria inseguro e pouco prático. Por isso,
depois do login, o usuário recebe um **token JWT**: uma credencial
**assinada digitalmente** que ele envia nas próximas requisições.

```text
1. Usuário  ──(e-mail + senha)──▶  POST /auth/token
2. API      ◀──────(token JWT)───  confere a senha e assina o token
3. Usuário  ──(Bearer <token>)──▶  rotas protegidas
4. API      ──▶ valida a assinatura e a validade e identifica o usuário
```

---

## 1. Instalando a dependência

```bash
poetry add pyjwt
```

## 2. Configurando o `.env`

O token é assinado com uma **chave secreta** que **só o servidor conhece**.
Ela fica no `.env`, **nunca** no código nem no GitHub:

```env
SECRET_KEY="sua_chave"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES="60"
ADMIN_EMAIL="seu_email@test.com"
```

E no `settings.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ADMIN_EMAIL: str
```

| Variável | Para que serve |
|---|---|
| `SECRET_KEY` | Chave que **assina** o token. Quem a tiver consegue forjar tokens. |
| `ALGORITHM` | Algoritmo de assinatura. O `HS256` é o padrão para uma API única. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token. Quanto menor, menor o estrago se for roubado. |
| `ADMIN_EMAIL` | E-mail que recebe a claim `is_admin` no token. |

> ⚠️ Confira se o `.env` está no `.gitignore`.

---

##  3. ` função create_access_token`: criando o token

### Para que serve

É a função chamada **no momento do login**, depois que a senha foi conferida.
Ela gera o "crachá digital" do usuário: um token JWT que diz **quem ele é**,
**até quando** o acesso vale e, se for o caso, que ele é **administrador**.

O usuário guarda esse token e o envia em todas as próximas requisições, sem
precisar mandar a senha de novo.

### 📄 O código

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from jwt import encode

from comprix.settings import Settings


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
    if data.username == settings.ADMIN_EMAIL:
        to_encode.update({'is_admin': True})

    # Agora vamos criar o TOKEN com jwt encode
    encode_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encode_jwt
```

### Explicando passo a passo a função create_access_token

#### 1 Recebendo os dados

```python
def create_access_token(data: dict) -> str:
```

A função recebe um **dicionário** com as informações que vão dentro do token.
No COMPRIX, a rota de login chama assim:

```python
create_access_token(data={'sub': usuario.email})
```

A chave `sub` (*subject*, "assunto") é uma **claim padrão do JWT** e
identifica **o dono do token**. O retorno (`-> str`) é o token pronto, em
forma de texto.

#### 2 Fazendo uma cópia

```python
    to_encode = data.copy()
```

Vamos acrescentar informações ao dicionário. O `.copy()` garante que essas
alterações aconteçam numa **cópia**, sem modificar o dicionário de quem
chamou a função. Isso evita efeitos colaterais difíceis de rastrear.

#### 3 Calculando a validade

```python
expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
)
to_encode.update({'exp': expire})
```

| Parte | O que faz |
|---|---|
| `datetime.now(tz=ZoneInfo('UTC'))` | Pega a hora **atual em UTC**. O JWT trabalha sempre em UTC, para não depender do fuso do servidor. |
| `timedelta(minutes=...)` | Representa um intervalo de N minutos, vindo do `.env`. |
| `+` | Soma os dois: "agora + 30 minutos", por exemplo. |
| `{'exp': expire}` | Grava o resultado na claim **`exp`** (*expiration*). |

O PyJWT converte o `datetime` em número (timestamp) automaticamente. Depois
desse horário, o token é **recusado** em qualquer validação.

> ⏳ Validade curta é uma proteção: se o token for roubado, ele só serve por
> alguns minutos.

#### 4 Marcando o administrador

```python
if to_encode.get('sub') == settings.ADMIN_EMAIL:
    to_encode.update({'is_admin': True})
```

Se o e-mail do usuário (`sub`) for igual ao e-mail de admin configurado no
`.env`, o token ganha a claim **`is_admin`**. Para usuários comuns, essa
claim **simplesmente não existe** no token.

Usamos `.get('sub')` em vez de `['sub']` para não quebrar caso o `sub` não
venha: o `.get` devolve `None` em vez de lançar erro.

> A versão anterior usava `data.username`. Como `data` é um **dicionário**,
> isso lançava `AttributeError` em todo login. Em dicionários, acessamos os
> valores pela chave: `data['sub']` ou `data.get('sub')`.

#### 5 Assinando o token

```python
return encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

O `encode` do PyJWT:

1. transforma o dicionário em JSON e o codifica em base64 (o **payload**);
2. calcula uma **assinatura** usando a `SECRET_KEY` e o algoritmo (`HS256`);
3. junta tudo no formato `header.payload.assinatura`.

```text
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhQGIuY29tIiwiZXhwIjoxNzYxMjM0NTY3fQ.k3Jx...
└────── header ─────┘└────────────── payload ──────────────────┘└ assinatura ┘
```

### O que fica dentro do token

```json
{
  "sub": "usuario@comprix.com",
  "exp": 1761234567,
  "is_admin": true
}
```

| Claim | Significado |
|---|---|
| `sub` | **Quem** é o dono do token |
| `exp` | **Até quando** ele vale (em segundos desde 1970, UTC) |
| `is_admin` | Só aparece para o e-mail de administrador |

> 💡 **O payload pode ser lido por qualquer um**, porque é só base64. Mas
> **não pode ser alterado**: se alguém trocar o `sub` ou incluir
> `"is_admin": true`, a assinatura deixa de conferir e o token é recusado.
> Por isso **nunca** coloque senha ou dados sensíveis no token.


## 4. `função get_current_user`: validando o token

### Para que serve

Se o `create_access_token` **emite** o crachá, o `get_current_user` é o
**porteiro** que confere o crachá na entrada de cada rota protegida.

A cada requisição ele verifica se o token é **autêntico**, se ainda está
**dentro da validade** e se o usuário **ainda existe**. Se estiver tudo certo,
entrega o usuário para a rota; senão, barra a requisição com **401**.

### Antes da função: o `oauth2_scheme`

```python
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='auth/token', refreshUrl='auth/refresh'
)
```

É ele quem **extrai o token** da requisição. O cliente envia o cabeçalho:

```text
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
```

e o `oauth2_scheme` entrega à função apenas a parte depois de `Bearer`.

| Parâmetro | O que faz |
|---|---|
| `tokenUrl` | Indica a rota de login. Ativa o botão **Authorize** no `/docs`. |
| `refreshUrl` | **Apenas informativo** para a documentação. A rota `auth/refresh` precisa ser implementada à parte. |

> Se o cabeçalho `Authorization` não vier, o próprio FastAPI responde **401**
> antes mesmo de chamar a função.

### O código

```python
from http import HTTPStatus

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import DecodeError, ExpiredSignatureError, decode
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comprix.database import get_session
from comprix.models import Usuarios
from comprix.settings import Settings

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl='auth/token', refreshUrl='auth/refresh'
)


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> Usuarios:
    """Valida o token e retorna o usuário logado."""
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Credencial inválida',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except InvalidTokenError:
        raise credentials_exception

    subject_email = payload.get('sub')
    if not subject_email:
        raise credentials_exception

    usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == subject_email)
    )
    if not usuario:
        raise credentials_exception

    return usuario
```

### Passo a passo

#### 1 Recebendo as dependências

```python
async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> Usuarios:
```

Ninguém chama essa função diretamente: o **FastAPI** a executa sozinho e
injeta, via `Depends`:

- `session`: uma sessão **assíncrona** do banco, aberta pelo `get_session`;
- `token`: o token extraído do cabeçalho pelo `oauth2_scheme`.

A função é `async` porque vai consultar o banco com `await`.

#### 2 Preparando o erro padrão

```python
credentials_exception = HTTPException(
    status_code=HTTPStatus.UNAUTHORIZED,
    detail='Credencial inválida',
    headers={'WWW-Authenticate': 'Bearer'},
)
```

O erro é criado **uma vez** e reaproveitado em todas as falhas.

| Parte | Por quê |
|---|---|
| `HTTPStatus.UNAUTHORIZED` | Código **401**: "você não está autenticado". |
| `detail='Credencial inválida'` | Mensagem **genérica de propósito**: não revela se o problema foi expiração, assinatura falsa ou usuário inexistente. Quanto menos pistas, melhor contra ataques. |
| `WWW-Authenticate: Bearer` | Cabeçalho exigido pela especificação HTTP em respostas 401. Informa ao cliente que tipo de autenticação é esperado. |

#### 3 Decodificando e validando

```python
try:
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
except InvalidTokenError:
    raise credentials_exception
```

O `decode` faz o caminho inverso do `encode` e, no processo, **valida tudo**:

| Verificação | Se falhar, lança |
|---|---|
| O token tem o formato `header.payload.assinatura`? | `DecodeError` |
| A assinatura confere com a `SECRET_KEY`? | `InvalidSignatureError` |
| A claim `exp` ainda não passou? | `ExpiredSignatureError` |

Todas essas exceções são "filhas" de **`InvalidTokenError`**, então um único
`except` cobre todos os casos.

> O `algorithms=[...]` é **obrigatório por segurança**. Ele impede que um
> atacante monte um token dizendo "use o algoritmo `none`" (sem assinatura)
> e engane o servidor.

Se tudo estiver certo, `payload` é o dicionário original:
`{'sub': '...', 'exp': ..., 'is_admin': True}`.

#### 4 Identificando o dono do token

```python
subject_email = payload.get('sub')
if not subject_email:
    raise credentials_exception
```

Pega o e-mail da claim `sub`. Um token **sem dono** não serve para nada,
então é recusado.

#### 5 Conferindo no banco

```python
usuario = await session.scalar(
    select(Usuarios).where(Usuarios.email == subject_email)
)
if not usuario:
    raise credentials_exception
```

Mesmo com o token válido, o usuário pode ter sido **apagado depois do
login**. Por isso buscamos no banco:

- `select(Usuarios).where(...)` monta a consulta;
- `session.scalar(...)` executa e devolve **o objeto** ou `None`;
- se for `None`, o acesso é negado.

#### 6 Entregando o usuário

```python
return usuario
```

A rota recebe o objeto `Usuarios` completo, pronto para uso:

```python
@router.get('/me')
async def me(usuario: Usuarios = Depends(get_current_user)):
    return usuario
```

### Resumo do fluxo

```text
Requisição
   │
   ├─ sem cabeçalho Authorization? ───────────▶ 401 (oauth2_scheme)
   │
   ├─ token malformado, forjado ou expirado? ──▶ 401 (decode)
   │
   ├─ token sem 'sub'? ───────────────────────▶ 401
   │
   ├─ usuário não existe no banco? ───────────▶ 401
   │
   └─ tudo certo ─────────────────────────────▶ rota recebe o usuário ✅
```

---

## 5. O módulo `security.py` completo

```python
from datetime import datetime, timedelta
from http import HTTPStatus
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError, decode, encode
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


def get_password_hash(senha: str) -> str:
    """Gera o hash Argon2 da senha."""
    return pwd_context.hash(senha)


def verify_password(senha: str, hashed_password: str) -> bool:
    """Confere a senha digitada com o hash salvo no banco."""
    return pwd_context.verify(senha, hashed_password)


def create_access_token(data: dict) -> str:
    """Cria o token JWT de acesso.

    `data` deve conter a claim 'sub' com o e-mail do usuário.
    """
    to_encode = data.copy()

    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({'exp': expire})

    if to_encode.get('sub') == settings.ADMIN_EMAIL:
        to_encode.update({'is_admin': True})

    return encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> Usuarios:
    """Valida o token e retorna o usuário logado."""
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Credencial inválida',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except InvalidTokenError:
        raise credentials_exception

    subject_email = payload.get('sub')
    if not subject_email:
        raise credentials_exception

    usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == subject_email)
    )
    if not usuario:
        raise credentials_exception

    return usuario
```

### O que mudou em relação à versão anterior

| Antes | Depois | Por quê |
|---|---|---|
| `data.username` | `to_encode.get('sub')` | `data` é um dicionário; a linha antiga lançava `AttributeError` em todo login. |
| `except DecodeError` + `except ExpiredSignatureError` | `except InvalidTokenError` | Um único `except` cobre **todos** os erros de token. |
| Sem tipo de retorno | `-> str`, `-> bool`, `-> Usuarios` | Ajuda o editor, o autocompletar e o mypy. |

---

## 6. Testes

Como o projeto já usa **SQLite em memória**, os testes vão usar um **banco de
verdade** em vez de sessões falsas. As fixtures ficam no `conftest.py` e são
reaproveitadas por todos os arquivos de teste.

### Dependências

```bash
poetry add pytest-asyncio aiosqlite
```

E no `pyproject.toml`, para o pytest-asyncio não emitir avisos:

```toml
[tool.pytest.ini_options]
pythonpath = '.'
asyncio_default_fixture_loop_scope = 'function'
```

---

### 6.1 Problemas no `conftest.py` atual

| Problema | Consequência |
|---|---|
| A fixture `client` cria **outro** banco em memória, diferente do da fixture `session` | Um usuário criado pela `session` **não existe** para a API. O login nos testes nunca encontraria ninguém. |
| O banco do `client` não roda o `create_all` | A API acessaria um banco **sem tabelas**. |
| `monkeypatch.setattr('comprix.database.engine', ...)` | Se o `get_session` já capturou o engine original na importação, a troca não tem efeito e os testes podem bater no **banco real**. |
| `sqlite:///:memory:` sem `StaticPool` | No SQLite em memória, **cada conexão é um banco novo e vazio**. Sem o `StaticPool`, conexões diferentes enxergam bancos diferentes. |

A solução é usar **um único banco** e fazer a API usar a **mesma sessão** dos
testes, com o `app.dependency_overrides`.

---

### 6.2 Novo `tests/conftest.py`

```python
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
    senha = 'senha-de-teste-123'

    usuario = Usuarios(
        email='usuario@comprix.com',
        senha=get_password_hash(senha),
    )
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)

    usuario.clean_password = senha  # senha pura, só para os testes
    return usuario


@pytest_asyncio.fixture
async def admin(session, settings):
    senha = 'senha-de-admin-123'

    admin = Usuarios(
        email=settings.ADMIN_EMAIL,
        senha=get_password_hash(senha),
    )
    session.add(admin)
    await session.commit()
    await session.refresh(admin)

    admin.clean_password = senha
    return admin


@pytest.fixture
def token(client, usuario):
    response = client.post(
        '/auth/token',
        data={'username': usuario.email, 'password': usuario.clean_password},
    )
    return response.json()['access_token']
```

> ⚠️ Ajuste `Usuarios(email=..., senha=...)` para os campos reais do seu
> model. Se houver outros campos obrigatórios, como `nome`, inclua-os aqui.

---

### 6.3 Entendendo cada fixture

> 💡 **Fixture** é uma função que **prepara algo** para o teste. O teste só
> precisa declarar o nome dela como parâmetro, e o pytest executa a fixture
> e entrega o resultado. Uma fixture pode depender de outras:
> `token` → `client` + `usuario` → `session`.

#### `settings`

Entrega as configurações do `.env` para os testes, como o `ADMIN_EMAIL`, a
`SECRET_KEY` e o tempo de expiração.

#### `session`: o banco de testes

```python
engine = create_async_engine(
    'sqlite+aiosqlite:///:memory:',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)
```

| Parte | Por quê |
|---|---|
| `sqlite+aiosqlite:///:memory:` | Banco **em memória**: nasce e morre com o teste, sem criar arquivo. |
| `poolclass=StaticPool` | Faz todas as operações usarem **a mesma conexão**, ou seja, o **mesmo banco**. |
| `check_same_thread=False` | O `TestClient` executa a API em outra thread. Sem isso, o SQLite recusaria o acesso. |

Depois disso, a fixture:

1. cria todas as tabelas (`create_all`);
2. abre uma sessão e a entrega ao teste (`yield`);
3. ao final do teste, apaga as tabelas e fecha o engine.

Cada teste começa com um **banco limpo**: um teste nunca interfere no outro.

#### `client`: a API apontando para o banco de testes

```python
app.dependency_overrides[get_session] = get_session_override
```

O `dependency_overrides` diz ao FastAPI: "sempre que uma rota pedir
`get_session`, entregue esta **outra** função". Assim, a API usa **a mesma
sessão** da fixture `session`, e tudo que o teste gravar fica visível para as
rotas.

O `.clear()` no final desfaz a troca, para não vazar para outros testes.

#### `usuario` e `admin`: dados prontos no banco

Gravam um usuário comum e um administrador no banco de testes, já com a senha
**em hash**, como no sistema real.

```python
usuario.clean_password = senha
```

O banco só guarda o hash, mas os testes de login precisam da **senha pura**.
Por isso ela fica num atributo extra do objeto, que **só existe nos testes**.

O `admin` usa o `settings.ADMIN_EMAIL`, então recebe a claim `is_admin`.

#### `token`: um usuário já logado

Faz o login de verdade em `/auth/token` e devolve o token. Qualquer teste que
precise de um usuário autenticado só declara `token` como parâmetro.

---

### 6.4 Testes unitários: `tests/test_security.py`

Testam as funções do `security.py` **diretamente**, mas agora com o **banco
de verdade** da fixture `session`.

```python
from datetime import datetime, timedelta
from http import HTTPStatus
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from jwt import decode, encode

from comprix.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)


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
# Hash de senha
# ---------------------------------------------------------------------------
def test_hash_nao_e_a_senha_em_texto_puro():
    hash_ = get_password_hash('minhasenha')
    assert hash_ != 'minhasenha'
    assert hash_.startswith('$argon2')


def test_verify_password():
    hash_ = get_password_hash('minhasenha')
    assert verify_password('minhasenha', hash_)
    assert not verify_password('outrasenha', hash_)


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------
def test_token_contem_sub_e_exp(settings):
    token = create_access_token({'sub': 'teste@comprix.com'})
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    assert payload['sub'] == 'teste@comprix.com'
    assert 'exp' in payload


def test_token_expira_no_tempo_configurado(settings):
    inicio = agora().timestamp()
    token = create_access_token({'sub': 'teste@comprix.com'})
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    esperado = inicio + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert abs(payload['exp'] - esperado) < 5


def test_usuario_comum_nao_recebe_is_admin(settings):
    token = create_access_token({'sub': 'teste@comprix.com'})
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
    data = {'sub': 'teste@comprix.com'}
    create_access_token(data)
    assert data == {'sub': 'teste@comprix.com'}


# ---------------------------------------------------------------------------
# get_current_user com o banco em memória
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_token_valido_retorna_o_usuario_do_banco(session, usuario):
    token = create_access_token({'sub': usuario.email})

    resultado = await get_current_user(session=session, token=token)

    assert resultado.id == usuario.id
    assert resultado.email == usuario.email


@pytest.mark.asyncio
async def test_token_malformado(session):
    await espera_401(session, 'isto-nao-e-um-jwt')


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
```

### Entendendo os testes unitários

#### Auxiliares

- **`agora()`**: hora atual em UTC, a mesma referência do módulo.
- **`token_manual()`**: o `create_access_token` sempre gera tokens
  **corretos**. Para testar erros, precisamos de tokens "defeituosos": vencidos,
  sem `sub` ou assinados com outra chave. Esta função monta um token com
  **qualquer payload** e **qualquer chave**.
- **`espera_401()`**: usa `pytest.raises(HTTPException)` para dizer "**espero**
  que este bloco lance erro". Se não lançar, o teste falha. Depois confere o
  status **401** e o cabeçalho `WWW-Authenticate`.

#### Hash de senha

| Teste | Garante que... |
|---|---|
| `test_hash_nao_e_a_senha_em_texto_puro` | a senha nunca é guardada como foi digitada e o algoritmo é o Argon2 |
| `test_verify_password` | a senha certa é aceita e a errada é recusada |

#### `create_access_token`

| Teste | Garante que... |
|---|---|
| `test_token_contem_sub_e_exp` | o token identifica o usuário e tem validade |
| `test_token_expira_no_tempo_configurado` | a validade bate com o `.env` (com 5 s de tolerância para o tempo de execução) |
| `test_usuario_comum_nao_recebe_is_admin` | um usuário comum **não** vira admin por engano |
| `test_admin_recebe_is_admin` | o e-mail do `ADMIN_EMAIL` recebe a claim |
| `test_nao_altera_o_dicionario_original` | o `.copy()` funciona e não há efeitos colaterais |

Esses testes não precisam de banco: só geram o token e o abrem com `decode`.

#### `get_current_user`

Aqui está a principal melhoria: a função consulta **o banco em memória de
verdade**, recebido pela fixture `session`.

> 💡 Chamamos `get_current_user(session=..., token=...)` passando os
> valores **diretamente**. Fora de uma rota, o `Depends` não é acionado.

| Teste | O que simula | Garante que... |
|---|---|---|
| `test_token_valido_retorna_o_usuario_do_banco` | login normal | o usuário certo é **buscado no banco** e devolvido |
| `test_token_malformado` | lixo no cabeçalho | entradas inválidas não derrubam a API |
| `test_token_expirado` | token vencido há 1 minuto | tokens vencidos não dão acesso |
| `test_token_assinado_com_outra_chave` | **atacante** sem a `SECRET_KEY` | tokens **forjados** são recusados |
| `test_token_sem_sub` | token sem dono | um token precisa identificar alguém |
| `test_token_de_email_que_nao_existe` | token assinado para um e-mail que não está no banco | só usuários cadastrados entram |
| `test_usuario_apagado_depois_do_login` | usuário removido com token ainda válido | quem foi apagado **perde o acesso na hora** |

O último teste só é possível com um banco real: o usuário é gravado pela
fixture, o token é gerado, o usuário é **apagado de verdade** com
`session.delete` e, então, o mesmo token passa a ser recusado.

---

### 6.5 Testes de integração: `tests/test_auth.py`

Testam o **fluxo completo pela API**, como um cliente real faria: login →
token → rota protegida.

```python
from datetime import datetime, timedelta
from http import HTTPStatus
from zoneinfo import ZoneInfo

from jwt import decode, encode


def test_login_retorna_token(client, usuario):
    response = client.post(
        '/auth/token',
        data={'username': usuario.email, 'password': usuario.clean_password},
    )
    dados = response.json()

    assert response.status_code == HTTPStatus.OK
    assert dados['token_type'] == 'bearer'
    assert 'access_token' in dados


def test_login_com_senha_errada(client, usuario):
    response = client.post(
        '/auth/token',
        data={'username': usuario.email, 'password': 'senha-errada'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_com_email_inexistente(client):
    response = client.post(
        '/auth/token',
        data={'username': 'ninguem@comprix.com', 'password': 'qualquer'},
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_login_do_admin_gera_token_com_is_admin(client, admin, settings):
    response = client.post(
        '/auth/token',
        data={'username': admin.email, 'password': admin.clean_password},
    )
    token = response.json()['access_token']
    payload = decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )

    assert payload['is_admin'] is True


def test_rota_protegida_com_token(client, usuario, token):
    response = client.get(
        '/auth/me', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()['email'] == usuario.email


def test_rota_protegida_sem_token(client):
    response = client.get('/auth/me')

    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_rota_protegida_com_token_expirado(client, usuario, settings):
    token = encode(
        {
            'sub': usuario.email,
            'exp': datetime.now(tz=ZoneInfo('UTC')) - timedelta(minutes=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    response = client.get(
        '/auth/me', headers={'Authorization': f'Bearer {token}'}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json() == {'detail': 'Credencial inválida'}
```

> ⚠️ Ajuste `/auth/me` se a sua rota protegida estiver em outro caminho.

### 🔍 Entendendo os testes de integração

Estes testes são **síncronos** (não usam `async`) porque o `TestClient`
cuida do loop assíncrono da API sozinho. Mesmo assim, eles podem usar as
fixtures assíncronas `usuario` e `admin`.

O formulário de login vai em `data=` (e não em `json=`) porque o
`OAuth2PasswordRequestForm` espera um **formulário**, como o padrão OAuth2
exige.

| Teste | O que faz | Garante que... |
|---|---|---|
| `test_login_retorna_token` | faz login com e-mail e senha corretos | o login devolve **200**, um `access_token` e o tipo `bearer` |
| `test_login_com_senha_errada` | usa a senha errada | senha errada não gera token (**401**) |
| `test_login_com_email_inexistente` | usa um e-mail que não está no banco | não dá para logar com conta inexistente (**401**) |
| `test_login_do_admin_gera_token_com_is_admin` | faz login como admin e abre o token | o fluxo real de login marca o admin |
| `test_rota_protegida_com_token` | chama `/auth/me` com o token da fixture | um usuário logado acessa a rota e recebe **os próprios dados** |
| `test_rota_protegida_sem_token` | chama `/auth/me` sem cabeçalho | rotas protegidas exigem login (**401**) |
| `test_rota_protegida_com_token_expirado` | envia um token vencido | a API recusa tokens vencidos e responde com a mensagem genérica |

> 🔒 Os testes de senha errada e de e-mail inexistente devolvem o **mesmo**
> erro. Isso é intencional: se as respostas fossem diferentes, um atacante
> descobriria quais e-mails estão cadastrados.

---

### 6.6 Estrutura final

```text
comprix/
├── src/
│   └── comprix/
│       ├── app.py
│       ├── database.py
│       ├── models.py
│       ├── security.py
│       └── settings.py
└── tests/
    ├── conftest.py        👈 fixtures compartilhadas
    ├── test_security.py   👈 testes unitários (funções + banco em memória)
```

### 🧭 Unitário x integração

| | Unitários (`test_security.py`) | Integração (`test_auth.py`) |
|---|---|---|
| **O que testam** | As funções do `security.py` isoladas | O fluxo completo pela API |
| **Como chamam** | `create_access_token(...)`, `await get_current_user(...)` | `client.post(...)`, `client.get(...)` |
| **Quando falham** | Apontam **exatamente** qual função quebrou | Mostram que **algo** no fluxo do usuário quebrou |

Os dois tipos se complementam: os unitários localizam o erro, e os de
integração garantem que as peças funcionam **juntas**.

### ▶️ Rodando

```bash
pytest -v
```

Ou só um arquivo:

```bash
pytest tests/test_auth.py -v
```

> Rodado contra a versão antiga do `security.py`, o
> `test_login_retorna_token` falharia com `AttributeError: 'dict' object has
> no attribute 'username'`. É para isso que os testes existem: o erro aparece
> aqui, e não no primeiro login em produção.

---

## ⏭️ 7. Próximos passos

- 🔄 Implementar a rota `auth/refresh` para renovar o token sem pedir a senha
  de novo.
- 👑 Trocar o `ADMIN_EMAIL` pela coluna de admin da tabela `usuarios`
  (migration `03`), para permitir mais de um administrador.
- 🧾 Medir a cobertura dos testes com `pytest --cov=comprix`.