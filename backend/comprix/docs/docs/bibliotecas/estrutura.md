# Estrutura do projeto

Como estamos utilizando o poetry em nosso projeto, já temos a nossa estrutura pronta, conforme verificamos na configuração do ambiente.

``` Projeto hl_lines="3 4" title="Estrutura"
comprix
├── src
│   └── comprix
│       └── __init__.py
├── tests
│   └── __init__.py
├── pyproject.toml
└── README.md
```

Abaixo, vamos detalhar a importância de cada um desses arquivos na nossa estrutura.

* [x] ***src/comprix***, é o pacote da nossa aplicação. O Poetry usa o chamado *src layout*: o código fica dentro de `src`, e o nome do pacote continua sendo `comprix` (por isso os imports são `from comprix...`).

* [x] ***\_\_init\_\_.py***, marca a pasta como um pacote Python.

* [x] ***pyproject.toml***, é um arquivo de configuração padrão de qualquer projeto python moderno, ele cumpre alguns papéis importantes, como nome do projeto, autores, dependências e ferramentas.

TOML é um formato de texto feito para configuração, parecido com um .ini, porém com tipos:

```toml title="pyproject.toml"
[project]
name = "comprix"                 # nome do pacote
version = "0.1.0"                # versão atual
description = ""
authors = [{name = "paulosmandrade", email = "..."}]
readme = "README.md"             # arquivo usado como descrição longa
requires-python = ">=3.14"       # versão mínima do Python
dependencies = [                 # o que a aplicação precisa para RODAR
    "fastapi[standard] (>=0.142.2,<0.143.0)"
]
```

* [x] ***README.md***, é o arquivo de apresentação do projeto, a primeira coisa que alguém deve ler para entender do que se trata.

* [x] ***tests***, diretório onde vamos escrever os nossos testes.

## Como o projeto fica ao longo da documentação

Cada página acrescenta novos arquivos a essa estrutura. Para ter uma visão geral, esta é a estrutura atual do projeto:

```text title="Estrutura atual"
comprix
├── docs/                       # Este site de documentação (Zensical)
├── migrations/                 # Migrações do banco de dados (Alembic)
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── src
│   └── comprix
│       ├── models/             # Tabelas do banco (SQLAlchemy)
│       │   ├── __init__.py
│       │   ├── base.py
│       │   └── usuarios.py
│       ├── routers/            # Rotas da API, separadas por assunto
│       │   ├── auth.py
│       │   └── usuarios.py
│       ├── schemas/            # Dados que entram e saem da API (Pydantic)
│       │   ├── __init__.py
│       │   ├── app.py
│       │   └── usuarios.py
│       ├── static/             # Arquivos estáticos (favicon)
│       ├── templates/
│       │   └── email/          # Templates HTML dos e-mails
│       ├── __init__.py
│       ├── app.py              # Ponto de entrada da aplicação
│       ├── database.py         # Conexão com o banco e lifespan
│       ├── email.py            # Envio de e-mails
│       ├── security.py         # Hash de senha e tokens JWT
│       └── settings.py         # Configurações lidas do .env
├── tests/                      # Testes automatizados (pytest)
├── .env                        # Configurações locais (fora do Git)
├── .env.example                # Modelo das variáveis de ambiente
├── alembic.ini                 # Configuração do Alembic
├── pyproject.toml
└── README.md
```
