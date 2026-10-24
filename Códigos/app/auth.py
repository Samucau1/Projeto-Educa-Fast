import base64
import binascii
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import current_app, g, jsonify, request


def normalize_role(role):
    return (role or "").strip().lower()


def _b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _sign(message):
    secret = current_app.config["SECRET_KEY"].encode("utf-8")
    signature = hmac.new(secret, message.encode("ascii"), hashlib.sha256).digest()
    return _b64url_encode(signature)


def generate_token(user):
    role = normalize_role(user.tipo)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=current_app.config["JWT_EXPIRATION_HOURS"]
    )

    # O token carrega a role para o backend validar permissoes nas rotas protegidas.
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": str(user.id),
        "role": role,
        "tipo": role,
        "exp": int(expires_at.timestamp()),
    }
    header_part = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{header_part}.{payload_part}"
    return f"{message}.{_sign(message)}"


def decode_token_from_request():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, (jsonify({"erro": "Token JWT nao informado"}), 401)

    token = auth_header.replace("Bearer ", "", 1).strip()
    try:
        header_part, payload_part, signature = token.split(".")
        message = f"{header_part}.{payload_part}"
        expected_signature = _sign(message)
        if not hmac.compare_digest(signature, expected_signature):
            return None, (jsonify({"erro": "Token JWT invalido"}), 401)

        header = json.loads(_b64url_decode(header_part))
        payload = json.loads(_b64url_decode(payload_part))
    except (ValueError, json.JSONDecodeError, UnicodeError, binascii.Error):
        return None, (jsonify({"erro": "Token JWT invalido"}), 401)

    if not isinstance(header, dict) or not isinstance(payload, dict):
        return None, (jsonify({"erro": "Token JWT invalido"}), 401)
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        return None, (jsonify({"erro": "Token JWT invalido"}), 401)

    try:
        exp = int(payload.get("exp", 0))
    except (TypeError, ValueError):
        return None, (jsonify({"erro": "Token JWT invalido"}), 401)

    if exp < int(datetime.now(timezone.utc).timestamp()):
        return None, (jsonify({"erro": "Token JWT expirado"}), 401)

    from app.database import get_session
    from app.models import UsuarioModel
    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        return None, (jsonify({"erro": "Token JWT invalido"}), 401)
    with get_session() as db:
        user = db.get(UsuarioModel, user_id)
        if user is None:
            return None, (jsonify({"erro": "Usuario nao encontrado"}), 401)
        # Inclusive rotas que decodificam JWT sem usar o decorador.
        payload["role"] = payload["tipo"] = normalize_role(user.tipo)

    return payload, None


def jwt_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        payload, error_response = decode_token_from_request()
        if error_response:
            return error_response

        # g.current_user deixa os dados do JWT disponiveis para as rotas protegidas.
        g.current_user = payload
        return view_func(*args, **kwargs)

    return wrapper


def professor_required(view_func):
    @wraps(view_func)
    @jwt_required
    def wrapper(*args, **kwargs):
        role = normalize_role(g.current_user.get("role") or g.current_user.get("tipo"))
        if role != "professor":
            return jsonify({"erro": "Acesso permitido apenas para professores"}), 403

        # Este decorador centraliza a regra das rotas exclusivas do professor.
        return view_func(*args, **kwargs)

    return wrapper
