from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.crypto import EncryptedLongText


class PedidoPrivacidadeModel(Base):
    __tablename__ = "pedidos_privacidade"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    detalhe: Mapped[str] = mapped_column(EncryptedLongText(), default="")
    status: Mapped[str] = mapped_column(String(20), default="aberto")
    resposta: Mapped[str] = mapped_column(EncryptedLongText(), default="")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditoriaPrivacidadeModel(Base):
    __tablename__ = "auditoria_privacidade"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ator_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    acao: Mapped[str] = mapped_column(String(50), nullable=False)
    referencia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class LimiteLoginModel(Base):
    __tablename__ = "limites_login"
    chave: Mapped[str] = mapped_column(String(64), primary_key=True)
    janela: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tentativas: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
