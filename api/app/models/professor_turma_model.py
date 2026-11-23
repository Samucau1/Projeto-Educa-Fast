from sqlalchemy import ForeignKey, Integer, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProfessorTurmaModel(Base):
    __tablename__ = "professores_turmas"
    __table_args__ = (
        UniqueConstraint("professor_id", "turma_id", name="uq_professor_turma"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    professor_id: Mapped[int] = mapped_column(Integer, ForeignKey("professores.id"), nullable=False)
    turma_id: Mapped[int] = mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    professor = relationship("ProfessorModel")
    turma = relationship("TurmaModel")
