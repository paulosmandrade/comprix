---
icon: lucide/sliders-horizontal
title: Settings
---

# :lucide-sliders-horizontal: Settings (configurações)

Endereço do banco, chave secreta dos tokens, dados do administrador, servidor
de e-mail... Tudo o que muda de um ambiente para outro, ou que é secreto, fica
**fora do código**, no arquivo `.env`. O `settings.py` lê esse arquivo e
entrega as configurações já **validadas** para o resto do projeto.

Esta página reúne todas as configurações do Comprix em um só lugar. Cada uma
é explicada em detalhes na página onde foi criada.

## O `settings.py`

```python title="src/comprix/settings.py" linenums="1"
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str = Field(init=False)
    ADMIN_USER: str = Field(init=False)
    ADMIN_EMAIL: str = Field(init=False)
    ADMIN_SENHA: str = Field(init=False)
    SECRET_KEY: str = Field(init=False)
    ALGORITHM: str = Field(init=False)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(init=False)

    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: str
    MAIL_SERVER: str
    MAIL_PORT: int
    FRONTEND_URL: str
```

- **Linhas 6 a 8:** as configurações são lidas do arquivo `.env`, com
  codificação UTF-8. Variáveis de ambiente do sistema com o mesmo nome têm
  prioridade sobre o `.env`.
- **Linhas 10 a 23:** cada atributo é uma configuração. O tipo é validado: o
  `ACCESS_TOKEN_EXPIRE_MINUTES="60"` do `.env` vira o número `60`, e um valor
  como `"sessenta"` faz a aplicação parar com um erro claro.
- **Linha 19:** o `MAIL_PASSWORD` usa `SecretStr`, que esconde a senha em
  logs e tracebacks (aparece como `'**********'`). O valor real é lido com
  `.get_secret_value()`.
- Nenhum campo tem valor padrão, então **todos são obrigatórios**. Se algum
  faltar no `.env`, a API para logo ao iniciar com um `ValidationError`.

??? info "Para que serve o `Field(init=False)`?"
    É uma dica para o editor: indica que o valor não é passado ao criar o
    objeto (`Settings()`), e sim lido do ambiente. Assim, o editor deixa de
    sublinhar o `Settings()` reclamando de argumentos faltando. Para o
    pydantic-settings, o comportamento é o mesmo de um campo sem `Field`.

## Todas as variáveis

| Variável | Exemplo | Para que serve | Página |
|---|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///comprix.db` | Endereço do banco de dados | [Sqlite - Models](sqlite.md) |
| `ADMIN_USER` | `Administrador` | Nome do administrador criado automaticamente | [Usuários](routers/usuarios.md) |
| `ADMIN_EMAIL` | `admin@seudominio.com.br` | E-mail (login) do administrador | [Usuários](routers/usuarios.md) |
| `ADMIN_SENHA` | `senha_do_admin` | Senha inicial do administrador | [Usuários](routers/usuarios.md) |
| `SECRET_KEY` | (texto aleatório e longo) | Chave que assina os tokens JWT | [Token](seguranca/token.md) |
| `ALGORITHM` | `HS256` | Algoritmo de assinatura dos tokens | [Token](seguranca/token.md) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Validade do token de acesso, em minutos | [Token](seguranca/token.md) |
| `MAIL_USERNAME` | `contato@seudominio.com.br` | Usuário do servidor de e-mail | [Usuários](routers/usuarios.md) |
| `MAIL_PASSWORD` | `senha_da_caixa_de_email` | Senha do servidor de e-mail | [Usuários](routers/usuarios.md) |
| `MAIL_FROM` | `contato@seudominio.com.br` | Remetente dos e-mails (igual ao `MAIL_USERNAME`) | [Usuários](routers/usuarios.md) |
| `MAIL_SERVER` | `smtp.hostinger.com` | Servidor SMTP | [Usuários](routers/usuarios.md) |
| `MAIL_PORT` | `587` | Porta SMTP: `587` (STARTTLS) ou `465` (SSL) | [Usuários](routers/usuarios.md) |
| `FRONTEND_URL` | `http://localhost:5173` | Endereço do frontend, usado no link do e-mail | [Usuários](routers/usuarios.md) |

!!! tip "Gerando uma `SECRET_KEY` segura"
    Nunca use um texto fácil de adivinhar. Gere uma chave aleatória com o
    próprio Python:

    ```console title="Terminal"
    $ python -c "import secrets; print(secrets.token_urlsafe(64))"
    ```

## O `.env.example`

O `.env` **nunca** vai para o Git. Para quem baixar o projeto saber quais
variáveis precisa preencher, mantemos o `.env.example`, com **todas** as
variáveis e nenhum valor secreto:

```bash title=".env.example"
DATABASE_URL="sqlite+aiosqlite:///comprix.db"

ADMIN_USER="Master"
ADMIN_EMAIL="seuemail@comprix.com.br"
ADMIN_SENHA="sua_senha"

ACCESS_TOKEN_EXPIRE_MINUTES="60"
SECRET_KEY="criar uma chave de segurança"
ALGORITHM="HS256"

MAIL_USERNAME="contato@seudominio.com.br"
MAIL_PASSWORD="senha_da_caixa_de_email"
MAIL_FROM="contato@seudominio.com.br"
MAIL_SERVER="smtp.seudominio.com.br"
MAIL_PORT="587"

FRONTEND_URL="http://localhost:5173"
```

Quem baixar o projeto só precisa copiá-lo e preencher os valores:

```console title="Terminal"
$ cp .env.example .env
```

!!! warning "Toda variável nova vai para os dois arquivos"
    Sempre que uma configuração nova for criada no `settings.py`, ela precisa
    ser acrescentada no `.env` **e** no `.env.example`.

## Usando as configurações

Basta criar o objeto e acessar os atributos:

```python
from comprix.settings import Settings

settings = Settings()

settings.DATABASE_URL  # 'sqlite+aiosqlite:///comprix.db'
settings.ACCESS_TOKEN_EXPIRE_MINUTES  # 60 (int, não texto)
```

No projeto, cada módulo cria o seu `settings = Settings()` uma única vez, no
topo do arquivo, e o reaproveita em todas as funções.

!!! warning "O `.env` só é lido quando a API sobe"
    Depois de alterar o `.env`, **pare e suba a API de novo**. O recarregamento
    automático do `fastapi dev` só reinicia quando um arquivo `.py` muda.
