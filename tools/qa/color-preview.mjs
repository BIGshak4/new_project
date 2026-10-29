// Isolated visual-preview verification. No real sign-in, model request or write.
// node tools/qa/color-preview.mjs [http://localhost:3225]
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

const root=resolve(import.meta.dirname,'../..');
const origin=process.argv[2] || 'http://localhost:3225';
assert.ok(['localhost','127.0.0.1','jobrun-practice.netlify.app'].includes(new URL(origin).hostname));
const require=createRequire('C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {chromium}=require('playwright');
const {colorPalettes}=await import(pathToFileURL(resolve(root,'apps/web/src/app/color-preview/palettes.ts')).href);
const out=resolve(root,'.impeccable/review/color-preview');
mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const page=await context.newPage(), runtimeErrors=[], backendWrites=[], checks=[];
page.on('pageerror',error=>runtimeErrors.push(error.message));
page.on('request',request=>{
  if(/supabase\.co|onrender\.com/.test(request.url()) && !['GET','HEAD','OPTIONS'].includes(request.method())) backendWrites.push({method:request.method(),url:new URL(request.url()).pathname});
});
const pass=name=>{checks.push(name);console.log(`PASS ${name}`);};
function url(palette,screen='home',embed=true) {
  const next=new URL('/color-preview',origin);
  next.search=new URLSearchParams({style:'ion-light',palette,screen,motion:'0',...(embed?{embed:'1'}:{})}).toString();
  return next.href;
}
async function settled() {
  await page.evaluate(()=>document.fonts.ready);
  await page.locator('img').evaluateAll(images=>Promise.all(images.map(async img=>{
    img.loading='eager';
    await img.decode();
    if(!img.naturalWidth) throw new Error('Preview artwork did not decode');
    // Decode is not a paint guarantee in full-page headless captures when a
    // responsive image starts partly below the current viewport.
    img.scrollIntoView({block:'center',behavior:'instant'});
    await new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done)));
  })));
  await page.evaluate(async()=>{
    window.scrollTo({top:0,behavior:'instant'});
    await new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done)));
  });
}
async function capture(name) {
  await settled();
  const metrics=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  assert.ok(metrics.scroll<=metrics.width+1,`${name}: document overflow`);
  assert.equal(await page.locator('body > button[aria-haspopup="dialog"][aria-controls]:visible').count(),0,`${name}: host support launcher leaked into the preview`);
  await page.screenshot({path:resolve(out,`${name}.png`),fullPage:true});
}
try {
  for(const palette of colorPalettes) {
    for(const screen of ['home','library']) {
      await page.goto(url(palette.id,screen),{waitUntil:'networkidle'});
      await page.locator(`[data-color-palette="${palette.id}"]`).waitFor();
      await page.getByRole('heading',{level:1}).waitFor();
      const actual=await page.locator(`[data-color-palette="${palette.id}"] > div[dir][lang]`).evaluate(element=>getComputedStyle(element).getPropertyValue('--bg').trim());
      assert.equal(actual.toLowerCase(),palette.tokens.bg.toLowerCase(),`${palette.id}: effective background token`);
      await capture(`${palette.id}-${screen}-desktop`);
      pass(`${palette.id}: ${screen} renders with its own palette and no overflow`);
    }
  }
  for(const id of ['sage','graphite','forest']) {
    await page.setViewportSize({width:390,height:844});
    await page.goto(url(id),{waitUntil:'networkidle'});
    await capture(`${id}-home-mobile`);
    await page.goto(url(id,'library'),{waitUntil:'networkidle'});
    await capture(`${id}-library-mobile`);
    pass(`${id}: phone landing and library remain readable without page overflow`);
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.goto(url('sage','home',false),{waitUntil:'networkidle'});
  assert.equal(await page.locator('[data-color-palette-button]').count(),10);
  await page.locator('[data-color-palette-button="forest"]').click();
  await page.locator('[data-color-preview-frame]').waitFor();
  assert.match(await page.locator('[data-color-preview-frame]').getAttribute('src'),/palette=forest/);
  await page.frameLocator('[data-color-preview-frame]').locator('[data-color-palette="forest"]').waitFor();
  await page.locator('[data-preview-screen="library"]').click();
  assert.match(await page.locator('[data-color-preview-frame]').getAttribute('src'),/screen=library/);
  await page.frameLocator('[data-color-preview-frame]').getByRole('heading',{name:'שאלה טובה. התחלה טובה.',exact:true}).waitFor();
  await capture('gallery-desktop');
  await page.setViewportSize({width:390,height:844});
  await capture('gallery-mobile');
  pass('gallery exposes all ten styles and keeps screen and palette in its frame URL');
  await page.setViewportSize({width:1440,height:1000});
  await page.goto(url('fog','library'),{waitUntil:'networkidle'});
  const storageBefore=await page.evaluate(()=>JSON.stringify({...localStorage}));
  const htmlTheme=await page.locator('html').getAttribute('data-theme');
  await page.getByPlaceholder('שאלה, נושא או חברה… למשל אינטל').fill('אינטל');
  await page.getByRole('button',{name:'Switch to English',exact:true}).click();
  await page.getByRole('heading',{name:'A good question. A good start.',exact:true}).waitFor();
  assert.equal(await page.locator('html').getAttribute('data-theme'),htmlTheme);
  assert.equal(await page.evaluate(()=>JSON.stringify({...localStorage})),storageBefore);
  pass('local search and language work without changing production preferences');
  assert.deepEqual(runtimeErrors,[]); assert.deepEqual(backendWrites,[]);
  pass('clean runtime and no backend writes in the preview');
  writeFileSync(resolve(out,'verification.json'),JSON.stringify({passed:true,clientDate:'2026-10-29',checks,variants:colorPalettes.map(({id,name,tokens,theme})=>({id,name,tokens,theme})),runtimeErrors,backendWrites},null,2));

  // A browser-rendered overview, not a modified raster: every source screenshot
  // remains available at full size for individual comparison and review.
  const html=`<!doctype html><html lang="he" dir="rtl"><meta charset="utf-8"><title>JobRun — עשרה כיווני צבע</title><style>*{box-sizing:border-box}body{margin:0;padding:36px;background:#f2f3f1;color:#35204f;font:18px Arial,sans-serif}h1{font-size:32px;margin:0 0 10px}p{margin:0 0 26px;color:#574b61}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}figure{margin:0;background:white;border:1px solid #c6cec8;border-radius:10px;overflow:hidden}figcaption{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;font-weight:700}img{display:block;width:100%;height:330px;object-fit:cover;object-position:top}span{display:flex;gap:5px}i{display:block;width:22px;height:22px;border-radius:50%;border:1px solid #0002}</style><h1>סגול, אפור וירוק. עשרה כיוונים.</h1><p>אותו אתר, רקעים ואופי שונים. תצוגות עיצוב לבחירה.</p><div class="grid">${colorPalettes.map((p,i)=>`<figure><figcaption>${i+1}. ${p.name}<span>${p.swatches.map(c=>`<i style="background:${c}"></i>`).join('')}</span></figcaption><img src="${p.id}-home-desktop.png" alt="${p.name}"></figure>`).join('')}</div></html>`;
  writeFileSync(resolve(out,'overview.html'),html);
  await page.setViewportSize({width:1500,height:1000});
  await page.goto(pathToFileURL(resolve(out,'overview.html')).href,{waitUntil:'load'});
  await page.screenshot({path:resolve(out,'overview.png'),fullPage:true});
} catch(error) {
  writeFileSync(resolve(out,'failure.txt'),`${error.stack}\n\n${(await page.locator('body').innerText()).slice(0,10000)}`);
  throw error;
} finally {await browser.close();}
