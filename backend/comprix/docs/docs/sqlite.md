---
icon: lucide/database-zap
title: Configuranco o banco de dados
---

# :lucide-database-zap: Configurando o banco de dados

Agora que já sabemos o que é um banco de dados e por que escolhemos o SQLite, vamos colocá-lo para funcionar no Comprix. Para isso, vamos usar algumas peças que trabalham juntas:

| Ferramenta | Papel no projeto |
|---|---|
| **SQLite** | O banco de dados em si: um único arquivo `.db` onde os dados ficam guardados |
| **SQLAlchemy** | Conecta no banco e permite criar tabelas e consultar dados usando classes Python |
| **aiosqlite** | Permite que o SQLAlchemy converse com o SQLite de forma **assíncrona** |
| **pydantic-settings** | Lê e valida as configurações do projeto, como o endereço do banco |

O SQLite já vem com o Python, então só precisamos instalar as outras três.

??? info "Por que assíncrono?"
    O FastAPI foi feito para trabalhar de forma **assíncrona**: enquanto uma requisição espera uma resposta do banco, a API pode atender outras requisições, em vez de ficar parada. Para aproveitar isso, a conexão com o banco também precisa ser assíncrona. É por isso que usamos o `asyncio` do SQLAlchemy e o driver `aiosqlite`.

## Instalando as dependências

No terminal, dentro da pasta do projeto, rode:

```console title="Terminal"
$ poetry add 'sqlalchemy[asyncio]' aiosqlite pydantic-settings
```

O Poetry baixa as bibliotecas, adiciona todas no `pyproject.toml` e atualiza o `poetry.lock`.

!!! warning "Não esqueça o `[asyncio]`"
    O `[asyncio]` instala junto uma biblioteca chamada **greenlet**, que o SQLAlchemy precisa para funcionar no modo assíncrono. Sem ela, a API para ao iniciar com o erro *"The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed"*. As aspas no comando evitam que o terminal interprete os colchetes.

## Guardando as configurações no `.env`

O endereço do banco é uma **configuração**, e configurações não devem ficar escritas direto no código. Se um dia quisermos usar outro banco, basta trocar a configuração, sem mexer em nenhuma linha de Python.

Crie um arquivo chamado `.env` na raiz do projeto, na mesma pasta do `pyproject.toml`:

```bash title=".env"
DATABASE_URL="sqlite+aiosqlite:///comprix.db"
```

Esse endereço tem três partes:

- **`sqlite`**: o banco de dados que vamos usar.
- **`+aiosqlite`**: o driver que faz a conexão de forma assíncrona.
- **`comprix.db`**: o nome do arquivo onde os dados ficam guardados, criado na pasta onde a API é executada.

!!! danger "O `.env` não vai para o Git"
    O `.env` pode guardar senhas e chaves secretas no futuro. Por isso, ele **nunca** deve ser enviado para o GitHub. O mesmo vale para o arquivo do banco, que guarda os dados. Adicione estas linhas ao `.gitignore`:

    ```
    .env
    *.db
    ```

Como o `.env` não vai para o GitHub, quem baixar o projeto não saberá quais configurações ele precisa ter. Para resolver isso, criamos também um arquivo de exemplo, sem nenhum dado secreto, que **vai** para o GitHub:

```bash title=".env.example"
DATABASE_URL="sqlite+aiosqlite:///comprix.db"
```

Quem baixar o projeto só precisa copiá-lo:

```console title="Terminal"
$ cp .env.example .env
```

## Lendo as configurações com o pydantic-settings

Agora vamos criar a classe que lê o `.env`:

```python title="src/comprix/settings.py" linenums="1"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str
```

- **Linha 1:** importamos a classe `BaseSettings`, que funciona como o `BaseModel` dos schemas, mas lê os dados do ambiente, e a `SettingsConfigDict`, que configura de onde ler.

- **Linhas 5 a 7:** dizemos que as configurações vêm do arquivo `.env`, com codificação UTF-8.

- **Linha 9:** declaramos a configuração `DATABASE_URL`, do tipo texto. Como ela não tem valor padrão, é **obrigatória**: se ela não existir no `.env`, a aplicação para logo ao iniciar, com uma mensagem clara de erro.

