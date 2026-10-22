import re
import secrets

import click
from flask import Blueprint, abort, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from werkzeug.security import generate_password_hash

from app.auth import normalize_role
from app.controllers.admin_controller import get_comunicados
from app.controllers.auth_controller import cadastrar_usuario
from app.database import get_session
from app.models import AlunoModel, ProfessorModel, UsuarioModel, ConfiguracaoModel


gestao_bp = Blueprint("gestao", __name__)
ROLES = {"admin", "professor", "aluno"}


def super_required():
    if session.get("user_role") != "superadmin":
        abort(403)


def _render_usuarios(error=None, permission_error=None, edit_user_id=None, status=200):
    with get_session() as db:
        users = []
        query = db.query(UsuarioModel).options(selectinload(UsuarioModel.aluno), selectinload(UsuarioModel.professor))
        for user in query.order_by(UsuarioModel.email):
            cadastro = user.professor or user.aluno
            users.append({
                "id": user.id, "email": user.email, "tipo": normalize_role(user.tipo),
                "nome": cadastro.nome if cadastro else user.email.split("@")[0],
                "tem_professor": user.professor is not None, "tem_aluno": user.aluno is not None,
            })
    return render_template("super_usuarios.html", usuarios=users, error=error,
                           permission_error=permission_error, edit_user_id=edit_user_id), status


@gestao_bp.route("/super/usuarios", methods=["GET", "POST"])
def usuarios():
    super_required()
    error = None
    if request.method == "POST":
        result, status = cadastrar_usuario(request.form)
        if status == 201:
            flash("Usuário criado. O acesso já está disponível.", "success")
            return redirect(url_for("gestao.usuarios"))
        error = result.get("erro")
    return _render_usuarios(error=error)


@gestao_bp.post("/super/usuarios/<int:user_id>/perfil")
def perfil(user_id):
    super_required()
    tipo = normalize_role(request.form.get("tipo"))
    error = None
    with get_session() as db:
        user = db.get(UsuarioModel, user_id)
        if not user:
            abort(404)
        if user.tipo == "superadmin" or tipo not in ROLES:
            abort(403)
        # Mantém os registros acadêmicos ao trocar permissões.
        if tipo == "professor" and not user.professor:
            nome, cpf = request.form.get("nome", "").strip(), request.form.get("cpf", "").strip()
            if not nome or not cpf:
                error = "Para atribuir professor, informe nome e CPF."
            else:
                db.add(ProfessorModel(usuario_id=user.id, nome=nome, cpf=cpf))
        if tipo == "aluno" and not user.aluno:
            nome, matricula = request.form.get("nome", "").strip(), request.form.get("matricula", "").strip()
            if not nome or not matricula:
                error = "Para atribuir aluno, informe nome e matrícula."
            else:
                db.add(AlunoModel(usuario_id=user.id, nome=nome, matricula=matricula))
        if not error:
            user.tipo = tipo
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                error = "CPF ou matrícula já cadastrado."
    if error:
        return _render_usuarios(permission_error=error, edit_user_id=user_id, status=400)
    flash("Permissões atualizadas. O novo perfil já está em vigor.", "success")
    return redirect(url_for("gestao.usuarios"))


@gestao_bp.route("/super/layout", methods=["GET", "POST"])
def layout():
    super_required()
    error = None
    if request.method == "POST":
        fundo = request.form.get("cor_fundo", "")
        destaque = request.form.get("cor_destaque", "")
        if not all(re.fullmatch(r"#[0-9a-fA-F]{6}", c) for c in (fundo, destaque)):
            error = "Informe cores no formato #RRGGBB."
        else:
            with get_session() as db:
                config = db.get(ConfiguracaoModel, 1)
                if config is None:
                    config = ConfiguracaoModel(id=1)
                    db.add(config)
                config.cor_fundo, config.cor_destaque = fundo, destaque
                db.commit()
            flash("Cores atualizadas. A nova aparência já está disponível.", "success")
            return redirect(url_for("gestao.layout"))
    return render_template("super_layout.html", error=error)


@gestao_bp.get("/mensagens")
def mensagens():
    if not session.get("user_id"):
        abort(403)
    return render_template("mensagens.html", comunicados=get_comunicados(limit=100))


def init_gestao(app):
    app.register_blueprint(gestao_bp)

    @app.before_request
    def atualizar_permissoes():
        if request.endpoint == "static":
            return
        g.tema = {"cor_fundo": "#06385d", "cor_destaque": "#22d3ee"}
        with get_session() as db:
            if session.get("user_id"):
                user = db.get(UsuarioModel, session["user_id"])
                if user is None:
                    session.clear()
                else:
                    session["user_role"] = normalize_role(user.tipo)
                    session["user_email"] = user.email
            config = db.get(ConfiguracaoModel, 1)
            if config:
                g.tema = {"cor_fundo": config.cor_fundo, "cor_destaque": config.cor_destaque}
        session.setdefault("csrf_token", secrets.token_hex(32))
        if request.method == "POST" and (request.blueprint == "gestao" or request.endpoint == "home.admin_comunicados"):
            token = request.form.get("csrf_token", "")
            if not secrets.compare_digest(token, session["csrf_token"]):
                abort(400, "Formulário expirado. Recarregue a página.")

    @app.context_processor
    def tema_context():
        return {"tema": getattr(g, "tema", {}), "csrf_token": session.get("csrf_token", "")}

    @app.cli.command("criar-superusuario")
    @click.option("--email", prompt=True)
    @click.option("--senha", prompt=True, hide_input=True, confirmation_prompt=True)
    def criar_superusuario(email, senha):
        """Cria o superperfil inicial sem expor cadastro público privilegiado."""
        if "@" not in email or len(email) > 120 or len(senha) < 8:
            raise click.ClickException("Informe e-mail válido e senha com pelo menos 8 caracteres.")
        with get_session() as db:
            if db.query(UsuarioModel).filter_by(email=email).first():
                raise click.ClickException("E-mail já cadastrado. Use um e-mail exclusivo.")
            db.add(UsuarioModel(email=email, senha=generate_password_hash(senha), tipo="superadmin"))
            db.commit()
        click.echo("Superperfil criado.")
