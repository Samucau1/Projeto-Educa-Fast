"""Autoriza somente SQLite descartável ou o Postgres exclusivo de testes."""
import os

from flask.testing import FlaskClient
from sqlalchemy.engine import make_url


class ClienteSPA(FlaskClient):
    """Cliente de testes que pede as telas no formato usado pela SPA (JSON)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.environ_base["HTTP_X_EDUCAFAST_SPA"] = "1"


def tela(resposta):
    """Dados da tela (JSON devolvido por render_page)."""
    return resposta.get_json()


def texto_tela(resposta):
    """Todo o conteúdo da tela como texto, para procurar valores exibidos.

    O React renderiza esses valores sempre como texto (nunca como HTML), então um
    conteúdo como "<script>" chega intacto nos dados e aparece escapado na página.
    """
    import json
    return json.dumps(tela(resposta), ensure_ascii=False)


# Hosts aceitos para o Postgres descartável: o serviço do Compose de testes ou um servidor local.
HOSTS_TESTE = {"postgres_test", "127.0.0.1", "localhost"}


def banco_real_de_testes():
    return os.environ.get("EDUCAFAST_TEST_DB") == "1"


def validar_banco_testes(url):
    parsed = make_url(url)
    if not (banco_real_de_testes() and parsed.drivername == "postgresql+psycopg"
            and parsed.host in HOSTS_TESTE and parsed.database == "educafast_regressao"
            and parsed.username == "testes"):
        raise RuntimeError("Operação permitida somente no Postgres isolado de testes (banco educafast_regressao).")


def configurar_banco_testes():
    # Os testes conversam com a API como a aplicação React: as telas respondem com JSON.
    from flask import Flask
    Flask.test_client_class = ClienteSPA
    # Somente o ambiente de testes recebe esta chave sintetica.
    os.environ["SECRET_KEY"] = "testes-isolados-chave-sintetica-2026-educafast"
    os.environ["DATA_ENCRYPTION_KEY"] = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
    if banco_real_de_testes():
        validar_banco_testes(os.environ.get("DB_URL", ""))
    else:
        os.environ["DB_URL"] = "sqlite:///:memory:"


def pasta_resultados(root):
    return root / "docs/testes/resultados" / ("postgres" if banco_real_de_testes() else "")
