# Sistema de Gestão da Secretaria Escolar DF

O Sistema de Gestão da Secretaria Escolar DF é uma plataforma digital desenvolvida para apoiar as atividades administrativas de instituições de ensino, centralizando e organizando informações acadêmicas e administrativas.

## Estrutura do projeto

```text
Códigos/
|-- app/
|   |-- controllers/
|   |-- models/
|   |-- routes/
|   |-- static/
|   |   |-- css/
|   |   `-- js/
|   |       |-- compartilhado/
|   |       `-- paginas/
|   |-- templates/
|   |   `-- partials/
|   `-- views/
|-- app.py
|-- config.py
|-- docker-compose.yml
|-- Dockerfile
`-- requirements.txt
```

## Tecnologias
- HTML5
- React 18 via CDN
- Tailwind CSS
- Python 3.12
- Flask
- SQLAlchemy (ORM)
- PyMySQL
- cryptography
- MySQL 8.4
- Docker e Docker Compose

## Requisitos

- Docker
- Docker Compose

## Como executar

1. Entre na pasta `Códigos`:

```bash
cd Códigos
```

2. Crie o arquivo de ambiente a partir do exemplo:

```bash
cp .env.example .env
```

3. Edite o `.env` e defina valores seguros para:
- `SECRET_KEY`
- `DB_PASSWORD`
- `MYSQL_ROOT_PASSWORD`

4. Suba os serviços:

```bash
docker compose up -d --build
```

5. Verifique se os containers estão rodando:

```bash
docker compose ps
```

6. Execute o seed para criar o usuário administrador inicial:

```bash
docker compose exec app python -m app.seed
```

7. Acesse a aplicação em `http://localhost:5000`.
8. O MySQL ficará disponível na porta `3306`.

Credenciais padrão geradas pelo script de seed (recomenda-se alterar para maior segurança):
- Email: `admin@admin.com`
- Senha: `123`

## Containers

- `app`: container da aplicação Flask
- `db`: container do MySQL

## Banco de dados

As tabelas são criadas automaticamente pelo ORM (SQLAlchemy) na inicialização da aplicação.

Importante:
- As variáveis `MYSQL_*` e criação de usuário/banco são aplicadas na primeira inicialização do volume do MySQL.
- Se você trocar senha no `.env` depois disso, será necessário recriar o volume:

```bash
docker compose down -v
docker compose up -d --build
```

## Configuração

As configurações da aplicação ficam em `config.py` e são lidas de variáveis de ambiente:

- `SECRET_KEY`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `MYSQL_ROOT_PASSWORD` (usada pelo container do MySQL)

No ambiente Docker, as variáveis são lidas do arquivo `.env` via `docker-compose.yml`.

## Arquitetura

- `app/controllers`: concentra regras de aplicação e operações de cadastro, documentos e dashboards
- `app/models`: concentra regras de negócio e acesso aos dados
- `app/routes`: organiza e registra as rotas da aplicação
- `app/views`: centraliza a renderização das respostas
- `app/templates`: armazena os templates HTML/Jinja usados pelo React Shell
- `app/templates/partials`: armazena trechos compartilhados de template, como o runtime do React
- `app/static/css`: guarda os estilos por área/página
- `app/static/js/compartilhado`: guarda JavaScript compartilhado
- `app/static/js/paginas`: guarda JavaScript específico de cada página

## Comandos úteis

Ver containers:

```bash
docker compose ps
```

Ver logs da aplicação:

```bash
docker compose logs -f app
```

Executar seed:

```bash
docker compose exec app python -m app.seed
```

Parar os containers:

```bash
docker compose down
```
