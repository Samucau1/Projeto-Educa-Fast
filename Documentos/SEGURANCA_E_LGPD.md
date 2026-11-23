# Segurança e proteção de dados — EducaFast

Controlador informado: **EducaFast**. O contato de privacidade deve ser definido em `LGPD_CONTATO` antes de usar dados reais. Este documento descreve controles técnicos e pendências operacionais; não certifica conformidade integral com a LGPD.

## Controles implementados

- Chave de sessão obrigatória, sem fallback, com pelo menos 32 caracteres. A chave de criptografia é separada.
- Senhas armazenadas com hash do Werkzeug, nunca com criptografia reversível. Cadastro exige pelo menos oito caracteres; login tem resposta uniforme para conta inexistente/senha incorreta e limite compartilhado de 120 requisições por IP a cada 15 minutos. Os contadores usam HMAC, sem IP bruto, e expiram após duas janelas. Redes compartilhadas dividem o limite; um proxy deve preservar essa política sem confiar em cabeçalhos arbitrários.
- Sessões `HttpOnly`, `SameSite=Lax`; `Secure` obrigatório em produção. POST/PUT/PATCH/DELETE autenticados por cookie exigem CSRF, incluindo JSON via `X-CSRF-Token`. Login aceita JSON e rejeita origem externa. GET de logout só mostra confirmação; POST encerra a sessão.
- APIs protegidas por identidade e permissões atuais no banco. JWT não contém mais e-mail. Não há CORS aberto. Acesso de professor a documentos exige vínculo com aluno, turma e disciplina. Busca de alunos é limitada às suas turmas e retorna somente identificador, nome e matrícula, sem CPF ou nascimento.
- Documentos e fotos exigem autenticação e autorização. Fotos são visíveis ao titular e à administração. Caminhos de retorno externos e variantes codificadas são rejeitados antes de persistir upload.
- Limite de 12 MiB por requisição, 10 MiB por arquivo e 512 MiB para o diretório completo de uploads, incluindo o custo da criptografia. Fotos mantêm limite adicional de 2 MiB. Um lock do sistema operacional serializa verificação de quota e escrita entre processos que compartilham o diretório. Solicitações de documento são consumidas por atualização condicional atômica, no mesmo commit do documento.
- Respostas privadas usam `Cache-Control: no-store`; proteção contra enquadramento e detecção indevida de MIME. HTTPS adiciona HSTS.

## Criptografia e chaves

Fernet, da biblioteca `cryptography`, fornece criptografia autenticada para **CPF, telefone de professor, data de nascimento de aluno, textos dos pedidos de privacidade e respostas**, além dos **novos arquivos e fotos enviados**. A aplicação descriptografa somente depois das verificações de acesso. CPF usa índice HMAC separado do valor cifrado para manter a unicidade inclusive com/sem pontuação. O HMAC é pseudonimização, não anonimização.

Nome, e-mail, matrícula, notas e associações continuam em campos pesquisáveis no banco. Para proteger o conjunto completo em repouso, a infraestrutura também precisa de disco/volume e backups criptografados. Criptografia de campo não protege contra administrador autorizado, aplicação comprometida ou chave exposta.

Gere chaves locais diferentes; não copie as chaves sintéticas dos testes para uma instalação real:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
.\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Guarde a primeira saída como `SECRET_KEY` e a segunda como `DATA_ENCRYPTION_KEY` no ambiente/gestor de segredos. Não envie chaves ao Git, aos logs ou pelo chat. `.env` e `certs/` ficam fora do contexto de build. Mantenha backup da chave de criptografia separado do backup dos dados e teste a recuperação. **Perder ou substituir DATA_ENCRYPTION_KEY sem migração torna os dados ilegíveis e altera os índices de CPF.** Rotação requer procedimento de recifragem com a chave anterior, em manutenção; não há rotação automática implementada. Alterar SECRET_KEY invalida sessões/JWTs existentes.

### Dados legados

Antes da primeira inicialização em instalação existente, faça backup consistente do banco, dos uploads e da chave. A inicialização adapta os campos de CPF/telefone/nascimento para ciphertext, adiciona índices de CPF e cifra os valores antigos. CPF duplicado com formatação diferente pode impedir a criação do índice; resolva a duplicidade no backup de homologação antes de atualizar produção. DDL do MySQL não é integralmente transacional: primeiro valide a migração numa cópia e mantenha janela de manutenção.

Arquivos antigos continuam legíveis por compatibilidade. Para cifrá-los, com os envs corretos e após backup, execute a partir de `Códigos`:

```powershell
python -m flask --app app.py criptografar-arquivos
```

O comando é idempotente e substitui cada arquivo por versão cifrada. Use janela de manutenção, espaço livre suficiente e arquivos dentro dos limites de memória disponíveis. Se houver interrupção com um arquivo `.encrypting`, restaure/verifique o arquivo de staging antes de repetir. Não mova uploads para uma pasta pública. Backups anteriores e cópias exportadas não se tornam cifrados automaticamente.

## Rede e produção

O Compose habitual publica a aplicação somente em `127.0.0.1:5000` e não publica MySQL. O inicializador manual mantém `127.0.0.1:5050`, banco descartável e chaves de demonstração. HTTP local serve para testes sintéticos.

