from flask import Blueprint, redirect, render_template, request, session, url_for

from app.auth import normalize_role
from app.controllers.admin_controller import (
    associar_aluno_turma,
    associar_professor_disciplina,
    associar_professor_turma,
    criar_comunicado,
    criar_disciplina,
    criar_turma,
    get_admin_data,
    get_aluno_detail,
    get_comunicados,
    get_disciplinas_page_data,
    get_professor_detail,
    get_turmas_page_data,
    request_professor_document,
    request_student_document,
    update_professor_data,
    update_student_data,
)
from app.routes.guards import admin_required
from app.views.dashboard_view import render_dashboard
from app.views.home_view import render_home

home_blueprint = Blueprint("home", __name__)


@home_blueprint.route("/", methods=["GET"])
def home():
    if normalize_role(session.get("user_role")) == "admin":
        return redirect(url_for("home.admin_dashboard"))
    if normalize_role(session.get("user_role")) == "aluno":
        return redirect(url_for("aluno.dashboard"))
    if normalize_role(session.get("user_role")) == "professor":
        return redirect(url_for("professor.dashboard"))

    context = {"title": "Secretaria Escolar DF"}
    return render_home(context)


@home_blueprint.route("/dashboard", methods=["GET"])
@home_blueprint.route("/dashboard.html", methods=["GET"])
@home_blueprint.route("/admin/dashboard", methods=["GET"])
@home_blueprint.route("/admin_painel.html", methods=["GET"])
def admin_dashboard():
    admin_required()

    context = {"title": "Dashboard da Secretaria", **get_admin_data()}
    return render_dashboard(context)


@home_blueprint.route("/cadastro/alunos", methods=["GET"])
@home_blueprint.route("/cadastro_aluno.html", methods=["GET"])
@home_blueprint.route("/admin/cadastro-alunos", methods=["GET"])
@home_blueprint.route("/admin_cadastro_aluno.html", methods=["GET"])
def admin_cadastro_alunos():
    admin_required()
    return render_template("admin_cadastro_aluno.html")


@home_blueprint.route("/cadastro/professores", methods=["GET"])
@home_blueprint.route("/cadastro_professores.html", methods=["GET"])
@home_blueprint.route("/admin/cadastro-professores", methods=["GET"])
@home_blueprint.route("/admin_cadastro_professores.html", methods=["GET"])
def admin_cadastro_professores():
    admin_required()
    return render_template("admin_cadastro_professores.html")


@home_blueprint.route("/banco-de-dados", methods=["GET"])
@home_blueprint.route("/banco_de_dados.html", methods=["GET"])
@home_blueprint.route("/admin/banco-de-dados", methods=["GET"])
@home_blueprint.route("/admin_banco_dados.html", methods=["GET"])
def admin_banco_dados():
    admin_required()
    return render_template("admin_banco_dados.html", **get_admin_data())


@home_blueprint.route("/comunicados", methods=["GET", "POST"])
@home_blueprint.route("/admin/comunicados", methods=["GET", "POST"])
@home_blueprint.route("/admin_comunicados.html", methods=["GET", "POST"])
def admin_comunicados():
    admin_required()
    error = None

    if request.method == "POST":
        response, status = criar_comunicado(request.form, session.get("user_email"))
        if status == 201:
            return redirect(url_for("home.admin_comunicados"))

        error = response.get("erro")

    return render_template(
        "admin_comunicados.html",
        comunicados=get_comunicados(),
        error=error,
    )


@home_blueprint.route("/disciplinas", methods=["GET", "POST"])
@home_blueprint.route("/admin/disciplinas", methods=["GET", "POST"])
@home_blueprint.route("/admin_disciplinas.html", methods=["GET", "POST"])
def admin_disciplinas():
    admin_required()
    error = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "associate_teacher":
            response, status = associar_professor_disciplina(request.form)
        else:
            response, status = criar_disciplina(request.form)

        if status == 201:
            return redirect(url_for("home.admin_disciplinas"))

        error = response.get("erro")

    return render_template(
        "admin_disciplinas.html",
        **get_disciplinas_page_data(),
        error=error,
    )


