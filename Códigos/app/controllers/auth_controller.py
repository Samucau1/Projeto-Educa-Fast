import os
from collections.abc import Mapping
from datetime import datetime
from uuid import uuid4

from flask import current_app
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.auth import generate_token, normalize_role
from app.database import get_session
from app.models import AlunoModel, ProfessorModel, UsuarioModel
from app.security import save_upload


PROFILE_PHOTO_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_PROFILE_PHOTO_BYTES = 2 * 1024 * 1024
DUMMY_PASSWORD_HASH = generate_password_hash("dummy-comparison-not-an-account")


def login_usuario(data):
    if not isinstance(data, Mapping) or not data:
        return {"erro": "Dados nao informados"}, 400

    email = data.get("email")
    senha = data.get("senha")

    if not isinstance(email, str) or not isinstance(senha, str) or not email or not senha or len(email) > 120 or len(senha) > 1024:
        return {"erro": "E-mail e senha sao obrigatorios"}, 400

    session = get_session()
    try:
        user = session.query(UsuarioModel).filter(UsuarioModel.email == email).first()
    finally:
        session.close()

    try:
        password_ok = check_password_hash(user.senha if user else DUMMY_PASSWORD_HASH, senha)
    except (ValueError, UnicodeError):
        password_ok = False
    if not user or not password_ok:
        return {"erro": "Credenciais invalidas"}, 401

    role = normalize_role(user.tipo)

    return {
        "id": user.id,
        "email": user.email,
        "tipo": role.upper(),
        "role": role,
        # O JWT tambem inclui a role para o front enviar nas proximas chamadas protegidas.
        "token": generate_token(user),
    }, 200


def _parse_date(value):
    if not value:
        return None

    return datetime.strptime(value, "%Y-%m-%d").date()


def _save_profile_photo(files):
    if not files or "foto_perfil" not in files:
        return None, None

    foto = files["foto_perfil"]
    if not foto or not foto.filename:
        return None, None

    original_filename = secure_filename(foto.filename)
    if not original_filename or "." not in original_filename:
        return None, ({"erro": "Nome da foto invalido"}, 400)

    extension = original_filename.rsplit(".", 1)[1].lower()
    if extension not in PROFILE_PHOTO_EXTENSIONS:
        return None, ({"erro": "A foto deve estar em JPG ou PNG"}, 400)

    foto.stream.seek(0, os.SEEK_END)
    file_size = foto.stream.tell()
    foto.stream.seek(0)
    if file_size > MAX_PROFILE_PHOTO_BYTES:
        return None, ({"erro": "A foto deve ter no maximo 2MB"}, 400)

    upload_folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"perfil_{uuid4().hex}_{original_filename}"
    saved_path = os.path.join(upload_folder, filename)
    save_upload(foto, saved_path)
    return filename, None


def _remove_saved_file(filename):
    if not filename:
        return

    path = os.path.join(os.path.abspath(current_app.config["UPLOAD_FOLDER"]), filename)
    if os.path.exists(path):
        os.remove(path)


def cadastrar_usuario(data, files=None):
    if not data:
        return {"erro": "Dados nao informados"}, 400

    tipo = normalize_role(data.get("tipo") or data.get("role"))
    email = data.get("email")
    senha = data.get("senha")
    nome = data.get("nome")

    if tipo not in {"admin", "professor", "aluno"}:
        return {"erro": "Tipo de usuario deve ser admin, professor ou aluno"}, 400

    if not email or not senha or not nome:
        return {"erro": "E-mail, senha e nome sao obrigatorios"}, 400
    if not all(isinstance(v, str) for v in (email, senha, nome)) or len(senha) < 8 or len(senha) > 1024 or len(email) > 120:
        return {"erro": "Informe e-mail valido e senha de 8 a 1024 caracteres"}, 400

    foto_perfil, upload_error = _save_profile_photo(files)
    if upload_error:
        return upload_error

    session = get_session()
    try:
        if session.query(UsuarioModel).filter(UsuarioModel.email == email).first():
            _remove_saved_file(foto_perfil)
            return {"erro": "E-mail ja cadastrado"}, 409

        usuario = UsuarioModel(
            email=email,
            senha=generate_password_hash(senha),
            # O cadastro agora grava a role do usuario para refletir professor/aluno no JWT.
            tipo=tipo,
        )
        session.add(usuario)
        session.flush()

        if tipo == "professor":
            cpf = data.get("cpf")
            if not cpf:
                session.rollback()
                _remove_saved_file(foto_perfil)
                return {"erro": "CPF e obrigatorio para professor"}, 400

            session.add(
                ProfessorModel(
                    usuario_id=usuario.id,
                    nome=nome,
                    cpf=cpf,
                    telefone=data.get("telefone"),
                    foto_perfil=foto_perfil,
                    disciplina_principal=(
                        data.get("disciplina_principal") or data.get("disciplina")
                    ),
                    formacao_academica=data.get("formacao_academica") or data.get("formacao"),
                    regime_trabalho=data.get("regime_trabalho") or data.get("regime"),
                    data_admissao=_parse_date(data.get("data_admissao") or data.get("admissao")),
                )
            )
        elif tipo == "aluno":
            cpf = data.get("cpf")
            matricula = data.get("matricula")
            if not matricula:
                session.rollback()
                _remove_saved_file(foto_perfil)
                return {"erro": "Matricula e obrigatoria para aluno"}, 400

            session.add(
                AlunoModel(
                    usuario_id=usuario.id,
                    nome=nome,
                    cpf=cpf,
                    matricula=matricula,
                    foto_perfil=foto_perfil,
                    curso_serie=data.get("curso_serie") or data.get("curso"),
                    status_matricula=data.get("status_matricula") or data.get("status"),
                    data_nascimento=_parse_date(data.get("data_nascimento")),
                )
            )

        session.commit()
        return {
            "id": usuario.id,
            "email": usuario.email,
            "tipo": tipo.upper(),
            "role": tipo,
        }, 201
    except ValueError:
        session.rollback()
        _remove_saved_file(foto_perfil)
        return {"erro": "Data de nascimento deve estar no formato YYYY-MM-DD"}, 400
    except IntegrityError:
        session.rollback()
        _remove_saved_file(foto_perfil)
        return {"erro": "Dados duplicados: verifique CPF, matricula ou e-mail"}, 409
    except Exception:
        session.rollback()
        _remove_saved_file(foto_perfil)
        raise
    finally:
        session.close()


def buscar_alunos(termo, professor_user_id):
    from app.models import AlunoTurmaModel, ProfessorTurmaModel
    termo = (termo or "").strip()
    if not termo:
        return {"erro": "Informe um termo de busca"}, 400

    session = get_session()
    try:
        alunos = (
            session.query(AlunoModel)
            .join(AlunoTurmaModel, AlunoTurmaModel.aluno_id == AlunoModel.id)
            .join(ProfessorTurmaModel, ProfessorTurmaModel.turma_id == AlunoTurmaModel.turma_id)
            .join(ProfessorModel, ProfessorModel.id == ProfessorTurmaModel.professor_id)
            .filter(ProfessorModel.usuario_id == professor_user_id)
            .filter(AlunoModel.nome.icontains(termo, autoescape=True))
            .distinct()
            .limit(20)
            .all()
        )

        return {
            "alunos": [
                {
                    "id": aluno.id,
                    "nome": aluno.nome,
                    "matricula": aluno.matricula,
                }
                for aluno in alunos
            ]
        }, 200
    finally:
        session.close()
