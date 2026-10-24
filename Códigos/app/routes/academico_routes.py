from decimal import Decimal
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from app.database import get_session
from app.models import (AlunoModel, AlunoTurmaModel, TurmaModel, TurmaDisciplinaModel, DisciplinaModel, NotaModel)
from app.models.curso_model import EstadoTurmaModel, AtribuicaoDocenteModel
from app.models.academico_model import PeriodoLetivoModel, AvaliacaoModel, LancamentoNotaModel
from app.services import cursos, academico as service
from app.routes.curso_routes import identidade, dados

academico_bp = Blueprint('academico', __name__)


def resposta(endpoint, status=200, **values):
    if request.is_json:
        return jsonify(values), status
    flash('Alteração acadêmica salva.', 'success')
    return redirect(url_for(endpoint, **values))


@academico_bp.errorhandler(HTTPException)
def erro(exc):
    if request.is_json or request.args.get('formato') == 'json':
        return jsonify(erro=exc.description), exc.code
    return render_template('academico_erro.html', error=exc.description), exc.code


@academico_bp.errorhandler(IntegrityError)
def conflito(exc):
    if request.is_json:
        return jsonify(erro='Registro duplicado ou conflito de gravação. Recarregue a página.'), 409
    return render_template('academico_erro.html', error='Registro duplicado ou conflito. Recarregue a página.'), 409


