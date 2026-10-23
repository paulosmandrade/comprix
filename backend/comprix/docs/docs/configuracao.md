---
icon: lucide/settings
title: Configurando o ambiente de desenvolvimento
---

# :lucide-settings: Configurando o ambiente de desenvolvimento

---

Como esse projeto é para usuários de nível intermediário, vamos levar em consideração que você já tenha o python instalado e criado o ambiente virtual (pip, uv ou poetry).

!!! linux
    Nessa minha máquina, estou utilizando linux.

Vamos utilizar a versão abaixo do python.

* [x] Python - (Versão 3.14 ou superior)

Com o python instalado, vamos criar nosso ambiente virtual, acessando o terminal e digitando o comando abaixo (No meu caso vou utilizar o poetry para gerenciar meu projeto e pacotes).


=== "Poetry"
    ``` poetry
    poetry new comprix
    ```

=== "pip"

    ``` pip
    python -m venv .venv
    ```

=== "uv"

    ``` uv
    uv venv  
    ```

Agora vamos ativar o ambiente virtual para poder instalar os frameworks do universo python.

=== "Poetry"
    ``` poetry
    eval $(poetry env activate)
    ```

    !!! info "E o `poetry shell`?"
        A partir do **Poetry 2.0**, o comando `poetry shell` deixou de vir instalado por padrão. O substituto é o `poetry env activate`, que mostra o comando de ativação; o `eval` executa esse comando no terminal atual. Também é possível rodar qualquer comando sem ativar o ambiente, com `poetry run <comando>`.

=== "pip"

    ``` pip
    source .venv/bin/activate  
    ```

=== "uv"

    ``` uv
    source .venv/bin/activate 
    ```

!!! Terminal
    ![Ambiente Virtual](../assets/configuracao/active_ambiente_virtual.png)


No meu caso, como estou utilizando o poetry o próprio sistema já cria uma estrutura de projeto.


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

Caso não conheça a ferramenta do poetry e suas estrutura, aconselho a olhar a documentação no site [poetry](https://python-poetry.org/).

## Atalhos de comandos com o Poe

Ao longo da documentação usamos comandos curtos, como `poetry serve` e `poetry test`. Eles não são comandos nativos do Poetry: são **tarefas** do [Poe the Poet](https://poethepoet.natn.io/), instalado como plugin do Poetry:

```console title="Terminal"
$ poetry self add 'poethepoet[poetry_plugin]'
```

As tarefas ficam no `pyproject.toml`. A linha `poetry_command = ""` faz cada tarefa virar um comando direto do Poetry (`poetry test` em vez de `poetry poe test`):

```toml title="pyproject.toml"
[tool.poe]
poetry_command = ""

[tool.poe.tasks]
lint = {cmd = "ruff check"}
format.sequence = [
    { cmd = "ruff check --fix"},
    { cmd = "ruff format"}
]
serve = "fastapi dev src/comprix/app.py"
test.sequence = [
    "lint",
    { cmd = "pytest -s -x -vv $POE_EXTRA_ARGS"},
    { cmd  = "coverage html --show-contexts"}
]
docs = {cmd = "zensical serve --dev-addr localhost:8001", cwd = "docs"}
```

| Comando | O que faz |
|---|---|
| `poetry lint` | Verifica o código com o **ruff** |
| `poetry format` | Corrige o que for possível e formata o código |
| `poetry serve` | Sobe a API em modo de desenvolvimento |
| `poetry test` | Roda o lint, os testes com cobertura e gera o relatório HTML |
| `poetry docs` | Sobe este site de documentação em `http://localhost:8001` |

Como essa documentação é voltada para nosso projeto Backend (api), já temos nosso ambiente configurado, próxima etapa é falar sobre as bibliotecas, frameworks e suas configurações.

