"""Regras declarativas de escola, calendário e identidade; sem CSS/código arbitrário."""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
import json
import re
from flask import abort
from app.models import ConfiguracaoModel, TurmaModel
from app.models.academico_model import PeriodoLetivoModel
from app.models.escola_model import (IdentidadeEscolaModel, CalendarioEscolaModel, EventoCalendarioModel,
    PoliticaEscolaModel, RegraTurmaEscolaModel, RegraPeriodoEscolaModel)
from app.services import cursos
from app.services.academico import decimal_limitado, auditar

IDENTIDADE_PADRAO = {'nome': 'EducaFast', 'sigla': 'ef', 'subtitulo': 'GESTÃO ESCOLAR',
    'modo': 'escuro', 'fundo': '#06385d', 'destaque': '#22d3ee', 'superficie': '#111c2b',
    'texto': '#ecf1f8', 'muted': '#a4bdce', 'raio': '12', 'densidade': 'confortavel', 'fonte': 'dm-sans'}


def identidade_atual(db):
    row = db.get(IdentidadeEscolaModel, 1)
    config = db.get(ConfiguracaoModel, 1)
    result = {**IDENTIDADE_PADRAO, **(json.loads(row.dados) if row else {})}
    if config:
        result['fundo'], result['destaque'] = config.cor_fundo, config.cor_destaque
    result['versao'] = row.versao if row else 0
    result['texto_botao'] = '#071923' if contraste('#071923', result['destaque']) >= contraste('#ffffff', result['destaque']) else '#ffffff'
    return result


def luminancia(color):
    components = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in components]
    return sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))


def contraste(a, b):
    hi, lo = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (hi + .05) / (lo + .05)


def validar_identidade(data):
    result = {}
    for field, limit in (('nome', 60), ('sigla', 3), ('subtitulo', 40)):
        value = data.get(field)
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit or any(ord(c) < 32 for c in value):
            abort(400, f'Confira {field}: limite de {limit} caracteres.')
        result[field] = value.strip()
    for field in ('fundo', 'destaque', 'superficie', 'texto', 'muted'):
        value = data.get(field)
        if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
            abort(400, 'As cores devem usar o formato #RRGGBB.')
        result[field] = value.lower()
    for field, choices in {'modo': {'escuro', 'claro'}, 'raio': {'8', '12', '16'},
                           'densidade': {'confortavel', 'compacta'}, 'fonte': {'dm-sans', 'sistema'}}.items():
        value = str(data.get(field, IDENTIDADE_PADRAO[field]))
        if value not in choices:
            abort(400, f'Opção visual inválida: {field}.')
        result[field] = value
    if contraste(result['texto'], result['superficie']) < 4.5 or contraste(result['muted'], result['superficie']) < 4.5:
        abort(400, 'Aumente o contraste do texto e do texto secundário com os cartões (mínimo interno de 4,5).')
    page = result['fundo']
    if result['modo'] == 'escuro':
        base = '#0a101a'
        page = '#' + ''.join(f'{round(int(page[i:i+2],16)*.16 + int(base[i:i+2],16)*.84):02x}' for i in (1,3,5))
    if any(contraste(result[field], page) < 4.5 for field in ('texto', 'muted')):
        abort(400, 'Aumente o contraste dos textos com o fundo da página ou escolha o modo correspondente à paleta.')
    if contraste(result['destaque'], page) < 3 or contraste(result['destaque'], result['superficie']) < 3:
        abort(400, 'A cor de destaque precisa se distinguir do fundo e dos cartões.')
    return result


def versao(data):
    value = str(data.get('versao', ''))
    if not value.isdigit() or len(value) > 9:
        abort(400, 'Recarregue o formulário para obter sua versão.')
    return int(value)


