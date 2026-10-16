# Estrutura do projeto

Como estamos utilizando o poetry em nosso projeto, já temos a nosso estrutura pronta, conforme verificamos na configuração do ambiente.

``` Projeto hl_lines="2" title="Estrutura"
├── comprix
    │  └── __init__.py
    ├── pyproject.toml
    ├── README.md
    └── tests
       └── __init__.py

```

Abaixo, vamos detalhar a importancia de cada um desses arquivo na nossa estrutura.

* [x] __init__.py, marca a pasta como um pacote Python.

* [x] ***project.toml***, é um arquivo de configuração padrão de qualquer projeto python moderno, ele cumpri alguns papéis importantes, como nome do projeto, autores, dependências e ferramentas. 

TOML é um formato de texto feito para configuração, parecido com um .ini, porém com tipos:
```

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

* [x] READMED.md , É o arquivo de apresentação do projeto, a primeira coisa que alguém deve ler para entender do que se trata.

* [x] tests, Diretório onde vamos realizar nos testes.


