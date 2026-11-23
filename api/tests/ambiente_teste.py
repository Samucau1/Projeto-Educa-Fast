"""Autoriza somente SQLite descartável ou o MySQL exclusivo do Compose de testes."""
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


def mysql_de_testes():
    return os.environ.get("EDUCAFAST_TEST_MYSQL") == "1"


def validar_mysql(url):
    parsed = make_url(url)
    if not (mysql_de_testes() and parsed.drivername == "mysql+pymysql"
            and parsed.host == "mysql_test" and parsed.database == "educafast_regressao"
            and parsed.username == "testes"):
        raise RuntimeError("Operação permitida somente no MySQL isolado do Compose de testes.")


def configurar_banco_testes():
    # Os testes conversam com a API como a aplicação React: as telas respondem com JSON.
    from flask import Flask
    Flask.test_client_class = ClienteSPA
    # Somente o ambiente de testes recebe esta chave sintetica.
    os.environ["SECRET_KEY"] = "testes-isolados-chave-sintetica-2026-educafast"
    os.environ["DATA_ENCRYPTION_KEY"] = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="
    if mysql_de_testes():
        validar_mysql(os.environ.get("DB_URL", ""))
    else:
        os.environ["DB_URL"] = "sqlite:///:memory:"


def pasta_resultados(root):
    return root / "docs/testes/resultados" / ("mysql" if mysql_de_testes() else "")
