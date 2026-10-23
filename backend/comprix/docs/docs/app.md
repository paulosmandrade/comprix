---
icon: lucide/monitor-cloud
title: App
---

# :lucide-monitor-cloud: App

Vamos criar nosso primeiro arquivo python, que será o principal da nossa aplicação, será o arquivo **app.py**, através dele será inicializado nossa aplicação para as demais rotas e funções do nosso sistema.

``` Projeto hl_lines="4" title="app.py"
comprix
├── src
│   └── comprix
│       ├── app.py
│       └── __init__.py
├── tests
│   └── __init__.py
├── pyproject.toml
└── README.md
```

## Primeira rota

Antes de criar as funcionalidades do Comprix, vamos entender o código mínimo de uma aplicação FastAPI: uma API com um único endereço que responde com uma mensagem de boas-vindas.


```python title="src/comprix/app.py" linenums="1" hl_lines="6 7 8"
from fastapi import FastAPI

app = FastAPI()


@app.get('/')
def read_root():
    return {'message': 'Bem-vindo ao Comprix'}
```

Na linha 1, importando a biblioteca do FastAPI.

Na linha 3, cria a aplicação e a guarda na variável app. É esse objeto que recebe as requisições e decide o que responder.

Nas linhas 6 a 8, criamos a rota: o decorador `@app.get('/')` diz que a função `read_root` responde às requisições `GET` no endereço `/`, e o dicionário retornado é convertido em JSON automaticamente.

??? info "Por que o nome app?" 
    O comando `fastapi dev src/comprix/app.py` procura uma variável chamada app dentro do arquivo.

Agora vamos executar o comando abaixo no nosso terminal:

**fastapi dev src/comprix/app.py**

!!! tip "Atalho"
    Esse mesmo comando está configurado como a tarefa `poetry serve` (veja [Configuração de Ambiente](configuracao.md#atalhos-de-comandos-com-o-poe)).

```console title="Terminal"
$ fastapi dev src/comprix/app.py

 ⚡️ Starting FastAPI in development mode

 🐍 Using import string: comprix.app:app

 🌐 Server started at http://127.0.0.1:8000
    Documentation at http://127.0.0.1:8000/docs

  Logs:

 ▕  Will watch for changes in these directories: ['/home/pandrade/Documentos/Projetos/comprix/backend/comprix']
 ▕  Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
 ▕  Started reloader process [305503] using WatchFiles
 ▕  Started server process [305509]
 ▕  Waiting for application startup.
 ▕  Application startup complete.
```

### :material-rocket-launch: sim, nossa aplicação já esta no Ar!

Observe no endereço host que esta sendo executado nossa aplicação http://127.0.0.1:8000.


![app](assets/app/app.png){ width="100%" }


O FastAPI é fantástico, porque ele já cria nossa documentação das rotas no endereço http://127.0.0.1:8000/docs.


![app docs](assets/app/app_docs.png){ width="100%" }

## Como o `app.py` fica no final

Conforme o projeto avança, o `app.py` recebe novas responsabilidades, cada uma explicada na sua página. Esta é a versão atual do arquivo:

```python title="src/comprix/app.py" linenums="1"
from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from comprix.database import lifespan
from comprix.routers import auth, usuarios
from comprix.schemas.app import Message

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(usuarios.router)


FAVICON = Path(__file__).parent / 'static' / 'comprix-icon.ico'


@app.get('/favicon.ico', include_in_schema=False)
def favicon():
    return FileResponse(FAVICON)


@app.get('/', status_code=HTTPStatus.OK, response_model=Message)
def read_root():
    return {'message': 'Bem-vindo ao Comprix'}
```

| Trecho | O que faz | Onde é explicado |
|---|---|---|
| `lifespan=lifespan` | Cria as tabelas e o administrador quando a API liga | [Sqlite - Models](sqlite.md#ligando-o-banco-na-api) e [Usuários](routers/usuarios.md) |
| `app.include_router(...)` | Registra as rotas de autenticação e de usuários | [Routers](routers/index.md) |
| `/favicon.ico` | Devolve o ícone do Comprix para o navegador. O `include_in_schema=False` esconde essa rota do `/docs` | — |
| `response_model=Message` | Define o formato da resposta da rota `/` | [Schemas](schemas.md) |


