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
ADMIN_USER="Administrador"
ADMIN_EMAIL="seu_email@test.com"
ADMIN_SENHA="senha_do_admin"
```

E no `settings.py`:

```python title="src/comprix/settings.py"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ADMIN_USER: str
    ADMIN_EMAIL: str
    ADMIN_SENHA: str
```

| Variável | Para que serve |
|---|---|
| `SECRET_KEY` | Chave que **assina** o token. Quem a tiver consegue forjar tokens. |
| `ALGORITHM` | Algoritmo de assinatura. O `HS256` é o padrão para uma API única. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Validade do token. Quanto menor, menor o estrago se for roubado. |
| `ADMIN_USER`, `ADMIN_EMAIL`, `ADMIN_SENHA` | Dados do administrador criado automaticamente pela função `criar_admin()`. O `ADMIN_EMAIL` também recebe a claim `is_admin` no token. |

> ⚠️ Confira se o `.env` está no `.gitignore`.

---

## 3. Função `create_access_token`: criando o token

### Para que serve

É a função chamada **no momento do login**, depois que a senha foi conferida.
Ela gera o "crachá digital" do usuário: um token JWT que diz **quem ele é** e
**até quando** o acesso vale.

O usuário guarda esse token e o envia em todas as próximas requisições, sem
precisar mandar a senha de novo.

### 📄 O código

```python title="src/comprix/security.py"
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from jwt import encode

from comprix.settings import Settings

settings = Settings()


# Criando o Token
def create_access_token(data: dict):
    to_encode = data.copy()

    # Acrescenta minutos no tempo atual, para validade do token
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    # Dentro do dicionário adiciona a CLAIM que tem a expiração do Token
    to_encode.update({'exp': expire})

    # Claim is_admin
    if to_encode.get('sub') == settings.ADMIN_EMAIL:
        to_encode.update({'is_admin': True})

    # Agora vamos criar o TOKEN com jwt encode
    encode_jwt = encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encode_jwt
```

### Explicando passo a passo

#### 1 Recebendo os dados

```python
def create_access_token(data: dict):
```

A função recebe um **dicionário** com as informações que vão dentro do token.
No COMPRIX, a rota de login chama assim:

```python
create_access_token(data={'sub': usuario.email})
```

A chave `sub` (*subject*, "assunto") é uma **claim padrão do JWT** e
identifica **o dono do token**. O retorno é o token pronto, em forma de texto.

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
| `+` | Soma os dois: "agora + 60 minutos", por exemplo. |
| `{'exp': expire}` | Grava o resultado na claim **`exp`** (*expiration*). |

O PyJWT converte o `datetime` em número (timestamp) automaticamente. Depois
desse horário, o token é **recusado** em qualquer validação.

> ⏳ Validade curta é uma proteção: se o token for roubado, ele só serve por
> alguns minutos.

#### 4 A claim `is_admin`

```python
if to_encode.get('sub') == settings.ADMIN_EMAIL:
    to_encode.update({'is_admin': True})
```

Se o e-mail do usuário (`sub`) for igual ao `ADMIN_EMAIL` do `.env`, o token
ganha a claim **`is_admin`**. Para os demais usuários, essa claim **não
existe** no token.

Usamos `.get('sub')` em vez de `['sub']` para não quebrar caso o `sub` não
venha: o `.get` devolve `None` em vez de lançar erro.

!!! warning "A claim `is_admin` é apenas informativa"
    O backend **não usa** essa claim para liberar ou bloquear rotas. Quem
    decide se um usuário é administrador é a **coluna `admin` da tabela
    `usuarios`**, verificada pela função `get_current_admin`
    ([seção 5](#5-funcao-get_current_admin-restringindo-ao-administrador)).

    Ela pode ser útil no **frontend**, por exemplo para mostrar ou esconder o
    menu de administração. Mas tem limitações:

    - só vale para o `ADMIN_EMAIL`, não para outros usuários com `admin=True`;
    - se a permissão for retirada, o token antigo continua dizendo
      `is_admin: true` até expirar.

#### 5 Assinando o token

```python
encode_jwt = encode(
    to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
)
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
  "exp": 1761234567
}
```

| Claim | Significado |
|---|---|
| `sub` | **Quem** é o dono do token |
| `exp` | **Até quando** ele vale (em segundos desde 1970, UTC) |
| `is_admin` | Só aparece para o `ADMIN_EMAIL` (informativa) |

> 💡 **O payload pode ser lido por qualquer um**, porque é só base64. Mas
> **não pode ser alterado**: se alguém trocar o `sub` ou incluir
> `"is_admin": true`, a assinatura deixa de conferir e o token é recusado.
> Por isso **nunca** coloque senha ou dados sensíveis no token.

---

## 4. Função `get_current_user`: validando o token

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
| `refreshUrl` | **Apenas informativo** para a documentação. A rota está implementada em [Refresh Token](../routers/refresh.md). |

> Se o cabeçalho `Authorization` não vier, o próprio FastAPI responde **401**
> antes mesmo de chamar a função.

### O código

```python title="src/comprix/security.py"
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
```

### Passo a passo

#### 1 Recebendo as dependências

```python
async def get_current_user(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme),
):
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
    subject_email = payload.get('sub')

    if not subject_email:
        raise credentials_exception

