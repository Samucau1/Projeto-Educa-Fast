"""Painel do ADM Supremo: o dono da plataforma cria escolas e o superadmin de cada uma."""
import logging
import secrets
from functools import wraps

import click
from flask import Blueprint, abort, flash, redirect, request, session, url_for
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app import escolas
from app.database import engine, get_session, inicializar_escola
from app.spa import render_page

log = logging.getLogger(__name__)
supremo_bp = Blueprint("supremo", __name__, url_prefix="/supremo")


def supremo_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not escolas.multiescola_ativo(engine):
            abort(404)
        operador_id = session.get("operador_id")
        if not operador_id or session.get("user_role") != "supremo":
            if request.method == "GET":
                return redirect(url_for("home.home"))
            abort(403)
        with Session(engine) as db:
            if db.get(escolas.OperadorModel, operador_id) is None:
                session.clear()
                abort(403)
        if request.method == "POST":
            token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
            if not secrets.compare_digest(token, session.get("csrf_token", "")):
                abort(400, "Formulário expirado. Recarregue a página.")
        return view(*args, **kwargs)
    return wrapper


def _resumo_escola(escola):
    """Números de cada escola, lidos dentro da área dela no banco."""
    from app.models import AlunoModel, ProfessorModel, TurmaModel, UsuarioModel
    resumo = {"id": escola.id, "nome": escola.nome, "slug": escola.slug, "schema": escola.schema_nome,
              "ativa": escola.ativa, "criada_em": escola.criada_em, "padrao": escola.schema_nome == escolas.SCHEMA_PADRAO}
    try:
        with get_session(escola.schema_nome) as db:
            resumo["usuarios"] = db.scalar(select(func.count()).select_from(UsuarioModel))
            resumo["alunos"] = db.scalar(select(func.count()).select_from(AlunoModel))
            resumo["professores"] = db.scalar(select(func.count()).select_from(ProfessorModel))
            resumo["turmas"] = db.scalar(select(func.count()).select_from(TurmaModel))
            resumo["superadmins"] = db.scalars(select(UsuarioModel.email).where(UsuarioModel.tipo == "superadmin")).all()
    except SQLAlchemyError:
        log.exception("Falha ao ler o resumo da escola %s", escola.slug)
        resumo["erro"] = "Não foi possível ler os dados desta escola."
    return resumo


@supremo_bp.route("", methods=["GET"])
@supremo_required
def painel():
    with Session(engine) as db:
        lista = db.scalars(select(escolas.EscolaModel).order_by(escolas.EscolaModel.criada_em)).all()
    resumos = [_resumo_escola(e) for e in lista]
    totais = {campo: sum(r.get(campo) or 0 for r in resumos) for campo in ("alunos", "professores", "usuarios")}
    totais["escolas"] = len(resumos)
    totais["ativas"] = sum(1 for r in resumos if r["ativa"])
    return render_page("supremo_painel", escolas=resumos, totais=totais, operador=session.get("user_email"))


@supremo_bp.route("/escolas", methods=["POST"])
@supremo_required
def criar():
    nome = request.form.get("nome", "")
    slug = request.form.get("slug", "")
    email = request.form.get("admin_email", "").strip()
    senha = request.form.get("admin_senha", "")
    if "@" not in email or len(email) > 120:
        flash("Informe um e-mail válido para o superadmin da escola.", "error")
        return redirect(url_for("supremo.painel"))
    if len(senha) < 8:
        flash("A senha do superadmin precisa ter pelo menos 8 caracteres.", "error")
        return redirect(url_for("supremo.painel"))
    try:
        escolas.criar_escola(engine, inicializar_escola, nome=nome, slug=slug,
                             admin_email=email, admin_senha_hash=generate_password_hash(senha))
    except ValueError as erro:
        flash(str(erro), "error")
    except IntegrityError:
        flash("Este e-mail já é usado em outra escola da plataforma. Use outro e-mail.", "error")
    except SQLAlchemyError:
        log.exception("Falha ao criar a escola %s", slug)
        flash("Não foi possível criar a escola. Nada foi gravado; tente novamente.", "error")
    else:
        flash(f"Escola “{nome.strip()}” criada. O superadmin já pode entrar com {email}.", "success")
    return redirect(url_for("supremo.painel"))


@supremo_bp.route("/escolas/<int:escola_id>/situacao", methods=["POST"])
@supremo_required
def alterar_situacao(escola_id):
    """Desativar bloqueia o acesso da escola sem apagar nenhum dado; reativar devolve o acesso."""
    ativar = request.form.get("ativa") == "1"
    with Session(engine) as db:
        escola = db.get(escolas.EscolaModel, escola_id)
        if escola is None:
            abort(404)
        if escola.schema_nome == escolas.SCHEMA_PADRAO and not ativar:
            flash("A escola padrão não pode ser desativada.", "error")
            return redirect(url_for("supremo.painel"))
        escola.ativa = ativar
        db.commit()
        nome = escola.nome
    flash(f"Escola “{nome}” {'reativada' if ativar else 'desativada'}.", "success")
    return redirect(url_for("supremo.painel"))


def init_supremo(app):
    app.register_blueprint(supremo_bp)

    @app.cli.command("criar-operador")
    @click.option("--email", prompt=True)
    @click.option("--nome", prompt=True)
    @click.option("--senha", prompt=True, hide_input=True, confirmation_prompt=True)
    def criar_operador(email, nome, senha):
        """Cria um ADM Supremo (dono da plataforma)."""
        if not escolas.multiescola_ativo(engine):
            raise click.ClickException("O ADM Supremo exige Postgres.")
        if "@" not in email or len(email) > 120 or len(senha) < 8:
            raise click.ClickException("Informe e-mail válido e senha com pelo menos 8 caracteres.")
        with Session(engine) as db:
            db.add(escolas.OperadorModel(email=escolas.normalizar_email(email), nome=nome.strip()[:120],
                                         senha=generate_password_hash(senha)))
            try:
                db.commit()
            except IntegrityError:
                raise click.ClickException("Já existe um ADM Supremo com este e-mail.") from None
        click.echo("ADM Supremo criado.")