def salvar_identidade(db, data, user_id):
    # Bloqueio em uma linha existente também serializa a primeira gravação do singleton.
    from app.models import UsuarioModel
    db.query(UsuarioModel).order_by(UsuarioModel.id).with_for_update().first()
    row = db.query(IdentidadeEscolaModel).filter_by(id=1).populate_existing().with_for_update().first()
    if versao(data) != (row.versao if row else 0):
        abort(409, 'A identidade foi alterada em outra sessão. Recarregue antes de salvar.')
    values = validar_identidade(data)
    if row:
        row.dados, row.versao = json.dumps(values), row.versao + 1
    else:
        row = IdentidadeEscolaModel(id=1, dados=json.dumps(values), versao=1)
        db.add(row)
    config = db.get(ConfiguracaoModel, 1)
    if not config:
        config = ConfiguracaoModel(id=1)
        db.add(config)
    config.cor_fundo, config.cor_destaque = values['fundo'], values['destaque']
    auditar(db, user_id, 'identidade_escola', 1, {'versao': row.versao, 'dados': values})
    return row


def data_iso(value):
    try:
        if not isinstance(value, str):
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        abort(400, 'Informe uma data válida.')


def calendario_travado(db, calendario_id, data=None):
    row = db.query(CalendarioEscolaModel).filter_by(id=calendario_id).populate_existing().with_for_update().first()
    if not row:
        abort(404)
    if data is not None and versao(data) != row.versao:
        abort(409, 'O calendário mudou. Recarregue antes de salvar.')
    return row


def validar_calendario(data):
    ano = cursos.inteiro(data, 'ano')
    inicio, fim = data_iso(data.get('inicio')), data_iso(data.get('fim'))
    if not 1900 <= ano <= 2200 or inicio.year != ano or fim.year != ano or inicio > fim:
        abort(400, 'As datas precisam estar em ordem e dentro do ano escolhido.')
    dias = data.get('dias_semana')
    if not isinstance(dias, list) or not dias or any(isinstance(d, bool) or str(d) not in set('0123456') for d in dias):
        abort(400, 'Selecione os dias da semana que podem ser letivos.')
    meta = cursos.inteiro(data, 'meta_letivos')
    if meta > (fim - inicio).days + 1:
        abort(400, 'A meta de dias letivos não pode exceder o intervalo do calendário.')
    return {'ano': ano, 'nome': cursos.titulo(data.get('nome'))[:120], 'inicio': inicio, 'fim': fim,
            'dias_semana': json.dumps(sorted({int(d) for d in dias})), 'meta_letivos': meta}


def resumo_calendario(db, calendario):
    eventos = {e.dia: e for e in db.query(EventoCalendarioModel).filter_by(calendario_id=calendario.id)}
    weekdays = json.loads(calendario.dias_semana)
    days, months = 0, {}
    current = calendario.inicio
    while current <= calendario.fim:
        event = eventos.get(current)
        letivo = (event.tipo == 'letivo') if event and event.tipo != 'evento' else current.weekday() in weekdays
        if letivo:
            days += 1
            months[current.month] = months.get(current.month, 0) + 1
        current += timedelta(days=1)
    return {'dias_planejados': days, 'meta': calendario.meta_letivos,
            'faltam': max(0, calendario.meta_letivos - days), 'meses': months}


def validar_politica(data, calendario):
    tipo = data.get('divisao')
    quantidade = {'semestres': 2, 'trimestres': 3, 'bimestres': 4}.get(tipo)
    if tipo == 'personalizada':
        quantidade = cursos.inteiro(data, 'quantidade')
    if quantidade is None or not 1 <= quantidade <= 12:
        abort(400, 'Escolha a divisão letiva (até 12 períodos).')
    raw = data.get('periodos')
    if not isinstance(raw, list) or len(raw) != quantidade:
        abort(400, 'Confira o nome, peso e datas de todos os períodos da divisão escolhida.')
    periodos, nomes = [], set()
    anterior = None
    for item in raw:
        if not isinstance(item, dict):
            abort(400)
        nome = cursos.titulo(item.get('nome'))
        if len(nome) > 80 or nome.casefold() in nomes:
            abort(400, 'Use nomes de período diferentes, com até 80 caracteres.')
        nomes.add(nome.casefold())
        inicio, fim = data_iso(item.get('inicio')), data_iso(item.get('fim'))
        if inicio < calendario.inicio or fim > calendario.fim or inicio > fim or (anterior and inicio <= anterior):
            abort(400, 'Períodos precisam estar em ordem, sem sobreposição e dentro do calendário.')
        anterior = fim
        periodos.append({'nome': nome, 'peso': str(decimal_limitado(item.get('peso'), Decimal('.01'), Decimal('100'))),
                         'inicio': inicio.isoformat(), 'fim': fim.isoformat()})
    casas, arredondamento = str(data.get('casas', '2')), data.get('arredondamento', 'comercial')
    if casas not in {'1', '2'} or arredondamento not in {'comercial', 'truncar'}:
        abort(400, 'Regra de arredondamento inválida.')
    return {'divisao': tipo, 'periodos': periodos, 'media_referencia': str(decimal_limitado(data.get('media_referencia', '6'))),
            'casas': int(casas), 'arredondamento': arredondamento}


