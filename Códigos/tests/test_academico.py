"""Homologação de vínculos antigos e notas por oferta/período."""
import unittest
from decimal import Decimal
from ambiente_teste import configurar_banco_testes, mysql_de_testes
configurar_banco_testes()
import test_cursos as curso_tests
from app import create_app
from app.database import Base, engine, get_session
from app.models import (ProfessorTurmaModel, ProfessorDisciplinaModel, TurmaDisciplinaModel,
                        AlunoTurmaModel, NotaModel, UsuarioModel)
from app.models.curso_model import EstadoTurmaModel, AtribuicaoDocenteModel
from app.models.academico_model import PeriodoLetivoModel, AvaliacaoModel, LancamentoNotaModel, AuditoriaAcademicaModel
from fixtures import exigir_banco_em_memoria, SENHA


class AcademicoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    def setUp(self):
        curso_tests.CursosTest.setUp(self)

    login = curso_tests.CursosTest.login
    post = curso_tests.CursosTest.post
    preparar_curso = curso_tests.CursosTest.preparar

    def preparar_diario(self):
        self.login('admin')
        self.periodos, self.vinculos = [], []
        for turma in (self.t, self.t2):
            self.post('/admin/gestao-turmas', {'acao': 'atribuir', 'turma_id': turma,
                      'professor_id': self.ids['professor_id'], 'disciplina_id': self.d})
            self.periodos.append(self.post('/academico/periodos', {'turma_id': turma, 'nome': '1º bimestre',
                                 'ordem': 1, 'media_referencia': '6'}, 201)['periodo_id'])
            with get_session() as db:
                self.vinculos.append(db.query(TurmaDisciplinaModel).filter_by(turma_id=turma, disciplina_id=self.d).one().id)
        self.login('professor')
        self.av = self.avaliacao(0, 'Prova', '1')
        self.av2 = self.avaliacao(0, 'Trabalho', '3')
        self.av_futura = self.avaliacao(1, 'Prova ano seguinte', '1')

    def avaliacao(self, indice, titulo, peso):
        return self.post('/academico/avaliacoes', {'turma_disciplina_id': self.vinculos[indice],
            'periodo_id': self.periodos[indice], 'titulo': titulo, 'peso': peso}, 201)['avaliacao_id']

    def nota(self, av, valor, versao=0, status=200, aluno=None):
        return self.post(f'/academico/avaliacoes/{av}/alunos/{aluno or self.ids["aluno_id"]}',
            {'valor': valor, 'versao': versao, 'observacao': 'Lançamento sintético'}, status)

    def publicar(self, av):
        self.post(f'/academico/avaliacoes/{av}/publicar', {})

    def ler_boletim(self):
        response = self.client.get('/boletim?formato=json')
        self.assertEqual(response.status_code, 200)
        return response.json

    def preparar_legado(self):
        with get_session() as db:
            db.add(ProfessorTurmaModel(professor_id=self.ids['professor_id'], turma_id=self.t))
            db.add_all([TurmaDisciplinaModel(turma_id=self.t, disciplina_id=d) for d in (self.d, self.d2)])
            db.commit()
        self.login('admin')
        return self.client.get(f'/academico/reconciliar/{self.t}?formato=json').json

    def test_weighted_grades_are_independent_across_years(self):
        self.preparar_diario()
        for av, valor in ((self.av, '8'), (self.av2, '6'), (self.av_futura, '4')):
            self.nota(av, valor)
            self.publicar(av)
        self.login('aluno')
        result = self.ler_boletim()['periodos']
        self.assertEqual([(r['ano'], r['media']) for r in result], [(2026, '6.50'), (2027, '4.00')])
        self.assertEqual(result[0]['situacao'], 'Média atingida')
        self.assertEqual(result[1]['situacao'], 'Abaixo da média')

    def test_missing_is_pending_and_draft_is_not_disclosed(self):
        self.preparar_diario()
        self.nota(self.av, '0')
        self.publicar(self.av)
        self.login('aluno')
        result = self.ler_boletim()['periodos'][0]
        self.assertIsNone(result['media'])
        self.assertEqual(result['avaliacoes'][0]['nota'], '0.00')
        self.assertNotIn('Trabalho', str(result))
        self.login('professor')
        self.publicar(self.av2)
        self.login('aluno')
        result = self.ler_boletim()['periodos'][0]
        self.assertIsNone(result['avaliacoes'][1]['nota'])
        self.assertIsNone(result['media'])

    def test_grade_validation_version_conflict_and_audit(self):
        self.preparar_diario()
        for invalid in ('NaN', 'Infinity', '-1', '10.01', '1.234', True, [], None):
            with self.subTest(invalid=invalid):
                self.nota(self.av, invalid, status=400)
        self.assertEqual(self.nota(self.av, '7,50')['versao'], 1)
        self.nota(self.av, '9', versao=0, status=409)
        self.assertEqual(self.nota(self.av, '8', versao=1)['versao'], 2)
        with get_session() as db:
            self.assertEqual(db.query(LancamentoNotaModel).count(), 1)
            self.assertEqual(db.query(LancamentoNotaModel).one().valor, Decimal('8'))
            self.assertEqual(db.query(AuditoriaAcademicaModel).filter_by(acao='salvar_nota').count(), 2)

    def test_closed_period_blocks_and_admin_can_reopen_with_reason(self):
        self.preparar_diario()
        self.nota(self.av, '7')
        self.login('admin')
        self.post(f'/academico/periodos/{self.periodos[0]}/estado', {'estado': 'fechado', 'motivo': 'Encerramento do bimestre'})
        self.login('professor')
        self.nota(self.av, '8', versao=1, status=409)
        self.post(f'/academico/periodos/{self.periodos[0]}/estado', {'estado': 'aberto', 'motivo': 'Tentativa do professor'}, 403)
        self.login('admin')
        self.post(f'/academico/periodos/{self.periodos[0]}/estado', {'estado': 'aberto', 'motivo': 'Correção revisada pela secretaria'})
        self.login('professor')
        self.nota(self.av, '8', versao=1)

    def test_roles_csrf_and_student_isolation(self):
        self.preparar_diario()
        self.nota(self.av, '7')
        self.publicar(self.av)
        self.assertEqual(self.client.post(f'/academico/avaliacoes/{self.av}/publicar', json={}).status_code, 400)
        self.nota(self.av, '7', aluno=self.ids['outro_aluno_id'], status=403)
        self.login('aluno')
        self.assertEqual(self.client.get(f'/academico/avaliacoes/{self.av}').status_code, 403)
        self.assertEqual(self.client.get(f'/academico/alunos/{self.ids["outro_aluno_id"]}/boletim').status_code, 403)
        self.nota(self.av, '9', status=403)
        self.login('outro_aluno')
        self.assertEqual(self.ler_boletim()['periodos'], [])
        self.login('admin')
        self.assertEqual(self.client.get(f'/academico/alunos/{self.ids["aluno_id"]}/boletim').status_code, 200)
        self.nota(self.av, '9', versao=1, status=403)

    def test_reconciliation_is_explicit_and_no_automatic_cartesian_grant(self):
        preview = self.preparar_legado()
        self.assertEqual(len(preview['candidatos']), 2)
        with get_session() as db:
            self.assertIsNone(db.get(EstadoTurmaModel, self.t))
            self.assertEqual(db.query(AtribuicaoDocenteModel).count(), 0)
        self.post(f'/academico/reconciliar/{self.t}', {'revisao': preview['revisao'],
                  'confirmadas': [f'{self.ids["professor_id"]}:{self.d}']})
        with get_session() as db:
            rows = db.query(AtribuicaoDocenteModel).all()
            self.assertEqual(len(rows), 1)
            self.assertIsNotNone(db.get(EstadoTurmaModel, self.t))
        self.login('professor')
        self.assertNotIn('Física'.encode(), self.client.get('/professor').data)

    def test_stale_and_invalid_reconciliation_rejected_without_partial_writes(self):
        preview = self.preparar_legado()
        self.post(f'/academico/reconciliar/{self.t}', {'revisao': preview['revisao'], 'confirmadas': ['999:999']}, 400)
        self.post(f'/academico/reconciliar/{self.t}', {'revisao': preview['revisao'], 'confirmadas': []}, 400)
        with get_session() as db:
            db.query(ProfessorDisciplinaModel).filter_by(professor_id=self.ids['professor_id'], disciplina_id=self.d2).delete()
            db.commit()
        self.post(f'/academico/reconciliar/{self.t}', {'revisao': preview['revisao'],
                  'confirmadas': [f'{self.ids["professor_id"]}:{self.d}']}, 409)
        with get_session() as db:
            self.assertIsNone(db.get(EstadoTurmaModel, self.t))

    def test_assignment_revocation_blocks_diary_and_old_grade_route(self):
        self.preparar_diario()
        with get_session() as db:
            row = db.query(AtribuicaoDocenteModel).filter_by(turma_disciplina_id=self.vinculos[0]).one()
            row.ativo = False
            db.commit()
        self.nota(self.av, '8', status=403)
        self.assertEqual(self.client.get(f'/academico/avaliacoes/{self.av}').status_code, 403)

    def test_period_and_weight_validation(self):
        self.preparar_diario()
        extra = self.avaliacao(0, 'Rascunho dispensável', '1')
        self.post(f'/academico/avaliacoes/{extra}/configurar', {'acao': 'salvar', 'titulo': 'Rascunho corrigido', 'peso': '2'})
        self.post(f'/academico/avaliacoes/{extra}/configurar', {'acao': 'remover'})
        self.nota(self.av, '7')
        self.post(f'/academico/avaliacoes/{self.av}/configurar', {'acao': 'remover'}, 409)
        self.publicar(self.av)
        self.post(f'/academico/avaliacoes/{self.av}/configurar', {'acao': 'salvar', 'titulo': 'Alterada', 'peso': '9'}, 409)
        self.post('/academico/avaliacoes', {'turma_disciplina_id': self.vinculos[0], 'periodo_id': self.periodos[1], 'titulo': 'Errada', 'peso': '1'}, 400)
        for peso in ('0', '-1', 'NaN', '101'):
            self.post('/academico/avaliacoes', {'turma_disciplina_id': self.vinculos[0], 'periodo_id': self.periodos[0], 'titulo': 'Errada', 'peso': peso}, 400)
        self.login('admin')
        self.post('/academico/periodos', {'turma_id': self.t, 'nome': '1º bimestre', 'ordem': 2}, 409)
        self.post('/admin/gestao-turmas', {'acao': 'editar', 'turma_id': self.t,
                  'nome': 'Turma alterada', 'ano_letivo': 2030}, 409)

    def test_legacy_note_requires_confirmation_and_preserves_source(self):
        self.preparar_diario()
        with get_session() as db:
            nota = NotaModel(aluno_id=self.ids['aluno_id'], professor_id=self.ids['professor_id'],
                             disciplina_id=self.d, nota=Decimal('7.25'), observacao='Histórico original')
            db.add(nota)
            db.commit()
            legacy_id = nota.id
        self.login('aluno')
        self.assertEqual(self.ler_boletim()['legadas'][0]['nota'], '7.25')
        self.login('admin')
        path = f'/academico/notas-antigas/{legacy_id}/vincular'
        self.post(path, {'avaliacao_id': self.av, 'valor_confirmado': '9.00'}, 409)
        self.post(path, {'avaliacao_id': self.av, 'valor_confirmado': '7.25'})
        self.post(path, {'avaliacao_id': self.av2, 'valor_confirmado': '7.25'}, 409)
        with get_session() as db:
            self.assertEqual(db.get(NotaModel, legacy_id).nota, Decimal('7.25'))
            self.assertEqual(db.query(LancamentoNotaModel).one().nota_legada_id, legacy_id)
        self.login('aluno')
        self.assertEqual(self.ler_boletim()['legadas'], [])

    def test_history_survives_unenrollment_and_privacy_export(self):
        self.preparar_diario()
        for av in (self.av, self.av2):
            self.nota(av, '8')
            self.publicar(av)
        self.login('admin')
        self.post('/admin/gestao-turmas', {'acao': 'desmatricular', 'turma_id': self.t, 'aluno_id': self.ids['aluno_id']})
        self.login('aluno')
        self.assertEqual(self.ler_boletim()['periodos'][0]['media'], '8.00')
        export = self.client.post('/minha-privacidade/exportar', headers={'X-CSRF-Token': self.csrf})
        self.assertEqual(export.status_code, 200)
        self.assertIn('boletim_por_periodo', export.json)

    def test_two_year_course_reconciliation_and_grades_end_to_end(self):
        self.preparar_curso()
        self.login('admin')
        preview = self.client.get(f'/academico/reconciliar/{self.t}?formato=json').json
        self.post(f'/academico/reconciliar/{self.t}', {'revisao': preview['revisao'], 'confirmadas': [f'{self.ids["professor_id"]}:{self.d}']})
        periodos, vinculos = [], []
        for turma in (self.t, self.t2):
            periodos.append(self.post('/academico/periodos', {'turma_id': turma, 'nome': 'Semestre 1', 'ordem': 1}, 201)['periodo_id'])
            with get_session() as db:
                vinculos.append(db.query(TurmaDisciplinaModel).filter_by(turma_id=turma, disciplina_id=self.d).one().id)
        self.periodos, self.vinculos = periodos, vinculos
        self.login('professor')
        for indice, valor in ((0, '9'), (1, '5')):
            av = self.avaliacao(indice, 'Avaliação final', '1')
            self.nota(av, valor)
            self.publicar(av)
        self.login('aluno')
        self.assertEqual(self.client.get(f'/aprender/{self.o}').status_code, 200)
        self.assertEqual(self.client.get(f'/aprender/{self.o2}').status_code, 200)
        self.assertEqual([p['media'] for p in self.ler_boletim()['periodos']], ['9.00', '5.00'])

    @unittest.skipUnless(mysql_de_testes(), 'Concorrência de notas exige MySQL isolado')
    def test_concurrent_correction_has_one_winner(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        self.preparar_diario()
        self.nota(self.av, '7')
        clients = []
        for _ in range(2):
            client = self.app.test_client()
            login = client.post('/login', json={'email': 'professor@teste.local', 'senha': SENHA})
            clients.append((client, login.json['csrf_token']))
        barrier = threading.Barrier(2)
        def save(index):
            client, csrf = clients[index]
            barrier.wait(timeout=10)
            return client.post(f'/academico/avaliacoes/{self.av}/alunos/{self.ids["aluno_id"]}',
                json={'valor': str(8 + index), 'versao': 1}, headers={'X-CSRF-Token': csrf}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(save, range(2))), [200, 409])
        with get_session() as db:
            self.assertEqual(db.query(LancamentoNotaModel).one().versao, 2)

    def test_demo_seeds_two_years_and_rejects_existing_data(self):
        from dados_homologacao import popular_homologacao
        from fixtures import criar_usuarios
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        ids = criar_usuarios()
        popular_homologacao(ids)
        self.login('aluno')
        self.assertEqual([p['media'] for p in self.ler_boletim()['periodos']], ['8.50', '5.00'])
        with self.assertRaises(RuntimeError):
            popular_homologacao(ids)
