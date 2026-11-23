# Especificação de Casos de Uso

## Sistema de Gestão da Secretaria Escolar DF
Versão em PDF formatada enviada no AVA.
---

## UC01 – Realizar Login
**Atores:** Secretário escolar, Administrador, Direção escolar  
**Descrição:** Permite que usuários acessem o sistema utilizando credenciais válidas.

**Pré-condições**
- Usuário cadastrado no sistema

**Fluxo principal**
1. Usuário acessa tela de login
2. Usuário informa email e senha
3. Sistema valida credenciais
4. Sistema autentica usuário
5. Sistema redireciona para painel principal

**Fluxos alternativos**
- 3A. Credenciais inválidas → sistema exibe erro
- 2A. Campos vazios → sistema solicita preenchimento

**Pós-condições**
- Usuário autenticado

---

## UC02 – Cadastrar Usuário
**Atores:** Administrador  
**Descrição:** Permite cadastrar novos usuários no sistema.

**Pré-condições**
- Administrador autenticado

**Fluxo principal**
1. Administrador acessa tela de cadastro
2. Informa nome, email e senha
3. Confirma cadastro
4. Sistema valida dados
5. Sistema salva no banco
6. Sistema exibe confirmação

**Fluxos alternativos**
- Email já existente
- Campos obrigatórios não preenchidos

**Pós-condições**
- Usuário cadastrado

---

## UC03 – Cadastrar Aluno
**Atores:** Secretário escolar  
**Descrição:** Permite registrar alunos no sistema.

**Pré-condições**
- Usuário autenticado

**Fluxo principal**
1. Usuário acessa cadastro de aluno
2. Informa dados do aluno
3. Confirma cadastro
4. Sistema valida dados
5. Sistema salva informações
6. Sistema exibe confirmação

**Fluxos alternativos**
- Matrícula já cadastrada
- Dados inválidos

**Pós-condições**
- Aluno registrado

---

## UC04 – Consultar Aluno
**Atores:** Secretário escolar, Direção escolar  
**Descrição:** Permite consultar alunos cadastrados.

**Pré-condições**
- Usuário autenticado

**Fluxo principal**
1. Usuário acessa consulta
2. Informa critério de busca (nome ou matrícula)
3. Sistema consulta banco
4. Sistema exibe resultados

**Fluxos alternativos**
- Nenhum registro encontrado

**Pós-condições**
- Dados exibidos

---

## UC05 – Atualizar Dados do Aluno
**Atores:** Secretário escolar  
**Descrição:** Permite atualizar informações cadastradas.

**Pré-condições**
- Usuário autenticado
- Registro existente

**Fluxo principal**
1. Usuário busca registro informando nome ou matrícula do aluno
2. Seleciona registro
3. Sistema exibe dados
4. Usuário altera informações
5. Confirma atualização
6. Sistema salva alterações

**Fluxos alternativos**
- Dados inválidos
- Cancelamento da operação

**Pós-condições**
- Dados atualizados

---

## UC06 – Remover Registro
**Atores:** Secretário escolar, Administrador  
**Descrição:** Permite excluir registros do sistema.

**Pré-condições**
- Usuário autenticado
- Registro existente

**Fluxo principal**
1. Usuário busca registro informando nome ou matrícula
2. Clica em excluir
3. Sistema solicita confirmação
4. Usuário confirma
5. Sistema remove registro

**Fluxos alternativos**
- Cancelamento da exclusão

**Pós-condições**
- Registro removido

---

## UC07 – Visualizar Dados Administrativos
**Atores:** Direção escolar  
**Descrição:** Permite visualizar informações administrativas organizadas.

**Pré-condições**
- Usuário autenticado

**Fluxo principal**
1. Usuário acessa painel
2. Sistema carrega dados
3. Sistema exibe informações

**Fluxos alternativos**
- Erro ao carregar dados

**Pós-condições**
- Informações exibidas

---

## UC08 – Encerrar Sessão
**Atores:** Secretário escolar, Administrador, Direção escolar  
**Descrição:** Permite ao usuário encerrar sua sessão no sistema.

**Pré-condições**
- Usuário autenticado

**Fluxo principal**
1. Usuário clica em "Logout"
2. Sistema invalida a sessão
3. Sistema redireciona para tela de login

**Fluxos alternativos**
- Sessão expirada automaticamente

**Pós-condições**
- Usuário desconectado

---

## UC09 – Gerenciar Usuários
**Atores:** Administrador  
**Descrição:** Permite listar, editar e remover usuários do sistema.

**Pré-condições**
- Administrador autenticado

**Fluxo principal**
1. Administrador acessa gerenciamento
2. Sistema lista usuários
3. Administrador seleciona usuário
4. Administrador escolhe ação:
   - editar
   - excluir
5. Sistema executa operação

**Fluxos alternativos**
- Usuário inexistente
- Erro ao salvar alterações

**Pós-condições**
- Dados atualizados
