"""Authenticated encryption. Keys belong in operator-managed secret storage."""
import hashlib
import hmac
from datetime import date
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, String, Text
from config import Config

PREFIX = "enc:v1:"
FILE_PREFIX = b"EDUCAFAST-ENC-1\n"


def cipher():
    return Fernet(Config.DATA_ENCRYPTION_KEY.encode("ascii"))


def encrypt(value):
    return PREFIX + cipher().encrypt(str(value).encode("utf-8")).decode("ascii")


def decrypt(value):
    if value is None:
        return None
    if not value.startswith(PREFIX):
        # Compatibility only until the controlled legacy migration runs.
        return value
    return cipher().decrypt(value[len(PREFIX):].encode("ascii")).decode("utf-8")


def cpf_index(value):
    if not value:
        return None
    normalized = "".join(c for c in value if c.isdigit())
    key = hashlib.sha256(Config.DATA_ENCRYPTION_KEY.encode("ascii") + b"cpf-index-v1").digest()
    return hmac.new(key, normalized.encode("utf-8"), hashlib.sha256).hexdigest()


class EncryptedText(TypeDecorator):
    impl = String(512)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return encrypt(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return decrypt(value)


class EncryptedDate(EncryptedText):
    cache_ok = True

    def process_result_value(self, value, dialect):
        decoded = decrypt(value)
        return date.fromisoformat(decoded) if decoded else None


class EncryptedLongText(EncryptedText):
    impl = Text
    cache_ok = True
