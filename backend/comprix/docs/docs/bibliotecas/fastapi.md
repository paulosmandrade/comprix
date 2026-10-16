![FastAPI](https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png){ width="500" }

[FastAPI](https://fastapi.tiangolo.com/pt/) é um framework web moderno e rápido (alta performace) para construção de APIs com Python, baseado nas anotações de tipo padrão do Python.

## Principais características

<div class="grid cards" markdown>

-   :lucide-zap:{ .lg .middle } **Rápido**

    ---

    Alta performance, equivalente a **NodeJS** e **Go**, graças ao Starlette e ao Pydantic.
    [Um dos frameworks Python mais rápidos disponíveis](https://www.techempower.com/benchmarks/).

-   :lucide-rocket:{ .lg .middle } **Rápido para codar**

    ---

    Aumenta a velocidade de desenvolvimento de recursos entre 200% e 300%.[^1]

-   :lucide-bug-off:{ .lg .middle } **Poucos bugs**

    ---

    Reduz cerca de 40% dos erros induzidos por humanos (desenvolvedores).[^1]

-   :lucide-sparkles:{ .lg .middle } **Intuitivo**

    ---

    Grande suporte a editores, com *autocompletar* em todos os lugares.
    Menos tempo depurando.

-   :lucide-smile:{ .lg .middle } **Fácil**

    ---

    Projetado para ser fácil de aprender e usar.
    Menos tempo lendo documentação.

-   :lucide-minimize-2:{ .lg .middle } **Enxuto**

    ---

    Minimiza a duplicação de código: várias funcionalidades a partir de cada
    declaração de parâmetro. Menos bugs.

-   :lucide-shield-check:{ .lg .middle } **Robusto**

    ---

    Código pronto para produção, com documentação interativa automática.

-   :lucide-badge-check:{ .lg .middle } **Baseado em padrões**

    ---

    Totalmente compatível com os padrões abertos para APIs:
    [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (antigo Swagger)
    e [JSON Schema](https://json-schema.org/).

</div>

[^1]: Estimativas baseadas em testes realizados pela equipe interna de desenvolvimento do FastAPI, construindo aplicações em produção.

!!! info "Fonte"
    Características extraídas da [documentação oficial do FastAPI](https://fastapi.tiangolo.com/pt/).


A forma de instalar esse framework em nossa aplicação python e utilizando o comando abaixo.

=== "Poetry"
    ``` poetry
    poetry install
    poetry add "fastapi[standard]"
    ```

=== "pip"

    ``` pip
    pip install "fastapi[standard]"
    ```

=== "uv"

    ``` uv
    uv pip install "fastapi[standard]"
    ```


Toda a biblioteca que adicionamos em nosso projeto, ela fica documentada no nosso arquivo raiz chamado **pyproject.toml**. No campo **dependencies** (nome e versão).

``` Projeto hl_lines="2" title="FastAPI"
[project]
name = "comprix"
version = "0.1.0"
description = ""
authors = [
    {name = "paulosmandrade",email = "paulo.smandrade@hotmail.com"}
]
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "fastapi[standard] (>=0.142.2,<0.143.0)"
]

```

Caso tenha interesse em aprender mais sobre esse maravilhoso framework FastAPI, aconselho você a fazer o curso com o nosso @dunossauro, [fastapidozero](https://fastapidozero.dunossauro.com/estavel/).