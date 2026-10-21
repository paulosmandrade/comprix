  ![Alembic](../assets/biblioteca/alembic-logo.png#only-light){ width="500" }
  ![Alembic](../assets/biblioteca/alembic-logo-dark.png#only-dark){ width="500" }

[Alembic](https://alembic.sqlalchemy.org/) é uma ferramenta de migrações de banco de dados para Python, criada pelo mesmo autor do SQLAlchemy. Ela permite versionar a estrutura do banco de dados da mesma forma que o Git versiona o código.

### Por que usar migrações

Sem migrações, toda mudança no banco (criar uma tabela, adicionar uma coluna, renomear um campo) precisa ser feita à mão em cada ambiente: na máquina de cada desenvolvedor, no servidor de testes e em produção. Isso costuma gerar bancos diferentes entre si e erros difíceis de rastrear.

Com o Alembic:

- cada mudança vira um **arquivo de migração**, guardado junto com o código;
- as migrações formam um **histórico em ordem**, que pode ser aplicado do zero em qualquer ambiente;
- toda mudança pode ser **desfeita**, voltando o banco para uma versão anterior;
- o Alembic **gera as migrações automaticamente**, comparando os modelos do SQLAlchemy com o banco.

### Instalação

```bash
pip install alembic
```

### Inicialização

Na raiz do projeto, rode:

```bash
alembic init migrations
```

Para projetos com driver assíncrono (como `aiosqlite` ou `asyncpg`), use o template assíncrono:

```bash
alembic init -t async migrations
```

O comando cria o arquivo `alembic.ini` e o diretório `migrations`:

```
comprix/
├── migrations/
│   ├── versions/        # Arquivos de migração
│   ├── env.py           # Ligação entre o Alembic e o projeto
│   ├── README
│   └── script.py.mako   # Modelo usado para gerar cada migração
└── alembic.ini          # Configuração do Alembic
```

| Arquivo | Função |
|---|---|
| `alembic.ini` | Configurações gerais: onde ficam as migrações, URL do banco, logs e formato do nome dos arquivos |
| `env.py` | Executado em todo comando; conecta ao banco e informa ao Alembic quais são os modelos |
| `script.py.mako` | Modelo usado para criar cada novo arquivo de migração |
| `versions/` | Pasta com as migrações geradas, que formam o histórico do banco |

### Configuração

A configuração principal fica no `migrations/env.py`, onde definimos:

- a **URL do banco**, lida do `.env` pelo `Settings`;
- o **`target_metadata`**, que aponta para os modelos do SQLAlchemy e permite gerar migrações automaticamente.

```python
from comprix.models import usuarios  # noqa: F401
from comprix.models.base import Base
from comprix.settings import Settings

config = context.config
config.set_main_option('sqlalchemy.url', Settings().DATABASE_URL)

target_metadata = Base.metadata
```

No `alembic.ini`, a linha abaixo faz o Alembic encontrar o pacote `comprix` dentro da pasta `src`:

```ini
prepend_sys_path = src
```

### Anatomia de uma migração

Cada arquivo em `versions/` tem esta estrutura:

```python
"""cria tabela usuarios

Revision ID: 720c9f529c84
Revises:
Create Date: 2026-10-21 10:51:12.092217

"""

from alembic import op
import sqlalchemy as sa

revision = '720c9f529c84'
down_revision = None


def upgrade() -> None:
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )


def downgrade() -> None:
    op.drop_table('usuarios')
```

- **`revision`**: identificador único da migração;
- **`down_revision`**: migração anterior; é o que define a ordem do histórico (`None` na primeira);
- **`upgrade()`**: aplica a mudança no banco;
- **`downgrade()`**: desfaz a mudança.

### Comandos mais usados

| Comando | O que faz |
|---|---|
| `alembic revision --autogenerate -m "mensagem"` | Gera uma migração comparando os modelos com o banco |
| `alembic revision -m "mensagem"` | Cria uma migração vazia, para escrever à mão |
| `alembic upgrade head` | Aplica todas as migrações pendentes |
| `alembic upgrade +1` | Aplica apenas a próxima migração |
| `alembic downgrade -1` | Desfaz a última migração aplicada |
| `alembic downgrade base` | Desfaz todas as migrações |
| `alembic current` | Mostra em qual migração o banco está |
| `alembic history` | Lista todas as migrações, em ordem |
| `alembic upgrade head --sql` | Mostra o SQL que seria executado, sem aplicar |

O Alembic registra a versão atual do banco em uma tabela própria, chamada `alembic_version`. É por ela que ele sabe quais migrações já foram aplicadas.

### Fluxo de trabalho

Toda alteração no banco segue os mesmos passos:

1. criar ou alterar o modelo em `models/`;
2. se for um arquivo novo, importá-lo no `env.py`;
3. gerar a migração:

    ```bash
    alembic revision --autogenerate -m "adiciona coluna telefone em usuarios"
    ```

4. **revisar o arquivo gerado** em `versions/`;
5. aplicar no banco:

    ```bash
    alembic upgrade head
    ```

6. fazer o commit do modelo e da migração juntos.

### Cuidados com o `--autogenerate`

O `--autogenerate` ajuda muito, mas não detecta tudo. Por isso, a migração gerada sempre deve ser revisada antes de ser aplicada.

- **Renomear tabela ou coluna**: o Alembic entende como "remover uma e criar outra", o que apaga os dados. Nesse caso, troque manualmente para `op.alter_column(...)` ou `op.rename_table(...)`.
- **Migração vazia** (só com `pass`): o Alembic não encontrou diferenças. Verifique se o modelo foi importado no `env.py` e se a tabela já não existe no banco.
- **SQLite**: tem suporte limitado a `ALTER TABLE`. Use `render_as_batch=True` no `env.py` para que o Alembic consiga alterar e remover colunas.

### Resumo

- O Alembic versiona a estrutura do banco de dados, como o Git faz com o código.
- O `env.py` conecta o Alembic aos modelos e ao banco do projeto.
- O `alembic revision --autogenerate` cria migrações a partir dos modelos.
- O `alembic upgrade head` aplica as migrações, e o `alembic downgrade -1` desfaz a última.
- Toda migração gerada deve ser revisada antes de ser aplicada.