??? info "Por que o editor sublinha o `Settings()`?"
    Em alguns editores, o `Settings()` aparece sublinhado com o aviso de que falta o argumento `DATABASE_URL`. Isso acontece porque o editor não sabe que o valor virá do `.env`. O código funciona normalmente.

## Criando as tabelas com o SQLAlchemy

No SQLAlchemy, cada tabela do banco é representada por uma classe Python, chamada de **model**. Para manter o projeto organizado, vamos criar um diretório chamado **models**, onde ficarão todos os models da nossa aplicação:

``` title="Estrutura do projeto" hl_lines="3-6"
src
└── comprix
    ├── models
    │   ├── __init__.py
    │   ├── base.py
    │   └── usuarios.py
    ├── schemas
    │   └── app.py
    ├── static
    │   └── comprix-icon.ico
    ├── __init__.py
    └── app.py
```

!!! warning "Model não é schema"
    O **schema** (Pydantic) define o formato dos dados que **entram e saem da API**. O **model** (SQLAlchemy) define como os dados são **guardados no banco**. Os dois se parecem, mas têm papéis diferentes, e por isso ficam em pastas separadas.

## A base dos nossos models

Todos os models do Comprix vão compartilhar algumas coisas em comum: a classe `Base`, que o SQLAlchemy usa para conhecer as tabelas, e as colunas de data de criação e de atualização. Para não repetir esse código em cada model, vamos reuni-lo no arquivo `base.py`.

```python title="src/comprix/models/base.py" linenums="1"
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from sqlalchemy.orm import DeclarativeBase, mapped_column

TIME = ZoneInfo('America/Sao_Paulo')


def time_zone() -> datetime:
    return datetime.now(TIME)


criado = Annotated[datetime, mapped_column(default=time_zone)]
atualizado = Annotated[
    datetime, mapped_column(default=time_zone, onupdate=time_zone)
]


class Base(DeclarativeBase):
    pass
```

### Os imports

- **Linha 1:** o `datetime` representa uma data com hora.
- **Linha 2:** o `Annotated` permite juntar um tipo com informações extras. Vamos usá-lo para criar tipos de coluna reutilizáveis.
- **Linha 3:** o `ZoneInfo` dá acesso aos fusos horários. Ele já vem com o Python, sem precisar instalar nada.
- **Linha 5:** do SQLAlchemy, importamos o `DeclarativeBase`, a base dos models, e o `mapped_column`, que configura as colunas.

### O fuso horário

```python linenums="7"
TIME = ZoneInfo('America/Sao_Paulo')


def time_zone() -> datetime:
    return datetime.now(TIME)
```

- **Linha 7:** guardamos o fuso horário de São Paulo na constante `TIME`.
- **Linhas 10 e 11:** a função `time_zone` devolve a data e a hora atuais nesse fuso.

!!! warning "Atenção ao nome do fuso"
    O nome correto é `America/Sao_Paulo`, **sem o "n"** no final de America. Com um nome errado, o Python para ao iniciar com o erro `ZoneInfoNotFoundError`.

??? info "Por que não usar o horário do banco?"
    O SQLite registra a data e a hora sempre no horário **UTC**, que fica 3 horas à frente de Brasília. Gerando a data no Python, garantimos que ela seja gravada no horário de São Paulo.

### Colunas reutilizáveis

```python linenums="14"
criado = Annotated[datetime, mapped_column(default=time_zone)]
atualizado = Annotated[
    datetime, mapped_column(default=time_zone, onupdate=time_zone)
]
```

Aqui criamos dois **tipos de coluna** que qualquer model pode usar:

- **`criado`** (linha 14): uma coluna de data cujo valor padrão (`default`) é o momento em que o registro é criado.
- **`atualizado`** (linhas 15 a 17): além do valor padrão, o `onupdate` faz essa data ser **atualizada automaticamente** sempre que o registro for alterado.

!!! warning "Sem parênteses em `time_zone`"
    Repare que escrevemos `default=time_zone`, e **não** `default=time_zone()`. Assim, passamos a função em si, e o SQLAlchemy a chama no momento de gravar cada registro. Com os parênteses, a função rodaria uma única vez, quando o servidor iniciasse, e todos os registros ficariam com a mesma data e hora.

