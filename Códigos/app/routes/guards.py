from flask import abort, jsonify, session

from app.auth import normalize_role


def admin_required():
    if normalize_role(session.get("user_role")) not in {"admin", "superadmin"}:
        abort(403)


def admin_json_required():
    if normalize_role(session.get("user_role")) not in {"admin", "superadmin"}:
        return jsonify({"erro": "Acesso permitido apenas para administradores"}), 403

    return None


def aluno_required():
    if normalize_role(session.get("user_role")) != "aluno":
        abort(403)


def teacher_required():
    if normalize_role(session.get("user_role")) != "professor":
        abort(403)
