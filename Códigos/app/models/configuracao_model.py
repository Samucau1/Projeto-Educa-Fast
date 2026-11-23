from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ConfiguracaoModel(Base):
    __tablename__ = "configuracoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cor_fundo: Mapped[str] = mapped_column(String(7), default="#06385d")
    cor_destaque: Mapped[str] = mapped_column(String(7), default="#22d3ee")