@academico_bp.get('/academico')
def painel():
    user_id, role = identidade()
    if role == 'aluno':
        return redirect(url_for('academico.meu_boletim'))
    with get_session() as db:
        vinculos = db.query(TurmaDisciplinaModel, TurmaModel, DisciplinaModel).join(TurmaModel,
            TurmaDisciplinaModel.turma_id == TurmaModel.id).join(DisciplinaModel,
            TurmaDisciplinaModel.disciplina_id == DisciplinaModel.id)
        if role == 'professor':
            prof = cursos.professor(db, user_id)
            vinculos = vinculos.join(AtribuicaoDocenteModel,
                AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(
                AtribuicaoDocenteModel.professor_id == prof.id, AtribuicaoDocenteModel.ativo.is_(True))
        offers = vinculos.order_by(TurmaModel.ano_letivo.desc(), TurmaModel.nome, DisciplinaModel.nome).all()
        ids = [v.id for v, _, _ in offers]
        turmas_ids = {t.id for _, t, _ in offers}
        avaliacoes = db.query(AvaliacaoModel).filter(AvaliacaoModel.turma_disciplina_id.in_(ids)).order_by(AvaliacaoModel.id).all()
        periodos = db.query(PeriodoLetivoModel).order_by(PeriodoLetivoModel.ordem).all()
        turmas = db.query(TurmaModel).order_by(TurmaModel.ano_letivo.desc()).all() if role != 'professor' else [t for t in db.query(TurmaModel) if t.id in turmas_ids]
        if request.args.get('formato') == 'json':
            return jsonify(vinculos=[{'id': v.id, 'turma_id': t.id, 'ano': t.ano_letivo,
                'disciplina_id': d.id, 'disciplina': d.nome} for v, t, d in offers],
                periodos=[{'id': p.id, 'turma_id': p.turma_id, 'nome': p.nome, 'fechado': p.fechado}
                          for p in periodos if role != 'professor' or p.turma_id in turmas_ids])
        return render_template('academico_painel.html', vinculos=offers, avaliacoes=avaliacoes,
            periodos=periodos, turmas=turmas, periodo_map={p.id: p for p in periodos},
            estados={e.turma_id: e for e in db.query(EstadoTurmaModel)})


@academico_bp.post('/academico/periodos')
def criar_periodo():
    user_id, _ = identidade(admin=True)
    data = dados()
    with get_session() as db:
        turma_id = cursos.inteiro(data, 'turma_id')
        turma = db.query(TurmaModel).filter_by(id=turma_id).with_for_update().first()
        if not turma:
            abort(404)
        if not cursos.turma_ativa(db, turma_id):
            abort(409, 'Turma arquivada.')
        nome = cursos.titulo(data.get('nome'))
        if len(nome) > 80:
            abort(400, 'Nome do período deve ter até 80 caracteres.')
        ordem = cursos.inteiro(data, 'ordem')
        if ordem > 24:
            abort(400, 'A ordem do período deve estar entre 1 e 24.')
        row = PeriodoLetivoModel(turma_id=turma_id, nome=nome, ordem=ordem,
                                media_referencia=service.decimal_limitado(data.get('media_referencia', '6')))
        db.add(row)
        db.flush()
        service.auditar(db, user_id, 'criar_periodo', row.id)
        db.commit()
        return resposta('academico.painel', 201, periodo_id=row.id)


@academico_bp.post('/academico/periodos/<int:periodo_id>/estado')
def estado_periodo(periodo_id):
    user_id, _ = identidade(admin=True)
    data = dados()
    if data.get('estado') not in {'aberto', 'fechado'}:
        abort(400)
    motivo = data.get('motivo', '')
    if not isinstance(motivo, str) or not 5 <= len(motivo.strip()) <= 500:
        abort(400, 'Informe o motivo do fechamento ou reabertura (5 a 500 caracteres).')
    with get_session() as db:
        row = db.query(PeriodoLetivoModel).filter_by(id=periodo_id).with_for_update().first()
        if not row:
            abort(404)
        if not cursos.turma_ativa(db, row.turma_id):
            abort(409, 'Turma arquivada.')
        row.fechado = data.get('estado') == 'fechado'
        service.auditar(db, user_id, 'periodo_' + data.get('estado'), row.id, {'motivo': motivo.strip()})
        db.commit()
    return resposta('academico.painel')


@academico_bp.post('/academico/avaliacoes')
def criar_avaliacao():
    user_id, role = identidade()
    data = dados()
    with get_session() as db:
        vinculo = cursos.obter(db, TurmaDisciplinaModel, cursos.inteiro(data, 'turma_disciplina_id'))
        service.docente_exato(db, user_id, role, vinculo)
        if not db.get(EstadoTurmaModel, vinculo.turma_id):
            abort(409, 'A secretaria precisa reconciliar esta turma antes de usar o novo diário.')
        periodo = service.periodo_mutavel(db, cursos.inteiro(data, 'periodo_id'))
        if periodo.turma_id != vinculo.turma_id:
            abort(400, 'Período de outra turma.')
        row = AvaliacaoModel(turma_disciplina_id=vinculo.id, periodo_id=periodo.id,
            titulo=cursos.titulo(data.get('titulo')), peso=service.decimal_limitado(data.get('peso', '1'), Decimal('.01'), Decimal('100')))
        db.add(row)
        db.flush()
        service.auditar(db, user_id, 'criar_avaliacao', row.id)
        db.commit()
        return resposta('academico.diario', 201, avaliacao_id=row.id)


@academico_bp.get('/academico/avaliacoes/<int:avaliacao_id>')
def diario(avaliacao_id):
    user_id, role = identidade()
    with get_session() as db:
        avaliacao, vinculo, periodo = service.avaliacao_autorizada(db, avaliacao_id, user_id, role)
        alunos = db.query(AlunoModel).join(AlunoTurmaModel, AlunoTurmaModel.aluno_id == AlunoModel.id).filter(
            AlunoTurmaModel.turma_id == vinculo.turma_id).order_by(AlunoModel.nome).all()
        notas = {n.aluno_id: n for n in db.query(LancamentoNotaModel).filter_by(avaliacao_id=avaliacao_id)}
        if request.args.get('formato') == 'json':
            return jsonify(avaliacao_id=avaliacao.id, publicada=avaliacao.publicada, periodo=periodo.nome,
                alunos=[{'id': a.id, 'nome': a.nome, 'valor': str(notas[a.id].valor) if a.id in notas else None,
                         'versao': notas[a.id].versao if a.id in notas else 0} for a in alunos])
        return render_template('academico_diario.html', avaliacao=avaliacao, periodo=periodo,
            turma=cursos.obter(db, TurmaModel, vinculo.turma_id), disciplina=cursos.obter(db, DisciplinaModel, vinculo.disciplina_id),
            alunos=alunos, notas=notas, ativa=cursos.turma_ativa(db, vinculo.turma_id))


@academico_bp.post('/academico/avaliacoes/<int:avaliacao_id>/alunos/<int:aluno_id>')
def lancar(avaliacao_id, aluno_id):
    user_id, role = identidade()
    data = dados()
    with get_session() as db:
        row = service.salvar_nota(db, avaliacao_id, aluno_id, data, user_id, role)
        db.commit()
        return resposta('academico.diario', avaliacao_id=avaliacao_id, versao=row.versao)


@academico_bp.post('/academico/avaliacoes/<int:avaliacao_id>/publicar')
def publicar(avaliacao_id):
    user_id, role = identidade()
    with get_session() as db:
        avaliacao, _, _ = service.avaliacao_autorizada(db, avaliacao_id, user_id, role, mutacao=True)
        avaliacao.publicada = True
        service.auditar(db, user_id, 'publicar_avaliacao', avaliacao_id)
        db.commit()
    return resposta('academico.diario', avaliacao_id=avaliacao_id)


@academico_bp.post('/academico/avaliacoes/<int:avaliacao_id>/configurar')
def configurar_avaliacao(avaliacao_id):
    user_id, role = identidade()
    data = dados()
    with get_session() as db:
        avaliacao, _, _ = service.avaliacao_autorizada(db, avaliacao_id, user_id, role, mutacao=True)
        if avaliacao.publicada:
            abort(409, 'A composição de uma avaliação publicada é preservada.')
        if data.get('acao') == 'remover':
            if db.query(LancamentoNotaModel).filter_by(avaliacao_id=avaliacao_id).first():
                abort(409, 'Avaliação com notas precisa ser preservada.')
            db.delete(avaliacao)
            service.auditar(db, user_id, 'remover_avaliacao_vazia', avaliacao_id)
        elif data.get('acao') == 'salvar':
            anterior = {'titulo': avaliacao.titulo, 'peso': str(avaliacao.peso)}
            avaliacao.titulo = cursos.titulo(data.get('titulo'))
            avaliacao.peso = service.decimal_limitado(data.get('peso'), Decimal('.01'), Decimal('100'))
            service.auditar(db, user_id, 'editar_avaliacao', avaliacao_id, {'anterior': anterior,
                'novo': {'titulo': avaliacao.titulo, 'peso': str(avaliacao.peso)}})
        else:
            abort(400)
        db.commit()
    return resposta('academico.painel')


def render_boletim(db, aluno):
    result = service.boletim(db, aluno.id)
    if request.args.get('formato') == 'json':
        return jsonify(aluno_id=aluno.id, **result)
    return render_template('academico_boletim.html', aluno=aluno, **result)


@academico_bp.get('/boletim')
def meu_boletim():
    user_id, role = identidade()
    if role != 'aluno':
        abort(403)
    with get_session() as db:
        aluno = db.query(AlunoModel).filter_by(usuario_id=user_id).first()
        if not aluno:
            abort(404)
        return render_boletim(db, aluno)


@academico_bp.get('/academico/alunos/<int:aluno_id>/boletim')
def boletim_admin(aluno_id):
    identidade(admin=True)
    with get_session() as db:
        return render_boletim(db, cursos.obter(db, AlunoModel, aluno_id))


@academico_bp.get('/academico/reconciliar')
def lista_reconciliacao():
    identidade(admin=True)
    with get_session() as db:
        return render_template('academico_reconciliar.html', turmas=db.query(TurmaModel).order_by(TurmaModel.ano_letivo.desc()).all(),
            estados={e.turma_id: e for e in db.query(EstadoTurmaModel)})


@academico_bp.route('/academico/reconciliar/<int:turma_id>', methods=['GET', 'POST'])
def reconciliar(turma_id):
    user_id, _ = identidade(admin=True)
    with get_session() as db:
        if request.method == 'POST':
            data = dados()
            escolhas = data.get('confirmadas') if request.is_json else request.form.getlist('confirmadas')
            service.reconciliar(db, turma_id, escolhas, data.get('revisao'), user_id)
            db.commit()
            return resposta('academico.reconciliar', turma_id=turma_id)
        turma, pares, revisao, ativos = service.candidatos_reconciliacao(db, turma_id)
        if request.args.get('formato') == 'json':
            return jsonify(turma_id=turma.id, revisao=revisao,
                candidatos=[{'chave': f'{p.id}:{d.id}', 'professor': p.nome, 'disciplina': d.nome,
                             'ativa': f'{p.id}:{d.id}' in ativos} for p, d in pares])
        return render_template('academico_reconciliar.html', turma=turma, pares=pares, revisao=revisao, ativos=ativos)


@academico_bp.get('/academico/notas-antigas')
def notas_antigas():
    identidade(admin=True)
    with get_session() as db:
        rows = db.query(NotaModel, AlunoModel, DisciplinaModel).join(AlunoModel, NotaModel.aluno_id == AlunoModel.id).join(
            DisciplinaModel, NotaModel.disciplina_id == DisciplinaModel.id).order_by(NotaModel.id).all()
        ids = {n.nota_legada_id for n in db.query(LancamentoNotaModel).filter(LancamentoNotaModel.nota_legada_id.is_not(None))}
        destinos = {}
        for nota, _, _ in rows:
            destinos[nota.id] = db.query(AvaliacaoModel, PeriodoLetivoModel, TurmaModel).join(PeriodoLetivoModel,
                AvaliacaoModel.periodo_id == PeriodoLetivoModel.id).join(TurmaDisciplinaModel,
                AvaliacaoModel.turma_disciplina_id == TurmaDisciplinaModel.id).join(TurmaModel,
                TurmaDisciplinaModel.turma_id == TurmaModel.id).join(AlunoTurmaModel,
                AlunoTurmaModel.turma_id == TurmaModel.id).filter(AlunoTurmaModel.aluno_id == nota.aluno_id,
                TurmaDisciplinaModel.disciplina_id == nota.disciplina_id, PeriodoLetivoModel.fechado.is_(False),
                AvaliacaoModel.publicada.is_(False)).all()
        return render_template('academico_legadas.html', notas=rows, migradas=ids, destinos=destinos)


@academico_bp.post('/academico/notas-antigas/<int:nota_id>/vincular')
def vincular_nota(nota_id):
    user_id, role = identidade(admin=True)
    data = dados()
    with get_session() as db:
        nota = cursos.obter(db, NotaModel, nota_id)
        avaliacao, vinculo, _ = service.avaliacao_autorizada(db, cursos.inteiro(data, 'avaliacao_id'), user_id, role, mutacao=True)
        if avaliacao.publicada:
            abort(409, 'Importe em uma avaliação em rascunho e revise antes de publicar.')
        if nota.disciplina_id != vinculo.disciplina_id or not db.query(AlunoTurmaModel).filter_by(
                aluno_id=nota.aluno_id, turma_id=vinculo.turma_id).first():
            abort(400, 'Disciplina ou matrícula incompatível com o destino confirmado.')
        if str(data.get('valor_confirmado')) != str(nota.nota):
            abort(409, 'A nota de origem mudou. Revise novamente.')
        if db.query(LancamentoNotaModel).filter_by(nota_legada_id=nota_id).first() or db.query(LancamentoNotaModel).filter_by(
                aluno_id=nota.aluno_id, avaliacao_id=avaliacao.id).first():
            abort(409, 'Nota já vinculada ou destino já possui lançamento.')
        db.add(LancamentoNotaModel(avaliacao_id=avaliacao.id, aluno_id=nota.aluno_id, professor_id=nota.professor_id,
            valor=nota.nota, observacao=nota.observacao or '', versao=1, nota_legada_id=nota.id))
        service.auditar(db, user_id, 'vincular_nota_antiga', nota.id, {'avaliacao': avaliacao.id, 'valor': str(nota.nota)})
        db.commit()
    return resposta('academico.notas_antigas')
