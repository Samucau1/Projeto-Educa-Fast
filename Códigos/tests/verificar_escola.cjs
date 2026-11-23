const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const { chromium } = require(path.join(root, '.cache/visual/node_modules/playwright'));
const base = 'http://127.0.0.1:5053';
const out = path.join(root, 'Documentos/testes/resultados/escola-interface');
fs.mkdirSync(out, { recursive: true });
(async () => {
  execFileSync(process.execPath, [path.join(__dirname, 'verificar_academico.cjs')], { stdio: 'inherit', timeout: 120000 });
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  let csrf;
  async function login(role) {
    const r = await page.request.post(base + '/login', { data: { email: role + '@teste.local', senha: 'Teste-local-2026!' } });
    assert.equal(r.status(), 200); csrf = (await r.json()).csrf_token;
  }
  async function post(route, data, expected=200) {
    const r = await page.request.post(base + route, { data, headers: { 'X-CSRF-Token': csrf }, maxRedirects: 0 });
    assert.equal(r.status(), expected, await r.text()); return r.json();
  }
  async function metadata() { return (await page.request.get(base + '/super/escola?formato=json')).json(); }
  async function noOverflow() { assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1), false); }
  try {
    await login('superadmin'); await page.goto(base + '/super/escola');
    await page.screenshot({path:path.join(out,'configuracao-padrao.png'),fullPage:true}); await noOverflow();
    await page.getByText('Criar calendário de um ano', {exact:true}).click();
    const cf=page.locator('form[action="/super/escola/calendarios"]');
    for (const [name,value] of Object.entries({ano:'2028',nome:'Calendário Horizonte',inicio:'2028-01-01',fim:'2028-12-31',meta_letivos:'200'})) await cf.locator(`[name="${name}"]`).fill(value);
    await Promise.all([page.waitForNavigation(),cf.getByRole('button',{name:'Criar calendário',exact:true}).click()]);
    let meta=await metadata(); const cid=meta.calendarios[0].id;
    await post(`/super/escola/calendarios/${cid}/eventos`,{versao:1,titulo:'Recesso da escola',tipo:'recesso',inicio:'2028-02-10'},201);
    await page.goto(base+'/super/escola'); await page.getByText('Criar uma versão das regras acadêmicas',{exact:true}).click();
    const pf=page.locator('[data-school-policy]');
    await pf.locator('[name="nome"]').fill('Semestres Horizonte 2028');
    await pf.locator('[name="calendario_id"]').selectOption(String(cid));
    await pf.locator('[name="divisao"]').selectOption('semestres');
    assert.equal(await pf.locator('[data-school-slot]:visible').count(),2);
    for(const [i,nome,peso,inicio,fim] of [[1,'Primeiro semestre','1','2028-01-01','2028-06-30'],[2,'Segundo semestre','3','2028-07-01','2028-12-31']]) {
      for(const [key,value] of Object.entries({nome,peso,inicio,fim})) await pf.locator(`[name="periodo_${i}_${key}"]`).fill(value);
    }
    await Promise.all([page.waitForNavigation(),pf.getByRole('button',{name:'Criar versão das regras',exact:true}).click()]);
    meta=await metadata(); const pid=meta.politicas[0].id;
    const turma=(await post('/admin/gestao-turmas',{acao:'criar',nome:'Horizonte A',codigo:'HORIZONTE-2028',ano_letivo:2028})).turma_id;
    await post('/admin/gestao-turmas',{acao:'atribuir',turma_id:turma,professor_id:1,disciplina_id:1});
    await post('/admin/gestao-turmas',{acao:'matricular',turma_id:turma,aluno_id:1});
    await post(`/super/escola/politicas/${pid}/aplicar`,{turma_id:turma});
    await page.goto(base+'/super/escola');
    const identity=page.locator('#school-identity');
    await identity.locator('[name="nome"]').fill('Colégio Horizonte'); await identity.locator('[name="sigla"]').fill('CH');
    await identity.locator('[name="subtitulo"]').fill('APRENDER E TRANSFORMAR');
    await identity.getByRole('button',{name:'Experimentar paleta clara'}).click();
    await Promise.all([page.waitForNavigation(),identity.getByRole('button',{name:'Salvar identidade',exact:true}).click()]);
    assert.ok((await page.locator('.brand').textContent()).includes('Colégio Horizonte'));
    await page.screenshot({path:path.join(out,'identidade-clara-desktop.png'),fullPage:true}); await noOverflow();
    await page.setViewportSize({width:390,height:844}); await page.screenshot({path:path.join(out,'identidade-clara-mobile.png'),fullPage:true}); await noOverflow();
    const ac=await (await page.request.get(base+'/academico?formato=json')).json();
    const vinculo=ac.vinculos.find(v=>v.turma_id===turma).id;
    const periods=ac.periodos.filter(p=>p.turma_id===turma);
    for(const [index,periodo] of periods.entries()) {
      await login('professor'); const aid=(await post('/academico/avaliacoes',{turma_disciplina_id:vinculo,periodo_id:periodo.id,titulo:'Avaliação Horizonte',peso:'1'},201)).avaliacao_id;
      await post(`/academico/avaliacoes/${aid}/alunos/1`,{valor:index===0?'8':'6',versao:0}); await post(`/academico/avaliacoes/${aid}/publicar`,{});
      await login('superadmin'); await post(`/academico/periodos/${periodo.id}/estado`,{estado:'fechado',motivo:'Conferência institucional'});
    }
    await login('aluno'); const report=await (await page.request.get(base+'/boletim?formato=json')).json();
    assert.equal(report.anuais.find(a=>a.ano===2028).media,'6.50');
    await page.setViewportSize({width:1440,height:1000}); await page.goto(base+'/boletim');
    await page.screenshot({path:path.join(out,'boletim-personalizado-desktop.png'),fullPage:true}); await noOverflow();
    await page.setViewportSize({width:390,height:844}); await page.screenshot({path:path.join(out,'boletim-personalizado-mobile.png'),fullPage:true}); await noOverflow();
    await page.goto(base+'/calendario-escolar'); assert.ok((await page.locator('main').textContent()).includes('Recesso da escola'));
    assert.equal((await page.request.get(base+'/super/escola')).status(),403);
    const logout=await page.request.post(base+'/logout',{headers:{'X-CSRF-Token':csrf},maxRedirects:0}); assert.equal(logout.status(),302);
    await page.goto(base+'/'); assert.ok((await page.locator('.brand').textContent()).includes('Colégio Horizonte'));
    await page.screenshot({path:path.join(out,'login-personalizado-mobile.png'),fullPage:true}); await noOverflow();
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(out,'resumo.json'),JSON.stringify({aprovado:true,data:new Date().toISOString(),desktop:'1440x1000',mobile:'390x844',cenarios:['padrão EducaFast','calendário e recesso','semestres pesos 1/3','marca e paleta clara','boletim anual 6.50','isolamento do superadmin'],erros_javascript:errors},null,2));
    console.log('Configuração institucional e protocolo visual aprovados em desktop e móvel.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
