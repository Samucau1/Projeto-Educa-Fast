# Testes de API, carga e regressão — Educa Fast

Resultado atual: [cursos e gestão acadêmica](RELATORIO_CURSOS.md). A coleção tem 158 requisições e 210 verificações; a regressão completa tem 56 cenários, incluindo 8 unitários e três corridas transacionais exclusivas do MySQL. A [validação anterior](RELATORIO_VALIDACAO_FINAL.md) permanece como histórico de segurança/LGPD.

Para testar pelo navegador, use o [roteiro de teste manual com usuários e comandos Docker](TESTE_MANUAL.md).

Os testes usam dados sintéticos e bancos descartáveis: SQLite localmente ou MySQL 8.4 no Docker. Não alteram o banco configurado no `.env`. O servidor HTTP do Postman escuta somente em `127.0.0.1`.

## Executar com MySQL no Docker

Com Docker Desktop iniciado, execute na raiz do repositório, em sequência:

```powershell
docker compose -p educafast-validacao -f Códigos/docker-compose.test.yml build testes
docker compose -p educafast-validacao -f Códigos/docker-compose.test.yml up -d --wait mysql_test

docker compose -p educafast-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_estresse.py --confirmar-banco-descartavel

docker compose -p educafast-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_regressao.py --somente-unitarios
docker compose -p educafast-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_regressao.py
docker compose -p educafast-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_postman.py
docker compose -p educafast-validacao -f Códigos/docker-compose.test.yml down
```

Confira o resultado de cada suíte antes de continuar. Não execute as duas simultaneamente: elas recriam as tabelas do banco exclusivo `educafast_regressao`. Ao terminar, o último comando remove os containers e a rede desse projeto de testes. Os dados do MySQL ficam em `tmpfs` e são descartados com o container; as evidências permanecem em [`resultados/mysql/`](resultados/mysql/).

Esse Compose não publica portas, não usa volumes persistentes e não exige a senha do root do MySQL instalado. As credenciais declaradas nele são sintéticas e exclusivas do ambiente de testes. Os executores só aceitam MySQL quando o modo de testes está habilitado e a conexão corresponde ao serviço, banco e usuário definidos nesse Compose. Não precisa instalar Python ou Newman no Windows para essa execução; a imagem inclui Python 3.12 e Newman 6.2.1.

## Executar pela linha de comando

Na raiz do repositório, com Python e Node.js instalados:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\Códigos\requirements.txt
npm.cmd install --prefix .cache/postman newman@6.2.1 --no-audit --no-fund
```

Se o ambiente virtual já existir, utilize-o diretamente. Execute a regressão e depois a coleção de API:

```powershell
.\.venv\Scripts\python.exe .\Códigos\tests\executar_regressao.py
.\.venv\Scripts\python.exe .\Códigos\tests\executar_postman.py
```

Cada comando retorna `0` quando passa e um código diferente de zero quando falha. Os relatórios locais são gravados em [`resultados/`](resultados/). Fora do modo Docker, a regressão habilita as chaves estrangeiras do SQLite e exige SQLite em memória. O servidor local do Postman cria um arquivo de banco temporário e habilita as chaves estrangeiras em cada conexão.

Também é possível executar somente unittest, na pasta `Códigos`:

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Executar no Postman Desktop

1. Na raiz do projeto, inicie o servidor descartável:

   ```powershell
   .\.venv\Scripts\python.exe .\Códigos\tests\executar_postman.py --serve
   ```

2. Importe [`EducaFast.postman_collection.json`](postman/EducaFast.postman_collection.json) e [`Local.postman_environment.json`](postman/Local.postman_environment.json).
3. Selecione o ambiente **Educa Fast - local descartavel**, cuja URL é `http://127.0.0.1:5051`.
4. Limpe cookies anteriores desse endereço. Desative **Automatically follow redirects** nas configurações do Postman; a coleção também declara essa opção por requisição. Os redirecionamentos `302` fazem parte dos contratos dos formulários.
5. Execute a coleção inteira, na ordem, com uma iteração. O cookie de sessão é gerenciado pelo Postman; os scripts extraem o CSRF dos formulários e armazenam os JWTs dos logins.
6. Encerre com `Ctrl+C`. Reinicie o servidor para uma nova execução, pois a coleção cria turmas e disciplinas com identificadores conhecidos da base vazia.

