![SQLAlchemy](../assets/biblioteca/sqlalchemy-logo-white.png#only-light){ width="500" }
![SQLAlchemy](../assets/biblioteca/sqlalchemy-logo-dark.png#only-dark){ width="500" }

[SQLAlchemy](https://www.sqlalchemy.org/) é a principal biblioteca de banco de dados do Python. Ela permite trabalhar com o banco usando classes e objetos Python, em vez de escrever SQL à mão, sem perder o controle sobre as consultas.

### Principais características

- **ORM (Object Relational Mapper):** cada tabela do banco é representada por uma classe Python, e cada linha, por um objeto.
- **Vários bancos de dados:** o mesmo código funciona com SQLite, PostgreSQL, MySQL, SQL Server e Oracle; muda apenas a URL de conexão.
- **Tipagem moderna:** os modelos usam as anotações de tipo do Python (`Mapped[...]`), o que melhora o autocompletar do editor e a verificação de erros.
- **Suporte assíncrono:** funciona com `async`/`await`, ideal para APIs com FastAPI.
- **Integração com o Alembic:** o Alembic lê os modelos do SQLAlchemy para gerar as migrações automaticamente.

### Instalação

```bash
pip install sqlalchemy aiosqlite
```

O `aiosqlite` é o driver assíncrono do SQLite usado no projeto.

### Base dos modelos

Todos os modelos herdam de uma classe base, que guarda o registro de todas as tabelas (`Base.metadata`):

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

### Criando um modelo

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from comprix.models.base import Base, atualizado, criado


class Usuario(Base):
    __tablename__ = 'usuarios'

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(unique=True)
    telefone: Mapped[str | None]
    criado_em: Mapped[criado]
    atualizado_em: Mapped[atualizado]
```

- **`__tablename__`**: nome da tabela no banco;
- **`Mapped[tipo]`**: define o tipo da coluna; `str | None` indica que a coluna aceita valor nulo;
- **`mapped_column(...)`**: adiciona regras, como chave primária, valor único e tamanho máximo.

Os tipos `criado` e `atualizado`, definidos no `base.py`, preenchem as datas automaticamente no fuso de São Paulo: `criado` na inserção, e `atualizado` na inserção e a cada alteração.

### Conexão e sessão

A **engine** é a conexão com o banco, e a **sessão** é por onde todas as operações passam:

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from comprix.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL)
Session = async_sessionmaker(engine, expire_on_commit=False)
```

### Operações básicas (CRUD)

```python
from sqlalchemy import select

async with Session() as session:
    # Criar
    usuario = Usuario(nome='Paulo', email='paulo@email.com')
    session.add(usuario)
    await session.commit()

    # Buscar um
    usuario = await session.scalar(
        select(Usuario).where(Usuario.email == 'paulo@email.com')
    )

    # Buscar vários
    usuarios = await session.scalars(select(Usuario).order_by(Usuario.nome))

    # Atualizar
    usuario.nome = 'Paulo Andrade'
    await session.commit()

    # Excluir
    await session.delete(usuario)
    await session.commit()
```

As alterações só são gravadas no banco depois do `commit()`. Até lá, podem ser desfeitas com `rollback()`.

### Relacionamentos

O `relationship` liga dois modelos, permitindo navegar de um objeto para outro:

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Pedido(Base):
    __tablename__ = 'pedidos'

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'))

    usuario: Mapped['Usuario'] = relationship(back_populates='pedidos')
```

E, no modelo `Usuario`:

```python
pedidos: Mapped[list['Pedido']] = relationship(back_populates='usuario')
```

Assim, `pedido.usuario` retorna o usuário do pedido, e `usuario.pedidos` retorna a lista de pedidos do usuário.

### Resumo

- O SQLAlchemy representa as tabelas como classes Python (ORM).
- Os modelos herdam de `Base` e usam `Mapped` e `mapped_column` para definir as colunas.
- A sessão controla todas as operações, e nada é salvo sem `commit()`.
- O `select()` monta as consultas, e o `relationship()` liga os modelos.
- O Alembic usa o `Base.metadata` para gerar as migrações do banco.
