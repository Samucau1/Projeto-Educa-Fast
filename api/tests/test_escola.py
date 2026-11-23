"""Configuração institucional: exclusividade, preservação de histórico e design."""
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import json
import unittest
from ambiente_teste import configurar_banco_testes
configurar_banco_testes()
import test_cursos as curso_tests
from app import create_app
from app.database import get_session, Base
from app.models import TurmaModel, TurmaDisciplinaModel
from app.models.academico_model import PeriodoLetivoModel
from app.models.escola_model import CalendarioEscolaModel, EventoCalendarioModel, PoliticaEscolaModel
from app.services.escola import IDENTIDADE_PADRAO
from fixtures import exigir_banco_em_memoria


class EscolaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.config['TESTING'] = True

    def setUp(self):
        curso_tests.CursosTest.setUp(self)

    login = curso_tests.CursosTest.login
    post = curso_tests.CursosTest.post

    def meta(self):
        response = self.client.get('/super/escola?formato=json')
        self.assertEqual(response.status_code, 200)
        return response.json

    def calendario(self, inicio='2026-01-01', fim='2026-12-31', meta=200):
        self.login('superadmin')
        return self.post('/super/escola/calendarios', {'nome': 'Calendário da escola', 'ano': 2026,
            'inicio': inicio, 'fim': fim, 'meta_letivos': meta, 'dias_semana': [0,1,2,3,4]}, 201)['calendario_id']

    def politica(self, calendario_id, divisao='semestres', pesos=None, **extra):
        n = {'semestres': 2, 'trimestres': 3, 'bimestres': 4}[divisao]
        pesos = pesos or ['1'] * n
        first = date(2026,1,1)
        days = (date(2027,1,1) - first).days
        periodos = [{'nome': f'{i+1}º período', 'peso': pesos[i],
            'inicio': (first + timedelta(days=days*i//n)).isoformat(),
            'fim': (first + timedelta(days=days*(i+1)//n-1)).isoformat()} for i in range(n)]
        return self.post('/super/escola/politicas', {'nome': 'Regra da escola', 'calendario_id': calendario_id,
            'divisao': divisao, 'periodos': periodos, 'media_referencia': '7',
            'casas': '2', 'arredondamento': 'comercial', **extra}, 201)['politica_id']

    def test_only_superadmin_can_configure_and_csrf_is_required(self):
        self.assertEqual(self.client.get('/super/escola').status_code, 403)
        for role in ('admin', 'professor', 'aluno'):
            self.login(role)
            self.assertEqual(self.client.get('/super/escola').status_code, 403)
            self.post('/super/escola/identidade', {}, 403)
        self.login('superadmin')
        self.assertEqual(self.client.post('/super/escola/identidade', json={}).status_code, 400)
        self.assertEqual(self.client.get('/super/escola').status_code, 200)

    def test_branding_is_global_escaped_and_versioned(self):
        self.login('superadmin')
        data = {**IDENTIDADE_PADRAO, 'nome': 'Escola <script>', 'sigla': 'ABC', 'versao': 0}
        self.post('/super/escola/identidade', data)
        self.post('/super/escola/identidade', data, 409)
        self.login('aluno')
        page = self.client.get('/mensagens')
        self.assertIn(b'Escola &lt;script&gt;', page.data)
        self.assertIn(b'ABC', page.data)
        self.assertIn(b'--school-radius:12px', page.data)

    def test_invalid_theme_values_and_low_contrast_rejected(self):
        self.login('superadmin')
        for changes in ({'superficie': 'red;}'}, {'texto': '#111c2b'}, {'fonte': 'https://evil.test/font'},
                        {'raio': '999'}, {'nome': ''}, {'modo': 'arbitrario'}):
            self.post('/super/escola/identidade', {**IDENTIDADE_PADRAO, 'versao': 0, **changes}, 400)
        self.assertEqual(self.meta()['identidade']['versao'], 0)

    def test_light_palette_and_legacy_color_editor_keep_versions_in_sync(self):
        self.login('superadmin')
        data = {**IDENTIDADE_PADRAO, 'modo': 'claro', 'fundo': '#f3f6fb', 'destaque': '#1d4ed8',
            'superficie': '#ffffff', 'texto': '#18283b', 'muted': '#475569', 'versao': 0}
        self.post('/super/escola/identidade', data)
        response = self.client.post('/super/layout', data={'cor_fundo': '#f3f6fb', 'cor_destaque': '#1e40af',
                                                         'csrf_token': self.csrf})
        self.assertEqual(response.status_code, 302)
        current = self.meta()['identidade']
        self.assertEqual(current['versao'], 2)
        self.assertEqual(current['destaque'], '#1e40af')
        self.assertIn(b'school-theme', self.client.get('/super/escola').data)

    def test_calendar_weekdays_holidays_and_makeup_days(self):
        cid = self.calendario('2026-01-05', '2026-01-11', 5)
        self.assertEqual(self.meta()['calendarios'][0]['dias_planejados'], 5)
        self.post(f'/super/escola/calendarios/{cid}/eventos', {'versao': 1, 'titulo': 'Feriado cadastrado pela escola',
            'tipo': 'feriado', 'inicio': '2026-01-06'}, 201)
        self.assertEqual(self.meta()['calendarios'][0]['dias_planejados'], 4)
        self.post(f'/super/escola/calendarios/{cid}/eventos', {'versao': 2, 'titulo': 'Reposição',
            'tipo': 'letivo', 'inicio': '2026-01-10'}, 201)
        self.assertEqual(self.meta()['calendarios'][0]['dias_planejados'], 5)
        self.login('aluno')
        self.assertIn('Reposição'.encode(), self.client.get('/calendario-escolar').data)

    def test_calendar_conflicts_invalid_ranges_and_atomic_event_batch(self):
        cid = self.calendario('2026-01-05', '2026-01-11', 5)
        self.post(f'/super/escola/calendarios/{cid}/eventos', {'versao': 1, 'titulo': 'Recesso',
            'tipo': 'recesso', 'inicio': '2026-01-06'}, 201)
        self.post(f'/super/escola/calendarios/{cid}/eventos', {'versao': 1, 'titulo': 'Desatualizado',
            'tipo': 'feriado', 'inicio': '2026-01-07'}, 409)
        self.post(f'/super/escola/calendarios/{cid}/eventos', {'versao': 2, 'titulo': 'Sobreposto',
            'tipo': 'recesso', 'inicio': '2026-01-05', 'fim': '2026-01-08'}, 409)
        with get_session() as db:
            self.assertEqual(db.query(EventoCalendarioModel).count(), 1)
            self.assertEqual(db.get(CalendarioEscolaModel, cid).versao, 2)
        self.post(f'/super/escola/calendarios/{cid}/eventos', {'versao': 2, 'titulo': 'Fora do ano',
            'tipo': 'feriado', 'inicio': '2027-01-01'}, 400)

    def test_division_choices_and_policy_validation(self):
        cid = self.calendario()
        for divisao, count in (('semestres', 2), ('trimestres', 3), ('bimestres', 4)):
            identity = self.politica(cid, divisao)
            spec = next(p for p in self.meta()['politicas'] if p['id'] == identity)
            self.assertEqual(len(spec['periodos']), count)
        self.post('/super/escola/politicas', {'nome': 'Inválida', 'calendario_id': cid, 'divisao': 'semestres',
            'periodos': [{'nome': 'A', 'peso': '0', 'inicio': '2026-01-01', 'fim': '2026-07-01'},
                         {'nome': 'B', 'peso': '1', 'inicio': '2026-06-01', 'fim': '2026-12-31'}]}, 400)

    def test_applied_rules_preserve_history_and_own_the_period_structure(self):
        cid = self.calendario()
        pid = self.politica(cid)
        self.post(f'/super/escola/politicas/{pid}/aplicar', {'turma_id': self.t})
        self.post(f'/super/escola/politicas/{pid}/aplicar', {'turma_id': self.t}, 409)
        self.post(f'/super/escola/politicas/{pid}/aplicar', {'turma_id': self.t2}, 400)
        self.login('admin')
        self.post('/academico/periodos', {'turma_id': self.t, 'nome': 'Injetado', 'ordem': 3}, 403)
        with get_session() as db:
            self.assertEqual(db.query(PeriodoLetivoModel).filter_by(turma_id=self.t).count(), 2)

    def test_annual_weighted_average_uses_superadmin_policy_and_closed_periods(self):
        cid = self.calendario()
        pid = self.politica(cid, pesos=['1', '3'])
        self.post('/admin/gestao-turmas', {'acao': 'atribuir', 'turma_id': self.t,
            'professor_id': self.ids['professor_id'], 'disciplina_id': self.d})
        self.post(f'/super/escola/politicas/{pid}/aplicar', {'turma_id': self.t})
        with get_session() as db:
            periodos = [p.id for p in db.query(PeriodoLetivoModel).filter_by(turma_id=self.t).order_by(PeriodoLetivoModel.ordem)]
            vinculo = db.query(TurmaDisciplinaModel).filter_by(turma_id=self.t, disciplina_id=self.d).one().id
        for periodo_id, valor in zip(periodos, ('8', '6')):
            self.login('professor')
            aid = self.post('/academico/avaliacoes', {'turma_disciplina_id': vinculo, 'periodo_id': periodo_id,
                'titulo': 'Prova', 'peso': '1'}, 201)['avaliacao_id']
            self.post(f'/academico/avaliacoes/{aid}/alunos/{self.ids["aluno_id"]}', {'valor': valor, 'versao': 0})
            self.post(f'/academico/avaliacoes/{aid}/publicar', {})
            self.login('superadmin')
            self.post(f'/academico/periodos/{periodo_id}/estado', {'estado': 'fechado', 'motivo': 'Conferência da escola'})
        self.login('aluno')
        anual = self.client.get('/boletim?formato=json').json['anuais'][0]
        self.assertEqual(anual['media'], '6.50')
        self.assertEqual(anual['pesos'], ['1', '3'])
        self.assertEqual(anual['situacao'], 'Abaixo da média')

    def test_rounding_and_protocol_gate(self):
        from app.services.escola import arredondar
        self.assertEqual(arredondar(Decimal('6.99'), {'casas': 1, 'arredondamento': 'truncar'}), Decimal('6.9'))
        self.assertEqual(arredondar(Decimal('6.95'), {'casas': 1, 'arredondamento': 'comercial'}), Decimal('7.0'))
        from verificar_protocolo_design import verificar
        self.assertEqual(verificar(Path(__file__).resolve().parents[2]), [])

    def test_migration_v2_to_v3_preserves_earlier_schema(self):
        from app.database import engine
        from app.migrations_cursos import migrar_cursos, tabelas_cursos
        from sqlalchemy import text
        for table in reversed(tabelas_cursos(Base.metadata)):
            if table.name.startswith('escola_'):
                table.drop(engine)
        with engine.begin() as connection:
            connection.execute(text('DELETE FROM educafast_migracoes'))
            connection.execute(text('INSERT INTO educafast_migracoes (versao) VALUES (1), (2)'))
        migrar_cursos(engine, Base.metadata)
        migrar_cursos(engine, Base.metadata)
        with get_session() as db:
            self.assertIsNotNone(db.get(TurmaModel, self.t))
            self.assertEqual(db.query(CalendarioEscolaModel).count(), 0)
