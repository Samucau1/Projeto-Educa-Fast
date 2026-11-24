"""Ponte com a aplicação React (render_page): formato, minimização de dados e erros."""
import unittest

from ambiente_teste import configurar_banco_testes, tela
configurar_banco_testes()

from app import create_app
from app.database import Base, engine, get_session
from app.models import ProfessorModel, UsuarioModel
from fixtures import exigir_banco_em_memoria
from werkzeug.security import generate_password_hash


class SpaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.config.update(TESTING=True, SECRET_KEY="test-secret")

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.client = self.app.test_client()
        with get_session() as db:
            for role in ("superadmin", "admin", "professor"):
                db.add(UsuarioModel(email=f"{role}@teste.com", senha=generate_password_hash("senha1234"), tipo=role))
            db.flush()
            prof = db.query(UsuarioModel).filter_by(email="professor@teste.com").one()
            db.add(ProfessorModel(usuario_id=prof.id, nome="Prof. Sigilo", cpf="12345678909", telefone="61999990000"))
            db.commit()

    def login(self, role):
        self.assertEqual(self.client.post("/login", json={"email": f"{role}@teste.com", "senha": "senha1234"}).status_code, 200)
        with self.client.session_transaction() as sess:
            return sess["csrf_token"]

    def test_formato_da_tela(self):
        resposta = self.client.get("/")
        self.assertEqual(resposta.headers["X-EducaFast-Pagina"], "1")
        dados = tela(resposta)
        self.assertEqual(dados["pagina"], "login")
        self.assertEqual(set(dados), {"pagina", "dados", "global", "mensagens", "form", "args"})
        self.assertIn("csrf_token", dados["global"])

    def test_objetos_orm_nao_levam_dados_pessoais(self):
        self.login("admin")
        texto = self.client.get("/cursos").get_data(as_text=True)
        self.assertIn("Prof. Sigilo", texto)
        for valor in ("12345678909", "61999990000", "cpf_hash", "senha"):
            self.assertNotIn(valor, texto)

    def test_painel_recebe_somente_o_que_exibe(self):
        self.login("admin")
        dados = tela(self.client.get("/admin/dashboard"))["dados"]
        self.assertNotIn("professores", dados)
        self.assertNotIn("alunos", dados)
        self.assertIn("registros_recentes", dados)

    def test_erro_de_formulario_nao_devolve_senha(self):
        token = self.login("superadmin")
        resposta = self.client.post("/super/usuarios", data={"csrf_token": token, "tipo": "admin", "nome": "X",
                                                              "email": "admin@teste.com", "senha": "segredo-123"})
        self.assertEqual(resposta.status_code, 200)
        form = tela(resposta)["form"]
        self.assertEqual(form.get("email"), "admin@teste.com")
        self.assertNotIn("senha", form)
        self.assertNotIn("csrf_token", form)

    def test_upload_grande_demais_vira_tela_de_erro(self):
        token = self.login("admin")
        limite = self.app.config["MAX_CONTENT_LENGTH"]
        self.app.config["MAX_CONTENT_LENGTH"] = 64
        try:
            resposta = self.client.post("/arquivos/upload", data={"csrf_token": token, "titulo": "x" * 200})
        finally:
            self.app.config["MAX_CONTENT_LENGTH"] = limite
        self.assertEqual(resposta.status_code, 413)
        dados = tela(resposta)
        self.assertEqual(dados["pagina"], "erro")
        self.assertEqual(dados["dados"]["codigo"], 413)

    def test_acesso_direto_sem_build_mantem_status(self):
        cliente = self.app.test_client()
        cliente.environ_base.pop("HTTP_X_EDUCAFAST_SPA", None)
        self.assertEqual(cliente.get("/pagina-inexistente").status_code, 404)
        self.assertEqual(cliente.get("/").status_code, 200)


if __name__ == "__main__":
    unittest.main()
