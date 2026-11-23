from sqlalchemy import ForeignKey, Integer, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlunoTurmaModel(Base):
    __tablename__ = "alunos_turmas"
    __table_args__ = (
        UniqueConstraint("aluno_id", "turma_id", name="uq_aluno_turma"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(Integer, ForeignKey("alunos.id"), nullable=False)
    turma_id: Mapped[int] = mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    aluno = relationship("AlunoModel")
    turma = relationship("TurmaModel", back_populates="alunos")
