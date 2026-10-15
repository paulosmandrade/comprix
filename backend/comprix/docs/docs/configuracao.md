---
icon: lucide/settings
---

# Configurando o ambiente de desenvolvimento

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
    poetry shell
    ```

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


No meu caso, como estou utilizando o poetry o próprio sistema ja cria uma estrutura de projeto.


``` Projeto hl_lines="2" title="Estrutura"
├── comprix
    │  └── __init__.py
    ├── pyproject.toml
    ├── README.md
    └── tests
       └── __init__.py

```

Caso não conheça a ferramenta do poetry e suas estrutura, aconselho a olhar a documentação no site [poetry](https://python-poetry.org/).

Como essa documentação é voltada para nosso projeto Backend (api), já temos nosso ambiente configurado, próxima etapa e falar sobre as bibliotecas, frameworks e suas configurações.

