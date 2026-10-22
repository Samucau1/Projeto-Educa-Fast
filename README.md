# Educa Fast — Secretaria Escolar DF

Sistema web de gestão escolar que centraliza cadastros, turmas, disciplinas, comunicados, notas, atividades e documentos. A aplicação possui áreas para a secretaria (administrador), professores e alunos.

## Funcionalidades

| Perfil | Recursos implementados |
| --- | --- |
| Administrador | Consultar o painel da secretaria; cadastrar e editar alunos e professores; criar disciplinas e turmas; associar alunos e professores às turmas e professores às disciplinas; publicar comunicados; solicitar, enviar e consultar documentos. |
| Professor | Consultar turmas e alunos vinculados; lançar atividades com anexos; registrar ou atualizar notas; consultar comunicados; enviar documentos solicitados pela secretaria. |
| Aluno | Consultar disciplinas, notas, atividades e comunicados; baixar arquivos disponíveis; enviar documentos solicitados pela secretaria. |

Os cadastros incluem dados específicos de cada perfil e foto opcional em JPG ou PNG de até 2 MB. As notas devem estar entre 0 e 10, com validação dos vínculos entre professor, aluno, turma e disciplina. Existe uma nota por aluno e disciplina; um novo lançamento atualiza esse registro.

## Tecnologias e arquitetura

- **Backend:** Python 3.12, Flask 3.1 e templates Jinja.
- **Banco:** SQLAlchemy 2.0, PyMySQL e MySQL 8.4.
- **Interface:** HTML, CSS, JavaScript, Tailwind CSS e React 18 via CDN.
- **Ambiente:** Docker, Docker Compose e python-dotenv.

O ponto de entrada `Códigos/app.py` chama `create_app()`, carrega a configuração, inicializa o banco e registra os blueprints. As rotas encaminham as operações aos controllers, que consultam os modelos SQLAlchemy e retornam páginas ou respostas JSON.

O HTML é renderizado no servidor com Jinja. Um shell React monta esse conteúdo no navegador, e scripts compartilhados e por página controlam abas, formulários e interações. Não há etapa de build com Node.js. O navegador precisa de internet para carregar as dependências externas da interface.

O login verifica senhas armazenadas como hash pelo Werkzeug, estabelece uma sessão Flask e retorna um JWT HS256. As páginas verificam o perfil pela sessão; algumas rotas JSON exigem o cabeçalho `Authorization: Bearer <token>`.

## Estrutura

```text
Projeto-Educa-Fast/
├── Códigos/
│   ├── app/
│   │   ├── controllers/    # Operações de cadastro, gestão e painéis
│   │   ├── models/         # Entidades e relacionamentos SQLAlchemy
│   │   ├── routes/         # Blueprints e verificações de acesso
│   │   ├── static/         # CSS e JavaScript compartilhado/por página
│   │   ├── templates/      # Páginas Jinja e runtime React
│   │   ├── views/          # Funções de renderização
│   │   ├── auth.py         # Geração e validação de JWT
│   │   ├── database.py     # Engine, sessões e inicialização do esquema
│   │   └── seed.py         # Administrador de demonstração
│   ├── app.py
│   ├── config.py
│   ├── .env.example
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
├── Documentos/             # Casos de uso e plano de negócios
├── Protótipo/              # Referência do protótipo no Figma
├── dashboard.html          # HTML avulso; não inicia a aplicação
├── LICENSE
└── README.md
```

## Executar com Docker Compose

Requisitos: Git, Docker e Docker Compose (comando `docker compose`). As portas `5000` e `3306` precisam estar disponíveis.

### 1. Obter o projeto

```bash
git clone https://github.com/Samucau1/Projeto-Educa-Fast.git
cd Projeto-Educa-Fast
cd "Códigos"
```

### 2. Configurar o ambiente

Copie o exemplo para `.env`. No PowerShell:

```powershell
Copy-Item .env.example .env
```

No Linux/macOS:

```bash
cp .env.example .env
```

Edite `.env` e substitua `SECRET_KEY`, `DB_PASSWORD` e `MYSQL_ROOT_PASSWORD` por valores próprios. Não publique credenciais reais.

### 3. Iniciar os serviços

Execute dentro de `Códigos/`:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f app
```

O serviço `app` aguarda o healthcheck do MySQL antes de iniciar. Na inicialização, a aplicação cria as tabelas e aplica os ajustes de esquema previstos em `app/database.py`.

### 4. Criar o administrador em um banco novo

> **Atenção:** o seed executa a exclusão de todos os registros de usuários antes de inserir o administrador. Use apenas na preparação de um banco novo de desenvolvimento. Reexecutá-lo em uma base com dados pode apagar acessos ou falhar por vínculos de chave estrangeira. O script não cria alunos, professores, disciplinas nem turmas.

Após a aplicação inicializar as tabelas:

```bash
docker compose exec app python -m app.seed
```

Acesse [http://localhost:5000](http://localhost:5000) com as credenciais de demonstração:

| Campo | Valor |
| --- | --- |
| E-mail | `admin@admin.com` |
| Senha | `123` |

Esses valores estão fixos em `app/seed.py`. Antes de utilizar o seed em outro ambiente, substitua as credenciais no script.

### 5. Preparar o fluxo escolar

1. Entre como administrador e cadastre alunos e professores, definindo seus acessos.
2. Crie disciplinas e vincule os professores responsáveis.
3. Crie turmas com suas disciplinas e associe alunos e professores.
4. Entre como professor para lançar atividades e notas nas turmas vinculadas.
5. Entre como aluno para consultar as informações acadêmicas.
6. Pela secretaria, solicite documentos; o destinatário poderá enviá-los em seu painel.

## Executar localmente sem Docker

Use Python 3.12 e uma instância MySQL com banco e usuário previamente criados. Dentro de `Códigos/`, copie `.env.example` para `.env` e configure `DB_HOST=localhost` e as credenciais dessa instância.

No PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

No Linux/macOS, ative o ambiente com `source .venv/bin/activate`. Depois que a aplicação criar as tabelas, execute `python -m app.seed` em outro terminal, dentro de `Códigos/` e com o ambiente virtual ativo, respeitando o aviso de exclusão de usuários acima. A aplicação fica em `http://localhost:5000`.

