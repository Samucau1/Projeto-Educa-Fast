from sqlalchemy import ForeignKey, Integer, String, Text, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SolicitacaoDocumentoModel(Base):
    __tablename__ = "solicitacoes_documentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aluno_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("alunos.id"), nullable=True)
    professor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("professores.id"), nullable=True)
    documento_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("documentos.id"), nullable=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pendente")
    created_at: Mapped[str] = mapped_column(TIMESTAMP, server_default=func.current_timestamp())
    completed_at: Mapped[str | None] = mapped_column(TIMESTAMP, nullable=True)

    aluno = relationship("AlunoModel")
    professor = relationship("ProfessorModel")
    documento = relationship("DocumentoModel")
