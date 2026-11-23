"""Notas vinculadas à oferta acadêmica e ao período, sem alterar o legado."""
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PeriodoLetivoModel(Base):
    __tablename__ = 'academico_periodos'
    id: Mapped[int] = mapped_column(primary_key=True)
    turma_id: Mapped[int] = mapped_column(ForeignKey('turmas.id'), nullable=False)
    nome: Mapped[str] = mapped_column(String(80))
    ordem: Mapped[int] = mapped_column(Integer)
    media_referencia: Mapped[object] = mapped_column(Numeric(4, 2), default=6)
    fechado: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (UniqueConstraint('turma_id', 'nome', name='uq_periodo_nome'),
                     UniqueConstraint('turma_id', 'ordem', name='uq_periodo_ordem'),
                     CheckConstraint('media_referencia >= 0 AND media_referencia <= 10', name='ck_periodo_media'))


class AvaliacaoModel(Base):
    __tablename__ = 'academico_avaliacoes'
    id: Mapped[int] = mapped_column(primary_key=True)
    turma_disciplina_id: Mapped[int] = mapped_column(ForeignKey('turmas_disciplinas.id'), nullable=False)
    periodo_id: Mapped[int] = mapped_column(ForeignKey('academico_periodos.id'), nullable=False)
    titulo: Mapped[str] = mapped_column(String(150))
    peso: Mapped[object] = mapped_column(Numeric(6, 2), default=1)
    publicada: Mapped[bool] = mapped_column(Boolean, default=False)
    __table_args__ = (CheckConstraint('peso > 0 AND peso <= 100', name='ck_avaliacao_peso'),)


class LancamentoNotaModel(Base):
    __tablename__ = 'academico_notas'
    id: Mapped[int] = mapped_column(primary_key=True)
    avaliacao_id: Mapped[int] = mapped_column(ForeignKey('academico_avaliacoes.id'), nullable=False)
    aluno_id: Mapped[int] = mapped_column(ForeignKey('alunos.id'), nullable=False)
    professor_id: Mapped[int] = mapped_column(ForeignKey('professores.id'), nullable=False)
    valor: Mapped[object] = mapped_column(Numeric(4, 2))
    observacao: Mapped[str] = mapped_column(String(255), default='')
    versao: Mapped[int] = mapped_column(Integer, default=1)
    nota_legada_id: Mapped[int | None] = mapped_column(ForeignKey('notas.id'), unique=True)
    atualizada_em: Mapped[object] = mapped_column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    __table_args__ = (UniqueConstraint('avaliacao_id', 'aluno_id', name='uq_lancamento_aluno'),
                     CheckConstraint('valor >= 0 AND valor <= 10', name='ck_lancamento_valor'))


class AuditoriaAcademicaModel(Base):
    __tablename__ = 'academico_auditoria'
    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey('usuarios.id'), nullable=False)
    acao: Mapped[str] = mapped_column(String(60))
    recurso: Mapped[str] = mapped_column(String(100))
    detalhe: Mapped[str] = mapped_column(Text, default='')
    criada_em: Mapped[object] = mapped_column(DateTime, server_default=func.current_timestamp())
