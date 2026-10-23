![Ruff](https://cdn.simpleicons.org/ruff){ width="80" }

O [Ruff](https://docs.astral.sh/ruff/) é um **linter** e **formatador** de código Python, escrito em Rust e extremamente rápido. Ele faz em uma só ferramenta o trabalho que antes exigia várias (Flake8, isort, Black, pylint...).

- **Linter:** procura erros e más práticas, como imports não usados, variáveis indefinidas e linhas longas demais.
- **Formatador:** padroniza o estilo do código (aspas, espaços, quebras de linha), para todo o projeto ficar com a mesma cara.

### Instalação

```bash
poetry add --group dev ruff
```

### Configuração

No `pyproject.toml`:

```toml
[tool.ruff]
line-length = 79
extend-exclude = ['migrations']

[tool.ruff.lint]
preview = true
select = ['I','F','E', 'W', 'PL', 'PT']

[tool.ruff.format]
preview = true
quote-style = 'single'
```

| Opção | O que faz |
|---|---|
| `line-length = 79` | Tamanho máximo da linha, seguindo a PEP 8 |
| `extend-exclude = ['migrations']` | Ignora as migrações, que são geradas pelo Alembic |
| `preview = true` | Ativa regras e estilos mais novos, ainda em fase de testes |
| `quote-style = 'single'` | Formata as strings com aspas simples |

As regras ativadas no `select`:

| Código | Regras de | O que verifica |
|---|---|---|
| `I` | isort | Ordem e agrupamento dos imports |
| `F` | Pyflakes | Erros como imports e variáveis não usados |
| `E` / `W` | pycodestyle | Estilo da PEP 8 (erros e avisos) |
| `PL` | Pylint | Boas práticas, como evitar números "mágicos" e imports fora do topo |
| `PT` | flake8-pytest-style | Boas práticas na escrita dos testes |

### Comandos

| Comando | O que faz |
|---|---|
| `poetry lint` | `ruff check`: mostra os problemas encontrados |
| `poetry format` | `ruff check --fix` + `ruff format`: corrige o que der e formata o código |

### Ignorando uma regra em uma linha

Às vezes uma regra precisa ser quebrada de propósito. O comentário `# noqa` com o código da regra avisa o ruff de que aquilo é intencional:

```python
from comprix.models import usuarios  # noqa: F401
```

Exemplos usados no projeto:

| Código | Regra | Onde aparece |
|---|---|---|
| `F401` | Import não utilizado | `migrations/env.py`, para registrar os models |
| `PLC0415` | Import fora do topo do arquivo | `lifespan` no `database.py`, para evitar import circular |
| `PLR2004` | Número "mágico" em uma comparação | `testar_conexao` no `email.py` |

!!! tip "Prefira corrigir a ignorar"
    Use o `# noqa` só quando houver um bom motivo, e sempre com o código da regra. Um `# noqa` sozinho ignora **todas** as regras naquela linha.

### Resumo

- O Ruff verifica (`ruff check`) e formata (`ruff format`) o código.
- As regras e o estilo ficam no `pyproject.toml`.
- O `poetry test` roda o ruff antes dos testes: código fora do padrão faz a execução parar.
