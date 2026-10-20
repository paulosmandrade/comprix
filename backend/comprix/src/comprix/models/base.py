from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from sqlalchemy.orm import DeclarativeBase, mapped_column

TIME = ZoneInfo('America/Sao_Paulo')


def time_zone() -> datetime:
    return datetime.now(TIME)


criado = Annotated[datetime, mapped_column(default=time_zone)]
atualizado = Annotated[
    datetime, mapped_column(default=time_zone, onupdate=time_zone)
]


class Base(DeclarativeBase):
    pass
