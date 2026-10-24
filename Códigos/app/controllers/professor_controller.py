import os
from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from app.controllers.admin_controller import format_created_at
from app.controllers.document_controller import get_upload_folder
from app.security import save_upload
from app.database import get_session
from app.models import (
    AlunoModel,
    AlunoTurmaModel,
    AtividadeModel,
    DisciplinaModel,
    DocumentoModel,
    NotaModel,
    ProfessorDisciplinaModel,
    ProfessorModel,
    ProfessorTurmaModel,
    SolicitacaoDocumentoModel,
    TurmaDisciplinaModel,
    TurmaModel,
    UsuarioModel,
)


def get_professor_by_user_id(user_id):
    db = get_session()
    try:
        row = (
            db.query(ProfessorModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == ProfessorModel.usuario_id)
            .filter(ProfessorModel.usuario_id == user_id)
            .first()
        )
        if not row:
            return None

        professor, email = row
        return {
            "id": professor.id,
            "nome": professor.nome,
            "email": email,
            "disciplina": professor.disciplina_principal or "Nao informado",
            "regime": professor.regime_trabalho or "Nao informado",
            "foto_perfil": professor.foto_perfil,
        }
    finally:
        db.close()


def _format_nota(value):
    if value is None:
        return ""

    return str(value).replace(".", ",")


def _get_or_create_disciplina_geral(db):
    disciplina = db.query(DisciplinaModel).filter(DisciplinaModel.codigo == "GERAL").first()
    if disciplina:
        return disciplina

    disciplina = DisciplinaModel(nome="Geral", codigo="GERAL", carga_horaria=0)
    db.add(disciplina)
    db.flush()
    return disciplina


