from sqlalchemy import ForeignKey, Integer, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TurmaDisciplinaModel(Base):
    __tablename__ = "turmas_disciplinas"
    __table_args__ = (
        UniqueConstraint("turma_id", "disciplina_id", name="uq_turma_disciplina"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    turma_id: Mapped[int] = mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)
    disciplina_id: Mapped[int] = mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    turma = relationship("TurmaModel", back_populates="disciplinas")
    disciplina = relationship("DisciplinaModel")
