"""Gera a coleção importável, mantendo cenários e scripts legíveis neste arquivo."""
import json
from pathlib import Path

DESTINO = Path(__file__).resolve().parents[2] / "Documentos" / "testes" / "postman"
folders = []


def folder(name):
    group = {"name": name, "item": []}
    folders.append(group)
    return group["item"]


def request(items, name, path, status=200, method="GET", data=None, json_body=None, scripts=(), bearer=None):
    headers = []
    req = {"method": method, "header": headers, "url": "{{base_url}}" + path}
    if data is not None:
        req["body"] = {"mode": "urlencoded", "urlencoded": [{"key": k, "value": str(v), "type": "text"} for k, v in data.items()]}
    if json_body is not None:
        headers.append({"key": "Content-Type", "value": "application/json"})
        req["body"] = {"mode": "raw", "raw": json.dumps(json_body, ensure_ascii=False), "options": {"raw": {"language": "json"}}}
    if bearer:
        headers.append({"key": "Authorization", "value": "Bearer " + bearer})
    checks = [f'pm.test("HTTP {status}", function () {{ pm.response.to.have.status({status}); }});']
    checks.extend(scripts)
    items.append({"name": name, "request": req, "protocolProfileBehavior": {"followRedirects": False}, "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": checks}}]})


def contains(text):
    name = json.dumps("Conteudo esperado: " + text[:60])
    return f'pm.test({name}, function () {{ pm.expect(pm.response.text()).to.include({json.dumps(text)}); }});'


def login(items, role):
    expected_role = "aluno" if role == "outro_aluno" else role
    request(items, f"Login {role}", "/login", method="POST", json_body={"email": f"{role}@teste.local", "senha": "{{senha_teste}}"}, scripts=[
        f'pm.test("Perfil {expected_role}", function () {{ pm.expect(pm.response.json().role).to.eql("{expected_role}"); }});',
        f'if (pm.response.code === 200) pm.collectionVariables.set("token_{role}", pm.response.json().token);',
    ])


def csrf(items, path):
    request(items, "Obter formulario e CSRF", path, scripts=[
        'const match = pm.response.text().match(/name="csrf_token" value="([^"]+)"/);',
        'pm.test("CSRF presente", function () { pm.expect(match).not.to.eql(null); });',
        'if (match) pm.collectionVariables.set("csrf_token", match[1]);',
    ])