Com isso, nos models, basta escrever:

```python
created_at: Mapped[criado]
updated_at: Mapped[atualizado]
```

### A classe `Base`

```python linenums="20"
class Base(DeclarativeBase):
    pass
```

A classe `Base` herda do `DeclarativeBase` do SQLAlchemy e serve como ponto de partida para todos os models. Ela fica vazia (`pass`) porque toda a funcionalidade vem do `DeclarativeBase`. Quando um model herda de `Base`, o SQLAlchemy passa a conhecer a tabela dele, e é assim que ele sabe quais tabelas criar.

## O model de usuários

Agora vamos criar o nosso primeiro model: a tabela que vai guardar os usuários do Comprix.

```python title="src/comprix/models/usuarios.py" linenums="1"
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from comprix.models.base import Base, atualizado, criado


class Usuarios(Base):
    __tablename__ = 'usuarios'
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[criado]
    updated_at: Mapped[atualizado]
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    senha: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[str] = mapped_column(String(6), nullable=False)
    primeiro_acesso: Mapped[bool] = mapped_column(default=True)
    status: Mapped[bool] = mapped_column(default=True)
```

### Os imports

- **Linha 1:** o `String` define colunas de texto com tamanho máximo.
- **Linha 2:** o `Mapped` indica o tipo de cada coluna, e o `mapped_column` permite configurá-la.
- **Linha 4:** do nosso `base.py`, importamos a classe `Base` e os tipos de coluna `criado` e `atualizado`, que já criamos.

### A classe e a tabela

- **Linha 7:** a classe `Usuarios` herda de `Base`. É isso que faz o SQLAlchemy reconhecê-la como uma tabela.
- **Linha 8:** o `__tablename__` define o nome da tabela no banco de dados.

### As colunas

| Linha | Coluna | Tipo | O que guarda |
|---|---|---|---|
| 9 | `id` | número inteiro | Identificador único de cada usuário |
| 10 | `created_at` | data e hora | Quando o usuário foi criado |
| 11 | `updated_at` | data e hora | Quando o usuário foi alterado pela última vez |
| 12 | `nome` | texto (até 50) | O nome do usuário |
| 13 a 15 | `email` | texto (até 100) | O e-mail, que não pode se repetir |
| 16 | `senha` | texto (até 100) | A senha, guardada de forma protegida |
| 17 | `codigo` | texto (até 6) | Um código de 6 caracteres |
| 18 | `primeiro_acesso` | verdadeiro ou falso | Se o usuário ainda precisa trocar a senha inicial |
| 19 | `status` | verdadeiro ou falso | Se o usuário está ativo |

Vamos entender as configurações usadas:

- **`primary_key=True`** (linha 9): transforma o `id` na **chave primária** da tabela. Por ser um número inteiro, o banco gera o valor automaticamente: o primeiro usuário recebe `1`, o segundo `2`, e assim por diante.

- **`Mapped[criado]` e `Mapped[atualizado]`** (linhas 10 e 11): usam os tipos que criamos no `base.py`. As datas são preenchidas e atualizadas sozinhas, no horário de São Paulo.

- **`String(50)`, `String(100)` e `String(6)`:** definem o **tamanho máximo** de cada texto.

- **`nullable=False`:** indica que o campo é **obrigatório**. O banco não aceita um usuário sem nome, e-mail, senha ou código.

- **`unique=True`** (linha 14): impede que dois usuários sejam cadastrados com o **mesmo e-mail**.

- **`default=True`** (linhas 18 e 19): todo usuário novo começa com o **primeiro acesso pendente** e **ativo**, sem precisar informar esses valores.

??? info "O `nullable=False` é necessário?"
    No SQLAlchemy 2.0, o `Mapped[str]` já indica que a coluna é obrigatória. Para um campo opcional, escreveríamos `Mapped[str | None]`. Mesmo assim, mantivemos o `nullable=False` para deixar a regra **explícita** para quem lê o código.

### O primeiro acesso

O campo `primeiro_acesso` é uma medida de **segurança**. Quando um usuário é cadastrado, ele recebe uma senha inicial, que pode ter sido criada ou vista por outra pessoa. Por isso, o sistema deve obrigá-lo a criar a sua própria senha logo ao entrar.

