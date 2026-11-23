"""Ponte entre as rotas Flask e a aplicação React (web/).

As rotas continuam decidindo permissões, dados e redirecionamentos. Em vez de renderizar
HTML, chamam ``render_page(nome_da_tela, **dados)``:

* requisições da SPA (cabeçalho ``X-EducaFast-SPA: 1``) recebem JSON com a tela, os dados
  serializados e o contexto global (sessão, tema, identidade da escola, CSRF, mensagens);
* navegações diretas do navegador recebem o ``index.html`` gerado pelo build do React, que
  então busca os mesmos dados em JSON.
"""
import datetime as dt
from decimal import Decimal
from pathlib import Path

from flask import current_app, g, get_flashed_messages, jsonify, request, session, url_for
from sqlalchemy import inspect as sa_inspect
from werkzeug.exceptions import HTTPException

SPA_HEADER = "X-EducaFast-SPA"
# Colunas de modelos que nunca vão para o navegador junto com objetos ORM (minimização, LGPD).
# Telas que exibem esses dados recebem valores preparados pelos controllers (ex.: cpf_value).
COLUNAS_PROTEGIDAS = {"senha", "cpf", "cpf_hash", "telefone", "data_nascimento"}
# Campos de formulário que não são devolvidos quando a tela é reexibida após um erro.
CAMPOS_NAO_DEVOLVIDOS = {"senha", "csrf_token"}
PAGE_HEADER = "X-EducaFast-Pagina"


def is_spa_request():
    return request.headers.get(SPA_HEADER) == "1"


def to_json(value):
    """Converte os dados das rotas preservando o texto que o Jinja exibia."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dt.datetime):
        return str(value)
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): to_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_json(v) for v in value]
    if hasattr(value, "_asdict"):
        return [to_json(v) for v in value]
    try:
        mapper = sa_inspect(value).mapper
    except Exception:
        mapper = None
    if mapper is not None:
        return {attr.key: to_json(getattr(value, attr.key)) for attr in mapper.column_attrs
                if attr.key not in COLUNAS_PROTEGIDAS}
    if hasattr(value, "keys") and hasattr(value, "__getitem__"):
        return {str(k): to_json(value[k]) for k in value.keys()}
    return str(value)


def _url_templates():
    """Mapa endpoint -> URL gerada pelo próprio url_for, com {arg} no lugar dos parâmetros."""
    cache = current_app.extensions.setdefault("educafast_urls", {})
    if cache:
        return cache
    endpoints = {}
    for rule in current_app.url_map.iter_rules():
        if rule.endpoint == "static" or rule.endpoint in endpoints:
            continue
        endpoints[rule.endpoint] = sorted(rule.arguments)
    for endpoint, args in endpoints.items():
        sentinels = {arg: 987654300 + i for i, arg in enumerate(args)}
        try:
            url = url_for(endpoint, **sentinels)
        except Exception:
            try:
                url = url_for(endpoint, **{a: f"__{a}__" for a in args})
                sentinels = {a: f"__{a}__" for a in args}
            except Exception:
                continue
        for arg, sentinel in sentinels.items():
            url = url.replace(str(sentinel), "{" + arg + "}")
        cache[endpoint] = url
    return cache


def global_context():
    return {
        "sessao": {
            "user_id": session.get("user_id"),
            "user_role": session.get("user_role"),
            "user_email": session.get("user_email"),
        },
        "endpoint": request.endpoint,
        "tema": to_json(getattr(g, "tema", {})),
        "escola": to_json(getattr(g, "escola", {})),
        "csrf_token": session.get("csrf_token", ""),
        "lgpd": {"controlador": current_app.config.get("LGPD_CONTROLADOR")},
    }


def formulario_devolvido():
    """Campos enviados, para a tela reexibida após um erro preencher o formulário de novo."""
    if request.method != "POST":
        return {}
    try:
        campos = request.form
    except HTTPException:
        # Ex.: corpo acima do limite (413); a tela de erro não depende do formulário.
        return {}
    return {k: v for k, v in campos.items() if k not in CAMPOS_NAO_DEVOLVIDOS}


def page_payload(page, data):
    payload = {
        "pagina": page,
        "dados": to_json(data),
        "global": global_context(),
        "mensagens": [list(m) for m in get_flashed_messages(with_categories=True)],
        "form": formulario_devolvido(),
        "args": request.args.to_dict(),
    }
    return payload


BUILD_AUSENTE = "Build do front-end ausente. Execute 'npm ci' e 'npm run build' na pasta web/."


def spa_index():
    """index.html gerado pelo build do React (web/), ou um aviso quando o build não existe."""
    index = Path(current_app.static_folder) / "dist" / "index.html"
    if not index.is_file():
        current_app.logger.warning(BUILD_AUSENTE)
        return BUILD_AUSENTE, "text/plain; charset=utf-8"
    return index.read_text(encoding="utf-8"), "text/html; charset=utf-8"


def render_page(page, status=200, **data):
    """Substitui render_template: a tela é desenhada pelo React."""
    if page.endswith(".html"):
        page = page[:-5]
    if is_spa_request():
        response = jsonify(page_payload(page, data))
        response.status_code = status
        response.headers[PAGE_HEADER] = "1"
        response.headers["Vary"] = SPA_HEADER
        return response
    body, content_type = spa_index()
    response = current_app.response_class(body, status=status, content_type=content_type)
    response.headers["Vary"] = SPA_HEADER
    return response


def init_spa(app):
    # Mantém a ordem dos dicionários (opções de formulários, por exemplo) como no Python.
    app.json.sort_keys = False

    @app.get("/api/rotas")
    def rotas():
        return jsonify(_url_templates())
