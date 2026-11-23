from sqlalchemy import ForeignKey, Integer, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AlunoDisciplinaModel(Base):
    __tablename__ = "alunos_disciplinas"
    __table_args__ = (
        UniqueConstraint("aluno_id", "disciplina_id", name="uq_aluno_disciplina"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(Integer, ForeignKey("alunos.id"), nullable=False)
    disciplina_id: Mapped[int] = mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    aluno = relationship("AlunoModel")
    disciplina = relationship("DisciplinaModel")