Para produção existe o arquivo **independente** `Códigos/docker-compose.production.yml`. Não o combine com o Compose manual. Ele publica somente HTTPS em 443, usa Gunicorn e deixa MySQL na rede Docker interna sem porta pública. App→MySQL exige TLS com verificação da CA **e da identidade do servidor**, sem ignorar certificados. O banco recusa transporte TCP sem TLS. O acesso HTTPS à aplicação usa certificado e chave montados como somente leitura; TLS mínimo 1.2.

Prepare `Códigos/certs/` fora do Git, com permissões restritas:

| Arquivo | Uso |
|---|---|
| `web.crt`, `web.key` | Certificado/cadeia e chave do domínio HTTPS |
| `ca.crt` | CA confiável que assinou o certificado do MySQL |
| `db.crt`, `db.key` | Certificado e chave MySQL, com SAN DNS `db` |

Configure `.env` com chaves aleatórias, senhas de banco distintas, `TRUSTED_HOSTS` contendo o domínio real, `LGPD_CONTROLADOR=EducaFast` e `LGPD_CONTATO` válido. Renove certificados antes de expirar e mantenha as chaves legíveis pelo processo correto nos containers. Não use certificado sem verificação em produção.

```powershell
cd .\Códigos
docker compose -f docker-compose.production.yml config --quiet
docker compose -f docker-compose.production.yml up -d --build
```

Não há provisionamento automático de domínio/certificado público. A validação ponta a ponta de produção depende desses certificados e domínio. HTTPS protege o transporte; não substitui autorização nas APIs. O ambiente de produção é separado do manual, e seus volumes não devem ser substituídos pelos volumes descartáveis dos testes.

## LGPD na interface

- `/privacidade`: aviso público com controlador, contato, categorias, finalidades, acesso, cookies e direitos.
- `/minha-privacidade`: titular autenticado abre até cinco solicitações em andamento e consulta somente seus protocolos e respostas. Representantes e titulares sem conta devem ter atendimento pelo contato externo da instituição.
- `/minha-privacidade/exportar` (POST com CSRF): cópia JSON de dados estruturados próprios; nunca inclui senha/hash, dados de outro titular ou aceita escolher outra conta por parâmetro. Documentos continuam disponíveis para download na área correspondente. A instituição deve complementar a resposta com informações de sistemas externos quando aplicável.
- `/admin/privacidade`: administração/superperfil analisa pedidos em fila paginada, registra resposta fundamentada e status; aluno/professor não acessa a fila. Uma conclusão registra a resposta, não executa exclusão/correção automaticamente. O operador deve efetuar a ação autorizada ou justificar a retenção antes de encerrar.
- Auditoria registra ator, ação, protocolo e horário, sem copiar o texto do pedido, CPF, IP ou senha. Textos de pedidos/respostas são cifrados no banco.

Não foi adicionado consentimento genérico obrigatório: a instituição deve identificar a hipótese legal de cada tratamento. Crianças/adolescentes exigem avaliação de melhor interesse e representação quando necessária; o sistema não verifica automaticamente guarda ou vínculo parental. Pedido de eliminação não apaga histórico escolar automaticamente.

## Providências da instituição antes de dados reais

1. Informar contato do controlador/encarregado, confirmar finalidades e bases legais por categoria e publicar o aviso completo, incluindo fornecedores/operadores e eventual transferência internacional.
2. Definir tabela de temporalidade para cadastro, documentos, notas, pedidos, auditoria, arquivos substituídos e backups, considerando obrigações educacionais. Não existe prazo único de retenção nem eliminação automática nesta versão.
3. Definir procedimento de verificação de identidade/representação sem coletar documentos em texto livre; para crianças/adolescentes, documentar a avaliação de melhor interesse e comunicações aos responsáveis.
4. Estabelecer atendimento aos direitos e prazos legais aplicáveis, responsáveis, escalonamento e revisão de indeferimentos. Controlar os protocolos pela fila, inclusive fora do sistema.
5. Restringir administradores, revisar acessos, proteger máquinas/volumes/backups, testar restauração, renovar certificados e manter dependências atualizadas.
6. Manter inventário/registro de operações, contratos com operadores, política interna de retenção e plano de resposta/comunicação de incidentes conforme a regulamentação vigente da ANPD. Esta implementação não comunica incidentes automaticamente.

Referências oficiais consultadas:
- [LGPD — Lei nº 13.709/2018, texto compilado](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm): princípios, crianças/adolescentes, retenção, direitos e segurança (arts. 6, 14, 16, 18 e 46).
- [ANPD — Direitos dos titulares](https://www.gov.br/anpd/pt-br/assuntos/titular-de-dados/direito-dos-titulares).
- [ANPD — Enunciado sobre crianças e adolescentes](https://bibliotecadigital.mj.gov.br/bitstream/1/10215/2/Enunciado_ANPD_2023_1.html).
- [Gunicorn — TLS](https://docs.gunicorn.org/en/stable/settings.html), [PyMySQL — validação TLS](https://pymysql.readthedocs.io/en/latest/modules/connections.html).

## Verificação

Testes negativos estão em `Códigos/tests/test_seguranca_lgpd.py`; regressão e coleção Postman mantêm autenticação e CSRF reais. Execute `python tests/executar_regressao.py` e `python tests/executar_postman.py` a partir de `Códigos`. Eles usam apenas banco descartável; não execute testes destrutivos sobre dados reais. O perfil MySQL exige explicitamente o Compose de testes. Certificados, backups, retenção e procedimentos da instituição precisam de validação operacional adicional.
