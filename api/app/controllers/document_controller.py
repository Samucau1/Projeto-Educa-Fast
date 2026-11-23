import os
from datetime import datetime
from uuid import uuid4

from flask import current_app
from werkzeug.utils import secure_filename

from app.database import get_session
from app.models import (AlunoModel, DisciplinaModel, DocumentoModel, ProfessorModel,
                        AlunoTurmaModel, ProfessorTurmaModel, ProfessorDisciplinaModel,
                        TurmaDisciplinaModel, SolicitacaoDocumentoModel)
from app.security import save_upload


def get_upload_folder():
    return os.path.abspath(current_app.config["UPLOAD_FOLDER"])


def _get_or_create_disciplina(session_db, disciplina_id=None):
    if disciplina_id:
        disciplina = session_db.get(DisciplinaModel, disciplina_id)
        if disciplina:
            return disciplina, None

        return None, ({"erro": "Disciplina nao encontrada"}, 404)

    disciplina = (
        session_db.query(DisciplinaModel)
        .filter(DisciplinaModel.codigo == "GERAL")
        .first()
    )
    if disciplina:
        return disciplina, None

    disciplina = DisciplinaModel(
        nome="Geral",
        codigo="GERAL",
        carga_horaria=0,
    )
    session_db.add(disciplina)
    session_db.flush()
    return disciplina, None


def upload_documento(form, files, current_user=None, is_admin=False, aluno_id_override=None, solicitacao_id=None):
    if "arquivo" not in files:
        return {"erro": "Arquivo nao enviado"}, 400

    aluno_id = aluno_id_override or form.get("aluno_id", type=int)
    if not aluno_id:
        return {"erro": "aluno_id e obrigatorio"}, 400

    arquivo = files["arquivo"]
    if not arquivo.filename:
        return {"erro": "Nome do arquivo nao informado"}, 400

    session_db = get_session()
    upload_folder = get_upload_folder()
    os.makedirs(upload_folder, exist_ok=True)
    saved_path = None

    try:
        solicitacao = None
        if solicitacao_id:
            # Conditional update claims the request atomically, including across workers.
            claimed = session_db.query(SolicitacaoDocumentoModel).filter_by(
                id=solicitacao_id, aluno_id=aluno_id, status="pendente"
            ).update({"status": "processando"}, synchronize_session=False)
            if not claimed:
                return {"erro": "Solicitacao ja atendida ou indisponivel"}, 409
            solicitacao = session_db.get(SolicitacaoDocumentoModel, solicitacao_id)
        aluno = session_db.get(AlunoModel, aluno_id)
        if not aluno:
            return {"erro": "Aluno nao encontrado"}, 404

        professor = None
        if not is_admin and current_user:
            professor = (
                session_db.query(ProfessorModel)
                .filter(ProfessorModel.usuario_id == int(current_user["sub"]))
                .first()
            )
            if not professor:
                return {"erro": "Professor nao encontrado para o usuario autenticado"}, 403

            disciplina_id = form.get("disciplina_id", type=int)
            vinculo = (session_db.query(AlunoTurmaModel)
                       .join(ProfessorTurmaModel, ProfessorTurmaModel.turma_id == AlunoTurmaModel.turma_id)
                       .join(TurmaDisciplinaModel, TurmaDisciplinaModel.turma_id == AlunoTurmaModel.turma_id)
                       .join(ProfessorDisciplinaModel, ProfessorDisciplinaModel.disciplina_id == TurmaDisciplinaModel.disciplina_id)
                       .filter(AlunoTurmaModel.aluno_id == aluno_id,
                               ProfessorTurmaModel.professor_id == professor.id,
                               ProfessorDisciplinaModel.professor_id == professor.id,
                               TurmaDisciplinaModel.disciplina_id == disciplina_id).first())
            if not vinculo:
                return {"erro": "Aluno ou disciplina fora das turmas do professor"}, 403

        disciplina, error = _get_or_create_disciplina(
            session_db,
            form.get("disciplina_id", type=int),
        )
        if error:
            return error

        original_filename = secure_filename(arquivo.filename)
        if not original_filename:
            return {"erro": "Nome do arquivo invalido"}, 400

        filename = f"{uuid4().hex}_{original_filename}"
        saved_path = os.path.join(upload_folder, filename)
        save_upload(arquivo, saved_path)

        documento = DocumentoModel(
            aluno_id=aluno.id,
            professor_id=professor.id if professor else None,
            disciplina_id=disciplina.id,
            titulo=(form.get("titulo") or original_filename)[:150],
            caminho_arquivo=filename,
        )
        session_db.add(documento)
        if solicitacao:
            session_db.flush()
            solicitacao.documento_id = documento.id
            solicitacao.status = "enviado"
            solicitacao.completed_at = datetime.now()
        session_db.commit()

        return {
            "mensagem": "Arquivo enviado",
            "documento": {
                "id": documento.id,
                "titulo": documento.titulo,
                "arquivo": documento.caminho_arquivo,
                "aluno_id": documento.aluno_id,
                "professor_id": documento.professor_id,
                "disciplina_id": documento.disciplina_id,
            },
        }, 201
    except Exception:
        session_db.rollback()
        if saved_path and os.path.exists(saved_path):
            os.remove(saved_path)
        raise
    finally:
        session_db.close()
