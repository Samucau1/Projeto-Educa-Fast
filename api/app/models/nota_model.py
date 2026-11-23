from sqlalchemy import DECIMAL, ForeignKey, Integer, String, TIMESTAMP, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotaModel(Base):
    __tablename__ = "notas"
    __table_args__ = (UniqueConstraint("aluno_id", "disciplina_id", name="uq_nota_aluno_disciplina"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aluno_id: Mapped[int] = mapped_column(Integer, ForeignKey("alunos.id"), nullable=False)
    disciplina_id: Mapped[int] = mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    professor_id: Mapped[int] = mapped_column(Integer, ForeignKey("professores.id"), nullable=False)
    nota: Mapped[float] = mapped_column(DECIMAL(4, 2), nullable=False)
    observacao: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_lancamento: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())

    aluno = relationship("AlunoModel", back_populates="notas")
    disciplina = relationship("DisciplinaModel", back_populates="notas")
    professor = relationship("ProfessorModel", back_populates="notas")
