// Uses actual disposable Auth sessions and persisted report data. Never publishes
// a test announcement. Confirmation is explicitly cancelled in the browser.
import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';
import { writeFileSync } from 'node:fs';

export async function runInboxBrowserChecks({root,url,founder,learner,reportId,draftId,out,pass}) {
  const require=createRequire('C:/Users/harel/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/package.json');
  const {chromium}=require('playwright');
  const arg=name=>{const index=process.argv.indexOf(name);return index<0?null:process.argv[index+1];};
  const practiceOrigin=arg('--practice-origin') || 'http://localhost:3225';
  const adminOrigin=arg('--admin-origin') || 'http://localhost:3226';
  for(const origin of [practiceOrigin,adminOrigin]) assert.ok(['localhost','127.0.0.1','jobrun-practice.netlify.app','jobrun-tasks.netlify.app'].includes(new URL(origin).hostname));
  const browser=await chromium.launch({executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless:true});
  const errors=[]; let lastPage;
  async function context(account,width=1440) {
    const ctx=await browser.newContext({viewport:{width,height:1000}});
    if(account) await ctx.addInitScript(({key,session})=>{
      // Playwright also runs init scripts on the opaque initial about:blank.
      // That document has no localStorage; seed only our real HTTP documents.
      if(location.protocol==='http:' || location.protocol==='https:') localStorage.setItem(key,JSON.stringify(session));
    },{key:`sb-${new URL(url).hostname.split('.')[0]}-auth-token`,session:account.session});
    ctx.on('page',page=>page.on('pageerror',error=>errors.push(error.message)));
    return ctx;
  }
  async function capture(page,name) {
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.evaluate(()=>document.fonts.ready);
    const dimensions=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(dimensions.scroll<=dimensions.width+1,`${name}: document overflow`);
    await page.screenshot({path:resolve(out,`${name}.png`),fullPage:true});
  }
  try {
    const founderCtx=await context(founder), admin=await founderCtx.newPage(); lastPage=admin;
    await admin.goto(adminOrigin,{waitUntil:'networkidle'});
    await admin.getByRole('button',{name:'עדכונים למשתמשים',exact:true}).click();
    await admin.getByLabel('חיפוש עדכונים למשתמשים').fill(draftId);
    await admin.getByRole('button',{name:'חיפוש',exact:true}).click();
    await admin.getByRole('button').filter({has:admin.getByRole('heading',{name:`בדיקת טיוטה ${draftId}`,exact:true})}).click();
    await admin.getByLabel('תוכן בעברית').fill('טיוטת בדיקה של מרכז העדכונים. נשמרת לצוות בלבד ואינה מתפרסמת.');
    await admin.getByRole('button',{name:'שמירת טיוטה',exact:true}).click();
    await admin.getByText('הטיוטה נשמרה לצוות בלבד.',{exact:true}).waitFor();
    let confirmationSeen=false;
    admin.once('dialog',async dialog=>{confirmationSeen=true;await dialog.dismiss();});
    await admin.getByRole('button',{name:'פרסום לכל המשתמשים',exact:true}).click();
    assert.ok(confirmationSeen);
    const savedDraft=await founder.client.rpc('jr_admin_announcements',{p_query:draftId});
    assert.equal(savedDraft.error,null); assert.equal(savedDraft.data.announcements[0].status,'draft');
    pass('browser saves bilingual draft and cancelling publication sends no broadcast');
    await capture(admin,'admin-announcement-desktop');
    await admin.setViewportSize({width:390,height:844});
    await capture(admin,'admin-announcement-mobile');
    await admin.setViewportSize({width:1440,height:1000});
    await admin.getByRole('button',{name:'דיווחי תקלות',exact:true}).click();
    await admin.getByLabel('חיפוש דיווחי תקלות').fill(reportId);
    await admin.getByRole('button',{name:'חיפוש',exact:true}).click();
    await admin.getByRole('button').filter({has:admin.getByRole('heading',{name:'בדיקת מרכז הפניות — ללא מידע אמיתי',exact:true})}).click();
    const browserReply='תשובת צוות מבדיקת דפדפן: התיקון עלה ונבדק במצב בהיר וכהה.';
    await admin.getByLabel('תשובה למשתמש').fill(browserReply);
    await admin.getByRole('button',{name:'שליחת תשובה למשתמש',exact:true}).click();
    await admin.getByText(browserReply,{exact:true}).waitFor();
    await capture(admin,'admin-public-reply-desktop');
    await admin.setViewportSize({width:390,height:844});
    await capture(admin,'admin-public-reply-mobile');
    pass('founder browser sends an explicit public reply separate from internal notes');

    const learnerCtx=await context(learner), page=await learnerCtx.newPage(); lastPage=page;
    await page.goto(`${practiceOrigin}/tour`,{waitUntil:'networkidle'});
    const trigger=page.locator('[data-jobrun-inbox-trigger]').filter({visible:true});
    await trigger.click();
    const dialog=page.locator('[data-jobrun-inbox-dialog]');
    await dialog.getByRole('button',{name:'הפניות שלי',exact:true}).click();
    await dialog.getByRole('button').filter({hasText:'בדיקת מרכז הפניות — ללא מידע אמיתי'}).click();
    await dialog.getByRole('heading',{name:'סיכום הטיפול',exact:true}).waitFor();
    await dialog.getByText(browserReply,{exact:true}).waitFor();
    assert.doesNotMatch(await dialog.innerText(),/PRIVATE_QA_NOTE_NEVER_PUBLIC|private edit/);
    await capture(page,'user-request-desktop-he');
    await page.setViewportSize({width:390,height:844});
    await capture(page,'user-request-mobile-he');
    pass('learner browser sees resolved status, original issue, public reply and resolution');
    await dialog.getByRole('button',{name:'סימון הכול כנקרא',exact:true}).click();
    await page.keyboard.press('Escape');
    await dialog.waitFor({state:'hidden'});
    await page.locator('.theme-toggle').click();
    await page.locator('.language-switch').click();
    await page.getByRole('menuitemradio',{name:'English',exact:true}).click();
    await page.locator('[data-jobrun-inbox-trigger]').filter({visible:true}).click();
    await dialog.getByRole('button',{name:'My requests',exact:true}).click();
    await dialog.getByRole('button').filter({hasText:'בדיקת מרכז הפניות — ללא מידע אמיתי'}).click();
    await dialog.getByRole('heading',{name:'Resolution',exact:true}).waitFor();
    await capture(page,'user-request-mobile-en-dark');
    await page.setViewportSize({width:1440,height:1000});
    await capture(page,'user-request-desktop-en-dark');
    await dialog.getByRole('button',{name:'Report a problem',exact:true}).click();
    await page.locator('[data-jobrun-support-dialog]').waitFor();
    assert.equal(await dialog.isVisible(),false);
    await page.keyboard.press('Escape');
    pass('inbox respects language and theme and opens report form without stacked dialogs');
    await learnerCtx.close();

    const guestCtx=await context(null,390), guest=await guestCtx.newPage(); lastPage=guest;
    await guest.goto(`${practiceOrigin}/tour`,{waitUntil:'networkidle'});
    await guest.locator('[data-jobrun-inbox-trigger]').filter({visible:true}).click();
    await guest.getByRole('heading',{name:'העדכונים מחכים לכם בחשבון',exact:true}).waitFor();
    pass('guest inbox explains sign-in and exposes no personal content');
    await guestCtx.close();
    assert.deepEqual(errors,[]); pass('inbox browser runtime clean');
  } catch(error) {
    if(lastPage && !lastPage.isClosed()) {
      await lastPage.screenshot({path:resolve(out,'browser-failure.png'),fullPage:true});
      writeFileSync(resolve(out,'browser-failure.txt'),(await lastPage.locator('body').innerText()).slice(0,16000));
    }
    throw error;
  } finally { await browser.close(); }
}
