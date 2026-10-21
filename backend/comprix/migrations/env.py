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
