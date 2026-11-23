import json
from datetime import timedelta
from flask import Blueprint, abort, jsonify, render_template, request, session, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
from app.database import get_session
from app.models import TurmaModel
from app.models.escola_model import (CalendarioEscolaModel, EventoCalendarioModel, PoliticaEscolaModel, RegraTurmaEscolaModel)
from app.services import escola as service, cursos
from app.services.academico import auditar
from app.routes.curso_routes import dados, identidade

escola_bp = Blueprint('escola', __name__)


def superperfil():
    user_id, role = identidade()
    if role != 'superadmin':
        abort(403)
    return user_id


def sucesso(status=200, **values):
    if request.is_json:
        return jsonify(values), status
    flash('Configuração da escola salva.', 'success')
    return redirect(url_for('escola.configurar'))


@escola_bp.errorhandler(HTTPException)
def erro(exc):
    if request.is_json or request.args.get('formato') == 'json':
        return jsonify(erro=exc.description), exc.code
    return render_template('escola_erro.html', error=exc.description), exc.code


@escola_bp.errorhandler(IntegrityError)
def conflito(exc):
    if request.is_json:
        return jsonify(erro='Registro duplicado ou edição concorrente. Recarregue antes de salvar.'), 409
    return render_template('escola_erro.html', error='Registro duplicado ou edição concorrente.'), 409


@escola_bp.get('/super/escola')
def configurar():
    superperfil()
    with get_session() as db:
        calendarios = db.query(CalendarioEscolaModel).order_by(CalendarioEscolaModel.ano.desc()).all()
        politicas = db.query(PoliticaEscolaModel).order_by(PoliticaEscolaModel.id.desc()).all()
        dados_cal = [{'id': c.id, 'ano': c.ano, 'nome': c.nome, 'inicio': c.inicio.isoformat(), 'fim': c.fim.isoformat(),
                      'versao': c.versao, 'dias_semana': json.loads(c.dias_semana), **service.resumo_calendario(db, c)} for c in calendarios]
        regras = [{'id': p.id, 'nome': p.nome, 'calendario_id': p.calendario_id,
                   **json.loads(p.configuracao)} for p in politicas]
        if request.args.get('formato') == 'json':
            return jsonify(identidade=service.identidade_atual(db), calendarios=dados_cal, politicas=regras)
        return render_template('escola_configurar.html', identidade=service.identidade_atual(db), calendarios=calendarios,
            resumos={c['id']: c for c in dados_cal}, politicas=regras,
            eventos=db.query(EventoCalendarioModel).order_by(EventoCalendarioModel.dia).all(),
            turmas=db.query(TurmaModel).order_by(TurmaModel.ano_letivo.desc(), TurmaModel.nome).all(),
            aplicadas={r.turma_id: r.politica_id for r in db.query(RegraTurmaEscolaModel)})


@escola_bp.post('/super/escola/identidade')
def identidade_visual():
    user_id = superperfil()
    with get_session() as db:
        row = service.salvar_identidade(db, dados(), user_id)
        db.commit()
        return sucesso(versao=row.versao)


@escola_bp.post('/super/escola/calendarios')
def criar_calendario():
    user_id = superperfil()
    data = dados()
    if not request.is_json:
        data = request.form.to_dict()
        data['dias_semana'] = request.form.getlist('dias_semana')
    with get_session() as db:
        row = CalendarioEscolaModel(**service.validar_calendario(data))
        db.add(row)
        db.flush()
        auditar(db, user_id, 'criar_calendario', row.id)
        db.commit()
        return sucesso(201, calendario_id=row.id)


@escola_bp.post('/super/escola/calendarios/<int:calendario_id>/editar')
def editar_calendario(calendario_id):
    user_id = superperfil()
    data = dados()
    if not request.is_json:
        data = request.form.to_dict()
        data['dias_semana'] = request.form.getlist('dias_semana')
    values = service.validar_calendario(data)
    with get_session() as db:
        row = service.calendario_travado(db, calendario_id, data)
        for politica in db.query(PoliticaEscolaModel).filter_by(calendario_id=calendario_id):
            spec = json.loads(politica.configuracao)
            if values['ano'] != row.ano or any(service.data_iso(p['inicio']) < values['inicio'] or service.data_iso(p['fim']) > values['fim'] for p in spec['periodos']):
                abort(409, 'As datas precisam preservar os períodos das políticas vinculadas.')
        if db.query(EventoCalendarioModel).filter(EventoCalendarioModel.calendario_id == calendario_id,
                ((EventoCalendarioModel.dia < values['inicio']) | (EventoCalendarioModel.dia > values['fim']))).first():
            abort(409, 'O intervalo precisa preservar os eventos já cadastrados.')
        for key, value in values.items():
            setattr(row, key, value)
        row.versao += 1
        auditar(db, user_id, 'editar_calendario', row.id, {'versao': row.versao})
        db.commit()
        return sucesso(versao=row.versao)


