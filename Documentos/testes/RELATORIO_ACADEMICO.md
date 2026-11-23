# Homologação — atribuições e notas por período

Data: 23/10/2026, horário de São Paulo. Escopo: testes práticos com exemplos, revisão de turmas antigas e diário/boletim por turma, ano e período. Dados exclusivamente sintéticos.

## Resultado

| Verificação | Resultado |
| --- | --- |
| Regressão SQLite | 70 testes, zero falhas/erros; quatro corridas MySQL ignoradas explicitamente |
| Regressão MySQL 8.4 | 70 testes, zero falhas/erros/ignorados |
| Postman SQLite e MySQL | 182 requisições e 243 verificações em cada banco, sem falhas |
| Navegador Edge/Playwright | Curso em dois anos, reconciliação, período, avaliação, lançamento, publicação, boletim e fechamento verificados; desktop 1440×1000 e móvel 390×844 |
| Exemplos do servidor manual | Seed testado; duas turmas/anos, médias independentes, turma legada e preservação de banco já preenchido |

Os 70 cenários incluem os 56 anteriores e 14 novos, incluindo uma corrida de correção de notas exclusiva do MySQL. Os testes unitários existentes também estão dentro do total. As quatro corridas não são simuladas em SQLite.

Evidências: [SQLite](resultados/regressao-resumo.json), [MySQL](resultados/mysql/regressao-resumo.json), [Postman SQLite](resultados/postman-resumo.json), [Postman MySQL](resultados/mysql/postman-resumo.json) e [interface acadêmica](resultados/academico-interface/resumo.json). JSON/TXT/XML detalham os resultados. O manifesto desta entrega vincula os arquivos ao conteúdo do commit validado; os manifestos e relatórios anteriores correspondem aos commits históricos em que foram criados.

## Cenários cobertos

- Curso compartilhado em 2026/2027 e notas independentes no boletim.
- Reconciliação com candidatos não selecionados automaticamente, confirmação explícita, rejeição de escolha inválida e formulário desatualizado, sem gravação parcial.
- Professor atribuído, revogação imediata, aluno fora da turma, separação entre boletins e CSRF.
- Média ponderada e pendências: zero legítimo se distingue de ausência; avaliação em rascunho não expõe suas notas/título ao aluno.
- Limites numéricos, vírgula decimal, NaN/infinito/tipos inválidos, pesos inválidos, período de outra turma e conflito de versão.
- Dois formulários concorrentes corrigem a mesma nota: um sucesso e um conflito, com versão final incrementada uma vez.
- Fechamento/reabertura com motivo; professor não reabre; período fechado impede alteração.
- Preservação e vínculo explícito de nota anterior; rejeição de origem alterada e vínculo duplicado.
- Histórico após remoção de matrícula, exportação própria, proteção do ano da turma e seed que não sobrescreve dados existentes.
- Migração aditiva v1/v2, repetição e preservação dos dados anteriores nos testes de migração existentes.

## Reproduzir

Execute sequencialmente e interrompa diante de qualquer falha:

```powershell
docker compose -p educafast-academico-validacao -f Códigos/docker-compose.test.yml build testes
docker compose -p educafast-academico-validacao -f Códigos/docker-compose.test.yml up -d --wait mysql_test
docker compose -p educafast-academico-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_regressao.py
docker compose -p educafast-academico-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_postman.py
docker compose -p educafast-academico-validacao -f Códigos/docker-compose.test.yml down
```

SQLite: `.venv/Scripts/python.exe Códigos/tests/executar_regressao.py` e, depois, `.venv/Scripts/python.exe Códigos/tests/executar_postman.py`.

Interface: com Playwright em `.cache/visual` e Edge instalado, iniciar uma base nova com `.venv/Scripts/python.exe Códigos/tests/executar_postman.py --serve --port 5053`; em outro terminal, executar `node Códigos/tests/verificar_academico.cjs`. Esse teste primeiro executa o fluxo dos cursos e depois a homologação acadêmica. Reinicie a base antes de repetir. As capturas mostram a revisão, o diário e o boletim em desktop e móvel.

## Limites

Não houve migração nem confirmação de vínculos no banco real. Vídeos usam IDs sintéticos; reprodução externa e legendas continuam exigindo material real autorizado. Não foi realizado novo ensaio de carga do diário; as cargas históricas de cursos/segurança permanecem identificadas em seus relatórios. Esta entrega não implementa frequência, recuperação, conselho de classe, aprovação anual ou exigências institucionais específicas. O boletim compara notas à referência configurada sem declarar aprovação escolar definitiva.
