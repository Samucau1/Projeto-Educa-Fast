# Educa Fast — API (backend Flask)

API do Educa Fast: dados, regras de negócio e permissões de todas as telas. Ela também serve o build da aplicação web ([`web/`](../web/README.md)), então o sistema completo fica em `http://localhost:5000`.

## Instalação, configuração e execução

### Pré-requisitos

| Forma de execução | Requisitos |
| --- | --- |
| Docker (recomendado) | Git, Docker e Docker Compose (comando `docker compose`), porta `5000` livre |
| Local, sem Docker | Git, Python 3.12, Node.js 22 e npm (build da web), MySQL 8 com banco e usuário criados |

### Dependências

As dependências Python estão em [`requirements.txt`](requirements.txt): Flask, SQLAlchemy, PyMySQL, python-dotenv, cryptography, gunicorn e as demais bibliotecas usadas. As dependências da interface estão em [`web/package.json`](../web/package.json). No Docker, tudo é instalado e compilado automaticamente durante o build da imagem. Fora do Docker, siga os passos 3 e 4 da execução local.

### Variáveis de ambiente

Todos os comandos abaixo são executados **dentro da pasta `api/`**. Copie o exemplo e edite o `.env`:

```bash
cp .env.example .env
```

(No PowerShell: `Copy-Item .env.example .env`.)

Gere as duas chaves obrigatórias e cole os valores no `.env`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

O primeiro comando gera a `SECRET_KEY` e o segundo, a `DATA_ENCRYPTION_KEY`. Se não tiver Python instalado no host, gere as chaves depois do build com `docker compose run --rm app python -c "..."`.

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `SECRET_KEY` | Sim | Assina sessões e JWTs, com no mínimo 32 caracteres aleatórios. |
| `DATA_ENCRYPTION_KEY` | Sim | Chave Fernet que cifra dados pessoais e arquivos. Guarde uma cópia: sem ela, os dados não podem ser lidos. |
| `DB_PASSWORD` | Sim | Senha do usuário do banco. |
| `MYSQL_ROOT_PASSWORD` | Sim (Docker) | Senha root do container MySQL. |
| `DB_HOST` | Não | Host do MySQL. Padrão `localhost`; no Docker, o Compose define `db`. |
| `DB_PORT` | Não | Porta do MySQL. Padrão `3306`. |
| `DB_USER` | Não | Usuário do banco. Padrão `app_user` no Compose e `root` no modo local. |
| `DB_NAME` | Não | Nome do banco. Padrão `app_web`. |
| `DB_URL` | Não | URL SQLAlchemy completa. Substitui as variáveis `DB_*`. |
| `LGPD_CONTROLADOR` / `LGPD_CONTATO` | Não (sim em produção) | Controlador dos dados e contato de privacidade. |
| `APP_ENV` | Não | `development` (padrão) ou `production`. |
| `COOKIE_SECURE` | Não | `1` exige HTTPS nos cookies. Obrigatória em produção. |
| `TRUSTED_HOSTS` | Não | Hosts aceitos. Padrão `localhost,127.0.0.1`. |
| `JWT_EXPIRATION_HOURS` | Não | Validade do JWT em horas. Padrão `8`. |
| `UPLOAD_FOLDER` | Não | Pasta de uploads. Padrão `uploads`. |

### Executar com Docker (recomendado)

O build da imagem compila também a aplicação web (`web/`); por isso o Compose usa a raiz do repositório como contexto.

```bash
docker compose up -d --build
```

```bash
docker compose ps
```

O MySQL sobe junto e as tabelas são criadas na primeira inicialização. Depois crie os acessos iniciais:

```bash
docker compose exec app python -m app.seed
```

```bash
docker compose exec app flask --app app.py criar-superusuario
```

- `app.seed` cria o administrador de demonstração `admin@admin.com` com senha `123`. **Atenção:** ele apaga todos os usuários existentes, por isso use só em banco novo.
- `criar-superusuario` pede e-mail e senha (mínimo de 8 caracteres) e cria o superadmin, responsável pelas configurações institucionais e pelos usuários.

