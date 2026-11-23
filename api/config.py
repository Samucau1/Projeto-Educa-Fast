import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATA_ENCRYPTION_KEY = os.getenv("DATA_ENCRYPTION_KEY", "")
    APP_ENV = os.getenv("APP_ENV", "development")
    DB_SSL_CA = os.getenv("DB_SSL_CA", "")
    TRUSTED_HOSTS = [h.strip() for h in os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024
    MAX_UPLOAD_BYTES = 10 * 1024 * 1024
    UPLOAD_QUOTA_BYTES = 512 * 1024 * 1024
    LOGIN_ATTEMPTS_PER_WINDOW = 120
    LGPD_CONTROLADOR = os.getenv("LGPD_CONTROLADOR", "EducaFast")
    LGPD_CONTATO = os.getenv("LGPD_CONTATO", "")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "8"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "app_web")
    DB_URL = os.getenv("DB_URL")

    SQLALCHEMY_DATABASE_URI = DB_URL or (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
