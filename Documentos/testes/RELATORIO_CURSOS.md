# Validação — cursos reutilizáveis e gestão acadêmica

Data local: 23/10/2026. Dados exclusivamente sintéticos; bancos descartáveis. O relatório anterior RELATORIO_VALIDACAO_FINAL.md é histórico da entrega de segurança/LGPD.

## Evidências desta entrega

| Verificação | Resultado |
| --- | --- |
| Regressão SQLite | 56 cenários, sem falhas/erros; três corridas específicas de MySQL ignoradas |
| Regressão MySQL 8.4 | 56 cenários, sem falhas/erros/ignorados |
| Postman SQLite | 158 requisições e 210 verificações, sem falhas |
| Postman MySQL | 158 requisições e 210 verificações, sem falhas |
| Interface Edge/Playwright | Fluxo admin → professor → aluno, desktop 1440×1000 e móvel 390×844; sem erros JavaScript ou overflow horizontal nas páginas verificadas |
| Carga de cursos MySQL | 609 requisições em rajadas de 1, 4, 8 e 16 clientes; zero HTTP inesperados; uma conclusão persistida após envios repetidos |

Os 56 cenários incluem os 8 unitários existentes e 15 novos testes de cursos. Não somar essas contagens como testes distintos. A execução SQLite ignora as duas corridas anteriores e a nova conclusão concorrente; todas são realmente executadas no MySQL.

Arquivos: [regressão SQLite](resultados/regressao-resumo.json), [regressão MySQL](resultados/mysql/regressao-resumo.json), [Postman SQLite](resultados/postman-resumo.json), [Postman MySQL](resultados/mysql/postman-resumo.json), [carga dos cursos](resultados/mysql/cursos-carga-resumo.json), [interface](resultados/cursos-interface/resumo.json). As capturas desktop e mobile estão na pasta da interface. O resultado de carga geral em estresse-resumo.json é da entrega anterior; a carga nova é exclusivamente a descrita em cursos-carga-resumo.json.

## Cobertura e limitações

Verificados: professor com duas turmas/matérias sem cruzamento indevido; revogação aplicada aos controllers de nota/atividade e ao painel; administração e CSRF; autoria por responsável; rascunho privado; hierarquia e pai de outro curso; escape HTML; validação de vídeo; publicação incompleta; ordenação/remoção; preservação do conteúdo publicado; duplicação integral sem ofertas/progresso; mesmo curso em dois anos; progresso por oferta e idempotência concorrente; revogação de matrícula/oferta, turma arquivada; migração de esquema legado, repetição e preservação de dados anteriores.

O navegador verificou formulários reais de autoria, revisão/publicação, cartões de dois anos, navegação e confirmação de conclusão. O player usa um ID sintético: endereço e incorporação foram verificados, mas reprodução de vídeo externo, disponibilidade do provedor e legendas não foram homologadas. A navegação móvel não teve overflow nas telas verificadas; isso não constitui auditoria completa de acessibilidade.

A carga usa servidor Werkzeug threaded local e MySQL temporário. O limite de aceite foi p95 por etapa até 5.000 ms, zero HTTP inesperados e unicidade do progresso. Não define SLA/capacidade de produção, nem substitui ensaio prolongado ou falhas de infraestrutura.

Defeito encontrado durante a integração: o reset de metadados removia tabelas novas sem remover o marcador de migração. A tabela de versões agora integra os metadados; regressão e Postman foram repetidos em sequência para verificar a correção. A migração de produção continua recusando marcador de versão com tabelas ausentes.

## Reproduzir

Na raiz do repositório, com Docker Desktop ativo, execute em sequência e interrompa em qualquer falha:

```powershell
docker compose -p educafast-cursos-validacao -f Códigos/docker-compose.test.yml build testes
docker compose -p educafast-cursos-validacao -f Códigos/docker-compose.test.yml up -d --wait mysql_test
docker compose -p educafast-cursos-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_regressao.py
docker compose -p educafast-cursos-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_postman.py
docker compose -p educafast-cursos-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_carga_cursos.py --confirmar-banco-descartavel
docker compose -p educafast-cursos-validacao -f Códigos/docker-compose.test.yml down
```

Os executores recriam o esquema do banco exclusivo de testes. Nunca execute-os simultaneamente contra o mesmo banco. O servidor manual/dados reais não participa desses comandos. O executor de carga não aceita URL externa.

Para SQLite, use `.venv/Scripts/python.exe Códigos/tests/executar_regressao.py` e depois `.venv/Scripts/python.exe Códigos/tests/executar_postman.py`.

Interface: instale Playwright na pasta `.cache/visual` (`npm.cmd install --prefix .cache/visual playwright`) e tenha Microsoft Edge instalado. Em um terminal, inicie uma base nova com `.venv/Scripts/python.exe Códigos/tests/executar_postman.py --serve --port 5053`. Em outro, execute `node Códigos/tests/verificar_cursos.cjs`. Encerre o servidor ao terminar. Reinicie esse servidor antes de repetir o fluxo; o teste usa identificadores conhecidos da base sintética vazia.

## Roteiro manual complementar

1. Criar duas turmas com anos distintos; atribuir matérias diferentes ao mesmo professor e matricular um aluno em ambas.
2. Como professor, criar curso, dois capítulos, temas e aulas com vídeos válidos autorizados; reordenar e conferir a prévia.
3. Como admin, publicar e liberar o mesmo curso nas duas turmas compatíveis com a disciplina.
4. Como aluno, abrir um curso, assistir ao vídeo válido, testar controles/legendas, teclado, anterior/próxima e marcar conclusão; conferir que a outra oferta mantém seu progresso independente.
5. Como professor, duplicar a edição publicada; editar a cópia e verificar que a turma anterior continua com o material original.
6. Suspender uma oferta ou remover a matrícula e confirmar que o aluno perde o acesso, inclusive com a URL guardada.
7. Revogar atribuição docente e confirmar a ausência da matéria/turma no painel e o bloqueio de novos lançamentos.

Os passos com reprodução de vídeo válido e legendas são complementares e permanecem para homologação institucional.
