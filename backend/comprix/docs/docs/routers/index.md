---
icon: lucide/layers
title: Routers
---
# :lucide-layers: Routers

## Organizando as rotas com `APIRouter`

Nosso projeto está bem estruturado e tem potencial para crescer ainda mais. A partir de agora, para manter essa organização, vamos usar um recurso do FastAPI chamado **`APIRouter`**, que permite separar as rotas em arquivos diferentes, agrupadas por assunto.

### O problema

Até aqui, todas as rotas ficam no `app.py`. Isso funciona bem no começo, mas, conforme o projeto cresce, o arquivo passa a acumular rotas de usuários, produtos, pedidos, autenticação e o que mais vier. O resultado é um arquivo enorme, difícil de ler, de manter e de testar.

### O que é o `APIRouter`

O `APIRouter` funciona como uma **"mini aplicação"**. Ele tem os mesmos decoradores do `app` (`@router.get`, `@router.post`, `@router.put`, `@router.delete`), mas fica em um arquivo separado. Depois, o `app.py` apenas **inclui** cada router na aplicação principal.

Assim, cada arquivo cuida de um único assunto:

```
src/comprix/
├── routers/
│   ├── __init__.py
│   ├── usuarios.py    # Rotas de usuários
│   └── produtos.py    # Rotas de produtos
└── app.py             # Cria a aplicação e inclui os routers
```

## Como vamos trabalhar a partir de agora

Até aqui, criamos as partes do projeto separadamente: primeiro a configuração, depois os modelos, os schemas, as migrações e os testes. A partir de agora, a forma de trabalhar muda.

Cada **assunto** do sistema será construído **completo, de uma só vez**. Ao criar as rotas de um assunto, vamos criar juntos tudo o que ele precisa para funcionar:

| Parte | Arquivo | O que faz |
|---|---|---|
| **Model** | `models/<assunto>.py` | Define a tabela no banco de dados (SQLAlchemy) |
| **Migration** | `migrations/versions/` | Cria ou altera a tabela no banco (Alembic) |
| **Schema** | `schemas/<assunto>.py` | Define os dados que entram e saem da API (Pydantic) |
| **Router** | `routers/<assunto>.py` | Define as rotas da API (FastAPI) |
| **Testes** | `tests/test_<assunto>.py` | Garante que as rotas funcionam como esperado (pytest) |

Assim, ao final de cada assunto, ele estará **pronto, testado e documentado**, e só então partimos para o próximo.

### Estrutura de cada assunto

Usando **usuários** como exemplo, os arquivos ficam assim:

```
comprix/
├── migrations/
│   └── versions/
│       └── ..._cria_tabela_usuarios.py   # Migration
├── src/comprix/
│   ├── models/
│   │   └── usuarios.py                   # Model
│   ├── schemas/
│   │   └── usuarios.py                   # Schema
│   ├── routers/
│   │   └── usuarios.py                   # Router
│   └── app.py                            # Inclui o router
└── tests/
    └── test_usuarios.py                  # Testes
```

O mesmo nome de arquivo se repete em cada pasta. Isso deixa fácil encontrar tudo o que pertence a um mesmo assunto.

### Passo a passo para criar um assunto

Todo assunto novo segue sempre a mesma sequência:

1. **Model:** criar a classe em `models/<assunto>.py`, herdando de `Base`.
2. **Importar no `env.py`:** adicionar o novo model no `migrations/env.py`, para o Alembic enxergar a tabela.
3. **Migration:** gerar e aplicar a migração:

    ```bash
    alembic revision --autogenerate -m "cria tabela <assunto>"
    alembic upgrade head
    ```

4. **Schemas:** criar os schemas de entrada e de saída em `schemas/<assunto>.py`.
5. **Router:** criar as rotas em `routers/<assunto>.py`, com `prefix` e `tags`.
6. **Incluir no `app.py`:** registrar o router com `app.include_router(...)`.
7. **Testes:** criar os testes em `tests/test_<assunto>.py` e rodar:

    ```bash
    pytest
    ```

8. **Documentação:** criar a página do assunto nesta seção.

!!! tip "Checklist"

    Um assunto só está concluído quando o model, a migration, os schemas, o router e os testes estão prontos, e todos os testes passam.

## Assuntos do projeto

Cada assunto tem sua própria página nesta seção, com o passo a passo completo da sua construção:

- **Usuários**
- **Seções**
- **Grupos**
- **Produtos**
- **Despesas**

Novos assuntos serão adicionados a esta lista conforme o projeto crescer.