@home_blueprint.route("/turmas", methods=["GET", "POST"])
@home_blueprint.route("/admin/turmas", methods=["GET", "POST"])
@home_blueprint.route("/admin_turmas.html", methods=["GET", "POST"])
def admin_turmas():
    admin_required()
    error = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "associate_student":
            response, status = associar_aluno_turma(request.form)
        elif action == "associate_teacher":
            response, status = associar_professor_turma(request.form)
        else:
            response, status = criar_turma(request.form)

        if status == 201:
            return redirect(url_for("home.admin_turmas"))

        error = response.get("erro")

    return render_template(
        "admin_turmas.html",
        **get_turmas_page_data(),
        error=error,
    )


@home_blueprint.route("/alunos/<int:aluno_id>", methods=["GET"])
@home_blueprint.route("/detalhes_aluno/<int:aluno_id>", methods=["GET"])
@home_blueprint.route("/admin/alunos/<int:aluno_id>", methods=["GET"])
@home_blueprint.route("/admin_detalhes_aluno/<int:aluno_id>", methods=["GET"])
def admin_detalhes_aluno(aluno_id):
    admin_required()
    return render_template("admin_detalhes_aluno.html", **get_aluno_detail(aluno_id))


@home_blueprint.route("/admin/alunos/<int:aluno_id>/documentos/solicitar", methods=["POST"])
def admin_solicitar_documento_aluno(aluno_id):
    admin_required()
    request_student_document(aluno_id, request.form)
    return redirect(url_for("home.admin_detalhes_aluno", aluno_id=aluno_id))


@home_blueprint.route("/admin/alunos/<int:aluno_id>/editar", methods=["POST"])
def admin_editar_aluno(aluno_id):
    admin_required()
    update_student_data(aluno_id, request.form, request.files)
    return redirect(url_for("home.admin_detalhes_aluno", aluno_id=aluno_id))


@home_blueprint.route("/professores/<int:professor_id>", methods=["GET"])
@home_blueprint.route("/detalhes_professor/<int:professor_id>", methods=["GET"])
@home_blueprint.route("/admin/professores/<int:professor_id>", methods=["GET"])
@home_blueprint.route("/admin_detalhes_professor/<int:professor_id>", methods=["GET"])
def admin_detalhes_professor(professor_id):
    admin_required()
    return render_template(
        "admin_detalhes_professor.html",
        **get_professor_detail(professor_id),
    )


@home_blueprint.route("/admin/professores/<int:professor_id>/editar", methods=["POST"])
def admin_editar_professor(professor_id):
    admin_required()
    update_professor_data(professor_id, request.form, request.files)
    return redirect(url_for("home.admin_detalhes_professor", professor_id=professor_id))


@home_blueprint.route("/admin/professores/<int:professor_id>/documentos/solicitar", methods=["POST"])
def admin_solicitar_documento_professor(professor_id):
    admin_required()
    request_professor_document(professor_id, request.form)
    return redirect(url_for("home.admin_detalhes_professor", professor_id=professor_id))


@home_blueprint.route("/detalhes_aluno.html", methods=["GET"])
@home_blueprint.route("/admin_detalhes_aluno.html", methods=["GET"])
def admin_detalhes_aluno_legacy():
    admin_required()
    aluno_id = request.args.get("id", type=int)
    return render_template("admin_detalhes_aluno.html", **get_aluno_detail(aluno_id))


@home_blueprint.route("/detalhes_professor.html", methods=["GET"])
@home_blueprint.route("/admin_detalhes_professor.html", methods=["GET"])
def admin_detalhes_professor_legacy():
    admin_required()
    professor_id = request.args.get("id", type=int)
    return render_template(
        "admin_detalhes_professor.html",
        **get_professor_detail(professor_id),
    )
