"""Carga limitada de cursos, exclusivamente no MySQL descartável do Compose."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import http.cookiejar
import json
import logging
import math
from pathlib import Path
import sys
import threading
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'Códigos'))
from ambiente_teste import configurar_banco_testes, mysql_de_testes, validar_mysql


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirmar-banco-descartavel', action='store_true')
    args = parser.parse_args()
    configurar_banco_testes()
    if not args.confirmar_banco_descartavel or not mysql_de_testes():
        parser.error('Exige confirmação e MySQL de testes isolado.')
    from app.database import engine, get_session
    validar_mysql(engine.url)
    from test_cursos import CursosTest
    from app.models.curso_model import ProgressoAulaModel
    from werkzeug.serving import make_server
    from fixtures import SENHA
    CursosTest.setUpClass()
    fixture = CursosTest()
    fixture.setUp()
    fixture.preparar()
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    server = make_server('127.0.0.1', 0, fixture.app, threaded=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f'http://127.0.0.1:{server.server_port}'
    stages = []
    try:
        def run(index):
            client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            def request(path, body=None, csrf=None):
                headers = {'Content-Type': 'application/json'} if body is not None else {}
                if csrf:
                    headers['X-CSRF-Token'] = csrf
                req = urllib.request.Request(base + path, data=json.dumps(body).encode() if body is not None else None, headers=headers)
                start = time.monotonic()
                with client.open(req, timeout=15) as response:
                    result = response.read()
                    if response.status != 200:
                        raise AssertionError(f'HTTP inesperado: {response.status}')
                return result, (time.monotonic() - start) * 1000
            body, elapsed = request('/login', {'email': 'aluno@teste.local', 'senha': SENHA})
            csrf = json.loads(body)['csrf_token']
            durations = [elapsed]
            for _ in range(10):
                body, elapsed = request(f'/aprender/{fixture.o}')
                if b'Primeira aula' not in body:
                    raise AssertionError('Conteúdo ausente')
                durations.append(elapsed)
                _, elapsed = request(f'/aprender/{fixture.o}/aulas/{fixture.aula}/concluir', {}, csrf)
                durations.append(elapsed)
            return durations
        for count in (1, 4, 8, 16):
            with ThreadPoolExecutor(max_workers=count) as pool:
                durations = sorted(v for values in pool.map(run, range(count)) for v in values)
            p95 = durations[math.ceil(len(durations) * .95) - 1]
            if p95 > 5000:
                raise AssertionError(f'p95 excedeu o limite local: {p95}')
            stages.append({'clientes': count, 'requisicoes': len(durations), 'p95_ms': round(p95, 3), 'http_inesperados': 0})
        with get_session() as db:
            if db.query(ProgressoAulaModel).count() != 1:
                raise AssertionError('Conclusão concorrente duplicada')
        summary = {'aprovado': True, 'data': datetime.now(timezone.utc).isoformat(),
                   'banco': 'MySQL 8.4 descartável', 'etapas': stages,
                   'requisicoes': sum(s['requisicoes'] for s in stages), 'progressos_persistidos': 1,
                   'limites': 'Rajadas locais curtas; não estabelece capacidade ou SLA de produção.'}
        output = ROOT / 'Documentos/testes/resultados/mysql/cursos-carga-resumo.json'
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    finally:
        server.shutdown()
        worker.join(timeout=5)
        server.server_close()
        fixture.doCleanups()
        engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
