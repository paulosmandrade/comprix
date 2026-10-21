![Pwdlib](../assets/biblioteca/pwdlib-logo.png#only-light){ width="500" }
![Pwdlib](../assets/biblioteca/pwdlib-logo-dark.png#only-dark){ width="500" }

[pwdlib](https://pypi.org/project/pwdlib/) é uma biblioteca moderna e simples para criar e verificar **hashes de senhas** em Python. Ela foi criada pelo autor do FastAPI Users como substituta do `passlib`, que deixou de ser mantido ativamente e não funciona a partir do Python 3.13.

### Por que fazer hash das senhas

Senhas **nunca** devem ser guardadas no banco como texto. Em vez disso, guardamos o **hash** da senha: um texto gerado a partir dela que não pode ser revertido para a senha original.

No login, a senha digitada passa pelo mesmo processo e o resultado é comparado com o hash salvo. Assim, mesmo que o banco de dados vaze, as senhas dos usuários não ficam expostas.

### Principais características

- **API simples:** apenas dois métodos principais, `hash()` e `verify()`.
- **Algoritmos seguros:** suporta **Argon2** (recomendado) e **Bcrypt**, e não oferece algoritmos antigos e inseguros, como MD5.
- **Implementações confiáveis:** não implementa os algoritmos por conta própria; usa bibliotecas já testadas, como a `argon2-cffi`.
- **Hash com "sal" automático:** cada hash é gerado com um valor aleatório, então a mesma senha gera hashes diferentes a cada vez.

### Instalação

O `[argon2]` instala junto o suporte ao algoritmo Argon2:

```bash
pip install "pwdlib[argon2]"
```

No `pyproject.toml` do projeto, a dependência aparece assim:

```toml
"pwdlib[argon2] (>=0.3.1,<0.4.0)"
```

### Uso básico

```python
from pwdlib import PasswordHash

pwd_context = PasswordHash.recommended()

# Gerar o hash (no cadastro)
senha_hash = pwd_context.hash('minha-senha-secreta')
# '$argon2id$v=19$m=65536,t=3,p=4$...'

# Verificar a senha (no login)
pwd_context.verify('minha-senha-secreta', senha_hash)  # True
pwd_context.verify('senha-errada', senha_hash)  # False
```

O `PasswordHash.recommended()` cria o objeto já configurado com o **Argon2** e os parâmetros recomendados.

### Uso no projeto

O ideal é concentrar o hash de senhas em um único arquivo, como `security.py`:

```python
from pwdlib import PasswordHash

pwd_context = PasswordHash.recommended()


def gerar_hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return pwd_context.verify(senha, senha_hash)
```

No cadastro, o usuário é salvo com o hash, nunca com a senha original:

```python
usuario = Usuario(
    nome=dados.nome,
    email=dados.email,
    senha=gerar_hash_senha(dados.senha),
)
```

No login, a senha recebida é comparada com o hash salvo:

```python
if not verificar_senha(dados.senha, usuario.senha):
    raise HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='E-mail ou senha incorretos',
    )
```

Atenção à ordem dos parâmetros no `verify()`: primeiro a **senha digitada**, depois o **hash salvo**.

### Resumo

- A pwdlib gera e verifica hashes de senhas de forma simples e segura.
- O `PasswordHash.recommended()` usa o Argon2, o algoritmo mais recomendado atualmente.
- O `hash()` é usado no cadastro, e o `verify()`, no login.
- O banco guarda apenas o hash, nunca a senha original.
