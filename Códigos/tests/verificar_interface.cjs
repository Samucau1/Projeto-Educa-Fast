/* Verificação de navegação e responsividade no ambiente manual descartável. */
const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const { chromium } = require(path.join(root, '.cache/visual/node_modules/playwright'));
const base = process.env.MANUAL_URL || 'http://127.0.0.1:5050';
if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(base)) throw new Error('Use apenas o ambiente manual local.');
const screenshots = path.join(root, '.cache/visual/todas-telas');
fs.mkdirSync(screenshots, { recursive: true });

(async () => {
    const browser = await chromium.launch({ channel: 'msedge', headless: true });
    const errors = [];
    const external = [];
    const checked = [];
    try {
        const loginPage = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
        loginPage.on('pageerror', error => errors.push(error.message));
        loginPage.on('request', request => { if (!request.url().startsWith(base + '/')) external.push(request.url()); });
        await loginPage.goto(base);
        await loginPage.screenshot({ path: path.join(screenshots, 'login-desktop.png'), fullPage: true });
        await loginPage.locator('#email').fill('admin@teste.local');
        await loginPage.locator('#senha').fill('incorreta');
        await loginPage.getByRole('button', { name: /Acessar sistema/i }).click();
        await loginPage.locator('#login-error:not([hidden])').waitFor();
        await loginPage.locator('#senha').fill('Teste-local-2026!');
        await loginPage.getByRole('button', { name: /Acessar sistema/i }).click();
        await loginPage.waitForURL('**/admin/dashboard');
        await loginPage.context().clearCookies();
        await loginPage.goto(base);
        await loginPage.setViewportSize({ width: 390, height: 844 });
        await loginPage.screenshot({ path: path.join(screenshots, 'login-mobile.png'), fullPage: true });
        assert(await loginPage.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), 'Login com overflow');
        for (const [url, code] of [['/mensagens', 403], ['/pagina-inexistente', 404]]) {
            const response = await loginPage.goto(base + url);
            assert.equal(response.status(), code);
            await loginPage.getByRole('link', { name: 'Ir para o login' }).waitFor();
            await loginPage.screenshot({ path: path.join(screenshots, 'visitante-' + code + '.png'), fullPage: true });
        }
        await loginPage.close();
        const routes = {
            admin: ['/admin/dashboard', '/admin/cadastro-alunos', '/admin/cadastro-professores', '/admin/banco-de-dados', '/admin/disciplinas', '/admin/turmas', '/admin/comunicados', '/admin/alunos/1', '/admin/professores/1'],
            superadmin: ['/super/usuarios', '/super/layout', '/mensagens'],
            professor: ['/professor', '/mensagens'],
            aluno: ['/aluno', '/aluno/disciplinas/1', '/mensagens']
        };
        for (const [role, urls] of Object.entries(routes)) {
            const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
            await context.route('**/*', route => {
                if (process.env.UI_LOCAL_CSS === '1' && route.request().url().includes('/static/css/app.css')) return route.fulfill({ path: path.join(root, 'Códigos/app/static/css/app.css'), contentType: 'text/css' });
                if (route.request().url().startsWith(base + '/')) return route.continue();
                external.push(route.request().url());
                return route.abort();
            });
            await context.request.post(base + '/login', { data: { email: role + '@teste.local', senha: 'Teste-local-2026!' } });
            const page = await context.newPage();
            page.on('pageerror', error => errors.push(role + ': ' + error.message));
            page.on('response', response => { if (response.url().includes('/static/') && response.status() >= 400) errors.push('Recurso indisponível: ' + response.url()); });
            for (const url of urls) {
                for (const [device, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
                    await page.setViewportSize({ width, height });
                    const response = await page.goto(base + url);
                    assert.equal(response.status(), 200, role + ' ' + url);
                    await page.locator('.workspace-sidebar').waitFor();
                    await page.locator('main h1').first().waitFor();
                    assert.equal(await page.locator('.workspace-sidebar').count(), 1);
                    const overflowing = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
                    if (overflowing) {
                        const details = await page.evaluate(() => [...document.querySelectorAll('body *')].filter(el => el.getBoundingClientRect().right > innerWidth + 2 && !el.closest('.app-table-scroll,.table-scroll,.sidebar-nav')).slice(0, 7).map(el => el.tagName + '.' + el.className));
                        throw new Error('Overflow ' + device + ' ' + role + ' ' + url + ': ' + JSON.stringify(details));
                    }
                    const file = role + '-' + url.replace(/[^a-z0-9]+/gi, '-') + '-' + device + '.png';
                    await page.screenshot({ path: path.join(screenshots, file), fullPage: true });
                    checked.push({ role, url, device });
                }
                if (url === '/aluno' || url === '/professor') {
                    const prefix = role === 'aluno' ? 'aluno' : 'professor';
                    for (const tab of ['notas', 'documentos']) {
                        await page.locator('[data-' + prefix + '-tab="' + tab + '"]').click();
                        assert(await page.locator('[data-' + prefix + '-panel="' + tab + '"]').isVisible(), role + ' aba ' + tab);
                    }
                }
                if (url === '/super/layout') {
                    const original = await page.locator('[name="cor_fundo"]').inputValue();
                    await page.getByRole('button', { name: 'Noturno', exact: true }).click();
                    assert.equal(await page.locator('[name="cor_fundo"]').inputValue(), '#16132b');
                    await page.getByRole('button', { name: 'Desfazer ajustes' }).click();
                    await page.waitForFunction(value => document.querySelector('[name="cor_fundo"]').value === value, original);
                }
                if (url === '/mensagens') {
                    await page.locator('#messages-search').fill('zzzz-sem-resultado');
                    assert(await page.locator('#messages-no-results').isVisible());
                    await page.locator('#messages-search').fill('');
                }
                console.log('OK ' + role + ' ' + url + ' desktop/mobile');
            }
            if (role === 'aluno') {
                for (const [url, code] of [['/admin/dashboard', 403], ['/pagina-inexistente', 404]]) {
                    const response = await page.goto(base + url);
                    assert.equal(response.status(), code);
                    await page.getByRole('link', { name: 'Voltar ao meu painel' }).waitFor();
                    await page.screenshot({ path: path.join(screenshots, 'aluno-' + code + '.png'), fullPage: true });
                }
            }
            await context.close();
        }
        assert.deepEqual(errors, []);
        assert.deepEqual(external, []);
        const summary = { aprovado: true, data_utc: new Date().toISOString(), verificacoes_de_pagina: checked, erros_javascript: errors, recursos_externos: external, observacao: 'Não altera usuários, notas, mensagens ou cores. Teste em Edge com MySQL manual.' };
        const report = path.join(root, 'Documentos/testes/resultados/interface-resumo.json');
        fs.writeFileSync(report, JSON.stringify(summary, null, 2) + '\n');
        console.log('OK: login real, ' + checked.length + ' verificações de página, abas, busca, prévia de cores e recursos locais.');
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exit(1); });
