# Relatório — migração da interface para React

Data: 23/11/2026. Escopo: substituição dos templates Jinja pela aplicação React/Vite em `web/`, com a API Flask de `api/` entregando os dados de cada tela em JSON (`render_page`, em `api/app/spa.py`). Requisito: não alterar a interface.

## Comparação visual

As telas das duas versões (Jinja, na tag `v1-jinja`, e React) foram capturadas com Playwright/Chromium contra o mesmo banco sintético (fixtures de homologação, datas fixas), percorrendo todos os links internos de cada perfil.

| Item | Resultado |
| --- | --- |
| Perfis | visitante, superadmin, admin, professor e aluno |
| Telas visitadas | 89 |
| Capturas comparadas | 206 (desktop 1440×1000, móvel 390×844 e cada aba aberta) |
| Diferença de pixels | **206/206 idênticas** (limiar 0,05) |
| Ruído medido | duas capturas da mesma versão: 206/206 idênticas |

A navegação interna (sem recarregar) também foi comparada com a abertura direta do endereço em 13 telas da barra lateral: todas idênticas, sem folhas de estilo duplicadas. A troca de tela não exibe a página sem estilo (medição do maior ícone a cada quadro: 20 px em todas as navegações).

## Fluxos no navegador

Login com senha errada e correta; navegação pela barra lateral sem recarga; busca de mensagens; salvar cores; erro de validação no cadastro de usuário com dados preservados no diálogo; criação de usuário; diálogo de permissões; cadastro de aluno pela API; filtro de registros; voltar do navegador; logout; abas do aluno por `#notas`; lançamento de nota no diário pelo professor; 404 com status e tela de erro. **Todos aprovados.**

## Testes automatizados

| Suíte | Resultado |
| --- | --- |
| `unittest` (SQLite em memória) | 90 testes, OK (4 exclusivos do MySQL pulados) |
| Postman/Newman | 201 requisições, 270 verificações, 0 falhas |
| `verificar_protocolo_design.py` | aprovado |

Os testes que procuravam texto no HTML passaram a verificar os dados da tela no JSON. Os testes de escape de conteúdo verificam que o texto chega intacto como dado; o React o exibe sempre como texto, nunca como HTML. `test_spa.py` cobre o formato da resposta, a minimização de dados, o formulário reexibido sem senha e o erro 413.

## Auditoria

- **Dados pessoais:** objetos do banco enviados às telas não incluem senha, CPF, `cpf_hash`, telefone nem data de nascimento; o painel recebe somente o que exibe; formulários reexibidos não devolvem senha nem token. Varredura do JSON de todas as telas por perfil confirmou que aluno e professor não recebem dados de outros alunos.
- **Erros:** 409, 413, 429, 507 e 500 viram a tela de erro na aplicação web.
- **CSRF:** o token só é enviado a formulários da própria origem.
- **Dependências:** `npm audit` e `pip-audit` sem vulnerabilidades conhecidas (Flask 3.1.3, python-dotenv 1.2.2, cryptography 50, Vite 6.4.6).
- **Docker:** imagem de produção (com build da web) e imagem de testes geradas; aplicação servida e validada com MySQL 8.4.

## Limitações

- Os scripts `api/tests/verificar_*.cjs` (inspeção manual com Microsoft Edge) não foram executados nesta validação.
- `/api/rotas` expõe a visitantes a lista de rotas, necessária antes do login; as permissões continuam verificadas em cada rota.
- O CI do GitHub não está habilitado no fork; a validação acima foi executada localmente.
