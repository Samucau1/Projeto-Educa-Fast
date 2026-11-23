"""Integração com SQLite em memória; não acessa o banco da instalação."""
import os
import unittest

from ambiente_teste import configurar_banco_testes
from csrf_client import FormClient
configurar_banco_testes()

from app import create_app
from app.auth import generate_token
from app.database import Base, engine, get_session
from app.models import UsuarioModel
from werkzeug.security import generate_password_hash
from fixtures import exigir_banco_em_memoria


class GestaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.test_client_class = FormClient
        cls.app.config.update(TESTING=True, SECRET_KEY="test-secret")

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.client = self.app.test_client()
        self.ids = {}
        with get_session() as db:
            for role in ("superadmin", "admin", "professor", "aluno"):
                user = UsuarioModel(email=f"{role}@teste.com", senha=generate_password_hash("senha1234"), tipo=role)
                db.add(user)
                db.flush()
                self.ids[role] = user.id
            db.commit()

    def login(self, role):
        response = self.client.post("/login", json={"email": f"{role}@teste.com", "senha": "senha1234"})
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as sess:
            return sess["csrf_token"]

    def test_broadcast_and_read_permissions(self):
        for role in ("admin", "superadmin"):
            token = self.login(role)
            response = self.client.post("/admin/comunicados", data={"titulo": role, "mensagem": "Mensagem para todos <script>alert(1)</script>", "csrf_token": token})
            self.assertEqual(response.status_code, 302)
        for role in ("aluno", "professor", "admin", "superadmin"):
            self.login(role)
            page = self.client.get("/mensagens")
            self.assertEqual(page.status_code, 200)
            self.assertIn(b"Mensagem para todos", page.data)
            self.assertIn(b"&lt;script&gt;", page.data)
        for role in ("aluno", "professor"):
            token = self.login(role)
            self.assertEqual(self.client.post("/admin/comunicados", data={"titulo": "X", "mensagem": "X", "csrf_token": token}).status_code, 403)
            self.assertEqual(self.client.get("/super/usuarios").status_code, 403)

    def test_super_creates_admin_and_changes_role_immediately(self):
        token = self.login("superadmin")
        self.assertEqual(self.client.post("/super/usuarios", data={"nome": "Novo", "email": "novo@teste.com", "senha": "senha1234", "tipo": "admin", "csrf_token": token}).status_code, 302)
        admin_client = self.app.test_client()
        admin_client.post("/login", json={"email": "admin@teste.com", "senha": "senha1234"})
        response = self.client.post(f"/super/usuarios/{self.ids['admin']}/perfil", data={"tipo": "aluno", "nome": "Aluno", "matricula": "2026-1", "csrf_token": token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(admin_client.get("/admin/dashboard").status_code, 403)
        self.assertEqual(admin_client.get("/aluno").status_code, 200)

    def test_registration_and_privilege_escalation_blocked(self):
        self.assertEqual(self.client.post("/cadastro", json={"tipo": "admin"}).status_code, 403)
        self.login("admin")
        self.assertEqual(self.client.post("/cadastro", json={"tipo": "admin"}).status_code, 403)
        token = self.login("superadmin")
        self.assertEqual(self.client.post("/super/usuarios", data={"tipo": "superadmin", "csrf_token": token}).status_code, 200)
        with get_session() as db:
            self.assertEqual(db.query(UsuarioModel).filter_by(tipo="superadmin").count(), 1)
        self.assertEqual(self.client.post(f"/super/usuarios/{self.ids['superadmin']}/perfil", data={"tipo": "aluno", "csrf_token": token}).status_code, 403)

    def test_layout_persistence_validation_and_csrf(self):
        token = self.login("superadmin")
        self.assertEqual(self.client.post("/super/layout", data={"cor_fundo": "#123456", "cor_destaque": "#abcdef"}).status_code, 400)
        self.assertEqual(self.client.post("/super/layout", data={"cor_fundo": "#123456", "cor_destaque": "#abcdef", "csrf_token": token}).status_code, 302)
        self.login("aluno")
        self.assertIn(b"#123456", self.client.get("/mensagens").data)
        self.assertEqual(self.client.get("/super/layout").status_code, 403)
        token = self.login("superadmin")
        self.client.post("/super/layout", data={"cor_fundo": "red;}", "cor_destaque": "#abcdef", "csrf_token": token})
        self.assertIn(b"#123456", self.client.get("/mensagens").data)

    def test_old_jwt_uses_current_role(self):
        with self.app.app_context(), get_session() as db:
            user = db.get(UsuarioModel, self.ids["professor"])
            token = generate_token(user)
            user.tipo = "aluno"
            db.commit()
        self.assertEqual(self.client.get("/professor/teste", headers={"Authorization": f"Bearer {token}"}).status_code, 403)

    def test_bootstrap_command(self):
        result = self.app.test_cli_runner().invoke(args=["criar-superusuario", "--email", "super@teste.com", "--senha", "segredo123"])
        self.assertEqual(result.exit_code, 0, result.output)
        result = self.app.test_cli_runner().invoke(args=["criar-superusuario", "--email", "super@teste.com", "--senha", "segredo123"])
        self.assertNotEqual(result.exit_code, 0)

    def test_pages_and_broadcast_validation(self):
        token = self.login("superadmin")
        for path in ("/super/usuarios", "/super/layout", "/admin/dashboard", "/admin/comunicados", "/mensagens"):
            self.assertEqual(self.client.get(path).status_code, 200, path)
        for data in ({"titulo": "", "mensagem": "vazia"}, {"titulo": "x" * 151, "mensagem": "longa"}):
            data["csrf_token"] = token
            response = self.client.post("/admin/comunicados", data=data)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"obrigatorios" if not data["titulo"] else b"150", response.data)
        self.assertEqual(self.client.post("/admin/comunicados", data={"titulo": "X", "mensagem": "X"}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
