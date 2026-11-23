"""Regras de autoria, publicação, oferta e autorização de cursos."""
import re
from urllib.parse import urlsplit, parse_qs
from flask import abort
from sqlalchemy import func
from app.models import (AlunoModel, AlunoTurmaModel, ProfessorModel, ProfessorDisciplinaModel,
                        ProfessorTurmaModel, TurmaModel, TurmaDisciplinaModel)
from app.models.curso_model import (CursoModel, CapituloModel, TemaModel, AulaModel,
    AtribuicaoDocenteModel, EstadoTurmaModel, OfertaCursoModel, ProgressoAulaModel, AuditoriaCursoModel)


def titulo(value):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= 150:
        abort(400, 'Informe um título com até 150 caracteres.')
    return value.strip()


def texto(value):
    if not isinstance(value, str) or len(value) > 10000:
        abort(400, 'Descrição inválida (máximo de 10.000 caracteres).')
    return value.strip()


def inteiro(data, key):
    try:
        value = data.get(key)
        if isinstance(value, bool) or not re.fullmatch(r'[1-9][0-9]*', str(value)):
            raise ValueError
        return int(value)
    except (ValueError, TypeError):
        abort(400, f'Identificador inválido: {key}.')


def video_id(value):
    if not isinstance(value, str):
        abort(400, 'Informe um link do YouTube ou identificador válido.')
    candidate = value.strip()
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', candidate):
        try:
            url = urlsplit(candidate)
            if url.scheme != 'https' or url.username or url.password or url.port or url.fragment:
                raise ValueError
            if url.hostname == 'youtu.be':
                candidate = url.path.lstrip('/')
            elif url.hostname in {'youtube.com', 'www.youtube.com', 'www.youtube-nocookie.com'}:
                if url.path == '/watch':
                    candidate = parse_qs(url.query).get('v', [''])[0]
                elif re.fullmatch(r'/(embed|shorts)/[A-Za-z0-9_-]{11}', url.path):
                    candidate = url.path.rsplit('/', 1)[-1]
                else:
                    raise ValueError
            else:
                raise ValueError
        except ValueError:
            abort(400, 'Use um link HTTPS válido do YouTube.')
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', candidate):
        abort(400, 'Identificador de vídeo inválido.')
    return candidate


def professor(db, user_id):
    row = db.query(ProfessorModel).filter_by(usuario_id=user_id).first()
    if not row:
        abort(403, 'Cadastro de professor necessário.')
    return row


def obter(db, model, identity):
    row = db.get(model, identity)
    if row is None:
        abort(404)
    return row


def turma_ativa(db, turma_id):
    state = db.get(EstadoTurmaModel, turma_id)
    return not (state and state.arquivada)


def autoria(db, curso_id, user_id, role, editar=False):
    curso = db.query(CursoModel).filter_by(id=curso_id).with_for_update().first()
    if curso is None:
        abort(404)
    if role not in {'admin', 'superadmin'}:
        if role != 'professor' or curso.professor_id != professor(db, user_id).id:
            abort(403)
        # Revogar a disciplina também revoga a autoria, preservando o material.
        if not db.query(ProfessorDisciplinaModel).filter_by(
                professor_id=curso.professor_id, disciplina_id=curso.disciplina_id).first():
            abort(403)
    if editar and curso.estado != 'rascunho':
        abort(409, 'Curso publicado é preservado. Duplique para preparar uma nova edição.')
    return curso


def estrutura(db, curso_id):
    result = []
    for cap in db.query(CapituloModel).filter_by(curso_id=curso_id).order_by(CapituloModel.posicao):
        temas = []
        for tema in db.query(TemaModel).filter_by(capitulo_id=cap.id).order_by(TemaModel.posicao):
            aulas = list(db.query(AulaModel).filter_by(tema_id=tema.id).order_by(AulaModel.posicao))
            temas.append({'tema': tema, 'aulas': aulas})
        result.append({'capitulo': cap, 'temas': temas})
    return result


def aulas_curso(db, curso_id):
    return db.query(AulaModel).join(TemaModel, AulaModel.tema_id == TemaModel.id).join(
        CapituloModel, TemaModel.capitulo_id == CapituloModel.id).filter(CapituloModel.curso_id == curso_id).order_by(
        CapituloModel.posicao, TemaModel.posicao, AulaModel.posicao).all()


