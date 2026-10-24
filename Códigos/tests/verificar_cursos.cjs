/* Fluxo real em navegador. Execute somente contra executar_postman.py --serve --port 5053. */
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const { chromium } = require(path.join(root, '.cache/visual/node_modules/playwright'));
const base = 'http://127.0.0.1:5053';
const out = path.join(root, 'Documentos/testes/resultados/cursos-interface');
fs.mkdirSync(out, { recursive: true });
(async () => {
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
  async function noOverflow() {
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1), false, 'Overflow horizontal');
  }
  try {
    await login('admin');
    const d = await page.request.post(base + '/admin/disciplinas', { form: { nome: 'Matemática E2E', codigo: 'E2E', carga_horaria: '60' }, headers: { 'X-CSRF-Token': csrf }, maxRedirects: 0 });
    assert.equal(d.status(), 302);
    const turma = (await post('/admin/gestao-turmas', { acao: 'criar', nome: 'Turma 2026', codigo: 'E2E26', ano_letivo: 2026 })).turma_id;
    const futura = (await post('/admin/gestao-turmas', { acao: 'criar', nome: 'Turma 2027', codigo: 'E2E27', ano_letivo: 2027 })).turma_id;
    for (const turma_id of [turma, futura]) {
      await post('/admin/gestao-turmas', { acao: 'atribuir', turma_id, professor_id: 1, disciplina_id: 1 });
      await post('/admin/gestao-turmas', { acao: 'matricular', turma_id, aluno_id: 1 });
    }
    await page.goto(base + '/admin/gestao-turmas');
    await page.screenshot({ path: path.join(out, 'gestao-desktop.png'), fullPage: true });
    await noOverflow();
    await login('professor');
    await page.goto(base + '/cursos');
    await page.getByLabel('Título', { exact: true }).fill('Álgebra para todos os anos');
    await page.locator('select[name="disciplina_id"]').selectOption('1');
    await page.getByLabel('Descrição', { exact: true }).fill('Um material reutilizável para aprender com autonomia.');
    await Promise.all([page.waitForURL(/\/cursos\/\d+$/), page.getByRole('button', { name: 'Criar rascunho', exact: true }).click()]);
    const curso = Number(new URL(page.url()).pathname.split('/').pop());
    async function adicionar(tipo, titulo, video) {
      await page.getByText('Adicionar ' + tipo, { exact: true }).click();
      const form = page.locator(`form:has(input[name="acao"][value="adicionar"]):has(input[name="tipo"][value="${tipo}"])`);
      await form.getByLabel('Título', { exact: true }).fill(titulo);
      if (video) await form.getByLabel('Vídeo do YouTube').fill(video);
      await Promise.all([page.waitForNavigation(), form.getByRole('button', { name: 'Adicionar', exact: true }).click()]);
    }
    await adicionar('capitulo', 'Capítulo 1 — Fundamentos');
    await adicionar('tema', 'Tema 1 — Equações');
    await adicionar('aula', 'Aula 1 — Primeiros passos', 'https://youtu.be/abcdefghijk');
    await page.screenshot({ path: path.join(out, 'editor-desktop.png'), fullPage: true });
    await noOverflow();
    await login('admin');
    await page.goto(base + '/cursos/' + curso);
    await Promise.all([page.waitForNavigation(), page.getByRole('button', { name: 'Revisar e publicar' }).click()]);
    const o = (await post('/cursos/' + curso + '/ofertas', { turma_id: turma })).oferta_id;
    const o2 = (await post('/cursos/' + curso + '/ofertas', { turma_id: futura })).oferta_id;
    await login('aluno');
    await page.goto(base + '/cursos');
    assert.equal(await page.getByRole('link', { name: 'Continuar aprendendo' }).count(), 2);
    await page.screenshot({ path: path.join(out, 'biblioteca-desktop.png'), fullPage: true });
    await page.goto(base + '/aprender/' + o);
    assert.equal(await page.locator('iframe').getAttribute('src'), 'https://www.youtube-nocookie.com/embed/abcdefghijk');
    await Promise.all([page.waitForNavigation(), page.getByRole('button', { name: 'Marcar aula como concluída' }).click()]);
    assert.ok((await page.locator('h1').textContent()).includes('Álgebra'));
    assert.ok((await page.locator('main').textContent()).includes('100%'));
    await page.screenshot({ path: path.join(out, 'aula-desktop.png'), fullPage: true });
    await noOverflow();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + '/aprender/' + o2);
    assert.ok((await page.locator('main').textContent()).includes('0 de 1 aulas'));
    await page.screenshot({ path: path.join(out, 'aula-mobile.png'), fullPage: true });
    await noOverflow();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement.tagName), 'A');
    assert.deepEqual(errors, []);
    fs.writeFileSync(path.join(out, 'resumo.json'), JSON.stringify({ aprovado: true, fluxo: 'admin → professor → aluno', desktop: '1440x1000', mobile: '390x844', erros_javascript: errors, limite: 'Player e endereço verificados; reprodução externa do YouTube não homologada.', data: new Date().toISOString() }, null, 2));
    console.log('Interface aprovada: autoria, publicação, duas ofertas anuais, progresso, desktop e mobile.');
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