O funcionamento é simples:

1. Todo usuário novo é criado com `primeiro_acesso = True`.
2. Ao fazer login, o sistema verifica esse campo. Se ele for `True`, o usuário é levado direto para a tela de troca de senha e não consegue usar o restante do sistema.
3. Depois que o usuário cadastra a nova senha, o campo passa a ser `False`, e o acesso ao sistema é liberado.

!!! tip "A regra fica na API"
    O model só **guarda** a informação. Quem vai **aplicar** a regra, bloqueando as outras rotas enquanto a senha não for trocada, são as rotas de autenticação que vamos criar mais adiante.

!!! danger "Nunca guarde a senha como ela foi digitada"
    A coluna `senha` não vai guardar a senha original, e sim um **hash**: uma versão embaralhada que não pode ser revertida. Assim, mesmo que alguém tenha acesso ao banco, não consegue descobrir a senha dos usuários. Vamos ver como fazer isso mais adiante.

### Criando um usuário

Com o model pronto, criar um usuário é como criar qualquer objeto Python. Não precisamos informar o `id`, as datas, o `primeiro_acesso` nem o `status`, porque eles são preenchidos automaticamente:

```python
usuario = Usuarios(
    nome='Admin',
    email='admin@comprix.com',
    senha='hash-da-senha',
    codigo='123456',
)
```

## Organizando os models com o `__init__.py`

Dentro da pasta `models`, o arquivo `__init__.py` tem um papel especial: ele é executado automaticamente sempre que alguma parte do projeto importa algo de `comprix.models`. Vamos usá-lo para reunir todos os nossos models em um só lugar.

```python title="src/comprix/models/__init__.py" linenums="1"
from comprix.models.base import Base
from comprix.models.usuarios import Usuarios

__all__ = ['Base', 'Usuarios']
```

- **Linha 1:** importamos a classe `Base`, que fica no arquivo `base.py`.

- **Linha 2:** importamos o model `Usuarios`, que fica no arquivo `usuarios.py`.

- **Linha 4:** a lista `__all__` declara quais nomes o pacote `models` oferece para o resto do projeto.

### Por que importar os models aqui?

Esses imports têm dois objetivos.

O primeiro é criar um **atalho**. Em vez de cada parte do projeto precisar saber em qual arquivo cada classe está, basta escrever:

```python
from comprix.models import Base, Usuarios
```

O segundo, e mais importante, é **registrar os models**. O comando `Base.metadata.create_all()`, que cria as tabelas no banco, só conhece os models que **já foram carregados** pelo Python. Como o `__init__.py` sempre roda quando importamos algo de `comprix.models`, temos a garantia de que todos os models estarão carregados antes de as tabelas serem criadas.

!!! danger "Cuidado"
    Se um model não for importado no `__init__.py`, o `create_all` simplesmente **não cria a tabela dele**, e não mostra nenhum erro. Por isso, todo model novo precisa ser adicionado aqui.

### E para que serve o `__all__`?

O `__all__` é uma lista com os nomes que o pacote torna públicos. No nosso projeto, ele também evita um aviso do **ruff**: como o `__init__.py` importa as classes mas não as usa diretamente, o ruff entenderia esses imports como esquecidos (regra F401). Com o `__all__`, deixamos claro que eles são intencionais.

??? info "Por que a `Base` fica em um arquivo separado?"
    Poderíamos escrever a classe `Base` direto no `__init__.py`. Mas o `usuarios.py` precisa importar a `Base`, e o `__init__.py` precisa importar o `usuarios.py`. Com os dois no mesmo arquivo, um dependeria do outro, causando um **erro de importação circular**. Separando a `Base` no `base.py`, cada arquivo depende só do que realmente precisa.

!!! warning "Os nomes precisam combinar"
    O nome importado no `__init__.py` precisa ser **exatamente** o nome da classe no `usuarios.py`, incluindo maiúsculas, minúsculas e plural. Se a classe se chama `Usuarios` e o `__init__.py` importa `Usuario`, o Python para com um `ImportError`.

### Adicionando novos models

