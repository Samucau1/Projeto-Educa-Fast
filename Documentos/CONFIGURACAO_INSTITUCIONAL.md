# Configuração institucional — superadministrador

Entrega de 24/10/2026. O EducaFast passa a oferecer configurações declarativas por escola, mantendo o layout e os componentes existentes. A configuração corresponde a uma instituição por instalação/banco; esta entrega não implementa isolamento de várias escolas dentro da mesma instância.

## Acesso e aparência

O superadmin acessa **Regras e identidade da escola** (`/super/escola`). Admin, professor e aluno não podem consultar nem alterar essa área. As gravações exigem sessão, perfil atual e CSRF. Alterações são auditadas; formulários de identidade e calendário usam versão para impedir sobrescrita desatualizada.

Na identidade visual, configure nome, sigla, subtítulo, fundo, destaque, cartões, textos, modo claro/escuro, fonte DM Sans ou do dispositivo, densidade e bordas. A marca é aplicada ao menu, aos títulos compartilhados e ao login. As opções derivam dos tokens do EducaFast; não se aceita CSS, HTML ou JavaScript arbitrário. Cores e opções são validadas, incluindo contraste dos textos e destaques. O editor anterior de cores continua compatível e sincroniza a versão da identidade.

As paletas são preenchidas no formulário; salve para aplicá-las. Outros usuários recebem a configuração na próxima requisição/recarregamento. Restaure a paleta padrão pelo formulário se necessário. A troca de fonte é limitada às opções disponíveis, sem carregamento de fonte externa configurável.

## Calendário

Crie um calendário por ano, definindo início/fim, dias da semana e meta de dias letivos. A meta sugerida no formulário é apenas um valor configurável; a instituição deve confirmar suas exigências antes da adoção.

Cadastre datas ou intervalos como:

- **Feriado/recesso:** o dia não conta como letivo, mesmo se cair num dia da semana normalmente letivo.
- **Reposição:** conta como letivo, inclusive sábado ou domingo.
- **Evento:** aparece na agenda sem alterar a regra semanal.

Há uma exceção por data. Sobreposições são recusadas sem gravação parcial. Para corrigir uma data, remova-a e cadastre novamente; cada operação exige a versão atual. A edição da base do calendário preserva o intervalo de eventos e períodos de políticas já vinculadas.

O cálculo percorre o intervalo inclusivo e aplica a exceção específica antes da regra semanal. Exibe dias planejados, meta e diferença para a meta. Isso é planejamento, não frequência nem comprovação de aula realizada. Não há importação automática de feriados nacionais/regionais: as datas são informadas pela escola. A comunidade autenticada consulta `/calendario-escolar`.

## Regras do boletim

Crie uma versão escolhendo calendário e divisão: dois semestres, três trimestres, quatro bimestres ou composição personalizada de até 12 períodos. Para cada período, defina nome, peso no resultado anual e datas. Configure também média de referência, uma ou duas casas decimais e arredondamento comercial ou truncamento.

As datas ficam dentro do calendário, em ordem e sem sobreposição; nomes não se repetem. Pesos são positivos e limitados a 100. A escala de notas nesta versão continua 0 a 10. Os pesos de avaliações dentro de um período continuam definidos no diário pelo docente autorizado; os pesos entre períodos são exclusivos do superadmin.

Depois de criar a versão, aplique-a explicitamente a turmas ativas do mesmo ano que ainda não tenham períodos. A aplicação cria os períodos e registra a política da turma. Não há sobrescrita nem remapeamento automático de períodos/notas anteriores. Uma versão não é editada após sua criação: crie outra para novas turmas. Turmas antigas continuam com seus períodos e registros preservados. Se já houver políticas institucionais, a divisão letiva deixa de ser criada pelo administrador comum; a estrutura das turmas vinculadas só vem da política.

Uma política não altera vínculos de professor ou matrículas. A secretaria ainda precisa configurar as atribuições exatas e os alunos da turma.

## Cálculo

A média de período continua ponderando notas pelas avaliações publicadas, com pendência enquanto houver avaliação não publicada ou sem nota. A política vinculada define a precisão/arredondamento exibidos.

`média anual = soma(média publicada do período × peso do período) / soma(pesos dos períodos)`

O resultado anual usa as médias de período já arredondadas conforme a política, e aplica novamente sua regra de precisão ao total. Só aparece como completo quando todos os períodos previstos estão fechados e possuem média. Com médias 8 e 6 e pesos 1 e 3, o resultado anual é 6,50. Disciplinas são agrupadas pelo identificador, não pelo nome.

O resultado compara notas com a referência configurada. Não declara aprovação escolar definitiva: frequência, recuperação e critérios adicionais ainda não fazem parte desse motor. Não é possível cadastrar fórmulas arbitrárias, código executável ou escalas diferentes de 0–10 nesta entrega.

## Design e evolução

O [protocolo de design](PROTOCOLO_DESIGN.md) e `AGENTS.md` orientam as próximas alterações. O portão estático verifica o uso do layout e a ausência de estilos/eventos inline nos novos templates; a inspeção visual desktop/móvel continua obrigatória. Os componentes de cursos/diário antes embutidos foram centralizados em `escola.css`, com tokens que acompanham a identidade da escola.

## Arquitetura e operação

Modelos em `app/models/escola_model.py`, regras em `app/services/escola.py`, rotas em `app/routes/escola_routes.py`. A migração aditiva v3 cria tabelas institucionais sem alterar notas ou deduzir regras do legado. Antes de usar em banco real, faça backup e ensaie a migração em cópia. Inicialize serialmente antes de abrir vários workers; o migrador atual não coordena processos simultâneos.

Uma versão antiga do aplicativo recusa uma versão de esquema futura. Um rollback exige aplicação/banco compatíveis e tratamento das gravações posteriores ao backup; não reduzir o marcador de versão nem apagar tabelas para forçar compatibilidade.

Consulte [as evidências de validação](testes/RELATORIO_ESCOLA.md). Configurações e calendários usados nos testes são sintéticos; nenhuma regra ou feriado foi inserido automaticamente no banco real.
