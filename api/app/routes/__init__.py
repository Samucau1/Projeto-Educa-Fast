from app.routes.document_routes import document_bp
from app.routes.home_routes import home_blueprint
from app.routes.auth_routes import auth_bp
from app.routes.professor_routes import professor_bp
from app.routes.aluno_routes import aluno_bp


def register_routes(app):
    app.register_blueprint(home_blueprint)
    app.register_blueprint(auth_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(professor_bp)
    app.register_blueprint(aluno_bp)
