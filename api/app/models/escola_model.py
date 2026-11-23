"""Configuração institucional versionada, independente de dados acadêmicos antigos."""
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class IdentidadeEscolaModel(Base):
    __tablename__ = 'escola_identidade'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    versao: Mapped[int] = mapped_column(Integer, default=1)
    dados: Mapped[str] = mapped_column(Text)


class CalendarioEscolaModel(Base):
    __tablename__ = 'escola_calendarios'
    id: Mapped[int] = mapped_column(primary_key=True)
    ano: Mapped[int] = mapped_column(Integer, unique=True)
    nome: Mapped[str] = mapped_column(String(120))
    inicio: Mapped[object] = mapped_column(Date)
    fim: Mapped[object] = mapped_column(Date)
    dias_semana: Mapped[str] = mapped_column(String(30), default='[0,1,2,3,4]')
    meta_letivos: Mapped[int] = mapped_column(Integer, default=200)
    versao: Mapped[int] = mapped_column(Integer, default=1)


class EventoCalendarioModel(Base):
    __tablename__ = 'escola_eventos'
    id: Mapped[int] = mapped_column(primary_key=True)
    calendario_id: Mapped[int] = mapped_column(ForeignKey('escola_calendarios.id'), nullable=False)
    dia: Mapped[object] = mapped_column(Date)
    titulo: Mapped[str] = mapped_column(String(150))
    tipo: Mapped[str] = mapped_column(String(20))
    __table_args__ = (UniqueConstraint('calendario_id', 'dia', name='uq_evento_calendario_dia'),)


class PoliticaEscolaModel(Base):
    __tablename__ = 'escola_politicas'
    id: Mapped[int] = mapped_column(primary_key=True)
    calendario_id: Mapped[int] = mapped_column(ForeignKey('escola_calendarios.id'), nullable=False)
    nome: Mapped[str] = mapped_column(String(120))
    configuracao: Mapped[str] = mapped_column(Text)


class RegraTurmaEscolaModel(Base):
    __tablename__ = 'escola_regras_turmas'
    turma_id: Mapped[int] = mapped_column(ForeignKey('turmas.id'), primary_key=True)
    politica_id: Mapped[int] = mapped_column(ForeignKey('escola_politicas.id'), nullable=False)


class RegraPeriodoEscolaModel(Base):
    __tablename__ = 'escola_regras_periodos'
    periodo_id: Mapped[int] = mapped_column(ForeignKey('academico_periodos.id'), primary_key=True)
    politica_id: Mapped[int] = mapped_column(ForeignKey('escola_politicas.id'), nullable=False)
    ordem: Mapped[int] = mapped_column(Integer)
