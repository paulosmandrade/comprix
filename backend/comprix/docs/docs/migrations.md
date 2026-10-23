---
icon: material/source-branch
---

# :material-source-branch: Migrações (Alembic)

Até agora, as tabelas do Comprix são criadas pelo `create_all`, que roda toda vez que a API liga. Isso funciona bem no começo, mas tem uma limitação importante: ele só **cria** tabelas que ainda não existem. Ele **nunca altera** uma tabela que já está no banco.

## O problema

Imagine esta situação:

1. Criamos o model `Usuarios` e rodamos a API. O `create_all` cria a tabela `usuarios` no banco.
2. Cadastramos alguns usuários reais.
3. Depois, decidimos adicionar uma coluna nova, como `primeiro_acesso`, no model.

Ao rodar a API de novo, o `create_all` vê que a tabela `usuarios` já existe e **não faz nada**. A coluna nova não é criada no banco, e a aplicação passa a dar erro sempre que tenta usá-la.

Durante o desenvolvimento, dá para contornar isso apagando o arquivo `comprix.db` e deixando a API criar tudo de novo. Mas, com dados reais, apagar o banco significa **perder todos os dados**. Precisamos de uma forma de alterar a estrutura do banco sem perder o que já está guardado.

## O que são migrações?

Uma **migração** é um arquivo que descreve uma mudança na estrutura do banco de dados, como:

- criar uma tabela nova;
- adicionar, renomear ou remover uma coluna;
- criar um índice ou uma restrição, como o `unique` do e-mail.

Cada migração é aplicada **uma única vez**, e em ordem. Juntas, elas formam um **histórico de versões do banco**, parecido com o histórico de commits do Git: olhando a lista de migrações, sabemos exatamente como o banco chegou ao formato atual.

``` title="Histórico de migrações"
001 - cria a tabela usuarios
002 - adiciona a coluna primeiro_acesso
003 - cria a tabela produtos
```

Assim, qualquer pessoa que baixar o projeto pode reconstruir o banco do zero, aplicando as migrações em sequência. E um banco que já existe, com dados, recebe só as migrações que ainda faltam.

## O que é o Alembic?

O **Alembic** é a ferramenta de migrações feita pelos mesmos criadores do SQLAlchemy. Ele trabalha diretamente com os nossos models e faz três coisas principais:

- :material-check-circle:{ style="color: #2fb985" } **Gera as migrações automaticamente:** ele compara os models com o banco e escreve o arquivo de migração com as diferenças que encontrou.

- :material-check-circle:{ style="color: #2fb985" } **Aplica as migrações:** com um comando, ele leva o banco para a versão mais recente, executando só o que ainda não foi aplicado.

- :material-check-circle:{ style="color: #2fb985" } **Desfaz as migrações:** se uma mudança deu errado, ele consegue voltar o banco para a versão anterior.

Na prática, o dia a dia com o Alembic se resume a dois comandos:

```console title="Terminal"
$ alembic revision --autogenerate -m "adiciona primeiro_acesso"
$ alembic upgrade head
```

- O primeiro **gera** uma nova migração a partir das mudanças nos models. O texto depois do `-m` é uma descrição, como a mensagem de um commit.
- O segundo **aplica** no banco todas as migrações que ainda faltam. O `head` significa "a versão mais recente".

!!! warning "Sempre revise a migração gerada"
    O `--autogenerate` é muito útil, mas não é perfeito. Ele não consegue perceber, por exemplo, que uma coluna foi **renomeada**: para ele, parece que uma coluna foi apagada e outra foi criada, o que faria os dados daquela coluna serem **perdidos**. Por isso, sempre abra o arquivo gerado e confira as alterações antes de rodar o `alembic upgrade head`.

## Instalando e configurando o Alembic

Abaixo o comando para adicionar a biblioteca do alembic em nosso projeto.

```console title="Terminal"
$ poetry add alembic
```

Com o Alembic instalado no projeto, podemos começar a configuração. O comando de inicialização cria um diretório chamado ***migrations*** e um arquivo de configuração chamado `alembic.ini`:

```console title="Terminal"
$ poetry run alembic init migrations
```
## Estrutura do projeto

