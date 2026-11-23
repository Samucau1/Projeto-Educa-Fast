import { test, expect } from '@playwright/test';

async function login(page, role) {
    await page.goto('/login');
    await page.getByRole('textbox', { name: 'E-mail Institucional' }).fill(`${role}@teste.local`);
    await page.getByRole('textbox', { name: 'Senha', exact: true }).fill('teste123');
    await page.getByRole('button', { name: 'Acessar Sistema' }).click();
    await expect(page).toHaveURL(role === 'admin' ? /\/admin\/dashboard$/ : new RegExp(`/${role}$`));
}

async function fecharJanela(page) {
    const janelas = page.getByRole('dialog');
    if (await janelas.count()) await janelas.last().getByRole('button', { name: 'Fechar janela', exact: true }).click();
}

function observeErrors(page) {
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    return errors;
}

const upload = { name: 'comprovante.txt', mimeType: 'text/plain', buffer: Buffer.from('Documento de teste') };

test('login, navegação SPA, cadastro, filtros e detalhes administrativos', async ({ page }) => {
    const errors = observeErrors(page);
    await page.goto('/admin/disciplinas');
    await expect(page).toHaveURL(/\/login$/);
    await page.getByRole('textbox', { name: 'E-mail Institucional' }).fill('admin@teste.local');
    await page.getByRole('textbox', { name: 'Senha', exact: true }).fill('invalida');
    await page.getByRole('button', { name: 'Acessar Sistema' }).click();
    await expect(page.getByRole('alert')).toContainText('Senha invalida');
    await page.getByRole('textbox', { name: 'Senha', exact: true }).fill('teste123');
    await page.getByRole('button', { name: 'Acessar Sistema' }).click();
    await expect(page.getByRole('heading', { name: 'Disciplinas', exact: true })).toBeVisible();
    await page.evaluate(() => { window.__spaMarker = 'mounted-once'; });
    await page.getByRole('button', { name: 'Nova disciplina', exact: true }).click();
    const discipline = page.getByRole('dialog', { name: 'Nova disciplina', exact: true });
    await expect(discipline.getByRole('textbox', { name: 'Nome', exact: true })).toBeFocused();
    await discipline.getByRole('textbox', { name: 'Nome', exact: true }).fill('História');
    await discipline.getByRole('textbox', { name: 'Código', exact: true }).fill('HIST');
    await discipline.getByRole('spinbutton', { name: 'Carga horária' }).fill('60');
    await discipline.getByRole('button', { name: 'Cadastrar Disciplina' }).click();
    await expect(page.getByRole('cell', { name: 'História', exact: true })).toBeVisible();
    await expect(discipline).not.toBeVisible();
    await page.getByRole('button', { name: 'Nova disciplina', exact: true }).click();
    await discipline.getByRole('textbox', { name: 'Nome', exact: true }).fill('História');
    await discipline.getByRole('textbox', { name: 'Código', exact: true }).fill('HIST');
    await discipline.getByRole('spinbutton', { name: 'Carga horária' }).fill('60');
    await discipline.getByRole('button', { name: 'Cadastrar Disciplina' }).click();
    await expect(discipline.getByRole('alert')).toContainText('ja cadastrado');
    await page.screenshot({ path: '/tmp/secretaria-disciplina-modal.png', fullPage: true });
    await page.keyboard.press('Escape');
    await expect(discipline).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Nova disciplina', exact: true })).toBeFocused();
    await page.getByRole('button', { name: 'História', exact: true }).click();
    const detalhesDisciplina = page.getByRole('dialog', { name: 'História', exact: true });
    await expect(detalhesDisciplina.getByText('Nenhum professor associado a esta disciplina.')).toBeVisible();
    await detalhesDisciplina.getByRole('button', { name: 'Associar professor', exact: true }).click();
    await detalhesDisciplina.getByLabel('Professor para associar').selectOption('1');
    await detalhesDisciplina.getByRole('button', { name: 'Confirmar associação', exact: true }).click();
    await expect(detalhesDisciplina.getByRole('status')).toContainText('Professor associado');
    await expect(detalhesDisciplina.getByRole('listitem').filter({ hasText: 'Professor Teste' })).toBeVisible();
    await expect(detalhesDisciplina.getByRole('button', { name: 'Associar professor', exact: true })).toBeDisabled();
    await page.screenshot({ path: '/tmp/secretaria-disciplina-professores.png', fullPage: true });
    await page.keyboard.press('Escape');
    await page.getByRole('button', { name: 'História', exact: true }).click();
    await expect(detalhesDisciplina.getByRole('listitem').filter({ hasText: 'Professor Teste' })).toBeVisible();
    await detalhesDisciplina.getByRole('button', { name: 'Fechar detalhes da disciplina' }).click();


    await page.getByRole('link', { name: 'Turmas', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Turmas', exact: true })).toBeVisible();
    const alunoAssociacao = await page.request.post('/api/cadastro/aluno', { form: { nome: 'Aluno Associação', email: 'associacao@teste.local', senha: 'teste123', matricula: 'ASSOC001' } });
    expect(alunoAssociacao.status()).toBe(201);
    await page.getByRole('button', { name: 'Nova turma', exact: true }).click();
    const classForm = page.getByRole('dialog', { name: 'Nova turma', exact: true });
    await classForm.locator('input[name="nome"]').fill('Turma SPA');
    await classForm.locator('input[name="codigo"]').fill('SPA');
    await classForm.locator('input[name="ano_letivo"]').fill('2026');
    await classForm.getByRole('button', { name: 'Cadastrar Turma', exact: true }).click();
    await expect(page.getByRole('cell', { name: 'Turma SPA', exact: true })).toBeVisible();
    await expect(classForm).not.toBeVisible();
    await page.getByRole('button', { name: 'Turma SPA', exact: true }).click();
    const detalhesTurma = page.getByRole('dialog', { name: 'Turma SPA', exact: true });
    await detalhesTurma.getByRole('button', { name: 'Associar aluno', exact: true }).click();
    await detalhesTurma.getByLabel('Aluno para associar').selectOption('2');
    await detalhesTurma.getByRole('button', { name: 'Confirmar associação', exact: true }).click();
    await expect(detalhesTurma.getByRole('status')).toContainText('Aluno associado');
    await expect(detalhesTurma.getByRole('listitem').filter({ hasText: 'Aluno Associação' })).toBeVisible();
    await detalhesTurma.getByRole('button', { name: 'Professores', exact: true }).click();
    await detalhesTurma.getByRole('button', { name: 'Associar professor', exact: true }).click();
    await detalhesTurma.getByLabel('Professor para associar').selectOption('1');
    await detalhesTurma.getByRole('button', { name: 'Confirmar associação', exact: true }).click();
    await expect(detalhesTurma.getByRole('status')).toContainText('Professor associado');
    await page.screenshot({ path: '/tmp/secretaria-turma-detalhes.png', fullPage: true });
    await detalhesTurma.getByRole('button', { name: 'Disciplinas e cronograma', exact: true }).click();
    await expect(detalhesTurma.getByRole('region', { name: 'Grade semanal de disciplinas' })).toBeVisible();
    await expect(detalhesTurma.getByLabel('Disciplina do cronograma')).toHaveCount(0);
    await detalhesTurma.getByRole('button', { name: 'Gerenciar disciplinas e horários', exact: true }).click();
    const gerenciamento = page.getByRole('dialog', { name: 'Gerenciar disciplinas e horários', exact: true });
    await expect(gerenciamento.getByLabel('Disciplina do cronograma')).toBeVisible();
    await expect(gerenciamento.getByRole('list')).toHaveCount(0);
    await page.keyboard.press('Escape');
    await expect(gerenciamento).not.toBeVisible();
    await expect(detalhesTurma).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(detalhesTurma).not.toBeVisible();

    await page.getByRole('link', { name: 'Comunicados', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Comunicados', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Novo comunicado', exact: true }).click();
    await page.locator('input[name="titulo"]').fill('Comunicado SPA');
    await page.locator('textarea[name="mensagem"]').fill('Reunião da secretaria');
    await page.getByRole('button', { name: 'Disparar Comunicado' }).click();
    await expect(page.getByRole('status')).toBeVisible();
    await fecharJanela(page);
    await expect(page.getByRole('heading', { name: 'Comunicado SPA', exact: true })).toBeVisible();
    await expect(page.getByText('Reunião da secretaria', { exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'Alunos', exact: true }).click();
    await page.getByRole('button', { name: 'Novo aluno', exact: true }).click();
    await page.locator('input[name="nome"]').fill('Novo Aluno');
    await page.locator('input[name="email"]').fill('novo@teste.local');
    await page.locator('input[name="matricula"]').fill('TESTE002');
    await page.locator('input[name="senha"]').fill('teste123');
    await page.getByRole('button', { name: 'Salvar Registro' }).click();
    await expect(page.locator('form').getByRole('status')).toContainText('sucesso');
    await page.screenshot({ path: '/tmp/secretaria-cadastro-modal.png', fullPage: true });
    await fecharJanela(page);
    await page.getByRole('link', { name: 'Professores', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Cadastro de Professores' })).toBeVisible();
    await page.getByRole('button', { name: 'Novo professor', exact: true }).click();
    await page.locator('input[name="nome"]').fill('Nova Professora');
    await page.locator('input[name="disciplina"]').fill('História');
    await page.locator('input[name="cpf"]').fill('33333333333');
    await page.locator('input[name="email"]').fill('nova.professora@teste.local');
    await page.locator('input[name="senha"]').fill('teste123');
    await page.getByRole('button', { name: 'Salvar Registro' }).click();
    await expect(page.locator('form').getByRole('status')).toContainText('sucesso');
    await fecharJanela(page);
    await page.getByRole('link', { name: 'Banco de Dados', exact: true }).click();
    await page.getByRole('searchbox', { name: 'Pesquisar registros' }).fill('Novo Aluno');
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await page.getByRole('link', { name: 'Ver detalhes', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Detalhes do Aluno' })).toBeVisible();
    await page.getByRole('button', { name: 'Editar dados', exact: true }).click();
    await page.locator('input[name="email"]').fill('admin@teste.local');
    await page.getByRole('button', { name: 'Salvar Alterações' }).click();
    await expect(page.locator('form.aluno-edit-form').getByRole('alert')).toContainText('ja cadastrados');
    await page.locator('input[name="email"]').fill('novo@teste.local');
    await page.locator('input[name="nome"]').fill('Novo Aluno Editado');
    await page.getByRole('button', { name: 'Salvar Alterações' }).click();
    await expect(page.locator('form.aluno-edit-form').getByRole('status')).toBeVisible();
    await fecharJanela(page);
    await expect(page.getByRole('heading', { name: 'Novo Aluno Editado' })).toBeVisible();
    await page.getByRole('tab', { name: 'Enviados', exact: true }).click();
    await expect(page.getByText('Nenhum documento enviado para este aluno.')).toBeVisible();
    await page.goBack();
    await expect(page.getByRole('heading', { name: 'Banco de Dados', exact: true })).toBeVisible();
    expect(await page.evaluate(() => window.__spaMarker)).toBe('mounted-once');
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Banco de Dados', exact: true })).toBeVisible();
    await page.getByRole('searchbox', { name: 'Pesquisar registros' }).fill('sem resultado');
    await expect(page.getByText('Nenhum registro encontrado para o filtro selecionado.')).toBeVisible();
    expect(errors).toEqual([]);
});

test('admin solicita documentos, aluno e professor enviam arquivos', async ({ page }) => {
    const errors = observeErrors(page);
    await login(page, 'admin');
    await page.goto('/admin/alunos/1');
    await page.getByRole('button', { name: 'Solicitar documento', exact: true }).click();
    const requestForm = page.locator('form').filter({ has: page.getByRole('button', { name: 'Disparar solicitação' }) });
    await requestForm.locator('input[name="titulo"]').fill('Comprovante SPA');
    await requestForm.locator('textarea').fill('Enviar para secretaria');
    await requestForm.getByRole('button').click();
    await expect(requestForm.getByRole('status')).toBeVisible();
    await fecharJanela(page);
    await expect(page.getByText('Comprovante SPA', { exact: true })).toBeVisible();
    await page.goto('/admin/professores/1');
    await expect(page.getByRole('heading', { name: 'Detalhes do Professor' })).toBeVisible();
    await page.getByRole('tab', { name: 'Documentos', exact: true }).click();
    await page.getByRole('button', { name: 'Solicitar documento', exact: true }).click();
    const teacherRequest = page.locator('form').filter({ has: page.getByRole('button', { name: 'Disparar solicitação' }) });
    await teacherRequest.locator('input[name="titulo"]').fill('Diploma SPA');
    await teacherRequest.getByRole('button').click();
    await expect(teacherRequest.getByRole('status')).toBeVisible();
    await fecharJanela(page);
    await expect(page.getByText('Diploma SPA', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'aluno');
    await page.getByRole('tab', { name: 'Documentos', exact: true }).click();
    await page.getByRole('button', { name: 'Enviar documento', exact: true }).click();
    const studentUpload = page.locator('form').filter({ has: page.locator('input[name="solicitacao_id"]') });
    await studentUpload.locator('input[type="file"]').setInputFiles(upload);
    await studentUpload.getByRole('button', { name: 'Enviar', exact: true }).click();
    await expect(page.getByText('Enviado', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'professor');
    await page.getByRole('tab', { name: 'Documentos', exact: true }).click();
    await page.getByRole('button', { name: 'Enviar documento', exact: true }).click();
    const teacherUpload = page.locator('form').filter({ has: page.locator('input[name="solicitacao_id"]') });
    await teacherUpload.locator('input[type="file"]').setInputFiles(upload);
    await teacherUpload.locator('button').click();
    await expect(page.getByText('Enviado', { exact: true })).toBeVisible();
    const download = page.waitForEvent('download');
    await page.getByRole('link', { name: 'Baixar', exact: true }).click();
    expect((await download).suggestedFilename()).toContain('comprovante.txt');
    expect(errors).toEqual([]);
});

test('professor lança atividade e nota; aluno consulta disciplina e histórico', async ({ page }) => {
    const errors = observeErrors(page);
    await login(page, 'professor');
    await page.getByRole('button', { name: 'Turma Teste', exact: true }).click();
    const turmaTeste = page.locator('article.professor-card').filter({ has: page.locator('h3').filter({ hasText: /^Turma Teste$/ }) });
    await turmaTeste.getByRole('button', { name: 'Lançar atividade', exact: true }).click();
    const activity = page.getByRole('dialog', { name: 'Nova atividade', exact: true }).locator('form.professor-activity-form');
    await activity.locator('input[name="titulo"]').fill('Atividade SPA');
    await activity.locator('textarea').fill('Resolver exercícios');
    await activity.locator('input[name="arquivo"]').setInputFiles(upload);
    await page.screenshot({ path: '/tmp/secretaria-atividade-modal.png', fullPage: true });
    await activity.getByRole('button', { name: 'Lançar atividade' }).click();
    await expect(activity.getByRole('status')).toBeVisible();
    await fecharJanela(page);
    await expect(page.getByText('Atividade SPA', { exact: true })).toBeVisible();
    await expect(turmaTeste.getByRole('button', { name: 'Lançar nota', exact: true })).toHaveCount(0);
    await fecharJanela(page);
    await page.getByRole('tab', { name: 'Notas', exact: true }).click();
    await page.getByRole('button', { name: 'Lançar notas', exact: true }).click();
    const grade = page.getByRole('dialog', { name: 'Lançar notas', exact: true }).locator('form.professor-grade-form').first();
    await grade.locator('input[name="nota"]').fill('8.5');
    await grade.locator('input[name="observacao"]').fill('Nota SPA');
    await grade.getByRole('button').click();
    await expect(grade.getByRole('status')).toContainText('Nota salva');
    await fecharJanela(page);
    await page.getByRole('tab', { name: 'Notas', exact: true }).click();
    await expect(page.getByRole('cell', { name: 'Nota SPA' })).toBeVisible();
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'aluno');
    await page.getByRole('link', { name: /Matemática/ }).click();
    await expect(page).toHaveURL(/\/aluno\/disciplinas\/1$/);
    await expect(page.getByText('Atividade SPA', { exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByText('Atividade SPA', { exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Professores', exact: true })).toHaveCount(0);
    const entregaActivity = page.locator('article.aluno-exclusive-activity').filter({ hasText: 'Atividade SPA' });
    await entregaActivity.getByRole('button', { name: 'Enviar atividade', exact: true }).click();
    await page.getByLabel('Arquivo da atividade').setInputFiles(upload);
    await page.getByRole('button', { name: 'Confirmar envio' }).click();
    await expect(page.getByRole('dialog').getByRole('status')).toContainText('Atividade enviada');
    await fecharJanela(page);
    await expect(entregaActivity.getByText('Atividade enviada', { exact: true })).toBeVisible();
    const entregaHref = await entregaActivity.getByRole('link', { name: /Baixar minha entrega/ }).getAttribute('href');
    expect((await page.request.get(entregaHref)).status()).toBe(200);
    await page.reload();
    await expect(entregaActivity.getByText('Atividade enviada', { exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'Voltar', exact: true }).click();
    await page.getByRole('tab', { name: 'Notas', exact: true }).click();
    await expect(page.getByRole('cell', { name: 'Nota SPA' })).toBeVisible();
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'professor');
    await page.getByRole('tab', { name: 'Documentos', exact: true }).click();
    await expect(page.getByText('Entrega de Aluno Teste', { exact: true })).toBeVisible();
    expect((await page.request.get(entregaHref)).status()).toBe(200);
    expect(errors).toEqual([]);
});

test('permissões, sessão expirada, URLs antigas e erro de registro', async ({ page, context }) => {
    const errors = observeErrors(page);
    await login(page, 'aluno');
    const forbidden = await page.request.get('/api/admin/dashboard');
    expect(forbidden.status()).toBe(403);
    expect(await forbidden.json()).toHaveProperty('erro');
    await page.goto('/admin/dashboard');
    await expect(page).toHaveURL(/\/aluno$/);
    await page.getByRole('tab', { name: 'Notas', exact: true }).click();
    await context.clearCookies();
    await page.reload();
    await expect(page).toHaveURL(/\/login$/);
    await login(page, 'admin');
    await page.goto('/admin_detalhes_aluno.html?id=1');
    await expect(page).toHaveURL(/\/admin\/alunos\/1$/);
    await expect(page.getByRole('heading', { name: 'Detalhes do Aluno' })).toBeVisible();
    await page.goto('/admin/alunos/999999');
    await expect(page.getByRole('heading', { name: 'Página ou registro não encontrado' })).toBeVisible();
    const expired = await page.request.post('/api/logout');
    expect(expired.ok()).toBeTruthy();
    const denied = await page.request.post('/api/professor/notas/salvar', { form: { nota: '10' } });
    expect(denied.status()).toBe(401);
    expect(errors).toEqual([]);
});

test('administrador gerencia secretaria, permissões e troca obrigatória de senha', async ({ page }) => {
    const errors = observeErrors(page);
    await page.goto('/login');
    await page.getByRole('textbox', { name: 'E-mail Institucional' }).fill('gestor@teste.local');
    await page.getByRole('textbox', { name: 'Senha', exact: true }).fill('teste123');
    await page.getByRole('button', { name: 'Acessar Sistema' }).click();
    await expect(page).toHaveURL(/\/gestao$/);
    await expect(page.getByRole('heading', { name: 'Administração geral' })).toBeVisible();
    await page.getByRole('button', { name: 'Nova conta', exact: true }).click();
    await page.getByRole('textbox', { name: 'E-mail', exact: true }).fill('secretaria.nova@teste.local');
    await page.getByLabel('Senha inicial').fill('temporaria123');
    await page.getByLabel('Gerenciar turmas e disciplinas').uncheck();
    await page.getByRole('button', { name: 'Salvar conta' }).click();
    await expect(page.getByRole('status')).toContainText('Conta salva');
    await expect(page.getByRole('cell', { name: 'secretaria.nova@teste.local', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Auditoria', exact: true }).click();
    await expect(page.getByRole('cell', { name: 'Conta criada', exact: true })).toBeVisible();
    await page.screenshot({ path: '/tmp/secretaria-admin-gestao.png', fullPage: true });
    await page.getByRole('button', { name: 'Configurações', exact: true }).click();
    await page.getByRole('button', { name: 'Editar configurações', exact: true }).click();
    await page.getByLabel('Ano letivo').fill('2027');
    await page.getByRole('button', { name: 'Salvar configurações' }).click();
    await expect(page.getByRole('status')).toContainText('Configurações salvas');
    await page.getByRole('button', { name: 'Backup', exact: true }).click();
    await expect(page.getByRole('link', { name: 'Baixar backup do banco' })).toBeVisible();
    await page.screenshot({ path: '/tmp/secretaria-botoes-backup.png', fullPage: true });
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await page.getByRole('textbox', { name: 'E-mail Institucional' }).fill('secretaria.nova@teste.local');
    await page.getByRole('textbox', { name: 'Senha', exact: true }).fill('temporaria123');
    await page.getByRole('button', { name: 'Acessar Sistema' }).click();
    await expect(page).toHaveURL(/\/alterar-senha$/);
    await page.getByLabel('Senha atual').fill('temporaria123');
    await page.getByLabel('Nova senha').fill('permanente123');
    await page.getByRole('button', { name: 'Salvar nova senha' }).click();
    await expect(page).toHaveURL(/\/admin\/dashboard$/);
    expect((await page.request.get('/api/gestao/painel')).status()).toBe(403);
    expect((await page.request.post('/api/admin/disciplinas', { form: { nome: 'Bloqueada', codigo: 'BLOCK' } })).status()).toBe(403);
    expect(errors).toEqual([]);
});

test('secretaria monta cronograma em Turmas e aluno consulta grade semanal', async ({ page }) => {
    await login(page, 'admin');
    await page.goto('/admin/turmas');
    await page.getByRole('button', { name: 'Turma Teste', exact: true }).click();
    const detalhesTurma = page.getByRole('dialog', { name: 'Turma Teste', exact: true });
    await detalhesTurma.getByRole('button', { name: 'Disciplinas e cronograma', exact: true }).click();
    await detalhesTurma.getByRole('button', { name: 'Gerenciar disciplinas e horários', exact: true }).click();
    const gerenciamento = page.getByRole('dialog', { name: 'Gerenciar disciplinas e horários', exact: true });
    const cronograma = gerenciamento.getByRole('region', { name: 'Cronograma semanal da turma', exact: true });
    await cronograma.getByLabel('Disciplina do cronograma').selectOption('1');
    await cronograma.getByLabel('Início da aula').fill('07:00');
    await cronograma.getByLabel('Fim da aula').fill('07:50');
    await cronograma.getByLabel('Segunda', { exact: true }).check();
    await cronograma.getByLabel('Quarta', { exact: true }).check();
    await cronograma.getByRole('button', { name: 'Associar disciplina e salvar horários' }).click();
    await expect(cronograma.getByRole('status')).toContainText('cronograma salvo');
    await cronograma.getByLabel('Disciplina do cronograma').selectOption('1');
    await cronograma.getByLabel('Início da aula').fill('07:00');
    await cronograma.getByLabel('Fim da aula').fill('07:50');
    await cronograma.getByLabel('Segunda', { exact: true }).check();
    await cronograma.getByRole('button', { name: 'Associar disciplina e salvar horários' }).click();
    await expect(cronograma.getByRole('alert')).toContainText('já possui aula');
    await cronograma.getByRole('button', { name: 'Editar horário', exact: true }).first().click();
    await cronograma.getByLabel('Início da aula').fill('08:00');
    await cronograma.getByLabel('Fim da aula').fill('08:50');
    await cronograma.getByRole('button', { name: 'Salvar alteração do horário' }).click();
    await expect(cronograma.getByRole('status')).toContainText('cronograma salvo');
    await gerenciamento.getByRole('button', { name: 'Fechar gerenciamento do cronograma' }).click();
    await expect(detalhesTurma.getByRole('region', { name: 'Grade semanal de disciplinas' })).toBeVisible();
    await page.screenshot({ path: '/tmp/secretaria-turma-grade-limpa.png', fullPage: true });
    await detalhesTurma.getByRole('button', { name: 'Fechar detalhes da turma' }).click();
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'aluno');
    const grade = page.getByRole('region', { name: 'Grade semanal de disciplinas', exact: true });
    await expect(grade.getByRole('columnheader', { name: /Segunda/ })).toBeVisible();
    await expect(grade.getByRole('link', { name: /Matemática/ })).toHaveCount(2);
    await page.screenshot({ path: '/tmp/secretaria-grade-semanal.png', fullPage: true });
    await grade.getByRole('link', { name: /Matemática/ }).first().click();
    await expect(page).toHaveURL(/\/aluno\/disciplinas\/1$/);
});


test('painel e banco abrem diretamente os detalhes de alunos e professores', async ({ page }) => {
    await login(page, 'admin');
    for (const path of ['/admin/dashboard', '/admin/banco-de-dados']) {
        for (const [nome, tipo] of [['Aluno Teste', 'alunos'], ['Professor Teste', 'professores']]) {
            await page.goto(path);
            const row = page.locator('tbody tr').filter({ hasText: nome }).first();
            await row.getByRole('link', { name: 'Ver detalhes', exact: true }).click();
            await expect(page).toHaveURL(new RegExp(`/admin/${tipo}/1$`));
            await expect(page.getByRole('dialog')).toHaveCount(0);
        }
    }
});

test('paginação da secretaria e gestão mantém busca em toda a base', async ({ page }) => {
    await login(page, 'admin');
    for (let n = 0; n < 12; n++) {
        const response = await page.request.post('/api/cadastro/aluno', { form: {
            nome: `Paginação ${n}`, email: `paginacao${n}@teste.local`, senha: 'teste1234',
            matricula: `PAG${n}`, cpf: `90000000${String(n).padStart(3, '0')}`,
        } });
        expect(response.ok()).toBeTruthy();
    }
    await page.goto('/admin/banco-de-dados');
    await page.getByLabel('Tipo de registro').selectOption('aluno');
    const pagination = page.getByRole('navigation', { name: 'Paginação de usuários' });
    await expect(pagination.getByLabel('Por página')).toBeEnabled();
    await pagination.getByLabel('Por página').selectOption('10');
    await expect(pagination.getByText(/Página 1 de/)).toBeVisible();
    await expect(pagination.getByRole('button', { name: 'Próxima' })).toBeEnabled();
    await pagination.getByRole('button', { name: 'Próxima' }).click();
    await expect(pagination.getByText(/Página 2 de/)).toBeVisible();
    await page.getByLabel('Pesquisar registros').fill('paginacao11@teste.local');
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await expect(page.getByRole('cell', { name: /paginacao11@teste.local/ })).toBeVisible();
    await expect(pagination.getByText('Página 1 de 1')).toBeVisible();
    await page.request.post('/api/logout');
    await page.goto('/login');
    await page.getByLabel('E-mail Institucional').fill('gestor@teste.local');
    await page.getByRole('textbox', { name: 'Senha', exact: true }).fill('teste123');
    await page.getByRole('button', { name: 'Acessar Sistema' }).click();
    await expect(pagination.getByLabel('Por página')).toBeEnabled();
    await pagination.getByLabel('Por página').selectOption('10');
    await expect(pagination.getByRole('button', { name: 'Próxima' })).toBeEnabled();
    await pagination.getByRole('button', { name: 'Próxima' }).click();
    await expect(pagination.getByText(/Página 2 de/)).toBeVisible();
    await page.getByLabel('Pesquisar usuários').fill('paginacao11@teste.local');
    await expect(page.getByRole('cell', { name: 'paginacao11@teste.local', exact: true })).toBeVisible();
    await expect(page.locator('tbody tr')).toHaveCount(1);
    await expect(pagination.getByText('Página 1 de 1')).toBeVisible();
});

 test('comunicados completos na página com paginação', async ({ page }) => {
    await login(page, 'admin');
    for (let n = 0; n < 12; n++) {
        expect((await page.request.post('/api/admin/comunicados', { form: { titulo: `Recado paginado ${n}`, mensagem: `Conteúdo completo do recado ${n}` } })).ok()).toBeTruthy();
    }
    await page.goto('/admin/comunicados');
    const pagination = page.getByRole('navigation', { name: 'Paginação de comunicados' });
    await expect(pagination.getByLabel('Por página')).toBeEnabled();
    await pagination.getByLabel('Por página').selectOption('10');
    await expect(page.locator('article')).toHaveCount(10);
    await expect(page.getByText('Conteúdo completo do recado 11', { exact: true })).toBeVisible();
    await expect(pagination.getByRole('button', { name: 'Próxima' })).toBeEnabled();
    await pagination.getByRole('button', { name: 'Próxima' }).click();
    await expect(pagination.getByText('Página 2 de 2')).toBeVisible();
    await page.getByRole('button', { name: 'Novo comunicado', exact: true }).click();
    await page.getByLabel('Título do Recado').fill('Novo recado na primeira página');
    await page.getByLabel('Mensagem', { exact: true }).fill('Mensagem inteira sem janela');
    await page.getByRole('button', { name: 'Disparar Comunicado' }).click();
    await expect(page.getByRole('dialog').getByRole('status')).toBeVisible();
    await fecharJanela(page);
    await expect(page.getByRole('heading', { name: 'Novo recado na primeira página' })).toBeVisible();
    await expect(pagination.getByText('Página 1 de 2')).toBeVisible();
    await expect(page.getByRole('dialog')).toHaveCount(0);
});

test('aluno consulta três comunicados e carrega mais cinco por vez', async ({ page }) => {
    await login(page, 'admin');
    for (let n = 0; n < 14; n++) {
        expect((await page.request.post('/api/admin/comunicados', { form: { titulo: `Aviso ao aluno ${n}`, mensagem: `Mensagem ${n}`, destinatario: n === 13 ? 'Professores' : 'Alunos' } })).ok()).toBeTruthy();
    }
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'aluno');
    await page.getByRole('tab', { name: 'Comunicados', exact: true }).click();
    const panel = page.getByRole('tabpanel', { name: 'Comunicados', exact: true });
    await expect(panel.locator('article')).toHaveCount(3);
    await expect(panel.getByRole('heading', { name: 'Aviso ao aluno 12', exact: true })).toBeVisible();
    await expect(panel.getByText('Aviso ao aluno 13', { exact: true })).toHaveCount(0);
    await panel.getByRole('button', { name: 'Carregar mais' }).click();
    await expect(panel.locator('article')).toHaveCount(8);
    await panel.getByRole('button', { name: 'Carregar mais' }).click();
    await expect(panel.locator('article')).toHaveCount(13);
    while (await panel.getByRole('button', { name: 'Carregar mais' }).count()) {
        const before = await panel.locator('article').count();
        await panel.getByRole('button', { name: 'Carregar mais' }).click();
        await expect.poll(() => panel.locator('article').count()).toBeGreaterThan(before);
        expect(await panel.locator('article').count()).toBeLessThanOrEqual(before + 5);
    }
    const scroll = panel.getByLabel('Comunicados da escola');
    expect(await scroll.evaluate(el => getComputedStyle(el).overflowY)).toBe('auto');
    await page.goto('/aluno/disciplinas/1');
    await page.getByRole('link', { name: 'Comunicados', exact: true }).click();
    await expect(page.getByRole('tabpanel', { name: 'Comunicados', exact: true })).toBeVisible();
});


test('consulta de comunicados disponível ao professor e restrita aos perfis acadêmicos', async ({ page }) => {
    await login(page, 'professor');
    await page.getByRole('tab', { name: 'Comunicados', exact: true }).click();
    await expect(page.getByRole('tabpanel', { name: 'Comunicados', exact: true })).toBeVisible();
    expect((await page.request.get('/api/professor/comunicados')).status()).toBe(200);
    expect((await page.request.get('/api/aluno/comunicados')).status()).toBe(403);
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'admin');
    expect((await page.request.get('/api/professor/comunicados')).status()).toBe(403);
    expect((await page.request.get('/api/aluno/comunicados')).status()).toBe(403);
    await expect(page.getByRole('tab', { name: 'Comunicados', exact: true })).toHaveCount(0);
});


test('ações de documentos nos detalhes têm espaçamento uniforme', async ({ page }) => {
    await login(page, 'admin');
    for (const path of ['/admin/alunos/1', '/admin/professores/1']) {
        await page.goto(path);
        if (path.includes('professores')) await page.getByRole('tab', { name: 'Documentos', exact: true }).click();
        const first = page.getByRole('button', { name: 'Solicitar documento', exact: true });
        const second = page.getByRole('button', { name: 'Enviar arquivo', exact: true });
        await expect(first).toBeVisible();
        const a = await first.boundingBox();
        const b = await second.boundingBox();
        expect(b.x - a.x - a.width).toBeGreaterThanOrEqual(15);
        expect(b.height).toBe(a.height);
    }
});


test('professor abre lançamento de notas em janela flutuante', async ({ page }) => {
    await login(page, 'professor');
    await page.getByRole('tab', { name: 'Notas', exact: true }).click();
    const panel = page.getByRole('tabpanel', { name: 'Notas', exact: true });
    await expect(panel.getByRole('heading', { name: 'Notas Lançadas' })).toBeVisible();
    await expect(panel.locator('form').first()).not.toBeVisible();
    await panel.getByRole('button', { name: 'Lançar notas', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Lançar notas', exact: true });
    await expect(dialog).toBeVisible();
    const form = dialog.locator('form').filter({ has: page.locator('input[name="aluno_id"][value="1"]') }).first();
    await form.getByLabel('Nota', { exact: true }).fill('7.75');
    await form.getByLabel('Observação').fill('Nota pela janela');
    await form.getByRole('button', { name: 'Salvar nota', exact: true }).click();
    await expect(form.getByRole('status')).toContainText('Nota salva');
    await fecharJanela(page);
    await expect(panel.getByRole('cell', { name: 'Nota pela janela' })).toBeVisible();
});

test('professor publica conteúdo separado das atividades e aluno consulta material', async ({ page }) => {
    await login(page, 'professor');
    await page.getByRole('button', { name: 'Turma Teste', exact: true }).click();
    await page.getByRole('tab', { name: 'Conteúdos', exact: true }).click();
    await page.getByRole('button', { name: 'Publicar conteúdo', exact: true }).click();
    const modal = page.getByRole('dialog', { name: 'Novo conteúdo', exact: true });
    await modal.getByLabel('Título do conteúdo').fill('Material de estudo separado');
    await modal.getByLabel('Descrição').fill('Leia o material para a próxima aula.');
    await modal.getByLabel('Anexo (opcional)').setInputFiles(upload);
    await expect(modal.getByLabel('Data de entrega')).toHaveCount(0);
    await modal.getByRole('button', { name: 'Publicar conteúdo', exact: true }).click();
    await expect(modal.getByRole('status')).toContainText('Conteúdo publicado');
    await fecharJanela(page);
    await expect(page.getByText('Material de estudo separado', { exact: true })).toBeVisible();
    await fecharJanela(page);
    await page.getByRole('button', { name: 'Sair do Sistema' }).click();
    await login(page, 'aluno');
    await page.goto('/aluno/disciplinas/1');
    await page.getByRole('tab', { name: 'Conteúdos', exact: true }).click();
    const section = page.getByRole('tabpanel', { name: 'Conteúdos', exact: true });
    await expect(section.getByText('Material de estudo separado', { exact: true })).toBeVisible();
    await expect(section.getByRole('button', { name: 'Enviar atividade', exact: true })).toHaveCount(0);
    const href = await section.getByRole('link', { name: 'Baixar arquivo' }).getAttribute('href');
    expect((await page.request.get(href)).status()).toBe(200);
    const data = await (await page.request.get('/api/aluno/disciplinas/1')).json();
    const item = data.atividades.find(a => a.titulo === 'Material de estudo separado');
    expect((await page.request.post(`/api/aluno/atividades/${item.id}/enviar`, { multipart: { arquivo: upload } })).status()).toBe(400);
});
