"""Várias escolas no mesmo servidor: cada escola tem o próprio schema no Postgres.

Organização do banco:

* ``plataforma``: tabelas do dono da plataforma (ADM Supremo). Guarda as escolas, o diretório
  de logins (e-mail -> escola) e os operadores. Nenhuma escola lê ou escreve aqui.
* ``public``: a escola padrão. Instalações antigas, de uma escola só, continuam funcionando sem
  mudança nenhuma.
* ``escola_<slug>``: uma área por escola criada pelo ADM Supremo, com o mesmo conjunto de tabelas.

Cada requisição usa somente o schema da escola da sessão: ``get_session()`` aplica um
``schema_translate_map``, então as consultas ORM da aplicação não precisam saber em que escola estão.
No SQLite (testes rápidos) não existe schema: o modo multiescola fica desligado e tudo usa a escola única.
"""
import json
import logging
import re
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, event, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

log = logging.getLogger(__name__)

SCHEMA_PLATAFORMA = "plataforma"
SCHEMA_PADRAO = "public"
SLUG_VALIDO = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])$")
SCHEMA_VALIDO = re.compile(r"^(public|escola_[a-z0-9_]{3,40})$")


class PlataformaBase(DeclarativeBase):
    """Metadados separados: o create_all das escolas nunca toca nas tabelas da plataforma."""


class EscolaModel(PlataformaBase):
    __tablename__ = "escolas"
    __table_args__ = {"schema": SCHEMA_PLATAFORMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    schema_nome: Mapped[str] = mapped_column(String(63), unique=True, nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
                                                default=lambda: datetime.now(timezone.utc))


class ContaModel(PlataformaBase):
    """Diretório de logins: um e-mail pertence a uma única escola em toda a plataforma."""
    __tablename__ = "contas"
    __table_args__ = {"schema": SCHEMA_PLATAFORMA}

    email: Mapped[str] = mapped_column(String(120), primary_key=True)
    escola_id: Mapped[int] = mapped_column(ForeignKey(f"{SCHEMA_PLATAFORMA}.escolas.id"), nullable=False, index=True)


class OperadorModel(PlataformaBase):
    """ADM Supremo: dono da plataforma. Não é usuário de nenhuma escola."""
    __tablename__ = "operadores"
    __table_args__ = {"schema": SCHEMA_PLATAFORMA}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    senha: Mapped[str] = mapped_column(String(200), nullable=False)


def multiescola_ativo(engine):
    return engine.dialect.name == "postgresql"


def normalizar_email(email):
    return (email or "").strip().lower()


def schema_da_escola(slug):
    return "escola_" + slug.replace("-", "_")


def validar_schema(schema):
    if not isinstance(schema, str) or not SCHEMA_VALIDO.match(schema):
        raise ValueError(f"Schema de escola inválido: {schema!r}")
    return schema


def schema_da_requisicao():
    """Schema da escola desta requisição (JWT ou sessão). None = escola padrão."""
    from flask import g, has_request_context, session
    if not has_request_context():
        return None
    schema = g.get("escola_schema") or session.get("escola_schema")
    if not schema or schema == SCHEMA_PADRAO:
        return None
    return validar_schema(schema)


# ---------- Plataforma ----------

def preparar_plataforma(engine, inicializar_escola):
    """Cria o schema da plataforma, registra a escola padrão e atualiza todas as escolas."""
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_PLATAFORMA}"))
        PlataformaBase.metadata.create_all(conn)
        padrao = conn.execute(select(EscolaModel.id).where(EscolaModel.schema_nome == SCHEMA_PADRAO)).scalar()
        if padrao is None:
            conn.execute(EscolaModel.__table__.insert().values(
                slug="padrao", nome="Escola padrão", schema_nome=SCHEMA_PADRAO, ativa=True,
                criada_em=datetime.now(timezone.utc)))
        escolas = conn.execute(select(EscolaModel.id, EscolaModel.schema_nome)).all()
    for escola_id, schema in escolas:
        if schema != SCHEMA_PADRAO:
            # Escolas existentes recebem tabelas novas quando a aplicação é atualizada.
            with engine.begin() as conn:
                inicializar_escola(conn.execution_options(schema_translate_map={None: schema}), schema)
        sincronizar_diretorio(engine, escola_id, schema)


def sincronizar_diretorio(engine, escola_id, schema):
    """Registra no diretório os e-mails já existentes na escola (instalações anteriores)."""
    usuarios = f'"{validar_schema(schema)}".usuarios'
    with engine.begin() as conn:
        existe = conn.execute(text("SELECT to_regclass(:t)"), {"t": usuarios}).scalar()
        if not existe:
            return
        conn.execute(text(
            f"INSERT INTO {SCHEMA_PLATAFORMA}.contas (email, escola_id) "
            f"SELECT DISTINCT lower(trim(email)), :escola FROM {usuarios} "
            "ON CONFLICT (email) DO NOTHING"), {"escola": escola_id})


def id_da_escola(conn, schema):
    return conn.execute(select(EscolaModel.id).where(EscolaModel.schema_nome == (schema or SCHEMA_PADRAO))).scalar()


def escola_do_email(engine, email):
    """Escola ativa dona do e-mail, ou None."""
    with Session(engine) as db:
        return db.execute(select(EscolaModel).join(ContaModel, ContaModel.escola_id == EscolaModel.id)
                          .where(ContaModel.email == normalizar_email(email), EscolaModel.ativa.is_(True))).scalar()


def escola_ativa(engine, schema):
    with Session(engine) as db:
        return db.execute(select(EscolaModel.id).where(EscolaModel.schema_nome == schema,
                                                       EscolaModel.ativa.is_(True))).scalar() is not None


