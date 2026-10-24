"""Biblioteca de cursos e gestão de ofertas por turma/ano."""
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from app.database import get_session
from app.models import (DisciplinaModel, ProfessorModel, ProfessorDisciplinaModel, TurmaModel,
                        TurmaDisciplinaModel, AlunoModel, AlunoTurmaModel)
from app.models.curso_model import (CursoModel, CapituloModel, TemaModel, AulaModel, OfertaCursoModel,
    ProgressoAulaModel, AtribuicaoDocenteModel, EstadoTurmaModel)
from app.services import cursos as service

cursos_bp = Blueprint('cursos', __name__)


def identidade(admin=False):
    role = session.get('user_role')
    if not session.get('user_id') or role not in ({'admin', 'superadmin'} if admin else {'admin', 'superadmin', 'professor', 'aluno'}):
        abort(403)
    return session['user_id'], role


def dados():
    data = request.get_json(silent=True) if request.is_json else request.form
    if not isinstance(data, dict) and not hasattr(data, 'getlist'):
        abort(400, 'Dados inválidos.')
    return data


def sucesso(endpoint, status=200, **values):
    if request.is_json:
        return jsonify(values), status
    flash('Alteração salva.', 'success')
    return redirect(url_for(endpoint, **values))


@cursos_bp.errorhandler(HTTPException)
def erro_http(exc):
    if request.is_json:
        return jsonify(erro=exc.description), exc.code
    return render_template('curso_erro.html', error=exc.description), exc.code


@cursos_bp.errorhandler(IntegrityError)
def conflito(exc):
    if request.is_json:
        return jsonify(erro='Conflito de gravação. Recarregue e tente novamente.'), 409
    return render_template('curso_erro.html', error='Conflito de gravação. Recarregue e tente novamente.'), 409


@cursos_bp.get('/cursos')
def biblioteca():
    user_id, role = identidade()
    with get_session() as db:
        if role == 'aluno':
            cards = []
            for oferta in db.query(OfertaCursoModel).filter_by(ativa=True):
                try:
                    _, curso, aluno = service.acesso_oferta(db, oferta.id, user_id, role)
                except HTTPException as exc:
                    if exc.code == 404:
                        continue
                    raise
                vinculo = db.get(TurmaDisciplinaModel, oferta.turma_disciplina_id)
                turma = db.get(TurmaModel, vinculo.turma_id)
                aulas = service.aulas_curso(db, curso.id)
                concluidas = db.query(ProgressoAulaModel).filter_by(aluno_id=aluno.id, oferta_id=oferta.id).count()
                cards.append({'oferta': oferta, 'curso': curso, 'turma': turma,
                              'progresso': round(100 * concluidas / len(aulas)) if aulas else 0})
            return render_template('curso_biblioteca.html', cards=cards, cursos=[], disciplinas=[], professores=[])
        query = db.query(CursoModel)
        disciplinas = db.query(DisciplinaModel)
        if role == 'professor':
            prof = service.professor(db, user_id)
            query = query.filter_by(professor_id=prof.id)
            disciplinas = disciplinas.join(ProfessorDisciplinaModel,
                ProfessorDisciplinaModel.disciplina_id == DisciplinaModel.id).filter(ProfessorDisciplinaModel.professor_id == prof.id)
        return render_template('curso_biblioteca.html', cursos=query.order_by(CursoModel.id.desc()).all(),
            cards=[], disciplinas=disciplinas.all(), professores=db.query(ProfessorModel).all() if role != 'professor' else [])


@cursos_bp.post('/cursos')
def criar():
    user_id, role = identidade()
    if role == 'aluno':
        abort(403)
    data = dados()
    with get_session() as db:
        disciplina_id = service.inteiro(data, 'disciplina_id')
        service.obter(db, DisciplinaModel, disciplina_id)
        prof_id = service.professor(db, user_id).id if role == 'professor' else service.inteiro(data, 'professor_id')
        service.obter(db, ProfessorModel, prof_id)
        if not db.query(ProfessorDisciplinaModel).filter_by(professor_id=prof_id, disciplina_id=disciplina_id).first():
            abort(403, 'Vincule o professor à disciplina antes de criar o curso.')
        curso = CursoModel(disciplina_id=disciplina_id, professor_id=prof_id,
                           titulo=service.titulo(data.get('titulo')), descricao=service.texto(data.get('descricao', '')))
        db.add(curso)
        db.flush()
        service.auditar(db, user_id, 'criar_curso', curso.id)
        db.commit()
        return sucesso('cursos.editor', 201, curso_id=curso.id)


