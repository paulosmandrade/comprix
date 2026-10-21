from datetime import datetime

from sqlalchemy import DateTime, String
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
    senha: Mapped[str] = mapped_column(String(255), nullable=False)
    primeiro_acesso: Mapped[bool] = mapped_column(default=True)
    admin: Mapped[bool] = mapped_column(default=False)
    status: Mapped[bool] = mapped_column(default=True)

    codigo_recuperacao: Mapped[str | None] = mapped_column(
        String(255), default=None
    )
    codigo_expira_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    codigo_tentativas: Mapped[int] = mapped_column(default=0)
