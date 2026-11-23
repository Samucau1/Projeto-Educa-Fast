import secrets
from flask import Blueprint, g, jsonify, redirect, request, session, url_for, render_template

from app.auth import professor_required
from app.controllers.auth_controller import buscar_alunos, cadastrar_usuario, login_usuario
from app.routes.guards import admin_json_required

auth_bp = Blueprint('auth', __name__)


def _admin_session_required():
    return admin_json_required()


def _get_request_data():
    if request.form:
        return request.form.copy()

    return request.get_json(silent=True) or {}


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    response, status = login_usuario(data)
    if status == 200:
        session.clear()
        session["csrf_token"] = secrets.token_hex(32)
        session["user_id"] = response["id"]
        session["user_email"] = response["email"]
        session["user_role"] = response["role"]
        response["csrf_token"] = session["csrf_token"]

    return jsonify(response), status


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == "GET":
        return render_template("logout.html")
    session.clear()
    return redirect(url_for("home.home"))


@auth_bp.route('/cadastro', methods=['POST'])
def cadastro():
    error = admin_json_required()
    if error:
        return error
    data = _get_request_data()
    if (data.get("tipo") or data.get("role") or "").strip().lower() == "admin" and session.get("user_role") != "superadmin":
        return jsonify({"erro": "Apenas o superperfil pode criar administradores"}), 403
    response, status = cadastrar_usuario(data, request.files)
    return jsonify(response), status


@auth_bp.route('/cadastro/aluno', methods=['POST'])
@auth_bp.route('/cadastro/alunos', methods=['POST'])
def cadastro_aluno():
    error_response = _admin_session_required()
    if error_response:
        return error_response

    data = _get_request_data()
    data["tipo"] = "aluno"
    response, status = cadastrar_usuario(data, request.files)
    return jsonify(response), status


@auth_bp.route('/cadastro/professor', methods=['POST'])
@auth_bp.route('/cadastro/professores', methods=['POST'])
def cadastro_professor():
    error_response = _admin_session_required()
    if error_response:
        return error_response

    data = _get_request_data()
    data["tipo"] = "professor"
    response, status = cadastrar_usuario(data, request.files)
    return jsonify(response), status


@auth_bp.route('/professor/teste', methods=['GET'])
@professor_required
def teste_professor():
    # Rota simples para validar se o JWT pertence a um professor.
    return jsonify({"mensagem": "Permissao de professor validada"}), 200


@auth_bp.route('/alunos/busca', methods=['GET'])
@professor_required
def alunos_busca():
    termo = request.args.get("termo") or request.args.get("q") or request.args.get("cpf")
    response, status = buscar_alunos(termo, int(g.current_user["sub"]))
    return jsonify(response), status
