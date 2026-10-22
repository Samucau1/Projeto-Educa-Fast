"""Dados sintéticos compartilhados pela regressão e pelo servidor do Postman."""
from werkzeug.security import generate_password_hash

from app.database import get_session, engine
from app.models import UsuarioModel, AlunoModel, ProfessorModel

SENHA = "Teste-local-2026!"


def exigir_banco_em_memoria():
    from ambiente_teste import mysql_de_testes, validar_mysql
    if mysql_de_testes():
        validar_mysql(engine.url)
        return
    if str(engine.url) != "sqlite:///:memory:":
        raise RuntimeError("Regressão permitida somente com SQLite em memória.")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def criar_usuarios():
    ids = {}
    with get_session() as db:
        for role in ("superadmin", "admin", "professor", "aluno", "outro_aluno"):
            user = UsuarioModel(email=f"{role}@teste.local", senha=generate_password_hash(SENHA), tipo="aluno" if role == "outro_aluno" else role)
            db.add(user)
            db.flush()
            ids[role] = user.id
            if role in ("aluno", "outro_aluno"):
                aluno = AlunoModel(usuario_id=user.id, nome=f"Aluno {role}", matricula=f"TESTE-{role}")
                db.add(aluno)
                db.flush()
                ids[f"{role}_id"] = aluno.id
            if role == "professor":
                professor = ProfessorModel(usuario_id=user.id, nome="Professor Teste", cpf="00000000001")
                db.add(professor)
                db.flush()
                ids["professor_id"] = professor.id
        db.commit()
    return ids
