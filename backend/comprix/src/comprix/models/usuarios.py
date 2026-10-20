from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from comprix.models.base import Base, atualizado, criado


class Usuarios(Base):
    __tablename__ = 'usuarios'
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[criado]
    updated_at: Mapped[atualizado]
    nome: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    senha: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[str] = mapped_column(String(6), nullable=False)
    primeiro_acesso: Mapped[bool] = mapped_column(default=True)
    status: Mapped[bool] = mapped_column(default=True)