@escola_bp.post('/super/escola/calendarios/<int:calendario_id>/eventos')
def criar_evento(calendario_id):
    user_id = superperfil()
    data = dados()
    with get_session() as db:
        row = service.calendario_travado(db, calendario_id, data)
        inicio, fim = service.data_iso(data.get('inicio')), service.data_iso(data.get('fim') or data.get('inicio'))
        tipo = data.get('tipo')
        if tipo not in {'feriado', 'recesso', 'letivo', 'evento'} or inicio > fim or inicio < row.inicio or fim > row.fim:
            abort(400, 'Confira as datas e o tipo do evento dentro do calendário.')
        titulo = cursos.titulo(data.get('titulo'))
        dia = inicio
        while dia <= fim:
            db.add(EventoCalendarioModel(calendario_id=calendario_id, dia=dia, titulo=titulo, tipo=tipo))
            dia += timedelta(days=1)
        row.versao += 1
        auditar(db, user_id, 'criar_evento_calendario', row.id, {'inicio': inicio.isoformat(), 'fim': fim.isoformat(), 'tipo': tipo})
        db.commit()
        return sucesso(201, versao=row.versao)


@escola_bp.post('/super/escola/eventos/<int:evento_id>/remover')
def remover_evento(evento_id):
    user_id = superperfil()
    data = dados()
    with get_session() as db:
        evento = cursos.obter(db, EventoCalendarioModel, evento_id)
        row = service.calendario_travado(db, evento.calendario_id, data)
        db.delete(evento)
        row.versao += 1
        auditar(db, user_id, 'remover_evento_calendario', evento_id)
        db.commit()
        return sucesso(versao=row.versao)


@escola_bp.post('/super/escola/politicas')
def criar_politica():
    user_id = superperfil()
    data = dados()
    if not request.is_json:
        data = request.form.to_dict()
        n = {'semestres': 2, 'trimestres': 3, 'bimestres': 4}.get(data.get('divisao'))
        if data.get('divisao') == 'personalizada':
            n = cursos.inteiro(data, 'quantidade')
        if n is None or not 1 <= n <= 12:
            abort(400)
        data['periodos'] = [{field: data.get(f'periodo_{i}_{field}') for field in ('nome', 'peso', 'inicio', 'fim')} for i in range(1, n + 1)]
    with get_session() as db:
        calendario = service.calendario_travado(db, cursos.inteiro(data, 'calendario_id'))
        spec = service.validar_politica(data, calendario)
        row = PoliticaEscolaModel(calendario_id=calendario.id, nome=cursos.titulo(data.get('nome'))[:120],
                                 configuracao=json.dumps(spec, ensure_ascii=False))
        db.add(row)
        db.flush()
        auditar(db, user_id, 'criar_politica_escola', row.id, spec)
        db.commit()
        return sucesso(201, politica_id=row.id)


@escola_bp.post('/super/escola/politicas/<int:politica_id>/aplicar')
def aplicar(politica_id):
    user_id = superperfil()
    data = dados()
    with get_session() as db:
        service.aplicar_politica(db, politica_id, cursos.inteiro(data, 'turma_id'), user_id)
        db.commit()
    return sucesso()


@escola_bp.get('/calendario-escolar')
def calendario_publicado():
    identidade()
    with get_session() as db:
        rows = db.query(CalendarioEscolaModel).order_by(CalendarioEscolaModel.ano.desc()).all()
        return render_template('escola_calendario.html', calendarios=rows,
            resumos={c.id: service.resumo_calendario(db, c) for c in rows},
            eventos=db.query(EventoCalendarioModel).order_by(EventoCalendarioModel.dia).all())
