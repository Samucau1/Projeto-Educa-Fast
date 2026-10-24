const path = require('node:path');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const { chromium } = require(path.join(root, '.cache/visual/node_modules/playwright'));
const base = process.env.PRIVACY_TEST_URL || 'http://127.0.0.1:5052';
if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(base)) throw Error('Use the isolated local test server.');
(async () => {
  const browser = await chromium.launch({channel:'msedge',headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  const directory=path.join(root,'.cache/visual/privacidade'); fs.mkdirSync(directory,{recursive:true});
  async function login(role) {
    const response=await page.request.post(base+'/login',{data:{email:role+'@teste.local',senha:'Teste-local-2026!'}});
    assert.equal(response.status(),200);
  }
  try {
    await page.goto(base+'/privacidade');
    await page.getByRole('heading',{name:'Privacidade.'}).waitFor();
    await login('aluno'); await page.goto(base+'/minha-privacidade');
    await page.locator('select[name=tipo]').selectOption('correcao');
    await page.locator('textarea[name=detalhe]').fill('Solicitacao de teste visual');
    await page.getByRole('button',{name:'Registrar solicitação'}).click();
    await page.getByText('Solicitacao de teste visual',{exact:true}).waitFor();
    await page.screenshot({path:path.join(directory,'titular-desktop.png'),fullPage:true});
    const download=page.waitForEvent('download');
    await page.getByRole('button',{name:'Baixar meus dados (JSON)'}).click();
    assert.equal((await download).suggestedFilename(),'meus-dados-educafast.json');
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:path.join(directory,'titular-mobile.png'),fullPage:true});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile overflow');
    await login('admin'); await page.goto(base+'/admin/privacidade');
    const form=page.locator('form[action^="/admin/privacidade/"]').first();
    await form.locator('select').selectOption('concluido');
    await form.locator('textarea').fill('Atendimento visual concluido');
    await form.getByRole('button',{name:'Registrar resposta'}).click();
    await page.getByText('Atendimento visual concluido',{exact:false}).waitFor();
    assert.deepEqual(errors,[]);
    console.log('PASS: public notice, student request, JSON download, mobile layout, admin response, no JS errors.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