def acesso_oferta(db, oferta_id, user_id, role):
    if role != 'aluno':
        abort(403)
    oferta = obter(db, OfertaCursoModel, oferta_id)
    curso = obter(db, CursoModel, oferta.curso_id)
    vinculo = obter(db, TurmaDisciplinaModel, oferta.turma_disciplina_id)
    aluno = db.query(AlunoModel).filter_by(usuario_id=user_id).first()
    if (not aluno or not oferta.ativa or curso.estado != 'publicado'
            or not turma_ativa(db, vinculo.turma_id)
            or str(aluno.status_matricula or '').lower() in {'inativo', 'inativa', 'cancelado', 'cancelada', 'trancado', 'trancada'}
            or not db.query(AlunoTurmaModel).filter_by(aluno_id=aluno.id, turma_id=vinculo.turma_id).first()):
        abort(404)
    return oferta, curso, aluno


def auditar(db, user_id, acao, recurso):
    db.add(AuditoriaCursoModel(usuario_id=user_id, acao=acao, recurso=str(recurso)))


def proxima_posicao(db, model, field, parent_id):
    return (db.query(func.max(model.posicao)).filter(field == parent_id).scalar() or 0) + 1


def atribuir(db, professor_id, turma_id, disciplina_id):
    obter(db, ProfessorModel, professor_id)
    obter(db, TurmaModel, turma_id)
    if not turma_ativa(db, turma_id):
        abort(409, 'Turma arquivada.')
    from app.models import DisciplinaModel
    obter(db, DisciplinaModel, disciplina_id)
    vinculo = db.query(TurmaDisciplinaModel).filter_by(turma_id=turma_id, disciplina_id=disciplina_id).first()
    if not vinculo:
        vinculo = TurmaDisciplinaModel(turma_id=turma_id, disciplina_id=disciplina_id)
        db.add(vinculo)
        db.flush()
    # Pares legados continuam alimentando os painéis existentes; nunca concedem novas combinações.
    for model, values in ((ProfessorTurmaModel, {'professor_id': professor_id, 'turma_id': turma_id}),
                          (ProfessorDisciplinaModel, {'professor_id': professor_id, 'disciplina_id': disciplina_id})):
        if not db.query(model).filter_by(**values).first():
            db.add(model(**values))
    row = db.query(AtribuicaoDocenteModel).filter_by(professor_id=professor_id, turma_disciplina_id=vinculo.id).first()
    if row:
        row.ativo = True
    else:
        row = AtribuicaoDocenteModel(professor_id=professor_id, turma_disciplina_id=vinculo.id)
        db.add(row)
    return row


def autoriza_docencia(db, professor_id, turma_id, disciplina_id):
    """Turmas sob gestão explícita nunca herdam o produto cartesiano legado."""
    if not turma_ativa(db, turma_id):
        return False
    # Adoção explícita por turma; turmas antigas continuam funcionando até reconciliação.
    if not db.get(EstadoTurmaModel, turma_id):
        return True
    return db.query(AtribuicaoDocenteModel).join(TurmaDisciplinaModel,
        AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(
        AtribuicaoDocenteModel.professor_id == professor_id,
        AtribuicaoDocenteModel.ativo.is_(True), TurmaDisciplinaModel.turma_id == turma_id,
        TurmaDisciplinaModel.disciplina_id == disciplina_id).first() is not None


def duplicar(db, curso, user_id):
    novo = CursoModel(disciplina_id=curso.disciplina_id, professor_id=curso.professor_id,
                      origem_id=curso.id, titulo=titulo(curso.titulo[:137] + ' (nova edição)'), descricao=curso.descricao)
    db.add(novo)
    db.flush()
    for item in estrutura(db, curso.id):
        cap = item['capitulo']
        nc = CapituloModel(curso_id=novo.id, titulo=cap.titulo, posicao=cap.posicao)
        db.add(nc)
        db.flush()
        for group in item['temas']:
            tema = group['tema']
            nt = TemaModel(capitulo_id=nc.id, titulo=tema.titulo, posicao=tema.posicao)
            db.add(nt)
            db.flush()
            for aula in group['aulas']:
                db.add(AulaModel(tema_id=nt.id, titulo=aula.titulo, descricao=aula.descricao,
                                 video_id=aula.video_id, posicao=aula.posicao))
    auditar(db, user_id, 'duplicar_curso', novo.id)
    return novo