Sempre que criarmos um model novo, como um `produtos.py`, basta acrescentar o import dele e o nome dele no `__all__`:

```python title="src/comprix/models/__init__.py" linenums="1" hl_lines="3 5"
from comprix.models.base import Base
from comprix.models.usuarios import Usuarios
from comprix.models.produtos import Produtos

__all__ = ['Base', 'Produtos', 'Usuarios']
```

## Conectando no banco

Com os models prontos, vamos criar a conexão com o banco. O arquivo `database.py` reúne tudo o que é de banco de dados: a conexão, a criação das tabelas e as sessões.

```python title="src/comprix/database.py" linenums="1"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from comprix.models import Base
from comprix.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL, echo=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


async def get_session():  # pragma: no cover
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except Exception:
            if session.is_active:
                await session.rollback()
            raise
```

### O engine

- **Linha 9:** o `engine` é o "motor" de conexão com o banco. Ele é criado a partir do endereço que está no `.env`. O `echo=False` desliga a exibição dos comandos SQL no terminal. Se quiser ver o SQL que o SQLAlchemy gera, troque para `echo=True`.

!!! info "Criar o engine não cria o banco"
    O `create_async_engine` só **prepara** a conexão. O arquivo `comprix.db` só é criado quando acontece a primeira conexão de verdade, e as tabelas só são criadas pelo `create_all`.

### Criando as tabelas automaticamente: o `lifespan`

- **Linhas 12 e 13:** o `lifespan` é uma função que o FastAPI executa quando a API **liga** e quando ela **desliga**.

- **Linhas 14 e 15:** quando a API liga, abrimos uma conexão e pedimos para o SQLAlchemy criar todas as tabelas que ainda não existem. O `run_sync` é necessário porque o `create_all` não é assíncrono, e ele faz a ponte entre os dois mundos.

- **Linha 16:** o `yield` separa os dois momentos. Tudo o que vem antes roda quando a API liga, e tudo o que vem depois roda quando ela desliga.

- **Linha 17:** quando a API desliga, o `dispose` fecha todas as conexões com o banco.

Com isso, quem baixar o projeto do GitHub não precisa criar o banco manualmente: ele é criado sozinho na primeira vez que a API for executada.

!!! warning "O `create_all` só cria, não altera"
    Se uma tabela já existe, o `create_all` **não mexe nela**. Ou seja, se adicionarmos uma coluna nova em um model, ela não será criada no banco. Durante o desenvolvimento, podemos apagar o arquivo `comprix.db` e deixar a API criá-lo de novo. Quando o projeto tiver dados reais, vamos usar o **Alembic**, uma ferramenta feita para alterar tabelas sem perder os dados.

### A sessão

- **Linhas 20 e 21:** a função `get_session` abre uma **sessão**, que é por onde fazemos as operações no banco: salvar, buscar, alterar e apagar. O `async with` garante que a sessão seja fechada automaticamente quando a operação terminar.

- **Linha 21:** o `expire_on_commit=False` mantém os dados dos objetos disponíveis depois de salvá-los. Sem ele, depois de um `commit`, acessar um campo como `usuario.id` exigiria uma nova consulta ao banco, o que não funciona bem no modo assíncrono.

- **Linhas 22 a 27:** se acontecer algum erro durante a operação, o `rollback` desfaz tudo o que foi feito naquela sessão, para o banco não ficar com dados pela metade. Depois, o `raise` deixa o erro seguir adiante, para que ele apareça.

- **Linha 20:** o comentário `# pragma: no cover` avisa à ferramenta de cobertura de testes para ignorar essa função. Ela vai ser usada nas rotas, que vamos testar de outra forma.

## Ligando o banco na API

Agora só falta avisar o FastAPI para usar o `lifespan`:

```python title="src/comprix/app.py" linenums="1" hl_lines="7 10"
from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from comprix.database import lifespan
from comprix.schemas.app import Message

app = FastAPI(lifespan=lifespan)

FAVICON = Path(__file__).parent / 'static' / 'comprix-icon.ico'


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    return FileResponse(FAVICON)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Bem-vindo ao Comprix'}
```

- **Linha 7:** importamos o `lifespan` do `database.py`.
- **Linha 10:** com o `lifespan=lifespan`, o FastAPI passa a executar essa função quando a API liga e desliga.

