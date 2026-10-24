"""Legacy workflow tests act like forms. Security tests use the unmodified client."""
from flask.testing import FlaskClient


class FormClient(FlaskClient):
    def post(self, *args, **kwargs):
        data = kwargs.get("data") or {}
        # Existing explicit CSRF tests intentionally omit the token on these routes.
        path = args[0] if args else ""
        protected_explicitly = path.startswith("/super/") or path == "/admin/comunicados"
        if path != "/login" and not protected_explicitly:
            with self.session_transaction() as sess:
                if sess.get("user_id"):
                    headers = dict(kwargs.pop("headers", {}))
                    headers.setdefault("X-CSRF-Token", sess["csrf_token"])
                    kwargs["headers"] = headers
        return super().post(*args, **kwargs)