except DecodeError:
    raise credentials_exception

except ExpiredSignatureError:
    raise credentials_exception
```

O `decode` faz o caminho inverso do `encode` e, no processo, **valida tudo**:

| Verificação | Se falhar, lança | Capturado por |
|---|---|---|
| O token tem o formato `header.payload.assinatura`? | `DecodeError` | `except DecodeError` |
| A assinatura confere com a `SECRET_KEY`? | `InvalidSignatureError` | `except DecodeError` (é uma subclasse dele) |
| A claim `exp` ainda não passou? | `ExpiredSignatureError` | `except ExpiredSignatureError` |

Dentro do mesmo `try`, pegamos o e-mail da claim `sub`. Um token **sem dono**
não serve para nada, então também é recusado.

> O `algorithms=[...]` é **obrigatório por segurança**. Ele impede que um
> atacante monte um token dizendo "use o algoritmo `none`" (sem assinatura)
> e engane o servidor.

!!! tip "Dica: um único `except`"
    Todas as exceções de token do PyJWT herdam de `InvalidTokenError`. Se
    quiser simplificar, os dois `except` podem virar um só:

    ```python
    from jwt import InvalidTokenError

    try:
        payload = decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        subject_email = payload.get('sub')

        if not subject_email:
            raise credentials_exception

    except InvalidTokenError:
        raise credentials_exception
    ```

#### 4 Conferindo no banco

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

#### 5 Entregando o usuário

```python
return usuario
```

A rota recebe o objeto `Usuarios` completo, pronto para uso:

```python
CurrentUser = Annotated[Usuarios, Depends(get_current_user)]


@router.get('/me')
async def me(usuario: CurrentUser):
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

## 5. Função `get_current_admin`: restringindo ao administrador

### Para que serve

Algumas rotas, como **criar, alterar e excluir usuários**, só podem ser usadas
por administradores. O `get_current_admin` é um **segundo porteiro**: ele
reaproveita o `get_current_user` e, depois, confere se o usuário é admin.

### O código

```python title="src/comprix/security.py"
async def get_current_admin(
    usuario: Usuarios = Depends(get_current_user),
):
    if not usuario.admin:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail='Acesso permitido somente para administradores',
        )

    return usuario
```

### Passo a passo

#### 1 Reaproveitando o `get_current_user`

```python
usuario: Usuarios = Depends(get_current_user)
```

Antes de executar o `get_current_admin`, o FastAPI executa o
`get_current_user`. Ou seja, o token já foi **validado** e o usuário já foi
**buscado no banco**. Se algo falhar ali, a resposta é **401** e o
`get_current_admin` nem chega a rodar.

#### 2 Conferindo a permissão

```python
if not usuario.admin:
    raise HTTPException(
        status_code=HTTPStatus.FORBIDDEN,
        detail='Acesso permitido somente para administradores',
    )
```

A verificação usa a **coluna `admin` do banco**, não a claim `is_admin` do
token. Assim:

- qualquer usuário com `admin=True` é reconhecido como administrador;
- se a permissão for retirada no banco, o efeito é **imediato**, mesmo que
  o token ainda esteja válido.

#### 3 401 ou 403?

| Status | Significado | Quem responde |
|---|---|---|
| `401 Unauthorized` | "Não sei quem você é": sem token, token inválido ou expirado | `get_current_user` |
| `403 Forbidden` | "Sei quem você é, mas você não tem permissão" | `get_current_admin` |

