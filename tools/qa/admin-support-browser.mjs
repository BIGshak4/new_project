// Browser portion of admin-support-smoke.mjs. Uses the disposable accounts
// provided by that harness; no persistent browser profile or real user login.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { writeFileSync } from 'node:fs';

export async function runBrowserChecks({root,url,founder,learner,outsider,reportId,out,pass}) {
  const require = createRequire('C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
  const {chromium} = require('playwright');
  const arg = name => {const i=process.argv.indexOf(name); return i<0 ? null : process.argv[i+1];};
  const practiceOrigin=arg('--practice-origin') || 'http://localhost:3225';
  const adminOrigin=arg('--admin-origin') || 'http://localhost:3226';
  for(const origin of [practiceOrigin,adminOrigin]) {
    const parsed=new URL(origin);
    assert.ok(['localhost','127.0.0.1','jobrun-practice.netlify.app','jobrun-tasks.netlify.app'].includes(parsed.hostname));
  }
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const errors=[];
  let lastPage;
  async function context(account,width=1440) {
    const ctx=await browser.newContext({viewport:{width,height:1000}});
    if(account) await ctx.addInitScript(({key,session})=>localStorage.setItem(key,JSON.stringify(session)),{key:`sb-${new URL(url).hostname.split('.')[0]}-auth-token`,session:account.session});
    return ctx;
  }
  async function capture(page,name) {
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.evaluate(()=>document.fonts.ready);
    const dimensions=await page.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(dimensions.scroll<=dimensions.viewport+1,`${name} has document overflow`);
    await page.screenshot({path:resolve(out,`${name}.png`),fullPage:true});
  }
  try {
    const publicCtx=await context(null,390);
    const publicPage=await publicCtx.newPage();
    await publicPage.goto(`${practiceOrigin}/tour`,{waitUntil:'domcontentloaded'});
    await publicPage.getByRole('button',{name:'נתקלתם בבעיה?',exact:true}).click();
    await publicPage.getByRole('heading',{name:'התחברו כדי לשלוח דיווח'}).waitFor();
    await capture(publicPage,'report-guest-mobile');
    pass('guest report entry explains authentication requirement');
    await publicCtx.close();

    const learnerCtx=await context(learner);
    const page=await learnerCtx.newPage();
    lastPage=page;
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(`${practiceOrigin}/tour?question=example-enabled-decoder`,{waitUntil:'domcontentloaded'});
    await page.getByRole('button',{name:'נתקלתם בבעיה?',exact:true}).click();
    const dialog=page.getByRole('dialog');
    await dialog.getByLabel('כותרת קצרה',{exact:true}).fill('בדיקת דפדפן — דיווח פרטי');
    await dialog.getByLabel('תיאור הבעיה',{exact:true}).fill('בדיקה אוטומטית של טופס הדיווח. הסוגריים Y[3:0] נשמרים ללא שינוי.');
    await page.keyboard.press('Escape');
    await page.getByRole('button',{name:'נתקלתם בבעיה?',exact:true}).click();
    assert.match(await dialog.locator('textarea[id$="-description"]').inputValue(),/Y\[3:0\]/);
    await dialog.locator('input[type=file]').setInputFiles({name:'blocked.svg',mimeType:'image/svg+xml',buffer:Buffer.from('<svg/>')});
    await dialog.getByRole('alert').waitFor();
    pass('closing report preserves draft and active SVG is rejected');
    const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jF1kAAAAASUVORK5CYII=','base64');
    await dialog.locator('input[type=file]').setInputFiles([{name:'browser-pixel.png',mimeType:'image/png',buffer:png},{name:'browser-note.txt',mimeType:'text/plain',buffer:Buffer.from('Synthetic browser attachment.')}]);
    await dialog.getByText('browser-note.txt',{exact:true}).waitFor();
    await capture(page,'report-desktop-he');
    await page.setViewportSize({width:390,height:844});
    await capture(page,'report-mobile-he');
    await dialog.evaluate(element=>{element.scrollTop=element.scrollHeight;});
    await capture(page,'report-actions-mobile-he');
    await page.keyboard.press('Escape');
    await page.locator('.theme-toggle').click();
    await page.locator('.language-switch').click();
    await page.getByRole('menuitemradio',{name:'English',exact:true}).click();
    await page.getByRole('button',{name:'Report a problem',exact:true}).click();
    await dialog.getByLabel('Short subject',{exact:true}).waitFor();
    await capture(page,'report-mobile-en-dark');
    await page.setViewportSize({width:1440,height:1000});
    await capture(page,'report-desktop-en-dark');
    await dialog.getByRole('button',{name:'Send report',exact:true}).scrollIntoViewIfNeeded();
    await capture(page,'report-actions-desktop-en-dark');
    pass('report language and theme switch preserves draft and attachments');
    await dialog.getByRole('button',{name:'Send report',exact:true}).click();
    await dialog.getByRole('heading',{name:'Your report is with us',exact:true}).waitFor({timeout:25000});
    pass('real browser submitted report with PNG and text attachments');
    await page.setViewportSize({width:390,height:844});
    await capture(page,'report-success-mobile');
    await learnerCtx.close();

    const deniedCtx=await context(outsider);
    const deniedPage=await deniedCtx.newPage();
    await deniedPage.goto(adminOrigin,{waitUntil:'domcontentloaded'});
    await deniedPage.getByRole('heading',{name:'החשבון מחובר. נדרשת הרשאת גישה.',exact:true}).waitFor();
    assert.equal(await deniedPage.getByRole('heading',{name:'משתמשים',exact:true}).count(),0);
    pass('non-founder browser cannot open administrative workspace');
    await deniedCtx.close();

    const adminCtx=await context(founder);
    const admin=await adminCtx.newPage();
    lastPage=admin;
    admin.on('pageerror',error=>errors.push(error.message));
    await admin.goto(adminOrigin,{waitUntil:'domcontentloaded'});
    await admin.getByRole('button',{name:'משתמשים',exact:true}).click();
    await admin.getByLabel('חיפוש משתמשים לפי שם או אימייל').fill(learner.email);
    await admin.getByRole('button',{name:'חיפוש',exact:true}).click();
    await admin.getByText(learner.email,{exact:true}).waitFor();
    await capture(admin,'admin-users-desktop');
    await admin.getByRole('button',{name:'ניהול',exact:true}).click();
    await admin.locator('.admin-user-editor').getByLabel('מסלול').selectOption('team');
    await admin.getByRole('button',{name:'שמירת מסלול וגישה',exact:true}).click();
    await admin.getByRole('status').filter({hasText:'המסלול והרשאת הגישה נשמרו'}).waitFor();
    pass('founder browser changes a synthetic user entitlement');
    await admin.setViewportSize({width:390,height:844});
    await capture(admin,'admin-users-mobile');
    await admin.setViewportSize({width:1440,height:1000});
    await admin.getByRole('button',{name:'דיווחי תקלות',exact:true}).click();
    // Queue/detail selectors are deliberately public labels, never test-only bypasses.
    await admin.getByLabel('חיפוש דיווחי תקלות',{exact:true}).fill(reportId);
    await admin.getByRole('button',{name:'חיפוש',exact:true}).click();
    await admin.getByText('בדיקה אוטומטית — אפשר להתעלם',{exact:true}).first().click();
    await admin.locator('#support-detail-title').waitFor();
    await admin.locator('.admin-handling').getByLabel('מצב').selectOption('resolved');
    await admin.locator('.admin-handling').getByLabel('הערות פנימיות').fill('בדיקת דפדפן: הטיפול נשמר ונראה לצוות בלבד.');
    await admin.locator('.admin-handling').getByLabel('סיכום הטיפול').fill('Synthetic end-to-end check completed.');
    await admin.getByRole('button',{name:'שמירת הטיפול',exact:true}).click();
    await admin.getByRole('status').filter({hasText:'הטיפול בפנייה נשמר.'}).waitFor();
    pass('browser triage saves resolution and internal notes');
    await capture(admin,'admin-reports-desktop');
    await admin.setViewportSize({width:390,height:844});
    await capture(admin,'admin-reports-mobile');
    pass('support queue and details remain usable at desktop and phone widths');
    await adminCtx.close();
    assert.deepEqual(errors,[],'No browser runtime errors');
    pass('browser runtime clean');
    return browser;
  } catch(error) {
    if(lastPage && !lastPage.isClosed()) {
      writeFileSync(resolve(out,'browser-failure.txt'),(await lastPage.locator('body').innerText()));
      await lastPage.screenshot({path:resolve(out,'browser-failure.png'),fullPage:true}).catch(()=>{});
    }
    await browser.close();throw error;
  }
}