@cursos_bp.get('/cursos/<int:curso_id>')
def editor(curso_id):
    user_id, role = identidade()
    with get_session() as db:
        curso = service.autoria(db, curso_id, user_id, role)
        ofertas = db.query(OfertaCursoModel, TurmaModel).join(TurmaDisciplinaModel,
            OfertaCursoModel.turma_disciplina_id == TurmaDisciplinaModel.id).join(TurmaModel,
            TurmaDisciplinaModel.turma_id == TurmaModel.id).filter(OfertaCursoModel.curso_id == curso_id).all()
        return render_template('curso_editor.html', curso=curso, estrutura=service.estrutura(db, curso_id),
                               ofertas=ofertas, turmas=db.query(TurmaModel).order_by(TurmaModel.ano_letivo.desc()).all())


@cursos_bp.post('/cursos/<int:curso_id>/estrutura')
def editar_estrutura(curso_id):
    user_id, role = identidade()
    data = dados()
    item_id = None
    with get_session() as db:
        curso = service.autoria(db, curso_id, user_id, role, editar=True)
        acao = data.get('acao')
        tipo = data.get('tipo')
        if acao == 'curso':
            curso.titulo = service.titulo(data.get('titulo'))
            curso.descricao = service.texto(data.get('descricao', ''))
        elif tipo in {'capitulo', 'tema', 'aula'}:
            model = {'capitulo': CapituloModel, 'tema': TemaModel, 'aula': AulaModel}[tipo]
            if acao == 'adicionar':
                if tipo == 'capitulo':
                    parent_id, field, values = curso.id, CapituloModel.curso_id, {'curso_id': curso.id}
                elif tipo == 'tema':
                    cap = service.obter(db, CapituloModel, service.inteiro(data, 'pai_id'))
                    if cap.curso_id != curso_id:
                        abort(404)
                    parent_id, field, values = cap.id, TemaModel.capitulo_id, {'capitulo_id': cap.id}
                else:
                    tema = service.obter(db, TemaModel, service.inteiro(data, 'pai_id'))
                    cap = service.obter(db, CapituloModel, tema.capitulo_id)
                    if cap.curso_id != curso_id:
                        abort(404)
                    parent_id, field, values = tema.id, AulaModel.tema_id, {'tema_id': tema.id}
                    values.update(video_id=service.video_id(data.get('video')), descricao=service.texto(data.get('descricao', '')))
                row = model(titulo=service.titulo(data.get('titulo')),
                            posicao=service.proxima_posicao(db, model, field, parent_id), **values)
                db.add(row)
                db.flush()
                item_id = row.id
            elif acao in {'editar', 'remover', 'subir', 'descer'}:
                row = service.obter(db, model, service.inteiro(data, 'id'))
                cap = row if tipo == 'capitulo' else (service.obter(db, CapituloModel, row.capitulo_id) if tipo == 'tema'
                       else service.obter(db, CapituloModel, service.obter(db, TemaModel, row.tema_id).capitulo_id))
                if cap.curso_id != curso_id:
                    abort(404)
                if acao == 'editar':
                    row.titulo = service.titulo(data.get('titulo'))
                    if tipo == 'aula':
                        row.video_id = service.video_id(data.get('video'))
                        row.descricao = service.texto(data.get('descricao', ''))
                elif acao == 'remover':
                    if tipo == 'capitulo' and db.query(TemaModel).filter_by(capitulo_id=row.id).first():
                        abort(409, 'Remova as aulas e os temas antes do capítulo.')
                    if tipo == 'tema' and db.query(AulaModel).filter_by(tema_id=row.id).first():
                        abort(409, 'Remova as aulas antes do tema.')
                    db.delete(row)
                else:
                    field = {'capitulo': CapituloModel.curso_id, 'tema': TemaModel.capitulo_id, 'aula': AulaModel.tema_id}[tipo]
                    parent_id = getattr(row, field.key)
                    candidates = db.query(model).filter(field == parent_id)
                    other = (candidates.filter(model.posicao < row.posicao).order_by(model.posicao.desc()).first() if acao == 'subir'
                             else candidates.filter(model.posicao > row.posicao).order_by(model.posicao).first())
                    if other:
                        previous = row.posicao
                        # A posição temporária não conflita com posições positivas.
                        row.posicao = -row.id
                        db.flush()
                        row_position = other.posicao
                        other.posicao = previous
                        db.flush()
                        row.posicao = row_position
            else:
                abort(400)
        else:
            abort(400)
        service.auditar(db, user_id, 'editar_estrutura', curso_id)
        db.commit()
    return sucesso('cursos.editor', curso_id=curso_id, **({'item_id': item_id} if item_id else {}))


