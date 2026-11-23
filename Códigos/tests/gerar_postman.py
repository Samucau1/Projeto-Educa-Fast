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
    if method == "POST" and path != "/login" and not ("sem CSRF" in name):
        headers.append({"key": "X-CSRF-Token", "value": "{{csrf_token}}"})
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
        f'if (pm.response.code === 200) pm.collectionVariables.set("csrf_token", pm.response.json().csrf_token); if (pm.response.code === 200) pm.collectionVariables.set("token_{role}", pm.response.json().token);',
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
        ("Usuario inexistente", {"email": "inexistente@teste.local", "senha": "x"}, 401),
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
    request(items, "Logout", "/logout", 302, "POST")
    request(items, "Mensagens bloqueadas apos logout", "/mensagens", 403)

    items = folder("06 - Revogacao de permissoes e restauracao do tema")
    login(items, "superadmin")
    csrf(items, "/super/usuarios")
    request(items, "Professor passa a aluno", "/super/usuarios/{{professor_user_id}}/perfil", 302, "POST", data={"tipo": "aluno", "nome": "Professor convertido", "matricula": "CONVERTIDO", "csrf_token": "{{csrf_token}}"})
    request(items, "JWT antigo perde permissao de professor", "/professor/teste", 403, bearer="{{token_professor}}")
    request(items, "Restaurar professor", "/super/usuarios/{{professor_user_id}}/perfil", 302, "POST", data={"tipo": "professor", "csrf_token": "{{csrf_token}}"})
    request(items, "Restaurar cores padrao", "/super/layout", 302, "POST", data={"cor_fundo": "#06385d", "cor_destaque": "#22d3ee", "csrf_token": "{{csrf_token}}"})
    request(items, "Conferir cores restauradas", "/super/layout", scripts=[contains('value="#06385d"')])
    request(items, "Encerrar sessao", "/logout", 302, "POST")

    items = folder("07 - LGPD, privacidade e protecoes de sessao")
    request(items, "Aviso publico de privacidade", "/privacidade", scripts=[contains("EducaFast")])
    request(items, "Visitante sem dados pessoais", "/minha-privacidade", 403)
    login(items, "aluno")
    request(items, "Solicitacao sem CSRF", "/minha-privacidade", 400, "POST", data={"tipo": "acesso"})
    request(items, "Registrar pedido LGPD", "/minha-privacidade", 302, "POST", data={"tipo": "correcao", "detalhe": "Pedido LGPD {{run_id}}"})
    request(items, "Consultar protocolo proprio", "/minha-privacidade", scripts=[
        'const protocol = pm.response.text().match(/Protocolo (\\d+)/);',
        'pm.test("Protocolo presente", function () { pm.expect(protocol).not.to.eql(null); });',
        'if (protocol) pm.collectionVariables.set("pedido_lgpd_id", protocol[1]);',
    ])
    export_checks = [
        'pm.test("Somente a conta titular", function () { pm.expect(pm.response.json().conta.email).to.eql("aluno@teste.local"); });',
        'pm.test("Senha ausente", function () { pm.expect(pm.response.json().conta).not.to.have.property("senha"); });',
        'pm.test("Sem cache de dados pessoais", function () { pm.expect(pm.response.headers.get("Cache-Control")).to.eql("no-store"); });',
    ]
    request(items, "Exportar dados proprios", "/minha-privacidade/exportar", method="POST", scripts=export_checks)
    request(items, "Parametro nao seleciona outra conta", "/minha-privacidade/exportar?usuario_id={{superadmin_id}}", method="POST", scripts=export_checks)
    request(items, "Aluno sem fila administrativa", "/admin/privacidade", 403)
    login(items, "outro_aluno")
    request(items, "Outro aluno nao ve o protocolo", "/minha-privacidade", scripts=[
        'pm.test("Pedido de outro titular ausente", function () { pm.expect(pm.response.text()).not.to.include("Pedido LGPD " + pm.collectionVariables.get("run_id")); });',
    ])
    login(items, "professor")
    request(items, "Professor sem fila administrativa", "/admin/privacidade", 403)
    login(items, "admin")
    request(items, "Cookie admin sem CSRF e Bearer falso", "/cadastro/aluno", 400, "POST", json_body={"nome": "Bloqueado"}, bearer="token.falso.assinatura")
    request(items, "Fila administrativa de privacidade", "/admin/privacidade")
    request(items, "Responder pedido do titular", "/admin/privacidade/{{pedido_lgpd_id}}", 302, "POST", data={"status": "concluido", "resposta": "Atendimento LGPD {{run_id}}"})
    request(items, "Pedido encerrado nao reabre", "/admin/privacidade/{{pedido_lgpd_id}}", 409, "POST", data={"status": "em_analise", "resposta": "Alteracao bloqueada"})
    login(items, "aluno")
    request(items, "Titular recebe resposta", "/minha-privacidade", scripts=[contains("Atendimento LGPD")])
    request(items, "GET logout apenas confirma", "/logout")
    request(items, "Sessao continua apos GET logout", "/minha-privacidade")
    request(items, "Logout com CSRF", "/logout", 302, "POST")
    request(items, "Dados bloqueados apos logout", "/minha-privacidade", 403)

    items = folder("10 - Cursos reutilizaveis por turma e ano")
    login(items, "professor")
    request(items, "Professor cria curso reutilizavel", "/cursos", 201, "POST", json_body={"disciplina_id": "{{disciplina_id}}", "titulo": "Curso reutilizavel {{run_id}}"}, scripts=['if (pm.response.code === 201) pm.collectionVariables.set("curso_id", pm.response.json().curso_id);'])
    request(items, "Professor cria capitulo", "/cursos/{{curso_id}}/estrutura", 200, "POST", json_body={"acao": "adicionar", "tipo": "capitulo", "titulo": "Capitulo inicial"}, scripts=['if (pm.response.code === 200) pm.collectionVariables.set("capitulo_id", pm.response.json().item_id);'])
    request(items, "Professor cria tema", "/cursos/{{curso_id}}/estrutura", 200, "POST", json_body={"acao": "adicionar", "tipo": "tema", "pai_id": "{{capitulo_id}}", "titulo": "Tema inicial"}, scripts=['if (pm.response.code === 200) pm.collectionVariables.set("tema_id", pm.response.json().item_id);'])
    request(items, "Video arbitrario recusado", "/cursos/{{curso_id}}/estrutura", 400, "POST", json_body={"acao": "adicionar", "tipo": "aula", "pai_id": "{{tema_id}}", "titulo": "Invalida", "video": "https://evil.test/video"})
    request(items, "Professor cria videoaula", "/cursos/{{curso_id}}/estrutura", 200, "POST", json_body={"acao": "adicionar", "tipo": "aula", "pai_id": "{{tema_id}}", "titulo": "Videoaula inicial", "video": "https://youtu.be/abcdefghijk"}, scripts=['if (pm.response.code === 200) pm.collectionVariables.set("aula_id", pm.response.json().item_id);'])
    request(items, "Professor nao publica", "/cursos/{{curso_id}}/estado", 403, "POST", json_body={"estado": "publicado"})
    request(items, "Previa do professor", "/cursos/{{curso_id}}", scripts=[contains("Videoaula inicial")])
    login(items, "admin")
    request(items, "Admin publica", "/cursos/{{curso_id}}/estado", 200, "POST", json_body={"estado": "publicado"})
    request(items, "Conteudo publicado preservado", "/cursos/{{curso_id}}/estrutura", 409, "POST", json_body={"acao": "curso", "titulo": "Alteracao indevida"})
    request(items, "Atribuicao explicita na turma atual", "/admin/gestao-turmas", 200, "POST", json_body={"acao": "atribuir", "turma_id": "{{turma_id}}", "professor_id": "{{professor_id}}", "disciplina_id": "{{disciplina_id}}"})
    request(items, "Liberar na turma atual", "/cursos/{{curso_id}}/ofertas", 200, "POST", json_body={"turma_id": "{{turma_id}}"}, scripts=['if (pm.response.code === 200) pm.collectionVariables.set("oferta_id", pm.response.json().oferta_id);'])
    request(items, "Criar turma de outro ano", "/admin/gestao-turmas", 200, "POST", json_body={"acao": "criar", "nome": "Turma proximo ano", "codigo": "ANO-{{run_id}}", "ano_letivo": 2027}, scripts=['if (pm.response.code === 200) pm.collectionVariables.set("turma_futura_id", pm.response.json().turma_id);'])
    request(items, "Atribuir na turma futura", "/admin/gestao-turmas", 200, "POST", json_body={"acao": "atribuir", "turma_id": "{{turma_futura_id}}", "professor_id": "{{professor_id}}", "disciplina_id": "{{disciplina_id}}"})
    request(items, "Matricular na turma futura", "/admin/gestao-turmas", 200, "POST", json_body={"acao": "matricular", "turma_id": "{{turma_futura_id}}", "aluno_id": "{{aluno_id}}"})
    request(items, "Mesmo curso em outro ano", "/cursos/{{curso_id}}/ofertas", 200, "POST", json_body={"turma_id": "{{turma_futura_id}}"}, scripts=['if (pm.response.code === 200) pm.collectionVariables.set("oferta_futura_id", pm.response.json().oferta_id);'])
    login(items, "aluno")
    request(items, "Biblioteca do aluno", "/cursos", scripts=[contains("Curso reutilizavel")])
    request(items, "Aluno acessa videoaula", "/aprender/{{oferta_id}}", scripts=[contains("Videoaula inicial")])
    request(items, "Confirmar conclusao", "/aprender/{{oferta_id}}/aulas/{{aula_id}}/concluir", 200, "POST", json_body={})
    request(items, "Conclusao idempotente", "/aprender/{{oferta_id}}/aulas/{{aula_id}}/concluir", 200, "POST", json_body={})
    request(items, "Progresso concluido", "/aprender/{{oferta_id}}", scripts=[contains("100%")])
    request(items, "Novo ano tem progresso independente", "/aprender/{{oferta_futura_id}}", scripts=[contains("0%"), contains("0 de 1 aulas")])
    request(items, "Aluno sem autoria", "/cursos/{{curso_id}}", 403)
    login(items, "outro_aluno")
    request(items, "Outra matricula bloqueada", "/aprender/{{oferta_id}}", 404)
    login(items, "professor")
    request(items, "Duplicar sem alterar original", "/cursos/{{curso_id}}/duplicar", 201, "POST", json_body={}, scripts=['if (pm.response.code === 201) pm.collectionVariables.set("curso_copia_id", pm.response.json().curso_id);'])
    request(items, "Editar nova edicao", "/cursos/{{curso_copia_id}}/estrutura", 200, "POST", json_body={"acao": "curso", "titulo": "Nova edicao"})
    login(items, "admin")
    request(items, "Suspender oferta", "/cursos/ofertas/{{oferta_id}}/revogar", 200, "POST", json_body={})
    login(items, "aluno")
    request(items, "Revogacao imediata", "/aprender/{{oferta_id}}", 404)


    items = folder("11 - Reconciliacao e diario por periodo")
    login(items, "admin")
    request(items, "Previa das atribuicoes sem alterar dados", "/academico/reconciliar/{{turma_id}}?formato=json", scripts=[
        'pm.collectionVariables.set("revisao_turma", pm.response.json().revisao);',
        'pm.test("Candidatos para revisao", function () { pm.expect(pm.response.json().candidatos).to.be.an("array"); });',
    ])
    request(items, "Confirmar somente a atribuicao revisada", "/academico/reconciliar/{{turma_id}}", 200, "POST", json_body={"revisao": "{{revisao_turma}}", "confirmadas": ["{{professor_id}}:{{disciplina_id}}"]})
    for suffix, turma in (("atual", "{{turma_id}}"), ("futuro", "{{turma_futura_id}}")):
        request(items, "Criar periodo " + suffix, "/academico/periodos", 201, "POST", json_body={"turma_id": turma, "nome": "1o bimestre", "ordem": 1, "media_referencia": "6"}, scripts=[f'if (pm.response.code === 201) pm.collectionVariables.set("periodo_{suffix}", pm.response.json().periodo_id);'])
    request(items, "Consultar ofertas academicas", "/academico?formato=json", scripts=[
        'const rows = pm.response.json().vinculos;',
        'pm.collectionVariables.set("vinculo_atual", rows.find(v => String(v.turma_id) === pm.environment.get("turma_id") && String(v.disciplina_id) === pm.environment.get("disciplina_id")).id);',
        'pm.collectionVariables.set("vinculo_futuro", rows.find(v => String(v.turma_id) === String(pm.collectionVariables.get("turma_futura_id"))).id);',
    ])
    login(items, "professor")
    for suffix in ("atual", "futuro"):
        request(items, "Criar avaliacao " + suffix, "/academico/avaliacoes", 201, "POST", json_body={"turma_disciplina_id": "{{vinculo_" + suffix + "}}", "periodo_id": "{{periodo_" + suffix + "}}", "titulo": "Prova " + suffix, "peso": "1"}, scripts=[f'if (pm.response.code === 201) pm.collectionVariables.set("avaliacao_{suffix}", pm.response.json().avaliacao_id);'])
    request(items, "Lancar nota no ano atual", "/academico/avaliacoes/{{avaliacao_atual}}/alunos/{{aluno_id}}", 200, "POST", json_body={"valor": "8,5", "versao": 0})
    request(items, "Impedir sobrescrita por formulario antigo", "/academico/avaliacoes/{{avaliacao_atual}}/alunos/{{aluno_id}}", 409, "POST", json_body={"valor": "1", "versao": 0})
    request(items, "Lancar nota independente no ano futuro", "/academico/avaliacoes/{{avaliacao_futuro}}/alunos/{{aluno_id}}", 200, "POST", json_body={"valor": "5", "versao": 0})
    request(items, "Bloquear aluno fora da turma", "/academico/avaliacoes/{{avaliacao_atual}}/alunos/{{outro_aluno_id}}", 403, "POST", json_body={"valor": "8", "versao": 0})
    for suffix in ("atual", "futuro"):
        request(items, "Publicar notas " + suffix, "/academico/avaliacoes/{{avaliacao_" + suffix + "}}/publicar", 200, "POST", json_body={})
    login(items, "aluno")
    request(items, "Boletim preserva dois anos", "/boletim?formato=json", scripts=[
        'const rows = pm.response.json().periodos;',
        'pm.test("Medias separadas por ano", function () { pm.expect(rows.find(r => r.ano === 2026).media).to.eql("8.50"); pm.expect(rows.find(r => r.ano === 2027).media).to.eql("5.00"); });',
    ])
    request(items, "Aluno nao acessa diario do professor", "/academico/avaliacoes/{{avaliacao_atual}}", 403)
    login(items, "outro_aluno")
    request(items, "Boletim nao revela notas de outro aluno", "/boletim?formato=json", scripts=['pm.test("Sem notas de outro titular", function () { pm.expect(pm.response.json().periodos).to.eql([]); });'])
    login(items, "admin")
    request(items, "Fechar periodo com motivo", "/academico/periodos/{{periodo_atual}}/estado", 200, "POST", json_body={"estado": "fechado", "motivo": "Encerramento conferido pela secretaria"})
    login(items, "professor")
    request(items, "Periodo fechado bloqueia correcao", "/academico/avaliacoes/{{avaliacao_atual}}/alunos/{{aluno_id}}", 409, "POST", json_body={"valor": "9", "versao": 1})


    items = folder("12 - Configuracao institucional do superadmin")
    login(items, "admin")
    request(items, "Admin nao altera regras institucionais", "/super/escola", 403)
    login(items, "superadmin")
    request(items, "Configuracao institucional", "/super/escola")
    request(items, "Identidade personalizada com tokens", "/super/escola/identidade", 200, "POST", json_body={"versao": 0, "nome": "Escola API", "sigla": "API", "subtitulo": "APRENDER JUNTOS", "modo": "claro", "fundo": "#f3f6fb", "destaque": "#1d4ed8", "superficie": "#ffffff", "texto": "#18283b", "muted": "#475569", "raio": "12", "densidade": "confortavel", "fonte": "dm-sans"})
    request(items, "Marca aparece nos paineis", "/mensagens", scripts=[contains("Escola API"), contains("school-theme")])
    request(items, "CSS arbitrario recusado", "/super/escola/identidade", 400, "POST", json_body={"versao": 1, "nome": "Escola API", "sigla": "API", "subtitulo": "Escola", "fundo": "red;}", "destaque": "#1d4ed8", "superficie": "#ffffff", "texto": "#18283b", "muted": "#475569"})
    request(items, "Criar calendario institucional", "/super/escola/calendarios", 201, "POST", json_body={"ano": 2028, "nome": "Calendario 2028", "inicio": "2028-01-01", "fim": "2028-12-31", "dias_semana": [0, 1, 2, 3, 4], "meta_letivos": 200}, scripts=['if (pm.response.code === 201) pm.collectionVariables.set("calendario_escola", pm.response.json().calendario_id);'])
    request(items, "Recesso informado pela escola", "/super/escola/calendarios/{{calendario_escola}}/eventos", 201, "POST", json_body={"versao": 1, "titulo": "Recesso de demonstracao", "tipo": "recesso", "inicio": "2028-02-10"})
    request(items, "Calendario desatualizado nao sobrescreve", "/super/escola/calendarios/{{calendario_escola}}/eventos", 409, "POST", json_body={"versao": 1, "titulo": "Desatualizado", "tipo": "recesso", "inicio": "2028-02-11"})
    request(items, "Criar regra de semestres com pesos diferentes", "/super/escola/politicas", 201, "POST", json_body={"nome": "Regra 2028", "calendario_id": "{{calendario_escola}}", "divisao": "semestres", "media_referencia": "7", "casas": "1", "arredondamento": "truncar", "periodos": [{"nome": "1o semestre", "peso": "1", "inicio": "2028-01-01", "fim": "2028-06-30"}, {"nome": "2o semestre", "peso": "3", "inicio": "2028-07-01", "fim": "2028-12-31"}]}, scripts=['if (pm.response.code === 201) pm.collectionVariables.set("politica_escola", pm.response.json().politica_id);'])
    request(items, "Criar turma do ano da regra", "/admin/gestao-turmas", 200, "POST", json_body={"acao": "criar", "nome": "Turma institucional", "codigo": "ESC-{{run_id}}", "ano_letivo": 2028}, scripts=['if (pm.response.code === 200) pm.collectionVariables.set("turma_escola", pm.response.json().turma_id);'])
    request(items, "Aplicar regras e criar periodos", "/super/escola/politicas/{{politica_escola}}/aplicar", 200, "POST", json_body={"turma_id": "{{turma_escola}}"})
    request(items, "Aplicacao repetida preserva historico", "/super/escola/politicas/{{politica_escola}}/aplicar", 409, "POST", json_body={"turma_id": "{{turma_escola}}"})
    login(items, "admin")
    request(items, "Admin nao muda a divisao institucional", "/academico/periodos", 403, "POST", json_body={"turma_id": "{{turma_escola}}", "nome": "Extra", "ordem": 3})
    login(items, "aluno")
    request(items, "Calendario visivel a comunidade", "/calendario-escolar", scripts=[contains("Recesso de demonstracao")])
    request(items, "Aluno sem acesso a configuracao", "/super/escola", 403)


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
