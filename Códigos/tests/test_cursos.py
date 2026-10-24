"""Cursos reutilizados entre turmas e anos; bancos sintéticos e descartáveis."""
import unittest
from werkzeug.exceptions import HTTPException
from ambiente_teste import configurar_banco_testes, mysql_de_testes
configurar_banco_testes()
from app import create_app
from app.database import Base, engine, get_session
from app.models import (DisciplinaModel, TurmaModel, ProfessorDisciplinaModel, AlunoTurmaModel,
                        TurmaDisciplinaModel, ProfessorModel, UsuarioModel)
from app.models.curso_model import (CursoModel, AulaModel, CapituloModel, TemaModel, ProgressoAulaModel,
    OfertaCursoModel, AtribuicaoDocenteModel, EstadoTurmaModel)
from app.services.cursos import video_id, autoriza_docencia
from fixtures import criar_usuarios, exigir_banco_em_memoria, SENHA


class CursosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.ids = criar_usuarios()
        self.client = self.app.test_client()
        with get_session() as db:
            d = DisciplinaModel(nome='Matemática', codigo='MAT-C', carga_horaria=60)
            d2 = DisciplinaModel(nome='Física', codigo='FIS-C', carga_horaria=60)
            t = TurmaModel(nome='Turma 2026', codigo='C26', ano_letivo=2026)
            t2 = TurmaModel(nome='Turma 2027', codigo='C27', ano_letivo=2027)
            db.add_all([d, d2, t, t2])
            db.flush()
            self.d, self.d2, self.t, self.t2 = d.id, d2.id, t.id, t2.id
            db.add_all([ProfessorDisciplinaModel(professor_id=self.ids['professor_id'], disciplina_id=d.id),
                        ProfessorDisciplinaModel(professor_id=self.ids['professor_id'], disciplina_id=d2.id),
                        AlunoTurmaModel(aluno_id=self.ids['aluno_id'], turma_id=t.id),
                        AlunoTurmaModel(aluno_id=self.ids['aluno_id'], turma_id=t2.id)])
            db.commit()

    def login(self, role):
        response = self.client.post('/login', json={'email': f'{role}@teste.local', 'senha': SENHA})
        self.assertEqual(response.status_code, 200)
        self.csrf = response.get_json()['csrf_token']

    def post(self, path, data, status=200):
        response = self.client.post(path, json=data, headers={'X-CSRF-Token': self.csrf})
        self.assertEqual(response.status_code, status, response.get_data(as_text=True)[:500])
        return response.get_json()

    def preparar(self, publicar=True):
        self.login('professor')
        self.c = self.post('/cursos', {'disciplina_id': self.d, 'titulo': 'Álgebra <script>', 'descricao': 'Aprenda álgebra'}, 201)['curso_id']
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'adicionar', 'tipo': 'capitulo', 'titulo': 'Fundamentos'})
        with get_session() as db:
            self.cap = db.query(CapituloModel).filter_by(curso_id=self.c).one().id
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'adicionar', 'tipo': 'tema', 'pai_id': self.cap, 'titulo': 'Equações'})
        with get_session() as db:
            self.tema = db.query(TemaModel).filter_by(capitulo_id=self.cap).one().id
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'adicionar', 'tipo': 'aula', 'pai_id': self.tema,
                                              'titulo': 'Primeira aula', 'video': 'https://youtu.be/abcdefghijk'})
        with get_session() as db:
            self.aula = db.query(AulaModel).filter_by(tema_id=self.tema).one().id
        if publicar:
            self.login('admin')
            self.post(f'/cursos/{self.c}/estado', {'estado': 'publicado'})
            for turma in (self.t, self.t2):
                self.post('/admin/gestao-turmas', {'acao': 'atribuir', 'turma_id': turma,
                          'professor_id': self.ids['professor_id'], 'disciplina_id': self.d})
                self.post(f'/cursos/{self.c}/ofertas', {'turma_id': turma})
            with get_session() as db:
                offers = db.query(OfertaCursoModel).filter_by(curso_id=self.c).order_by(OfertaCursoModel.id).all()
                self.o, self.o2 = [row.id for row in offers]

    def test_reuse_two_years_with_separate_progress(self):
        self.preparar()
        self.post('/admin/gestao-turmas', {'acao': 'editar', 'turma_id': self.t,
                  'nome': 'Turma 2026', 'ano_letivo': 2028}, 409)
        self.login('aluno')
        self.assertEqual(self.client.get('/cursos').status_code, 200)
        self.post(f'/aprender/{self.o}/aulas/{self.aula}/concluir', {})
        self.post(f'/aprender/{self.o}/aulas/{self.aula}/concluir', {})
        self.assertIn(b'100%', self.client.get(f'/aprender/{self.o}').data)
        self.assertIn(b'0%', self.client.get(f'/aprender/{self.o2}').data)
        with get_session() as db:
            self.assertEqual(db.query(ProgressoAulaModel).count(), 1)
            self.assertEqual(db.query(CursoModel).count(), 1)
            self.assertEqual(db.query(AulaModel).count(), 1)

    def test_student_isolation_and_no_forged_progress_owner(self):
        self.preparar()
        self.login('outro_aluno')
        self.assertEqual(self.client.get(f'/aprender/{self.o}').status_code, 404)
        self.post(f'/aprender/{self.o}/aulas/{self.aula}/concluir', {}, 404)
        self.assertNotIn(b'Primeira aula', self.client.get('/cursos').data)
        self.login('aluno')
        self.post(f'/aprender/{self.o}/aulas/{self.aula}/concluir', {'aluno_id': self.ids['outro_aluno_id']})
        with get_session() as db:
            self.assertEqual(db.query(ProgressoAulaModel).one().aluno_id, self.ids['aluno_id'])

    def test_draft_private_and_publication_admin_only(self):
        self.preparar(False)
        self.post(f'/cursos/{self.c}/estado', {'estado': 'publicado'}, 403)
        self.login('aluno')
        self.assertEqual(self.client.get(f'/cursos/{self.c}').status_code, 403)
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'curso', 'titulo': 'X'}, 403)

    def test_duplicate_preserves_original_without_offers_or_progress(self):
        self.preparar()
        self.login('professor')
        novo = self.post(f'/cursos/{self.c}/duplicar', {}, 201)['curso_id']
        with get_session() as db:
            self.assertEqual(db.get(CursoModel, novo).estado, 'rascunho')
            self.assertEqual(db.get(CursoModel, novo).origem_id, self.c)
            self.assertEqual(db.query(OfertaCursoModel).filter_by(curso_id=novo).count(), 0)
            cap = db.query(CapituloModel).filter_by(curso_id=novo).one()
            tema = db.query(TemaModel).filter_by(capitulo_id=cap.id).one()
            aula = db.query(AulaModel).filter_by(tema_id=tema.id).one()
            self.assertNotEqual(aula.id, self.aula)
            self.assertEqual(aula.video_id, 'abcdefghijk')
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'curso', 'titulo': 'Alterado'}, 409)
        self.post(f'/cursos/{novo}/estrutura', {'acao': 'curso', 'titulo': 'Nova edição'})
        with get_session() as db:
            self.assertEqual(db.get(CursoModel, self.c).titulo, 'Álgebra <script>')

    def test_revoked_offer_and_enrollment_remove_access(self):
        self.preparar()
        self.login('admin')
        self.post(f'/cursos/ofertas/{self.o}/revogar', {})
        self.login('aluno')
        self.assertEqual(self.client.get(f'/aprender/{self.o}').status_code, 404)
        self.login('admin')
        self.post('/admin/gestao-turmas', {'acao': 'desmatricular', 'turma_id': self.t2, 'aluno_id': self.ids['aluno_id']})
        self.login('aluno')
        self.post(f'/aprender/{self.o2}/aulas/{self.aula}/concluir', {}, 404)

    def test_archived_class_blocks_access_and_teaching(self):
        self.preparar()
        self.login('admin')
        self.post('/admin/gestao-turmas', {'acao': 'arquivar', 'turma_id': self.t})
        self.login('aluno')
        self.assertEqual(self.client.get(f'/aprender/{self.o}').status_code, 404)
        with get_session() as db:
            self.assertFalse(autoriza_docencia(db, self.ids['professor_id'], self.t, self.d))

    def test_precise_teacher_assignment_and_immediate_revocation(self):
        self.login('admin')
        for turma, disciplina in ((self.t, self.d), (self.t2, self.d2)):
            self.post('/admin/gestao-turmas', {'acao': 'atribuir', 'turma_id': turma,
                      'professor_id': self.ids['professor_id'], 'disciplina_id': disciplina})
        with get_session() as db:
            self.assertTrue(autoriza_docencia(db, self.ids['professor_id'], self.t, self.d))
            self.assertTrue(autoriza_docencia(db, self.ids['professor_id'], self.t2, self.d2))
            self.assertFalse(autoriza_docencia(db, self.ids['professor_id'], self.t, self.d2))
            row = db.query(AtribuicaoDocenteModel).join(TurmaDisciplinaModel,
                AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(TurmaDisciplinaModel.turma_id == self.t).one()
            row_id = row.id
        self.post('/admin/gestao-turmas', {'acao': 'revogar', 'turma_id': self.t, 'atribuicao_id': row_id})
        with get_session() as db:
            self.assertFalse(autoriza_docencia(db, self.ids['professor_id'], self.t, self.d))

    def test_class_management_roles_csrf_and_duplicate(self):
        self.assertEqual(self.client.get('/admin/gestao-turmas').status_code, 403)
        for role in ('aluno', 'professor'):
            self.login(role)
            self.post('/admin/gestao-turmas', {'acao': 'criar'}, 403)
        self.login('admin')
        self.assertEqual(self.client.post('/admin/gestao-turmas', json={'acao': 'criar'}).status_code, 400)
        self.post('/admin/gestao-turmas', {'acao': 'criar', 'nome': 'Nova turma', 'codigo': 'NOV', 'ano_letivo': 2028})
        self.post('/admin/gestao-turmas', {'acao': 'criar', 'nome': 'Duplicada', 'codigo': 'NOV', 'ano_letivo': 2028}, 409)
        self.assertEqual(self.client.get('/admin/gestao-turmas').status_code, 200)

    def test_invalid_video_and_valid_youtube_links(self):
        for valid in ('abcdefghijk', 'https://youtu.be/abcdefghijk', 'https://www.youtube.com/watch?v=abcdefghijk', 'https://www.youtube.com/embed/abcdefghijk'):
            self.assertEqual(video_id(valid), 'abcdefghijk')
        for invalid in ('javascript:alert(1)', '<iframe>', 'https://youtube.com.evil.test/watch?v=abcdefghijk',
                        'https://user@youtube.com/watch?v=abcdefghijk', 'http://youtu.be/abcdefghijk', 'https://[', None):
            with self.subTest(invalid=invalid), self.assertRaises(HTTPException):
                video_id(invalid)

    def test_cross_course_parent_rejected_and_html_escaped(self):
        self.preparar(False)
        novo = self.post('/cursos', {'disciplina_id': self.d, 'titulo': 'Outro'}, 201)['curso_id']
        self.post(f'/cursos/{novo}/estrutura', {'acao': 'adicionar', 'tipo': 'tema', 'pai_id': self.cap, 'titulo': 'Inválido'}, 404)
        page = self.client.get(f'/cursos/{self.c}')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'&lt;script&gt;', page.data)

    def test_reorder_edit_delete_and_empty_publish_block(self):
        self.preparar(False)
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'adicionar', 'tipo': 'aula', 'pai_id': self.tema, 'titulo': 'Segunda', 'video': '12345678901'})
        with get_session() as db:
            segunda = db.query(AulaModel).filter_by(titulo='Segunda').one().id
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'subir', 'tipo': 'aula', 'id': segunda})
        with get_session() as db:
            self.assertEqual(db.get(AulaModel, segunda).posicao, 1)
        self.post(f'/cursos/{self.c}/estrutura', {'acao': 'remover', 'tipo': 'capitulo', 'id': self.cap}, 409)
        for aula_id in (self.aula, segunda):
            self.post(f'/cursos/{self.c}/estrutura', {'acao': 'remover', 'tipo': 'aula', 'id': aula_id})
        self.login('admin')
        self.post(f'/cursos/{self.c}/estado', {'estado': 'publicado'}, 400)

    def test_owner_authorization_and_role_refresh(self):
        self.preparar(False)
        with get_session() as db:
            from werkzeug.security import generate_password_hash
            user = UsuarioModel(email='prof2@teste.local', senha=generate_password_hash(SENHA), tipo='professor')
            db.add(user)
            db.flush()
            db.add(ProfessorModel(usuario_id=user.id, nome='Outro professor', cpf='00000000003'))
            db.commit()
        self.client.post('/login', json={'email': 'prof2@teste.local', 'senha': SENHA})
        self.assertEqual(self.client.get(f'/cursos/{self.c}').status_code, 403)
        self.login('professor')
        with get_session() as db:
            db.get(UsuarioModel, self.ids['professor']).tipo = 'aluno'
            db.commit()
        self.assertEqual(self.client.get(f'/cursos/{self.c}').status_code, 403)

    def test_migration_repeatable_and_legacy_rows_preserved(self):
        from app.migrations_cursos import migrar_cursos, tabelas_cursos
        from sqlalchemy import text
        for table in reversed(tabelas_cursos(Base.metadata)):
            table.drop(engine, checkfirst=True)
        with engine.begin() as connection:
            connection.execute(text('DELETE FROM educafast_migracoes'))
        migrar_cursos(engine, Base.metadata)
        migrar_cursos(engine, Base.metadata)
        with get_session() as db:
            self.assertEqual(db.get(TurmaModel, self.t).nome, 'Turma 2026')
            self.assertEqual(db.query(AtribuicaoDocenteModel).count(), 0)
            self.assertEqual(db.execute(text('SELECT COUNT(*) FROM educafast_migracoes')).scalar(), 1)

    def test_assignment_applies_to_existing_grade_and_activity_endpoints(self):
        self.preparar()
        self.login('admin')
        with get_session() as db:
            row = db.query(AtribuicaoDocenteModel).join(TurmaDisciplinaModel,
                AtribuicaoDocenteModel.turma_disciplina_id == TurmaDisciplinaModel.id).filter(TurmaDisciplinaModel.turma_id == self.t).one()
            identity = row.id
        self.post('/admin/gestao-turmas', {'acao': 'revogar', 'turma_id': self.t, 'atribuicao_id': identity})
        self.login('professor')
        from werkzeug.datastructures import MultiDict
        from app.controllers.professor_controller import save_student_grade, launch_activity
        data = MultiDict({'turma_id': str(self.t), 'disciplina_id': str(self.d),
                         'aluno_id': str(self.ids['aluno_id']), 'nota': '8', 'titulo': 'Bloqueada'})
        # Controllers exercitados pelas rotas existentes: não depender do redirecionamento HTML.
        with self.app.app_context():
            self.assertEqual(save_student_grade(self.ids['professor'], data)[1], 403)
            self.assertEqual(launch_activity(self.ids['professor'], data)[1], 403)
        self.assertNotIn(b'Turma 2026', self.client.get('/professor').data)

    @unittest.skipUnless(mysql_de_testes(), 'Concorrência de progresso exige MySQL isolado')
    def test_concurrent_completion_is_idempotent(self):
        from concurrent.futures import ThreadPoolExecutor
        import threading
        self.preparar()
        clients = []
        for _ in range(2):
            client = self.app.test_client()
            login = client.post('/login', json={'email': 'aluno@teste.local', 'senha': SENHA})
            clients.append((client, login.json['csrf_token']))
        barrier = threading.Barrier(2)
        def send(index):
            client, token = clients[index]
            barrier.wait(timeout=10)
            return client.post(f'/aprender/{self.o}/aulas/{self.aula}/concluir', json={}, headers={'X-CSRF-Token': token}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(list(pool.map(send, range(2))), [200, 200])
        with get_session() as db:
            self.assertEqual(db.query(ProgressoAulaModel).count(), 1)
