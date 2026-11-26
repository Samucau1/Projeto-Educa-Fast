"""Várias escolas no mesmo Postgres: isolamento, ADM Supremo e diretório de logins.

Roda somente no Postgres descartável de testes (EDUCAFAST_TEST_DB=1); SQLite não tem schemas.
"""
import os
import tempfile
import unittest

from ambiente_teste import ClienteSPA, banco_real_de_testes, configurar_banco_testes, tela, texto_tela
configurar_banco_testes()
from sqlalchemy import text
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from app import create_app, escolas
from app.database import Base, engine, get_session
from app.models import ComunicadoModel, UsuarioModel
from fixtures import SENHA, criar_usuarios, exigir_banco_em_memoria

OPERADOR = "supremo@teste.local"
SENHA_ESCOLAS = "Senha-escola-2026!"


@unittest.skipUnless(banco_real_de_testes(), "Várias escolas exigem o Postgres de testes")
class MultiEscolaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.test_client_class = ClienteSPA

    def setUp(self):
        exigir_banco_em_memoria()  # nunca apaga schemas fora do banco descartável
        with engine.begin() as conn:
            for (schema,) in conn.execute(text("SELECT nspname FROM pg_namespace WHERE nspname LIKE 'escola\\_%'")):
                conn.execute(text(f'DROP SCHEMA "{escolas.validar_schema(schema)}" CASCADE'))
            conn.execute(text("DELETE FROM plataforma.contas"))
            conn.execute(text("DELETE FROM plataforma.escolas WHERE schema_nome <> 'public'"))
            conn.execute(text("DELETE FROM plataforma.operadores"))
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.ids = criar_usuarios()  # escola padrão (public)
        with Session(engine) as db:
            db.add(escolas.OperadorModel(email=OPERADOR, nome="Dono da plataforma", senha=generate_password_hash(SENHA)))
            db.commit()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app.config["UPLOAD_FOLDER"] = self.temp.name

    def entrar(self, email, senha=SENHA):
        client = self.app.test_client()
        resposta = client.post("/login", json={"email": email, "senha": senha})
        return client, resposta

    def token(self, client):
        with client.session_transaction() as sess:
            return sess["csrf_token"]

    def criar_escola(self, client, nome, slug, email):
        return client.post("/supremo/escolas", data={"nome": nome, "slug": slug, "admin_email": email,
                                                     "admin_senha": SENHA_ESCOLAS, "csrf_token": self.token(client)})

    def supremo_com_duas_escolas(self):
        supremo, resposta = self.entrar(OPERADOR)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.criar_escola(supremo, "Colégio Alfa", "alfa", "direcao@alfa.local").status_code, 302)
        self.assertEqual(self.criar_escola(supremo, "Colégio Beta", "beta", "direcao@beta.local").status_code, 302)
        return supremo

    def test_supremo_entra_e_ve_o_painel(self):
        supremo, resposta = self.entrar(OPERADOR)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["tipo"], "SUPREMO")
        painel = supremo.get("/supremo")
        self.assertEqual(painel.status_code, 200)
        dados = tela(painel)["dados"]
        self.assertEqual([e["slug"] for e in dados["escolas"]], ["padrao"])
        self.assertEqual(dados["escolas"][0]["usuarios"], 5)

    def test_perfis_de_escola_nao_acessam_o_painel_supremo(self):
        for role in ("superadmin", "admin", "professor", "aluno"):
            client, resposta = self.entrar(f"{role}@teste.local")
            self.assertEqual(resposta.status_code, 200)
            self.assertIn(client.get("/supremo").status_code, (302, 403))
            self.assertEqual(client.post("/supremo/escolas", data={"nome": "X", "slug": "xxx",
                "admin_email": "x@x.local", "admin_senha": SENHA_ESCOLAS, "csrf_token": self.token(client)}).status_code, 403)
        anonimo = self.app.test_client()
        self.assertEqual(anonimo.get("/supremo").status_code, 302)

    def test_supremo_cria_escola_com_schema_proprio_e_superadmin(self):
        supremo = self.supremo_com_duas_escolas()
        with engine.connect() as conn:
            schemas = set(conn.execute(text("SELECT nspname FROM pg_namespace WHERE nspname LIKE 'escola\\_%'")).scalars())
        self.assertEqual(schemas, {"escola_alfa", "escola_beta"})
        dados = tela(supremo.get("/supremo"))["dados"]
        alfa = next(e for e in dados["escolas"] if e["slug"] == "alfa")
        self.assertEqual(alfa["superadmins"], ["direcao@alfa.local"])
        self.assertEqual((alfa["usuarios"], alfa["alunos"]), (1, 0))
        client, resposta = self.entrar("direcao@alfa.local", SENHA_ESCOLAS)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.json["tipo"], "SUPERADMIN")
        with client.session_transaction() as sess:
            self.assertEqual(sess["escola_schema"], "escola_alfa")
        # O nome da escola nova aparece nas telas dela.
        self.assertEqual(tela(client.get("/super/usuarios"))["global"]["escola"]["nome"], "Colégio Alfa")

    def test_uma_escola_nao_enxerga_os_dados_da_outra(self):
        self.supremo_com_duas_escolas()
        alfa, _ = self.entrar("direcao@alfa.local", SENHA_ESCOLAS)
        criado = alfa.post("/super/usuarios", data={"nome": "Prof Alfa", "email": "prof@alfa.local", "senha": "senha1234",
                                                    "tipo": "admin", "csrf_token": self.token(alfa)})
        self.assertEqual(criado.status_code, 302)
        alfa.post("/admin/comunicados", data={"titulo": "Recado só da Alfa", "mensagem": "Segredo da Alfa",
                                              "csrf_token": self.token(alfa)})
        beta, _ = self.entrar("direcao@beta.local", SENHA_ESCOLAS)
        usuarios_beta = texto_tela(beta.get("/super/usuarios"))
        self.assertIn("direcao@beta.local", usuarios_beta)
        for vazamento in ("prof@alfa.local", "direcao@alfa.local", "superadmin@teste.local"):
            self.assertNotIn(vazamento, usuarios_beta)
        self.assertNotIn("Segredo da Alfa", texto_tela(beta.get("/mensagens")))
        self.assertIn("Segredo da Alfa", texto_tela(alfa.get("/mensagens")))
        padrao, _ = self.entrar("superadmin@teste.local")
        self.assertNotIn("prof@alfa.local", texto_tela(padrao.get("/super/usuarios")))
        # O novo usuário da Alfa entra direto na escola dele.
        prof, resposta = self.entrar("prof@alfa.local", "senha1234")
        self.assertEqual(resposta.status_code, 200)
        with prof.session_transaction() as sess:
            self.assertEqual(sess["escola_schema"], "escola_alfa")

    def test_email_e_unico_em_toda_a_plataforma(self):
        supremo = self.supremo_com_duas_escolas()
        beta, _ = self.entrar("direcao@beta.local", SENHA_ESCOLAS)
        repetido = beta.post("/super/usuarios", data={"nome": "Copia", "email": "direcao@alfa.local", "senha": "senha1234",
                                                      "tipo": "admin", "csrf_token": self.token(beta)})
        self.assertNotEqual(repetido.status_code, 302)
        with get_session("escola_beta") as db:
            self.assertEqual(db.query(UsuarioModel).filter_by(email="direcao@alfa.local").count(), 0)
        # Também não dá para abrir escola nova com um e-mail já usado.
        self.criar_escola(supremo, "Gama", "gama", "admin@teste.local")
        with engine.connect() as conn:
            self.assertIsNone(conn.execute(text("SELECT to_regnamespace('escola_gama')")).scalar())
            self.assertIsNone(conn.execute(text("SELECT id FROM plataforma.escolas WHERE slug = 'gama'")).scalar())

    def test_codigo_da_escola_invalido_ou_repetido_e_recusado(self):
        supremo = self.supremo_com_duas_escolas()
        for slug in ("alfa", "padrao", "A", "com espaço", "x" * 50, "'; drop schema public; --"):
            self.criar_escola(supremo, "Outra", slug, f"novo{len(slug)}@x.local")
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT count(*) FROM plataforma.escolas")).scalar(), 3)

    def test_escola_desativada_perde_o_acesso_sem_perder_dados(self):
        supremo = self.supremo_com_duas_escolas()
        alfa, _ = self.entrar("direcao@alfa.local", SENHA_ESCOLAS)
        self.assertEqual(alfa.get("/super/usuarios").status_code, 200)
        escola_id = next(e["id"] for e in tela(supremo.get("/supremo"))["dados"]["escolas"] if e["slug"] == "alfa")
        supremo.post(f"/supremo/escolas/{escola_id}/situacao", data={"ativa": "0", "csrf_token": self.token(supremo)})
        self.assertNotEqual(alfa.get("/super/usuarios").status_code, 200)
        self.assertEqual(self.entrar("direcao@alfa.local", SENHA_ESCOLAS)[1].status_code, 401)
        with get_session("escola_alfa") as db:
            self.assertEqual(db.query(UsuarioModel).count(), 1)
        supremo.post(f"/supremo/escolas/{escola_id}/situacao", data={"ativa": "1", "csrf_token": self.token(supremo)})
        self.assertEqual(self.entrar("direcao@alfa.local", SENHA_ESCOLAS)[1].status_code, 200)

    def test_token_jwt_fica_preso_a_escola(self):
        self.supremo_com_duas_escolas()
        _, resposta = self.entrar("direcao@alfa.local", SENHA_ESCOLAS)
        import base64, json
        corpo = resposta.json["token"].split(".")[1]
        payload = json.loads(base64.urlsafe_b64decode(corpo + "=" * (-len(corpo) % 4)))
        self.assertEqual(payload["esc"], "escola_alfa")

    def test_token_de_escola_desativada_deixa_de_valer(self):
        supremo = self.supremo_com_duas_escolas()
        _, resposta = self.entrar("direcao@alfa.local", SENHA_ESCOLAS)
        token = resposta.json["token"]
        with self.app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
            from app.auth import decode_token_from_request
            payload, erro = decode_token_from_request()
            self.assertIsNone(erro)
        escola_id = next(e["id"] for e in tela(supremo.get("/supremo"))["dados"]["escolas"] if e["slug"] == "alfa")
        supremo.post(f"/supremo/escolas/{escola_id}/situacao", data={"ativa": "0", "csrf_token": self.token(supremo)})
        with self.app.test_request_context(headers={"Authorization": f"Bearer {token}"}):
            from app.auth import decode_token_from_request
            payload, erro = decode_token_from_request()
            self.assertIsNone(payload)
            self.assertEqual(erro[1], 401)

    def test_arquivos_de_cada_escola_ficam_em_pastas_separadas(self):
        self.supremo_com_duas_escolas()
        with self.app.test_request_context():
            from flask import session
            session["escola_schema"] = "escola_alfa"
            pasta = escolas.pasta_uploads(self.temp.name)
        self.assertEqual(pasta, os.path.join(self.temp.name, "escolas", "escola_alfa"))
        with self.app.test_request_context():
            self.assertEqual(escolas.pasta_uploads(self.temp.name), os.path.abspath(self.temp.name))


if __name__ == "__main__":
    unittest.main()
