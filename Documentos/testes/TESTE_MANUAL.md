> Para notas por período, revisão das turmas antigas e demonstração em dois anos, consulte [o guia acadêmico](../DIARIO_E_RECONCILIACAO.md).

> Para os novos cursos reutilizáveis e a gestão acadêmica, consulte [o roteiro atualizado](RELATORIO_CURSOS.md#roteiro-manual-complementar).

# Teste manual no navegador

## Iniciar o ambiente em segundo plano

No **PowerShell**, aberto na pasta do projeto, execute:

```powershell
.\iniciar-educafast.ps1
```

O script abre o Docker Desktop se necessário, constrói a aplicação, sobe o MySQL, cria o esquema e os exemplos no primeiro uso, aguarda os serviços saudáveis e abre **http://127.0.0.1:5050**. Ao terminar o comando, os containers continuam rodando em segundo plano; você pode fechar o terminal.

No **CMD**, use o iniciador equivalente, pois arquivos `.ps1` são executados pelo PowerShell:

```cmd
.\iniciar-educafast.cmd
```

Ou chame o PowerShell explicitamente:

```cmd
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\iniciar-educafast.ps1
```

Opções pelo PowerShell:

```powershell
.\iniciar-educafast.ps1 -SemNavegador
.\iniciar-educafast.ps1 -Acao Status
.\iniciar-educafast.ps1 -Acao Parar
```

`-Acao Parar` remove os containers e **descarta os dados de demonstração**. Os mesmos parâmetros funcionam com `iniciar-educafast.cmd`. O Docker deve continuar aberto para manter os serviços funcionando.

## Iniciar com um clique

Na raiz do repositório, dê dois cliques em **`iniciar-teste-manual.cmd`** (atalho compatível com o iniciador acima). Não exige Python nem a senha do MySQL instalado; é necessário ter Docker Desktop instalado e configurado para containers Linux. Na primeira execução, o Docker pode baixar as imagens.

Iniciar novamente atualiza a aplicação e preserva os dados do MySQL manual que ainda estiver ativo. O script trabalha somente com o projeto Docker `educafast-manual` e a porta local 5050.

## Acessar o sistema

Abra **http://127.0.0.1:5050**. A aplicação e o MySQL rodam no Docker, no projeto separado `educafast-manual`.

Todos os usuários abaixo usam a senha **`Teste-local-2026!`**:

| Perfil | E-mail |
| --- | --- |
| Superperfil | `superadmin@teste.local` |
| Administrador | `admin@teste.local` |
| Professor | `professor@teste.local` |
| Aluno | `aluno@teste.local` |
| Outro aluno, sem vínculo com a turma | `outro_aluno@teste.local` |

Use janelas de navegadores diferentes ou uma janela anônima para manter perfis conectados simultaneamente. Abas na mesma sessão compartilham o usuário; para trocar de perfil, saia do sistema antes de entrar novamente.

## Roteiro

| Etapa | Ação | Resultado esperado |
| --- | --- | --- |
| 1 | Entre como superperfil | Abre a gestão de usuários; aparecem os acessos a permissões, cores e mensagens |
| 2 | Clique em Novo usuário, escolha Administrador e preencha nome, e-mail novo e senha de pelo menos 8 caracteres | Cadastro aparece na lista e há confirmação de sucesso; o novo usuário consegue entrar |
| 3 | Crie professor e aluno | Professor exige nome e CPF; aluno exige nome e matrícula; ambos conseguem entrar |
| 4 | Use Gerenciar na linha de um usuário criado e altere de admin para professor ou aluno | Exige apenas os dados acadêmicos que faltarem; ao recarregar a sessão desse usuário, a permissão anterior deixa de funcionar |
| 5 | Abra Cores do layout, escolha cores diferentes e salve | Após recarregar, o fundo e os destaques compartilhados mudam também para outros usuários |
| 6 | Publique um comunicado pelo superperfil | Aparece com texto completo em Mensagens |
| 7 | Entre como admin e publique outro comunicado | Todos conseguem ler; admin não tem acesso à gestão do superperfil nem à edição de cores |
| 8 | Entre como aluno e abra Mensagens | Exibe os dois comunicados; não apresenta opção de envio |
| 9 | Como aluno, digite `http://127.0.0.1:5050/admin/comunicados` e depois `/super/usuarios` na barra de endereços | Acesso negado, HTTP 403 |
| 10 | Entre como professor | Vê a turma de demonstração e Matemática; consegue lançar atividade e nota para o aluno vinculado; pode ler mensagens |
| 11 | Entre como aluno e abra Matemática | Vê a atividade de demonstração, novas atividades e a nota lançada |
| 12 | Entre como outro aluno | Consegue ler mensagens gerais, mas não vê a disciplina da turma sem vínculo |
| 13 | Como admin, solicite um documento nos detalhes do aluno; depois entre como aluno e envie um arquivo de exemplo | Solicitação aparece ao aluno e passa a enviada após o upload; admin consegue consultar o documento |
| 14 | Saia e tente abrir `/mensagens` diretamente | Acesso negado; precisa entrar novamente |
| 15 | Reduza a largura da janela e confira as páginas | Verifique se menus, formulários e botões continuam utilizáveis; registre problemas de sobreposição ou rolagem |

Comece pelos passos 1, 5, 6, 7, 8 e 9 para conferir as funcionalidades novas. Os demais completam a regressão manual.

Na nova tela de usuários, confira também a busca por nome/e-mail, o filtro por perfil e a aba **Mapa de permissões**. No celular, cada usuário é apresentado com seu botão Gerenciar. Os formulários de cadastro e permissões abrem em janelas com seleção visual do perfil; CPF e matrícula aparecem apenas quando necessários. Erros de cadastro mantêm os campos preenchidos, mas não preservam a senha. Pressione Esc ou use Cancelar para fechar.

## Iniciar novamente e encerrar

Na raiz do projeto, com o Docker Desktop aberto:

```powershell
docker compose -p educafast-manual -f Códigos/docker-compose.test.yml --profile manual up -d --build --wait manual
```

Para encerrar e remover esse ambiente:

```powershell
docker compose -p educafast-manual -f Códigos/docker-compose.test.yml --profile manual down
```

Os dados são descartáveis. Ao remover/recriar o container MySQL, seus testes manuais serão perdidos e os usuários de exemplo serão recriados na próxima inicialização. Reiniciar somente a aplicação preserva os dados do banco ainda ativo. O serviço não redefine usuários nem cores quando encontra um banco já preenchido.

Use o projeto `educafast-validacao` para as suítes automáticas e `educafast-manual` para o navegador: as suítes recriam tabelas e não devem usar o ambiente em que você está fazendo o teste manual.

## Registrar o resultado

Para cada problema, anote: perfil, caminho da tela, ação realizada, resultado esperado e resultado observado. Inclua uma captura da tela quando houver problema visual. Este roteiro ainda precisa ser executado por uma pessoa; a preparação e a verificação HTTP do ambiente não substituem essa conferência.

## Seguranca e privacidade (LGPD)

1. Reinicie o ambiente com `.\iniciar-educafast.ps1` para reconstruir a imagem atual. Use somente dados sinteticos.
2. Na tela de login, abra o aviso de privacidade: controlador EducaFast.
3. Entre como aluno e abra **Meus dados e direitos**. Registre um pedido de correcao e baixe a copia JSON.
4. Entre como outro aluno: o protocolo anterior nao deve aparecer.
5. Entre como administrador e abra **Atendimento LGPD**. Registre resposta fundamentada e conclua o pedido.
6. Volte ao aluno e confirme a resposta. Alunos/professores nao podem acessar a fila administrativa.
7. Tente enviar arquivo maior que 10 MiB, repetir uma solicitacao atendida e anexar documento por professor sem vinculo: o backend deve recusar.
8. Fotos e documentos privados exigem autenticacao. Sair agora mostra confirmacao e encerra a sessao por POST com CSRF.

O ambiente manual usa HTTP em loopback e chaves sinteticas. Producao exige chaves proprias, HTTPS, TLS no banco e contato de privacidade; consulte [Seguranca e LGPD](../SEGURANCA_E_LGPD.md).
