# Contexto: raiz do repositório (docker compose usa context: ..).
# 1) Build da aplicação React (web/) — gera api/app/static/dist.
FROM node:22-alpine AS web
WORKDIR /build/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# 2) API Flask, que também serve o build do React.
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY api/ .
COPY --from=web /build/api/app/static/dist ./app/static/dist

EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:create_app()"]
