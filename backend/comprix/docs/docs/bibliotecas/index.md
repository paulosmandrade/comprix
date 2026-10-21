---
icon: lucide/library
title: Bibliotecas/Frameworks
---

# :lucide-library: Bibliotecas/Frameworks

Nesta seção apresentamos as principais ferramentas usadas no projeto: o que cada uma faz e por que foi escolhida.

!!! info "Como usar esta seção"

    As páginas de cada biblioteca trazem uma visão geral, **apenas para conhecimento**. Não é preciso decorar nada agora: cada recurso será usado na prática conforme o projeto avançar.

    O mais importante é criar o hábito de **consultar a documentação oficial** de cada ferramenta. É lá que estão os detalhes, os exemplos atualizados e as respostas para a maioria das dúvidas.

## Aplicação

| Ferramenta | Para que serve | Documentação |
|---|---|---|
| **FastAPI** | Framework web para construir a API: rotas, requisições e respostas | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/pt/) |
| **Pydantic** | Validação dos dados que entram e saem da API e leitura das configurações do `.env` | [docs.pydantic.dev](https://docs.pydantic.dev/) |
| **pwdlib** | Geração e verificação de hashes de senhas, com o algoritmo Argon2 | [pypi.org/project/pwdlib](https://pypi.org/project/pwdlib/) |

## Banco de dados

| Ferramenta | Para que serve | Documentação |
|---|---|---|
| **SQLAlchemy** | Comunicação com o banco de dados usando classes e objetos Python (ORM) | [docs.sqlalchemy.org](https://docs.sqlalchemy.org/) |
| **Alembic** | Migrações: versiona a estrutura do banco de dados | [alembic.sqlalchemy.org](https://alembic.sqlalchemy.org/) |
| **aiosqlite** | Driver assíncrono que conecta o SQLAlchemy ao SQLite | [aiosqlite.omnilib.dev](https://aiosqlite.omnilib.dev/) |

## Desenvolvimento

| Ferramenta | Para que serve | Documentação |
|---|---|---|
| **pytest** | Execução dos testes automatizados | [docs.pytest.org](https://docs.pytest.org/) |
| **Ruff** | Verificação de erros e formatação do código | [docs.astral.sh/ruff](https://docs.astral.sh/ruff/) |
| **Zensical** | Geração deste site de documentação | [zensical.org](https://zensical.org/) |

## Como as ferramentas se conectam

Uma requisição percorre o projeto mais ou menos assim:

1. O **FastAPI** recebe a requisição e encaminha para a rota certa.
2. O **Pydantic** valida os dados recebidos.
3. Se houver senha envolvida, a **pwdlib** gera ou verifica o hash.
4. O **SQLAlchemy** lê ou grava os dados no banco, usando o **aiosqlite**.
5. O **Pydantic** formata a resposta, e o **FastAPI** a devolve para quem chamou.

Já o **Alembic** atua fora desse fluxo: ele mantém a estrutura do banco atualizada sempre que os modelos mudam.

!!! tip "Dica"

    Ao encontrar um recurso novo durante o projeto, procure-o na documentação oficial antes de pesquisar em outros lugares. Além de mais confiável, ela costuma ter exemplos prontos para testar.