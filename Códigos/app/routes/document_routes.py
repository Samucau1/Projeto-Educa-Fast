import os
from uuid import uuid4

from flask import Blueprint, jsonify, redirect, request, send_from_directory, session
from werkzeug.utils import secure_filename

from app.auth import decode_token_from_request, normalize_role
from app.controllers.document_controller import get_upload_folder, upload_documento
from app.security import local_return_path, save_upload, download_upload
from app.database import get_session
from app.models import (
    AlunoModel,
    AlunoTurmaModel,
    AtividadeModel,
    DisciplinaModel,
    DocumentoModel,
    ProfessorModel,
)

document_bp = Blueprint("document", __name__)


def _get_or_create_disciplina_geral(db):
    disciplina = db.query(DisciplinaModel).filter(DisciplinaModel.codigo == "GERAL").first()
    if disciplina:
        return disciplina

    disciplina = DisciplinaModel(nome="Geral", codigo="GERAL", carga_horaria=0)
    db.add(disciplina)
    db.flush()
    return disciplina


@document_bp.route('/arquivos/upload', methods=['POST'])
def upload_arquivo():
    redirect_to = local_return_path(request.form.get("redirect_to"))
    is_admin = normalize_role(session.get("user_role")) in {"admin", "superadmin"}
    jwt_payload = None
    if not is_admin:
        jwt_payload, error_response = decode_token_from_request()
        if error_response:
            return error_response

        role = normalize_role(jwt_payload.get("role") or jwt_payload.get("tipo"))
        if role != "professor":
            return jsonify({"erro": "Acesso permitido apenas para professores ou administradores"}), 403

    if "arquivo" not in request.files:
        return jsonify({"erro": "Arquivo nao enviado"}), 400

    response, status = upload_documento(
        request.form,
        request.files,
        current_user=jwt_payload,
        is_admin=is_admin,
    )

    if 200 <= status < 300 and redirect_to:
        return redirect(redirect_to)

    return jsonify(response), status


@document_bp.route('/arquivos/download/<path:filename>', methods=['GET'])
def download_arquivo(filename):
    role = normalize_role(session.get("user_role"))
    user_id = session.get("user_id")
    if not user_id:
        payload, error_response = decode_token_from_request()
        if error_response:
            return error_response
        role = normalize_role(payload.get("role"))
        user_id = int(payload["sub"])
    safe_filename = secure_filename(filename)

    if role == "aluno":
        db = get_session()
        try:
            documento = (
                db.query(DocumentoModel)
                .join(AlunoModel, AlunoModel.id == DocumentoModel.aluno_id)
                .filter(
                    AlunoModel.usuario_id == user_id,
                    DocumentoModel.caminho_arquivo == safe_filename,
                )
                .first()
            )
            atividade = (
                db.query(AtividadeModel)
                .join(AlunoTurmaModel, AlunoTurmaModel.turma_id == AtividadeModel.turma_id)
                .join(AlunoModel, AlunoModel.id == AlunoTurmaModel.aluno_id)
                .filter(
                    AlunoModel.usuario_id == user_id,
                    AtividadeModel.caminho_arquivo == safe_filename,
                )
                .first()
            )
        finally:
            db.close()

        if not documento and not atividade:
            return jsonify({"erro": "Arquivo nao encontrado para este aluno"}), 404
    elif role == "professor":
        db = get_session()
        try:
            documento = (
                db.query(DocumentoModel)
                .join(ProfessorModel, ProfessorModel.id == DocumentoModel.professor_id)
                .filter(
                    ProfessorModel.usuario_id == user_id,
                    DocumentoModel.caminho_arquivo == safe_filename,
                )
                .first()
            )
            atividade = (
                db.query(AtividadeModel)
                .join(ProfessorModel, ProfessorModel.id == AtividadeModel.professor_id)
                .filter(
                    ProfessorModel.usuario_id == user_id,
                    AtividadeModel.caminho_arquivo == safe_filename,
                )
                .first()
            )
        finally:
            db.close()

        if not documento and not atividade:
            return jsonify({"erro": "Arquivo nao encontrado para este professor"}), 404
    elif role not in {"admin", "superadmin"}:
        return jsonify({"erro": "Perfil sem permissao para arquivos"}), 403

    return download_upload(get_upload_folder(), safe_filename)


@document_bp.route('/professores/<int:professor_id>/arquivos/upload', methods=['POST'])
def upload_arquivo_professor(professor_id):
    redirect_to = local_return_path(request.form.get("redirect_to"))
    if normalize_role(session.get("user_role")) not in {"admin", "superadmin"}:
        return jsonify({"erro": "Acesso permitido apenas para administradores"}), 403

    if "arquivo" not in request.files:
        return jsonify({"erro": "Arquivo nao enviado"}), 400

    arquivo = request.files["arquivo"]
    if not arquivo.filename:
        return jsonify({"erro": "Nome do arquivo nao informado"}), 400

    original_filename = secure_filename(arquivo.filename)
    if not original_filename:
        return jsonify({"erro": "Nome do arquivo invalido"}), 400

    upload_folder = get_upload_folder()
    os.makedirs(upload_folder, exist_ok=True)
    filename = f"{uuid4().hex}_{original_filename}"
    saved_path = os.path.join(upload_folder, filename)

    db = get_session()
    try:
        professor = db.get(ProfessorModel, professor_id)
        if not professor:
            return jsonify({"erro": "Professor nao encontrado"}), 404

        disciplina = _get_or_create_disciplina_geral(db)
        save_upload(arquivo, saved_path)
        documento = DocumentoModel(
            aluno_id=None,
            professor_id=professor.id,
            disciplina_id=disciplina.id,
            titulo=(request.form.get("titulo") or original_filename)[:150],
            caminho_arquivo=filename,
        )
        db.add(documento)
        db.commit()
    except Exception:
        db.rollback()
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise
    finally:
        db.close()

    if redirect_to:
        return redirect(redirect_to)

    return jsonify({"mensagem": "Arquivo enviado"}), 201


@document_bp.route('/arquivos/perfil/<path:filename>', methods=['GET'])
def perfil_arquivo(filename):
    if not session.get("user_id"):
        return jsonify({"erro": "Autenticacao obrigatoria"}), 403
    safe_filename = secure_filename(filename)
    if not safe_filename.startswith("perfil_"):
        return jsonify({"erro": "Arquivo nao encontrado"}), 404

    if session.get("user_role") not in {"admin", "superadmin"}:
        with get_session() as db:
            own = (db.query(AlunoModel).filter_by(usuario_id=session["user_id"], foto_perfil=safe_filename).first()
                   or db.query(ProfessorModel).filter_by(usuario_id=session["user_id"], foto_perfil=safe_filename).first())
            if not own:
                return jsonify({"erro": "Arquivo nao encontrado"}), 404

    return download_upload(get_upload_folder(), safe_filename, attachment=False)
