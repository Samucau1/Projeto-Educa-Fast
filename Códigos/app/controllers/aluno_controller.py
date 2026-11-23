from datetime import datetime

from app.controllers.admin_controller import format_created_at
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
    UsuarioModel,
)


def get_aluno_by_user_id(user_id):
    db = get_session()
    try:
        row = (
            db.query(AlunoModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == AlunoModel.usuario_id)
            .filter(AlunoModel.usuario_id == user_id)
            .first()
        )
        if not row:
            return None

        aluno, email = row
        return {
            "id": aluno.id,
            "nome": aluno.nome,
            "email": email,
            "matricula": aluno.matricula,
            "curso": aluno.curso_serie or "Nao informado",
            "status": aluno.status_matricula or "Nao informado",
            "foto_perfil": aluno.foto_perfil,
        }
    finally:
        db.close()


def get_aluno_area_data(user_id):
    db = get_session()
    try:
        row = (
            db.query(AlunoModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == AlunoModel.usuario_id)
            .filter(AlunoModel.usuario_id == user_id)
            .first()
        )
        if not row:
            return None

        aluno, email = row
        notas = (
            db.query(NotaModel, DisciplinaModel.nome)
            .join(DisciplinaModel, DisciplinaModel.id == NotaModel.disciplina_id)
            .filter(NotaModel.aluno_id == aluno.id)
            .order_by(DisciplinaModel.nome.asc())
            .all()
        )
        documentos = (
            db.query(DocumentoModel)
            .filter(DocumentoModel.aluno_id == aluno.id)
            .order_by(DocumentoModel.id.desc())
            .limit(12)
            .all()
        )
        solicitacoes = (
            db.query(SolicitacaoDocumentoModel)
            .filter(SolicitacaoDocumentoModel.aluno_id == aluno.id)
            .order_by(SolicitacaoDocumentoModel.id.desc())
            .limit(12)
            .all()
        )
        disciplinas = (
            db.query(DisciplinaModel)
            .join(
                TurmaDisciplinaModel,
                TurmaDisciplinaModel.disciplina_id == DisciplinaModel.id,
            )
            .join(AlunoTurmaModel, AlunoTurmaModel.turma_id == TurmaDisciplinaModel.turma_id)
            .filter(AlunoTurmaModel.aluno_id == aluno.id)
            .order_by(DisciplinaModel.nome.asc())
            .distinct()
            .all()
        )

        disciplinas_map = {
            disciplina.id: {
                "id": disciplina.id,
                "nome": disciplina.nome,
                "codigo": disciplina.codigo,
                "carga_horaria": disciplina.carga_horaria,
                "professores": [],
                "atividades": [],
            }
            for disciplina in disciplinas
        }

        if disciplinas_map:
            turma_ids = [
                turma_id
                for (turma_id,) in (
                    db.query(AlunoTurmaModel.turma_id)
                    .filter(AlunoTurmaModel.aluno_id == aluno.id)
                    .all()
                )
            ]
            professor_links = (
                db.query(ProfessorDisciplinaModel.disciplina_id, ProfessorModel.nome)
                .join(ProfessorModel, ProfessorModel.id == ProfessorDisciplinaModel.professor_id)
                .join(
                    ProfessorTurmaModel,
                    ProfessorTurmaModel.professor_id == ProfessorDisciplinaModel.professor_id,
                )
                .join(AlunoTurmaModel, AlunoTurmaModel.turma_id == ProfessorTurmaModel.turma_id)
                .filter(ProfessorDisciplinaModel.disciplina_id.in_(disciplinas_map.keys()))
                .filter(AlunoTurmaModel.aluno_id == aluno.id)
                .order_by(ProfessorModel.nome.asc())
                .distinct()
                .all()
            )
            for disciplina_id, professor_name in professor_links:
                if disciplina_id in disciplinas_map:
                    disciplinas_map[disciplina_id]["professores"].append(professor_name)

            if turma_ids:
                atividade_rows = (
                    db.query(AtividadeModel, DisciplinaModel, ProfessorModel)
                    .join(DisciplinaModel, DisciplinaModel.id == AtividadeModel.disciplina_id)
                    .join(ProfessorModel, ProfessorModel.id == AtividadeModel.professor_id)
                    .filter(AtividadeModel.turma_id.in_(turma_ids))
                    .filter(AtividadeModel.disciplina_id.in_(disciplinas_map.keys()))
                    .order_by(AtividadeModel.id.desc())
                    .limit(80)
                    .all()
                )
                for atividade, disciplina, professor in atividade_rows:
                    disciplinas_map[disciplina.id]["atividades"].append(
                        {
                            "titulo": atividade.titulo,
                            "descricao": atividade.descricao or "Sem descricao.",
                            "professor": professor.nome,
                            "data_entrega": atividade.data_entrega or "Sem prazo",
                            "arquivo": atividade.caminho_arquivo,
                            "data": format_created_at(atividade.created_at),
                        }
                    )

        return {
            "aluno": {
                "id": aluno.id,
                "nome": aluno.nome,
                "email": email,
                "matricula": aluno.matricula,
                "curso": aluno.curso_serie or "Nao informado",
                "status": aluno.status_matricula or "Nao informado",
                "foto_perfil": aluno.foto_perfil,
            },
            "disciplinas": list(disciplinas_map.values()),
            "notas": [
                {
                    "disciplina": disciplina_nome,
                    "nota": nota.nota,
                    "observacao": nota.observacao or "-",
                    "data": format_created_at(nota.data_lancamento),
                }
                for nota, disciplina_nome in notas
            ],
            "documentos": [
                {
                    "titulo": documento.titulo,
                    "arquivo": documento.caminho_arquivo,
                    "data": format_created_at(documento.data_envio),
                }
                for documento in documentos
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
                for solicitacao in solicitacoes
            ],
        }
    finally:
        db.close()


