"""Bounded HTTP stress of every functional family, only on the disposable MySQL.

No target URL is accepted. Starts its own threaded server on loopback, creates
synthetic users, and asserts HTTP contracts plus persistence after concurrency.
"""
import argparse
import base64
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import http.cookiejar
import json
import logging
import math
from pathlib import Path
import secrets
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Códigos'))
from ambiente_teste import configurar_banco_testes, mysql_de_testes, validar_mysql


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, run, stage, worker):
        self.run, self.stage, self.worker = run, stage, worker
        self.http = urllib.request.build_opener(NoRedirect, urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf, self.jwt = '', ''

    def request(self, label, path, expected=200, method='GET', data=None, json_body=None, file=None, csrf=True, bearer=None):
        headers, body = {}, None
        if json_body is not None:
            body = json.dumps(json_body).encode(); headers['Content-Type'] = 'application/json'
        elif file is not None:
            boundary = 'educafast-' + secrets.token_hex(12)
            chunks = []
            for key, value in (data or {}).items():
                chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{file[0]}"; filename="{file[1]}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode())
            chunks.extend([file[2], f'\r\n--{boundary}--\r\n'.encode()])
            body = b''.join(chunks); headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
        elif data is not None:
            body = urllib.parse.urlencode(data).encode(); headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if csrf and method != 'GET' and self.csrf:
            headers['X-CSRF-Token'] = self.csrf
        if bearer:
            headers['Authorization'] = 'Bearer ' + bearer
        request = urllib.request.Request(self.run.url + path, data=body, headers=headers, method=method)
        start = time.monotonic()
        status, content = 0, b''
        try:
            try:
                response = self.http.open(request, timeout=30)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                status, content = response.code, response.read()
        finally:
            with self.run.lock:
                self.run.records.append({'stage':self.stage, 'label':label, 'status':status,
                                         'expected':expected, 'ms':round((time.monotonic()-start)*1000,3)})
        if status != expected:
            raise AssertionError(f'{label}: expected {expected}, got {status}; {content[:200]!r}')
        return content

    def login(self, email):
        result = json.loads(self.request('autenticacao/login','/login', method='POST', json_body={'email':email,'senha':self.run.password}))
        self.csrf, self.jwt = result['csrf_token'], result['token']


