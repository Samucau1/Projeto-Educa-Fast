# Educa Fast — Secretaria Escolar DF

[![CI](https://github.com/Samucau1/Projeto-Educa-Fast/actions/workflows/ci.yml/badge.svg)](https://github.com/Samucau1/Projeto-Educa-Fast/actions/workflows/ci.yml)

Sistema web de gestão escolar que centraliza cadastros, turmas, disciplinas, comunicados, notas, atividades e documentos. A aplicação possui áreas para a secretaria (administrador), professores e alunos.

## Índice

- [Funcionalidades](#funcionalidades)
- [Tecnologias e arquitetura](#tecnologias-e-arquitetura)
- [Arquitetura em camadas](#arquitetura-em-camadas)
- [Telas do sistema](#telas-do-sistema)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como executar](#como-executar)
- [Validação e limites atuais](#validação-e-limites-atuais)
- [Documentação e licença](#documentação-e-licença)

## Configuração institucional

O superadmin configura a identidade da escola, o calendário, dias letivos, feriados/recessos/reposições e versões das regras de boletim. Semestres, trimestres, bimestres, pesos anuais e arredondamento são aplicados explicitamente por turma, preservando históricos. Consulte [o guia](docs/CONFIGURACAO_INSTITUCIONAL.md), [o protocolo obrigatório de design](docs/PROTOCOLO_DESIGN.md) e [a validação](docs/testes/RELATORIO_ESCOLA.md).

## Diário e boletim por período

O sistema inclui revisão explícita das atribuições antigas, avaliações com pesos e notas separadas por turma, ano e período. Professores lançam e publicam notas; a secretaria gerencia períodos e o vínculo das notas anteriores. Consulte [uso e arquitetura](docs/DIARIO_E_RECONCILIACAO.md) e [homologação](docs/testes/RELATORIO_ACADEMICO.md).

## Cursos reutilizáveis

Professores organizam cursos em capítulos, temas e videoaulas. A administração publica o conteúdo e libera o mesmo curso para várias turmas e anos, com progresso separado por oferta. Cursos publicados são preservados; novas edições podem ser duplicadas em rascunho. A tela **Gestão acadêmica** permite atribuir professor, turma e disciplina explicitamente.

Consulte [arquitetura e uso](docs/CURSOS_REUTILIZAVEIS.md) e [validação dos cursos](docs/testes/RELATORIO_CURSOS.md).

## Funcionalidades

| Perfil | Recursos implementados |
| --- | --- |
| Administrador | Consultar o painel da secretaria; cadastrar e editar alunos e professores; criar disciplinas e turmas; associar alunos e professores às turmas e professores às disciplinas; publicar comunicados; solicitar, enviar e consultar documentos. |
| Professor | Consultar turmas e alunos vinculados; lançar atividades com anexos; registrar ou atualizar notas; consultar comunicados; enviar documentos solicitados pela secretaria. |
| Aluno | Consultar disciplinas, notas, atividades e comunicados; baixar arquivos disponíveis; enviar documentos solicitados pela secretaria. |

Os cadastros incluem dados específicos de cada perfil e foto opcional em JPG ou PNG de até 2 MB. As notas devem estar entre 0 e 10, com validação dos vínculos entre professor, aluno, turma e disciplina. Existe uma nota por aluno e disciplina; um novo lançamento atualiza esse registro.

## Tecnologias e arquitetura

- **API (`api/`):** Python 3.12 e Flask 3.1.
- **Banco:** SQLAlchemy 2.0, psycopg 3 e Postgres 16, com várias escolas no mesmo banco (um schema por escola; veja [Várias escolas](docs/MULTIESCOLA.md)).
- **Aplicação web (`web/`):** React 18 e Vite, com CSS próprio e utilitários Tailwind pré-compilados.
- **Ambiente:** Docker, Docker Compose e python-dotenv.
- **Dependência de criptografia:** cryptography, incluída nos requisitos Python.

O ponto de entrada `api/app.py` chama `create_app()`, carrega a configuração, inicializa o banco e registra os blueprints. As rotas encaminham as operações aos controllers, que consultam os modelos SQLAlchemy e respondem em JSON.

As telas são desenhadas no navegador pela aplicação React (`web/`). Cada rota de tela da API continua decidindo permissões, dados e redirecionamentos e, por meio de `render_page` (`api/app/spa.py`), responde com JSON quando a SPA pede (cabeçalho `X-EducaFast-SPA`) ou com o `index.html` do build quando o navegador abre o endereço diretamente. Links e formulários são tratados pela SPA, sem recarregar a página. O build do React é servido pela própria API em `/static/dist/`, na mesma origem, então sessão e CSRF funcionam sem CORS. A interface não depende de recursos externos.

O login verifica senhas armazenadas como hash pelo Werkzeug, estabelece uma sessão Flask e retorna um JWT HS256. As páginas verificam o perfil pela sessão; algumas rotas JSON exigem o cabeçalho `Authorization: Bearer <token>`.

## Arquitetura em camadas

A organização segue uma separação de responsabilidades semelhante ao MVC, com blueprints para as rotas. A API entrega os dados de cada tela; a aplicação React (`web/`) os apresenta.

```mermaid
flowchart TD
    Navegador["Navegador: administrador, professor ou aluno"]
    Rotas["Flask: blueprints em app/routes"]
    Acesso["Sessão Flask, guards e validação JWT"]
    Controllers["Controllers: operações e validações"]
    Modelos["Modelos SQLAlchemy e sessões do banco"]
    Banco[(Postgres)]
    Spa["render_page: dados da tela em JSON"]
    Interface["Aplicação React (web/)"]
    Arquivos["Pasta de uploads"]

    Navegador -->|Requisição HTTP| Rotas
    Rotas --> Acesso
    Acesso --> Controllers
    Controllers --> Modelos
    Modelos <--> Banco
    Controllers -->|Dados da tela| Spa
    Spa --> Interface
    Interface -->|Telas e interações| Navegador
    Controllers -->|Resposta JSON ou redirecionamento| Navegador
    Controllers <--> Arquivos
```

| Camada | Arquivos/pastas | Responsabilidade |
| --- | --- | --- |
| Inicialização | `app.py`, `app/__init__.py`, `config.py` | Criar a aplicação, carregar configurações e registrar rotas. |
| Entrada HTTP | `app/routes/` | Receber formulários, JSON e arquivos; selecionar a operação e montar a resposta. |
| Autenticação e acesso | `app/auth.py`, `app/routes/guards.py` | Assinar/validar JWTs e verificar o perfil nas rotas protegidas. |
| Aplicação | `app/controllers/` | Executar cadastros, associações, consultas dos painéis, notas, atividades e documentos. |
| Persistência | `app/models/`, `app/database.py` | Mapear entidades e vínculos, abrir sessões e inicializar o esquema. |
| Ponte com a interface | `app/spa.py`, `app/views/` | Entregar os dados de cada tela em JSON (ou o `index.html` do build) e o mapa de rotas (`/api/rotas`). |
| Telas | `web/src/pages/`, `web/src/components/` | Desenhar cada tela, abas, filtros e diálogos em React. |
| Navegação e estilos | `web/src/core/`, `web/public/css/` | Navegação sem recarga, envio de formulários com CSRF e folhas de estilo de cada tela. |

### Implantação com containers

```mermaid
flowchart LR
    Browser["Navegador"] -->|localhost:5000| App["Serviço app / flask_app\nAPI Flask + telas React :5000"]
    App -->|db:5432| DB["Serviço db / postgres_db\nPostgres 16"]
    DB --> Dados[(postgres_data)]
    App --> Uploads[(uploads_data)]
    Web["Build da aplicação web (web/)"] -->|Copiado na imagem, /static/dist| App
```

O serviço `app` é construído pelo `api/Dockerfile` (um estágio Node gera o build de `web/` e o estágio Python serve a API e esse build) e depende do estado saudável de `db`. O serviço `db` usa a imagem `postgres:16-alpine`. A aplicação acessa o banco pelo nome do serviço na rede interna do Compose; os volumes mantêm os dados e os anexos entre reinicializações.

### Organização dos dados

| Grupo | Modelos e vínculos |
| --- | --- |
| Identidade | `UsuarioModel` armazena e-mail, hash de senha e perfil. `AlunoModel` e `ProfessorModel` armazenam os dados específicos e referenciam o usuário. |
| Organização acadêmica | `TurmaModel` e `DisciplinaModel`, ligados por `TurmaDisciplinaModel`. Os vínculos de participação ficam em `AlunoTurmaModel`, `ProfessorTurmaModel` e `ProfessorDisciplinaModel`; também existe `AlunoDisciplinaModel`. |
| Ensino | `AtividadeModel` relaciona professor, turma e disciplina. `NotaModel` relaciona aluno, professor e disciplina, com unicidade por aluno/disciplina. |
| Comunicação | `ComunicadoModel` armazena os recados publicados pela secretaria. |
| Documentação | `DocumentoModel` registra os metadados dos arquivos. `SolicitacaoDocumentoModel` registra destinatário, status e eventual documento enviado. Os arquivos ficam na pasta de uploads. |

## Telas do sistema

O catálogo abaixo descreve as telas implementadas e aponta para seus componentes React. Para visualizá-las em funcionamento, execute a aplicação e entre com o perfil correspondente. As abas dos painéis de professor e aluno são seções da mesma página.

### Login

| Tela | Rota | Conteúdo e ações |
| --- | --- | --- |
| [Login](web/src/pages/login.jsx) | `/` | Campos de e-mail institucional e senha. Após autenticar, o usuário é direcionado ao painel de seu perfil. |

### Secretaria / administrador

| Tela | Rota principal | Conteúdo e ações |
| --- | --- | --- |
| [Dashboard da secretaria](web/src/pages/admin_painel.jsx) | `/admin/dashboard` | Saudação, totais de alunos e professores, matrículas pendentes e últimos registros. Menu lateral para as áreas administrativas. |
| [Cadastro de alunos](web/src/pages/admin_cadastro_aluno.jsx) | `/admin/cadastro-alunos` | Dados pessoais e acadêmicos, matrícula, credenciais de acesso e foto de perfil. |
| [Cadastro de professores](web/src/pages/admin_cadastro_professores.jsx) | `/admin/cadastro-professores` | Nome, CPF, contato, disciplina principal, formação, regime de trabalho, admissão, credenciais e foto. |
| [Banco de dados](web/src/pages/admin_banco_dados.jsx) | `/admin/banco-de-dados` | Indicadores, listagem de registros acadêmicos e busca por nome ou ID, com acesso aos detalhes dos cadastros. É uma tela de consulta de pessoas, sem editor SQL. |
| [Detalhes do aluno](web/src/pages/admin_detalhes_aluno.jsx) | `/admin/alunos/<aluno_id>` | Perfil, edição cadastral, solicitações de documentos e arquivos enviados. |
| [Detalhes do professor](web/src/pages/admin_detalhes_professor.jsx) | `/admin/professores/<professor_id>` | Perfil e edição cadastral, aba de atuação e aba de documentos com solicitações e arquivos enviados. |
| [Disciplinas](web/src/pages/admin_disciplinas.jsx) | `/admin/disciplinas` | Criação com nome, código e carga horária; listagem e associação de professores. |
| [Turmas](web/src/pages/admin_turmas.jsx) | `/admin/turmas` | Cadastro e listagem de turmas, associação de alunos e professores e consulta das disciplinas vinculadas. |
| [Comunicados](web/src/pages/admin_comunicados.jsx) | `/admin/comunicados` | Formulário com título e mensagem e consulta dos recados publicados. |

### Professor

O [painel do professor](web/src/pages/professor_painel.jsx), em `/professor/dashboard` (também `/professor`), reúne:

| Aba | Conteúdo e ações |
| --- | --- |
| Turmas | Turmas vinculadas, alunos, disciplinas e lançamento de atividades, com possibilidade de anexar arquivo. |
| Notas | Formulários de lançamento por aluno e disciplina, nota de 0 a 10, observação e consulta das notas lançadas. |
| Documentos | Solicitações da secretaria, envio do arquivo de resposta e consulta dos documentos enviados. |

### Aluno

| Tela | Rota principal | Conteúdo e ações |
| --- | --- | --- |
| [Painel do aluno](web/src/pages/aluno_painel.jsx) | `/aluno/dashboard` (também `/aluno`) | Abas de disciplinas, notas e documentos. Exibe as disciplinas associadas, as notas e observações e as solicitações de documentos, com upload de resposta e arquivos enviados. |
| [Detalhes da disciplina](web/src/pages/aluno_disciplina.jsx) | `/aluno/disciplinas/<disciplina_id>` | Informações da disciplina, professores e atividades com arquivos disponíveis para download. |

### Navegação entre as telas

```mermaid
flowchart TD
    Login["Login /"] --> Perfil{"Perfil autenticado"}
    Perfil -->|admin| Admin["Dashboard da secretaria"]
    Perfil -->|professor| Professor["Painel do professor"]
    Perfil -->|aluno| Aluno["Painel do aluno"]
    Admin --> Cadastros["Cadastro de alunos e professores"]
    Admin --> Registros["Banco de dados"]
    Registros --> Detalhes["Detalhes de aluno ou professor"]
    Detalhes --> Documentos["Solicitar e consultar documentos"]
    Admin --> Organizacao["Turmas e disciplinas"]
    Admin --> Comunicados["Comunicados"]
    Professor --> PT["Turmas e atividades"]
    Professor --> PN["Notas"]
    Professor --> PD["Documentos"]
    Aluno --> AD["Disciplinas"]
    AD --> Disciplina["Detalhes da disciplina e atividades"]
    Aluno --> AN["Notas"]
    Aluno --> AQ["Documentos"]
```

Para percorrer as telas com conteúdo, cadastre os usuários, configure as associações acadêmicas e lance dados conforme o [fluxo inicial](docs/DOCUMENTACAO_DO_SISTEMA.md#104-preparação-funcional). Listagens sem registros apresentam estados vazios; os dados exibidos dependem do perfil e dos vínculos cadastrados.

## Estrutura do repositório

```text
Projeto-Educa-Fast/
├── docs/       # Documentação: integrantes, BMC, modelo de dados, casos de uso, testes e protótipo
├── api/        # API Flask (dados, regras e permissões; serve o build da web)
├── web/        # Aplicação web React/Vite (todas as telas)
├── .github/    # CI (GitHub Actions)
├── iniciar-educafast.ps1 / .cmd      # Atalhos para o ambiente de teste manual (Windows)
├── iniciar-educafast.sh / .command  # Ambiente de teste manual com tutorial guiado (macOS)
├── LICENSE
└── README.md
```

Cada aplicação tem seu próprio `README.md`, com instalação, configuração e execução logo no início.

## Como executar

Com Docker, o build da aplicação web é feito automaticamente junto com a API. Siga o passo a passo de [`api/README.md`](api/README.md); para desenvolver as telas, veja [`web/README.md`](web/README.md). Resumo com Docker:

```bash
cd api
cp .env.example .env   # preencha SECRET_KEY, DATA_ENCRYPTION_KEY, DB_PASSWORD e MYSQL_ROOT_PASSWORD
docker compose up -d --build
docker compose exec app python -m app.seed
```

Depois acesse [http://localhost:5000](http://localhost:5000).

Sem Docker, gere o build da web (`npm ci` e `npm run build` em `web/`) antes de iniciar a API.

## Validação e limites atuais

O repositório inclui regressão automatizada, cenários de segurança/LGPD e coleção Postman. Consulte [Testes](docs/testes/README.md). Para o fluxo manual, entre com cada perfil, configure os vínculos de turma/disciplina e confira os controles de acesso e privacidade em banco descartável.

O Compose local usa Gunicorn, sem depuração, e publica a aplicação somente em loopback. Para produção com HTTPS e TLS verificado no Postgres (o arquivo `certs/pg_hba.conf` deve aceitar somente `hostssl`), use o arquivo independente `api/docker-compose.production.yml`, após preparar chaves e certificados conforme [Segurança e LGPD](docs/SEGURANCA_E_LGPD.md). Não publique o servidor de desenvolvimento.

## Documentação e licença

- [Documentação completa do sistema](docs/DOCUMENTACAO_DO_SISTEMA.md)
- [Segurança, criptografia e LGPD — configuração e responsabilidades](docs/SEGURANCA_E_LGPD.md)
- [Testes de API/Postman e regressão](docs/testes/README.md)
- [Iniciar o ambiente manual](docs/testes/TESTE_MANUAL.md#iniciar-o-ambiente-em-segundo-plano): execute `.\iniciar-educafast.ps1` no PowerShell ou `.\iniciar-educafast.cmd` no CMD, na raiz do projeto. No macOS, dê dois cliques em `iniciar-educafast.command` ([detalhes](docs/testes/TESTE_MANUAL.md#iniciar-no-macos-com-tutorial-guiado)).
- [Especificação de casos de uso](docs/Especificação%20de%20Casos%20de%20Uso.md)
- [Documentos do projeto](docs/) — integrantes e vídeo em [docs/README.md](docs/README.md)
- [Business Model Canvas](docs/BMC.md) e [modelo de dados](docs/DADOS.md) ([PDF](docs/DADOS.pdf))
- [Referência do protótipo](docs/prototipo/)
- [Licença MIT](LICENSE)