# ---------- Diretório de logins, mantido automaticamente ----------

def _registrar_conta(conn, email, escola_id):
    """Grava e-mail -> escola. Recusa e-mail que já pertence a outra escola."""
    gravado = conn.execute(text(
        f"INSERT INTO {SCHEMA_PLATAFORMA}.contas (email, escola_id) VALUES (:email, :escola) "
        "ON CONFLICT (email) DO UPDATE SET escola_id = EXCLUDED.escola_id "
        f"WHERE {SCHEMA_PLATAFORMA}.contas.escola_id = EXCLUDED.escola_id RETURNING email"),
        {"email": email, "escola": escola_id}).scalar()
    if gravado is None:
        raise IntegrityError("diretório de contas", {"email": email},
                             Exception("E-mail já cadastrado em outra escola da plataforma"))


def _remover_conta(conn, email, escola_id):
    conn.execute(text(f"DELETE FROM {SCHEMA_PLATAFORMA}.contas WHERE email = :email AND escola_id = :escola"),
                 {"email": email, "escola": escola_id})


def instalar_diretorio(session_factory):
    """Mantém plataforma.contas em dia sempre que um usuário de escola é criado, muda ou sai."""
    from sqlalchemy import inspect as sa_inspect

    @event.listens_for(session_factory, "before_flush")
    def _antes_de_gravar(session, _context, _instances):
        if not session.info.get("multiescola"):
            return
        from app.models import UsuarioModel
        mudancas = []
        for obj in session.new:
            if isinstance(obj, UsuarioModel):
                mudancas.append((None, obj.email))
        for obj in session.dirty:
            if isinstance(obj, UsuarioModel):
                historico = sa_inspect(obj).attrs.email.history
                if historico.has_changes():
                    antigo = historico.deleted[0] if historico.deleted else None
                    mudancas.append((antigo, obj.email))
        for obj in session.deleted:
            if isinstance(obj, UsuarioModel):
                mudancas.append((obj.email, None))
        if not mudancas:
            return
        conn = session.connection()
        escola_id = id_da_escola(conn, session.info.get("escola_schema"))
        if escola_id is None:
            raise RuntimeError("Escola desta sessão não está registrada na plataforma.")
        for antigo, novo in mudancas:
            if antigo and normalizar_email(antigo) != normalizar_email(novo):
                _remover_conta(conn, normalizar_email(antigo), escola_id)
            if novo:
                _registrar_conta(conn, normalizar_email(novo), escola_id)


# ---------- Criação de escola pelo ADM Supremo ----------

def criar_escola(engine, inicializar_escola, *, nome, slug, admin_email, admin_senha_hash):
    """Cria schema, tabelas e o superadmin da escola numa única transação (tudo ou nada)."""
    from app.models import UsuarioModel
    nome = (nome or "").strip()
    slug = (slug or "").strip().lower()
    if not nome or len(nome) > 120:
        raise ValueError("Informe o nome da escola (até 120 caracteres).")
    if not SLUG_VALIDO.match(slug):
        raise ValueError("O código da escola deve ter de 3 a 40 letras minúsculas, números ou hífen.")
    if slug == "padrao":
        raise ValueError("Este código é reservado.")
    schema = validar_schema(schema_da_escola(slug))
    # O DDL do Postgres é transacional: se qualquer passo falhar, nada fica criado.
    with engine.begin() as conn:
        if conn.execute(select(EscolaModel.id).where(EscolaModel.slug == slug)).scalar():
            raise ValueError("Já existe uma escola com este código.")
        escola_id = conn.execute(EscolaModel.__table__.insert().values(
            slug=slug, nome=nome, schema_nome=schema, ativa=True,
            criada_em=datetime.now(timezone.utc)).returning(EscolaModel.id)).scalar_one()
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        escola_conn = conn.execution_options(schema_translate_map={None: schema})
        inicializar_escola(escola_conn, schema)
        with Session(bind=escola_conn, info={"multiescola": True, "escola_schema": schema}) as db:
            db.add(UsuarioModel(email=admin_email.strip(), senha=admin_senha_hash, tipo="superadmin"))
            db.commit()
        # O nome aparece na tela de login e no menu da escola nova.
        from app.models import IdentidadeEscolaModel
        sigla = "".join(p[0] for p in nome.split()[:2]).lower() or "ef"
        escola_conn.execute(IdentidadeEscolaModel.__table__.insert().values(
            id=1, versao=1, dados=json.dumps({"nome": nome, "sigla": sigla}, ensure_ascii=False)))
    log.info("Escola criada: slug=%s schema=%s", slug, schema)
    return escola_id, schema


# ---------- Arquivos enviados ----------

PASTA_ESCOLAS = "escolas"


def pasta_uploads(base):
    """Cada escola guarda seus arquivos numa pasta própria; a escola padrão usa a pasta base."""
    import os
    schema = schema_da_requisicao()
    raiz = os.path.abspath(base)
    if not schema:
        return raiz
    return os.path.join(raiz, PASTA_ESCOLAS, schema)


def instalar_validacao_de_sessao(app, engine):
    """Sessão de escola desativada (ou inválida) é encerrada antes de qualquer outra regra."""
    from flask import session

    @app.before_request
    def _escola_da_sessao():
        schema = session.get("escola_schema")
        if not schema or not multiescola_ativo(engine):
            return
        try:
            validar_schema(schema)
            ativa = escola_ativa(engine, schema)
        except ValueError:
            ativa = False
        if not ativa:
            log.warning("Sessão encerrada: escola inativa ou inválida (%s)", schema)
            session.clear()