class Run:
    def __init__(self, url, password, identities):
        self.url, self.password, self.identities = url, password, identities
        self.records, self.errors, self.stages = [], [], []
        self.lock = threading.Lock()
        self.cycles = 0

    def workflow(self, worker, stage, cycles):
        from app.database import get_session
        from app.models import (AlunoModel, ProfessorModel, UsuarioModel, DisciplinaModel, TurmaModel,
                                SolicitacaoDocumentoModel, PedidoPrivacidadeModel)
        clients = {role:Client(self, stage, worker) for role in ('superadmin','admin','professor','aluno','outro')}
        identity = self.identities[worker]
        for role, client in clients.items():
            client.login(identity[role])
        su, admin, teacher, student, other = (clients[r] for r in ('superadmin','admin','professor','aluno','outro'))
        visitor = Client(self,stage,worker)
        visitor.request('publico/privacidade','/privacidade')
        visitor.request('bloqueio/visitante','/admin/dashboard',403)
        for cycle in range(cycles):
            tag = f's{stage}w{worker}c{cycle}'
            su.request('super/tela','/super/usuarios')
            created = json.loads(su.request('super/criar-admin','/cadastro',201,'POST',json_body={
                'nome':tag,'email':f'{tag}@teste.local','senha':self.password,'tipo':'admin'}))
            uid = created['id']
            for role in ('aluno','admin'):
                su.request('super/alterar-perfil','/super/usuarios/'+str(uid)+'/perfil',302,'POST',
                           data={'tipo':role,'nome':tag,'matricula':'M'+tag})
            su.request('layout/gravar','/super/layout',302,'POST',data={'cor_fundo':'#06385d','cor_destaque':'#22d3ee'})
            su.request('layout/ler','/super/layout')
            for path in ('/admin/dashboard','/admin/cadastro-alunos','/admin/cadastro-professores','/admin/banco-de-dados'):
                admin.request('admin/telas',path)
            for role, extra in [('aluno',{'matricula':'NEW'+tag}),('professor',{'cpf':str(90000000000+len(self.stages)*10000+worker*100+cycle)})]:
                admin.request('cadastro/'+role,'/cadastro/'+role,201,'POST',json_body={'nome':tag,'email':f'{role}{tag}@teste.local','senha':self.password,**extra})
            admin.request('academico/disciplina','/admin/disciplinas',302,'POST',data={'nome':tag,'codigo':'D'+tag,'carga_horaria':60})
            admin.request('academico/turma','/admin/turmas',302,'POST',data={'nome':tag,'codigo':'T'+tag,'ano_letivo':2026})
            with get_session() as db:
                discipline = db.query(DisciplinaModel).filter_by(codigo='D'+tag).one().id
                classroom = db.query(TurmaModel).filter_by(codigo='T'+tag).one().id
            aid, pid = identity['aluno_id'], identity['professor_id']
            admin.request('academico/vinculo-disciplina','/admin/disciplinas',302,'POST',data={'action':'associate_teacher','professor_id':pid,'disciplina_id':discipline})
            for action, key, value in [('associate_teacher','professor_id',pid),('associate_student','aluno_id',aid)]:
                admin.request('academico/vinculo-turma','/admin/turmas',302,'POST',data={'action':action,key:value,'turma_id':classroom})
            photo=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
            admin.request('cadastro/editar-aluno',f'/admin/alunos/{aid}/editar',302,'POST',data={'nome':'Aluno '+str(worker),'email':identity['aluno'],'matricula':'SEED'+str(worker)},file=('foto_perfil','avatar.png',photo))
            with get_session() as db:
                avatar=db.get(AlunoModel,aid).foto_perfil
            assert student.request('documentos/foto','/arquivos/perfil/'+avatar)==photo
            other.request('bloqueio/foto-alheia','/arquivos/perfil/'+avatar,404)
            admin.request('cadastro/editar-professor',f'/admin/professores/{pid}/editar',302,'POST',data={'nome':'Professor '+str(worker),'email':identity['professor'],'cpf':str(10000000000+worker)})
            for kind, rid in [('alunos',aid),('professores',pid)]:
                admin.request('cadastro/detalhes',f'/admin/{kind}/{rid}')
                admin.request('documentos/solicitar',f'/admin/{kind}/{rid}/documentos/solicitar',302,'POST',data={'titulo':tag,'mensagem':'Documento sintetico'})
            admin.request('comunicados/publicar','/admin/comunicados',302,'POST',data={'titulo':tag,'mensagem':'Aviso <script>teste</script>'})
            for client in (su,admin,teacher,student):
                content = client.request('comunicados/ler','/mensagens')
                assert b'&lt;script&gt;' in content
            teacher.request('bloqueio/professor-publicacao','/admin/comunicados',403,'POST',data={'titulo':'X','mensagem':'X'})
            for path in ('/professor','/professor/teste'):
                teacher.request('professor/telas',path,bearer=teacher.jwt)
            base = {'turma_id':classroom,'disciplina_id':discipline}
            teacher.request('academico/atividade','/professor/atividades/lancar',302,'POST',data={**base,'titulo':tag},file=('arquivo','atividade.txt',b'atividade'))
            for grade in ('8,5','9'):
                teacher.request('academico/nota','/professor/notas/salvar',302,'POST',data={**base,'aluno_id':aid,'nota':grade})
            search=json.loads(teacher.request('professor/busca','/alunos/busca?termo=Aluno',bearer=teacher.jwt))
            assert all(set(row)=={'id','nome','matricula'} for row in search['alunos'])
            api = Client(self,stage,worker)
            document=json.loads(api.request('documentos/upload-jwt','/arquivos/upload',201,'POST',data={'aluno_id':aid,'disciplina_id':discipline},file=('arquivo','privado.txt',tag.encode()),bearer=teacher.jwt))
            filename=document['documento']['arquivo']
            assert student.request('documentos/download','/arquivos/download/'+filename)==tag.encode()
            other.request('bloqueio/documento-alheio','/arquivos/download/'+filename,404)
            with get_session() as db:
                sr=db.query(SolicitacaoDocumentoModel).filter_by(aluno_id=aid,titulo=tag).one().id
                pr=db.query(SolicitacaoDocumentoModel).filter_by(professor_id=pid,titulo=tag).one().id
            for client,path,rid in [(student,'/aluno/documentos/upload',sr),(teacher,'/professor/documentos/upload',pr)]:
                client.request('documentos/responder',path,302,'POST',data={'solicitacao_id':rid},file=('arquivo','resposta.txt',b'documento'))
                client.request('bloqueio/reenvio',path,409,'POST',data={'solicitacao_id':rid},file=('arquivo','resposta.txt',b'documento'))
            admin.request('documentos/upload-professor',f'/professores/{pid}/arquivos/upload',201,'POST',file=('arquivo','professor.txt',b'documento'))
            for path in ('/aluno',f'/aluno/disciplinas/{discipline}'):
                student.request('aluno/telas',path)
            other.request('bloqueio/disciplina-alheia',f'/aluno/disciplinas/{discipline}',404)
            student.request('bloqueio/csrf','/minha-privacidade',400,'POST',data={'tipo':'acesso'},csrf=False)
            student.request('lgpd/pedido','/minha-privacidade',302,'POST',data={'tipo':'correcao','detalhe':tag})
            with get_session() as db:
                request_id=db.query(PedidoPrivacidadeModel).filter_by(usuario_id=identity['aluno_user']).order_by(PedidoPrivacidadeModel.id.desc()).first().id
            admin.request('lgpd/fila','/admin/privacidade')
            admin.request('lgpd/resposta',f'/admin/privacidade/{request_id}',302,'POST',data={'status':'concluido','resposta':'Atendido '+tag})
            admin.request('bloqueio/reabertura',f'/admin/privacidade/{request_id}',409,'POST',data={'status':'em_analise','resposta':'X'})
            student.request('lgpd/protocolos','/minha-privacidade')
            exported=json.loads(student.request('lgpd/exportar','/minha-privacidade/exportar',method='POST'))
            assert exported['conta']['email']==identity['aluno'] and 'senha' not in exported['conta']
            student.request('bloqueio/lgpd-admin','/admin/privacidade',403)
            with self.lock: self.cycles += 1
        for client in clients.values():
            client.request('autenticacao/logout','/logout',302,'POST')

    def reads(self, worker, stage, count):
        client=Client(self,stage,worker)
        client.login(self.identities[worker%len(self.identities)]['aluno'])
        for i in range(count):
            client.request('leitura/saturacao',('/aluno','/mensagens','/privacidade','/minha-privacidade')[i%4])

    def stage(self, label, users, target):
        start=time.monotonic(); before=len(self.records)
        with ThreadPoolExecutor(max_workers=users) as pool:
            futures=[pool.submit(target,i,label) for i in range(users)]
            for future in futures:
                try: future.result()
                except Exception as error: self.errors.append({'stage':label,'error':str(error)})
        result=metrics(self.records[before:]); result.update(stage=label,usuarios=users,segundos=round(time.monotonic()-start,3))
        result['req_por_segundo']=round(result['requisicoes']/max(result['segundos'],0.001),2)
        self.stages.append(result)
        print(json.dumps(result),flush=True)


