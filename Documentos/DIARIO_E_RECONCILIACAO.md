> Atualização de 24/10/2026: o superadmin já pode definir divisões, pesos e arredondamento por política institucional. Consulte [a configuração da escola](CONFIGURACAO_INSTITUCIONAL.md). As instruções de criação manual de períodos abaixo se aplicam às turmas ainda sem políticas institucionais.

# Diário, boletim e reconciliação acadêmica

Entrega de 23/10/2026. Complementa os cursos reutilizáveis com avaliações por turma/ano/período e revisão explícita dos vínculos antigos.

## Fluxo da secretaria

1. Em **Revisar atribuições**, abra cada turma antiga. O sistema mostra candidatos derivados dos vínculos existentes, sem conceder novas combinações. Marque somente professor + matéria confirmados e salve. Combinações não marcadas ficam revogadas nessa turma. Se os vínculos mudaram desde a abertura, a confirmação é recusada e a revisão precisa ser refeita.
2. Em **Gestão acadêmica**, confira as matrículas e as atribuições por matéria. Novas combinações que não existiam no legado devem ser cadastradas explicitamente por essa tela.
3. Em **Diário e avaliações**, crie os períodos de cada turma: nome livre, ordem e média de referência configurável de 0 a 10. É possível representar bimestres, trimestres ou semestres. O valor de exemplo 6 não substitui a regra da instituição.
4. Feche o período após a revisão. Somente admin/superadmin podem fechar ou reabrir, com motivo registrado. O fechamento bloqueia criação, publicação e alteração de notas. Arquivar a turma também bloqueia alterações.

O boletim de um aluno pode ser consultado pela secretaria em `/academico/alunos/<id>/boletim`. Professores não recebem acesso ao boletim completo de outras disciplinas.

## Fluxo do professor

O professor entra em **Diário e avaliações**, vê somente as combinações explicitamente atribuídas e cria avaliações com título e peso positivo de até 100. Para cada aluno matriculado, informa nota de 0 a 10, com até duas casas decimais e observação opcional. A vírgula decimal é aceita.

As avaliações começam em rascunho. O professor atribuído ou a administração publica a avaliação para liberar suas notas aos alunos. Notas podem ser corrigidas enquanto o período estiver aberto; cada correção gera auditoria com valor anterior, novo valor e versão. Se outro formulário já alterou a nota, a gravação antiga recebe conflito e não sobrescreve o lançamento recente.

Nas turmas reconciliadas, o formulário antigo de nota única por disciplina é substituído por um acesso ao novo diário. O endpoint antigo também recusa lançamentos nessas turmas, evitando gravar fora de um período. Nas turmas ainda não reconciliadas, o comportamento legado continua disponível durante a transição.

## Boletim do aluno

**Boletim por período** (`/boletim`) separa turma, ano, período, disciplina e avaliações publicadas. Nota ausente é uma pendência, não zero. A média usa Decimal e arredondamento comercial para duas casas:

`média = soma(nota × peso) / soma(pesos)`

Exemplo: prova 8 com peso 1 e trabalho 6 com peso 3 resultam em 6,50. A média só aparece quando todas as avaliações cadastradas naquele período/disciplina estão publicadas e possuem nota para o aluno. Enquanto o período está aberto, avaliações futuras podem alterar essa composição. Não há aprovação automática: a situação exibida compara a média à referência configurada; frequência, recuperação e outras regras institucionais não foram implementadas nesta entrega.

O histórico de notas publicadas permanece disponível ao próprio aluno mesmo após a remoção da matrícula ou o arquivamento da turma. O acesso ao material dos cursos continua obedecendo à matrícula/oferta ativa. O parâmetro de outro aluno não seleciona boletim alheio, e a exportação dos próprios dados inclui o boletim publicado.

## Preservar notas anteriores

As tabelas antigas não são apagadas nem convertidas por inferência. Em **Histórico de notas**, a secretaria escolhe explicitamente uma avaliação em rascunho, na disciplina correspondente e em uma turma com matrícula do aluno. O sistema confere o valor da origem e recusa origem já vinculada, destino com lançamento ou contexto incompatível.

A nota de origem permanece intacta; o novo lançamento registra seu identificador único de origem. Após a vinculação, ela deixa de aparecer como registro sem período no novo boletim. Importar não publica automaticamente a avaliação. Enquanto não houver confirmação, as notas antigas ficam separadas das médias por período.

Não foram reconciliados vínculos nem migradas notas de banco real automaticamente. Os testes e exemplos usam apenas dados sintéticos; a confirmação dos vínculos de uma instituição precisa ser feita pela secretaria que conhece seu histórico.

## Arquitetura e migração

Tabelas novas: `academico_periodos`, `academico_avaliacoes`, `academico_notas` e `academico_auditoria`. O lançamento é único por avaliação/aluno; a avaliação identifica turma-disciplina e período. O serviço valida que período e oferta pertencem à mesma turma. O ano da turma fica protegido contra alteração quando já existem períodos ou cursos ofertados.

Serviços em `app/services/academico.py`; rotas e autorização em `app/routes/academico_routes.py`; modelos em `app/models/academico_model.py`. A migração aditiva v2 usa o registro `educafast_migracoes`, aceita atualização a partir da v1 e não reinterpreta notas antigas. A inicialização deve ser serial, antes de iniciar vários workers, após backup e ensaio em cópia do banco real.

Gravações de notas bloqueiam o período e a avaliação em transação. A leitura do lançamento para controle de versão usa leitura bloqueante atual no MySQL, evitando usar o snapshot antigo de uma sessão que esperou pela transação anterior. Unicidade e restrições numéricas também são aplicadas no banco.

Rollback de aplicação preserva as tabelas novas. A versão anterior recusa versões de migração futuras; portanto, para retornar a uma aplicação antiga, é necessário restaurar uma cópia compatível do banco e reconciliar gravações posteriores. Não baixar o marcador de migração manualmente, não remover tabelas com dados e não restaurar backup por cima de novas gravações sem procedimento de recuperação.

## Demonstração reproduzível

O servidor manual do Compose, quando iniciado com banco sintético vazio, cria:

- Turmas de 2026 e 2027 com o mesmo curso de álgebra, progresso independente e notas 8,50 e 5,00.
- Professor com atribuições em mais de uma turma e matéria.
- Turma de 2025 com combinações antigas para revisão, sem confirmação presumida.
- Nota antiga 7,25 para testar o vínculo histórico explícito.

Na raiz do projeto, com Docker Desktop ativo e a porta 5050 disponível:

```powershell
docker compose -p educafast-homologacao -f Códigos/docker-compose.test.yml --profile manual up -d --build --wait manual
```

Abra `http://127.0.0.1:5050`. Use `admin@teste.local`, `professor@teste.local` ou `aluno@teste.local`, com a senha sintética `Teste-local-2026!`. O vídeo usa identificador sintético; para testar reprodução, use um vídeo real autorizado em uma nova edição do curso.

Um banco já preenchido é preservado e não recebe exemplos sobrepostos. Para encerrar somente esse ambiente:

```powershell
docker compose -p educafast-homologacao -f Códigos/docker-compose.test.yml --profile manual down
```

O MySQL dessa composição é descartável e perde os exemplos quando o container é removido. Não compartilhar o mesmo projeto Compose com suítes que recriam o esquema. Evidências e comandos de testes estão em [testes/RELATORIO_ACADEMICO.md](testes/RELATORIO_ACADEMICO.md).