def get_aluno_disciplina_detail(user_id, disciplina_id):
    db = get_session()
    try:
        row = (
            db.query(AlunoModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == AlunoModel.usuario_id)
            .filter(AlunoModel.usuario_id == user_id)
            .first()
        )
        if not row:
            return None

        aluno, email = row
        disciplina = (
            db.query(DisciplinaModel)
            .join(TurmaDisciplinaModel, TurmaDisciplinaModel.disciplina_id == DisciplinaModel.id)
            .join(AlunoTurmaModel, AlunoTurmaModel.turma_id == TurmaDisciplinaModel.turma_id)
            .filter(AlunoTurmaModel.aluno_id == aluno.id)
            .filter(DisciplinaModel.id == disciplina_id)
            .first()
        )
        if not disciplina:
            return None

        turma_ids = [
            turma_id
            for (turma_id,) in (
                db.query(AlunoTurmaModel.turma_id)
                .join(
                    TurmaDisciplinaModel,
                    TurmaDisciplinaModel.turma_id == AlunoTurmaModel.turma_id,
                )
                .filter(AlunoTurmaModel.aluno_id == aluno.id)
                .filter(TurmaDisciplinaModel.disciplina_id == disciplina.id)
                .all()
            )
        ]
        professores = (
            db.query(ProfessorModel.nome)
            .join(ProfessorDisciplinaModel, ProfessorDisciplinaModel.professor_id == ProfessorModel.id)
            .join(ProfessorTurmaModel, ProfessorTurmaModel.professor_id == ProfessorModel.id)
            .filter(ProfessorDisciplinaModel.disciplina_id == disciplina.id)
            .filter(ProfessorTurmaModel.turma_id.in_(turma_ids))
            .order_by(ProfessorModel.nome.asc())
            .distinct()
            .all()
            if turma_ids
            else []
        )
        atividades = (
            db.query(AtividadeModel, ProfessorModel)
            .join(ProfessorModel, ProfessorModel.id == AtividadeModel.professor_id)
            .filter(AtividadeModel.turma_id.in_(turma_ids))
            .filter(AtividadeModel.disciplina_id == disciplina.id)
            .order_by(AtividadeModel.id.desc())
            .all()
            if turma_ids
            else []
        )

        return {
            "aluno": {
                "id": aluno.id,
                "nome": aluno.nome,
                "email": email,
                "matricula": aluno.matricula,
                "curso": aluno.curso_serie or "Nao informado",
                "status": aluno.status_matricula or "Nao informado",
                "foto_perfil": aluno.foto_perfil,
            },
            "disciplina": {
                "id": disciplina.id,
                "nome": disciplina.nome,
                "codigo": disciplina.codigo,
                "carga_horaria": disciplina.carga_horaria,
                "professores": [nome for (nome,) in professores],
            },
            "atividades": [
                {
                    "titulo": atividade.titulo,
                    "descricao": atividade.descricao or "Sem descricao.",
                    "professor": professor.nome,
                    "data_entrega": atividade.data_entrega or "Sem prazo",
                    "arquivo": atividade.caminho_arquivo,
                    "data": format_created_at(atividade.created_at),
                }
                for atividade, professor in atividades
            ],
        }
    finally:
        db.close()


def get_aluno_document_request(solicitacao_id, aluno_id):
    db = get_session()
    try:
        solicitacao = (
            db.query(SolicitacaoDocumentoModel)
            .filter(
                SolicitacaoDocumentoModel.id == solicitacao_id,
                SolicitacaoDocumentoModel.aluno_id == aluno_id,
            )
            .first()
        )
        if not solicitacao:
            return None

        return {
            "id": solicitacao.id,
            "titulo": solicitacao.titulo,
            "status": solicitacao.status,
        }
    finally:
        db.close()


def marcar_documento_aluno_enviado(solicitacao_id, aluno_id, documento_id):
    db = get_session()
    try:
        solicitacao = (
            db.query(SolicitacaoDocumentoModel)
            .filter(
                SolicitacaoDocumentoModel.id == solicitacao_id,
                SolicitacaoDocumentoModel.aluno_id == aluno_id,
            )
            .first()
        )
        if not solicitacao:
            return

        solicitacao.documento_id = documento_id
        solicitacao.status = "enviado"
        solicitacao.completed_at = datetime.now()
        db.commit()
    finally:
        db.close()