Agora, rode a API:

```console title="Terminal"
$ poetry serve
```

Ao iniciar, a API cria o arquivo `comprix.db` com a tabela `usuarios`. Para conferir, instale o terminal do SQLite e consulte o banco:

```console title="Terminal"
$ sudo apt install -y sqlite3
$ sqlite3 comprix.db ".schema usuarios"
```

O resultado mostra a estrutura da tabela, com todas as colunas que definimos no model:

```sql
CREATE TABLE usuarios (
    id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    nome VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    senha VARCHAR(100) NOT NULL,
    codigo VARCHAR(6) NOT NULL,
    primeiro_acesso BOOLEAN NOT NULL,
    status BOOLEAN NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (email)
)
```

!!! tip "Visualizando o banco no VS Code"
    Se preferir ver os dados em forma de tabela, instale uma extensão como a **SQLite Viewer** no VS Code e clique no arquivo `comprix.db`.

## Testando o banco

Por fim, vamos garantir que tudo funciona com um teste. Como o banco é assíncrono, os testes também precisam ser. Para isso, instalamos o **pytest-asyncio** como dependência de desenvolvimento:

```console title="Terminal"
$ poetry add --group dev pytest-asyncio
```

Nos testes, usamos um banco **em memória** (`sqlite+aiosqlite:///:memory:`): ele é criado do zero a cada teste e desaparece ao final, sem tocar no `comprix.db`.

### As fixtures

Primeiro, criamos as **fixtures**: funções que preparam o que os testes precisam e que eles recebem como parâmetro. Vamos ter duas: uma que liga a API e outra que entrega uma sessão do banco.

```python title="tests/conftest.py" linenums="1"
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from comprix.app import app
from comprix.models import Base


@pytest.fixture
def client(monkeypatch):
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    monkeypatch.setattr('comprix.database.engine', engine)

    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    await engine.dispose()
```

#### A fixture `client`

- **Linha 12:** criamos um engine que aponta para um banco em memória.
- **Linha 13:** o `monkeypatch.setattr` troca, **só durante o teste**, o `engine` do `database.py` por esse engine em memória. Assim, os testes nunca criam nem alteram o `comprix.db` de verdade. Ao final do teste, o `monkeypatch` desfaz a troca sozinho.
- **Linhas 15 e 16:** ligamos a API com o `TestClient` e a entregamos ao teste com o `yield`.

!!! warning "O `with` é obrigatório"
    O `TestClient` só executa o `lifespan` quando é usado com `with`. Sem ele, a API responde normalmente, mas as tabelas não são criadas, e o código do `lifespan` nunca é testado.

#### A fixture `session`

- **Linha 19:** o `@pytest_asyncio.fixture` transforma a função em uma fixture assíncrona.
- **Linhas 21 a 24:** criamos o banco em memória e as tabelas, do mesmo jeito que o `lifespan` faz.
- **Linhas 26 e 27:** abrimos uma sessão e a entregamos ao teste com o `yield`.
- **Linha 29:** depois do teste, fechamos as conexões, e o banco em memória desaparece.

### Testando a API

Com a fixture `client`, os testes da API ficam simples. Além da rota principal, testamos também a rota do favicon:

```python title="tests/test_app.py" linenums="1"
from http import HTTPStatus


def test_root_deve_retornar_ok_e_mensagem(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Bem-vindo ao Comprix'}


def test_favicon_deve_retornar_o_icone(client):
    response = client.get('/favicon.ico')

    assert response.status_code == HTTPStatus.OK
    assert response.headers['content-type'] == 'image/vnd.microsoft.icon'
```

- **Linhas 4 a 8:** a rota `/` deve responder com o código **200** e a mensagem de boas-vindas.
- **Linhas 11 a 15:** a rota `/favicon.ico` deve responder com o código **200** e com o tipo de arquivo de um ícone (`image/vnd.microsoft.icon`).

Repare que os testes recebem `client` como parâmetro: o pytest encontra a fixture com esse nome no `conftest.py` e a entrega automaticamente.

### Testando o banco

E então o teste do banco de dados:

