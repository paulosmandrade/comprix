![pytest](https://cdn.simpleicons.org/pytest){ width="80" }

O [pytest](https://docs.pytest.org/) é a ferramenta de **testes automatizados** mais usada no Python. Com ele, um teste é só uma função cujo nome começa com `test_`, e as verificações são feitas com o `assert` comum do Python.

### Principais características

- **Testes simples:** sem classes obrigatórias nem métodos especiais, basta `assert`.
- **Mensagens claras:** quando um `assert` falha, o pytest mostra os valores comparados.
- **Fixtures:** funções que preparam o que o teste precisa (banco, cliente da API, usuário logado) e são entregues como parâmetro.
- **Plugins:** o projeto usa o `pytest-cov` (cobertura) e o `pytest-asyncio` (testes assíncronos).

### Instalação

No projeto, o pytest e os plugins são dependências de **desenvolvimento**: são usados para testar, mas não para rodar a API.

```bash
poetry add --group dev pytest pytest-cov pytest-asyncio freezegun
```

| Pacote | Para que serve |
|---|---|
| `pytest` | Executa os testes |
| `pytest-cov` | Mede a cobertura: quais linhas do código os testes executaram |
| `pytest-asyncio` | Permite escrever testes e fixtures com `async`/`await` |
| `freezegun` | Congela o relógio, para testar tokens e links expirados |

### Configuração

No `pyproject.toml`:

```toml
[tool.pytest]
pythonpath = ['src']
addopts = ['-p', 'no:warnings', '--cov=comprix', '--cov-context=test']
asyncio_default_fixture_loop_scope = 'function'

[tool.coverage.run]
concurrency = ['thread', 'greenlet']
core = 'ctrace'
```

- **`pythonpath`**: permite importar o pacote `comprix`, que fica dentro de `src`;
- **`addopts`**: opções usadas em toda execução: esconde avisos, mede a cobertura do pacote `comprix` e registra qual teste executou cada linha;
- **`[tool.coverage.run]`**: ajustes para a cobertura funcionar com o SQLAlchemy assíncrono (explicados em [Sqlite - Models](../sqlite.md#configurando-a-cobertura-de-testes)).

### Um teste simples

```python title="tests/test_app.py"
from http import HTTPStatus


def test_root_deve_retornar_ok_e_mensagem(client):
    response = client.get('/')

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {'message': 'Bem-vindo ao Comprix'}
```

O parâmetro `client` é uma **fixture**: o pytest a encontra no `conftest.py` e a entrega pronta ao teste.

### Fixtures e o `conftest.py`

As fixtures compartilhadas ficam no `tests/conftest.py`. O pytest carrega esse arquivo automaticamente, sem precisar de import.

```python
import pytest


@pytest.fixture
def numeros():
    return [1, 2, 3]


def test_soma(numeros):
    assert sum(numeros) == 6
```

Com `yield` no lugar do `return`, o código depois do `yield` roda **ao final** do teste, ideal para limpar recursos (fechar o banco, desfazer alterações).

As fixtures do Comprix são explicadas na página [Token](../seguranca/token.md#73-entendendo-cada-fixture).

### Testes assíncronos

Funções `async` precisam do marcador do `pytest-asyncio`:

```python
import pytest


@pytest.mark.asyncio
async def test_criar_usuario(session): ...
```

E as fixtures assíncronas usam `@pytest_asyncio.fixture` no lugar de `@pytest.fixture`.

### Testando erros

O `pytest.raises` confirma que um trecho de código **lança** uma exceção:

```python
with pytest.raises(HTTPException) as exc:
    await get_current_admin(usuario=usuario_comum)

assert exc.value.status_code == HTTPStatus.FORBIDDEN
```

### Comandos mais usados

| Comando | O que faz |
|---|---|
| `poetry test` | Roda o ruff, os testes com cobertura e gera o relatório HTML |
| `pytest` | Roda todos os testes |
| `pytest -v` | Mostra o nome de cada teste e o resultado |
| `pytest tests/test_auth.py` | Roda apenas um arquivo |
| `pytest tests/test_auth.py::test_login_sucesso` | Roda apenas um teste |
| `pytest -k refresh` | Roda os testes que têm `refresh` no nome |
| `pytest -x` | Para no primeiro teste que falhar |
| `pytest -s` | Mostra os `print` dos testes |

### Resumo

- Um teste é uma função `test_...` com `assert`.
- As fixtures preparam o que o teste precisa e ficam no `conftest.py`.
- O `pytest-asyncio` permite testar código assíncrono.
- O `pytest-cov` mostra quais linhas do código os testes cobrem.
