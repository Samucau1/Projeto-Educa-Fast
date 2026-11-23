"""Shared browser and storage boundaries."""
import os
import secrets
import hashlib
import hmac
import time
from contextlib import contextmanager
from urllib.parse import unquote, urlsplit

from flask import abort, current_app, request, session
from app.crypto import cipher, FILE_PREFIX
from io import BytesIO
from werkzeug.exceptions import HTTPException


class StorageFull(HTTPException):
    code = 507
    description = "Armazenamento cheio. Contate a administracao."


def local_return_path(value):
    if not value:
        return None
    decoded = unquote(value)
    if any(ord(c) < 32 or ord(c) == 127 for c in decoded) or "\\" in decoded:
        abort(400, "Destino de retorno invalido.")
    try:
        parsed = urlsplit(decoded)
    except ValueError:
        abort(400, "Destino de retorno invalido.")
    if not decoded.startswith("/") or decoded.startswith("//") or parsed.scheme or parsed.netloc:
        abort(400, "Destino de retorno invalido.")
    return value


@contextmanager
def storage_lock(folder):
    """OS lock shared by workers on the same upload filesystem."""
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, ".storage.lock"), "a+b") as lock:
        if os.name == "nt":
            import msvcrt
            lock.seek(0)
            lock.write(b"0")
            lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def save_upload(file, path):
    folder = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    limit = current_app.config["MAX_UPLOAD_BYTES"]
    quota = current_app.config["UPLOAD_QUOTA_BYTES"]
    with storage_lock(folder):
        used = 0
        for root, _, names in os.walk(folder):
            for name in names:
                if name == ".storage.lock":
                    continue
                try:
                    used += os.path.getsize(os.path.join(root, name))
                except FileNotFoundError:
                    # Replacing a profile photo may remove an old file concurrently.
                    # A deletion only reduces usage; other errors must still propagate.
                    continue
        written = 0
        try:
            content = BytesIO()
            while True:
                chunk = file.stream.read(64 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > limit:
                    abort(413, "Arquivo excede o limite permitido.")
                content.write(chunk)
            encrypted = FILE_PREFIX + cipher().encrypt(content.getvalue())
            if used + len(encrypted) > quota:
                raise StorageFull()
            with open(path, "xb") as destination:
                destination.write(encrypted)
        except Exception:
            if os.path.isfile(path):
                os.remove(path)
            raise


def download_upload(folder, filename, attachment=True):
    from flask import send_file
    from werkzeug.utils import safe_join
    import mimetypes
    path = safe_join(folder, filename)
    if not path or not os.path.isfile(path):
        abort(404)
    with open(path, "rb") as source:
        data = source.read()
    if data.startswith(FILE_PREFIX):
        data = cipher().decrypt(data[len(FILE_PREFIX):])
    return send_file(BytesIO(data), download_name=filename, as_attachment=attachment,
                     mimetype=mimetypes.guess_type(filename)[0] or "application/octet-stream")


def init_security(app):
    @app.cli.command("criptografar-arquivos")
    def encrypt_legacy_uploads():
        """Encrypt existing uploads after an operator backup. Never changes the key."""
        folder = os.path.abspath(app.config["UPLOAD_FOLDER"])
        count = 0
        with storage_lock(folder):
            for root, _, names in os.walk(folder):
                for name in names:
                    if name == ".storage.lock":
                        continue
                    path = os.path.join(root, name)
                    with open(path, "rb") as source:
                        data = source.read()
                    if data.startswith(FILE_PREFIX):
                        continue
                    encrypted = FILE_PREFIX + cipher().encrypt(data)
                    staging = path + ".encrypting"
                    with open(staging, "xb") as destination:
                        destination.write(encrypted)
                    os.replace(staging, path)
                    count += 1
        import click
        click.echo(f"Arquivos criptografados: {count}")
    @app.before_request
    def browser_mutations():
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return
        if request.endpoint == "auth.login":
            # Login only accepts JSON; cross-origin JSON requires CORS, which is not enabled.
            origin = request.headers.get("Origin")
            if origin and origin != request.host_url.rstrip("/"):
                abort(403)
            enforce_login_limit()
            return
        if session.get("user_id"):
            token = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token", "")
            if not secrets.compare_digest(token, session.get("csrf_token", "")):
                abort(400, "Formulario expirado. Recarregue a pagina.")

    @app.after_request
    def privacy_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response


def enforce_login_limit():
    """Shared SQL counters; retain no raw IP and expire old windows."""
    from app.database import get_session
    from app.models import LimiteLoginModel
    from sqlalchemy.exc import IntegrityError
    window = int(time.time()) // 900
    identity = f"{request.remote_addr}:{window}".encode("utf-8")
    key = hmac.new(current_app.secret_key.encode("utf-8"), identity, hashlib.sha256).hexdigest()
    for attempt in range(2):
        with get_session() as db:
            db.query(LimiteLoginModel).filter(LimiteLoginModel.janela < window - 1).delete()
            existing = db.get(LimiteLoginModel, key)
            if existing:
                updated = db.query(LimiteLoginModel).filter(
                    LimiteLoginModel.chave == key,
                    LimiteLoginModel.tentativas < current_app.config["LOGIN_ATTEMPTS_PER_WINDOW"]
                ).update({"tentativas": LimiteLoginModel.tentativas + 1}, synchronize_session=False)
                db.commit()
                if not updated:
                    abort(429, "Muitas tentativas. Aguarde ate 15 minutos.")
                return
            db.add(LimiteLoginModel(chave=key, janela=window, tentativas=1))
            try:
                db.commit()
                return
            except IntegrityError:
                db.rollback()
    abort(429)
