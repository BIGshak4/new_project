// Production component QA, with fresh guest sessions. No login, backend writes,
// model calls, synthetic authenticated bank, or preview harness.
// node tools/qa/mineral-theme.mjs [http://localhost:3227]
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {mkdirSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';

const root=resolve(import.meta.dirname,'../..');
const origin=process.argv.find(value=>/^https?:/.test(value)) || 'http://localhost:3227';
const confirm=process.argv.includes('--confirm');
assert.ok(['localhost','127.0.0.1'].includes(new URL(origin).hostname));
const require=createRequire('C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
const {chromium}=require('playwright');
const out=resolve(root,'.impeccable/review/mineral-production');
mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
const checks=[],captures=[],runtimeErrors=[],backendWrites=[],failedRequests=[],materialFindings=[],evidence={};
const pass=name=>{checks.push(name);console.log(`PASS ${name}`);};
const contexts=[];
async function guest(viewport={width:1440,height:1000}) {
  const context=await browser.newContext({viewport,reducedMotion:'reduce',colorScheme:'dark'});
  contexts.push(context);
  const page=await context.newPage();
  page.on('pageerror',e=>runtimeErrors.push(e.message));
  page.on('request',r=>{if(!['GET','HEAD','OPTIONS'].includes(r.method())) backendWrites.push({method:r.method(),url:r.url()});});
  page.on('requestfailed',r=>failedRequests.push({url:r.url(),error:r.failure()?.errorText}));
  return page;
}
async function paint(page) {
  await page.evaluate(()=>document.fonts.ready);
  const decoded=await page.locator('img').evaluateAll(async imgs=>{
    const result=[];
    for(const img of imgs) {
      if(!img.getClientRects().length) continue;
      img.loading='eager'; await img.decode();
      if(!img.naturalWidth) throw new Error(`Image did not decode: ${img.src}`);
      img.scrollIntoView({block:'center',behavior:'instant'});
      await new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done)));
      result.push({alt:img.alt,width:img.naturalWidth,height:img.naturalHeight});
    }
    return result;
  });
  await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
  return decoded;
}
async function noOverflow(page,name) {
  const m=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
  assert.ok(m.scroll<=m.width+1,`${name}: horizontal document overflow ${JSON.stringify(m)}`);
}
async function capture(page,name,{fullPage=false,scrollTop=false}={}) {
  const images=await paint(page);
  if(scrollTop) await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
  await noOverflow(page,name);
  const file=`${name}.png`;
  await page.screenshot({path:resolve(out,file),fullPage,animations:'disabled'});
  captures.push({file,viewport:page.viewportSize(),images});
  console.log(`CAPTURE ${file}`);
}
async function tokens(page) {
  return page.locator('html').evaluate(el=>Object.fromEntries(['paper','surface','surface-2','ink','muted','line','action','action-ink','link','soft','code-comment'].map(k=>[k,getComputedStyle(el).getPropertyValue(`--${k}`).trim().toLowerCase()])));
}
const mineral={'paper':'#e0e6e5','surface':'#f2f6f4','surface-2':'#cbd8d5','ink':'#35204f','muted':'#5b4a68','line':'#687a74','action':'#634086','action-ink':'#fffaf2','link':'#633c87','soft':'#dfd9e8'};
async function theme(page,next) {
  if(await page.locator('html').getAttribute('data-theme')!==next) await page.locator('.theme-toggle').click();
  await page.waitForFunction(value=>document.documentElement.dataset.theme===value,next);
  assert.equal(await page.evaluate(()=>localStorage.getItem('jobrun-theme')),next);
}
async function language(page,next) {
  await page.locator('.language-switch').click();
  await page.getByRole('menuitemradio',{name:next==='en'?'English':'עברית',exact:true}).click();
  await page.waitForFunction(value=>localStorage.getItem('jobrun-language')===value,next);
}
async function landing(page) {
  await page.goto(origin,{waitUntil:'networkidle'});
  await page.locator('.ion-landing').waitFor();
  await page.locator('.ion-landing h1').waitFor();
}
async function xor(page) {
  const group=page.getByRole('group',{name:/XOR/});
  const a=group.locator('button').nth(0),b=group.locator('button').nth(1),output=group.locator('output');
  try {await b.click({timeout:1500});} catch(error) {
    materialFindings.push({kind:'XOR pointer interception',viewport:page.viewportSize(),detail:error.message.split('\n').filter(line=>/intercept|Timeout/.test(line)).join('\n')});
    evidence.pointerGeometry=await b.evaluate(el=>{
      const box=el.getBoundingClientRect(),hit=document.elementFromPoint(box.x+box.width/2,box.y+box.height/2),scene=document.querySelector('.ion-chip-scene');
      const detail=node=>{if(!node)return null;const rect=node.getBoundingClientRect(),css=getComputedStyle(node);return{tag:node.tagName,class:node.className,bounds:{x:rect.x,y:rect.y,width:rect.width,height:rect.height},position:css.position,zIndex:css.zIndex,pointerEvents:css.pointerEvents};};
      return{button:detail(el),centerHit:detail(hit),scene:detail(scene),image:detail(scene?.querySelector('img'))};
    });
  }
  for(const [av,bv] of [[0,0],[0,1],[1,0],[1,1]]) {
    if((await a.getAttribute('aria-pressed'))!==String(!!av)) {await a.focus();await page.keyboard.press('Space');}
    if((await b.getAttribute('aria-pressed'))!==String(!!bv)) {await b.focus();await page.keyboard.press('Space');}
    assert.equal(await output.getAttribute('data-value'),String(av^bv));
  }
  await a.focus(); await page.keyboard.press('Space');
  assert.equal(await a.getAttribute('aria-pressed'),'false');
  await page.keyboard.press('Tab');
  assert.ok(await b.evaluate(el=>el===document.activeElement));
  const focus=await b.evaluate(el=>({visible:el.matches(':focus-visible'),width:getComputedStyle(el).outlineWidth,style:getComputedStyle(el).outlineStyle,color:getComputedStyle(el).outlineColor}));
  assert.ok(focus.visible && focus.style!=='none' && parseFloat(focus.width)>0,`Invisible keyboard focus ${JSON.stringify(focus)}`);
  evidence.landingKeyboardFocus=focus;
}
async function pointerXor(page,label) {
  const group=page.getByRole('group',{name:/XOR/}),a=group.locator('button').nth(0),b=group.locator('button').nth(1);
  for(const [av,bv] of [[0,0],[0,1],[1,0],[1,1]]) {
    if((await a.getAttribute('aria-pressed'))!==String(!!av)) await a.click();
    if((await b.getAttribute('aria-pressed'))!==String(!!bv)) await b.click();
    assert.equal(await group.locator('output').getAttribute('data-value'),String(av^bv));
  }
  pass(`${label}: both XOR inputs accept normal pointer clicks for all four cases`);
}
async function modals(page,mode,captureOne) {
  await page.locator('button[aria-haspopup="dialog"][aria-controls]').click();
  const support=page.locator('[data-jobrun-support-dialog]');
  await support.locator('h3').filter({hasText:/התחברו כדי לשלוח דיווח|Sign in to submit a report/}).waitFor();
  assert.ok(await support.evaluate(el=>el.contains(document.activeElement)));
  await noOverflow(page,`support guest ${mode}`);
  if(captureOne==='support') await capture(page,`support-guest-he-${mode}-desktop`);
  await page.keyboard.press('Escape');
  assert.equal(await support.getAttribute('open'),null);
  assert.ok(await page.locator('button[aria-haspopup="dialog"][aria-controls]').evaluate(el=>el===document.activeElement));
  await page.locator('[data-jobrun-inbox-trigger]').click();
  const inbox=page.locator('[data-jobrun-inbox-dialog]');
  await inbox.getByRole('heading',{name:/העדכונים מחכים לכם בחשבון|Your updates live in your account/}).waitFor();
  assert.ok(await inbox.evaluate(el=>el.contains(document.activeElement)));
  await noOverflow(page,`inbox guest ${mode}`);
  if(captureOne==='inbox') await capture(page,`inbox-guest-he-${mode}-desktop`);
  await page.keyboard.press('Escape');
  assert.equal(await inbox.getAttribute('open'),null);
  assert.ok(await page.locator('[data-jobrun-inbox-trigger]').evaluate(el=>el===document.activeElement));
  pass(`${mode}: real guest support/inbox dialogs, Escape, focus restore`);
}
async function station(page,name) {await page.locator(`[data-muxi-station="${name}"]`).waitFor();}
async function skip(page,name) {await page.getByRole('button',{name:'דלגו על התחנה הזאת',exact:true}).click();await station(page,name);}
async function stageScroll(page,selector) {
  await page.locator(selector).evaluate(el=>el.scrollIntoView({block:'center',behavior:'instant'}));
  await page.evaluate(()=>new Promise(done=>requestAnimationFrame(()=>requestAnimationFrame(done))));
}
function contrast(hex1,hex2) {
  const lum=hex=>{const rgb=hex.startsWith('#')?hex.slice(1).match(/.{2}/g).map(x=>parseInt(x,16)):hex.match(/[\d.]+/g).slice(0,3).map(Number);return rgb.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);};
  const a=lum(hex1),b=lum(hex2);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
}
let current;
try {
  for(const [size,viewport] of [['desktop',{width:1440,height:1000}],['phone',{width:390,height:844}]]) {
    const page=current=await guest(viewport); await landing(page);
    assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
    assert.equal(await page.evaluate(()=>localStorage.getItem('jobrun-theme')),null);
    const t=await tokens(page); for(const [key,value] of Object.entries(mineral)) assert.equal(t[key],value,`${key} Mineral`);
    evidence.mineral=t;
    await xor(page); pass(`${size}: first visit uses exact Mineral light tokens despite dark OS preference; all four XOR cases and keyboard focus`);
    if(confirm) await pointerXor(page,`${size} Hebrew light`);
    await capture(page,`landing-he-light-${size}`,{fullPage:true,scrollTop:true});
    if(size==='desktop') await modals(page,'light','support');
    await language(page,'en'); await page.getByRole('heading',{level:1,name:'Your next idea starts here.'}).waitFor();
    if(confirm) await pointerXor(page,`${size} English light`);
    await capture(page,`landing-en-light-${size}`,{fullPage:true,scrollTop:true});
    await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('.language-switch').innerText(),'EN');
    await language(page,'he'); await theme(page,'dark');
    const d=await tokens(page); assert.equal(d.paper,'#171024');assert.equal(d.surface,'#21182f');evidence.darkIon=d;
    await page.reload({waitUntil:'networkidle'});assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
    if(confirm) await pointerXor(page,`${size} Hebrew dark`);
    await capture(page,`landing-he-dark-${size}`,{fullPage:true,scrollTop:true});
    if(size==='desktop') await modals(page,'dark','inbox');
    pass(`${size}: actual language menu, language reload persistence, saved dark theme persistence, unchanged Ion root tokens`);
    await page.close();
  }
  const page=current=await guest(); await page.goto(`${origin}/tour`,{waitUntil:'networkidle'});
  await page.getByRole('button',{name:'מתחילים בסיור הקצר',exact:true}).click();await station(page,'goal');
  await skip(page,'search');await skip(page,'topics');await skip(page,'code');
  await page.locator('[data-muxi-control="code-open"]').click();
  await page.locator('[data-muxi-control="code-copy"]').click();
  const editor=page.locator('[data-muxi-control="code-input"]'); await editor.waitFor();
  const initial=await editor.innerText();assert.match(initial,/for/);
  await editor.click();await page.keyboard.press('Control+Home');await page.keyboard.press('Control+Shift+End');
  await page.keyboard.insertText(`${initial.replace(/<=/,'<')}\n// Keep the loop inside the array bounds.`);
  const edited=await editor.innerText();assert.notEqual(edited,initial);
  await page.keyboard.press('Control+Home');await page.keyboard.press('Control+Shift+End');
  await page.locator('.cm-selectionBackground').first().waitFor();
  const selection=await page.locator('.cm-selectionBackground').first().evaluate(el=>getComputedStyle(el).backgroundColor);
  assert.equal(selection,'rgb(223, 217, 232)');
  const lightCode=await tokens(page);evidence.codeSelection={background:selection,usesSoft:true,comment:lightCode['code-comment'],commentContrast:contrast(lightCode['code-comment'],mineral.soft)};
  evidence.codeSelection.contrasts=Object.fromEntries(['paper','surface','surface-2','soft'].map(key=>[key,contrast(lightCode['code-comment'],lightCode[key])]));
  evidence.codeSelection.renderedComment=await editor.locator('.cm-line').last().locator('span').first().evaluate(el=>({text:el.textContent,color:getComputedStyle(el).color}));
  if(evidence.codeSelection.commentContrast<4.5) materialFindings.push({kind:'Light code-comment selection contrast',ratio:evidence.codeSelection.commentContrast,foreground:lightCode['code-comment'],background:mineral.soft});
  if(confirm) {
    assert.equal(lightCode['code-comment'],'#695573');
    assert.equal(evidence.codeSelection.renderedComment.color,'rgb(105, 85, 115)');
    for(const [surface,ratio] of Object.entries(evidence.codeSelection.contrasts)) assert.ok(ratio>=4.5,`${surface} code-comment contrast ${ratio}`);
    pass('actual rendered code comment uses #695573 with >=4.5:1 against paper, surface, surface-2 and --soft selection');
  }
  await stageScroll(page,'.technical-code-editor'); await capture(page,'tour-code-selection-he-light-desktop');
  await theme(page,'dark');assert.equal(await editor.innerText(),edited);
  await editor.click();await page.keyboard.press('Control+Home');await page.keyboard.press('Control+Shift+End');
  await capture(page,'tour-code-selection-he-dark-desktop');
  await theme(page,'light');assert.equal(await editor.innerText(),edited);
  pass('real tour CodeMirror edit and selection use --soft; theme switch preserves code draft and mounted editor');
  await page.locator('[data-muxi-control="code-language"]').selectOption('python');
  assert.equal(await editor.getAttribute('dir'),'ltr');
  assert.equal(await editor.innerText(),edited);
  await page.setViewportSize({width:390,height:844});await noOverflow(page,'tour code phone');
  await page.setViewportSize({width:1440,height:1000});
  await skip(page,'simulate');
  await page.locator('[data-muxi-control="circuit-prewired"]').click();
  await page.locator('[data-muxi-control="circuit-simulate"]').click();
  assert.equal(await page.locator('[data-muxi-control="circuit-simulate"]').getAttribute('aria-pressed'),'true');
  await page.locator('[data-muxi-control="circuit-truth-table"]').click();
  const table=page.locator('[data-muxi-target="circuit"] table');await table.waitFor();
  const rows=await table.locator('tbody tr').evaluateAll(rows=>rows.map(r=>[...r.cells].map(c=>c.textContent.trim())));
  assert.deepEqual(rows,[['0','0','0'],['0','1','0'],['1','0','0'],['1','1','1']]);evidence.truthTable=rows;
  await stageScroll(page,'[data-muxi-control="circuit-truth-table"]');
  await capture(page,'tour-and-truth-table-he-light-desktop');
  await theme(page,'dark');assert.deepEqual(await table.locator('tbody tr').evaluateAll(rows=>rows.map(r=>[...r.cells].map(c=>c.textContent.trim()))),rows);
  await stageScroll(page,'.react-flow');
  await capture(page,'tour-and-simulation-he-dark-desktop');
  await page.setViewportSize({width:390,height:844});await noOverflow(page,'tour circuit phone dark');
  await theme(page,'light');await noOverflow(page,'tour circuit phone light');
  pass('real circuit editor prewired AND, local simulation, correct four-row truth table, theme state preservation, phone overflow checks');
  assert.deepEqual(runtimeErrors,[]); assert.deepEqual(backendWrites,[]);
  if(confirm) assert.deepEqual(materialFindings,[]);
  pass('all production component checks have zero page errors, backend writes or model calls');
  writeFileSync(resolve(out,'verification.json'),JSON.stringify({passed:materialFindings.length===0,confirm,origin,checks,captures,evidence,materialFindings,runtimeErrors,backendWrites,failedRequests,limitations:['Authenticated library, practice, history and admin paths were not tested; no real user login was used.','Tour exercises use the real editors with their explicitly labeled local sample data.']},null,2));
} catch(error) {
  writeFileSync(resolve(out,'verification.json'),JSON.stringify({passed:false,origin,error:error.stack,checks,captures,evidence,materialFindings,runtimeErrors,backendWrites,failedRequests},null,2));
  if(current && !current.isClosed()) writeFileSync(resolve(out,'failure.txt'),`${error.stack}\n\n${(await current.locator('body').innerText()).slice(0,18000)}`);
  throw error;
} finally {await browser.close();}