```
comprix/
├── migrations/           # Migrações do banco de dados (Alembic)
│   ├── versions/         # Arquivos de migração
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── src/
│   └── comprix/
│       ├── models/       # Modelos do banco de dados
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── usuarios.py
│       ├── schemas/      # Schemas de validação
│       │   └── app.py
│       ├── static/       # Arquivos estáticos
│       ├── __init__.py
│       ├── app.py        # Ponto de entrada da aplicação
│       ├── database.py   # Conexão com o banco de dados
│       └── settings.py   # Configurações da aplicação
├── tests/                # Testes automatizados
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_app.py
│   └── test_db.py
├── .env.example          # Modelo das variáveis de ambiente
└── alembic.ini           # Configuração do Alembic
```

## Diretório `migrations`

O diretório `migrations` é criado pelo comando `alembic init migrations`. Ele guarda tudo que o Alembic usa para versionar o banco de dados: cada mudança na estrutura das tabelas vira um arquivo de migração que pode ser aplicado (`upgrade`) ou desfeito (`downgrade`).

### `README`

Um arquivo de texto curto gerado automaticamente pelo Alembic. Ele só informa qual template foi usado na criação do diretório e não interfere no funcionamento das migrações.

### `script.py.mako`

É o **modelo** usado para gerar cada novo arquivo de migração. Sempre que rodamos `alembic revision`, o Alembic preenche esse template e cria um arquivo novo dentro de `versions/`, já com:

- o identificador da revisão e o da revisão anterior;
- a data de criação e a mensagem informada no comando;
- as funções `upgrade()` e `downgrade()`, onde ficam as alterações do banco.

Só é preciso editar esse arquivo se quisermos mudar o formato padrão de todas as migrações futuras (por exemplo, adicionar um import que toda migração usa).

### `env.py`

É o arquivo que o Alembic executa sempre que um comando é rodado. Ele faz a ligação entre o Alembic e o projeto:

- lê a URL de conexão com o banco de dados;
- importa os modelos (`target_metadata`) para que o Alembic compare as tabelas existentes com os modelos e gere migrações automaticamente com `--autogenerate`;
- define como as migrações são executadas, conectado ao banco (modo *online*) ou gerando apenas o SQL (modo *offline*).

### `versions/`

Pasta onde ficam os arquivos de migração gerados. Cada arquivo representa uma alteração no banco, e juntos formam o histórico da estrutura do banco de dados, na ordem em que as mudanças foram feitas.

### Comandos mais usados

```bash
# Criar uma nova migração a partir das mudanças nos modelos
alembic revision --autogenerate -m "descrição da mudança"

# Aplicar todas as migrações pendentes
alembic upgrade head

# Desfazer a última migração
alembic downgrade -1
```

## Ajustando o arquivo migrations/env.py

1º Devemos importar as **Settings** do nosso arquivo **settings.py** e a classe **Base** (do SQLAlchemy) dos nossos modelos, junto com os arquivos dos modelos.

2º Definir o caminho da nossa base de dados pela URL do `.env` (`DATABASE_URL`).

3º No arquivo migrations/env.py, definir o `target_metadata` como `Base.metadata`. É a partir dele que o Alembic compara os modelos com o banco e gera as migrações automaticamente.

O projeto usa SQLite com o driver assíncrono **aiosqlite**. O template padrão do Alembic é síncrono e não funciona com esse driver, por isso o `env.py` abaixo é baseado no template assíncrono (`alembic init -t async migrations`).

### Pré-requisitos

- Driver instalado:

  ```bash
  pip install aiosqlite
  ```

- `DATABASE_URL` no `.env` usando o driver assíncrono:

  ```env
  DATABASE_URL="sqlite+aiosqlite:///comprix.db"
  ```

- No `alembic.ini`, apontar para a pasta `src`, caso o projeto não esteja instalado no ambiente:

  ```ini
  prepend_sys_path = src
  ```

### Arquivo `migrations/env.py`

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from comprix.models import usuarios  # noqa: F401
from comprix.models.base import Base
from comprix.settings import Settings

# Objeto de configuração do Alembic, com acesso aos valores do alembic.ini
config = context.config

