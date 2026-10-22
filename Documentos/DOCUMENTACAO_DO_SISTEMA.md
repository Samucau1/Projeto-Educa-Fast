# Documentação do sistema — Educa Fast

**Sistema:** Educa Fast / Secretaria Escolar DF  
**Data da análise:** 21/10/2026  
**Código de referência:** commit `d148af1`  
**Escopo:** documentação funcional, técnica e operacional da implementação atual.

Este documento complementa o [README](../README.md). Foi elaborado pela leitura de rotas, controllers, modelos, templates, scripts e configuração. Descreve o código encontrado; não constitui relatório de execução de testes de ponta a ponta. As limitações e diferenças em relação aos requisitos estão registradas explicitamente.

## Índice

1. [Visão geral e perfis](#1-visão-geral-e-perfis)
2. [Tecnologias](#2-tecnologias)
3. [Arquitetura e componentes](#3-arquitetura-e-componentes)
4. [Inicialização e configuração](#4-inicialização-e-configuração)
5. [Modelo de dados](#5-modelo-de-dados)
6. [Regras de negócio e fluxos](#6-regras-de-negócio-e-fluxos)
7. [Telas e navegação](#7-telas-e-navegação)
8. [Contratos HTTP](#8-contratos-http)
9. [Autenticação e arquivos](#9-autenticação-e-arquivos)
10. [Instalação e operação](#10-instalação-e-operação)
11. [Validação manual](#11-validação-manual)
12. [Limitações e evolução](#12-limitações-e-evolução)
13. [Manutenção e referências](#13-manutenção-e-referências)
14. [Inventário completo de rotas](#14-inventário-completo-de-rotas)
15. [Dicionário de colunas](#15-dicionário-de-colunas)

## 1. Visão geral e perfis

A aplicação apoia a secretaria escolar, reunindo cadastros, organização acadêmica, comunicação e documentos. O administrador prepara o ambiente; professores registram atividades e notas; alunos consultam informações e respondem a solicitações documentais.

Os perfis reconhecidos são `admin`, `professor` e `aluno`. Secretário e direção, citados nos casos de uso, não são perfis separados na implementação.

| Recurso | Administrador | Professor | Aluno |
| --- | --- | --- | --- |
| Painel administrativo e consulta de cadastros | Sim | Não | Não |
| Cadastro pelas rotas específicas e edição de pessoas | Sim | Não | Não |
| Criar disciplinas, turmas e associações | Sim | Não | Não |
| Publicar comunicados | Sim | Não | Não |
| Lançar atividades e notas | Não pelas rotas de professor | Sim, com vínculos validados | Não |
| Consultar disciplinas pelo painel do aluno | Não pelo painel do aluno | Não pelo painel do aluno | Conforme suas turmas |
| Solicitar documentos | Sim | Não | Não |
| Responder à própria solicitação | Não pelo painel do destinatário | Sim | Sim |
| Busca JSON de alunos | Não com JWT admin | Sim, com JWT professor | Não |

A tabela descreve os fluxos principais. Existem exceções na implementação: o cadastro genérico é público e o download com JWT tem regras diferentes do download por sessão. Consulte a seção 9.

Não foram encontrados módulos de frequência, cobrança, biblioteca, recuperação de senha ou entrega de respostas de atividades pelo aluno. Upload de documento é um fluxo diferente de entrega de atividade.

## 2. Tecnologias

| Componente | Versão/configuração no repositório | Uso |
| --- | --- | --- |
| Python | `3.12-slim` no Dockerfile | Backend |
| Flask | `3.1.0` | HTTP, blueprints, sessão e templates |
| SQLAlchemy | `2.0.44` | ORM, consultas e transações |
| PyMySQL | `1.1.2` | Conexão com MySQL |
| python-dotenv | `1.0.1` | Leitura de `.env` |
| cryptography | `>=42,<46` | Dependência criptográfica do ambiente Python |
| Werkzeug | Dependência do Flask | Hash de senha e sanitização de nomes de arquivos |
| MySQL | `8.4` no Compose | Banco relacional |
| React / ReactDOM | `18`, UMD via unpkg | Montagem do shell das páginas |
| Tailwind CSS | Script CDN | Estilização utilitária |
| HTML5, CSS, JavaScript e Jinja | Sem build frontend próprio | Interface |
| Docker e Docker Compose | Serviços `app` e `db` | Ambiente integrado |

As dependências estão em [requirements.txt](../Códigos/requirements.txt). Não existe etapa necessária de `npm install` ou compilação JSX na interface atual.

## 3. Arquitetura e componentes

### 3.1 Organização em camadas

```mermaid
flowchart TD
    Cliente["Navegador"] --> Rotas["Blueprints Flask"]
    Rotas --> Guardas["Sessão / guards / JWT"]
    Guardas --> Controle["Controllers"]
    Controle --> Modelos["Modelos SQLAlchemy"]
    Modelos <--> Banco[(MySQL)]
    Controle --> HTML["Views e templates Jinja"]
    HTML --> React["Shell React e scripts de página"]
    React --> Cliente
    Controle -->|JSON ou redirecionamento| Cliente
    Controle <--> Uploads["Pasta de uploads"]
```

A separação lembra MVC. As views dedicadas atendem à home e ao painel administrativo; outras rotas chamam `render_template()` diretamente.

| Local em `Códigos/` | Responsabilidade |
| --- | --- |
| `app.py` | Criar a aplicação e iniciar o servidor em `0.0.0.0:5000`, com debug. |
| `app/__init__.py` | Fábrica `create_app()`, configuração, banco e blueprints. |
| `config.py` | Variáveis de ambiente e URL de conexão. |
| `app/database.py` | Engine, `SessionLocal`, base declarativa e ajustes de esquema. |
| `app/routes/` | Entrada HTTP, guardas e construção de respostas. |
| `app/controllers/` | Validações, consultas e operações de aplicação. |
| `app/models/` | Tabelas, colunas, relações e restrições. |
| `app/views/` | Renderização da home e do dashboard administrativo. |
| `app/templates/` | Páginas HTML/Jinja. |
| `app/templates/partials/` | Runtime compartilhado de React. |
| `app/static/js/compartilhado/` | Shell React, abas e eventos compartilhados. |
| `app/static/js/paginas/` | Scripts de login, cadastro e consulta de registros. |
| `app/static/css/` | Estilos gerais e por tela. |
| `app/seed.py` | Exclusão de usuários e criação do administrador de demonstração. |

### 3.2 Divisão dos controllers

| Controller | Operações |
| --- | --- |
| `auth_controller.py` | Login, cadastros, foto de perfil e busca de alunos. |
| `admin_controller.py` | Indicadores, comunicados, disciplinas, turmas, associações, edição e solicitações de documentos. |
| `professor_controller.py` | Painel do professor, atividades, notas e resposta documental. |
| `aluno_controller.py` | Painel do aluno, detalhes da disciplina e conclusão de solicitação. |
| `document_controller.py` | Pasta de uploads, disciplina geral e upload de documento de aluno. |

### 3.3 Interface

Jinja gera o HTML no servidor. `shell_react.js` lê o template da página e insere o conteúdo usando `dangerouslySetInnerHTML`. Após montar, inicializa abas e dispara `react-shell:mounted`; scripts de página vinculam seus eventos a essa montagem.

O React atua como shell do conteúdo renderizado. As páginas dependem de recursos externos para montagem e estilos. Conteúdo nessa estrutura deve continuar recebendo escape adequado no servidor.

### 3.4 Containers

```mermaid
flowchart LR
    Navegador -->|localhost:5000| App["app / flask_app"]
    App -->|db:3306| DB["db / mysql_db"]
    SQL["Cliente SQL no host"] -->|localhost:3306| DB
    Codigo["Códigos no host"] -->|/app| App
    App -->|/app/uploads| Arquivos[(uploads_data)]
    DB -->|/var/lib/mysql| Dados[(mysql_data)]
```

`app` é construído pelo Dockerfile e espera o healthcheck de `db`. Ambos usam `restart: unless-stopped`. O código é montado em `/app`; dados e uploads usam volumes nomeados.

## 4. Inicialização e configuração

### 4.1 Sequência de inicialização

1. `app.py` importa `create_app()`; `Config` carrega `.env`.
2. Os modelos são importados e registram suas tabelas na base declarativa.
3. A fábrica cria Flask e aplica os atributos de `Config`.
4. `init_db()` cria tabelas ausentes e aplica ajustes pontuais.
5. `register_routes()` registra home, autenticação, professor, aluno e documentos.
6. A execução direta inicia o servidor de desenvolvimento na porta 5000.

O banco precisa estar acessível na criação da aplicação. Não existe comando separado obrigatório de migração antes de iniciar.

### 4.2 Variáveis de ambiente

| Variável | Padrão no código | Comportamento |
| --- | --- | --- |
| `SECRET_KEY` | `desenvolvimento-web-flask` | Assina sessão e JWT; obrigatória no Compose. |
| `JWT_EXPIRATION_HOURS` | `8` | Inteiro; validade do JWT em horas. |
| `UPLOAD_FOLDER` | `uploads` | Pasta resolvida com `os.path.abspath()`. |
| `DB_HOST` | `localhost` | O Compose define `db`. |
| `DB_PORT` | `3306` | Inteiro; porta de conexão Python. |
| `DB_USER` | `root` | O Compose usa `app_user` como padrão. |
| `DB_PASSWORD` | Vazio | Obrigatória no Compose. |
| `DB_NAME` | `app_web` | Nome do banco. |
| `DB_URL` | Não definida | Substitui a URL composta com `DB_*` quando informada. |
| `MYSQL_ROOT_PASSWORD` | Sem padrão no Compose | Senha root para inicialização do MySQL. |

A URL composta segue `mysql+pymysql://usuario:senha@host:porta/banco`. Caracteres reservados em credenciais precisam de codificação adequada; `DB_URL` permite informar a conexão completa.

O Compose injeta as variáveis declaradas no serviço. `JWT_EXPIRATION_HOURS` e `DB_URL` não estão nesse bloco, mas podem ser carregadas do `.env` montado em `/app`. O dotenv padrão não sobrescreve variáveis já existentes no processo.

Mudar `DB_PORT` não muda a porta interna do MySQL nem o mapeamento fixo `3306:3306`. Para alterar somente a porta no host, ajuste o lado esquerdo do mapeamento e mantenha a conexão entre containers na porta interna correta.

## 5. Modelo de dados

### 5.1 Entidades e restrições

São 15 tabelas, todas com `id` inteiro, chave primária autoincremental. O dicionário completo de declarações de coluna está na seção 15.

| Tabela | Dados armazenados | Restrições relevantes |
| --- | --- | --- |
| `usuarios` | E-mail, hash de senha e tipo | E-mail único; tipo é texto, não enum. |
| `alunos` | Usuário, nome, CPF, matrícula, curso/série, status, foto, nascimento e criação | Usuário e matrícula únicos; CPF único opcional. |
| `professores` | Usuário, nome, CPF, contato, disciplina principal, formação, regime, foto, admissão e criação | Usuário único; CPF único obrigatório. |
| `disciplinas` | Nome, código e carga horária | Código único. |
| `turmas` | Nome, código, ano letivo e turno | Código único. |
| `alunos_turmas` | Aluno, turma e criação | Par aluno/turma único. |
| `professores_turmas` | Professor, turma e criação | Par professor/turma único. |
| `professores_disciplinas` | Professor, disciplina e criação | Par professor/disciplina único. |
| `turmas_disciplinas` | Turma, disciplina e criação | Par turma/disciplina único. |
| `alunos_disciplinas` | Aluno, disciplina e criação | Par aluno/disciplina único; o painel atual deriva disciplinas pelas turmas. |
| `notas` | Aluno, professor, disciplina, nota, observação e data | Par aluno/disciplina único; nota `DECIMAL(4,2)`; sem turma ou período. |
| `atividades` | Professor, turma, disciplina, título, descrição, entrega, arquivo e criação | Entrega é `VARCHAR(10)` opcional; anexo opcional. |
| `comunicados` | Título, destinatário, mensagem, autor e criação | Destinatário/autor são texto, sem chaves estrangeiras. |
| `documentos` | Aluno, professor, disciplina, título, arquivo e envio | Aluno e professor opcionais; disciplina obrigatória. |
| `solicitacoes_documentos` | Destinatário, documento, título, mensagem, status, criação e conclusão | Status inicial `pendente`; destinatários/documento opcionais no esquema. |

O fluxo define um destinatário por solicitação, mas o esquema não exige exatamente um entre aluno e professor. Um documento pode associar aluno e professor simultaneamente quando o professor envia arquivo de aluno, ou apenas professor quando é um documento pessoal.

### 5.2 Relacionamentos

```mermaid
erDiagram
    USUARIOS ||--o| ALUNOS : identifica
    USUARIOS ||--o| PROFESSORES : identifica
    ALUNOS ||--o{ ALUNOS_TURMAS : participa
    TURMAS ||--o{ ALUNOS_TURMAS : recebe
    PROFESSORES ||--o{ PROFESSORES_TURMAS : leciona
    TURMAS ||--o{ PROFESSORES_TURMAS : recebe
    PROFESSORES ||--o{ PROFESSORES_DISCIPLINAS : ensina
    DISCIPLINAS ||--o{ PROFESSORES_DISCIPLINAS : possui
    TURMAS ||--o{ TURMAS_DISCIPLINAS : oferece
    DISCIPLINAS ||--o{ TURMAS_DISCIPLINAS : integra
    ALUNOS ||--o{ ALUNOS_DISCIPLINAS : vincula
    DISCIPLINAS ||--o{ ALUNOS_DISCIPLINAS : vincula
    ALUNOS ||--o{ NOTAS : recebe
    DISCIPLINAS ||--o{ NOTAS : avalia
    PROFESSORES ||--o{ NOTAS : registra
    PROFESSORES ||--o{ ATIVIDADES : cria
    TURMAS ||--o{ ATIVIDADES : recebe
    DISCIPLINAS ||--o{ ATIVIDADES : organiza
    ALUNOS o|--o{ DOCUMENTOS : possui
    PROFESSORES o|--o{ DOCUMENTOS : possui
    DISCIPLINAS ||--o{ DOCUMENTOS : classifica
    ALUNOS o|--o{ SOLICITACOES_DOCUMENTOS : recebe
    PROFESSORES o|--o{ SOLICITACOES_DOCUMENTOS : recebe
    DOCUMENTOS o|--o{ SOLICITACOES_DOCUMENTOS : responde
```

O diagrama expressa as chaves estrangeiras. `comunicados` é independente dessas relações.

### 5.3 Sessões, esquema e datas

`database.py` usa `pool_pre_ping=True`, `autocommit=False` e `autoflush=False`. Controllers abrem sessões, executam operações e fecham as sessões em `finally`; em operações tratadas há rollback quando necessário. Não há uma transação global única por requisição.

`create_all()` cria tabelas ausentes. `_ensure_schema_updates()` adiciona campos específicos de alunos, professores, solicitações e atividades e pode alterar a nulabilidade de destinatários no MySQL. Não há migrações versionadas nem reconciliação completa de tipos e índices de bases antigas. O usuário do banco precisa das permissões exigidas pelos ajustes executados.

Vários timestamps usam padrão do servidor. O JWT usa UTC, mas outros fluxos usam `datetime.now()` e `date.today()`, sem política centralizada de timezone. A atualização de nota não renova explicitamente sua data original de lançamento.

## 6. Regras de negócio e fluxos

### 6.1 Login e saída

O navegador envia JSON a `POST /login`. O controller busca o usuário, verifica o hash com Werkzeug, normaliza o perfil e emite JWT. A rota grava `user_id`, `user_email` e `user_role` na sessão. O JavaScript direciona `ADMIN` para `/admin/dashboard`, `PROFESSOR` para `/professor` e `ALUNO` para `/aluno`.

O script de login não armazena o JWT retornado; a navegação usa a sessão. `GET /logout` limpa a sessão e redireciona para `/`, mas não revoga JWTs emitidos.

### 6.2 Pessoas e fotos

| Operação | Obrigatórios no controller | Observações |
| --- | --- | --- |
| Cadastrar aluno | Tipo aluno, e-mail, senha, nome e matrícula | CPF, nascimento, curso, status e foto opcionais. |
| Cadastrar professor | Tipo professor, e-mail, senha, nome e CPF | Contato, disciplina principal, formação, regime, admissão e foto opcionais. |
| Editar aluno | Nome, e-mail e matrícula | Atualiza dados e foto; não altera senha. |
| Editar professor | Nome, e-mail e CPF | Atualiza dados e foto; não altera senha. |

O cadastro aceita `tipo` ou `role`, apenas aluno/professor. Há aliases de campos como `curso`, `status`, `disciplina`, `formacao`, `regime` e `admissao`. Datas usam `YYYY-MM-DD`. Campos exigidos pela interface podem ser mais restritivos que os exigidos pelo controller.

Usuário e perfil são criados na mesma transação. Duplicidade de e-mail, matrícula ou CPF gera conflito. A foto aceita JPG/JPEG/PNG por extensão até 2 MiB, com UUID no nome; a edição remove a anterior após persistir a substituição.

`disciplina_principal` é texto descritivo: não cria o vínculo professor/disciplina.

### 6.3 Disciplinas, turmas e associações

- Disciplina exige nome, código e carga horária inteira não negativa.
- Turma exige nome, código e ano letivo inteiro maior ou igual a 2000; turno é opcional.
- Códigos são normalizados para maiúsculas; códigos duplicados geram conflito.
- Associação aluno/turma e professor/disciplina valida existência e evita duplicidade do par.
- Professor precisa de ao menos uma disciplina associada para entrar em uma turma.
- Ao associar professor/turma, o sistema acrescenta à turma suas disciplinas atuais ainda não vinculadas.

Vincular outra disciplina ao professor posteriormente não sincroniza automaticamente todas as turmas anteriores. O painel do aluno deriva as disciplinas de `alunos_turmas` e `turmas_disciplinas`, não de `alunos_disciplinas`.

### 6.4 Atividades

Exige turma, disciplina e título; descrição, entrega e arquivo são opcionais. Verifica professor existente, professor na turma, professor na disciplina e disciplina na turma. O título é limitado a 150 caracteres na atribuição. O prazo é cortado para 10 caracteres, sem validação completa de calendário nessa função.

O anexo usa prefixo `atividade_`, UUID e nome sanitizado. Em exceção de persistência há rollback e tentativa de remoção do arquivo. Alunos consultam atividades das turmas e disciplinas disponíveis a eles. Não há entrega de atividade pelo aluno.

### 6.5 Notas

Recebe aluno, turma, disciplina, nota e observação opcional. Converte nota para `Decimal`, aceita vírgula na entrada e compara ao intervalo 0–10. Verifica aluno na turma, professor na turma, professor na disciplina e disciplina na turma.

O registro é buscado por aluno/disciplina: se existir, atualiza nota, professor e observação; caso contrário, insere. Não há notas por bimestre, atividade, turma ou ano, nem histórico de versões. A observação é limitada a 255 caracteres na atribuição.

### 6.6 Comunicados

Título e mensagem são obrigatórios. Destinatário usa `Geral` como padrão e o autor vem do e-mail da sessão. A operação grava no banco; não envia e-mail nem mensagens externas. O destinatário é classificação textual, sem associação relacional a usuários.

### 6.7 Documentos

```mermaid
sequenceDiagram
    participant S as Secretaria
    participant F as Flask
    participant B as Banco
    participant U as Aluno ou professor
    participant A as Uploads
    S->>F: Solicita documento com título e instruções
    F->>B: Cria solicitação pendente
    U->>F: Consulta seu painel
    F->>B: Busca solicitações do destinatário
    U->>F: Envia solicitacao_id e arquivo
    F->>B: Valida titularidade
    F->>A: Salva arquivo com nome único
    F->>B: Registra documento e conclusão
    F-->>U: Redireciona ao painel
```

A solicitação exige título e destinatário existente. A resposta exige ID da solicitação e arquivo e verifica seu destinatário. Os estados usados são `pendente` e `enviado`; `completed_at` registra conclusão. Não há aprovação/rejeição nem bloqueio por status de solicitação já respondida.

No fluxo de professor, documento e conclusão compartilham uma transação. No fluxo de aluno, o documento é salvo antes e a solicitação é atualizada em outra sessão/transação; falha entre essas etapas pode deixar arquivo/documento sem concluir a solicitação.

Sem disciplina explícita, os documentos usam `GERAL` / `Geral`, carga zero, criada quando necessário. O administrador também pode anexar documentos diretamente a alunos e professores.

### 6.8 Indicadores e limites

O painel conta alunos, professores, alunos de status `pendente` e cadastros de aluno criados na data atual. “Matrículas hoje” usa `created_at` do aluno; não há entidade separada de evento de matrícula.

| Consulta | Limite encontrado |
| --- | --- |
| Alunos/professores no contexto administrativo | 100 / 20 |
| Últimos registros administrativos | 8 |
| Busca JSON de alunos | 20 |
| Documentos e solicitações no painel do aluno | 12 por consulta |
| Atividades agregadas no painel do aluno | 80 |
| Atividades no painel do professor | 60 |
| Notas, documentos e solicitações no painel do professor | 30 por consulta |

Há outros limites nas consultas de detalhes e associações. Não existe paginação de servidor que permita percorrer necessariamente toda a base nessas listagens.

## 7. Telas e navegação

São 13 templates de página, além do parcial React. Os links abrem os arquivos-fonte; não são capturas de tela.

| Tela | Rota principal | Template e conteúdo |
| --- | --- | --- |
| Login | `/` | [login.html](../Códigos/app/templates/login.html): e-mail, senha e erros. |
| Dashboard administrativo | `/admin/dashboard` | [admin_painel.html](../Códigos/app/templates/admin_painel.html): indicadores e últimos registros. |
| Cadastro de aluno | `/admin/cadastro-alunos` | [admin_cadastro_aluno.html](../Códigos/app/templates/admin_cadastro_aluno.html): dados pessoais/acadêmicos, acesso e foto. |
| Cadastro de professor | `/admin/cadastro-professores` | [admin_cadastro_professores.html](../Códigos/app/templates/admin_cadastro_professores.html): dados profissionais, acesso e foto. |
| Consulta de registros | `/admin/banco-de-dados` | [admin_banco_dados.html](../Códigos/app/templates/admin_banco_dados.html): indicadores, pesquisa e acesso aos detalhes; não é console SQL. |
| Detalhes do aluno | `/admin/alunos/<aluno_id>` | [admin_detalhes_aluno.html](../Códigos/app/templates/admin_detalhes_aluno.html): perfil, edição e documentos. |
| Detalhes do professor | `/admin/professores/<professor_id>` | [admin_detalhes_professor.html](../Códigos/app/templates/admin_detalhes_professor.html): perfil, edição, atuação e documentos. |
| Disciplinas | `/admin/disciplinas` | [admin_disciplinas.html](../Códigos/app/templates/admin_disciplinas.html): cadastro, listagem e vínculo de professor. |
| Turmas | `/admin/turmas` | [admin_turmas.html](../Códigos/app/templates/admin_turmas.html): cadastro, alunos, professores e disciplinas. |
| Comunicados | `/admin/comunicados` | [admin_comunicados.html](../Códigos/app/templates/admin_comunicados.html): publicação e recados anteriores. |
| Professor | `/professor` | [professor_painel.html](../Códigos/app/templates/professor_painel.html): abas Turmas, Notas e Documentos. |
| Aluno | `/aluno` | [aluno_painel.html](../Códigos/app/templates/aluno_painel.html): abas Disciplinas, Notas e Documentos. |
| Disciplina do aluno | `/aluno/disciplinas/<disciplina_id>` | [aluno_disciplina.html](../Códigos/app/templates/aluno_disciplina.html): professores, atividades e arquivos. |

Login leva ao painel do perfil. A secretaria navega pelo menu lateral, abre registros e seus detalhes. Professor e aluno alternam abas na mesma página; o aluno abre uma disciplina em página própria. Telas sem registros exibem estados vazios.

O `dashboard.html` da raiz é avulso. A rota `/dashboard.html` é um alias protegido que renderiza `app/templates/admin_painel.html`, não o arquivo da raiz.

## 8. Contratos HTTP

### 8.1 Convenções e respostas

Há HTML, JSON, formulários e multipart, sem prefixo único `/api`. IDs com conversor `<int:...>` são inteiros; arquivos usam `<path:filename>`. Erros JSON normalmente usam `{"erro": "mensagem"}`; guardas de páginas podem retornar HTML.

| Status | Uso |
| --- | --- |
| 200 | Consulta, login e atualização. |
| 201 | Criação/cadastro/upload com resposta JSON. |
| 302 | Redirecionamento após formulário ou logout. |
| 400 | Campo ausente/valor inválido tratado. |
| 401 | JWT ausente/inválido/expirado ou senha inválida. |
| 403 | Perfil sem acesso ou vínculo acadêmico insuficiente. |
| 404 | Entidade/arquivo inexistente ou indisponível no contexto. |
| 409 | Duplicidade de dado ou associação. |
| 415 | Pode ocorrer em `/login` sem corpo identificado como JSON. |
| 500 | Exceção não tratada; não há formato global padronizado. |

Erros de turmas, disciplinas e comunicados podem aparecer no HTML com status 200, mesmo que o controller produza 400/409 internamente. Rotas administrativas de edição/solicitação redirecionam sem propagar explicitamente a falha retornada pelo controller; redirecionamento isolado não comprova gravação.

### 8.2 Login, cadastro e busca

| Método e rota | Entrada | Acesso e saída |
| --- | --- | --- |
| `POST /login` | JSON `email`, `senha` | Público; cria sessão; retorna `id`, `email`, `tipo` maiúsculo, `role` minúsculo e `token`. |
| `GET /logout` | Sem corpo | Limpa sessão e redireciona. |
| `POST /cadastro` | JSON/formulário com `tipo`/`role` e dados do perfil | Público na implementação; aceita aluno/professor. |
| `POST /cadastro/aluno` ou `/cadastro/alunos` | Dados de aluno | Sessão admin; força tipo aluno. |
| `POST /cadastro/professor` ou `/cadastro/professores` | Dados de professor | Sessão admin; força tipo professor. |
| `GET /professor/teste` | Bearer JWT | JWT professor; mensagem de permissão validada. |
| `GET /alunos/busca` | Query `termo`, `q` ou `cpf`, nessa precedência | JWT professor; busca parcial em nome/CPF, até 20 resultados. |

Exemplo de login:

```json
{"email": "professor@exemplo.com", "senha": "senha-definida-no-cadastro"}
```

Cadastro bem-sucedido retorna `id`, `email`, `tipo` e `role`. Para foto, use multipart com `foto_perfil`. A busca retorna `alunos` com `id`, `usuario_id`, `nome`, `cpf`, `matricula` e `data_nascimento` ISO ou nula; não restringe por turma do professor.

### 8.3 Formulários administrativos

Todas as operações abaixo são POST e exigem sessão admin.

| Rota | Campos | Operação |
| --- | --- | --- |
| `/admin/disciplinas` | `nome`, `codigo`, `carga_horaria` | Criar disciplina. |
| `/admin/disciplinas` | `action=associate_teacher`, `professor_id`, `disciplina_id` | Associar professor. |
| `/admin/turmas` | `nome`, `codigo`, `ano_letivo`, `turno` opcional | Criar turma. |
| `/admin/turmas` | `action=associate_student`, `aluno_id`, `turma_id` | Associar aluno. |
| `/admin/turmas` | `action=associate_teacher`, `professor_id`, `turma_id` | Associar professor e acrescentar disciplinas. |
| `/admin/comunicados` | `titulo`, `mensagem`, `destinatario` opcional | Publicar comunicado. |
| `/admin/alunos/<aluno_id>/editar` | Dados editáveis de aluno e foto opcional | Atualizar aluno. |
| `/admin/professores/<professor_id>/editar` | Dados editáveis de professor e foto opcional | Atualizar professor. |
| `/admin/alunos/<aluno_id>/documentos/solicitar` | `titulo`, `mensagem` opcional | Solicitar documento de aluno. |
| `/admin/professores/<professor_id>/documentos/solicitar` | `titulo`, `mensagem` opcional | Solicitar documento de professor. |

### 8.4 Ensino e arquivos

| Método e rota | Entrada | Acesso/retorno |
| --- | --- | --- |
| `POST /professor/notas/salvar` | `aluno_id`, `turma_id`, `disciplina_id`, `nota`, `observacao` opcional | Sessão professor; sucesso redireciona; falha JSON. |
| `POST /professor/atividades/lancar` | `turma_id`, `disciplina_id`, `titulo`; `descricao`, `data_entrega`, `arquivo` opcionais | Sessão professor; multipart com anexo; sucesso redireciona. |
| `POST /professor/documentos/upload` | Multipart `solicitacao_id`, `arquivo` | Sessão professor; sucesso redireciona. |
| `POST /aluno/documentos/upload` | Multipart `solicitacao_id`, `arquivo` | Sessão aluno; sucesso redireciona. |
| `POST /arquivos/upload` | Multipart `aluno_id`, `arquivo`; `disciplina_id`, `titulo`, `redirect_to` opcionais | Sessão admin ou JWT professor; retorna documento ou redireciona. |
| `POST /professores/<professor_id>/arquivos/upload` | Multipart `arquivo`; `titulo`, `redirect_to` opcionais | Sessão admin; documento pessoal do professor. |
| `GET /arquivos/download/<path:filename>` | Nome persistido do arquivo | Download; regras na seção 9. |
| `GET /arquivos/perfil/<path:filename>` | Nome iniciado com `perfil_` | Imagem sem autenticação. |

Upload genérico retorna `mensagem` e `documento` com `id`, `titulo`, `arquivo`, `aluno_id`, `professor_id` e `disciplina_id`.

Todos os aliases estão na seção 14. A rota estática automática do Flask vem de `app/static` e não aparece nos decoradores do inventário.

## 9. Autenticação e arquivos

### 9.1 Sessão e JWT

A sessão usa o mecanismo padrão de cookie assinado do Flask. As guardas comparam `user_role`. Um JWT isolado não cria uma sessão de navegador nem autentica automaticamente as páginas.

O JWT é implementado em `auth.py` com JSON, Base64 URL-safe e HMAC-SHA256 da biblioteca padrão. Cabeçalho: `alg=HS256`, `typ=JWT`. Payload: `sub` textual, `email`, `role`, `tipo` e `exp`. Usa a mesma `SECRET_KEY` da sessão e exige `Authorization: Bearer <token>`.

A validação verifica assinatura, cabeçalho e expiração. Não consulta o usuário a cada chamada, não implementa renovação/lista de revogação e não atualiza automaticamente o perfil de tokens existentes. A validação de tipos do payload não cobre todas as estruturas JSON possíveis.

### 9.2 Regras de arquivos

| Contexto | Verificação encontrada |
| --- | --- |
| Foto | Extensão JPG/JPEG/PNG, até 2 MiB, prefixo `perfil_`, UUID e nome sanitizado. |
| Documento/anexo | Arquivo e nome presentes; `secure_filename()` e UUID; sem limite geral de tamanho, MIME ou extensão. |
| Download por sessão aluno | Documento do próprio aluno ou atividade de turma do aluno. |
| Download por sessão professor | Documento associado ao professor ou atividade criada por ele. |
| Download por sessão admin | Acesso ao arquivo solicitado dentro da pasta de uploads. |
| Download sem perfil de sessão reconhecido | JWT válido, sem posterior verificação de perfil/titularidade do arquivo. |
| Foto de perfil | Nome sanitizado com prefixo `perfil_`; rota pública. |

O upload genérico com JWT professor verifica a existência de professor, aluno e disciplina, mas não os vínculos acadêmicos entre eles. O download de atividade por aluno verifica turma, sem revalidar o vínculo de disciplina nessa etapa.

Os nomes ficam no banco e os binários na pasta configurada. `send_from_directory()` serve o conteúdo. UUID reduz colisões; não substitui autorização.

### 9.3 Pontos a revisar antes de produção

- Cadastro genérico público, diferentemente das rotas administrativas específicas.
- Download com JWT sem verificação de titularidade e upload genérico sem validação de vínculo acadêmico.
- Ausência de proteção CSRF explícita e limitação de tentativas de login.
- Ausência de recuperação de senha e revogação de JWT.
- Chave padrão conhecida e senha de demonstração do seed.
- Anexos/documentos sem política geral de tamanho e conteúdo.
- `redirect_to` validado apenas por começar com `/`, admitindo também caminhos iniciados com `//`.
- Servidor com debug e banco publicado no host.

São observações estáticas do código, não resultados de exploração. Este documento não modifica os controles de acesso.

## 10. Instalação e operação

### 10.1 Docker Compose

Requer Git, Docker, Docker Compose e portas 5000/3306 disponíveis.

```bash
git clone https://github.com/Samucau1/Projeto-Educa-Fast.git
cd Projeto-Educa-Fast
cd "Códigos"
```

Copie o exemplo. No PowerShell:

```powershell
Copy-Item .env.example .env
```

No Linux/macOS, use `cp .env.example .env`. Substitua `SECRET_KEY`, `DB_PASSWORD` e `MYSQL_ROOT_PASSWORD`. Não publique `.env` com credenciais reais.

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f app db
```

O MySQL inicializa banco/usuário em volume vazio. Seu healthcheck tem intervalo de 10 segundos, timeout de 5 segundos, 10 tentativas e período inicial de 20 segundos. Após o backend iniciar, acesse `http://localhost:5000`.

### 10.2 Administrador inicial

> O seed exclui todos os usuários antes de inserir o administrador. Use apenas em um banco novo de desenvolvimento. Com dados vinculados, pode falhar por integridade referencial. Não é criação idempotente de acesso nem reset completo da base.

Depois de a aplicação criar as tabelas:

```bash
docker compose exec app python -m app.seed
```

Credenciais fixas: `admin@admin.com` / `123`. O seed não cria pessoas, turmas ou disciplinas. Os valores devem ser substituídos no script antes de uso fora de demonstração; não há variáveis de ambiente para as credenciais do seed.

### 10.3 Sem Docker

Prepare MySQL com banco e usuário. Em `Códigos/`, crie `.env` e configure `DB_HOST=localhost` e as credenciais locais.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

No Linux/macOS, ative com `source .venv/bin/activate`. Depois da criação das tabelas, rode `python -m app.seed` em outro terminal com o ambiente ativo, observando o aviso anterior.

### 10.4 Preparação funcional

1. Entre como administrador e cadastre professor e aluno com acessos próprios.
2. Crie disciplina e associe o professor a ela.
3. Crie turma e associe o professor; suas disciplinas serão acrescentadas à turma.
4. Associe o aluno à turma.
5. Entre como professor e registre atividade e nota.
6. Entre como aluno e consulte os registros.
7. Solicite documentos pela secretaria e responda pelos dois perfis.

### 10.5 Persistência e backup

`mysql_data` mantém `/var/lib/mysql`; `uploads_data` mantém `/app/uploads`. Mantenha `UPLOAD_FOLDER=uploads` para o volume configurado na execução em `/app`.

`docker compose down` preserva os volumes. **`docker compose down -v` apaga também banco e uploads.** Não é um procedimento de atualização que preserve dados.

As variáveis MySQL de criação de banco/usuários atuam apenas na primeira inicialização de um volume vazio. Alterar `.env` não modifica as senhas já persistidas: ajuste também os usuários no MySQL.

Backup completo exige exportação consistente do banco e cópia dos uploads. Restaurar apenas o banco não recupera os binários. Não há rotina automatizada de backup/restauração no repositório; valide a recuperação em ambiente separado.

### 10.6 Manutenção e diagnóstico

```bash
# Estado e logs, dentro de Códigos/
docker compose ps
docker compose logs -f app db

# Reconstruir imagem e atualizar serviços
docker compose up -d --build

# Parar preservando dados
docker compose down
```

| Sintoma | Conferir |
| --- | --- |
| Falha de banco | Healthcheck, credenciais persistidas, host e porta. |
| Porta ocupada | Serviços em 5000/3306 e mapeamento do host. |
| Cadastro rejeitado | Obrigatórios, duplicatas, datas e foto. |
| Professor sem opções acadêmicas | Associações de disciplina e turma; texto de disciplina principal não basta. |
| Aluno sem disciplinas | Vínculo aluno/turma e disciplinas da turma. |
| Nota/atividade com 403 | Vínculos professor/turma/disciplina e aluno/turma para nota. |
| Página sem montagem/estilo | Console do navegador e acesso às CDNs. |
| Arquivo não encontrado | Nome persistido, existência do binário e volume/pasta. |
| Painel com 403 | Sessão e perfil; JWT sozinho não autentica páginas. |

## 11. Validação manual

Não há suíte automatizada de testes no repositório analisado. Este é um roteiro proposto para base descartável, não um relatório de testes executados.

| Cenário | Verificação esperada |
| --- | --- |
| Inicializar Compose | Banco saudável, app iniciado, tabelas criadas. |
| Login válido/inválido | Painel correto ou erro apropriado. |
| Acesso cruzado de perfil | Aluno não acessa painel administrativo. |
| Cadastro e duplicatas | Criação válida; conflito sem usuário parcial. |
| Foto válida e maior que 2 MiB | Aceita formato/tamanho permitido e rejeita excesso. |
| Editar dados e substituir foto | Alterações persistidas e foto antiga removida após sucesso. |
| Configurar associações | Professor e aluno visualizam as opções correspondentes. |
| Professor sem disciplinas na turma | Operação rejeitada. |
| Atividade com anexo | Aluno da turma consulta e baixa o arquivo. |
| Notas 0, 10 e fora da faixa | Limites respeitados; atualização mantém um registro aluno/disciplina. |
| Nota/atividade com vínculo inválido | Operação bloqueada. |
| Comunicado | Registro persistido e disponível na consulta correspondente. |
| Documento de aluno/professor | Solicitação, envio e arquivo acessível; estado enviado. |
| Download de outro usuário por sessão | Bloqueio conforme filtros implementados. |
| JWT ausente, alterado, expirado ou perfil incorreto | 401/403 nas rotas de professor apropriadas. |
| Reiniciar sem remover volumes | Cadastros e arquivos preservados. |

Os pontos da seção 9 também precisam de testes específicos antes de considerar o sistema adequado para produção.

## 12. Limitações e evolução

### 12.1 Requisitos e implementação

A [Especificação de Casos de Uso](Especificação%20de%20Casos%20de%20Uso.md) prevê secretário/direção, remoção de registros e gerenciamento de usuários. No código, a administração usa o perfil `admin`; há cadastro, consulta e edição, mas não foram encontradas rotas de exclusão de pessoas/usuários. A exclusão do seed não implementa esse caso de uso. Também não há fluxo próprio de troca/recuperação de senha.

### 12.2 Evoluções possíveis

| Área | Limite atual | Evolução proposta |
| --- | --- | --- |
| Acesso | Exceções em cadastro, download JWT e upload genérico | Unificar autorização e titularidade. |
| Notas | Uma nota por aluno/disciplina, sem histórico/período | Avaliações e períodos com auditoria. |
| Documentos | Pendente/enviado, reenvio, duas transações no fluxo aluno | Revisão documental e atomicidade. |
| Listagens | Limites fixos | Paginação e filtros de servidor. |
| Esquema | Criação e ajustes pontuais | Migrações versionadas. |
| Formulários | Algumas falhas ignoradas no redirecionamento | Retorno consistente e mensagens de validação. |
| Prazo de atividade | Texto truncado | Tipo e validação de calendário. |
| Comunicados | Persistência sem envio externo | Definir segmentação e notificações, se necessárias. |
| Implantação | Flask debug, bind mount, banco no host | Servidor/configuração de produção. |
| Qualidade | Sem suíte automatizada | Testar acesso, vínculos, transações e fluxos. |
| Operação | Backup e observabilidade não automatizados | Procedimentos verificáveis e monitoramento. |

As evoluções são propostas e não estão implementadas por este documento.

## 13. Manutenção e referências

Ao alterar funcionalidade, confira rota e guardas, controller, modelos e template/script correspondente. Valide falhas e transações além do sucesso. Alterar um modelo não faz `create_all()` atualizar todas as colunas de tabelas existentes.

Novas telas devem considerar runtime React, evento de montagem e estilos. Mudanças de acesso precisam cobrir sessão e JWT. Atualize esta documentação quando modificar contratos, campos ou regras.

- [README](../README.md)
- [Casos de uso](Especificação%20de%20Casos%20de%20Uso.md)
- [Protótipo](../Protótipo/)
- [Configuração](../Códigos/config.py)
- [Docker Compose](../Códigos/docker-compose.yml)
- [Rotas](../Códigos/app/routes/)
- [Controllers](../Códigos/app/controllers/)
- [Modelos](../Códigos/app/models/)
- [Templates](../Códigos/app/templates/)
- [Licença MIT](../LICENSE)

Há também um plano de negócios na pasta de documentos. Os materiais de produto complementam os objetivos; o comportamento descrito aqui se baseia no código local analisado.

## 14. Inventário completo de rotas

As tabelas abaixo transcrevem os decoradores encontrados nos arquivos de rotas, incluindo aliases. Métodos automáticos HEAD/OPTIONS não são listados separadamente. A autorização e os contratos são descritos nas seções 8 e 9.

### aluno_routes.py

Fonte: [aluno_routes.py](../Códigos/app/routes/aluno_routes.py).

| Métodos | Caminho | Handler |
| --- | --- | --- |
| `GET` | `/aluno` | `dashboard` |
| `GET` | `/aluno/dashboard` | `dashboard` |
| `GET` | `/aluno/disciplinas/<int:disciplina_id>` | `disciplina_detail` |
| `POST` | `/aluno/documentos/upload` | `upload_documento_aluno` |

### auth_routes.py

Fonte: [auth_routes.py](../Códigos/app/routes/auth_routes.py).

| Métodos | Caminho | Handler |
| --- | --- | --- |
| `POST` | `/login` | `login` |
| `GET` | `/logout` | `logout` |
| `POST` | `/cadastro` | `cadastro` |
| `POST` | `/cadastro/aluno` | `cadastro_aluno` |
| `POST` | `/cadastro/alunos` | `cadastro_aluno` |
| `POST` | `/cadastro/professor` | `cadastro_professor` |
| `POST` | `/cadastro/professores` | `cadastro_professor` |
| `GET` | `/professor/teste` | `teste_professor` |
| `GET` | `/alunos/busca` | `alunos_busca` |

### document_routes.py

Fonte: [document_routes.py](../Códigos/app/routes/document_routes.py).

| Métodos | Caminho | Handler |
| --- | --- | --- |
| `POST` | `/arquivos/upload` | `upload_arquivo` |
| `GET` | `/arquivos/download/<path:filename>` | `download_arquivo` |
| `POST` | `/professores/<int:professor_id>/arquivos/upload` | `upload_arquivo_professor` |
| `GET` | `/arquivos/perfil/<path:filename>` | `perfil_arquivo` |

### home_routes.py

Fonte: [home_routes.py](../Códigos/app/routes/home_routes.py).

| Métodos | Caminho | Handler |
| --- | --- | --- |
| `GET` | `/` | `home` |
| `GET` | `/dashboard` | `admin_dashboard` |
| `GET` | `/dashboard.html` | `admin_dashboard` |
| `GET` | `/admin/dashboard` | `admin_dashboard` |
| `GET` | `/admin_painel.html` | `admin_dashboard` |
| `GET` | `/cadastro/alunos` | `admin_cadastro_alunos` |
| `GET` | `/cadastro_aluno.html` | `admin_cadastro_alunos` |
| `GET` | `/admin/cadastro-alunos` | `admin_cadastro_alunos` |
| `GET` | `/admin_cadastro_aluno.html` | `admin_cadastro_alunos` |
| `GET` | `/cadastro/professores` | `admin_cadastro_professores` |
| `GET` | `/cadastro_professores.html` | `admin_cadastro_professores` |
| `GET` | `/admin/cadastro-professores` | `admin_cadastro_professores` |
| `GET` | `/admin_cadastro_professores.html` | `admin_cadastro_professores` |
| `GET` | `/banco-de-dados` | `admin_banco_dados` |
| `GET` | `/banco_de_dados.html` | `admin_banco_dados` |
| `GET` | `/admin/banco-de-dados` | `admin_banco_dados` |
| `GET` | `/admin_banco_dados.html` | `admin_banco_dados` |
| `GET,POST` | `/comunicados` | `admin_comunicados` |
| `GET,POST` | `/admin/comunicados` | `admin_comunicados` |
| `GET,POST` | `/admin_comunicados.html` | `admin_comunicados` |
| `GET,POST` | `/disciplinas` | `admin_disciplinas` |
| `GET,POST` | `/admin/disciplinas` | `admin_disciplinas` |
| `GET,POST` | `/admin_disciplinas.html` | `admin_disciplinas` |
| `GET,POST` | `/turmas` | `admin_turmas` |
| `GET,POST` | `/admin/turmas` | `admin_turmas` |
| `GET,POST` | `/admin_turmas.html` | `admin_turmas` |
| `GET` | `/alunos/<int:aluno_id>` | `admin_detalhes_aluno` |
| `GET` | `/detalhes_aluno/<int:aluno_id>` | `admin_detalhes_aluno` |
| `GET` | `/admin/alunos/<int:aluno_id>` | `admin_detalhes_aluno` |
| `GET` | `/admin_detalhes_aluno/<int:aluno_id>` | `admin_detalhes_aluno` |
| `POST` | `/admin/alunos/<int:aluno_id>/documentos/solicitar` | `admin_solicitar_documento_aluno` |
| `POST` | `/admin/alunos/<int:aluno_id>/editar` | `admin_editar_aluno` |
| `GET` | `/professores/<int:professor_id>` | `admin_detalhes_professor` |
| `GET` | `/detalhes_professor/<int:professor_id>` | `admin_detalhes_professor` |
| `GET` | `/admin/professores/<int:professor_id>` | `admin_detalhes_professor` |
| `GET` | `/admin_detalhes_professor/<int:professor_id>` | `admin_detalhes_professor` |
| `POST` | `/admin/professores/<int:professor_id>/editar` | `admin_editar_professor` |
| `POST` | `/admin/professores/<int:professor_id>/documentos/solicitar` | `admin_solicitar_documento_professor` |
| `GET` | `/detalhes_aluno.html` | `admin_detalhes_aluno_legacy` |
| `GET` | `/admin_detalhes_aluno.html` | `admin_detalhes_aluno_legacy` |
| `GET` | `/detalhes_professor.html` | `admin_detalhes_professor_legacy` |
| `GET` | `/admin_detalhes_professor.html` | `admin_detalhes_professor_legacy` |

### professor_routes.py

Fonte: [professor_routes.py](../Códigos/app/routes/professor_routes.py).

| Métodos | Caminho | Handler |
| --- | --- | --- |
| `GET` | `/professor` | `dashboard` |
| `GET` | `/professor/dashboard` | `dashboard` |
| `POST` | `/professor/notas/salvar` | `salvar_nota` |
| `POST` | `/professor/atividades/lancar` | `lancar_atividade` |
| `POST` | `/professor/documentos/upload` | `upload_documento_professor` |

## 15. Dicionário de colunas

Transcrição das declarações `mapped_column()` dos modelos, com tipos, nulabilidade, padrões e chaves. Nas anotações Python, `str | None` indica um valor opcional. `String(n)` limita o campo a n caracteres; `ForeignKey` indica a referência. As restrições compostas de unicidade estão resumidas na seção 5.


### alunos_disciplinas

Fonte: [aluno_disciplina_model.py](../Códigos/app/models/aluno_disciplina_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `aluno_id` | `int` | `mapped_column(Integer, ForeignKey("alunos.id"), nullable=False)` |
| `disciplina_id` | `int` | `mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### alunos

Fonte: [aluno_model.py](../Códigos/app/models/aluno_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `usuario_id` | `int` | `mapped_column( Integer, ForeignKey("usuarios.id"), unique=True, nullable=False, )` |
| `nome` | `str` | `mapped_column(String(120), nullable=False)` |
| `cpf` | `str \| None` | `mapped_column(String(14), unique=True, nullable=True)` |
| `matricula` | `str` | `mapped_column(String(30), unique=True, nullable=False)` |
| `curso_serie` | `str \| None` | `mapped_column(String(80), nullable=True)` |
| `status_matricula` | `str \| None` | `mapped_column(String(20), nullable=True)` |
| `foto_perfil` | `str \| None` | `mapped_column(String(255), nullable=True)` |
| `data_nascimento` | `date \| None` | `mapped_column(Date, nullable=True)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### alunos_turmas

Fonte: [aluno_turma_model.py](../Códigos/app/models/aluno_turma_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `aluno_id` | `int` | `mapped_column(Integer, ForeignKey("alunos.id"), nullable=False)` |
| `turma_id` | `int` | `mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### atividades

Fonte: [atividade_model.py](../Códigos/app/models/atividade_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `professor_id` | `int` | `mapped_column(Integer, ForeignKey("professores.id"), nullable=False)` |
| `turma_id` | `int` | `mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)` |
| `disciplina_id` | `int` | `mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)` |
| `titulo` | `str` | `mapped_column(String(150), nullable=False)` |
| `descricao` | `str \| None` | `mapped_column(Text, nullable=True)` |
| `data_entrega` | `str \| None` | `mapped_column(String(10), nullable=True)` |
| `caminho_arquivo` | `str \| None` | `mapped_column(String(255), nullable=True)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### comunicados

Fonte: [comunicado_model.py](../Códigos/app/models/comunicado_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `titulo` | `str` | `mapped_column(String(150), nullable=False)` |
| `destinatario` | `str` | `mapped_column(String(80), nullable=False)` |
| `mensagem` | `str` | `mapped_column(Text, nullable=False)` |
| `criado_por` | `str \| None` | `mapped_column(String(120), nullable=True)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### disciplinas

Fonte: [disciplina_model.py](../Códigos/app/models/disciplina_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `nome` | `str` | `mapped_column(String(120), nullable=False)` |
| `codigo` | `str` | `mapped_column(String(30), unique=True, nullable=False)` |
| `carga_horaria` | `int` | `mapped_column(Integer, nullable=False)` |

### documentos

Fonte: [documento_model.py](../Códigos/app/models/documento_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `aluno_id` | `int \| None` | `mapped_column(Integer, ForeignKey("alunos.id"), nullable=True)` |
| `professor_id` | `int \| None` | `mapped_column(Integer, ForeignKey("professores.id"), nullable=True)` |
| `disciplina_id` | `int` | `mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)` |
| `titulo` | `str` | `mapped_column(String(150), nullable=False)` |
| `caminho_arquivo` | `str` | `mapped_column(String(255), nullable=False)` |
| `data_envio` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### notas

Fonte: [nota_model.py](../Códigos/app/models/nota_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `aluno_id` | `int` | `mapped_column(Integer, ForeignKey("alunos.id"), nullable=False)` |
| `disciplina_id` | `int` | `mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)` |
| `professor_id` | `int` | `mapped_column(Integer, ForeignKey("professores.id"), nullable=False)` |
| `nota` | `float` | `mapped_column(DECIMAL(4, 2), nullable=False)` |
| `observacao` | `str \| None` | `mapped_column(String(255), nullable=True)` |
| `data_lancamento` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### professores_disciplinas

Fonte: [professor_disciplina_model.py](../Códigos/app/models/professor_disciplina_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `professor_id` | `int` | `mapped_column(Integer, ForeignKey("professores.id"), nullable=False)` |
| `disciplina_id` | `int` | `mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### professores

Fonte: [professor_model.py](../Códigos/app/models/professor_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `usuario_id` | `int` | `mapped_column( Integer, ForeignKey("usuarios.id"), unique=True, nullable=False, )` |
| `nome` | `str` | `mapped_column(String(120), nullable=False)` |
| `cpf` | `str` | `mapped_column(String(14), unique=True, nullable=False)` |
| `telefone` | `str \| None` | `mapped_column(String(20), nullable=True)` |
| `disciplina_principal` | `str \| None` | `mapped_column(String(80), nullable=True)` |
| `formacao_academica` | `str \| None` | `mapped_column(String(120), nullable=True)` |
| `regime_trabalho` | `str \| None` | `mapped_column(String(50), nullable=True)` |
| `foto_perfil` | `str \| None` | `mapped_column(String(255), nullable=True)` |
| `data_admissao` | `date \| None` | `mapped_column(Date, nullable=True)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### professores_turmas

Fonte: [professor_turma_model.py](../Códigos/app/models/professor_turma_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `professor_id` | `int` | `mapped_column(Integer, ForeignKey("professores.id"), nullable=False)` |
| `turma_id` | `int` | `mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### solicitacoes_documentos

Fonte: [solicitacao_documento_model.py](../Códigos/app/models/solicitacao_documento_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `aluno_id` | `int \| None` | `mapped_column(Integer, ForeignKey("alunos.id"), nullable=True)` |
| `professor_id` | `int \| None` | `mapped_column(Integer, ForeignKey("professores.id"), nullable=True)` |
| `documento_id` | `int \| None` | `mapped_column(Integer, ForeignKey("documentos.id"), nullable=True)` |
| `titulo` | `str` | `mapped_column(String(150), nullable=False)` |
| `mensagem` | `str \| None` | `mapped_column(Text, nullable=True)` |
| `status` | `str` | `mapped_column(String(20), nullable=False, default="pendente")` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |
| `completed_at` | `str \| None` | `mapped_column(TIMESTAMP, nullable=True)` |

### turmas_disciplinas

Fonte: [turma_disciplina_model.py](../Códigos/app/models/turma_disciplina_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `turma_id` | `int` | `mapped_column(Integer, ForeignKey("turmas.id"), nullable=False)` |
| `disciplina_id` | `int` | `mapped_column(Integer, ForeignKey("disciplinas.id"), nullable=False)` |
| `created_at` | `str` | `mapped_column(TIMESTAMP, server_default=func.current_timestamp())` |

### turmas

Fonte: [turma_model.py](../Códigos/app/models/turma_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `nome` | `str` | `mapped_column(String(120), nullable=False)` |
| `codigo` | `str` | `mapped_column(String(30), unique=True, nullable=False)` |
| `ano_letivo` | `int` | `mapped_column(Integer, nullable=False)` |
| `turno` | `str \| None` | `mapped_column(String(30), nullable=True)` |

### usuarios

Fonte: [usuario_model.py](../Códigos/app/models/usuario_model.py).

| Coluna | Tipo Python | Declaração SQLAlchemy |
| --- | --- | --- |
| `id` | `int` | `mapped_column(Integer, primary_key=True, autoincrement=True)` |
| `email` | `str` | `mapped_column(String(120), unique=True, nullable=False)` |
| `senha` | `str` | `mapped_column(String(200), nullable=False)` |
| `tipo` | `str` | `mapped_column(String(20), nullable=False)` |
