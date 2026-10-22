"""Ambiente manual local: cria exemplos somente quando o banco está vazio."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ambiente_teste import validar_mysql


def main():
    if os.environ.get("EDUCAFAST_MANUAL") != "1":
        raise RuntimeError("Use o serviço manual do Compose de testes.")
    validar_mysql(os.environ.get("DB_URL", ""))
    from app import create_app
    from app.database import get_session
    from app.models import (
        UsuarioModel, DisciplinaModel, TurmaModel, ProfessorDisciplinaModel,
        ProfessorTurmaModel, AlunoTurmaModel, TurmaDisciplinaModel,
        AtividadeModel, ComunicadoModel,
    )
    from fixtures import criar_usuarios

    app = create_app()
    with get_session() as db:
        vazio = db.query(UsuarioModel).count() == 0
    if vazio:
        ids = criar_usuarios()
        with get_session() as db:
            disciplina = DisciplinaModel(nome="Matemática — teste manual", codigo="MAT-MANUAL", carga_horaria=60)
            turma = TurmaModel(nome="Turma de demonstração", codigo="MANUAL-1", ano_letivo=2026, turno="Matutino")
            db.add_all([disciplina, turma])
            db.flush()
            db.add_all([
                ProfessorDisciplinaModel(professor_id=ids["professor_id"], disciplina_id=disciplina.id),
                ProfessorTurmaModel(professor_id=ids["professor_id"], turma_id=turma.id),
                AlunoTurmaModel(aluno_id=ids["aluno_id"], turma_id=turma.id),
                TurmaDisciplinaModel(turma_id=turma.id, disciplina_id=disciplina.id),
                AtividadeModel(professor_id=ids["professor_id"], turma_id=turma.id, disciplina_id=disciplina.id,
                               titulo="Atividade de demonstração", descricao="Exemplo para conferir a visão do professor e do aluno."),
                ComunicadoModel(titulo="Bem-vindo ao teste manual", destinatario="Geral",
                                mensagem="Este ambiente contém apenas dados de demonstração. Teste os perfis, cores e mensagens.",
                                criado_por="admin@teste.local"),
            ])
            db.commit()
        print("Usuários e exemplos criados no banco manual.", flush=True)
    else:
        print("Banco existente preservado; exemplos não serão recriados.", flush=True)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
