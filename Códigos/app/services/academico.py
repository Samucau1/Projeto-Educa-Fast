"""Regras transacionais de atribuições, avaliações e boletim."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import secrets
from flask import abort
from app.models import (AlunoModel, AlunoTurmaModel, ProfessorModel, ProfessorDisciplinaModel,
                        ProfessorTurmaModel, TurmaModel, TurmaDisciplinaModel, DisciplinaModel, NotaModel)
from app.models.curso_model import EstadoTurmaModel, AtribuicaoDocenteModel
from app.models.academico_model import PeriodoLetivoModel, AvaliacaoModel, LancamentoNotaModel, AuditoriaAcademicaModel
from app.services import cursos


def decimal_limitado(raw, minimo=Decimal('0'), maximo=Decimal('10')):
    try:
        if isinstance(raw, bool) or not isinstance(raw, (str, int, float, Decimal)) or len(str(raw)) > 30:
            raise ValueError
        value = Decimal(str(raw).strip().replace(',', '.'))
        if not value.is_finite() or not minimo <= value <= maximo or value != value.quantize(Decimal('.01')):
            raise ValueError
        return value
    except (ValueError, InvalidOperation):
        abort(400, f'Informe um valor entre {minimo} e {maximo}, com até duas casas decimais.')


def auditar(db, user_id, acao, recurso, detalhe=None):
    db.add(AuditoriaAcademicaModel(usuario_id=user_id, acao=acao, recurso=str(recurso),
           detalhe=json.dumps(detalhe or {}, ensure_ascii=False, sort_keys=True)))


def candidatos_reconciliacao(db, turma_id):
    turma = cursos.obter(db, TurmaModel, turma_id)
    pairs = db.query(ProfessorModel, DisciplinaModel).join(ProfessorTurmaModel,
        ProfessorTurmaModel.professor_id == ProfessorModel.id).join(ProfessorDisciplinaModel,
        ProfessorDisciplinaModel.professor_id == ProfessorModel.id).join(DisciplinaModel,
        ProfessorDisciplinaModel.disciplina_id == DisciplinaModel.id).join(TurmaDisciplinaModel,
        TurmaDisciplinaModel.disciplina_id == DisciplinaModel.id).filter(
        ProfessorTurmaModel.turma_id == turma_id, TurmaDisciplinaModel.turma_id == turma_id).order_by(
        ProfessorModel.id, DisciplinaModel.id).all()
    explicit = db.query(AtribuicaoDocenteModel, TurmaDisciplinaModel).join(TurmaDisciplinaModel,
        AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(
        TurmaDisciplinaModel.turma_id == turma_id).order_by(AtribuicaoDocenteModel.id).all()
    state = db.get(EstadoTurmaModel, turma_id)
    snapshot = {'turma': turma_id, 'ano': turma.ano_letivo,
                'gerida': state is not None, 'arquivada': bool(state and state.arquivada),
                'candidatos': [(p.id, d.id) for p, d in pairs],
                'explicitas': [(a.professor_id, v.disciplina_id, a.ativo) for a, v in explicit]}
    fingerprint = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
    ativos = {f'{a.professor_id}:{v.disciplina_id}' for a, v in explicit if a.ativo}
    return turma, pairs, fingerprint, ativos


def reconciliar(db, turma_id, selecionados, fingerprint, user_id):
    turma = db.query(TurmaModel).filter_by(id=turma_id).with_for_update().first()
    if turma is None:
        abort(404)
    _, pairs, atual, _ = candidatos_reconciliacao(db, turma_id)
    if not isinstance(fingerprint, str) or not secrets.compare_digest(atual, fingerprint):
        abort(409, 'Os vínculos mudaram. Revise novamente antes de confirmar.')
    if not cursos.turma_ativa(db, turma_id):
        abort(409, 'Turma arquivada.')
    if not isinstance(selecionados, list) or not selecionados or any(not isinstance(k, str) for k in selecionados):
        abort(400, 'Selecione explicitamente ao menos uma atribuição confirmada.')
    validos = {f'{p.id}:{d.id}' for p, d in pairs}
    chosen = set(selecionados)
    if not chosen <= validos:
        abort(400, 'Atribuição fora dos vínculos revisados.')
    rows = db.query(AtribuicaoDocenteModel).join(TurmaDisciplinaModel,
        AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(TurmaDisciplinaModel.turma_id == turma_id).all()
    for row in rows:
        row.ativo = False
    db.flush()
    for key in sorted(chosen):
        prof_id, disc_id = map(int, key.split(':'))
        cursos.atribuir(db, prof_id, turma_id, disc_id)
    if not db.get(EstadoTurmaModel, turma_id):
        db.add(EstadoTurmaModel(turma_id=turma_id))
    auditar(db, user_id, 'reconciliar_turma', turma_id, {'confirmadas': sorted(chosen), 'revisao': fingerprint})


def docente_exato(db, user_id, role, vinculo):
    if role not in {'professor', 'admin', 'superadmin'}:
        abort(403)
    if role in {'admin', 'superadmin'}:
        return
    prof = cursos.professor(db, user_id)
    if not db.query(AtribuicaoDocenteModel).filter_by(professor_id=prof.id,
              turma_disciplina_id=vinculo.id, ativo=True).first():
        abort(403, 'É necessária atribuição explícita para esta matéria e turma.')


def periodo_mutavel(db, periodo_id):
    periodo = db.query(PeriodoLetivoModel).filter_by(id=periodo_id).with_for_update().first()
    if periodo is None:
        abort(404)
    if periodo.fechado or not cursos.turma_ativa(db, periodo.turma_id):
        abort(409, 'Período fechado ou turma arquivada. A secretaria precisa revisar a situação.')
    return periodo


def avaliacao_autorizada(db, avaliacao_id, user_id, role, mutacao=False):
    initial = cursos.obter(db, AvaliacaoModel, avaliacao_id)
    periodo = periodo_mutavel(db, initial.periodo_id) if mutacao else cursos.obter(db, PeriodoLetivoModel, initial.periodo_id)
    avaliacao = db.query(AvaliacaoModel).filter_by(id=avaliacao_id).populate_existing().with_for_update().one() if mutacao else initial
    vinculo = cursos.obter(db, TurmaDisciplinaModel, avaliacao.turma_disciplina_id)
    docente_exato(db, user_id, role, vinculo)
    return avaliacao, vinculo, periodo


def salvar_nota(db, avaliacao_id, aluno_id, data, user_id, role):
    if role != 'professor':
        abort(403, 'Lançamentos são feitos pelo professor atribuído.')
    avaliacao, vinculo, _ = avaliacao_autorizada(db, avaliacao_id, user_id, role, mutacao=True)
    aluno = cursos.obter(db, AlunoModel, aluno_id)
    if not db.query(AlunoTurmaModel).filter_by(aluno_id=aluno_id, turma_id=vinculo.turma_id).first():
        abort(403, 'Aluno não matriculado nesta turma.')
    if str(aluno.status_matricula or '').lower() in {'inativo', 'inativa', 'cancelado', 'cancelada', 'trancado', 'trancada'}:
        abort(403, 'Matrícula inativa.')
    valor = decimal_limitado(data.get('valor'))
    obs = data.get('observacao', '')
    if not isinstance(obs, str) or len(obs) > 255:
        abort(400, 'Observação deve ter até 255 caracteres.')
    raw = data.get('versao')
    if isinstance(raw, bool) or not str(raw).isdigit() or len(str(raw)) > 9:
        abort(400, 'Informe a versão do lançamento exibida no formulário.')
    esperado = int(raw)
    row = db.query(LancamentoNotaModel).filter_by(avaliacao_id=avaliacao_id, aluno_id=aluno_id).with_for_update().first()
    if esperado != (row.versao if row else 0):
        abort(409, 'A nota mudou desde a abertura do formulário. Recarregue antes de corrigir.')
    anterior = {'valor': str(row.valor), 'observacao': row.observacao, 'versao': row.versao} if row else None
    prof_id = cursos.professor(db, user_id).id
    if row:
        row.valor, row.observacao, row.professor_id = valor, obs.strip(), prof_id
        row.versao += 1
    else:
        row = LancamentoNotaModel(avaliacao_id=avaliacao_id, aluno_id=aluno_id, professor_id=prof_id,
                                  valor=valor, observacao=obs.strip(), versao=1)
        db.add(row)
    db.flush()
    auditar(db, user_id, 'salvar_nota', row.id, {'anterior': anterior, 'novo': {'valor': str(valor), 'observacao': row.observacao, 'versao': row.versao}})
    return row


def boletim(db, aluno_id):
    # Notas pertencem ao aluno mesmo após encerramento/remoção de matrícula; não dependem de vínculo atual para histórico.
    linhas = db.query(LancamentoNotaModel, AvaliacaoModel, PeriodoLetivoModel, TurmaModel, DisciplinaModel).join(
        AvaliacaoModel, LancamentoNotaModel.avaliacao_id == AvaliacaoModel.id).join(
        PeriodoLetivoModel, AvaliacaoModel.periodo_id == PeriodoLetivoModel.id).join(
        TurmaDisciplinaModel, AvaliacaoModel.turma_disciplina_id == TurmaDisciplinaModel.id).join(
        TurmaModel, TurmaDisciplinaModel.turma_id == TurmaModel.id).join(
        DisciplinaModel, TurmaDisciplinaModel.disciplina_id == DisciplinaModel.id).filter(
        LancamentoNotaModel.aluno_id == aluno_id, AvaliacaoModel.publicada.is_(True)).all()
    # Incluir avaliações publicadas ainda sem nota, inclusive em turmas matriculadas.
    matriculas = [t for t, in db.query(AlunoTurmaModel.turma_id).filter_by(aluno_id=aluno_id)]
    grupos = {}
    for nota, avaliacao, periodo, turma, disciplina in linhas:
        grupos[(turma.id, periodo.id, disciplina.id)] = (turma, periodo, disciplina, avaliacao.turma_disciplina_id)
    for avaliacao, periodo, turma, disciplina in db.query(AvaliacaoModel, PeriodoLetivoModel, TurmaModel, DisciplinaModel).join(
        PeriodoLetivoModel, AvaliacaoModel.periodo_id == PeriodoLetivoModel.id).join(TurmaDisciplinaModel,
        AvaliacaoModel.turma_disciplina_id == TurmaDisciplinaModel.id).join(TurmaModel,
        TurmaDisciplinaModel.turma_id == TurmaModel.id).join(DisciplinaModel,
        TurmaDisciplinaModel.disciplina_id == DisciplinaModel.id).filter(
        TurmaModel.id.in_(matriculas), AvaliacaoModel.publicada.is_(True)).all():
        grupos[(turma.id, periodo.id, disciplina.id)] = (turma, periodo, disciplina, avaliacao.turma_disciplina_id)
    resultado = []
    for turma, periodo, disciplina, vinculo_id in sorted(grupos.values(), key=lambda g: (g[0].ano_letivo, g[0].nome, g[1].ordem, g[2].nome)):
        avals = db.query(AvaliacaoModel).filter_by(periodo_id=periodo.id, turma_disciplina_id=vinculo_id).order_by(AvaliacaoModel.id).all()
        publicadas = [a for a in avals if a.publicada]
        notas = {n.avaliacao_id: n for n in db.query(LancamentoNotaModel).filter(
            LancamentoNotaModel.aluno_id == aluno_id, LancamentoNotaModel.avaliacao_id.in_([a.id for a in publicadas]))}
        completa = bool(avals) and all(a.publicada and a.id in notas for a in avals)
        media = (sum(notas[a.id].valor * a.peso for a in avals) / sum(a.peso for a in avals)).quantize(
                    Decimal('.01'), rounding=ROUND_HALF_UP) if completa else None
        resultado.append({'turma': turma.nome, 'turma_id': turma.id, 'ano': turma.ano_letivo,
            'periodo': periodo.nome, 'disciplina': disciplina.nome, 'fechado': periodo.fechado,
            'media': str(media) if media is not None else None, 'media_referencia': str(periodo.media_referencia),
            'situacao': ('Média atingida' if media >= periodo.media_referencia else 'Abaixo da média') if media is not None else 'Pendente',
            'avaliacoes': [{'id': a.id, 'titulo': a.titulo, 'peso': str(a.peso),
                'nota': str(notas[a.id].valor) if a.id in notas else None,
                'observacao': notas[a.id].observacao if a.id in notas else ''} for a in publicadas]})
    migradas = db.query(LancamentoNotaModel.nota_legada_id).filter(LancamentoNotaModel.nota_legada_id.is_not(None))
    legadas = [{'id': n.id, 'disciplina': d.nome, 'nota': str(n.nota), 'observacao': n.observacao or ''}
        for n, d in db.query(NotaModel, DisciplinaModel).join(DisciplinaModel, NotaModel.disciplina_id == DisciplinaModel.id).filter(
            NotaModel.aluno_id == aluno_id, ~NotaModel.id.in_(migradas)).all()]
    return {'periodos': resultado, 'legadas': legadas}