def build():
    folders.clear()
    items = folder("01 - Visitante e autenticacao")
    request(items, "Inicio e identificador da execucao", "/", scripts=['pm.collectionVariables.set("run_id", String(Date.now()));'])
    for path in ("/mensagens", "/admin/dashboard", "/super/usuarios", "/super/layout"):
        request(items, f"Visitante bloqueado: {path}", path, 403)
    request(items, "Cadastro publico bloqueado", "/cadastro", 403, "POST", json_body={"tipo": "admin"})
    for name, payload, expected in (
        ("Login vazio", {}, 400), ("Login array", [1], 400), ("Login numero", 123, 400),
        ("Login email invalido por tipo", {"email": ["admin@teste.local"], "senha": "x"}, 400),
        ("Senha errada", {"email": "admin@teste.local", "senha": "errada"}, 401),
        ("Usuario inexistente", {"email": "inexistente@teste.local", "senha": "x"}, 404),
    ):
        request(items, name, "/login", expected, "POST", json_body=payload)
    request(items, "JWT ausente", "/professor/teste", 401)
    request(items, "JWT adulterado", "/professor/teste", 401, bearer="token.invalido.assinatura")

    items = folder("02 - Superperfil, cadastro e layout")
    login(items, "superadmin")
    csrf(items, "/super/usuarios")
    request(items, "Criar administrador", "/cadastro", 201, "POST", json_body={"tipo": "admin", "nome": "Admin API", "email": "admin-{{run_id}}@teste.local", "senha": "{{senha_teste}}"}, scripts=['if (pm.response.code === 201) pm.collectionVariables.set("novo_admin_id", pm.response.json().id);'])
    request(items, "Criar aluno via API", "/cadastro/aluno", 201, "POST", json_body={"nome": "Aluno API", "email": "aluno-{{run_id}}@teste.local", "senha": "{{senha_teste}}", "matricula": "API-{{run_id}}"})
    request(items, "Criar professor via API", "/cadastro/professor", 201, "POST", json_body={"nome": "Professor API", "email": "prof-{{run_id}}@teste.local", "senha": "{{senha_teste}}", "cpf": "00000000002"})
    request(items, "Email duplicado", "/cadastro", 409, "POST", json_body={"tipo": "admin", "nome": "Duplicado", "email": "admin-{{run_id}}@teste.local", "senha": "{{senha_teste}}"})
    request(items, "Criar aluno sem matricula", "/cadastro/aluno", 400, "POST", json_body={"nome": "Sem matricula", "email": "sem-{{run_id}}@teste.local", "senha": "{{senha_teste}}"})
    request(items, "Criar professor sem CPF", "/cadastro/professor", 400, "POST", json_body={"nome": "Sem CPF", "email": "semcpf-{{run_id}}@teste.local", "senha": "{{senha_teste}}"})
    request(items, "Superperfil nao pode ser criado por cadastro", "/cadastro", 400, "POST", json_body={"tipo": "superadmin", "nome": "Invalido", "email": "invalido@teste.local", "senha": "{{senha_teste}}"})
    request(items, "Superperfil nao pode ser rebaixado", "/super/usuarios/{{superadmin_id}}/perfil", 403, "POST", data={"tipo": "aluno", "csrf_token": "{{csrf_token}}"})
    request(items, "Usuario inexistente", "/super/usuarios/999999/perfil", 404, "POST", data={"tipo": "admin", "csrf_token": "{{csrf_token}}"})
    request(items, "Atribuir professor sem dados obrigatorios", "/super/usuarios/{{novo_admin_id}}/perfil", 400, "POST", data={"tipo": "professor", "csrf_token": "{{csrf_token}}"})
    request(items, "Atribuir professor", "/super/usuarios/{{novo_admin_id}}/perfil", 302, "POST", data={"tipo": "professor", "nome": "Professor convertido", "cpf": "00000000003", "csrf_token": "{{csrf_token}}"})
    csrf(items, "/super/layout")
    request(items, "Cores sem CSRF", "/super/layout", 400, "POST", data={"cor_fundo": "#123456", "cor_destaque": "#abcdef"})
    request(items, "Salvar cores", "/super/layout", 302, "POST", data={"cor_fundo": "#123456", "cor_destaque": "#abcdef", "csrf_token": "{{csrf_token}}"})
    request(items, "Cores persistidas", "/super/layout", scripts=[contains("#123456"), contains("#abcdef")])
    request(items, "Cor invalida rejeitada", "/super/layout", method="POST", data={"cor_fundo": "red;}", "cor_destaque": "#abcdef", "csrf_token": "{{csrf_token}}"}, scripts=[contains("#RRGGBB")])
    request(items, "Cor anterior preservada", "/super/layout", scripts=[contains('value="#123456"')])
    request(items, "Comunicado do superperfil", "/admin/comunicados", 302, "POST", data={"titulo": "Super {{run_id}}", "mensagem": "Comunicado do superperfil para todos", "csrf_token": "{{csrf_token}}"})

    items = folder("03 - Admin, turmas e comunicados")
    login(items, "admin")
    for path in ("/admin/dashboard", "/admin/cadastro-alunos", "/admin/cadastro-professores", "/admin/banco-de-dados", "/admin/disciplinas", "/admin/turmas"):
        request(items, f"Tela {path}", path)
    request(items, "Admin nao cria outro admin", "/cadastro", 403, "POST", json_body={"tipo": "admin", "nome": "Escalada", "email": "escalada@teste.local", "senha": "{{senha_teste}}"})
    request(items, "Admin sem acesso ao superperfil", "/super/usuarios", 403)
    request(items, "Admin sem acesso ao layout", "/super/layout", 403)
    request(items, "Criar disciplina", "/admin/disciplinas", 302, "POST", data={"nome": "Matematica API", "codigo": "MAT", "carga_horaria": "60"})
    request(items, "Criar turma", "/admin/turmas", 302, "POST", data={"nome": "Turma API", "codigo": "API-T1", "ano_letivo": "2026"})
    request(items, "Vincular professor a disciplina", "/admin/disciplinas", 302, "POST", data={"action": "associate_teacher", "professor_id": "{{professor_id}}", "disciplina_id": "{{disciplina_id}}"})
    request(items, "Vincular professor a turma", "/admin/turmas", 302, "POST", data={"action": "associate_teacher", "professor_id": "{{professor_id}}", "turma_id": "{{turma_id}}"})
    request(items, "Vincular aluno a turma", "/admin/turmas", 302, "POST", data={"action": "associate_student", "aluno_id": "{{aluno_id}}", "turma_id": "{{turma_id}}"})
    csrf(items, "/admin/comunicados")
    request(items, "Comunicado sem CSRF", "/admin/comunicados", 400, "POST", data={"titulo": "Sem CSRF", "mensagem": "Bloqueada"})
    request(items, "Comunicado vazio", "/admin/comunicados", method="POST", data={"titulo": "", "mensagem": "Vazia", "csrf_token": "{{csrf_token}}"}, scripts=[contains("obrigatorios")])
    request(items, "Comunicado com titulo acima do limite", "/admin/comunicados", method="POST", data={"titulo": "x" * 151, "mensagem": "Limite", "csrf_token": "{{csrf_token}}"}, scripts=[contains("150")])
    request(items, "Publicar mensagem geral", "/admin/comunicados", 302, "POST", data={"titulo": "Regressao {{run_id}}", "mensagem": "Texto integral para todos <script>alert(1)</script>", "csrf_token": "{{csrf_token}}"})
    request(items, "Mensagem publicada e escapada", "/mensagens", scripts=[contains("Texto integral para todos &lt;script&gt;"), contains("Comunicado do superperfil para todos")])
    request(items, "Upload sem arquivo", "/arquivos/upload", 400, "POST", data={"aluno_id": "{{aluno_id}}"})

    items = folder("04 - Professor e regressao academica")
    login(items, "professor")
    request(items, "Painel professor", "/professor")
    request(items, "JWT professor", "/professor/teste", bearer="{{token_professor}}")
    request(items, "Busca aluno com JWT", "/alunos/busca?termo=Aluno", bearer="{{token_professor}}", scripts=['pm.test("Alunos encontrados", function () { pm.expect(pm.response.json().alunos.length).to.be.above(0); });'])
    request(items, "Busca vazia", "/alunos/busca", 400, bearer="{{token_professor}}")
    request(items, "Professor le mensagens", "/mensagens", scripts=[contains("Texto integral para todos &lt;script&gt;")])
    request(items, "Professor nao publica", "/admin/comunicados", 403, "POST", data={"titulo": "Bloqueada", "mensagem": "Bloqueada", "csrf_token": "{{csrf_token}}"})
    request(items, "Professor nao cria usuarios", "/cadastro/aluno", 403, "POST", json_body={"nome": "Bloqueado"})
    request(items, "Professor nao acessa admin", "/admin/dashboard", 403)
    base = {"turma_id": "{{turma_id}}", "disciplina_id": "{{disciplina_id}}"}
    request(items, "Lancar atividade", "/professor/atividades/lancar", 302, "POST", data={**base, "titulo": "Atividade API", "descricao": "Exercicios de regressao"})
    request(items, "Atividade em turma sem vinculo", "/professor/atividades/lancar", 403, "POST", data={**base, "turma_id": "999", "titulo": "Invalida"})
    nota = {**base, "aluno_id": "{{aluno_id}}"}
    for value in ("-1", "11", "abc", "NaN", "sNaN", "Infinity"):
        request(items, f"Nota invalida: {value}", "/professor/notas/salvar", 400, "POST", data={**nota, "nota": value})
    request(items, "Salvar nota com virgula", "/professor/notas/salvar", 302, "POST", data={**nota, "nota": "8,5"})
    request(items, "Atualizar nota", "/professor/notas/salvar", 302, "POST", data={**nota, "nota": "9"})
    request(items, "Aluno fora da turma", "/professor/notas/salvar", 403, "POST", data={**nota, "aluno_id": "{{outro_aluno_id}}", "nota": "9"})

    items = folder("05 - Aluno, leitura e bloqueios")
    login(items, "aluno")
    request(items, "Painel aluno", "/aluno")
    request(items, "Aluno ve disciplina e atividade", "/aluno/disciplinas/{{disciplina_id}}", scripts=[contains("Atividade API")])
    request(items, "Aluno le mensagens e tema", "/mensagens", scripts=[contains("Texto integral para todos &lt;script&gt;"), contains("#123456")])
    request(items, "Aluno nao publica", "/admin/comunicados", 403, "POST", data={"titulo": "Bloqueada", "mensagem": "Bloqueada", "csrf_token": "{{csrf_token}}"})
    request(items, "Aluno nao cria usuarios", "/cadastro/aluno", 403, "POST", json_body={"nome": "Bloqueado"})
    request(items, "Aluno nao usa JWT de professor", "/professor/teste", 403, bearer="{{token_aluno}}")
    request(items, "Aluno nao altera nota", "/professor/notas/salvar", 403, "POST", data={**nota, "nota": "10"})
    for path in ("/super/usuarios", "/super/layout", "/admin/dashboard", "/professor"):
        request(items, f"Aluno bloqueado: {path}", path, 403)
    login(items, "outro_aluno")
    request(items, "Outro aluno nao ve disciplina", "/aluno/disciplinas/{{disciplina_id}}", 404)
    request(items, "Logout", "/logout", 302)
    request(items, "Mensagens bloqueadas apos logout", "/mensagens", 403)

    items = folder("06 - Revogacao de permissoes e restauracao do tema")
    login(items, "superadmin")
    csrf(items, "/super/usuarios")
    request(items, "Professor passa a aluno", "/super/usuarios/{{professor_user_id}}/perfil", 302, "POST", data={"tipo": "aluno", "nome": "Professor convertido", "matricula": "CONVERTIDO", "csrf_token": "{{csrf_token}}"})
    request(items, "JWT antigo perde permissao de professor", "/professor/teste", 403, bearer="{{token_professor}}")
    request(items, "Restaurar professor", "/super/usuarios/{{professor_user_id}}/perfil", 302, "POST", data={"tipo": "professor", "csrf_token": "{{csrf_token}}"})
    request(items, "Restaurar cores padrao", "/super/layout", 302, "POST", data={"cor_fundo": "#06385d", "cor_destaque": "#22d3ee", "csrf_token": "{{csrf_token}}"})
    request(items, "Conferir cores restauradas", "/super/layout", scripts=[contains('value="#06385d"')])
    request(items, "Encerrar sessao", "/logout", 302)

    collection = {
        "info": {"name": "Educa Fast - API e regressao", "description": "Executar integralmente em banco descartavel criado por tests/executar_postman.py --serve. Usa cookies de sessao, JWT e CSRF reais. Ha requisicoes que criam dados e alteram permissoes. Desative o redirecionamento automatico. Reinicie o servidor descartavel antes de cada execucao.", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "item": folders,
        "variable": [{"key": "csrf_token", "value": ""}, {"key": "run_id", "value": ""}],
    }
    values = {"base_url": "http://127.0.0.1:5051", "senha_teste": "Teste-local-2026!", "superadmin_id": "1", "professor_user_id": "3", "professor_id": "1", "aluno_id": "1", "outro_aluno_id": "2", "turma_id": "1", "disciplina_id": "1"}
    environment = {"name": "Educa Fast - local descartavel", "values": [{"key": k, "value": v, "enabled": True} for k, v in values.items()], "_postman_variable_scope": "environment"}
    DESTINO.mkdir(parents=True, exist_ok=True)
    for filename, data in (("EducaFast.postman_collection.json", collection), ("Local.postman_environment.json", environment)):
        (DESTINO / filename).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Colecao gerada: {sum(len(f['item']) for f in folders)} requisicoes")


if __name__ == "__main__":
    build()
