from flask import Flask

from config import Config
from .database import init_db
from . import models  # noqa: F401
from .routes import register_routes


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(Config)
    secret = app.config.get("SECRET_KEY") or ""
    if len(secret) < 32 or secret in {"desenvolvimento-web-flask", "troque-esta-chave-por-uma-chave-longa-e-aleatoria"}:
        raise RuntimeError("Configure SECRET_KEY com pelo menos 32 caracteres aleatorios antes de iniciar.")
    from .crypto import cipher
    try:
        cipher()
    except (ValueError, UnicodeError):
        raise RuntimeError("Configure DATA_ENCRYPTION_KEY com uma chave Fernet valida, separada da SECRET_KEY.") from None
    if app.config["APP_ENV"] == "production":
        if not app.config["SESSION_COOKIE_SECURE"] or not app.config["DB_SSL_CA"] or not app.config["LGPD_CONTATO"]:
            raise RuntimeError("Producao exige COOKIE_SECURE=1, DB_SSL_CA e LGPD_CONTATO.")
    init_db()

    register_routes(app)
    from .routes.curso_routes import cursos_bp
    app.register_blueprint(cursos_bp)
    from .routes.academico_routes import academico_bp
    app.register_blueprint(academico_bp)
    from .routes.escola_routes import escola_bp
    app.register_blueprint(escola_bp)
    from .routes.gestao_routes import init_gestao
    init_gestao(app)
    from .routes.privacidade_routes import privacidade_bp
    app.register_blueprint(privacidade_bp)
    from .security import init_security
    init_security(app)
    from .views.error_view import register_error_pages
    register_error_pages(app)

    return app
