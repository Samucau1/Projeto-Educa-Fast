FROM node:22-bookworm-slim AS newman
RUN npm install --prefix /opt/newman newman@6.2.1 --no-audit --no-fund

FROM python:3.12-slim-bookworm
COPY --from=newman /usr/local/bin/node /usr/local/bin/node
COPY --from=newman /opt/newman /opt/newman
WORKDIR /workspace/Códigos
COPY Códigos/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY Códigos/app ./app
COPY Códigos/app.py Códigos/config.py ./
COPY Códigos/tests ./tests
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 NEWMAN_PATH=/opt/newman/node_modules/newman/bin/newman.js
CMD ["python", "tests/executar_regressao.py"]
