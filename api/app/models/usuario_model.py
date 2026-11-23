from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    senha: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)

    professor = relationship("ProfessorModel", back_populates="usuario", uselist=False)
    aluno = relationship("AlunoModel", back_populates="usuario", uselist=False)
