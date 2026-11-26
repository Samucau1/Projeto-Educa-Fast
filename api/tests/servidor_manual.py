"""Servidor manual restrito ao Compose sintético; preserva dados já existentes."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ambiente_teste import validar_banco_testes


OPERADOR_DEMO = 'supremo@teste.local'


def criar_operador_demo():
    """ADM Supremo de demonstração, com a mesma senha dos outros usuários de teste."""
    from sqlalchemy.orm import Session
    from werkzeug.security import generate_password_hash
    from app.database import engine
    from app.escolas import OperadorModel, multiescola_ativo
    from fixtures import SENHA
    if not multiescola_ativo(engine):
        return
    with Session(engine) as db:
        if db.query(OperadorModel).filter_by(email=OPERADOR_DEMO).first() is None:
            db.add(OperadorModel(email=OPERADOR_DEMO, nome='ADM Supremo (demonstração)', senha=generate_password_hash(SENHA)))
            db.commit()
            print('ADM Supremo de demonstração criado.', flush=True)


def main():
    if os.environ.get('EDUCAFAST_MANUAL') != '1':
        raise RuntimeError('Use o serviço manual do Compose de testes.')
    validar_banco_testes(os.environ.get('DB_URL', ''))
    from app import create_app
    from app.database import get_session
    from app.models import UsuarioModel
    from fixtures import criar_usuarios
    from dados_homologacao import popular_homologacao
    app = create_app()
    with get_session() as db:
        vazio = db.query(UsuarioModel).count() == 0
    if vazio:
        popular_homologacao(criar_usuarios())
        print('Demonstração criada: curso em 2026/2027, boletins separados e turma de 2025 para revisão.', flush=True)
    else:
        print('Banco existente preservado; exemplos não serão recriados.', flush=True)
    criar_operador_demo()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