## Configuração

| Variável | Uso e comportamento |
| --- | --- |
| `SECRET_KEY` | Assina sessões e JWTs; obrigatória no Compose. Use uma chave longa e aleatória. |
| `DB_HOST` | Host MySQL; padrão local `localhost`. O Compose define `db`. |
| `DB_PORT` | Porta de conexão ao MySQL; padrão `3306`. O Compose mantém a publicação fixa `3306:3306`. |
| `DB_USER` | Usuário do banco; padrão local `root`, padrão do Compose `app_user`. |
| `DB_PASSWORD` | Senha do usuário do banco; obrigatória no Compose. |
| `DB_NAME` | Nome do banco; padrão `app_web`. |
| `MYSQL_ROOT_PASSWORD` | Senha administrativa na inicialização do container MySQL; obrigatória no Compose. |
| `JWT_EXPIRATION_HOURS` | Validade do JWT em horas; padrão `8`. |
| `UPLOAD_FOLDER` | Pasta dos arquivos enviados; padrão `uploads`. |
| `DB_URL` | URL SQLAlchemy opcional; substitui a conexão montada com as variáveis `DB_*`. |

Localmente, `config.py` lê o `.env` com `load_dotenv()`. No Docker, o Compose injeta as variáveis declaradas no serviço. `JWT_EXPIRATION_HOURS` e `DB_URL` não são repassadas explicitamente pelo bloco `environment`, mas podem ser lidas do `.env` montado em `/app`.

## Persistência

Os modelos representam usuários, alunos, professores, turmas, disciplinas, seus vínculos, notas, atividades, comunicados, documentos e solicitações de documentos. A inicialização cria o esquema e aplica alterações pontuais; não há ferramenta de migrações versionadas configurada.

No Compose, `mysql_data` persiste o banco e `uploads_data` persiste os arquivos em `/app/uploads`. Mantenha `UPLOAD_FOLDER=uploads` para usar esse volume como configurado. O código local é montado em `/app`.

As variáveis de criação de banco e credenciais do container MySQL são aplicadas na primeira inicialização de um volume vazio. Alterar somente o `.env` não atualiza as senhas de um banco existente; ajuste também os usuários no MySQL. Faça backup do banco e dos arquivos antes de alterações no ambiente.

`docker compose down` preserva os volumes. **Adicionar `-v` remove os volumes declarados, incluindo o banco e os uploads**; não use essa opção se precisar manter os dados.

## Principais rotas

| Método | Caminho | Finalidade |
| --- | --- | --- |
| GET | `/` | Login ou redirecionamento ao painel do perfil autenticado. |
| POST | `/login` | Recebe JSON com `email` e `senha`; retorna JWT e cria sessão. |
| GET | `/logout` | Encerra a sessão Flask. |
| GET | `/admin/dashboard` | Painel da secretaria. |
| GET/POST | `/admin/turmas` | Cadastro de turmas e associações. |
| GET/POST | `/admin/disciplinas` | Disciplinas e vínculo com professores. |
| GET/POST | `/admin/comunicados` | Consulta e publicação de comunicados. |
| GET | `/professor/dashboard` | Painel do professor. |
| POST | `/professor/notas/salvar` | Registro ou atualização de nota. |
| POST | `/professor/atividades/lancar` | Criação de atividade, com anexo opcional. |
| GET | `/aluno/dashboard` | Painel do aluno. |
| GET | `/aluno/disciplinas/<disciplina_id>` | Detalhes de uma disciplina do aluno. |
| GET | `/alunos/busca` | Busca de alunos; exige JWT de professor. |
| POST | `/arquivos/upload` | Upload pela secretaria ou professor autenticado com JWT. |
| GET | `/arquivos/download/<filename>` | Download com verificação de autenticação/acesso. |

Consulte `Códigos/app/routes/` para os demais endpoints e aliases de compatibilidade.

## Comandos úteis

Dentro de `Códigos/`:

```bash
# Estado dos serviços
docker compose ps

# Logs da aplicação e do banco
docker compose logs -f app db

# Reconstruir após alterações nas dependências ou imagem
docker compose up -d --build

# Parar e remover containers, preservando volumes
docker compose down
```

Se a aplicação não iniciar, confira os logs, as credenciais e o estado de `db`. Conflitos nas portas `5000` ou `3306` exigem liberar a porta ou ajustar o mapeamento no Compose.

## Validação e limites atuais

O repositório não inclui uma suíte de testes automatizados. Para verificar o fluxo manualmente, use um banco de desenvolvimento: entre com cada perfil, configure os vínculos de turma/disciplina, lance uma atividade e uma nota, confira a visualização pelo aluno e percorra a solicitação, o envio e o download de um documento.

O comando atual executa o servidor de desenvolvimento Flask com `debug=True`. Uma implantação em produção exige configuração de servidor apropriada, desativação do debug e revisão das credenciais e dos controles de acesso.

## Documentação e licença

- [Especificação de casos de uso](Documentos/Especificação%20de%20Casos%20de%20Uso.md)
- [Documentos do projeto](Documentos/)
- [Referência do protótipo](Protótipo/)
- [Licença MIT](LICENSE)