def metrics(records):
    times=sorted(row['ms'] for row in records)
    return {'requisicoes':len(records),'inesperadas':sum(r['status']!=r['expected'] for r in records),
            'http_5xx':sum(r['status']>=500 for r in records),
            'p50_ms':times[max(0,math.ceil(len(times)*.5)-1)] if times else 0,
            'p95_ms':times[max(0,math.ceil(len(times)*.95)-1)] if times else 0,
            'max_ms':max(times,default=0)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirmar-banco-descartavel',action='store_true',required=True)
    parser.add_argument('--max-usuarios',type=int,default=8,choices=range(1,17))
    args=parser.parse_args()
    if not mysql_de_testes(): raise RuntimeError('Estresse exige o MySQL descartavel do Compose de testes.')
    import os
    validar_mysql(os.environ.get('DB_URL',''))
    configurar_banco_testes()
    from app import create_app
    from app.database import Base, engine, get_session
    from app.models import (UsuarioModel,AlunoModel,ProfessorModel,ConfiguracaoModel,NotaModel,DocumentoModel,PedidoPrivacidadeModel,AtividadeModel)
    from werkzeug.security import generate_password_hash
    from werkzeug.serving import make_server
    Base.metadata.drop_all(engine)
    app=create_app()
    password='Estresse-sintetico-2026!'
    identities=[]
    with get_session() as db:
        db.add(ConfiguracaoModel(id=1,cor_fundo='#06385d',cor_destaque='#22d3ee'))
        for worker in range(args.max_usuarios):
            identity={}
            for role in ('superadmin','admin','professor','aluno','outro'):
                email=f'{role}{worker}@teste.local'
                user=UsuarioModel(email=email,senha=generate_password_hash(password),tipo='aluno' if role=='outro' else role)
                db.add(user); db.flush(); identity[role]=email
                if role=='professor':
                    profile=ProfessorModel(usuario_id=user.id,nome='Professor '+str(worker),cpf=str(10000000000+worker))
                    db.add(profile); db.flush(); identity['professor_id']=profile.id
                if role in ('aluno','outro'):
                    profile=AlunoModel(usuario_id=user.id,nome='Aluno '+str(worker),matricula=('SEED' if role=='aluno' else 'OTHER')+str(worker))
                    db.add(profile); db.flush()
                    if role=='aluno': identity.update(aluno_id=profile.id,aluno_user=user.id)
            identities.append(identity)
        db.commit()
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    with tempfile.TemporaryDirectory(prefix='educafast-estresse-') as folder:
        app.config['UPLOAD_FOLDER']=folder
        server=make_server('127.0.0.1',0,app,threaded=True)
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        run=Run(f'http://127.0.0.1:{server.server_port}',password,identities)
        try:
            for users,cycles in [(1,1),(min(4,args.max_usuarios),2),(args.max_usuarios,3)]:
                run.stage('fluxos-'+str(users)+'-'+str(cycles),users,lambda i,stage:run.workflow(i,stage,cycles))
            for users in (16,32):
                run.stage('leituras-'+str(users),users,lambda i,stage:run.reads(i,stage,25))
            with get_session() as db:
                counts={name:db.query(model).count() for name,model in [('notas',NotaModel),('documentos',DocumentoModel),('pedidos_lgpd',PedidoPrivacidadeModel),('atividades',AtividadeModel)]}
            expected={'notas':run.cycles,'documentos':run.cycles*4,'pedidos_lgpd':run.cycles,'atividades':run.cycles}
            integrity=counts==expected
            groups=defaultdict(list)
            for row in run.records: groups[row['label']].append(row)
            summary={'data_sao_paulo':datetime.now(timezone(timedelta(hours=-3))).isoformat(),
                     'servidor':'Werkzeug HTTP threaded, loopback, MySQL 8.4 descartavel',
                     'limites':'Amostra limitada, nao determina capacidade maxima nem substitui soak prolongado.',
                     'etapas':run.stages,'total':metrics(run.records),'familias':{k:metrics(v) for k,v in sorted(groups.items())},
                     'ciclos_completos':run.cycles,'persistencia':counts,'esperado':expected,'integridade':integrity,
                     'erros':run.errors,'criterio_p95_ms':5000,
                     'aprovado':not run.errors and integrity and all(s['inesperadas']==0 and s['p95_ms']<=5000 for s in run.stages)}
            reports=ROOT/'Documentos/testes/resultados/mysql'; reports.mkdir(parents=True,exist_ok=True)
            (reports/'estresse-resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            print(json.dumps({'aprovado':summary['aprovado'],'total':summary['total'],'integridade':integrity,'erros':run.errors},ensure_ascii=False),flush=True)
            return 0 if summary['aprovado'] else 1
        finally:
            server.shutdown(); thread.join(timeout=5); server.server_close(); engine.dispose()


if __name__=='__main__':
    raise SystemExit(main())