```python title="tests/test_db.py" linenums="1"
import pytest
from sqlalchemy import select

from comprix.models import Usuarios


@pytest.mark.asyncio
async def test_criar_usuario(session):
    usuario = Usuarios(
        nome='Admin',
        email='admin@comprix.com',
        senha='hash-da-senha',
        codigo='123456',
    )

    session.add(usuario)
    await session.commit()

    resultado = await session.scalar(
        select(Usuarios).where(Usuarios.email == 'paulo@email.com')
    )

    assert resultado.id == 1
    assert resultado.primeiro_acesso is True
    assert resultado.status is True
```

- **Linha 7:** o `@pytest.mark.asyncio` avisa ao pytest que o teste é assíncrono.
- **Linhas 9 a 14:** criamos um usuário informando só os campos obrigatórios.
- **Linhas 16 e 17:** adicionamos o usuário na sessão e confirmamos a gravação com o `commit`.
- **Linhas 19 a 21:** buscamos no banco o usuário com aquele e-mail.
- **Linhas 23 a 25:** verificamos que o banco gerou o `id` e que o `primeiro_acesso` e o `status` receberam os valores padrão.

### Configurando a cobertura de testes

O nosso `poetry test` mede a **cobertura**: quantas linhas do código foram executadas pelos testes. Mas há um detalhe: no modo assíncrono, o SQLAlchemy executa parte do trabalho dentro de um **greenlet**, e a ferramenta de cobertura não acompanha esse caminho por padrão. Sem uma configuração extra, a linha do `create_all` aparece como não testada, mesmo sendo executada.

Para resolver, acrescente no `pyproject.toml`:

```toml title="pyproject.toml"
[tool.coverage.run]
concurrency = ['thread', 'greenlet']
core = 'ctrace'
```

- **`concurrency`:** avisa ao coverage que o código usa **threads** (o `TestClient` roda a API em uma thread separada) e **greenlets** (usados pelo SQLAlchemy assíncrono).
- **`core = 'ctrace'`:** a partir do Python 3.14, o coverage usa por padrão um modo de rastreamento que não suporta o `--cov-context=test` do nosso projeto, e mostra um aviso a cada execução. Com essa linha, ele volta ao modo tradicional.

Com tudo configurado, vamos ver o resultado no final desta página.

## Estrutura do projeto

Ao final desta etapa, o projeto fica assim:

Observe que agora temos nosso banco de dados **comprix.db**, você pode abri-lo através de ferramentas gratuitas no mercado como DBeaver, TablePlus, Beekeeper Studio, entre outros.

``` title="Estrutura do projeto" hl_lines="1 2 3 7-10 15 16 20 21"
├── .env
├── .env.example
├── comprix.db
├── pyproject.toml
├── src
│   └── comprix
│       ├── models
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── usuarios.py
│       ├── schemas
│       │   └── app.py
│       ├── static
│       │   └── comprix-icon.ico
│       ├── database.py
│       ├── settings.py
│       ├── __init__.py
│       └── app.py
└── tests
    ├── conftest.py
    ├── test_db.py
    └── test_app.py
```

## Rodando os testes

Com o projeto completo, rode os testes:

```console title="Terminal"
$ poetry test
```

O `poetry test` executa três etapas em sequência: o **ruff**, para verificar o código, o **pytest**, para rodar os testes e medir a cobertura, e o **coverage**, para gerar o relatório em HTML. O resultado deve ser parecido com este:

```console title="Terminal"
Poe => ruff check
All checks passed!
Poe => pytest -s -x -vv
============================= test session starts ==============================
collected 3 items

tests/test_app.py::test_root_deve_retornar_ok_e_mensagem PASSED
tests/test_app.py::test_favicon_deve_retornar_o_icone PASSED
tests/test_db.py::test_criar_usuario PASSED

================================ tests coverage ================================

Name                             Stmts   Miss  Cover
----------------------------------------------------
src/comprix/__init__.py              0      0   100%
src/comprix/app.py                  14      0   100%
src/comprix/database.py             12      0   100%
src/comprix/models/__init__.py       3      0   100%
src/comprix/models/base.py          11      0   100%
src/comprix/models/usuarios.py      12      0   100%
src/comprix/schemas/app.py           2      0   100%
src/comprix/settings.py              4      0   100%
----------------------------------------------------
TOTAL                               58      0   100%
============================== 3 passed in 0.51s ===============================
Poe => coverage html --show-contexts
Wrote HTML report to htmlcov/index.html
```

