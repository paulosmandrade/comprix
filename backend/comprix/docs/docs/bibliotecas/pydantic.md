![Pydantic](https://cdn.simpleicons.org/pydantic){ width="80" }

O **Pydantic** é uma biblioteca Python para **validação de dados** usando *type hints* (as anotações de tipo do Python). Em vez de escrever vários `if` para checar se um dado está correto, descrevemos o formato esperado em uma classe e o Pydantic valida, converte e informa os erros automaticamente.

No projeto, ele é usado em dois lugares:

- **`schemas/`**: define o formato dos dados que entram e saem da API;
- **`settings.py`**: carrega e valida as variáveis de ambiente do `.env` (com o pacote `pydantic-settings`).

O FastAPI é construído sobre o Pydantic, então toda validação de requisições e respostas da API passa por ele.

### Instalação

```bash
pip install pydantic pydantic-settings "pydantic[email]"
```

- `pydantic`: a biblioteca principal (já vem como dependência do FastAPI);
- `pydantic-settings`: leitura de configurações e variáveis de ambiente;
- `pydantic[email]`: habilita o tipo `EmailStr` para validar e-mails.

### Criando um schema

Um schema é uma classe que herda de `BaseModel`. Cada atributo tem um tipo, e o Pydantic garante que os dados sigam esse tipo.

```python
from pydantic import BaseModel, EmailStr


class UsuarioSchema(BaseModel):
    nome: str
    email: EmailStr
    senha: str
```

Ao criar um objeto, os dados são validados na hora:

```python
usuario = UsuarioSchema(nome='Paulo', email='paulo@email.com', senha='123456')
print(usuario.nome)  # Paulo
```

Se algum dado estiver errado, o Pydantic lança um `ValidationError` explicando o problema:

```python
UsuarioSchema(nome='Paulo', email='email-invalido', senha='123456')
# ValidationError: email - value is not a valid email address
```

### Conversão de tipos

Quando possível, o Pydantic converte o valor para o tipo declarado:

```python
class Produto(BaseModel):
    preco: float
    quantidade: int


Produto(preco='19.90', quantidade='3')
# Produto(preco=19.9, quantidade=3)
```

Se a conversão não for possível (por exemplo, `quantidade='três'`), ocorre um erro de validação.

### Campos opcionais e valores padrão

```python
from pydantic import BaseModel


class Produto(BaseModel):
    nome: str
    descricao: str | None = None  # opcional
    ativo: bool = True  # valor padrão
```

### Regras de validação com `Field`

O `Field` permite adicionar regras e informações extras a um campo:

```python
from pydantic import BaseModel, Field


class Produto(BaseModel):
    nome: str = Field(min_length=3, max_length=100)
    preco: float = Field(gt=0, description='Preço em reais')
    quantidade: int = Field(ge=0, default=0)
```

| Parâmetro | Significado |
|---|---|
| `gt` / `ge` | maior que / maior ou igual a |
| `lt` / `le` | menor que / menor ou igual a |
| `min_length` / `max_length` | tamanho mínimo / máximo do texto |
| `default` | valor padrão |
| `description` | descrição exibida na documentação da API |

### Validações personalizadas

Quando as regras do `Field` não bastam, usamos `field_validator`:

```python
from pydantic import BaseModel, field_validator


class UsuarioSchema(BaseModel):
    nome: str
    senha: str

    @field_validator('senha')
    @classmethod
    def senha_forte(cls, valor: str) -> str:
        if len(valor) < 8:
            raise ValueError('A senha deve ter pelo menos 8 caracteres')
        return valor
```

### Schemas de entrada e de saída

É uma boa prática separar o que **entra** na API do que **sai** dela. A senha, por exemplo, é recebida no cadastro, mas nunca deve ser devolvida na resposta.

```python
from pydantic import BaseModel, ConfigDict, EmailStr


class UsuarioSchema(BaseModel):
    """Dados recebidos para criar um usuário."""

    nome: str
    email: EmailStr
    senha: str


class UsuarioPublico(BaseModel):
    """Dados devolvidos pela API (sem a senha)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
```

O `from_attributes=True` permite criar o schema a partir de um objeto do SQLAlchemy (o modelo `Usuario`), lendo os atributos do objeto em vez de um dicionário:

```python
usuario_publico = UsuarioPublico.model_validate(usuario_do_banco)
```

### Uso no FastAPI

O FastAPI usa os schemas para validar o corpo da requisição e filtrar a resposta:

```python
from http import HTTPStatus

from fastapi import FastAPI

app = FastAPI()


@app.post(
    '/usuarios/',
    status_code=HTTPStatus.CREATED,
    response_model=UsuarioPublico,
)
def criar_usuario(usuario: UsuarioSchema): ...
```

- O parâmetro `usuario: UsuarioSchema` faz o FastAPI validar o JSON recebido. Se estiver inválido, a API responde automaticamente com status **422** e a descrição do erro.
- O `response_model=UsuarioPublico` garante que a resposta só contenha os campos do schema público, sem a senha.
- Os schemas também aparecem na documentação automática da API, em `/docs`.

### Métodos mais usados

| Método | O que faz |
|---|---|
| `model_dump()` | converte o objeto em dicionário |
| `model_dump_json()` | converte o objeto em texto JSON |
| `model_validate(dados)` | cria o objeto a partir de um dicionário ou de outro objeto |
| `model_validate_json(texto)` | cria o objeto a partir de um texto JSON |

```python
usuario = UsuarioSchema(
    nome='Paulo', email='paulo@email.com', senha='12345678'
)

usuario.model_dump()
# {'nome': 'Paulo', 'email': 'paulo@email.com', 'senha': '12345678'}

usuario.model_dump(exclude={'senha'})
# {'nome': 'Paulo', 'email': 'paulo@email.com'}
```

### Configurações com `pydantic-settings`

O `pydantic-settings` lê as variáveis de ambiente e o arquivo `.env`, validando cada valor como em um schema comum:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
    )

    DATABASE_URL: str
```

Com o `.env`:

```env
DATABASE_URL="sqlite+aiosqlite:///database.db"
```

Basta instanciar a classe para ter acesso às configurações:

```python
from comprix.settings import Settings

Settings().DATABASE_URL
```

Se uma variável obrigatória estiver faltando, a aplicação já falha na inicialização com uma mensagem clara, em vez de quebrar mais tarde em algum ponto do código.

### Resumo

- O Pydantic valida e converte dados a partir dos tipos declarados nas classes.
- Os schemas ficam em `schemas/` e definem o formato dos dados da API.
- Separar schemas de entrada e de saída evita expor dados sensíveis, como senhas.
- O `from_attributes=True` permite converter modelos do SQLAlchemy em schemas.
- O `pydantic-settings` centraliza e valida as configurações do `.env`.