# Usa a URL do banco definida no .env, em vez da que está no alembic.ini
config.set_main_option('sqlalchemy.url', Settings().DATABASE_URL)

# Configura o logging a partir do alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados dos modelos, usados pelo --autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera o SQL das migrações sem conectar ao banco."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cria uma engine assíncrona e executa as migrações."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Executa as migrações conectado ao banco."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### O que cada parte faz

- **Imports dos modelos**: o `Base.metadata` só conhece as tabelas cujas classes foram importadas. Cada novo arquivo em `models/` precisa ser importado aqui, como o `usuarios`, senão o `--autogenerate` não encontra a tabela.
- **`config.set_main_option`**: substitui a URL do `alembic.ini` pela do `.env`, para o banco ser configurado em um só lugar.
- **`target_metadata`**: é o que o Alembic compara com o banco para gerar as migrações automaticamente.
- **`render_as_batch=True`**: o SQLite tem suporte limitado a `ALTER TABLE` (não remove nem altera colunas diretamente). Com essa opção, o Alembic recria a tabela por baixo dos panos quando precisa fazer essas alterações.
- **`run_async_migrations`**: cria uma engine assíncrona e usa `run_sync` para executar as migrações, já que o Alembic em si trabalha de forma síncrona.
- **`run_migrations_offline`**: usada com a opção `--sql`, gera o SQL das migrações sem conectar ao banco.

### Testando a configuração

```bash
alembic revision --autogenerate -m "cria tabela usuarios"
alembic upgrade head
```

Se a migração gerada tiver o `op.create_table(...)` da tabela de usuários, a configuração está funcionando.

Se as funções `upgrade()` e `downgrade()` vierem apenas com `pass`, o Alembic não encontrou diferença entre os modelos e o banco. As causas mais comuns são:

- o modelo não foi importado no `env.py`;
- o modelo herda de outra base (ou usa outro `registry`) diferente da usada em `target_metadata`;
- a tabela já existe no banco, criada antes por um `create_all`, por exemplo.

Nesse caso, apague o arquivo gerado, corrija a causa e rode o comando de novo.

### Por que importar `usuarios` no `env.py`

```python
from comprix.models import usuarios  # noqa: F401
```

O SQLAlchemy só registra uma tabela no `Base.metadata` quando a classe do modelo é **carregada** pelo Python. Enquanto o arquivo `usuarios.py` não for importado, a classe `Usuario` não existe para o SQLAlchemy, e o `Base.metadata` fica vazio.

Esse import serve apenas para carregar o arquivo e registrar a tabela. Nada dele é usado diretamente no `env.py`, por isso o linter (Ruff ou Flake8) mostraria o aviso **F401 – import não utilizado** e poderia até removê-lo numa correção automática. O comentário `# noqa: F401` diz ao linter para ignorar esse aviso nessa linha, mantendo o import.

Sempre que um novo arquivo de modelo for criado em `models/`, ele precisa ser importado da mesma forma:

```python
from comprix.models import produtos, usuarios  # noqa: F401
```

Uma alternativa é importar todos os modelos no `models/__init__.py`. Assim, o `env.py` só precisa importar o pacote `comprix.models`, e basta lembrar de atualizar o `__init__.py`.

### Nomeando as migrações em ordem

Ao rodar o comando abaixo, o texto do `-m` vira parte do nome do arquivo, mas ele fica **depois** do ID da revisão, que é um hash aleatório:

```bash
alembic revision --autogenerate -m "01_cria tabela usuarios"
# gera: 720c9f529c84_01_cria_tabela_usuarios.py
```

Com isso, os arquivos ficam ordenados pelo hash, e não pelo número. Existem duas formas de manter as migrações em ordem.

#### Opção 1: número como ID da revisão

O parâmetro `--rev-id` permite definir o ID manualmente:

```bash
alembic revision --autogenerate --rev-id 01 -m "cria_tabela_usuarios"
# gera: 01_cria_tabela_usuarios.py
```

A numeração é controlada à mão. Se duas pessoas criarem a migração `02` em branches diferentes, elas vão entrar em conflito.

#### Opção 2: data no nome do arquivo (recomendada)

