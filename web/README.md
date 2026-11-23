# Educa Fast — Web (React)

Aplicação web em React + Vite que consome a API de [`api/`](../api/README.md).

> **Status: migração em andamento.** As telas em funcionamento hoje são servidas pela própria API (templates Jinja) em `http://localhost:5000`. Para usar o sistema, siga o [README da API](../api/README.md). Esta pasta guarda a base React que vai substituir essas telas.

## Instalação, configuração e execução

### Pré-requisitos

- Node.js 22 (ou 20 LTS) e npm
- A API rodando conforme [`api/README.md`](../api/README.md)

### Dependências

As dependências estão em [`package.json`](package.json): React 18, React Router, Vite, Tailwind CSS e Playwright (testes). Instale dentro de `web/`:

```bash
npm ci
```

A pasta `node_modules/` é gerada por esse comando e **não** deve ser versionada nem incluída no `.zip` de entrega.

### Variáveis de ambiente

Nenhuma. O build é servido pela API no caminho `/static/dist/`, que fica na mesma origem, então não há URL de API para configurar.

### Comandos

| Comando | O que faz |
| --- | --- |
| `npm run build` | Gera o build de produção em `../api/app/static/dist/`, que a API serve. |
| `npm run dev` | Refaz o build automaticamente a cada alteração. |
| `npm run test:e2e` | Testes de interface com Playwright. Depende do servidor de testes da migração. |

## Estrutura

```text
web/
├── src/
│   ├── components/   # Componentes reutilizáveis
│   ├── pages/        # Telas (login, painéis, cadastros)
│   ├── styles/       # CSS por tela
│   └── main.js       # Ponto de entrada
├── tests/            # Testes Playwright
├── package.json
├── vite.config.js
└── tailwind.config.js
```
