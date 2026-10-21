from pwdlib import PasswordHash

pwd_context = PasswordHash.recommended()


# Criptograda a senha
def get_password_hash(senha: str):
    return pwd_context.hash(senha=senha)


# Verifica senha
def verify_password(senha: str, hashed_password: str):
    return pwd_context.verify(senha, hashed_password)