No `alembic.ini`, descomente e ajuste a linha `file_template`:

```ini
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s
```

Os arquivos passam a ser gerados assim:

```
2026_10_21_1051-720c9f529c84_cria_tabela_usuarios.py
```

A ordem fica automática pela data, sem numeração manual e sem risco de números repetidos.

#### A ordem real das migrações

Para o Alembic, a sequência das migrações não depende do nome do arquivo, e sim do campo `down_revision` dentro de cada um, que aponta para a migração anterior. A primeira migração tem `down_revision = None`. O nome do arquivo serve apenas para facilitar a leitura.

Para ver a sequência oficial:

```bash
alembic history
```

## As migrações do Comprix

Até aqui, o projeto tem três migrações, todas na tabela `usuarios`:

| Arquivo | O que faz |
|---|---|
| `720c9f529c84_01_cria_tabela_usuarios.py` | Primeira migração. Veio **vazia** (só com `pass`), porque a tabela já tinha sido criada antes pelo `create_all`. Ela marca o ponto de partida do histórico. |
| `d9c95ddfa8ff_02_recuperacao_de_senha_em_usuarios.py` | Remove a coluna `codigo`, cria `codigo_recuperacao`, `codigo_expira_em` e `codigo_tentativas` e aumenta a `senha` de 100 para 255 caracteres. |
| `e4ae67941be3_03_adiciona_admin_em_usuarios.py` | Cria a coluna `admin`, usada pelo `get_current_admin`. |

Com elas, o model `Usuarios` fica assim:

```python title="src/comprix/models/usuarios.py" linenums="1"
from datetime import datetime

from sqlalchemy import DateTime, String
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
    senha: Mapped[str] = mapped_column(String(255), nullable=False)
    primeiro_acesso: Mapped[bool] = mapped_column(default=True)
    admin: Mapped[bool] = mapped_column(default=False)
    status: Mapped[bool] = mapped_column(default=True)

    codigo_recuperacao: Mapped[str | None] = mapped_column(
        String(255), default=None
    )
    codigo_expira_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    codigo_tentativas: Mapped[int] = mapped_column(default=0)
```

| Coluna nova | Para que serve |
|---|---|
| `senha` com `String(255)` | O hash do Argon2 tem cerca de 100 caracteres; 255 dá folga para mudanças de parâmetros do algoritmo. |
| `admin` | Indica se o usuário é administrador. Começa como `False`. |
| `codigo_recuperacao` | Código de recuperação de senha (opcional). Preparada para a futura rota de "esqueci minha senha". |
| `codigo_expira_em` | Até quando o código de recuperação vale. `DateTime(timezone=True)` guarda a data com fuso. |
| `codigo_tentativas` | Quantas vezes o código foi digitado errado. |

!!! warning "Coluna obrigatória em tabela que já tem dados"
    Repare que as migrações 02 e 03 criam colunas `nullable=False` (`codigo_tentativas` e `admin`) **sem valor padrão no banco**. O `default=` do model só vale quando o SQLAlchemy insere um registro; ele não preenche as linhas que já existem. Se a tabela tiver usuários, o SQLite recusa a migração, porque as linhas antigas ficariam com a coluna vazia.

    Para colunas obrigatórias em tabelas com dados, acrescente um `server_default` na migração:

    ```python
    batch_op.add_column(
        sa.Column('admin', sa.Boolean(), nullable=False, server_default=sa.false())
    )
    ```

### Conclusão

Parabéns! 🎉 Com o Alembic configurado, o banco de dados do projeto passa a ter um histórico versionado: cada mudança nos modelos vira uma migração que pode ser revisada, aplicada com `alembic upgrade head` e desfeita com `alembic downgrade -1`.

A partir daqui, o fluxo para qualquer alteração no banco é sempre o mesmo:

1. criar ou alterar o modelo em `models/`;
2. garantir que ele está importado no `env.py`;
3. gerar a migração com `alembic revision --autogenerate`;
4. revisar o arquivo gerado;
5. aplicar com `alembic upgrade head`.

Assim, toda a equipe trabalha com a mesma estrutura de banco, e qualquer ambiente novo pode ser criado do zero com um único comando.