def get_teacher_area_data(user_id):
    db = get_session()
    try:
        row = (
            db.query(ProfessorModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == ProfessorModel.usuario_id)
            .filter(ProfessorModel.usuario_id == user_id)
            .first()
        )
        if not row:
            return None

        professor, email = row
        turma_rows = (
            db.query(TurmaModel)
            .join(ProfessorTurmaModel, ProfessorTurmaModel.turma_id == TurmaModel.id)
            .filter(ProfessorTurmaModel.professor_id == professor.id)
            .order_by(TurmaModel.nome.asc())
            .all()
        )
        from app.services.cursos import turma_ativa, autoriza_docencia
        from app.models.curso_model import EstadoTurmaModel, AtribuicaoDocenteModel
        turma_rows = [t for t in turma_rows if turma_ativa(db, t.id) and (
            not db.get(EstadoTurmaModel, t.id) or db.query(AtribuicaoDocenteModel).join(
            TurmaDisciplinaModel, AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(
            AtribuicaoDocenteModel.professor_id == professor.id, AtribuicaoDocenteModel.ativo.is_(True),
            TurmaDisciplinaModel.turma_id == t.id).first())]
        turma_ids = [turma.id for turma in turma_rows]

        disciplinas_por_turma = {turma.id: [] for turma in turma_rows}
        alunos_por_turma = {turma.id: [] for turma in turma_rows}
        atividades_por_turma = {turma.id: [] for turma in turma_rows}

        if turma_ids:
            disciplina_rows = (
                db.query(TurmaDisciplinaModel.turma_id, DisciplinaModel)
                .join(DisciplinaModel, DisciplinaModel.id == TurmaDisciplinaModel.disciplina_id)
                .join(
                    ProfessorDisciplinaModel,
                    ProfessorDisciplinaModel.disciplina_id == DisciplinaModel.id,
                )
                .filter(TurmaDisciplinaModel.turma_id.in_(turma_ids))
                .filter(ProfessorDisciplinaModel.professor_id == professor.id)
                .order_by(DisciplinaModel.nome.asc())
                .distinct()
                .all()
            )
            for turma_id, disciplina in disciplina_rows:
                if not autoriza_docencia(db, professor.id, turma_id, disciplina.id):
                    continue
                disciplinas_por_turma.setdefault(turma_id, []).append(
                    {
                        "id": disciplina.id,
                        "nome": disciplina.nome,
                        "codigo": disciplina.codigo,
                        "carga_horaria": disciplina.carga_horaria,
                    }
                )

            aluno_rows = (
                db.query(AlunoTurmaModel.turma_id, AlunoModel)
                .join(AlunoModel, AlunoModel.id == AlunoTurmaModel.aluno_id)
                .filter(AlunoTurmaModel.turma_id.in_(turma_ids))
                .order_by(AlunoModel.nome.asc())
                .all()
            )
            for turma_id, aluno in aluno_rows:
                alunos_por_turma.setdefault(turma_id, []).append(
                    {
                        "id": aluno.id,
                        "nome": aluno.nome,
                        "matricula": aluno.matricula,
                        "curso": aluno.curso_serie or "Nao informado",
                    }
                )

            atividade_rows = (
                db.query(AtividadeModel, DisciplinaModel)
                .join(DisciplinaModel, DisciplinaModel.id == AtividadeModel.disciplina_id)
                .filter(AtividadeModel.professor_id == professor.id)
                .filter(AtividadeModel.turma_id.in_(turma_ids))
                .order_by(AtividadeModel.id.desc())
                .limit(60)
                .all()
            )
            for atividade, disciplina in atividade_rows:
                atividades_por_turma.setdefault(atividade.turma_id, []).append(
                    {
                        "titulo": atividade.titulo,
                        "descricao": atividade.descricao or "Sem descricao.",
                        "disciplina": disciplina.nome,
                        "data_entrega": atividade.data_entrega or "Sem prazo",
                        "arquivo": atividade.caminho_arquivo,
                        "data": format_created_at(atividade.created_at),
                    }
                )

        notas_rows = (
            db.query(NotaModel, AlunoModel, DisciplinaModel, TurmaModel)
            .join(AlunoModel, AlunoModel.id == NotaModel.aluno_id)
            .join(DisciplinaModel, DisciplinaModel.id == NotaModel.disciplina_id)
            .join(AlunoTurmaModel, AlunoTurmaModel.aluno_id == AlunoModel.id)
            .join(TurmaModel, TurmaModel.id == AlunoTurmaModel.turma_id)
            .join(ProfessorTurmaModel, ProfessorTurmaModel.turma_id == TurmaModel.id)
            .filter(NotaModel.professor_id == professor.id)
            .filter(ProfessorTurmaModel.professor_id == professor.id)
            .order_by(NotaModel.id.desc())
            .limit(30)
            .all()
        )
        documentos_rows = (
            db.query(DocumentoModel, DisciplinaModel)
            .join(DisciplinaModel, DisciplinaModel.id == DocumentoModel.disciplina_id)
            .filter(
                DocumentoModel.professor_id == professor.id,
                DocumentoModel.aluno_id.is_(None),
            )
            .order_by(DocumentoModel.id.desc())
            .limit(30)
            .all()
        )
        solicitacoes_rows = (
            db.query(SolicitacaoDocumentoModel)
            .filter(SolicitacaoDocumentoModel.professor_id == professor.id)
            .order_by(SolicitacaoDocumentoModel.id.desc())
            .limit(30)
            .all()
        )

        return {
            "professor": {
                "id": professor.id,
                "nome": professor.nome,
                "email": email,
                "disciplina": professor.disciplina_principal or "Nao informado",
                "regime": professor.regime_trabalho or "Nao informado",
                "foto_perfil": professor.foto_perfil,
            },
            "turmas": [
                {
                    "id": turma.id,
                    "nome": turma.nome,
                    "codigo": turma.codigo,
                    "ano_letivo": turma.ano_letivo,
                    "turno": turma.turno or "Nao informado",
                    "disciplinas": disciplinas_por_turma.get(turma.id, []),
                    "alunos": alunos_por_turma.get(turma.id, []),
                    "atividades": atividades_por_turma.get(turma.id, []),
                }
                for turma in turma_rows
            ],
            "notas": [
                {
                    "aluno": aluno.nome,
                    "matricula": aluno.matricula,
                    "disciplina": disciplina.nome,
                    "turma": turma.nome,
                    "nota": _format_nota(nota.nota),
                    "observacao": nota.observacao or "-",
                    "data": format_created_at(nota.data_lancamento),
                }
                for nota, aluno, disciplina, turma in notas_rows
            ],
            "documentos": [
                {
                    "titulo": documento.titulo,
                    "arquivo": documento.caminho_arquivo,
                    "disciplina": disciplina.nome,
                    "data": format_created_at(documento.data_envio),
                }
                for documento, disciplina in documentos_rows
            ],
            "solicitacoes_documentos": [
                {
                    "id": solicitacao.id,
                    "titulo": solicitacao.titulo,
                    "mensagem": solicitacao.mensagem or "Envie o documento solicitado pela secretaria.",
                    "status": solicitacao.status,
                    "status_label": "Enviado" if solicitacao.status == "enviado" else "Pendente",
                    "data": format_created_at(solicitacao.created_at),
                }
                for solicitacao in solicitacoes_rows
            ],
        }
    finally:
        db.close()


def launch_activity(user_id, data, files=None):
    turma_id = data.get("turma_id", type=int)
    disciplina_id = data.get("disciplina_id", type=int)
    titulo = (data.get("titulo") or "").strip()
    descricao = (data.get("descricao") or "").strip()
    data_entrega = (data.get("data_entrega") or "").strip()

    if not turma_id or not disciplina_id or not titulo:
        return {"erro": "Turma, disciplina e titulo sao obrigatorios"}, 400

    arquivo = files.get("arquivo") if files else None
    filename = None
    saved_path = None
    if arquivo and arquivo.filename:
        original_filename = secure_filename(arquivo.filename)
        if not original_filename:
            return {"erro": "Nome do arquivo invalido"}, 400

        upload_folder = get_upload_folder()
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"atividade_{uuid4().hex}_{original_filename}"
        saved_path = os.path.join(upload_folder, filename)

    db = get_session()
    try:
        professor = (
            db.query(ProfessorModel)
            .filter(ProfessorModel.usuario_id == user_id)
            .first()
        )
        if not professor:
            return {"erro": "Professor nao encontrado"}, 404

        professor_na_turma = (
            db.query(ProfessorTurmaModel)
            .filter(
                ProfessorTurmaModel.professor_id == professor.id,
                ProfessorTurmaModel.turma_id == turma_id,
            )
            .first()
        )
        professor_disciplina = (
            db.query(ProfessorDisciplinaModel)
            .filter(
                ProfessorDisciplinaModel.professor_id == professor.id,
                ProfessorDisciplinaModel.disciplina_id == disciplina_id,
            )
            .first()
        )
        turma_disciplina = (
            db.query(TurmaDisciplinaModel)
            .filter(
                TurmaDisciplinaModel.turma_id == turma_id,
                TurmaDisciplinaModel.disciplina_id == disciplina_id,
            )
            .first()
        )

        from app.services.cursos import autoriza_docencia
        if not autoriza_docencia(db, professor.id, turma_id, disciplina_id):
            return {"erro": "Atribuicao docente ausente, revogada ou turma arquivada"}, 403
        if not professor_na_turma:
            return {"erro": "Professor nao pertence a esta turma"}, 403
        if not professor_disciplina or not turma_disciplina:
            return {"erro": "Disciplina nao disponivel para este professor nesta turma"}, 403

        atividade = AtividadeModel(
            professor_id=professor.id,
            turma_id=turma_id,
            disciplina_id=disciplina_id,
            titulo=titulo[:150],
            descricao=descricao or None,
            data_entrega=data_entrega[:10] or None,
            caminho_arquivo=filename,
        )
        if saved_path:
            save_upload(arquivo, saved_path)
        db.add(atividade)
        db.commit()
        return {"mensagem": "Atividade lancada"}, 201
    except Exception:
        db.rollback()
        if saved_path and os.path.exists(saved_path):
            os.remove(saved_path)
        raise
    finally:
        db.close()


def upload_requested_document(user_id, form, files):
    solicitacao_id = form.get("solicitacao_id", type=int)
    if not solicitacao_id:
        return {"erro": "Solicitacao de documento nao informada"}, 400

    if "arquivo" not in files:
        return {"erro": "Arquivo nao enviado"}, 400

    arquivo = files["arquivo"]
    if not arquivo.filename:
        return {"erro": "Nome do arquivo nao informado"}, 400

    original_filename = secure_filename(arquivo.filename)
    if not original_filename:
        return {"erro": "Nome do arquivo invalido"}, 400

    upload_folder = get_upload_folder()
    os.makedirs(upload_folder, exist_ok=True)
    filename = f"{uuid4().hex}_{original_filename}"
    saved_path = os.path.join(upload_folder, filename)

    db = get_session()
    try:
        professor = (
            db.query(ProfessorModel)
            .filter(ProfessorModel.usuario_id == user_id)
            .first()
        )
        if not professor:
            return {"erro": "Professor nao encontrado"}, 404

        solicitacao = (
            db.query(SolicitacaoDocumentoModel)
            .filter(
                SolicitacaoDocumentoModel.id == solicitacao_id,
                SolicitacaoDocumentoModel.professor_id == professor.id,
            )
            .first()
        )
        if not solicitacao:
            return {"erro": "Solicitacao de documento nao encontrada"}, 404

        claimed = db.query(SolicitacaoDocumentoModel).filter_by(
            id=solicitacao.id, professor_id=professor.id, status="pendente"
        ).update({"status": "processando"}, synchronize_session=False)
        if not claimed:
            return {"erro": "Solicitacao ja atendida"}, 409

        disciplina = _get_or_create_disciplina_geral(db)
        save_upload(arquivo, saved_path)
        documento = DocumentoModel(
            aluno_id=None,
            professor_id=professor.id,
            disciplina_id=disciplina.id,
            titulo=solicitacao.titulo[:150],
            caminho_arquivo=filename,
        )
        db.add(documento)
        db.flush()

        solicitacao.documento_id = documento.id
        solicitacao.status = "enviado"
        solicitacao.completed_at = datetime.now()
        db.commit()
        return {"mensagem": "Documento enviado"}, 201
    except Exception:
        db.rollback()
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise
    finally:
        db.close()


def save_student_grade(user_id, data):
    aluno_id = data.get("aluno_id", type=int)
    turma_id = data.get("turma_id", type=int)
    disciplina_id = data.get("disciplina_id", type=int)
    nota_raw = (data.get("nota") or "").strip().replace(",", ".")
    observacao = (data.get("observacao") or "").strip()

    if not aluno_id or not turma_id or not disciplina_id or not nota_raw:
        return {"erro": "Aluno, turma, disciplina e nota sao obrigatorios"}, 400

    try:
        nota_value = Decimal(nota_raw)
    except InvalidOperation:
        return {"erro": "Nota invalida"}, 400

    if not nota_value.is_finite() or nota_value < 0 or nota_value > 10:
        return {"erro": "Nota deve estar entre 0 e 10"}, 400

    db = get_session()
    try:
        professor = (
            db.query(ProfessorModel)
            .filter(ProfessorModel.usuario_id == user_id)
            .first()
        )
        if not professor:
            return {"erro": "Professor nao encontrado"}, 404

        aluno_na_turma = (
            db.query(AlunoTurmaModel)
            .filter(
                AlunoTurmaModel.aluno_id == aluno_id,
                AlunoTurmaModel.turma_id == turma_id,
            )
            .first()
        )
        professor_na_turma = (
            db.query(ProfessorTurmaModel)
            .filter(
                ProfessorTurmaModel.professor_id == professor.id,
                ProfessorTurmaModel.turma_id == turma_id,
            )
            .first()
        )
        professor_disciplina = (
            db.query(ProfessorDisciplinaModel)
            .filter(
                ProfessorDisciplinaModel.professor_id == professor.id,
                ProfessorDisciplinaModel.disciplina_id == disciplina_id,
            )
            .first()
        )
        turma_disciplina = (
            db.query(TurmaDisciplinaModel)
            .filter(
                TurmaDisciplinaModel.turma_id == turma_id,
                TurmaDisciplinaModel.disciplina_id == disciplina_id,
            )
            .first()
        )

        if not aluno_na_turma:
            return {"erro": "Aluno nao pertence a esta turma"}, 403
        from app.services.cursos import autoriza_docencia
        if not autoriza_docencia(db, professor.id, turma_id, disciplina_id):
            return {"erro": "Atribuicao docente ausente, revogada ou turma arquivada"}, 403
        if not professor_na_turma:
            return {"erro": "Professor nao pertence a esta turma"}, 403
        if not professor_disciplina or not turma_disciplina:
            return {"erro": "Disciplina nao disponivel para este professor nesta turma"}, 403

        nota = (
            db.query(NotaModel)
            .filter(
                NotaModel.aluno_id == aluno_id,
                NotaModel.disciplina_id == disciplina_id,
            )
            .first()
        )
        if nota:
            nota.professor_id = professor.id
            nota.nota = nota_value
            nota.observacao = observacao[:255] or None
        else:
            nota = NotaModel(
                aluno_id=aluno_id,
                disciplina_id=disciplina_id,
                professor_id=professor.id,
                nota=nota_value,
                observacao=observacao[:255] or None,
            )
            db.add(nota)

        db.commit()
        return {"mensagem": "Nota salva"}, 200
    except IntegrityError:
        db.rollback()
        return {"erro": "Nao foi possivel salvar a nota"}, 409
    finally:
        db.close()