def aplicar_politica(db, politica_id, turma_id, user_id):
    turma = db.query(TurmaModel).filter_by(id=turma_id).with_for_update().first()
    if not turma:
        abort(404)
    politica = cursos.obter(db, PoliticaEscolaModel, politica_id)
    calendario = cursos.obter(db, CalendarioEscolaModel, politica.calendario_id)
    if turma.ano_letivo != calendario.ano or not cursos.turma_ativa(db, turma_id):
        abort(400, 'Escolha uma turma ativa do mesmo ano do calendário.')
    if db.get(RegraTurmaEscolaModel, turma_id) or db.query(PeriodoLetivoModel).filter_by(turma_id=turma_id).first():
        abort(409, 'Esta turma já tem períodos ou regras aplicadas. Seu histórico será preservado; use outra turma para a nova configuração.')
    spec = json.loads(politica.configuracao)
    db.add(RegraTurmaEscolaModel(turma_id=turma_id, politica_id=politica_id))
    for index, item in enumerate(spec['periodos'], 1):
        periodo = PeriodoLetivoModel(turma_id=turma_id, nome=item['nome'], ordem=index,
                                    media_referencia=Decimal(spec['media_referencia']))
        db.add(periodo)
        db.flush()
        db.add(RegraPeriodoEscolaModel(periodo_id=periodo.id, politica_id=politica_id, ordem=index))
    auditar(db, user_id, 'aplicar_politica', turma_id, {'politica_id': politica_id})


def regra_periodo(db, periodo):
    row = db.get(RegraPeriodoEscolaModel, periodo.id)
    if not row:
        return None
    politica = cursos.obter(db, PoliticaEscolaModel, row.politica_id)
    spec = json.loads(politica.configuracao)
    return {**spec, 'item': spec['periodos'][row.ordem - 1], 'politica_id': politica.id}


def arredondar(valor, spec=None):
    spec = spec or {'casas': 2, 'arredondamento': 'comercial'}
    return valor.quantize(Decimal('0.1') if spec['casas'] == 1 else Decimal('0.01'),
                          rounding=ROUND_HALF_UP if spec['arredondamento'] == 'comercial' else ROUND_DOWN)


def resumo_anual(db, periodos):
    groups = {}
    for item in periodos:
        groups.setdefault((item['turma_id'], item['disciplina_id']), []).append(item)
    result = []
    for (turma_id, disciplina_id), items in groups.items():
        regra = db.get(RegraTurmaEscolaModel, turma_id)
        if not regra:
            continue
        politica = cursos.obter(db, PoliticaEscolaModel, regra.politica_id)
        spec = json.loads(politica.configuracao)
        ordered = {i['ordem']: i for i in items}
        complete = all(i in ordered and ordered[i]['media'] is not None and ordered[i]['fechado'] for i in range(1, len(spec['periodos']) + 1))
        # A média anual utiliza as médias de período publicadas, seguindo a precisão da política.
        media = arredondar(sum(Decimal(ordered[i]['media']) * Decimal(p['peso']) for i, p in enumerate(spec['periodos'], 1)) /
                            sum(Decimal(p['peso']) for p in spec['periodos']), spec) if complete else None
        result.append({'turma': items[0]['turma'], 'ano': items[0]['ano'], 'disciplina': items[0]['disciplina'], 'disciplina_id': disciplina_id,
            'politica': politica.nome, 'media': str(media) if media is not None else None,
            'media_referencia': spec['media_referencia'], 'pesos': [p['peso'] for p in spec['periodos']],
            'situacao': ('Média atingida' if media >= Decimal(spec['media_referencia']) else 'Abaixo da média') if media is not None else 'Pendente'})
    return result
