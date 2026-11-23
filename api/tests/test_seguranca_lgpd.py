import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ambiente_teste import configurar_banco_testes
configurar_banco_testes()
from flask.testing import FlaskClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app import create_app
from app.crypto import FILE_PREFIX, PREFIX, cipher
from app.database import Base, engine, get_session, init_db
from app.models import (AlunoModel, UsuarioModel, ProfessorModel, DisciplinaModel, TurmaModel,
                        AlunoTurmaModel, ProfessorTurmaModel, ProfessorDisciplinaModel,
                        TurmaDisciplinaModel, SolicitacaoDocumentoModel, DocumentoModel,
                        PedidoPrivacidadeModel, AuditoriaPrivacidadeModel)
from config import Config
from fixtures import criar_usuarios, exigir_banco_em_memoria, SENHA


class SegurancaLGPDTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.test_client_class = FlaskClient
        cls.app.config.update(TESTING=True)

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app.config.update(UPLOAD_FOLDER=self.temp.name, MAX_UPLOAD_BYTES=1024,
                               MAX_CONTENT_LENGTH=4096, UPLOAD_QUOTA_BYTES=8192)
        self.ids = criar_usuarios()
        self.client = self.app.test_client()

    def login(self, role):
        result = self.client.post('/login', json={'email': f'{role}@teste.local', 'senha': SENHA})
        self.assertEqual(result.status_code, 200)
        self.csrf = result.json['csrf_token']
        return result.json['token']

    def post(self, path, **kwargs):
        return self.client.post(path, headers={'X-CSRF-Token': self.csrf}, **kwargs)

    def upload(self, **data):
        return {"aluno_id": self.ids['aluno_id'], "arquivo": (io.BytesIO(b'conteudo privado'), 'segredo.txt'), **data}

    def vinculos(self):
        with get_session() as db:
            d = DisciplinaModel(nome='Materia', codigo='SEC', carga_horaria=10)
            t = TurmaModel(nome='Turma', codigo='SEC', ano_letivo=2026)
            db.add_all([d, t]); db.flush()
            self.disciplina, self.turma = d.id, t.id
            db.add_all([AlunoTurmaModel(aluno_id=self.ids['aluno_id'], turma_id=t.id),
                        ProfessorTurmaModel(professor_id=self.ids['professor_id'], turma_id=t.id),
                        ProfessorDisciplinaModel(professor_id=self.ids['professor_id'], disciplina_id=d.id),
                        TurmaDisciplinaModel(turma_id=t.id, disciplina_id=d.id)])
            db.commit()

    def test_startup_requires_keys_and_production_configuration(self):
        for value in ('', 'desenvolvimento-web-flask'):
            with patch.object(Config, 'SECRET_KEY', value), self.assertRaises(RuntimeError):
                create_app()
        with patch.object(Config, 'DATA_ENCRYPTION_KEY', ''), self.assertRaises(RuntimeError):
            create_app()
        with patch.object(Config, 'APP_ENV', 'production'), self.assertRaises(RuntimeError):
            create_app()

    def test_csrf_all_mutations_and_bearer_cannot_bypass_admin_cookie(self):
        self.login('admin')
        for path in ('/cadastro/aluno', '/admin/turmas', '/admin/disciplinas', '/arquivos/upload',
                     '/admin/alunos/1/editar', '/logout', '/minha-privacidade', '/minha-privacidade/exportar'):
            self.assertEqual(self.client.post(path, headers={'Authorization': 'Bearer fake'}).status_code, 400, path)
        self.assertEqual(self.post('/admin/disciplinas', data={'nome': 'Real', 'codigo': 'REAL', 'carga_horaria': 10}).status_code, 302)
        self.assertEqual(self.client.get('/logout').status_code, 200)
        self.assertEqual(self.client.get('/admin/dashboard').status_code, 200)
        self.assertEqual(self.post('/logout').status_code, 302)
        self.assertEqual(self.client.get('/admin/dashboard').status_code, 403)

    def test_login_origin_and_cookie_headers(self):
        self.assertEqual(self.client.post('/login', json={'email':'admin@teste.local','senha':SENHA}, headers={'Origin':'https://evil.example'}).status_code, 403)
        response = self.client.post('/login', json={'email':'admin@teste.local','senha':SENHA})
        self.assertIn('HttpOnly', response.headers['Set-Cookie'])
        self.assertIn('SameSite=Lax', response.headers['Set-Cookie'])
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(self.client.post('/login', json={'email':'admin@teste.local','senha':'\ud800'}).status_code, 401)
        self.assertEqual(self.client.get('/professor/teste', headers={'Authorization':'Bearer \u00e9.x.x'}).status_code, 401)

    def test_teacher_upload_assignment_and_privacy_search(self):
        token = self.login('professor')
        api = self.app.test_client()
        headers = {'Authorization': 'Bearer '+token}
        self.assertEqual(api.post('/arquivos/upload', headers=headers, data=self.upload()).status_code, 403)
        self.vinculos()
        for extra in ({'disciplina_id':999}, {'aluno_id':self.ids['outro_aluno_id'], 'disciplina_id':self.disciplina}):
            self.assertEqual(api.post('/arquivos/upload', headers=headers, data=self.upload(**extra)).status_code, 403)
        result = api.post('/arquivos/upload', headers=headers, data=self.upload(disciplina_id=self.disciplina))
        self.assertEqual(result.status_code, 201)
        result = api.get('/alunos/busca?termo=Aluno', headers=headers)
        self.assertEqual(len(result.json['alunos']), 1)
        self.assertEqual(set(result.json['alunos'][0]), {'id','nome','matricula'})
        self.assertEqual(api.get('/alunos/busca?termo=%25', headers=headers).json['alunos'], [])

    def test_redirect_variants_rejected_before_file_save(self):
        self.login('admin')
        for url in ('//evil.example', '/\\evil.example', '/%2fevil.example', '/%5cevil.example', '/x%0d%0aLocation:evil', 'https://evil.example'):
            self.assertEqual(self.post('/arquivos/upload', data=self.upload(redirect_to=url)).status_code, 400, url)
            self.assertEqual(self.post(f"/professores/{self.ids['professor_id']}/arquivos/upload", data=self.upload(redirect_to=url)).status_code, 400)
        with get_session() as db:
            self.assertEqual(db.query(DocumentoModel).count(), 0)
        self.assertEqual(self.post('/arquivos/upload', data=self.upload(redirect_to='/aluno')).status_code, 302)

    def test_size_quota_and_encrypted_file_roundtrip(self):
        self.login('admin')
        self.assertEqual(self.post('/arquivos/upload', data=self.upload(arquivo=(io.BytesIO(b'x'*1025),'large.txt'))).status_code, 413)
        response = self.post('/arquivos/upload', data=self.upload())
        self.assertEqual(response.status_code, 201)
        filename = response.json['documento']['arquivo']
        raw = (Path(self.temp.name)/filename).read_bytes()
        self.assertTrue(raw.startswith(FILE_PREFIX)); self.assertNotIn(b'conteudo privado', raw)
        self.login('aluno')
        download = self.client.get('/arquivos/download/'+filename)
        self.assertEqual(download.data, b'conteudo privado'); download.close()
        self.login('outro_aluno')
        self.assertEqual(self.client.get('/arquivos/download/'+filename).status_code, 404)
        self.login('admin')
        self.app.config['UPLOAD_QUOTA_BYTES'] = 1
        self.assertEqual(self.post('/arquivos/upload', data=self.upload()).status_code, 507)
        self.app.config['MAX_CONTENT_LENGTH'] = 32
        self.assertEqual(self.post('/arquivos/upload', data=self.upload()).status_code, 413)

    def test_student_and_teacher_requests_cannot_be_reused(self):
        with get_session() as db:
            a = SolicitacaoDocumentoModel(aluno_id=self.ids['aluno_id'], titulo='Aluno', status='pendente')
            p = SolicitacaoDocumentoModel(professor_id=self.ids['professor_id'], titulo='Professor', status='pendente')
            db.add_all([a,p]); db.flush(); aid,pid=a.id,p.id; db.commit()
        for role, path, rid in [('aluno','/aluno/documentos/upload',aid), ('professor','/professor/documentos/upload',pid)]:
            self.login(role)
            first = self.post(path, data=self.upload(solicitacao_id=rid))
            self.assertEqual(first.status_code, 302, first.data)
            self.assertEqual(self.post(path, data=self.upload(solicitacao_id=rid)).status_code, 409)
        with get_session() as db:
            self.assertEqual(db.query(DocumentoModel).count(), 2)

    def test_fields_encrypted_and_cpf_uniqueness(self):
        with get_session() as db:
            a = db.get(AlunoModel, self.ids['aluno_id']); a.cpf='123.456.789-00'; db.commit()
        with engine.connect() as conn:
            raw=conn.execute(text('SELECT cpf, cpf_hash FROM alunos WHERE id=:id'), {'id':self.ids['aluno_id']}).one()
            self.assertTrue(raw[0].startswith(PREFIX)); self.assertNotIn('123.456', raw[0])
        with get_session() as db:
            self.assertEqual(db.get(AlunoModel,self.ids['aluno_id']).cpf, '123.456.789-00')
            other=db.get(AlunoModel,self.ids['outro_aluno_id']); other.cpf='12345678900'
            with self.assertRaises(IntegrityError): db.commit()

    def test_legacy_fields_and_files_migration(self):
        with engine.begin() as conn:
            conn.execute(text("UPDATE alunos SET cpf='98765432100', cpf_hash=NULL, data_nascimento='2010-01-02' WHERE id=:id"), {'id':self.ids['aluno_id']})
        init_db()
        with get_session() as db:
            self.assertEqual(str(db.get(AlunoModel,self.ids['aluno_id']).data_nascimento),'2010-01-02')
        path=Path(self.temp.name)/'legacy.txt'; path.write_bytes(b'legacy')
        self.assertEqual(self.app.test_cli_runner().invoke(args=['criptografar-arquivos']).exit_code,0)
        self.assertTrue(path.read_bytes().startswith(FILE_PREFIX))
        self.assertEqual(self.app.test_cli_runner().invoke(args=['criptografar-arquivos']).exit_code,0)

    def test_privacy_request_export_ownership_and_admin_workflow(self):
        self.assertEqual(self.client.get('/privacidade').status_code, 200)
        self.assertEqual(self.client.get('/minha-privacidade').status_code, 403)
        self.login('aluno')
        self.assertEqual(self.post('/minha-privacidade',data={'tipo':'correcao','detalhe':'Nome <script>alert(1)</script>'}).status_code,302)
        self.assertIn(b'&lt;script&gt;',self.client.get('/minha-privacidade').data)
        exported=self.post('/minha-privacidade/exportar?usuario_id='+str(self.ids['admin']))
        self.assertEqual(exported.json['conta']['email'],'aluno@teste.local')
        self.assertNotIn(b'senha',exported.data)
        self.assertEqual(exported.headers['Cache-Control'],'no-store')
        with get_session() as db:
            pid=db.query(PedidoPrivacidadeModel).one().id
        with engine.connect() as conn:
            self.assertTrue(conn.execute(text('SELECT detalhe FROM pedidos_privacidade')).scalar().startswith(PREFIX))
        self.login('outro_aluno')
        self.assertNotIn(b'Nome &lt;script&gt;',self.client.get('/minha-privacidade').data)
        self.assertEqual(self.client.get('/admin/privacidade').status_code,403)
        self.assertEqual(self.post(f'/admin/privacidade/{pid}',data={'status':'concluido','resposta':'x'}).status_code,403)
        self.login('admin')
        self.assertEqual(self.client.get('/admin/privacidade').status_code,200)
        self.assertEqual(self.post(f'/admin/privacidade/{pid}',data={'status':'concluido','resposta':'Atendido'}).status_code,302)
        self.assertEqual(self.post(f'/admin/privacidade/{pid}',data={'status':'em_analise','resposta':'x'}).status_code,409)
        with get_session() as db:
            self.assertEqual(db.query(AuditoriaPrivacidadeModel).count(),3)

    def test_photos_require_owner_or_admin(self):
        with get_session() as db:
            db.get(AlunoModel,self.ids['aluno_id']).foto_perfil='perfil_teste.jpg'; db.commit()
        (Path(self.temp.name)/'perfil_teste.jpg').write_bytes(FILE_PREFIX+cipher().encrypt(b'image'))
        self.assertEqual(self.client.get('/arquivos/perfil/perfil_teste.jpg').status_code,403)
        self.login('outro_aluno'); self.assertEqual(self.client.get('/arquivos/perfil/perfil_teste.jpg').status_code,404)
        self.login('aluno'); self.assertEqual(self.client.get('/arquivos/perfil/perfil_teste.jpg').data,b'image')

    def test_login_limit_shared_and_no_account_enumeration(self):
        self.app.config['LOGIN_ATTEMPTS_PER_WINDOW'] = 2
        try:
            for email in ('admin@teste.local', 'missing@teste.local'):
                response = self.client.post('/login', json={'email':email, 'senha':'wrong'})
                self.assertEqual(response.status_code,401)
                self.assertEqual(response.json,{'erro':'Credenciais invalidas'})
            self.assertEqual(self.client.post('/login',json={}).status_code,429)
        finally:
            self.app.config['LOGIN_ATTEMPTS_PER_WINDOW'] = 120

    def test_sibling_upload_writers_enforce_size_and_rollback_claim(self):
        self.vinculos()
        self.login('admin')
        self.assertEqual(self.post(f"/professores/{self.ids['professor_id']}/arquivos/upload",data=self.upload(arquivo=(io.BytesIO(b'x'*1025),'large.txt'))).status_code,413)
        data={'nome':'Novo','email':'novo@teste.local','senha':SENHA,'cpf':'00000000002',
              'foto_perfil':(io.BytesIO(b'x'*1025),'photo.png')}
        self.assertEqual(self.post('/cadastro/professor',data=data).status_code,413)
        self.login('professor')
        self.assertEqual(self.post('/professor/atividades/lancar',data={'turma_id':self.turma,'disciplina_id':self.disciplina,'titulo':'X','arquivo':(io.BytesIO(b'x'*1025),'large.txt')}).status_code,413)
        with get_session() as db:
            p=SolicitacaoDocumentoModel(professor_id=self.ids['professor_id'],titulo='Pendente',status='pendente')
            db.add(p); db.flush(); rid=p.id; db.commit()
        self.assertEqual(self.post('/professor/documentos/upload',data=self.upload(solicitacao_id=rid,arquivo=(io.BytesIO(b'x'*1025),'large.txt'))).status_code,413)
        with get_session() as db:
            self.assertEqual(db.get(SolicitacaoDocumentoModel,rid).status,'pendente')
        self.assertEqual(self.post('/professor/documentos/upload',data=self.upload(solicitacao_id=rid)).status_code,302)

    def test_duplicate_legacy_cpfs_are_rejected_before_migration(self):
        from sqlalchemy import create_engine, inspect
        from app.database import _protect_legacy_fields
        legacy = create_engine('sqlite:///:memory:')
        self.addCleanup(legacy.dispose)
        with legacy.begin() as conn:
            conn.execute(text('CREATE TABLE alunos (id INTEGER, cpf VARCHAR(14), data_nascimento DATE)'))
            conn.execute(text('CREATE TABLE professores (id INTEGER, cpf VARCHAR(14), telefone VARCHAR(20))'))
            conn.execute(text("INSERT INTO alunos (id,cpf) VALUES (1,'12345678900'),(2,'123.456.789-00')"))
        with patch('app.database.engine', legacy), self.assertRaisesRegex(RuntimeError,'duplicados'):
            _protect_legacy_fields()
        self.assertNotIn('cpf_hash',[c['name'] for c in inspect(legacy).get_columns('alunos')])
        with legacy.connect() as conn:
            self.assertEqual(conn.execute(text('SELECT cpf FROM alunos WHERE id=1')).scalar(),'12345678900')