Use o Desktop Agent se executar pela interface web do Postman. Se a porta estiver ocupada, utilize `--port 5052` e altere `base_url` no ambiente para a mesma porta.

As credenciais sintéticas do ambiente são `superadmin@teste.local`, `admin@teste.local`, `professor@teste.local`, `aluno@teste.local` e `outro_aluno@teste.local`, todas com senha `Teste-local-2026!`. Elas existem apenas no servidor descartável. Os identificadores do ambiente dependem dessas fixtures; não aponte esta coleção para o banco da instalação.

A coleção tem 158 requisições e 210 verificações, incluindo cursos, LGPD e proteções de sessão. Algumas rotas são formulários HTML, não APIs JSON: nesses casos, a coleção verifica o status HTTP, os textos de validação e o conteúdo publicado. A troca de perfis e as cores são exercitadas e restauradas ao final.

## Cobertura

| Área | Verificações |
| --- | --- |
| Autenticação | Login por perfil, senha incorreta, usuário inexistente, JSON inválido por estrutura/tipo, logout e telas protegidas |
| Cadastro | Aluno, professor e admin; e-mail duplicado; matrícula/CPF obrigatórios; bloqueio de escalada de privilégio |
| Superperfil | Atribuição de perfil, criação de cadastro acadêmico, proteção do próprio superperfil e usuário inexistente |
| Permissões | Admin, professor, aluno e visitante; efeito imediato em sessão e JWT após alteração de perfil |
| Aparência | Cores persistidas, formato inválido, preservação do valor anterior, aplicação ao aluno e CSRF |
| Comunicados | Admin/superperfil publicam; aluno/professor leem; envio indevido bloqueado; conteúdo escapado; tamanho e campos obrigatórios |
| Acadêmico | Disciplina, turma, associações, atividade, nota com vírgula, atualização sem duplicar, limites de nota e vínculos obrigatórios |
| Documentos | Upload/download por admin e superperfil, solicitação/resposta de aluno, isolamento entre alunos por sessão e JWT e revogação de upload por JWT |

Os testes de documentos com arquivos e a comprovação direta da persistência no banco estão na suíte Python. A coleção verifica as rotas HTTP, formulários, sessões e JWTs; não valida a aparência da interface nem executa JavaScript do navegador.

## Evidências e situação antes do GitHub

Consulte [`RELATORIO_VALIDACAO_FINAL.md`](RELATORIO_VALIDACAO_FINAL.md). O relatório anterior fica preservado como histórico em [`RELATORIO_REGRESSAO.md`](RELATORIO_REGRESSAO.md). Os resultados detalhados estão em:

- [`regressao-unittest.txt`](resultados/regressao-unittest.txt) e [`regressao-resumo.json`](resultados/regressao-resumo.json).
- [`postman-newman.txt`](resultados/postman-newman.txt), [`postman-junit.xml`](resultados/postman-junit.xml) e [`postman-resumo.json`](resultados/postman-resumo.json).
- [Resultados de regressão e Postman com MySQL no Docker](resultados/mysql/).

Os resultados atuais de carga, unitários, Postman e regressão passaram. SQLite ignora as três corridas específicas de MySQL; elas passam na execução MySQL. O executor de carga usa HTTP real com até 8 clientes nos fluxos completos e 32 nas leituras, mede p50/p95/máximo e confere persistência. Não aponte esses executores para dados reais nem execute suítes simultaneamente contra o mesmo banco.

Para alterar os cenários da coleção, edite `Códigos/tests/gerar_postman.py` e execute-o; os JSONs são gerados novamente. O executor do Postman também os regenera antes de iniciar.
