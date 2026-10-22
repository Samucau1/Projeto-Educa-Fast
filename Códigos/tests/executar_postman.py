"""Servidor isolado e execução HTTP real da coleção Postman via Newman."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Códigos"))
from ambiente_teste import mysql_de_testes, validar_mysql, pasta_resultados


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="Mantém servidor descartável para usar no Postman Desktop")
    parser.add_argument("--port", type=int, default=5051)
    args = parser.parse_args()
    newman = Path(os.environ.get("NEWMAN_PATH", str(ROOT / ".cache/postman/node_modules/newman/bin/newman.js")))
    node = shutil.which("node")
    if not args.serve and (not newman.is_file() or not node):
        parser.error("Instale Node.js e execute npm install --prefix .cache/postman newman@6.2.1 na raiz.")

    with tempfile.TemporaryDirectory(prefix="educafast-postman-") as temp:
        # Sobrescreve a URL antes de importar a aplicação. Nunca utiliza o banco do .env.
        if mysql_de_testes():
            validar_mysql(os.environ.get("DB_URL", ""))
        else:
            os.environ["DB_URL"] = "sqlite:///" + (Path(temp) / "teste.sqlite").as_posix()
        from app import create_app
        from app.database import engine, Base
        from sqlalchemy import event
        from fixtures import criar_usuarios
        from gerar_postman import build
        from werkzeug.serving import make_server

        if mysql_de_testes():
            Base.metadata.drop_all(engine)
        else:
            @event.listens_for(engine, "connect")
            def foreign_keys(connection, _):
                connection.execute("PRAGMA foreign_keys=ON")

        app = create_app()
        app.config.update(SECRET_KEY="somente-testes-descartaveis", UPLOAD_FOLDER=str(Path(temp) / "uploads"))
        criar_usuarios()
        build()
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        server = make_server("127.0.0.1", args.port if args.serve else 0, app)
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Servidor de testes descartável: {url}", flush=True)
        try:
            if args.serve:
                print("Importe coleção e ambiente no Postman. Ctrl+C encerra e remove a base.", flush=True)
                server.serve_forever()
                return 0
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            reports = pasta_resultados(ROOT)
            reports.mkdir(parents=True, exist_ok=True)
            start = time.monotonic()
            result = subprocess.run([
                node, str(newman), "run", str(ROOT / "Documentos/testes/postman/EducaFast.postman_collection.json"),
                "-e", str(ROOT / "Documentos/testes/postman/Local.postman_environment.json"),
                "--env-var", f"base_url={url}", "--ignore-redirects", "--timeout-request", "10000",
                "--reporters", "cli,junit", "--reporter-junit-export", str(reports / "postman-junit.xml"), "--color", "off",
            ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
            (reports / "postman-newman.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
            xml = ET.parse(reports / "postman-junit.xml").getroot()
            summary = {
                "data_sao_paulo": datetime.now(timezone(timedelta(hours=-3))).isoformat(),
                "newman": json.loads((newman.parents[1] / "package.json").read_text(encoding="utf-8"))["version"],
                "banco": "MySQL 8.4 isolado no Docker" if mysql_de_testes() else "SQLite descartável com foreign_keys=ON",
                "requisicoes": len(xml.findall("testsuite")), "verificacoes": len(xml.findall(".//testcase")),
                "falhas": len(xml.findall(".//failure")), "erros": len(xml.findall(".//error")),
                "duracao_segundos": round(time.monotonic() - start, 3),
                "exit_code": result.returncode, "aprovado": result.returncode == 0,
            }
            (reports / "postman-resumo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            return result.returncode
        except KeyboardInterrupt:
            return 0 if args.serve else 130
        finally:
            if not args.serve:
                server.shutdown()
                worker.join(timeout=5)
            server.server_close()
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