Acesse [http://localhost:5000](http://localhost:5000). Para ver os logs, use `docker compose logs -f app`. Para parar, use `docker compose down`, que mantém os dados. **Não use `-v`**: essa opção apaga o banco e os uploads.

### Executar localmente (sem Docker)

1. Crie no MySQL o banco e o usuário informados no `.env` e defina `DB_HOST=localhost`.
2. Crie e ative o ambiente virtual:

   ```bash
   python -m venv .venv
   ```

   ```bash
   source .venv/bin/activate
   ```

   No Windows (PowerShell), ative com `.\.venv\Scripts\Activate.ps1`.
3. Instale as dependências:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Gere o build da aplicação web (sai em `app/static/dist/`):

   ```bash
   cd ../web && npm ci && npm run build && cd ../api
   ```

5. Inicie a aplicação, que fica em `http://localhost:5000`:

   ```bash
   python app.py
   ```

   Sem o passo 4, a API funciona, mas as telas exibem um aviso de build ausente.

6. Em outro terminal, com o ambiente ativo e as tabelas já criadas, rode `python -m app.seed` e `flask --app app.py criar-superusuario`.

### Executar os testes

Os testes usam SQLite em memória e não precisam de MySQL. Com as dependências instaladas:

```bash
cd tests && PYTHONPATH=.. python -m unittest discover -p "test_*.py" -v
```

As suítes de regressão com MySQL, Postman e estresse estão descritas em [`docs/testes/README.md`](../docs/testes/README.md).

---

## Estrutura

```text
api/
├── app/
│   ├── controllers/    # Regras de cadastro, gestão e painéis
│   ├── models/         # Entidades e relacionamentos SQLAlchemy
│   ├── routes/         # Blueprints e verificações de acesso
│   ├── services/       # Regras acadêmicas, cursos e configuração da escola
│   ├── static/dist/    # Build da aplicação web (gerado; fora do Git)
│   ├── views/          # Telas de entrada, painel e páginas de erro
│   ├── spa.py          # render_page: dados das telas em JSON para a aplicação React
│   ├── auth.py         # Geração e validação de JWT
│   ├── crypto.py       # Criptografia de dados pessoais
│   ├── security.py     # CSRF, cabeçalhos e limites de requisição
│   ├── database.py     # Engine, sessões e inicialização do esquema
│   └── seed.py         # Administrador de demonstração
├── tests/              # Testes automatizados e scripts de validação
├── app.py              # Ponto de entrada
├── config.py           # Leitura das variáveis de ambiente
├── gunicorn.conf.py
├── Dockerfile
├── docker-compose.yml             # Ambiente local (app + MySQL)
├── docker-compose.test.yml        # Ambiente descartável de testes
├── docker-compose.production.yml  # Produção com HTTPS
└── requirements.txt
```

## Principais rotas

As rotas de tela respondem com JSON quando recebem o cabeçalho `X-EducaFast-SPA: 1` (é o que a aplicação web envia) e com o `index.html` da aplicação web quando abertas direto no navegador. `GET /api/rotas` devolve o mapa de rotas usado pela interface para montar os links.

| Método | Caminho | Finalidade |
| --- | --- | --- |
| GET | `/` | Login ou redirecionamento ao painel do perfil autenticado. |
| POST | `/login` | Recebe `email` e `senha`, cria a sessão e retorna um JWT. |
| GET / POST | `/logout` | Confirma e encerra a sessão (POST com CSRF). |
| GET | `/admin/dashboard` | Painel da secretaria. |
| GET/POST | `/admin/turmas`, `/admin/disciplinas`, `/admin/comunicados` | Cadastros e vínculos. |
| GET | `/professor/dashboard` | Painel do professor. |
| POST | `/professor/notas/salvar`, `/professor/atividades/lancar` | Notas e atividades. |
| GET | `/aluno/dashboard` | Painel do aluno. |
| GET/POST | `/super/usuarios`, `/super/layout` | Gestão de usuários e identidade visual (superadmin). |
| POST | `/arquivos/upload` | Upload autenticado. |
| GET | `/arquivos/download/<filename>` | Download com verificação de acesso. |

Os demais endpoints (cursos, diário, escola e privacidade) estão em `app/routes/`.

## Persistência

No Compose, o volume `mysql_data` guarda o banco e o `uploads_data` guarda os arquivos enviados. As variáveis de criação do MySQL valem só na primeira inicialização de um volume vazio. Faça backup do banco, dos uploads **e** da `DATA_ENCRYPTION_KEY` antes de qualquer mudança no ambiente.

Para produção com HTTPS, use `docker-compose.production.yml` conforme [Segurança e LGPD](../docs/SEGURANCA_E_LGPD.md).