### Usando nas rotas

```python title="src/comprix/routers/usuarios.py"
from comprix.security import get_current_admin

CurrentUserAdmin = Annotated[Usuarios, Depends(get_current_admin)]


@router.post(
    '/',
    status_code=HTTPStatus.CREATED,
    response_model=UsuarioPublico,
)
async def criar_usuarios(
    user: UsuarioSchema,
    session: Session,
    current_user: CurrentUserAdmin,
): ...
```

Basta receber um parâmetro do tipo `CurrentUserAdmin`. Mesmo sem ser usado
dentro da função, ele obriga o FastAPI a executar a verificação.

| Tipo | Quem pode acessar |
|---|---|
| `CurrentUser` | Qualquer usuário logado |
| `CurrentUserAdmin` | Somente administradores |

---

## 6. O módulo `security.py` completo

```python title="src/comprix/security.py"
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

    # Dentro do dicionário adiciona a CLAIM que tem a expiração do Token
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


# Validando se o usuario e administrador
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
```

A função `create_definir_senha_token` é explicada na página
[Usuários](../routers/usuarios.md#5-o-token-do-link-ajustes-no-securitypy).

---

## 7. Testes

Como o projeto já usa **SQLite em memória**, os testes usam um **banco de
verdade** em vez de sessões falsas. As fixtures ficam no `conftest.py` e são
reaproveitadas por todos os arquivos de teste.

### Dependências

```bash
poetry add --group dev pytest-asyncio
```

O `aiosqlite` já foi instalado como dependência principal na página
[Sqlite - Models](../sqlite.md), porque a API também usa.

E no `pyproject.toml`, a configuração do pytest:

```toml
[tool.pytest]
pythonpath = ['src']
addopts = ['-p', 'no:warnings', '--cov=comprix', '--cov-context=test']
asyncio_default_fixture_loop_scope = 'function'
```

| Opção | Para que serve |
|---|---|
| `pythonpath = ['src']` | Permite importar `comprix` nos testes, já que o pacote fica em `src`. |
| `addopts` | Opções usadas em toda execução: esconde avisos e mede a cobertura por teste. |
| `asyncio_default_fixture_loop_scope` | Evita o aviso do pytest-asyncio sobre o escopo do *event loop*. |

---

### 7.1 Por que o `conftest.py` é montado assim

Alguns cuidados evitam problemas difíceis de encontrar:

| Cuidado | Sem ele... |
|---|---|
| A API e os testes usam **o mesmo banco** | Um usuário criado pela `session` **não existiria** para a API, e o login nos testes nunca encontraria ninguém. |
| O banco de testes roda o `create_all` | A API acessaria um banco **sem tabelas**. |
| Usar `app.dependency_overrides` em vez de `monkeypatch` no engine | Se o `get_session` já tiver capturado o engine original, a troca não tem efeito e os testes podem bater no **banco real**. |
| `StaticPool` no SQLite em memória | **Cada conexão seria um banco novo e vazio**, e conexões diferentes enxergariam bancos diferentes. |

---

### 7.2 O `tests/conftest.py`

```python title="tests/conftest.py"
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
        nome='Usuário teste',
        email='usuario@comprix.com.br',
        senha=get_password_hash(senha),
    )
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)

    usuario.clean_password = senha  # senha pura, só para os testes
    return usuario


@pytest_asyncio.fixture
async def usuario_admin(session):
    senha = 'senha_admin'

    admin = Usuarios(
        nome='Admin Teste',
        email='admin@comprix.com.br',
        senha=get_password_hash(senha),
        admin=True,
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


@pytest.fixture
def token_admin(client, usuario_admin):
    response = client.post(
        '/auth/token',
        data={
            'username': usuario_admin.email,
            'password': usuario_admin.clean_password,
        },
    )
    return response.json()['access_token']
```

> ⚠️ Ajuste os campos de `Usuarios(...)` para os campos reais do seu model.
> Se houver outros campos obrigatórios, inclua-os aqui.

> 💡 Mais adiante, na página [Usuários](../routers/usuarios.md#131-ajustes-no-conftestpy),
> o `conftest.py` recebe mais uma fixture, a `emails_enviados`, que impede os
> testes de enviarem e-mails de verdade.

---

### 7.3 Entendendo cada fixture

> 💡 **Fixture** é uma função que **prepara algo** para o teste. O teste só
> precisa declarar o nome dela como parâmetro, e o pytest executa a fixture
> e entrega o resultado. Uma fixture pode depender de outras:
> `token` → `client` + `usuario` → `session`.

#### `settings`

Entrega as configurações do `.env` para os testes, como a `SECRET_KEY`, o
`ALGORITHM`, o `ADMIN_EMAIL` e o tempo de expiração.

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

#### `usuario` e `usuario_admin`: dados prontos no banco

Gravam um usuário **comum** e um **administrador** (`admin=True`) no banco de
testes, já com a senha **em hash**, como no sistema real.

```python
usuario.clean_password = senha
```

O banco só guarda o hash, mas os testes de login precisam da **senha pura**.
Por isso ela fica num atributo extra do objeto, que **só existe nos testes** e
não vai para o banco.

!!! warning "Senha em texto puro nos testes"
    No login dos testes, use `usuario.clean_password`, nunca `usuario.senha`.
    O `usuario.senha` é o **hash**, e enviá-lo faz o `verify_password` falhar
    com **401**.

#### `token` e `token_admin`: usuários já logados

Fazem o login de verdade em `/auth/token` e devolvem o token. Qualquer teste
que precise de um usuário autenticado só declara `token` (usuário comum) ou
`token_admin` (administrador) como parâmetro.

O `token_admin` é usado nos testes de integração da página de **Usuários**.

---

### 7.4 Testes unitários: `tests/test_security.py`

Testam as funções do `security.py` **diretamente**, com o **banco de
verdade** da fixture `session`.

```python title="tests/test_security.py"
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
    # senha_hash é diferente do texto puro
    assert senha_hash != 'minha_senha'
    # senha_hash começa com $argon2
    assert senha_hash.startswith('$argon2')


def test_hash_da_mesma_senha_muda_a_cada_requisicao():
    assert get_password_hash('abc') != get_password_hash('abc')


def test_verify_password_senha_correta():
    senha_hash = get_password_hash('minha_senha')
    # Retorna True para a senha correta
    assert verify_password('minha_senha', senha_hash)


def test_verify_password_senha_errada():
    senha_hash = get_password_hash('minha_senha')
    # Retorna False para a senha errada
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
async def test_token_valido_retorna_o_usuario_do_banco(session, usuario):
    token = create_access_token({'sub': usuario.email})

    resultado = await get_current_user(session=session, token=token)

    assert resultado.id == usuario.id
    assert resultado.email == usuario.email


@pytest.mark.asyncio
async def test_token_malformado(session):
    await espera_401(session, 'isso_nao_e_um_jwt')


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
```

### Entendendo os testes unitários

#### Auxiliares

- **`agora()`**: hora atual em UTC, a mesma referência do módulo.
- **`token_manual()`**: o `create_access_token` sempre gera tokens
  **corretos**. Para testar erros, precisamos de tokens "defeituosos":
  vencidos, sem `sub` ou assinados com outra chave. Esta função monta um
  token com **qualquer payload** e **qualquer chave**.
- **`espera_401()`**: usa `pytest.raises(HTTPException)` para dizer "**espero**
  que este bloco lance erro". Se não lançar, o teste falha. Depois confere o
  status **401** e o cabeçalho `WWW-Authenticate`.

#### Hash de senha

| Teste | Garante que... |
|---|---|
| `test_hash_nao_e_a_senha_em_texto_puro` | a senha nunca é guardada como foi digitada e o algoritmo é o Argon2 |
| `test_hash_da_mesma_senha_muda_a_cada_requisicao` | o *salt* aleatório gera um hash diferente a cada vez |
| `test_verify_password_senha_correta` | a senha certa é aceita |
| `test_verify_password_senha_errada` | a senha errada é recusada |

#### `create_access_token`

| Teste | Garante que... |
|---|---|
| `test_token_contem_sub_e_exp` | o token identifica o usuário e tem validade |
| `test_token_expira_no_tempo_configurado` | a validade bate com o `.env` (com 5 s de tolerância para o tempo de execução) |
| `test_usuario_comum_nao_recebe_is_admin` | um e-mail comum **não** recebe a claim `is_admin` |
| `test_admin_recebe_is_admin` | o `ADMIN_EMAIL` recebe a claim |
| `test_nao_altera_o_dicionario_original` | o `.copy()` funciona e não há efeitos colaterais |

Esses testes não precisam de banco: só geram o token e o abrem com `decode`.

#### `get_current_user`

A função consulta **o banco em memória de verdade**, recebido pela fixture
`session`.

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

#### `get_current_admin`

Aqui passamos o usuário direto no parâmetro `usuario=`, sem token. Numa
chamada direta, o `Depends(get_current_user)` é ignorado, então o teste foca
**apenas** na regra de administrador.

| Teste | O que simula | Garante que... |
|---|---|---|
| `test_get_current_admin_com_usuario_admin` | usuário com `admin=True` | o administrador passa e é devolvido |
| `test_get_current_admin_com_usuario_comum` | usuário com `admin=False` | o usuário comum é barrado com **403** |

---

### 7.5 Estrutura final

```text
comprix/
├── src/
│   └── comprix/
│       ├── models/
│       ├── routers/
│       │   ├── auth.py
│       │   └── usuarios.py
│       ├── schemas/
│       ├── app.py
│       ├── database.py
│       ├── security.py
│       └── settings.py
└── tests/
    ├── conftest.py        👈 fixtures compartilhadas
    ├── test_security.py   👈 testes unitários (funções + banco em memória)
    ├── test_auth.py       👈 integração: login e refresh
    └── test_usuarios.py   👈 integração: rotas de usuários
```

Os testes de integração ficam nas páginas de cada rota:
[Auth](../routers/auth.md) e [Refresh Token](../routers/refresh.md) para o
login e a renovação do token, e a página de [Usuários](../routers/usuarios.md)
para as permissões de administrador.

### 🧭 Unitário x integração

| | Unitários (`test_security.py`) | Integração (`test_auth.py`, `test_usuarios.py`) |
|---|---|---|
| **O que testam** | As funções do `security.py` isoladas | O fluxo completo pela API |
| **Como chamam** | `create_access_token(...)`, `await get_current_user(...)` | `client.post(...)`, `client.get(...)` |
| **Quando falham** | Apontam **exatamente** qual função quebrou | Mostram que **algo** no fluxo do usuário quebrou |

Os dois tipos se complementam: os unitários localizam o erro, e os de
integração garantem que as peças funcionam **juntas**.

### ▶️ Rodando

```bash
poetry run pytest tests/test_security.py -v
```

Saída esperada:

```text
tests/test_security.py::test_hash_nao_e_a_senha_em_texto_puro PASSED
tests/test_security.py::test_hash_da_mesma_senha_muda_a_cada_requisicao PASSED
tests/test_security.py::test_verify_password_senha_correta PASSED
tests/test_security.py::test_verify_password_senha_errada PASSED
tests/test_security.py::test_token_contem_sub_e_exp PASSED
tests/test_security.py::test_token_expira_no_tempo_configurado PASSED
tests/test_security.py::test_usuario_comum_nao_recebe_is_admin PASSED
tests/test_security.py::test_admin_recebe_is_admin PASSED
tests/test_security.py::test_nao_altera_o_dicionario_original PASSED
tests/test_security.py::test_token_valido_retorna_o_usuario_do_banco PASSED
tests/test_security.py::test_token_malformado PASSED
tests/test_security.py::test_token_expirado PASSED
tests/test_security.py::test_token_assinado_com_outra_chave PASSED
tests/test_security.py::test_token_sem_sub PASSED
tests/test_security.py::test_token_de_email_que_nao_existe PASSED
tests/test_security.py::test_usuario_apagado_depois_do_login PASSED
tests/test_security.py::test_get_current_admin_com_usuario_admin PASSED
tests/test_security.py::test_get_current_admin_com_usuario_comum PASSED

============================== 18 passed ==============================
```

Todos os testes do projeto:

```bash
poetry run pytest -v
```

---

## ⏭️ 8. Próximos passos

- [x] Implementar a rota `auth/refresh`. Veja [Refresh Token](../routers/refresh.md).
- [x] Usar a coluna `admin` da tabela `usuarios` para as permissões, com o
      `get_current_admin`.
- [x] Medir a cobertura dos testes (o `--cov=comprix` já está no `addopts`
      do `pyproject.toml`).
- [ ] Proteger as rotas de **alterar** e **excluir** usuários com
      `CurrentUserAdmin`.
- [ ] Decidir se a claim `is_admin` continua no token (uso no frontend) ou se
      será removida.
- [ ] Recusar usuários com `status=False` (inativos) no `get_current_user`.
