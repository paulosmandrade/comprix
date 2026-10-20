---
icon: lucide/database-zap
---

# :material-database-cog: Configurando o banco de dados

Agora que já sabemos o que é um banco de dados e por que escolhemos o SQLite, vamos colocá-lo para funcionar no Comprix. Para isso, vamos usar três peças que trabalham juntas:

| Ferramenta | Papel no projeto |
|---|---|
| **SQLite** | O banco de dados em si: um único arquivo `.db` onde os dados ficam guardados |
| **SQLAlchemy** | Conecta no banco e permite criar tabelas e consultar dados usando classes Python |
| **pydantic-settings** | Lê e valida as configurações do projeto, como o endereço do banco |


O SQLite já vem com o Python, então só precisamos instalar as outras duas.

## Instalando as dependências

No terminal, dentro da pasta do projeto, rode:

```console title="Terminal"
$ poetry add sqlalchemy pydantic-settings
```

O Poetry baixa as bibliotecas, adiciona as duas no `pyproject.toml` e atualiza o `poetry.lock`.

## Guardando as configurações no `.env`

O endereço do banco é uma **configuração**, e configurações não devem ficar escritas direto no código. Se um dia quisermos usar outro banco, basta trocar a configuração, sem mexer em nenhuma linha de Python.

Crie um arquivo chamado `.env` na raiz do projeto, na mesma pasta do `pyproject.toml`:

```bash title=".env"
DATABASE_URL="sqlite:///database.db"
```

Esse endereço segue o formato `banco:///caminho`. Aqui, ele diz para usar o **SQLite** com um arquivo chamado `database.db`.

!!! danger "O `.env` não vai para o Git"
    O `.env` pode guardar senhas e chaves secretas no futuro. Por isso, ele **nunca** deve ser enviado para o GitHub. O mesmo vale para o arquivo do banco, que guarda os dados. Adicione estas linhas ao `.gitignore`:

    ```
    .env
    *.db
    ```

## Lendo as configurações com o pydantic-settings

Agora vamos criar a classe que lê o `.env`:

```python title="src/comprix/settings.py" linenums="1"
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    DATABASE_URL: str
```

- **Linha 1:** importamos a classe `BaseSettings`, que funciona como o `BaseModel` dos schemas, mas lê os dados do ambiente, e a `SettingsConfigDict`, que configura de onde ler.

- **Linhas 5 a 7:** dizemos que as configurações vêm do arquivo `.env`, com codificação UTF-8.

- **Linha 9:** declaramos a configuração `DATABASE_URL`, do tipo texto. Como ela não tem valor padrão, é **obrigatória**: se ela não existir no `.env`, a aplicação para logo ao iniciar, com uma mensagem clara de erro.

??? info "Por que o editor sublinha o `Settings()`?"
    Em alguns editores, o `Settings()` aparece sublinhado com o aviso de que falta o argumento `DATABASE_URL`. Isso acontece porque o editor não sabe que o valor virá do `.env`. O código funciona normalmente.

## Criando a primeira tabela com o SQLAlchemy

No SQLAlchemy, cada tabela do banco é representada por uma classe Python, chamada de **model**. Vamos criar a tabela de usuarios:

