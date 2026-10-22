# Relatório de API e regressão

**Data:** 22/10/2026, horário de São Paulo.  
**Repositório local:** `Projeto-Educa-Fast`, branch `main`, remoto `origin` correspondente a `Samucau1/Projeto-Educa-Fast`.  
**Escopo:** alterações locais ainda não publicadas, incluindo superperfil, permissões, cores, comunicados e fluxos acadêmicos/documentais existentes.

## Resultado

| Execução | Quantidade | Falhas | Resultado |
| --- | --- | --- | --- |
| Regressão Python/unittest | 17 testes, incluindo cenários parametrizados | 0 | Aprovada no ambiente local |
| Coleção Postman pelo Newman | 100 requisições HTTP, 124 verificações | 0 | Aprovada no ambiente local |
| Regressão Python/unittest no Docker/MySQL | 17 testes, incluindo cenários parametrizados | 0 | Aprovada com MySQL 8.4 |
| Coleção Postman no Docker/MySQL | 100 requisições HTTP, 124 verificações | 0 | Aprovada com MySQL 8.4 |

A execução da coleção usa um servidor Flask real em loopback, cookie de sessão, CSRF e JWTs. A regressão usa o cliente de testes do Flask e verifica também persistência, documentos e isolamento dos usuários. Nenhum dos dois utiliza o banco da instalação.

Ambiente local: Python 3.14.3, Flask 3.1.0, SQLAlchemy 2.0.44, Newman 6.2.1 e SQLite com verificação de chaves estrangeiras habilitada.

Ambiente Docker: Python 3.12.15, Flask 3.1.0, SQLAlchemy 2.0.44, Newman 6.2.1 e imagem `mysql:8.4` (binários MySQL 8.4.13). Foram executadas integralmente as mesmas duas suítes no MySQL isolado. A regressão levou cerca de 12 segundos; a execução HTTP da coleção levou cerca de 3 segundos, sem incluir download e construção das imagens. Os tempos completos estão nos resumos JSON.

O Compose de testes não utiliza o `.env`, não publica a porta do MySQL e armazena os dados em memória via `tmpfs`. O usuário de testes acessa apenas o banco `educafast_regressao`. Os executores validam o destino antes de recriar as tabelas. Os relatórios MySQL foram salvos separadamente em [`resultados/mysql/`](resultados/mysql/), preservando as evidências anteriores de SQLite.

## Defeitos reproduzidos e corrigidos

| Defeito observado | Correção | Evidência de regressão |
| --- | --- | --- |
| `/login` gerava exceção com JSON em formato de lista, texto ou número; campos com tipos inválidos também precisavam ser rejeitados | Validação do objeto e dos tipos de e-mail/senha; retorno 400 | `test_login_rejects_non_object_json` e coleção Postman |
| Notas `NaN`/`sNaN` geravam `decimal.InvalidOperation` | Rejeição de valores não finitos antes da comparação de limites | `test_grade_boundaries_and_nonfinite_values` e coleção Postman |
| JWT de professor continuava permitindo upload após a troca de perfil | A leitura do JWT consulta o perfil atual no banco, inclusive nas rotas sem decorador | `test_revoked_teacher_jwt_cannot_upload` e teste de revogação na coleção |
| Download sem sessão, usando JWT de outro aluno, retornava arquivo sem verificar propriedade | Mesma verificação de usuário e vínculo aplicada a sessão e JWT | `test_jwt_download_obeys_same_ownership_as_session` |

Os testes que reproduzem esses defeitos falharam antes das correções. Após as correções, a suíte completa passou.

## Limites e pendências

- **Banco antigo:** a autenticação do serviço `MySQL80` instalado continuou sem acesso; esse serviço e seus dados não foram alterados. A validação MySQL foi concluída em um container separado, sem recuperar nem redefinir a senha antiga.
- **Migração histórica:** as suítes cobrem a criação do esquema atual e sua reutilização no MySQL. Não simulam todas as versões históricas do esquema nem a migração de uma cópia do banco antigo.
- **Interface:** templates renderizados por HTTP, sem inspeção visual no navegador, sem teste do carregamento das CDNs e sem automação de cliques.
- **Operação:** não foram executados testes de carga, infraestrutura de produção ou envio por canais externos; os comunicados são internos.

Resultado: regressão aprovada com SQLite local e MySQL no Docker, no escopo acima. A revisão visual e a homologação de produção não fazem parte desses resultados. Não houve commit nem push para o GitHub nesta etapa.

Os comandos para repetir os testes e importar a coleção estão no [guia de testes](README.md). As evidências finais estão na pasta [resultados](resultados/).

## Verificação da nova interface de usuários e permissões

Após a modernização dessa tela, os 17 testes Python e as 100 requisições/124 verificações Postman passaram novamente com SQLite. A verificação de navegador foi feita no Edge, via Playwright, em 1440 × 1000 e 390 × 844: busca, filtro, mapa de permissões, abertura/fechamento dos formulários, exibição de campos por perfil, criação de usuário, troca de perfil e reaproveitamento de cadastro acadêmico passaram sem erros JavaScript. Os fluxos que gravam novos usuários foram exercitados em uma base SQLite separada.

No ambiente manual Docker/MySQL, foram conferidos a renderização responsiva, os formulários e o tratamento de e-mail/CPF duplicados com reabertura da janela e preservação dos campos, sem reexibir a senha. Os dados já existentes no ambiente manual foram preservados. Essa verificação é específica da tela de usuários e permissões; a revisão manual das outras páginas continua pendente.
