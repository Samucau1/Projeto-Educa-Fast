from werkzeug.security import generate_password_hash

from app.database import get_session
from app.models import UsuarioModel


def run_seed():
    session = get_session()
    try:
        session.query(UsuarioModel).delete()
        admin = UsuarioModel(
            email="admin@admin.com",
            senha=generate_password_hash("123"),
            tipo="ADMIN",
        )
        session.add(admin)
        session.commit()
    finally:
        session.close()

    print("Usuários criados com sucesso!")


if __name__ == "__main__":
    run_seed()
