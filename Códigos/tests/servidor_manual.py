"""Servidor manual restrito ao Compose sintético; preserva dados já existentes."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ambiente_teste import validar_mysql


def main():
    if os.environ.get('EDUCAFAST_MANUAL') != '1':
        raise RuntimeError('Use o serviço manual do Compose de testes.')
    validar_mysql(os.environ.get('DB_URL', ''))
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
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
