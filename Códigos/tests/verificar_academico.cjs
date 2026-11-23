/* Homologação completa: base nova de executar_postman.py --serve --port 5053. */
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const { chromium } = require(path.join(root, '.cache/visual/node_modules/playwright'));
const base = 'http://127.0.0.1:5053';
const out = path.join(root, 'Documentos/testes/resultados/academico-interface');
fs.mkdirSync(out, { recursive: true });
(async () => {
  execFileSync(process.execPath, [path.join(__dirname, 'verificar_cursos.cjs')], { stdio: 'inherit', timeout: 120000 });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  let csrf;
  async function login(role) {
    const response = await page.request.post(base + '/login', { data: { email: role + '@teste.local', senha: 'Teste-local-2026!' } });
    assert.equal(response.status(), 200);
    csrf = (await response.json()).csrf_token;
  }
  async function post(route, data, expected = 200) {
    const response = await page.request.post(base + route, { data, headers: { 'X-CSRF-Token': csrf }, maxRedirects: 0 });
    assert.equal(response.status(), expected, await response.text());
    return response.json();
  }
  async function formPost(route, form) {
    const response = await page.request.post(base + route, { form, headers: { 'X-CSRF-Token': csrf }, maxRedirects: 0 });
    assert.equal(response.status(), 302, await response.text());
  }
  async function noOverflow() {
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1), false);
  }
  try {
    await login('admin');
    await formPost('/admin/turmas', { nome: 'Turma anterior para revisão', codigo: 'LEG-E2E', ano_letivo: '2025' });
    await page.goto(base + '/academico/reconciliar');
    const href = await page.locator('a.course-outline').filter({ hasText: 'Turma anterior' }).getAttribute('href');
    const legada = Number(href.split('/').pop());
    await formPost('/admin/turmas', { action: 'associate_teacher', turma_id: String(legada), professor_id: '1' });
    await page.goto(base + href);
    assert.equal(await page.locator('input[name="confirmadas"]:checked').count(), 0);
    await page.locator('input[name="confirmadas"]').first().check();
    await page.screenshot({ path: path.join(out, 'revisao-desktop.png'), fullPage: true });
    await Promise.all([page.waitForNavigation(), page.getByRole('button', { name: 'Confirmar atribuições revisadas' }).click()]);
    assert.equal(await page.locator('input[name="confirmadas"]:checked').count(), 1);
    await page.goto(base + '/academico');
    const periodForm = page.locator('form[action="/academico/periodos"]');
    await periodForm.locator('[name="turma_id"]').selectOption('1');
    await periodForm.locator('[name="nome"]').fill('1º bimestre');
    await periodForm.locator('[name="ordem"]').fill('1');
    await Promise.all([page.waitForNavigation(), periodForm.getByRole('button', { name: 'Criar período' }).click()]);
    const p2 = (await post('/academico/periodos', { turma_id: 2, nome: '1º bimestre', ordem: 1, media_referencia: '6' }, 201)).periodo_id;
    const meta = await (await page.request.get(base + '/academico?formato=json')).json();
    const v1 = meta.vinculos.find(v => v.turma_id === 1);
    const v2 = meta.vinculos.find(v => v.turma_id === 2);
    const p1 = meta.periodos.find(p => p.turma_id === 1).id;
    await login('professor');
    await page.goto(base + '/academico');
    const assessmentForm = page.locator(`form[action="/academico/avaliacoes"]:has(input[name="periodo_id"][value="${p1}"]):has(input[name="turma_disciplina_id"][value="${v1.id}"])`);
    await assessmentForm.locator('..').getByText('Nova avaliação', { exact: true }).click();
    await assessmentForm.locator('[name="titulo"]').fill('Prova de álgebra 2026');
    await assessmentForm.locator('[name="peso"]').fill('1');
    await Promise.all([page.waitForNavigation(), assessmentForm.getByRole('button', { name: 'Criar avaliação' }).click()]);
    const av = Number(new URL(page.url()).pathname.split('/').pop());
    const gradeForm = page.locator('form').filter({ has: page.locator('input[name="valor"]') }).first();
    await gradeForm.locator('[name="valor"]').fill('8.5');
    await gradeForm.locator('[name="observacao"]').fill('Primeiro ano validado.');
    await Promise.all([page.waitForNavigation(), gradeForm.getByRole('button', { name: 'Salvar nota' }).click()]);
    await Promise.all([page.waitForNavigation(), page.getByRole('button', { name: 'Publicar notas para os alunos' }).click()]);
    await page.screenshot({ path: path.join(out, 'diario-desktop.png'), fullPage: true });
    await noOverflow();
    const av2 = (await post('/academico/avaliacoes', { turma_disciplina_id: v2.id, periodo_id: p2, titulo: 'Prova de álgebra 2027', peso: '1' }, 201)).avaliacao_id;
    await post('/academico/avaliacoes/' + av2 + '/alunos/1', { valor: '5', versao: 0 });
    await post('/academico/avaliacoes/' + av2 + '/publicar', {});
    await login('aluno');
    const boletim = await (await page.request.get(base + '/boletim?formato=json')).json();
    assert.equal(boletim.periodos.find(p => p.ano === 2026).media, '8.50');
    assert.equal(boletim.periodos.find(p => p.ano === 2027).media, '5.00');
    await page.goto(base + '/boletim');
    assert.ok((await page.locator('main').textContent()).includes('8.50'));
    assert.ok((await page.locator('main').textContent()).includes('5.00'));
    await page.screenshot({ path: path.join(out, 'boletim-desktop.png'), fullPage: true });
    await noOverflow();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(out, 'boletim-mobile.png'), fullPage: true });
    await noOverflow();
    await login('admin');
    await post('/academico/periodos/' + p1 + '/estado', { estado: 'fechado', motivo: 'Fechamento após homologação' });
    await login('professor');
    await page.goto(base + '/academico/avaliacoes/' + av);
    assert.equal(await page.locator('input[name="valor"]').count(), 0);
    await post('/academico/avaliacoes/' + av + '/alunos/1', { valor: '9', versao: 1 }, 409);
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(out, 'resumo.json'), JSON.stringify({ aprovado: true, data: new Date().toISOString(),
      cenarios: ['curso reutilizado 2026/2027', 'reconciliação explícita de turma antiga', 'criação de período e avaliação',
        'lançamento e publicação', 'médias independentes entre anos', 'fechamento bloqueia alteração'],
      desktop: '1440x1000', mobile: '390x844', erros_javascript: errors }, null, 2));
    console.log('Homologação acadêmica aprovada: cursos, reconciliação e boletim por ano/período.');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
