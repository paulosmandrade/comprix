from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioSchema(BaseModel):
    """Dados para criar um usuário."""

    nome: str = Field(max_length=50)
    email: EmailStr = Field(max_length=100)


class UsuarioUpdateSchema(BaseModel):
    """Dados para atualizar um usuário (todos opcionais)."""

    nome: str | None = Field(None, max_length=50)
    email: EmailStr | None = Field(None, max_length=100)
    senha: str | None = Field(None, min_length=8)
    status: bool | None = None


class UsuarioPublico(BaseModel):
    """Dados devolvidos pela API (sem a senha)."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: EmailStr
    status: bool


class UsuarioLista(BaseModel):
    """Lista de usuários devolvida pela API."""

    usuarios: list[UsuarioPublico]


class NovaSenhaBase(BaseModel):
    """Regra da nova senha, compartilhada pelos schemas abaixo."""

    nova_senha: str = Field(min_length=8)


class DefinirSenhaSchema(NovaSenhaBase):
    """Dados para o usuário definir a senha pelo link."""

    token: str


class RedefinirSenhaSchema(NovaSenhaBase):
    """Usuario que esqueceu a senah redefine com o código do e-mail"""

    email: EmailStr
    codigo: str = Field(pattern=r'^\d{6}$')


class EsqueciSenhaSchema(BaseModel):
    """E-mail de quem esqueceu a senha."""

    email: EmailStr
