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
return encode(
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

#### 2️⃣ Preparando o erro padrão

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

#### 3️⃣ Decodificando e validando

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

> 🛡️ O `algorithms=[...]` é **obrigatório por segurança**. Ele impede que um
> atacante monte um token dizendo "use o algoritmo `none`" (sem assinatura)
> e engane o servidor.

Se tudo estiver certo, `payload` é o dicionário original:
`{'sub': '...', 'exp': ..., 'is_admin': True}`.

#### 4️⃣ Identificando o dono do token

```python
    subject_email = payload.get('sub')
    if not subject_email:
        raise credentials_exception
```

Pega o e-mail da claim `sub`. Um token **sem dono** não serve para nada,
então é recusado.

#### 5️⃣ Conferindo no banco

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

#### 6️⃣ Entregando o usuário

```python
    return usuario
```

A rota recebe o objeto `Usuarios` completo, pronto para uso:

```python
@router.get('/me')
async def me(usuario: Usuarios = Depends(get_current_user)):
    return usuario
```

### 🔄 Resumo do fluxo

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

## 📄 5. O módulo `security.py` completo

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

    return encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
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

### 🐞 O que mudou em relação à versão anterior

| Antes | Depois | Por quê |
|---|---|---|
| `data.username` | `to_encode.get('sub')` | `data` é um dicionário; a linha antiga lançava `AttributeError` em todo login. |
| `except DecodeError` + `except ExpiredSignatureError` | `except InvalidTokenError` | Um único `except` cobre **todos** os erros de token. |
| Sem tipo de retorno | `-> str`, `-> bool`, `-> Usuarios` | Ajuda o editor, o autocompletar e o mypy. |

---

## 🔗 6. Usando no sistema

### Rota de login (`auth/token`)

```python
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from comprix.database import get_session
from comprix.models import Usuarios
from comprix.security import create_access_token, verify_password

router = APIRouter(prefix='/auth', tags=['auth'])


@router.post('/token')
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    usuario = await session.scalar(
        select(Usuarios).where(Usuarios.email == form_data.username)
    )

    if not usuario or not verify_password(
        form_data.password, usuario.senha
    ):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='E-mail ou senha incorretos',
        )

    access_token = create_access_token(data={'sub': usuario.email})
    return {'access_token': access_token, 'token_type': 'bearer'}
```

> 📌 O `OAuth2PasswordRequestForm` usa o campo `username` por exigência do
> padrão OAuth2. No COMPRIX, enviamos o **e-mail** nele.

### Rota protegida

```python
from comprix.security import get_current_user


@router.get('/me')
async def me(usuario: Usuarios = Depends(get_current_user)):
    return usuario
```

Basta adicionar `Depends(get_current_user)` para exigir login em qualquer
rota. 🔒

---

## 🧪 7. Testes

### 📦 Dependências

```bash
pip install pytest pytest-asyncio
```

O `pytest-asyncio` permite testar funções `async`, como o
`get_current_user`. Os testes assíncronos são marcados com
`@pytest.mark.asyncio`.

### 🧭 Estratégia

São **testes unitários**: testamos as funções diretamente, **sem subir a API
e sem banco de dados real**. Isso os torna rápidos e focados.

- Para o **`create_access_token`**, geramos um token e o decodificamos para
  conferir o que está dentro.
- Para o **`get_current_user`**, trocamos o banco por uma **sessão falsa**
  e montamos tokens "defeituosos" na mão para simular ataques e erros.

### 📄 Arquivo `tests/test_token.py`

```python
from datetime import datetime, timedelta
from http import HTTPStatus
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from fastapi import HTTPException
from jwt import decode, encode

from comprix.security import (
    create_access_token,
    get_current_user,
    settings,
)

EMAIL = 'usuario@comprix.com'


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------
class FakeSession:
    """Imita a AsyncSession: o scalar() devolve o usuário informado."""

    def __init__(self, usuario):
        self.usuario = usuario

    async def scalar(self, stmt):
        return self.usuario


def fake_usuario(email=EMAIL):
    return SimpleNamespace(id=1, email=email)


def agora():
    return datetime.now(tz=ZoneInfo('UTC'))


def decodifica(token: str) -> dict:
    return decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )


def token_manual(payload: dict, chave: str | None = None) -> str:
    """Monta um token com qualquer payload, para simular ataques e erros."""
    return encode(
        payload,
        chave or settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


async def espera_401(token: str, usuario=None):
    session = FakeSession(usuario if usuario is not None else fake_usuario())

    with pytest.raises(HTTPException) as exc:
        await get_current_user(session=session, token=token)

    assert exc.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.value.headers == {'WWW-Authenticate': 'Bearer'}


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------
def test_token_contem_sub_e_exp():
    payload = decodifica(create_access_token({'sub': EMAIL}))

    assert payload['sub'] == EMAIL
    assert 'exp' in payload


def test_token_expira_no_tempo_configurado():
    inicio = agora().timestamp()
    payload = decodifica(create_access_token({'sub': EMAIL}))

    esperado = inicio + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert abs(payload['exp'] - esperado) < 5  # tolerância de 5 segundos


def test_usuario_comum_nao_recebe_is_admin():
    payload = decodifica(create_access_token({'sub': EMAIL}))
    assert 'is_admin' not in payload


def test_admin_recebe_is_admin():
    payload = decodifica(create_access_token({'sub': settings.ADMIN_EMAIL}))
    assert payload['is_admin'] is True


def test_nao_altera_o_dicionario_original():
    data = {'sub': EMAIL}
    create_access_token(data)
    assert data == {'sub': EMAIL}


# ---------------------------------------------------------------------------
# get_current_user: caminho feliz
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_token_valido_retorna_o_usuario():
    usuario = fake_usuario()
    token = create_access_token({'sub': usuario.email})

    resultado = await get_current_user(
        session=FakeSession(usuario), token=token
    )

    assert resultado is usuario


# ---------------------------------------------------------------------------
# get_current_user: casos de erro (todos devem retornar 401)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_token_malformado():
    await espera_401('isto-nao-e-um-jwt')


@pytest.mark.asyncio
async def test_token_expirado():
    token = token_manual({
        'sub': EMAIL,
        'exp': agora() - timedelta(minutes=1),
    })
    await espera_401(token)


@pytest.mark.asyncio
async def test_token_assinado_com_outra_chave():
    token = token_manual(
        {'sub': EMAIL, 'exp': agora() + timedelta(minutes=5)},
        chave='chave-de-um-atacante',
    )
    await espera_401(token)


@pytest.mark.asyncio
async def test_token_sem_sub():
    token = token_manual({'exp': agora() + timedelta(minutes=5)})
    await espera_401(token)


@pytest.mark.asyncio
async def test_usuario_apagado_depois_do_login():
    token = create_access_token({'sub': EMAIL})
    session = FakeSession(usuario=None)

    with pytest.raises(HTTPException) as exc:
        await get_current_user(session=session, token=token)

    assert exc.value.status_code == HTTPStatus.UNAUTHORIZED
```

---

### 🧰 7.1 Entendendo as funções auxiliares

#### `FakeSession`

```python
class FakeSession:
    def __init__(self, usuario):
        self.usuario = usuario

    async def scalar(self, stmt):
        return self.usuario
```

O `get_current_user` só usa **um** método da sessão: o `scalar`. Então
criamos uma classe que tem apenas esse método e que **sempre devolve o
usuário que passarmos**, ignorando a consulta.

- `FakeSession(fake_usuario())` simula "o usuário existe no banco";
- `FakeSession(None)` simula "o usuário não existe".

Isso é um **dublê de teste** (*test double*): testamos a lógica do token sem
depender de banco.

#### `fake_usuario`

```python
def fake_usuario(email=EMAIL):
    return SimpleNamespace(id=1, email=email)
```

O `SimpleNamespace` cria um objeto simples com os atributos que quisermos
(`usuario.id`, `usuario.email`). Serve como um "usuário de mentira", sem
precisar do model do SQLAlchemy.

#### `agora`

Atalho para a hora atual em UTC, a mesma referência usada pelo módulo.

#### `decodifica`

```python
def decodifica(token: str) -> dict:
    return decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
```

Abre o token gerado e devolve o payload, para conferirmos as claims.

#### `token_manual`

```python
def token_manual(payload: dict, chave: str | None = None) -> str:
```

O `create_access_token` sempre gera tokens **corretos**. Para testar os
**erros**, precisamos de tokens "defeituosos": vencidos, sem `sub` ou
assinados com outra chave. Esta função monta um token com **qualquer
payload** e, opcionalmente, **qualquer chave**.

#### `espera_401`

```python
async def espera_401(token: str, usuario=None):
    ...
    with pytest.raises(HTTPException) as exc:
        await get_current_user(session=session, token=token)

    assert exc.value.status_code == HTTPStatus.UNAUTHORIZED
    assert exc.value.headers == {'WWW-Authenticate': 'Bearer'}
```

Vários testes verificam a mesma coisa: "este token deve ser recusado". Em
vez de repetir o código, ele fica aqui:

- `pytest.raises(HTTPException)` diz ao pytest: "**espero** que este bloco
  lance `HTTPException`". Se não lançar, o teste **falha**.
- `as exc` guarda a exceção para inspecionarmos depois;
- conferimos se o status é **401** e se o cabeçalho `WWW-Authenticate` veio.

---

### 🎟️ 7.2 Testes do `create_access_token`

#### `test_token_contem_sub_e_exp`

Gera um token e o abre. Confere se o `sub` é o e-mail informado e se a
claim `exp` existe.
**Garante:** o token identifica o usuário e tem prazo de validade.

#### `test_token_expira_no_tempo_configurado`

```python
    inicio = agora().timestamp()
    ...
    esperado = inicio + settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert abs(payload['exp'] - esperado) < 5
```

Guarda o horário antes de gerar o token, calcula quando ele **deveria**
expirar (minutos × 60 = segundos) e compara com o `exp` real. A tolerância
de 5 segundos cobre o tempo de execução do próprio teste.
**Garante:** a validade respeita o valor do `.env`.

#### `test_usuario_comum_nao_recebe_is_admin`

Gera um token para um e-mail comum e confere que **não existe** a claim
`is_admin`.
**Garante:** um usuário comum não vira administrador por engano. É o
teste de segurança mais importante deste grupo.

#### `test_admin_recebe_is_admin`

Gera um token para o `ADMIN_EMAIL` e confere que `is_admin` é `True`.
**Garante:** o administrador é reconhecido.

#### `test_nao_altera_o_dicionario_original`

Passa um dicionário para a função e confere que ele continua **igual**
depois.
**Garante:** o `.copy()` está funcionando e a função não tem efeitos
colaterais.

---

### 🛡️ 7.3 Testes do `get_current_user`

#### ✅ `test_token_valido_retorna_o_usuario`

```python
    resultado = await get_current_user(
        session=FakeSession(usuario), token=token
    )
    assert resultado is usuario
```

Gera um token válido, chama a função com a sessão falsa e confere se ela
devolve **exatamente o mesmo objeto** (`is`).
**Garante:** o fluxo normal funciona.

> 💡 Repare que chamamos `get_current_user` passando `session` e `token`
> **diretamente**. Fora de uma rota, o `Depends` não é acionado, então nós
> mesmos fornecemos os valores.

#### ❌ `test_token_malformado`

Envia um texto qualquer (`'isto-nao-e-um-jwt'`) no lugar do token.
**Garante:** lixo no cabeçalho é recusado com 401, sem derrubar a API.

#### ❌ `test_token_expirado`

```python
    'exp': agora() - timedelta(minutes=1),
```

Monta um token que **venceu há 1 minuto**.
**Garante:** tokens vencidos não dão acesso.

#### ❌ `test_token_assinado_com_outra_chave`

```python
        chave='chave-de-um-atacante',
```

Simula um **atacante** que monta um token perfeito, com e-mail válido e
dentro da validade, mas sem conhecer a `SECRET_KEY` verdadeira.
**Garante:** tokens **forjados** são recusados. É o teste que prova que a
assinatura protege o sistema.

#### ❌ `test_token_sem_sub`

Monta um token válido e assinado corretamente, mas **sem a claim `sub`**.
**Garante:** um token sem dono não dá acesso.

#### ❌ `test_usuario_apagado_depois_do_login`

```python
    session = FakeSession(usuario=None)
```

O token é **totalmente válido**, mas a sessão falsa responde que o usuário
**não existe** no banco.
**Garante:** quem foi removido perde o acesso imediatamente, mesmo com um
token ainda dentro da validade.

---

### 📋 7.4 Resumo

| Teste | Garante que... |
|---|---|
| `test_token_contem_sub_e_exp` | o token identifica o usuário e tem validade |
| `test_token_expira_no_tempo_configurado` | a validade respeita o `.env` |
| `test_usuario_comum_nao_recebe_is_admin` | usuários comuns **não** viram admin |
| `test_admin_recebe_is_admin` | o e-mail de admin recebe a claim |
| `test_nao_altera_o_dicionario_original` | a função não tem efeitos colaterais |
| `test_token_valido_retorna_o_usuario` | o fluxo normal funciona |
| `test_token_malformado` | lixo no cabeçalho é recusado |
| `test_token_expirado` | token vencido é recusado |
| `test_token_assinado_com_outra_chave` | token **forjado** é recusado |
| `test_token_sem_sub` | token sem dono é recusado |
| `test_usuario_apagado_depois_do_login` | usuário removido perde o acesso |

### ▶️ Rodando

```bash
pytest tests/test_token.py -v
```

> 🐞 Rodado contra a versão antiga do `security.py`, o primeiro teste já
> falharia com `AttributeError: 'dict' object has no attribute 'username'`.
> É para isso que os testes existem: o erro aparece aqui, e não no primeiro
> login em produção.

---

## ⏭️ Próximos passos

- 🔄 Implementar a rota `auth/refresh` para renovar o token sem pedir a senha
  de novo.
- 👑 Trocar o `ADMIN_EMAIL` pela coluna de admin da tabela `usuarios`
  (migration `03`), para permitir mais de um administrador.
- 🌐 Criar testes de integração com o `AsyncClient` do `httpx`, cobrindo
  login → token → rota protegida.