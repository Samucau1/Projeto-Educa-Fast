import os
import ssl

bind = "0.0.0.0:5000"
workers = 2
preload_app = True
timeout = 60
limit_request_line = 4094
certfile = os.environ.get("TLS_CERT_FILE")
keyfile = os.environ.get("TLS_KEY_FILE")
# Do not log URLs containing potentially personal search terms.
accesslog = None

if os.environ.get("APP_ENV") == "production" and not (certfile and keyfile):
    raise RuntimeError("Producao exige TLS_CERT_FILE e TLS_KEY_FILE.")


def ssl_context(conf, default_ssl_context_factory):
    context = default_ssl_context_factory()
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def post_fork(server, worker):
    # A forked worker must create its own DB connections after master initialization.
    from app.database import engine
    engine.dispose(close=False)
