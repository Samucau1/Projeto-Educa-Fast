from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from app.crypto import EncryptedText, EncryptedDate, cpf_index

from app.database import Base


class AlunoModel(Base):
    __tablename__ = "alunos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("usuarios.id"),
        unique=True,
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    cpf: Mapped[str | None] = mapped_column(EncryptedText(), nullable=True)
    cpf_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    matricula: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    curso_serie: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status_matricula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    foto_perfil: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_nascimento: Mapped[date | None] = mapped_column(EncryptedDate(), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    usuario = relationship("UsuarioModel", back_populates="aluno")
    @validates("cpf")
    def proteger_cpf(self, key, value):
        self.cpf_hash = cpf_index(value)
        return value
    documentos = relationship("DocumentoModel", back_populates="aluno")
    notas = relationship("NotaModel", back_populates="aluno")
