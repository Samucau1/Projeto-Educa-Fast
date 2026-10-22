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
    init_db()

    register_routes(app)
    from .routes.gestao_routes import init_gestao
    init_gestao(app)
    from .views.error_view import register_error_pages
    register_error_pages(app)

    return app
