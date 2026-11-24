# Educa Fast — Web (React)

Aplicação web do Educa Fast em React + Vite. Todas as telas (login, painéis da secretaria, do professor e do aluno, cursos, diário, boletim, calendário, privacidade e gestão de usuários) são desenhadas aqui e consomem a API de [`api/`](../api/README.md).

## Instalação, configuração e execução

### Pré-requisitos

- Node.js 22 (ou 20 LTS) e npm
- A API configurada conforme [`api/README.md`](../api/README.md)

Com Docker, nada disto é necessário: o build da imagem da API já compila esta aplicação (`docker compose up -d --build` em `api/`).

### Dependências

As dependências estão em [`package.json`](package.json): React 18, Vite e o plugin React do Vite (Tailwind CSS só para regenerar `public/css/utilities.css`). Instale dentro de `web/`:

```bash
npm ci
```

A pasta `node_modules/` é gerada por esse comando e **não** deve ser versionada nem incluída no `.zip` de entrega.

### Variáveis de ambiente

| Variável | Obrigatória | Descrição |
| --- | --- | --- |
| `EDUCAFAST_API` | Não | Só para `npm run dev`: endereço da API para onde o Vite encaminha as requisições. Padrão `http://127.0.0.1:5000`. |

Em produção não há variáveis: o build é servido pela própria API em `/static/dist/`, na mesma origem (sessão e CSRF funcionam sem CORS).

### Comandos

| Comando | O que faz |
| --- | --- |
| `npm run build` | Gera o build de produção em `../api/app/static/dist/`, servido pela API em `http://localhost:5000`. |
| `npm run dev` | Servidor de desenvolvimento em `http://localhost:5173` com recarga automática; encaminha os dados para a API (que precisa estar rodando). |
| `npm run watch` | Refaz o build a cada alteração (alternativa ao `dev`, usando o servidor da API). |
| `npm run css:utilities` | Regenera `public/css/utilities.css` a partir das classes usadas nas telas. |

Fluxo comum de desenvolvimento: suba a API (`python app.py` em `api/`) e, em outro terminal, rode `npm run dev` aqui.

---

## Como funciona

- Cada rota de tela da API responde com JSON quando recebe o cabeçalho `X-EducaFast-SPA: 1`: o nome da tela, seus dados e o contexto global (sessão, tema, identidade da escola, token CSRF e mensagens).
- [`src/core/App.jsx`](src/core/App.jsx) busca esses dados, carrega as folhas de estilo da tela e renderiza o componente correspondente em [`src/pages/`](src/pages/). O nome do arquivo é o nome da tela.
- Links internos e formulários são tratados pela aplicação: navegam sem recarregar a página, enviam o token CSRF e seguem os redirecionamentos da API.
- As URLs são geradas com `urlFor(endpoint, parâmetros)`, a partir do mapa de rotas da API (`/api/rotas`).

## Estrutura

```text
web/
├── public/
│   ├── css/          # Folhas de estilo (design system, painéis e telas)
│   └── fonts/        # DM Sans
├── src/
│   ├── core/         # Navegação, contexto, rotas, <head> e formatações
│   ├── components/   # Layouts, barra lateral, ícones, abas e peças comuns
│   ├── pages/        # Uma tela por arquivo (mesmo nome usado pela API)
│   └── main.jsx      # Ponto de entrada
├── tailwind/         # Entrada do Tailwind para utilities.css
├── index.html
├── package.json
└── vite.config.js
```