@cursos_bp.post('/cursos/<int:curso_id>/duplicar')
def duplicar(curso_id):
    user_id, role = identidade()
    with get_session() as db:
        curso = service.autoria(db, curso_id, user_id, role)
        novo = service.duplicar(db, curso, user_id)
        db.commit()
        return sucesso('cursos.editor', 201, curso_id=novo.id)


@cursos_bp.post('/cursos/<int:curso_id>/estado')
def estado(curso_id):
    user_id, role = identidade(admin=True)
    data = dados()
    with get_session() as db:
        curso = service.autoria(db, curso_id, user_id, role)
        destino = data.get('estado')
        if destino not in {'publicado', 'arquivado'}:
            abort(400)
        if destino == 'publicado':
            if curso.estado == 'arquivado':
                abort(409, 'Duplique o curso arquivado para uma nova edição.')
            tree = service.estrutura(db, curso_id)
            if not tree or any(not cap['temas'] or any(not tema['aulas'] for tema in cap['temas']) for cap in tree):
                abort(400, 'Preencha os capítulos, temas e ao menos uma aula em cada tema.')
        curso.estado = destino
        service.auditar(db, user_id, 'curso_' + destino, curso_id)
        db.commit()
    return sucesso('cursos.editor', curso_id=curso_id)


@cursos_bp.post('/cursos/<int:curso_id>/ofertas')
def ofertar(curso_id):
    user_id, role = identidade(admin=True)
    data = dados()
    with get_session() as db:
        curso = service.autoria(db, curso_id, user_id, role)
        turma_id = service.inteiro(data, 'turma_id')
        service.obter(db, TurmaModel, turma_id)
        if curso.estado != 'publicado' or not service.turma_ativa(db, turma_id):
            abort(409, 'Publique o curso e selecione uma turma ativa.')
        vinculo = db.query(TurmaDisciplinaModel).filter_by(turma_id=turma_id, disciplina_id=curso.disciplina_id).first()
        if not vinculo:
            abort(400, 'A disciplina precisa estar vinculada à turma.')
        oferta = db.query(OfertaCursoModel).filter_by(curso_id=curso_id, turma_disciplina_id=vinculo.id).first()
        if not oferta:
            oferta = OfertaCursoModel(curso_id=curso_id, turma_disciplina_id=vinculo.id)
            db.add(oferta)
        else:
            oferta.ativa = True
        service.auditar(db, user_id, 'liberar_oferta', f'{curso_id}:{turma_id}')
        db.commit()
        return sucesso('cursos.editor', curso_id=curso_id, oferta_id=oferta.id)


@cursos_bp.post('/cursos/ofertas/<int:oferta_id>/revogar')
def revogar_oferta(oferta_id):
    user_id, _ = identidade(admin=True)
    with get_session() as db:
        oferta = service.obter(db, OfertaCursoModel, oferta_id)
        oferta.ativa = False
        curso_id = oferta.curso_id
        service.auditar(db, user_id, 'revogar_oferta', oferta_id)
        db.commit()
    return sucesso('cursos.editor', curso_id=curso_id)


@cursos_bp.get('/aprender/<int:oferta_id>')
def aprender(oferta_id):
    user_id, role = identidade()
    with get_session() as db:
        oferta, curso, aluno = service.acesso_oferta(db, oferta_id, user_id, role)
        aulas = service.aulas_curso(db, curso.id)
        concluidas = {p.aula_id for p in db.query(ProgressoAulaModel).filter_by(aluno_id=aluno.id, oferta_id=oferta_id)}
        aula_id = request.args.get('aula', type=int)
        atual = next((a for a in aulas if a.id == aula_id), None) if aula_id else next((a for a in aulas if a.id not in concluidas), aulas[0] if aulas else None)
        if aula_id and atual is None:
            abort(404)
        index = aulas.index(atual) if atual else -1
        return render_template('curso_aprender.html', curso=curso, oferta=oferta, estrutura=service.estrutura(db, curso.id),
            atual=atual, concluidas=concluidas, total=len(aulas), progresso=round(100 * len(concluidas) / len(aulas)) if aulas else 0,
            anterior=aulas[index - 1] if index > 0 else None,
            proxima=aulas[index + 1] if 0 <= index < len(aulas) - 1 else None)


@cursos_bp.post('/aprender/<int:oferta_id>/aulas/<int:aula_id>/concluir')
def concluir(oferta_id, aula_id):
    user_id, role = identidade()
    with get_session() as db:
        oferta, curso, aluno = service.acesso_oferta(db, oferta_id, user_id, role)
        if aula_id not in {a.id for a in service.aulas_curso(db, curso.id)}:
            abort(404)
        if not db.query(ProgressoAulaModel).filter_by(aluno_id=aluno.id, oferta_id=oferta_id, aula_id=aula_id).first():
            db.add(ProgressoAulaModel(aluno_id=aluno.id, oferta_id=oferta_id, aula_id=aula_id))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                if not db.query(ProgressoAulaModel).filter_by(aluno_id=aluno.id, oferta_id=oferta_id, aula_id=aula_id).first():
                    raise
    return sucesso('cursos.aprender', oferta_id=oferta_id)


