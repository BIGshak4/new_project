// Real Auth/RPC checks with disposable accounts. No email, AI call, or broadcast
// is sent. Announcement publishing is tested in rollback-only SQL fixtures.
// node tools/qa/user-inbox-smoke.mjs --run [--browser]
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';

if (!process.argv.includes('--run')) throw new Error('Pass --run to create and clean up disposable QA accounts.');
const root = resolve(import.meta.dirname, '../..');
const require = createRequire(resolve(root, 'apps/web/package.json'));
const { createClient } = require('@supabase/supabase-js');
const envFile = path => Object.fromEntries(readFileSync(path, 'utf8').split(/\r?\n/).flatMap(line => {
  const match = line.match(/^([A-Z_][A-Z_0-9]*)=(.*)$/);
  return match ? [[match[1], match[2].trim().replace(/^(['"])(.*)\1$/, '$2')]] : [];
}));
const server = envFile(resolve(root, 'backend/.env'));
const publicEnv = envFile(resolve(root, 'apps/web/.env.local'));
const url = server.SUPABASE_URL;
assert.equal(new URL(url).hostname, 'djpwvqpsqbkvprlncjjg.supabase.co');
const options = {auth:{persistSession:false,autoRefreshToken:false,detectSessionInUrl:false},global:{fetch:(target,init)=>fetch(target,{...init,signal:AbortSignal.timeout(20000)})}};
const service = createClient(url, server.SUPABASE_SERVICE_ROLE_KEY, options);
const client = () => createClient(url, publicEnv.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, options);
const accounts = [], draftAnnouncements = [], checks = [];
const out = resolve(root, '.impeccable/review/user-inbox');
mkdirSync(out, {recursive:true});
const control = resolve(out, `control-${crypto.randomUUID()}`);
mkdirSync(control);
let failure;
const pass = name => { checks.push(name); console.log(`PASS ${name}`); };
async function ok(operation, name) {
  const result = await operation;
  assert.equal(result.error, null, `${name}: ${result.error?.message}`);
  return result.data;
}
async function denied(operation, name) {
  const started = Date.now(), result = await operation;
  assert.ok(result.error, `${name}: unexpectedly allowed`);
  assert.ok(result.error.code || result.error.status || result.error.statusCode, `${name}: no server rejection`);
  assert.doesNotMatch(result.error.message, /timeout|abort|fetch failed/i);
  assert.ok(Date.now()-started < 15000, `${name}: rejection must be prompt`);
  pass(name);
}
async function account(label, manager=false, member=true) {
  const email = `jobrun-inbox-qa-${label}-${crypto.randomUUID()}@example.com`, password=`${crypto.randomUUID()}Aa7!`;
  const created = await ok(service.auth.admin.createUser({email,password,email_confirm:true,user_metadata:{display_name:`בדיקת מרכז פניות · ${label}`,can_manage_tasks:true}}), 'create synthetic account');
  const entry = {id:created.user.id,email,manager,member,client:client()};
  accounts.push(entry);
  entry.session = (await ok(entry.client.auth.signInWithPassword({email,password}), 'synthetic sign-in')).session;
  return entry;
}
async function coordinate(phase) {
  writeFileSync(resolve(control, `${phase}-request.json`), JSON.stringify({accounts:accounts.map(({id,email,manager,member})=>({id,email,manager,member})),draftAnnouncements},null,2));
  console.log(`QA_${phase.toUpperCase()} ${control}`);
  const deadline=Date.now()+300000;
  while(!existsSync(resolve(control,`${phase}.done`))) {
    if(Date.now()>deadline) throw new Error(`Privileged SQL ${phase} acknowledgement required: ${control}`);
    await new Promise(done=>setTimeout(done,500));
  }
}
try {
  const founder=await account('founder',true), learner=await account('learner'), outsider=await account('outsider',false,false);
  await coordinate('setup');
  await denied(client().rpc('jr_user_inbox'), 'anonymous inbox blocked');
  await denied(learner.client.rpc('jr_admin_announcements'), 'learner cannot manage broadcasts despite forged metadata');
  const reportId=crypto.randomUUID();
  await ok(learner.client.rpc('jr_submit_support_report',{p_id:reportId,p_subject:'בדיקת מרכז הפניות — ללא מידע אמיתי',p_description:'Synthetic inbox verification. Y[3:0] remains literal.',p_category:'bug',p_language:'he',p_page_path:'/',p_question_key:null}), 'create report');
  const inbox=async()=>ok(learner.client.rpc('jr_user_inbox',{p_kind:'support',p_page:1,p_page_size:100,p_language:'he'}),'learner inbox');
  const initial=await inbox(), received=initial.items.find(item=>item.report_id===reportId);
  assert.ok(received && !received.read_at);
  pass('new report appears as unread personal support update');
  await denied(outsider.client.rpc('jr_my_support_detail',{p_id:reportId}), 'another user cannot read report or public reply history');
  await denied(outsider.client.rpc('jr_mark_inbox_read',{p_kind:'support',p_id:received.id}), 'another user cannot mark a private update read');
  await ok(learner.client.rpc('jr_mark_inbox_read',{p_kind:'support',p_id:received.id}), 'mark own update read');
  await ok(learner.client.rpc('jr_mark_inbox_read',{p_kind:'support',p_id:received.id}), 'retry read marker');
  assert.ok((await inbox()).items.find(item=>item.id===received.id).read_at);
  pass('read markers persist and retries are idempotent');
  let detail=await ok(founder.client.rpc('jr_admin_support_detail',{p_id:reportId}),'admin detail');
  const update=async(status,resolution,notes='PRIVATE_QA_NOTE_NEVER_PUBLIC')=>ok(founder.client.rpc('jr_admin_update_support',{p_id:reportId,p_expected_version:detail.report.version,p_status:status,p_priority:'normal',p_assigned_to:null,p_internal_notes:notes,p_resolution:resolution}),'admin update');
  const beforeNotes=(await inbox()).total;
  detail.report=await update('open','');
  assert.equal((await inbox()).total,beforeNotes);
  pass('internal-note changes create no user notification');
  detail.report=await update('in_progress','');
  assert.ok((await inbox()).items.some(item=>item.report_id===reportId && item.status==='in_progress' && !item.read_at));
  const message='בדיקת מערכת: זיהינו את הבעיה ואנחנו בודקים את תצוגת הסוגריים.';
  const replyArgs={p_report_id:reportId,p_expected_version:detail.report.version,p_idempotency_id:crypto.randomUUID(),p_message:message,p_status:null,p_language:'he'};
  const reply=await ok(founder.client.rpc('jr_admin_reply_support',replyArgs),'public reply');
  const retried=await ok(founder.client.rpc('jr_admin_reply_support',replyArgs),'retry public reply');
  assert.equal(reply.update.id,retried.update.id);
  await denied(learner.client.rpc('jr_admin_reply_support',replyArgs),'learner cannot send a team reply');
  await denied(founder.client.rpc('jr_admin_reply_support',{...replyArgs,p_idempotency_id:crypto.randomUUID()}),'stale reply cannot overwrite report version');
  const publicDetail=await ok(learner.client.rpc('jr_my_support_detail',{p_id:reportId}),'safe report detail');
  assert.ok(publicDetail.updates.some(item=>item.body===message));
  assert.doesNotMatch(JSON.stringify(publicDetail),/PRIVATE_QA_NOTE_NEVER_PUBLIC|internal_notes|actor_email|actor_id|assigned_to|reporter_email/);
  pass('public replies arrive once and never include internal notes or staff identity');
  detail=await ok(founder.client.rpc('jr_admin_support_detail',{p_id:reportId}),'fresh admin detail');
  await denied(founder.client.rpc('jr_admin_update_support',{p_id:reportId,p_expected_version:detail.report.version,p_status:'resolved',p_priority:'normal',p_assigned_to:null,p_internal_notes:'PRIVATE_QA_NOTE_NEVER_PUBLIC',p_resolution:''}),'resolution requires a public explanation');
  const resolution='בדיקת מערכת: תיקנו את כיוון הטקסט ובדקנו שסוגריים מוצגים בסדר המקורי.';
  detail.report=await update('resolved',resolution);
  const resolved=await ok(learner.client.rpc('jr_my_support_detail',{p_id:reportId}),'resolved public report');
  assert.equal(resolved.report.status,'resolved'); assert.equal(resolved.report.resolution,resolution);
  assert.ok(resolved.updates.some(item=>item.status==='resolved' && item.body===resolution));
  pass('resolved report includes the actual team explanation and unread notification');
  await ok(learner.client.rpc('jr_mark_all_inbox_read'),'mark all read');
  assert.equal((await inbox()).unread_count,0);
  pass('mark all read persists for this account');
  const draftId=crypto.randomUUID(); draftAnnouncements.push(draftId);
  const draftArgs={p_id:draftId,p_expected_version:0,p_title_he:`בדיקת טיוטה ${draftId}`,p_body_he:'טיוטת בדיקה בלבד. אינה מתפרסמת למשתמשים.',p_title_en:'QA draft only',p_body_en:'This draft is never published.',p_action:'save'};
  const draft=await ok(founder.client.rpc('jr_admin_save_announcement',draftArgs),'save announcement draft');
  assert.equal(draft.status,'draft');
  await denied(founder.client.rpc('jr_admin_save_announcement',{...draftArgs,p_expected_version:0}),'stale announcement save rejected');
  const all=await ok(learner.client.rpc('jr_user_inbox',{p_kind:'all',p_language:'en'}),'learner all updates');
  assert.ok(!all.items.some(item=>item.id===draftId));
  pass('announcement drafts stay founder-only and do not notify users');
  if(process.argv.includes('--browser')) {
    const {runInboxBrowserChecks}=await import('./user-inbox-browser.mjs');
    await runInboxBrowserChecks({root,url,founder,learner,outsider,reportId,draftId,out,pass});
  }
  writeFileSync(resolve(out,'e2e-report.json'),JSON.stringify({passed:true,checks,syntheticAccounts:accounts.length,testBroadcastsPublished:0,checkedAt:new Date().toISOString()},null,2));
} catch(error) { failure=error; console.error(`QA_FAILURE ${error.message}`); }
finally {
  if(accounts.length) await coordinate('cleanup');
  const errors=[];
  for(const entry of accounts.reverse()) {
    const deleted=await service.auth.admin.deleteUser(entry.id);
    if(deleted.error) errors.push(deleted.error.code);
  }
  assert.deepEqual(errors,[],'Every disposable account must be removed');
  console.log('Disposable accounts, support history, read states and announcement drafts cleaned up.');
}
if(failure) throw failure;
