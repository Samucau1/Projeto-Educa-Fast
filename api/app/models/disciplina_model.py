from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DisciplinaModel(Base):
    __tablename__ = "disciplinas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    carga_horaria: Mapped[int] = mapped_column(Integer, nullable=False)

    documentos = relationship("DocumentoModel", back_populates="disciplina")
    notas = relationship("NotaModel", back_populates="disciplina")