Vamos entender o que o relatório mostra:

| Coluna | Significado |
|---|---|
| **Name** | O arquivo analisado |
| **Stmts** | Quantas instruções o arquivo tem |
| **Miss** | Quantas instruções **não** foram executadas pelos testes |
| **Cover** | A porcentagem do arquivo coberta pelos testes |

Os três testes passaram (**PASSED**), e todos os arquivos estão com **100%** de cobertura: cada linha do nosso código foi executada por pelo menos um teste.

## O relatório em HTML

A última linha do resultado mostra que o coverage também gerou um relatório em HTML, na pasta `htmlcov`. Ele mostra as mesmas informações do terminal, mas de forma visual: dá para clicar em cada arquivo e ver o código com as linhas coloridas.

- :material-square:{ style="color: #2fb985" } **Verde:** linha executada pelos testes.
- :material-square:{ style="color: #d93025" } **Vermelho:** linha que nenhum teste executou.

Para abrir o relatório no navegador do Windows direto pelo terminal do WSL, rode:

=== "Google Chrome"

    ```console title="Terminal"
    $ "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe" "$(wslpath -w htmlcov/index.html)"
    ```

=== "Firefox"

    ```console title="Terminal"
    $ "/mnt/c/Program Files/Mozilla Firefox/firefox.exe" "$(wslpath -w htmlcov/index.html)"
    ```

=== "Microsoft Edge"

    ```console title="Terminal"
    $ "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" "$(wslpath -w htmlcov/index.html)"
    ```

=== "Navegador padrão"

    ```console title="Terminal"
    $ explorer.exe "$(wslpath -w htmlcov/index.html)"
    ```

Os comandos têm duas partes:

- **O caminho do navegador:** o WSL enxerga o disco `C:` do Windows na pasta `/mnt/c`, então conseguimos executar o navegador instalado no Windows.
- **O `wslpath -w`:** converte o caminho do arquivo do formato do Linux para o formato do Windows, que é o que o navegador entende.

??? info "O navegador não abriu?"
    O caminho de instalação pode variar de um computador para outro. Se aparecer *"No such file or directory"*, procure onde o navegador está instalado, por exemplo com `ls "/mnt/c/Program Files/"`, e ajuste o caminho do comando.

    Se você usa **Linux** sem o WSL, use `xdg-open htmlcov/index.html`. No **macOS**, use `open htmlcov/index.html`.

??? info "Para que serve o `--show-contexts`?"
    No nosso `pyproject.toml`, o pytest roda com a opção `--cov-context=test`, que registra **qual teste** executou cada linha. O `--show-contexts` leva essa informação para o relatório HTML: ao lado de cada linha verde, aparece a lista dos testes que passaram por ela. Isso ajuda muito a entender quais testes protegem cada parte do código.

!!! warning "O relatório não vai para o Git"
    A pasta `htmlcov` e o arquivo `.coverage` são gerados de novo a cada execução dos testes, então não precisam ir para o GitHub. Adicione estas linhas ao `.gitignore`:

    ```
    htmlcov/
    .coverage
    ```

## :material-party-popper: Parabéns!

!!! success "O Comprix agora tem um banco de dados!"
    Chegamos ao fim de uma etapa importante. Nesta seção, você:

    - :material-check-circle: instalou o **SQLAlchemy**, o **aiosqlite** e o **pydantic-settings**;
    - :material-check-circle: guardou as configurações com segurança no `.env`;
    - :material-check-circle: criou a **base dos models**, com datas no horário de São Paulo;
    - :material-check-circle: criou o primeiro model, a tabela de **usuários**;
    - :material-check-circle: conectou a API ao banco, que agora é **criado automaticamente** quando ela liga;
    - :material-check-circle: escreveu **testes** para a API e para o banco, com **100% de cobertura**.

    Com essa base pronta, o próximo passo é criar as **rotas de usuários**, para cadastrar, consultar, alterar e remover usuários pela API.
