from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TurmaModel(Base):
    __tablename__ = "turmas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    codigo: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    ano_letivo: Mapped[int] = mapped_column(Integer, nullable=False)
    turno: Mapped[str | None] = mapped_column(String(30), nullable=True)

    alunos = relationship("AlunoTurmaModel", back_populates="turma")
    disciplinas = relationship("TurmaDisciplinaModel", back_populates="turma")
