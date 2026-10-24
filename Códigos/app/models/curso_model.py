"""Material reutilizável, separado das ofertas anuais e do progresso."""
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class MigracaoSchemaModel(Base):
    __tablename__ = 'educafast_migracoes'
    versao: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)


class CursoModel(Base):
    __tablename__ = 'cursos'
    id: Mapped[int] = mapped_column(primary_key=True)
    disciplina_id: Mapped[int] = mapped_column(ForeignKey('disciplinas.id'), nullable=False)
    professor_id: Mapped[int] = mapped_column(ForeignKey('professores.id'), nullable=False)
    origem_id: Mapped[int | None] = mapped_column(ForeignKey('cursos.id'))
    titulo: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str] = mapped_column(Text, default='')
    estado: Mapped[str] = mapped_column(String(20), default='rascunho')
    __table_args__ = (CheckConstraint("estado IN ('rascunho','publicado','arquivado')", name='ck_curso_estado'),)


class CapituloModel(Base):
    __tablename__ = 'curso_capitulos'
    id: Mapped[int] = mapped_column(primary_key=True)
    curso_id: Mapped[int] = mapped_column(ForeignKey('cursos.id'), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150))
    posicao: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint('curso_id', 'posicao', name='uq_capitulo_posicao'),)


class TemaModel(Base):
    __tablename__ = 'curso_temas'
    id: Mapped[int] = mapped_column(primary_key=True)
    capitulo_id: Mapped[int] = mapped_column(ForeignKey('curso_capitulos.id'), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150))
    posicao: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint('capitulo_id', 'posicao', name='uq_tema_posicao'),)


class AulaModel(Base):
    __tablename__ = 'curso_aulas'
    id: Mapped[int] = mapped_column(primary_key=True)
    tema_id: Mapped[int] = mapped_column(ForeignKey('curso_temas.id'), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150))
    descricao: Mapped[str] = mapped_column(Text, default='')
    video_id: Mapped[str] = mapped_column(String(11))
    posicao: Mapped[int] = mapped_column(Integer)
    __table_args__ = (UniqueConstraint('tema_id', 'posicao', name='uq_aula_posicao'),)


class AtribuicaoDocenteModel(Base):
    __tablename__ = 'atribuicoes_docentes'
    id: Mapped[int] = mapped_column(primary_key=True)
    professor_id: Mapped[int] = mapped_column(ForeignKey('professores.id'), nullable=False)
    turma_disciplina_id: Mapped[int] = mapped_column(ForeignKey('turmas_disciplinas.id'), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint('professor_id', 'turma_disciplina_id', name='uq_atribuicao_docente'),)


class EstadoTurmaModel(Base):
    __tablename__ = 'turma_estados'
    turma_id: Mapped[int] = mapped_column(ForeignKey('turmas.id'), primary_key=True)
    arquivada: Mapped[bool] = mapped_column(Boolean, default=False)


class OfertaCursoModel(Base):
    __tablename__ = 'curso_ofertas'
    id: Mapped[int] = mapped_column(primary_key=True)
    curso_id: Mapped[int] = mapped_column(ForeignKey('cursos.id'), nullable=False)
    turma_disciplina_id: Mapped[int] = mapped_column(ForeignKey('turmas_disciplinas.id'), nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint('curso_id', 'turma_disciplina_id', name='uq_curso_oferta'),)


class ProgressoAulaModel(Base):
    __tablename__ = 'curso_progressos'
    id: Mapped[int] = mapped_column(primary_key=True)
    aluno_id: Mapped[int] = mapped_column(ForeignKey('alunos.id'), nullable=False)
    oferta_id: Mapped[int] = mapped_column(ForeignKey('curso_ofertas.id'), nullable=False)
    aula_id: Mapped[int] = mapped_column(ForeignKey('curso_aulas.id'), nullable=False)
    concluida_em: Mapped[object] = mapped_column(DateTime, server_default=func.current_timestamp())
    __table_args__ = (UniqueConstraint('aluno_id', 'oferta_id', 'aula_id', name='uq_progresso_oferta_aula'),)


class AuditoriaCursoModel(Base):
    __tablename__ = 'curso_auditoria'
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'), nullable=False)
    acao: Mapped[str] = mapped_column(String(60))
    recurso: Mapped[str] = mapped_column(String(120))
    criada_em: Mapped[object] = mapped_column(DateTime, server_default=func.current_timestamp())
