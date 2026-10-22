import io
import json
import os
import tempfile
import unittest

from ambiente_teste import configurar_banco_testes
configurar_banco_testes()

from app import create_app
from app.database import Base, engine, get_session
from app.models import DisciplinaModel, TurmaModel, AtividadeModel, NotaModel, ComunicadoModel, UsuarioModel, SolicitacaoDocumentoModel
from fixtures import criar_usuarios, exigir_banco_em_memoria, SENHA


class RegressaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exigir_banco_em_memoria()
        cls.app = create_app()
        cls.app.config.update(TESTING=True, SECRET_KEY="regressao-local")

    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.uploads = tempfile.TemporaryDirectory()
        self.addCleanup(self.uploads.cleanup)
        self.app.config["UPLOAD_FOLDER"] = self.uploads.name
        self.ids = criar_usuarios()
        self.client = self.app.test_client()

    def login(self, role, client=None):
        client = client or self.client
        response = client.post("/login", json={"email": f"{role}@teste.local", "senha": SENHA})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def csrf(self):
        with self.client.session_transaction() as session:
            return session["csrf_token"]

    def preparar_turma(self):
        self.login("admin")
        self.assertEqual(self.client.post("/admin/disciplinas", data={"nome": "Matemática", "codigo": "MAT", "carga_horaria": "60"}).status_code, 302)
        self.assertEqual(self.client.post("/admin/turmas", data={"nome": "Turma Teste", "codigo": "T1", "ano_letivo": "2026"}).status_code, 302)
        with get_session() as db:
            self.disciplina_id = db.query(DisciplinaModel).filter_by(codigo="MAT").one().id
            self.turma_id = db.query(TurmaModel).filter_by(codigo="T1").one().id
        self.assertEqual(self.client.post("/admin/disciplinas", data={"action": "associate_teacher", "professor_id": self.ids["professor_id"], "disciplina_id": self.disciplina_id}).status_code, 302)
        self.assertEqual(self.client.post("/admin/turmas", data={"action": "associate_teacher", "professor_id": self.ids["professor_id"], "turma_id": self.turma_id}).status_code, 302)
        self.assertEqual(self.client.post("/admin/turmas", data={"action": "associate_student", "aluno_id": self.ids["aluno_id"], "turma_id": self.turma_id}).status_code, 302)

    def test_login_logout_and_invalid_credentials(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.post("/login", json={}).status_code, 400)
        self.assertEqual(self.client.post("/login", json={"email": "admin@teste.local", "senha": "errada"}).status_code, 401)
        self.assertEqual(self.client.post("/login", json={"email": "inexistente@teste.local", "senha": SENHA}).status_code, 404)
        for role, path in (("admin", "/admin/dashboard"), ("professor", "/professor"), ("aluno", "/aluno")):
            self.login(role)
            self.assertEqual(self.client.get(path).status_code, 200)
            self.assertEqual(self.client.get("/").status_code, 302)
            self.client.get("/logout")
            self.assertEqual(self.client.get(path).status_code, 403)

    def test_login_rejects_non_object_json(self):
        for value in ([1], "texto", 123, None):
            with self.subTest(value=value):
                response = self.client.post("/login", data=json.dumps(value), content_type="application/json")
                self.assertEqual(response.status_code, 400)
        for data in ({"email": ["admin@teste.local"], "senha": SENHA}, {"email": "admin@teste.local", "senha": 123}):
            self.assertEqual(self.client.post("/login", json=data).status_code, 400)

    def test_registration_validation_duplicates_and_panels(self):
        self.login("admin")
        for tipo, extra in (("aluno", {"matricula": "NOVA"}), ("professor", {"cpf": "00000000002"})):
            data = {"nome": "Novo cadastro", "email": f"novo-{tipo}@teste.local", "senha": SENHA, **extra}
            response = self.client.post(f"/cadastro/{tipo}", json=data)
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.get_json()["role"], tipo)
            self.assertEqual(self.client.post(f"/cadastro/{tipo}", json=data).status_code, 409)
            client = self.app.test_client()
            self.assertEqual(client.post("/login", json={"email": data["email"], "senha": SENHA}).status_code, 200)
            self.assertEqual(client.get(f"/{tipo}").status_code, 200)
        self.assertEqual(self.client.post("/cadastro/aluno", json={"nome": "Sem matrícula", "email": "sem@teste.local", "senha": SENHA}).status_code, 400)
        with get_session() as db:
            self.assertIsNone(db.query(UsuarioModel).filter_by(email="sem@teste.local").first())

    def test_academic_flow_and_student_isolation(self):
        self.preparar_turma()
        self.login("professor")
        data = {"turma_id": self.turma_id, "disciplina_id": self.disciplina_id}
        self.assertEqual(self.client.post("/professor/atividades/lancar", data={**data, "titulo": "Atividade de regressão", "descricao": "Exercícios"}).status_code, 302)
        nota = {**data, "aluno_id": self.ids["aluno_id"], "nota": "8,5"}
        self.assertEqual(self.client.post("/professor/notas/salvar", data=nota).status_code, 302)
        self.assertEqual(self.client.post("/professor/notas/salvar", data={**nota, "nota": "9"}).status_code, 302)
        with get_session() as db:
            self.assertEqual(db.query(AtividadeModel).count(), 1)
            self.assertEqual(db.query(NotaModel).count(), 1)
            self.assertEqual(float(db.query(NotaModel).one().nota), 9)
        self.assertEqual(self.client.post("/professor/notas/salvar", data={**nota, "aluno_id": self.ids["outro_aluno_id"]}).status_code, 403)
        self.assertEqual(self.client.post("/professor/atividades/lancar", data={**data, "turma_id": 999, "titulo": "Sem vínculo"}).status_code, 403)
        self.login("aluno")
        page = self.client.get(f"/aluno/disciplinas/{self.disciplina_id}")
        self.assertEqual(page.status_code, 200)
        self.assertIn("Atividade de regressão".encode(), page.data)
        self.login("outro_aluno")
        self.assertEqual(self.client.get(f"/aluno/disciplinas/{self.disciplina_id}").status_code, 404)

    def test_grade_boundaries_and_nonfinite_values(self):
        self.preparar_turma()
        self.login("professor")
        data = {"turma_id": self.turma_id, "disciplina_id": self.disciplina_id, "aluno_id": self.ids["aluno_id"]}
        for nota in ("-1", "11", "abc", "NaN", "sNaN", "Infinity", "-Infinity"):
            with self.subTest(nota=nota):
                self.assertEqual(self.client.post("/professor/notas/salvar", data={**data, "nota": nota}).status_code, 400)
        for nota in ("0", "10"):
            self.assertEqual(self.client.post("/professor/notas/salvar", data={**data, "nota": nota}).status_code, 302)

    def test_document_upload_download_and_other_student_denied(self):
        for role in ("admin", "superadmin"):
            self.login(role)
            self.assertEqual(self.client.post("/arquivos/upload").status_code, 400)
            response = self.client.post("/arquivos/upload", data={"aluno_id": self.ids["aluno_id"], "arquivo": (io.BytesIO(b"Documento sintetico"), "regressao.txt")})
            self.assertEqual(response.status_code, 201)
            filename = response.get_json()["documento"]["arquivo"]
            self.login("aluno")
            download = self.client.get(f"/arquivos/download/{filename}")
            self.assertEqual(download.status_code, 200)
            self.assertEqual(download.data, b"Documento sintetico")
            download.close()
            self.login("outro_aluno")
            self.assertEqual(self.client.get(f"/arquivos/download/{filename}").status_code, 404)

    def test_requested_document_end_to_end(self):
        self.login("admin")
        aluno_id = self.ids["aluno_id"]
        self.assertEqual(self.client.post(f"/admin/alunos/{aluno_id}/documentos/solicitar", data={"titulo": "Comprovante", "mensagem": "Enviar comprovante"}).status_code, 302)
        with get_session() as db:
            solicitacao_id = db.query(SolicitacaoDocumentoModel).one().id
        self.login("outro_aluno")
        self.assertEqual(self.client.post("/aluno/documentos/upload", data={"solicitacao_id": solicitacao_id}).status_code, 404)
        self.login("aluno")
        self.assertEqual(self.client.post("/aluno/documentos/upload", data={"solicitacao_id": solicitacao_id, "arquivo": (io.BytesIO(b"Comprovante teste"), "comprovante.txt")}).status_code, 302)
        with get_session() as db:
            self.assertEqual(db.get(SolicitacaoDocumentoModel, solicitacao_id).status, "enviado")

    def test_revoked_teacher_jwt_cannot_upload(self):
        token = self.login("professor")["token"]
        with get_session() as db:
            db.get(UsuarioModel, self.ids["professor"]).tipo = "aluno"
            db.commit()
        response = self.client.post("/arquivos/upload", headers={"Authorization": f"Bearer {token}"}, data={"aluno_id": self.ids["aluno_id"], "arquivo": (io.BytesIO(b"Revogado"), "revogado.txt")})
        self.assertEqual(response.status_code, 403)

    def test_jwt_download_obeys_same_ownership_as_session(self):
        self.login("admin")
        response = self.client.post("/arquivos/upload", data={"aluno_id": self.ids["aluno_id"], "arquivo": (io.BytesIO(b"Privado"), "privado.txt")})
        self.assertEqual(response.status_code, 201)
        filename = response.get_json()["documento"]["arquivo"]
        own_token = self.login("aluno")["token"]
        other_token = self.login("outro_aluno")["token"]
        no_session = self.app.test_client()
        download = no_session.get(f"/arquivos/download/{filename}", headers={"Authorization": f"Bearer {own_token}"})
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, b"Privado")
        download.close()
        download = no_session.get(f"/arquivos/download/{filename}", headers={"Authorization": f"Bearer {other_token}"})
        try:
            self.assertEqual(download.status_code, 404)
        finally:
            download.close()

    def test_broadcast_survives_logout_and_invalid_payload_not_saved(self):
        self.login("admin")
        token = self.csrf()
        self.client.post("/admin/comunicados", data={"titulo": "Mensagem persistida", "mensagem": "Texto integral\nLinha 2", "csrf_token": token})
        self.client.post("/admin/comunicados", data={"titulo": "Excesso", "mensagem": "x" * 10001, "csrf_token": token})
        self.client.get("/logout")
        self.assertEqual(self.client.get("/mensagens").status_code, 403)
        self.login("aluno")
        self.assertIn(b"Texto integral\nLinha 2", self.client.get("/mensagens").data)
        with get_session() as db:
            self.assertEqual(db.query(ComunicadoModel).count(), 1)


if __name__ == "__main__":
    unittest.main()
