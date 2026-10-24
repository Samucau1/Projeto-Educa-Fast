# Validação — configuração institucional e protocolo de design

Data: 24/10/2026, horário de São Paulo. Dados exclusivamente sintéticos e bancos descartáveis.

Resultado: 81 testes aprovados no MySQL, sem falhas/erros/ignorados; SQLite aprovado com quatro corridas específicas ignoradas. Postman aprovado em ambos os bancos, com 201 requisições e 269 verificações. O portão estático e a homologação visual desktop/móvel também passaram.

## Escopo

Permissões do superadmin, identidade versionada, calendário por ano, contagem de dias, feriados/recessos/reposição, divisão 2/3/4 períodos, regras versionadas por turma, arredondamento e média anual. Protocolo visual com verificador e inspeção de capturas.

Os resumos JSON registram números e horários reais: [regressão SQLite](resultados/regressao-resumo.json), [regressão MySQL](resultados/mysql/regressao-resumo.json), [Postman SQLite](resultados/postman-resumo.json), [Postman MySQL](resultados/mysql/postman-resumo.json) e [interface](resultados/escola-interface/resumo.json). O manifesto desta entrega vincula essas evidências ao commit validado. Relatórios e manifestos anteriores correspondem aos seus commits históricos.

A regressão inclui 81 cenários, dos quais 11 são novos nesta entrega. Quatro corridas transacionais são exclusivas de MySQL e ficam explicitamente ignoradas no SQLite. A coleção contém 201 requisições; os JSONs/XML detalham as verificações e falhas efetivamente observadas.

## O que foi exercitado

- Superadmin autorizado; admin/professor/aluno/visitante bloqueados; CSRF obrigatório.
- Marca global escapada, versão desatualizada, rejeição de CSS/cores/opções inválidas e contraste insuficiente.
- Paleta clara e sincronização com editor de cores anterior.
- Contagem de dias semanais, feriado que remove um dia, reposição que adiciona dia e lote sobreposto sem persistência parcial.
- Semestres/trimestres/bimestres, pesos inválidos, datas sobrepostas, aplicação repetida/ano incompatível e preservação dos períodos existentes.
- Média anual ponderada com períodos encerrados; referência da escola e arredondamento comercial/truncado.
- Atualização v2→v3 e preservação do esquema anterior; protocolo estático executado localmente e no pacote de testes Docker.
- Navegador com o fluxo anterior de cursos/notas, nova área institucional, calendário, regras de semestres com pesos 1/3, marca e tema claro, boletim anual 6,50 e acesso restrito.

Capturas em `resultados/escola-interface/`: padrão EducaFast, identidade clara desktop/móvel, boletim personalizado desktop/móvel e login móvel personalizado. As paletas foram inspecionadas visualmente; ajustes de contraste em botões secundários, avisos e textos de tabela foram feitos após a primeira inspeção.

## Reproduzir

Na raiz do repositório, execute em sequência, interrompendo em caso de falha:

```powershell
docker compose -p educafast-escola-validacao -f Códigos/docker-compose.test.yml build testes
docker compose -p educafast-escola-validacao -f Códigos/docker-compose.test.yml up -d --wait mysql_test
docker compose -p educafast-escola-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_regressao.py
docker compose -p educafast-escola-validacao -f Códigos/docker-compose.test.yml run --rm testes python tests/executar_postman.py
docker compose -p educafast-escola-validacao -f Códigos/docker-compose.test.yml down
```

SQLite: `.venv/Scripts/python.exe Códigos/tests/executar_regressao.py` e depois `.venv/Scripts/python.exe Códigos/tests/executar_postman.py`.

Design: `.venv/Scripts/python.exe Códigos/tests/verificar_protocolo_design.py`. Interface: iniciar uma base nova com `.venv/Scripts/python.exe Códigos/tests/executar_postman.py --serve --port 5053` e executar `node Códigos/tests/verificar_escola.cjs`, com Edge e Playwright disponíveis em `.cache/visual`. O executor inclui os fluxos anteriores; reinicie o servidor antes de repetir.

O Docker de testes recebe apenas `AGENTS.md` e o protocolo necessário ao verificador, além do código; os demais documentos continuam excluídos do contexto. Suítes que recriam tabelas não podem compartilhar o mesmo banco simultaneamente.

## Limites

Não é auditoria completa de acessibilidade, prova de aprovação escolar legal, teste de carga do motor institucional ou homologação com dados reais. A configuração é por instalação, sem isolamento multiescola na mesma instância. Feriados são cadastrados, não buscados automaticamente. A escala continua 0–10; não há fórmulas arbitrárias, frequência ou recuperação nesta entrega. Regras novas não reescrevem períodos históricos já existentes.
