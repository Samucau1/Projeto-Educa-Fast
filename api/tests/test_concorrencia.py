"""Transaction races use the real disposable MySQL; SQLite is not a substitute."""
import io
from concurrent.futures import ThreadPoolExecutor
import tempfile
import threading
import unittest
from unittest.mock import patch

from ambiente_teste import configurar_banco_testes, mysql_de_testes
configurar_banco_testes()
from flask import request
from flask.testing import FlaskClient
from sqlalchemy.orm import Session
from app import create_app
from app.database import Base, engine, get_session
from app.models import SolicitacaoDocumentoModel, DocumentoModel, PedidoPrivacidadeModel
from fixtures import criar_usuarios, exigir_banco_em_memoria, SENHA


@unittest.skipUnless(mysql_de_testes(), 'Corridas transacionais exigem MySQL isolado')
class ConcorrenciaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app=create_app()
        cls.app.config['TESTING']=True
        cls.app.test_client_class=FlaskClient

    def setUp(self):
        Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.app.config['UPLOAD_FOLDER']=self.temp.name
        self.ids=criar_usuarios()

    def clients(self,role):
        result=[]
        for _ in range(2):
            client=self.app.test_client()
            login=client.post('/login',json={'email':role+'@teste.local','senha':SENHA})
            self.assertEqual(login.status_code,200)
            result.append((client,{'X-CSRF-Token':login.json['csrf_token']}))
        return result

    def test_simultaneous_document_fulfillment_has_one_winner(self):
        with get_session() as db:
            row=SolicitacaoDocumentoModel(aluno_id=self.ids['aluno_id'],titulo='Concorrente',status='pendente')
            db.add(row); db.flush(); rid=row.id; db.commit()
        clients=self.clients('aluno'); barrier=threading.Barrier(2)
        def send(index):
            client,headers=clients[index]; barrier.wait(timeout=10)
            return client.post('/aluno/documentos/upload',headers=headers,
                               data={'solicitacao_id':rid,'arquivo':(io.BytesIO(b'one document'),'race.txt')}).status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(send,range(2))),[302,409])
        with get_session() as db:
            self.assertEqual(db.query(DocumentoModel).count(),1)
            self.assertEqual(db.get(SolicitacaoDocumentoModel,rid).status,'enviado')

    def test_stale_admin_cannot_reopen_concurrently_closed_request(self):
        with get_session() as db:
            row=PedidoPrivacidadeModel(usuario_id=self.ids['aluno'],tipo='acesso',status='aberto')
            db.add(row); db.flush(); rid=row.id; db.commit()
        clients=self.clients('admin'); barrier=threading.Barrier(2); closed=threading.Event()
        original=Session.get
        def synchronize_read(db,model,*args,**kwargs):
            result=original(db,model,*args,**kwargs)
            if model is PedidoPrivacidadeModel:
                barrier.wait(timeout=10)
                if request.form['status']=='em_analise':
                    if not closed.wait(timeout=15): raise TimeoutError('Closing transaction did not finish')
            return result
        def send(index):
            client,headers=clients[index]
            try:
                return client.post(f'/admin/privacidade/{rid}',headers=headers,
                                   data={'status':'concluido' if index==0 else 'em_analise','resposta':'Response'}).status_code
            finally:
                if index==0: closed.set()
        with patch.object(Session,'get',synchronize_read), ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(send,range(2)))
        self.assertEqual(results,[302,409])
        with get_session() as db:
            self.assertEqual(db.get(PedidoPrivacidadeModel,rid).status,'concluido')
