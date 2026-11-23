from sqlalchemy import ForeignKey, Integer, String, TIMESTAMP, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AtividadeModel(Base):
    __tablename__ = "atividades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    professor_id: Mapped[int] = mapped_column(Integer, ForeignKey("professores.id"), nullable=False)
    turma_id: Mapped[int] = mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)
    disciplina_id: Mapped[int] = mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_entrega: Mapped[str | None] = mapped_column(String(10), nullable=True)
    caminho_arquivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    professor = relationship("ProfessorModel")
    turma = relationship("TurmaModel")
    disciplina = relationship("DisciplinaModel")
