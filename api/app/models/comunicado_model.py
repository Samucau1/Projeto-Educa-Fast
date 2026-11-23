from sqlalchemy import Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComunicadoModel(Base):
    __tablename__ = "comunicados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    destinatario: Mapped[str] = mapped_column(String(80), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    criado_por: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
