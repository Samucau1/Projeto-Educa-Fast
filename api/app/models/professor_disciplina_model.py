from sqlalchemy import ForeignKey, Integer, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProfessorDisciplinaModel(Base):
    __tablename__ = "professores_disciplinas"
    __table_args__ = (
        UniqueConstraint("professor_id", "disciplina_id", name="uq_professor_disciplina"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    professor_id: Mapped[int] = mapped_column(Integer, ForeignKey("professores.id"), nullable=False)
    disciplina_id: Mapped[int] = mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    professor = relationship("ProfessorModel")
    disciplina = relationship("DisciplinaModel")
