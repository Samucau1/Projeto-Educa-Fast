# Validação final — segurança, LGPD, carga e regressão

Resultado: **aprovado no escopo testado**. Foram usados somente dados sintéticos, SQLite descartável e MySQL 8.4 em Docker, no projeto separado `educafast-validacao-final`. O ambiente manual e o MySQL instalado não foram utilizados.

## Resultados

| Etapa | Resultado |
| --- | --- |
| Unitários puros | 8 aprovados no Windows e na imagem Docker; sem consultas ao banco |
| Postman/Newman com SQLite | 124 requisições, 163 verificações, nenhuma falha |
| Postman/Newman com MySQL | 124 requisições, 163 verificações, nenhuma falha |
| Regressão com SQLite | 39 aprovados; 2 cenários específicos de concorrência MySQL ignorados explicitamente |
| Regressão com MySQL | 41 aprovados, sem ignorados, falhas ou erros |
| Carga HTTP com MySQL | 3.252 requisições, zero respostas inesperadas e zero HTTP 5xx |
| Sintaxe e diff | Python, PowerShell e `git diff --check` aprovados |

Os 8 testes unitários também fazem parte dos 41 cenários da regressão; as contagens não devem ser somadas como testes distintos. As duas corridas transacionais são executadas realmente no MySQL, em vez de simular concorrência com SQLite.

Evidências: [SQLite](resultados/), [MySQL](resultados/mysql/), [carga final](resultados/mysql/estresse-resumo.json), [falha inicial preservada](resultados/mysql/estresse-inicial-falha.json).

## Carga e estresse limitado

O executor inicia seu próprio servidor HTTP em loopback, sem aceitar URL externa. O destino MySQL é validado antes de recriar o esquema. Mantém autenticação, CSRF, JWT, limites de login, criptografia e quotas habilitados.

| Etapa | Clientes simultâneos | Requisições | p95 | Respostas inesperadas |
| --- | --- | --- | --- | --- |
| Fluxo completo, 1 ciclo | 1 | 68 | 74,801 ms | 0 |
| Fluxo completo, 2 ciclos por cliente | 4 | 496 | 100,250 ms | 0 |
| Fluxo completo, 3 ciclos por cliente | 8 | 1.440 | 210,702 ms | 0 |
| Leituras concorrentes | 16 | 416 | 327,671 ms | 0 |
| Leituras concorrentes | 32 | 832 | 561,782 ms | 0 |

p95 geral: **424,259 ms**; máximo observado: **1.092,642 ms**. O critério desta execução foi p95 por etapa de até 5.000 ms, zero divergências de status, zero HTTP 5xx e persistência coerente. Esse critério é um gate local, não um SLA de produção.

Foram completados 33 ciclos funcionais. A verificação direta do banco confirmou 33 notas, 33 atividades, 132 documentos e 33 pedidos LGPD, conforme o esperado. Os códigos 400/403/404/409 deliberadamente esperados nos testes de bloqueio não são contados como falhas.

Famílias exercitadas: login/logout, criação de admin/aluno/professor, troca de perfis, aparência, painéis e detalhes, edição de cadastros e foto, disciplinas/turmas/vínculos, atividades com anexo, notas e atualização sem duplicação, busca restrita de alunos, comunicados e leitura por perfil, uploads JWT e administrativos, download autorizado e isolamento, pedidos de documento e bloqueio de reenvio, aviso LGPD, protocolos, fila administrativa, resposta e exportação própria.

Limites: ensaio de rajadas e concorrência de curta duração, com servidor Werkzeug threaded e MySQL de testes. Não mede capacidade máxima de Gunicorn, não realiza soak de horas, teste de falha de infraestrutura ou homologação de produção, e não garante cobertura de todas as combinações de entrada/aliases históricos. TLS real e interface foram verificados na etapa anterior de implementação; não são inferidos dos números desta carga HTTP.

## Defeitos encontrados e corrigidos

1. **Concorrência na troca de fotos:** o teste inicial gerou quatro HTTP 500 porque um arquivo era removido entre a listagem do diretório e a consulta de seu tamanho. O cálculo da quota agora tolera exclusivamente `FileNotFoundError` de arquivos removidos, mantendo as demais falhas e os limites. O teste unitário `test_concurrent_photo_removal_during_quota_scan` reproduz a condição; a repetição completa da carga passou.
2. **Destino de retorno malformado:** a variante `//[` gerava erro de parsing. Agora retorna 400, como os demais destinos externos inválidos, com teste unitário.
3. **CSRF via cabeçalho nos formulários de gestão:** a verificação antiga ignorava `X-CSRF-Token` mesmo após o controle global aceitá-lo. Ambas usam o mesmo contrato, preservando o token de formulário. Carga, Postman e regressão verificaram o fluxo legítimo e o bloqueio sem token.

## Verificações adicionais de concorrência

- Duas submissões simultâneas ao mesmo pedido de documento resultam em um sucesso e um 409, com somente um documento persistido.
- Duas sessões administrativas leem um pedido aberto; uma o conclui e a outra tenta reabri-lo com leitura desatualizada. A segunda recebe 409 e o estado final continua concluído.

## Reprodução

Consulte os comandos completos no [guia de testes](README.md). As evidências JSON/TXT/XML acompanham o código. O commit inclui as alterações de segurança/LGPD, os inicializadores e os testes/documentos correspondentes; segredos reais, certificados, bancos e caches ficam fora do versionamento.

Antes de operar com dados reais, continuam necessários contato LGPD, chaves próprias, certificados/domínio e procedimentos institucionais de retenção e atendimento, conforme [Segurança e LGPD](../SEGURANCA_E_LGPD.md).
