from datetime import date

from flask import abort
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.controllers.auth_controller import _remove_saved_file, _save_profile_photo
from app.database import get_session
from app.models import (
    AlunoModel,
    AlunoTurmaModel,
    ComunicadoModel,
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


def format_created_at(value):
    if not value:
        return "Sem data"

    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y %H:%M")

    return str(value)


def status_class(status):
    status_normalized = (status or "").strip().lower()
    if status_normalized == "ativo":
        return "status-active"
    if status_normalized == "pendente":
        return "status-pending"
    if status_normalized == "inativo":
        return "status-inactive"

    return "status-neutral"


def format_relative_date(value):
    if not value or not hasattr(value, "date"):
        return "Agora"

    days = (date.today() - value.date()).days
    if days <= 0:
        return "Hoje"
    if days == 1:
        return "Ha 1 dia"

    return f"Ha {days} dias"


def get_admin_data():
    db = get_session()
    try:
        total_alunos = db.query(func.count(AlunoModel.id)).scalar() or 0
        total_professores = db.query(func.count(ProfessorModel.id)).scalar() or 0
        matriculas_pendentes = (
            db.query(func.count(AlunoModel.id))
            .filter(func.lower(func.coalesce(AlunoModel.status_matricula, "")) == "pendente")
            .scalar()
            or 0
        )
        matriculas_hoje = (
            db.query(func.count(AlunoModel.id))
            .filter(func.date(AlunoModel.created_at) == date.today())
            .scalar()
            or 0
        )

        aluno_rows = (
            db.query(AlunoModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == AlunoModel.usuario_id)
            .order_by(AlunoModel.id.desc())
            .limit(100)
            .all()
        )
        professor_rows = (
            db.query(ProfessorModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == ProfessorModel.usuario_id)
            .order_by(ProfessorModel.id.desc())
            .limit(20)
            .all()
        )

        alunos = [
            {
                "id": aluno.id,
                "matricula": aluno.matricula,
                "nome": aluno.nome,
                "email": email,
                "curso": aluno.curso_serie or "Nao informado",
                "status": aluno.status_matricula or "Nao informado",
                "status_class": status_class(aluno.status_matricula),
                "created_at": aluno.created_at,
                "created_at_label": format_created_at(aluno.created_at),
            }
            for aluno, email in aluno_rows
        ]

        professores = [
            {
                "id": professor.id,
                "nome": professor.nome,
                "email": email,
                "cpf": professor.cpf,
                "disciplina": professor.disciplina_principal or "Nao informado",
                "created_at": professor.created_at,
                "created_at_label": format_created_at(professor.created_at),
            }
            for professor, email in professor_rows
        ]

        registros_recentes = [
            {
                "aluno_id": aluno["id"],
                "nome": aluno["nome"],
                "tipo": "Matricula Escolar",
                "detalhe": aluno["curso"],
                "created_at": aluno["created_at"],
                "created_at_label": aluno["created_at_label"],
            }
            for aluno in alunos[:8]
        ] + [
            {
                "aluno_id": None,
                "nome": professor["nome"],
                "tipo": "Cadastro de Professor",
                "detalhe": professor["disciplina"],
                "created_at": professor["created_at"],
                "created_at_label": professor["created_at_label"],
            }
            for professor in professores[:8]
        ]

        registros_recentes.sort(
            key=lambda item: (
                item["created_at"].isoformat()
                if hasattr(item["created_at"], "isoformat")
                else str(item["created_at"] or "")
            ),
            reverse=True,
        )

        return {
            "total_alunos": total_alunos,
            "total_professores": total_professores,
            "matriculas_pendentes": matriculas_pendentes,
            "matriculas_hoje": matriculas_hoje,
            "alunos": alunos,
            "professores": professores,
            "registros_recentes": registros_recentes[:8],
        }
    finally:
        db.close()


def get_comunicados(limit=8):
    db = get_session()
    try:
        comunicados = (
            db.query(ComunicadoModel)
            .order_by(ComunicadoModel.id.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": comunicado.id,
                "titulo": comunicado.titulo,
                "destinatario": comunicado.destinatario,
                "mensagem": comunicado.mensagem,
                "mensagem_resumo": (
                    comunicado.mensagem[:92] + "..."
                    if len(comunicado.mensagem) > 95
                    else comunicado.mensagem
                ),
                "created_at_label": format_relative_date(comunicado.created_at),
            }
            for comunicado in comunicados
        ]
    finally:
        db.close()


def criar_comunicado(data, criado_por=None):
    titulo = (data.get("titulo") or "").strip()
    destinatario = "Geral"
    mensagem = (data.get("mensagem") or "").strip()

    if not titulo or not mensagem:
        return {"erro": "Titulo e mensagem sao obrigatorios"}, 400
    if len(titulo) > 150 or len(mensagem) > 10000:
        return {"erro": "Use ate 150 caracteres no titulo e 10000 na mensagem"}, 400

    db = get_session()
    try:
        comunicado = ComunicadoModel(
            titulo=titulo,
            destinatario=destinatario,
            mensagem=mensagem,
            criado_por=criado_por,
        )
        db.add(comunicado)
        db.commit()
        return {"id": comunicado.id}, 201
    finally:
        db.close()


def get_disciplinas():
    db = get_session()
    try:
        disciplinas = (
            db.query(DisciplinaModel)
            .order_by(DisciplinaModel.nome.asc())
            .all()
        )

        return [
            {
                "id": disciplina.id,
                "nome": disciplina.nome,
                "codigo": disciplina.codigo,
                "carga_horaria": disciplina.carga_horaria,
            }
            for disciplina in disciplinas
        ]
    finally:
        db.close()


def get_disciplinas_page_data():
    db = get_session()
    try:
        disciplinas = (
            db.query(DisciplinaModel)
            .order_by(DisciplinaModel.nome.asc())
            .all()
        )
        professores = (
            db.query(ProfessorModel)
            .order_by(ProfessorModel.nome.asc())
            .limit(200)
            .all()
        )
        professor_vinculos = (
            db.query(ProfessorDisciplinaModel, ProfessorModel, DisciplinaModel)
            .join(ProfessorModel, ProfessorModel.id == ProfessorDisciplinaModel.professor_id)
            .join(DisciplinaModel, DisciplinaModel.id == ProfessorDisciplinaModel.disciplina_id)
            .order_by(ProfessorDisciplinaModel.id.desc())
            .limit(30)
            .all()
        )

        return {
            "disciplinas": [
                {
                    "id": disciplina.id,
                    "nome": disciplina.nome,
                    "codigo": disciplina.codigo,
                    "carga_horaria": disciplina.carga_horaria,
                }
                for disciplina in disciplinas
            ],
            "professores": [
                {
                    "id": professor.id,
                    "nome": professor.nome,
                    "disciplina": professor.disciplina_principal or "Nao informado",
                }
                for professor in professores
            ],
            "professor_vinculos": [
                {
                    "professor": professor.nome,
                    "disciplina": disciplina.nome,
                    "codigo": disciplina.codigo,
                    "data": format_created_at(vinculo.created_at),
                }
                for vinculo, professor, disciplina in professor_vinculos
            ],
        }
    finally:
        db.close()


def criar_disciplina(data):
    nome = (data.get("nome") or "").strip()
    codigo = (data.get("codigo") or "").strip().upper()
    carga_horaria_raw = (data.get("carga_horaria") or "").strip()

    if not nome or not codigo or not carga_horaria_raw:
        return {"erro": "Nome, codigo e carga horaria sao obrigatorios"}, 400

    try:
        carga_horaria = int(carga_horaria_raw)
    except ValueError:
        return {"erro": "Carga horaria deve ser um numero inteiro"}, 400

    if carga_horaria < 0:
        return {"erro": "Carga horaria nao pode ser negativa"}, 400

    db = get_session()
    try:
        disciplina = DisciplinaModel(
            nome=nome[:120],
            codigo=codigo[:30],
            carga_horaria=carga_horaria,
        )
        db.add(disciplina)
        db.commit()
        return {"id": disciplina.id}, 201
    except IntegrityError:
        db.rollback()
        return {"erro": "Codigo de disciplina ja cadastrado"}, 409
    finally:
        db.close()


def associar_professor_disciplina(data):
    professor_id = data.get("professor_id", type=int)
    disciplina_id = data.get("disciplina_id", type=int)

    if not professor_id or not disciplina_id:
        return {"erro": "Professor e disciplina sao obrigatorios"}, 400

    db = get_session()
    try:
        if not db.get(ProfessorModel, professor_id):
            return {"erro": "Professor nao encontrado"}, 404
        if not db.get(DisciplinaModel, disciplina_id):
            return {"erro": "Disciplina nao encontrada"}, 404

        db.add(
            ProfessorDisciplinaModel(
                professor_id=professor_id,
                disciplina_id=disciplina_id,
            )
        )
        db.commit()
        return {"mensagem": "Professor associado a disciplina"}, 201
    except IntegrityError:
        db.rollback()
        return {"erro": "Este professor ja esta associado a esta disciplina"}, 409
    finally:
        db.close()


def get_turmas_page_data():
    db = get_session()
    try:
        turmas = db.query(TurmaModel).order_by(TurmaModel.nome.asc()).all()
        alunos = db.query(AlunoModel).order_by(AlunoModel.nome.asc()).limit(250).all()
        professores = db.query(ProfessorModel).order_by(ProfessorModel.nome.asc()).limit(250).all()
        professor_ids = [professor.id for professor in professores]
        disciplinas_por_professor = {professor.id: [] for professor in professores}
        if professor_ids:
            professor_disciplina_rows = (
                db.query(ProfessorDisciplinaModel, DisciplinaModel)
                .join(DisciplinaModel, DisciplinaModel.id == ProfessorDisciplinaModel.disciplina_id)
                .filter(ProfessorDisciplinaModel.professor_id.in_(professor_ids))
                .order_by(DisciplinaModel.nome.asc())
                .all()
            )
            for vinculo, disciplina in professor_disciplina_rows:
                disciplinas_por_professor.setdefault(vinculo.professor_id, []).append(
                    disciplina.nome
                )
        aluno_vinculos = (
            db.query(AlunoTurmaModel, AlunoModel, TurmaModel)
            .join(AlunoModel, AlunoModel.id == AlunoTurmaModel.aluno_id)
            .join(TurmaModel, TurmaModel.id == AlunoTurmaModel.turma_id)
            .order_by(AlunoTurmaModel.id.desc())
            .limit(40)
            .all()
        )
        professor_vinculos = (
            db.query(ProfessorTurmaModel, ProfessorModel, TurmaModel)
            .join(ProfessorModel, ProfessorModel.id == ProfessorTurmaModel.professor_id)
            .join(TurmaModel, TurmaModel.id == ProfessorTurmaModel.turma_id)
            .order_by(ProfessorTurmaModel.id.desc())
            .limit(40)
            .all()
        )
        disciplina_vinculos = (
            db.query(TurmaDisciplinaModel, TurmaModel, DisciplinaModel)
            .join(TurmaModel, TurmaModel.id == TurmaDisciplinaModel.turma_id)
            .join(DisciplinaModel, DisciplinaModel.id == TurmaDisciplinaModel.disciplina_id)
            .order_by(TurmaDisciplinaModel.id.desc())
            .limit(40)
            .all()
        )

        return {
            "turmas": [
                {
                    "id": turma.id,
                    "nome": turma.nome,
                    "codigo": turma.codigo,
                    "ano_letivo": turma.ano_letivo,
                    "turno": turma.turno or "Nao informado",
                }
                for turma in turmas
            ],
            "alunos": [
                {
                    "id": aluno.id,
                    "nome": aluno.nome,
                    "matricula": aluno.matricula,
                }
                for aluno in alunos
            ],
            "professores": [
                {
                    "id": professor.id,
                    "nome": professor.nome,
                    "disciplinas": (
                        ", ".join(disciplinas_por_professor.get(professor.id) or [])
                        or "Sem disciplina associada"
                    ),
                }
                for professor in professores
            ],
            "aluno_vinculos": [
                {
                    "aluno": aluno.nome,
                    "matricula": aluno.matricula,
                    "turma": turma.nome,
                    "codigo": turma.codigo,
                    "data": format_created_at(vinculo.created_at),
                }
                for vinculo, aluno, turma in aluno_vinculos
            ],
            "professor_vinculos": [
                {
                    "professor": professor.nome,
                    "disciplina": (
                        ", ".join(disciplinas_por_professor.get(professor.id) or [])
                        or "Sem disciplina associada"
                    ),
                    "turma": turma.nome,
                    "codigo": turma.codigo,
                    "data": format_created_at(vinculo.created_at),
                }
                for vinculo, professor, turma in professor_vinculos
            ],
            "disciplina_vinculos": [
                {
                    "turma": turma.nome,
                    "codigo": turma.codigo,
                    "disciplina": disciplina.nome,
                    "disciplina_codigo": disciplina.codigo,
                    "data": format_created_at(vinculo.created_at),
                }
                for vinculo, turma, disciplina in disciplina_vinculos
            ],
        }
    finally:
        db.close()


def criar_turma(data):
    nome = (data.get("nome") or "").strip()
    codigo = (data.get("codigo") or "").strip().upper()
    ano_letivo_raw = (data.get("ano_letivo") or "").strip()
    turno = (data.get("turno") or "").strip()

    if not nome or not codigo or not ano_letivo_raw:
        return {"erro": "Nome, codigo e ano letivo sao obrigatorios"}, 400

    try:
        ano_letivo = int(ano_letivo_raw)
    except ValueError:
        return {"erro": "Ano letivo deve ser um numero inteiro"}, 400

    if ano_letivo < 2000:
        return {"erro": "Ano letivo invalido"}, 400

    db = get_session()
    try:
        turma = TurmaModel(
            nome=nome[:120],
            codigo=codigo[:30],
            ano_letivo=ano_letivo,
            turno=turno[:30] or None,
        )
        db.add(turma)
        db.commit()
        return {"id": turma.id}, 201
    except IntegrityError:
        db.rollback()
        return {"erro": "Codigo de turma ja cadastrado"}, 409
    finally:
        db.close()


def associar_aluno_turma(data):
    aluno_id = data.get("aluno_id", type=int)
    turma_id = data.get("turma_id", type=int)

    if not aluno_id or not turma_id:
        return {"erro": "Aluno e turma sao obrigatorios"}, 400

    db = get_session()
    try:
        if not db.get(AlunoModel, aluno_id):
            return {"erro": "Aluno nao encontrado"}, 404
        if not db.get(TurmaModel, turma_id):
            return {"erro": "Turma nao encontrada"}, 404

        db.add(AlunoTurmaModel(aluno_id=aluno_id, turma_id=turma_id))
        db.commit()
        return {"mensagem": "Aluno associado a turma"}, 201
    except IntegrityError:
        db.rollback()
        return {"erro": "Este aluno ja esta associado a esta turma"}, 409
    finally:
        db.close()


def associar_professor_turma(data):
    professor_id = data.get("professor_id", type=int)
    turma_id = data.get("turma_id", type=int)

    if not professor_id or not turma_id:
        return {"erro": "Professor e turma sao obrigatorios"}, 400

    db = get_session()
    try:
        professor = db.get(ProfessorModel, professor_id)
        if not professor:
            return {"erro": "Professor nao encontrado"}, 404
        if not db.get(TurmaModel, turma_id):
            return {"erro": "Turma nao encontrada"}, 404

        disciplinas_professor = (
            db.query(ProfessorDisciplinaModel)
            .filter(ProfessorDisciplinaModel.professor_id == professor_id)
            .all()
        )
        if not disciplinas_professor:
            return {"erro": "Este professor nao possui disciplinas associadas"}, 400

        db.add(ProfessorTurmaModel(professor_id=professor_id, turma_id=turma_id))
        for vinculo in disciplinas_professor:
            exists = (
                db.query(TurmaDisciplinaModel)
                .filter(
                    TurmaDisciplinaModel.turma_id == turma_id,
                    TurmaDisciplinaModel.disciplina_id == vinculo.disciplina_id,
                )
                .first()
            )
            if not exists:
                db.add(
                    TurmaDisciplinaModel(
                        turma_id=turma_id,
                        disciplina_id=vinculo.disciplina_id,
                    )
                )

        db.commit()
        return {"mensagem": "Professor associado a turma"}, 201
    except IntegrityError:
        db.rollback()
        return {"erro": "Este professor ja esta associado a esta turma"}, 409
    finally:
        db.close()


def request_student_document(aluno_id, data):
    titulo = (data.get("titulo") or "").strip()
    mensagem = (data.get("mensagem") or "").strip()

    if not titulo:
        return {"erro": "Titulo do documento e obrigatorio"}, 400

    db = get_session()
    try:
        aluno = db.get(AlunoModel, aluno_id)
        if not aluno:
            return {"erro": "Aluno nao encontrado"}, 404

        solicitacao = SolicitacaoDocumentoModel(
            aluno_id=aluno.id,
            titulo=titulo[:150],
            mensagem=mensagem or None,
            status="pendente",
        )
        db.add(solicitacao)
        db.commit()
        return {"id": solicitacao.id}, 201
    finally:
        db.close()


def request_professor_document(professor_id, data):
    titulo = (data.get("titulo") or "").strip()
    mensagem = (data.get("mensagem") or "").strip()

    if not titulo:
        return {"erro": "Titulo do documento e obrigatorio"}, 400

    db = get_session()
    try:
        professor = db.get(ProfessorModel, professor_id)
        if not professor:
            return {"erro": "Professor nao encontrado"}, 404

        solicitacao = SolicitacaoDocumentoModel(
            professor_id=professor.id,
            titulo=titulo[:150],
            mensagem=mensagem or None,
            status="pendente",
        )
        db.add(solicitacao)
        db.commit()
        return {"id": solicitacao.id}, 201
    finally:
        db.close()


def _parse_optional_date(value):
    if not value:
        return None

    return date.fromisoformat(value)


def update_student_data(aluno_id, data, files=None):
    foto_perfil, upload_error = _save_profile_photo(files)
    if upload_error:
        return upload_error

    db = get_session()
    try:
        aluno = db.get(AlunoModel, aluno_id)
        if not aluno:
            _remove_saved_file(foto_perfil)
            return {"erro": "Aluno nao encontrado"}, 404

        usuario = db.get(UsuarioModel, aluno.usuario_id)
        if not usuario:
            _remove_saved_file(foto_perfil)
            return {"erro": "Usuario do aluno nao encontrado"}, 404

        nome = (data.get("nome") or "").strip()
        email = (data.get("email") or "").strip()
        matricula = (data.get("matricula") or "").strip()

        if not nome or not email or not matricula:
            _remove_saved_file(foto_perfil)
            return {"erro": "Nome, e-mail e matricula sao obrigatorios"}, 400

        foto_antiga = aluno.foto_perfil
        aluno.nome = nome[:120]
        aluno.cpf = (data.get("cpf") or "").strip()[:14] or None
        aluno.matricula = matricula[:30]
        aluno.curso_serie = (data.get("curso_serie") or "").strip()[:80] or None
        aluno.status_matricula = (data.get("status_matricula") or "").strip()[:20] or None
        aluno.data_nascimento = _parse_optional_date(data.get("data_nascimento"))
        if foto_perfil:
            aluno.foto_perfil = foto_perfil
        usuario.email = email[:120]

        db.commit()
        if foto_perfil:
            _remove_saved_file(foto_antiga)
        return {"mensagem": "Dados do aluno atualizados"}, 200
    except ValueError:
        db.rollback()
        _remove_saved_file(foto_perfil)
        return {"erro": "Data de nascimento deve estar no formato YYYY-MM-DD"}, 400
    except IntegrityError:
        db.rollback()
        _remove_saved_file(foto_perfil)
        return {"erro": "E-mail, CPF ou matricula ja cadastrados"}, 409
    except Exception:
        db.rollback()
        _remove_saved_file(foto_perfil)
        raise
    finally:
        db.close()


def update_professor_data(professor_id, data, files=None):
    foto_perfil, upload_error = _save_profile_photo(files)
    if upload_error:
        return upload_error

    db = get_session()
    try:
        professor = db.get(ProfessorModel, professor_id)
        if not professor:
            _remove_saved_file(foto_perfil)
            return {"erro": "Professor nao encontrado"}, 404

        usuario = db.get(UsuarioModel, professor.usuario_id)
        if not usuario:
            _remove_saved_file(foto_perfil)
            return {"erro": "Usuario do professor nao encontrado"}, 404

        nome = (data.get("nome") or "").strip()
        email = (data.get("email") or "").strip()
        cpf = (data.get("cpf") or "").strip()

        if not nome or not email or not cpf:
            _remove_saved_file(foto_perfil)
            return {"erro": "Nome, e-mail e CPF sao obrigatorios"}, 400

        foto_antiga = professor.foto_perfil
        professor.nome = nome[:120]
        professor.cpf = cpf[:14]
        professor.telefone = (data.get("telefone") or "").strip()[:20] or None
        professor.disciplina_principal = (
            data.get("disciplina_principal") or ""
        ).strip()[:80] or None
        professor.formacao_academica = (
            data.get("formacao_academica") or ""
        ).strip()[:120] or None
        professor.regime_trabalho = (data.get("regime_trabalho") or "").strip()[:50] or None
        professor.data_admissao = _parse_optional_date(data.get("data_admissao"))
        if foto_perfil:
            professor.foto_perfil = foto_perfil
        usuario.email = email[:120]

        db.commit()
        if foto_perfil:
            _remove_saved_file(foto_antiga)
        return {"mensagem": "Dados do professor atualizados"}, 200
    except ValueError:
        db.rollback()
        _remove_saved_file(foto_perfil)
        return {"erro": "Data de admissao deve estar no formato YYYY-MM-DD"}, 400
    except IntegrityError:
        db.rollback()
        _remove_saved_file(foto_perfil)
        return {"erro": "E-mail ou CPF ja cadastrados"}, 409
    except Exception:
        db.rollback()
        _remove_saved_file(foto_perfil)
        raise
    finally:
        db.close()


def get_aluno_detail(aluno_id):
    db = get_session()
    try:
        query = (
            db.query(AlunoModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == AlunoModel.usuario_id)
        )

        if aluno_id:
            aluno_row = query.filter(AlunoModel.id == aluno_id).first()
        else:
            aluno_row = query.order_by(AlunoModel.id.desc()).first()

        if not aluno_row:
            abort(404)

        aluno, email = aluno_row
        documentos = (
            db.query(DocumentoModel)
            .filter(DocumentoModel.aluno_id == aluno.id)
            .order_by(DocumentoModel.id.desc())
            .limit(10)
            .all()
        )
        solicitacoes = (
            db.query(SolicitacaoDocumentoModel)
            .filter(SolicitacaoDocumentoModel.aluno_id == aluno.id)
            .order_by(SolicitacaoDocumentoModel.id.desc())
            .limit(10)
            .all()
        )

        return {
            "aluno": {
                "id": aluno.id,
                "nome": aluno.nome,
                "email": email,
                "cpf": aluno.cpf or "Nao informado",
                "cpf_value": aluno.cpf or "",
                "matricula": aluno.matricula,
                "curso": aluno.curso_serie or "Nao informado",
                "curso_value": aluno.curso_serie or "",
                "foto_perfil": aluno.foto_perfil,
                "status": aluno.status_matricula or "Nao informado",
                "status_value": aluno.status_matricula or "",
                "data_nascimento": (
                    aluno.data_nascimento.strftime("%d/%m/%Y")
                    if aluno.data_nascimento
                    else "Nao informado"
                ),
                "data_nascimento_value": (
                    aluno.data_nascimento.isoformat() if aluno.data_nascimento else ""
                ),
                "created_at_label": format_created_at(aluno.created_at),
            },
            "documentos": [
                {
                    "titulo": documento.titulo,
                    "arquivo": documento.caminho_arquivo,
                    "data_envio": format_created_at(documento.data_envio),
                }
                for documento in documentos
            ],
            "solicitacoes_documentos": [
                {
                    "id": solicitacao.id,
                    "titulo": solicitacao.titulo,
                    "mensagem": solicitacao.mensagem or "Sem instrucoes adicionais.",
                    "status": solicitacao.status,
                    "status_label": "Enviado" if solicitacao.status == "enviado" else "Pendente",
                    "data": format_created_at(solicitacao.created_at),
                }
                for solicitacao in solicitacoes
            ],
        }
    finally:
        db.close()


def get_professor_detail(professor_id):
    db = get_session()
    try:
        query = (
            db.query(ProfessorModel, UsuarioModel.email)
            .join(UsuarioModel, UsuarioModel.id == ProfessorModel.usuario_id)
        )

        if professor_id:
            professor_row = query.filter(ProfessorModel.id == professor_id).first()
        else:
            professor_row = query.order_by(ProfessorModel.id.desc()).first()

        if not professor_row:
            abort(404)

        professor, email = professor_row
        disciplinas = (
            db.query(ProfessorDisciplinaModel, DisciplinaModel)
            .join(DisciplinaModel, DisciplinaModel.id == ProfessorDisciplinaModel.disciplina_id)
            .filter(ProfessorDisciplinaModel.professor_id == professor.id)
            .order_by(ProfessorDisciplinaModel.id.desc())
            .limit(10)
            .all()
        )
        documentos = (
            db.query(DocumentoModel, AlunoModel, DisciplinaModel)
            .join(AlunoModel, AlunoModel.id == DocumentoModel.aluno_id)
            .join(DisciplinaModel, DisciplinaModel.id == DocumentoModel.disciplina_id)
            .filter(DocumentoModel.professor_id == professor.id)
            .order_by(DocumentoModel.id.desc())
            .limit(10)
            .all()
        )
        notas = (
            db.query(NotaModel, AlunoModel, DisciplinaModel)
            .join(AlunoModel, AlunoModel.id == NotaModel.aluno_id)
            .join(DisciplinaModel, DisciplinaModel.id == NotaModel.disciplina_id)
            .filter(NotaModel.professor_id == professor.id)
            .order_by(NotaModel.id.desc())
            .limit(10)
            .all()
        )
        arquivos_professor = (
            db.query(DocumentoModel, DisciplinaModel)
            .join(DisciplinaModel, DisciplinaModel.id == DocumentoModel.disciplina_id)
            .filter(
                DocumentoModel.professor_id == professor.id,
                DocumentoModel.aluno_id.is_(None),
            )
            .order_by(DocumentoModel.id.desc())
            .limit(10)
            .all()
        )
        solicitacoes = (
            db.query(SolicitacaoDocumentoModel)
            .filter(SolicitacaoDocumentoModel.professor_id == professor.id)
            .order_by(SolicitacaoDocumentoModel.id.desc())
            .limit(10)
            .all()
        )

        return {
            "professor": {
                "id": professor.id,
                "nome": professor.nome,
                "email": email,
                "cpf": professor.cpf or "Nao informado",
                "cpf_value": professor.cpf or "",
                "telefone": professor.telefone or "Nao informado",
                "telefone_value": professor.telefone or "",
                "disciplina": professor.disciplina_principal or "Nao informado",
                "disciplina_value": professor.disciplina_principal or "",
                "formacao": professor.formacao_academica or "Nao informado",
                "formacao_value": professor.formacao_academica or "",
                "regime": professor.regime_trabalho or "Nao informado",
                "regime_value": professor.regime_trabalho or "",
                "foto_perfil": professor.foto_perfil,
                "data_admissao": (
                    professor.data_admissao.strftime("%d/%m/%Y")
                    if professor.data_admissao
                    else "Nao informado"
                ),
                "data_admissao_value": (
                    professor.data_admissao.isoformat() if professor.data_admissao else ""
                ),
                "created_at_label": format_created_at(professor.created_at),
            },
            "disciplinas": [
                {
                    "nome": disciplina.nome,
                    "codigo": disciplina.codigo,
                    "carga_horaria": disciplina.carga_horaria,
                    "data": format_created_at(vinculo.created_at),
                }
                for vinculo, disciplina in disciplinas
            ],
            "documentos": [
                {
                    "titulo": documento.titulo,
                    "arquivo": documento.caminho_arquivo,
                    "aluno": aluno.nome,
                    "disciplina": disciplina.nome,
                    "data_envio": format_created_at(documento.data_envio),
                }
                for documento, aluno, disciplina in documentos
            ],
            "arquivos_professor": [
                {
                    "titulo": documento.titulo,
                    "arquivo": documento.caminho_arquivo,
                    "disciplina": disciplina.nome,
                    "data_envio": format_created_at(documento.data_envio),
                }
                for documento, disciplina in arquivos_professor
            ],
            "solicitacoes_documentos": [
                {
                    "id": solicitacao.id,
                    "titulo": solicitacao.titulo,
                    "mensagem": solicitacao.mensagem or "Sem instrucoes adicionais.",
                    "status": solicitacao.status,
                    "status_label": "Enviado" if solicitacao.status == "enviado" else "Pendente",
                    "data": format_created_at(solicitacao.created_at),
                }
                for solicitacao in solicitacoes
            ],
            "notas": [
                {
                    "aluno": aluno.nome,
                    "disciplina": disciplina.nome,
                    "nota": nota.nota,
                    "observacao": nota.observacao or "Sem observacao.",
                    "data": format_created_at(nota.data_lancamento),
                }
                for nota, aluno, disciplina in notas
            ],
        }
    finally:
        db.close()
