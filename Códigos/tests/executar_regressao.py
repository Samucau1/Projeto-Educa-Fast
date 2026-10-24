"""Executa unittest e salva evidências sem conectar ao banco da instalação."""
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
import io
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Códigos"))
from ambiente_teste import configurar_banco_testes, mysql_de_testes, pasta_resultados
configurar_banco_testes()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--somente-unitarios", action="store_true")
    args = parser.parse_args()
    prefix = "unitarios" if args.somente_unitarios else "regressao"
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_unitarios.py" if args.somente_unitarios else "test_*.py")
    output = io.StringIO()
    start = time.monotonic()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(suite)
    elapsed = time.monotonic() - start
    reports = pasta_resultados(ROOT)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / f"{prefix}-unittest.txt").write_text(output.getvalue(), encoding="utf-8")
    summary = {
        "data_sao_paulo": datetime.now(timezone(timedelta(hours=-3))).isoformat(),
        "python": platform.python_version(),
        "flask": version("Flask"), "sqlalchemy": version("SQLAlchemy"),
        "banco": "Nao utilizado (testes unitarios)" if args.somente_unitarios else "MySQL 8.4 isolado no Docker" if mysql_de_testes() else "SQLite em memória com foreign_keys=ON",
        "testes": result.testsRun, "falhas": len(result.failures), "erros": len(result.errors),
        "ignorados": len(result.skipped), "duracao_segundos": round(elapsed, 3), "aprovado": result.wasSuccessful(),
    }
    (reports / f"{prefix}-resumo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output.getvalue(), end="")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