@cursos_bp.route('/admin/gestao-turmas', methods=['GET', 'POST'])
def gestao_turmas():
    user_id, _ = identidade(admin=True)
    with get_session() as db:
        if request.method == 'POST':
            data = dados()
            acao = data.get('acao')
            if acao == 'criar':
                ano = service.inteiro(data, 'ano_letivo')
                if not 1900 <= ano <= 2200:
                    abort(400, 'Ano letivo inválido.')
                codigo = data.get('codigo', '')
                if not isinstance(codigo, str) or not 1 <= len(codigo.strip()) <= 30:
                    abort(400, 'Código obrigatório com até 30 caracteres.')
                turma = TurmaModel(nome=service.titulo(data.get('nome'))[:120], codigo=codigo.strip(), ano_letivo=ano)
                db.add(turma)
                db.flush()
                db.add(EstadoTurmaModel(turma_id=turma.id))
            else:
                turma_id = service.inteiro(data, 'turma_id')
                turma = service.obter(db, TurmaModel, turma_id)
                if acao == 'arquivar':
                    state = db.get(EstadoTurmaModel, turma_id)
                    if not state:
                        state = EstadoTurmaModel(turma_id=turma_id)
                        db.add(state)
                    state.arquivada = True
                elif acao == 'adotar':
                    if not db.get(EstadoTurmaModel, turma_id):
                        db.add(EstadoTurmaModel(turma_id=turma_id))
                elif not service.turma_ativa(db, turma_id):
                    abort(409, 'Turma arquivada.')
                elif acao == 'editar':
                    turma.nome = service.titulo(data.get('nome'))[:120]
                    ano = service.inteiro(data, 'ano_letivo')
                    if not 1900 <= ano <= 2200:
                        abort(400)
                    if ano != turma.ano_letivo and db.query(OfertaCursoModel).join(TurmaDisciplinaModel,
                            OfertaCursoModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(
                            TurmaDisciplinaModel.turma_id == turma_id).first():
                        abort(409, 'A turma já possui cursos. Crie outra turma para o novo ano.')
                    turma.ano_letivo = ano
                elif acao == 'atribuir':
                    # Adoção é explícita: o formulário informa professor, turma e disciplina.
                    if not db.get(EstadoTurmaModel, turma_id):
                        db.add(EstadoTurmaModel(turma_id=turma_id))
                    service.atribuir(db, service.inteiro(data, 'professor_id'), turma_id, service.inteiro(data, 'disciplina_id'))
                elif acao == 'revogar':
                    row = service.obter(db, AtribuicaoDocenteModel, service.inteiro(data, 'atribuicao_id'))
                    if service.obter(db, TurmaDisciplinaModel, row.turma_disciplina_id).turma_id != turma_id:
                        abort(404)
                    row.ativo = False
                elif acao in {'matricular', 'desmatricular'}:
                    aluno_id = service.inteiro(data, 'aluno_id')
                    service.obter(db, AlunoModel, aluno_id)
                    row = db.query(AlunoTurmaModel).filter_by(aluno_id=aluno_id, turma_id=turma_id).first()
                    if acao == 'matricular' and not row:
                        db.add(AlunoTurmaModel(aluno_id=aluno_id, turma_id=turma_id))
                    elif acao == 'desmatricular' and row:
                        db.delete(row)
                else:
                    abort(400)
            service.auditar(db, user_id, 'turma_' + str(acao), turma.id)
            db.commit()
            return sucesso('cursos.gestao_turmas', turma_id=turma.id)
        turmas = db.query(TurmaModel).order_by(TurmaModel.ano_letivo.desc(), TurmaModel.nome).all()
        atribuicoes = db.query(AtribuicaoDocenteModel, TurmaDisciplinaModel, ProfessorModel, DisciplinaModel).join(
            TurmaDisciplinaModel, AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).join(
            ProfessorModel, AtribuicaoDocenteModel.professor_id == ProfessorModel.id).join(
            DisciplinaModel, TurmaDisciplinaModel.disciplina_id == DisciplinaModel.id).all()
        return render_template('curso_turmas.html', turmas=turmas, professores=db.query(ProfessorModel).all(),
            disciplinas=db.query(DisciplinaModel).all(), alunos=db.query(AlunoModel).all(),
            estados={s.turma_id: s for s in db.query(EstadoTurmaModel)}, atribuicoes=atribuicoes)
