// Explicit, disposable end-to-end check against the configured JobRun Supabase.
// Creates confirmed synthetic accounts without sending email, and removes them
// and their private uploaded objects in finally. Never prints keys or sessions.
// node tools/qa/admin-support-smoke.mjs --run [--browser --practice-origin URL --admin-origin URL]
import assert from 'node:assert/strict';
import { readFileSync, mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { resolve } from 'node:path';

if (!process.argv.includes('--run')) throw new Error('Pass --run to create and clean up disposable QA accounts.');
const root = resolve(import.meta.dirname, '../..');
const require = createRequire(resolve(root, 'apps/web/package.json'));
const { createClient } = require('@supabase/supabase-js');
function envFile(path) {
  return Object.fromEntries(readFileSync(path, 'utf8').split(/\r?\n/).flatMap(line => {
    const m = line.match(/^([A-Z_][A-Z_0-9]*)=(.*)$/);
    return m ? [[m[1], m[2].trim().replace(/^(['"])(.*)\1$/, '$2')]] : [];
  }));
}
const config = envFile(resolve(root, 'backend/.env'));
const publicConfig = envFile(resolve(root, 'apps/web/.env.local'));
const url = config.SUPABASE_URL;
assert.equal(new URL(url).hostname, 'djpwvqpsqbkvprlncjjg.supabase.co', 'Only the intended JobRun project is permitted.');
const options = { auth: { persistSession: false, autoRefreshToken: false, detectSessionInUrl: false }, global:{fetch:(url,init)=>fetch(url,{...init,signal:AbortSignal.timeout(20000)})} };
const service = createClient(url, config.SUPABASE_SERVICE_ROLE_KEY, options);
const client = () => createClient(url, publicConfig.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, options);
const accounts = [], uploaded = [], checks = [];
let browser;
let failure;
function pass(name) { checks.push(name); console.log(`PASS ${name}`); }
async function ok(promise, name) {
  console.log(`CHECK ${name}`);
  const result = await promise;
  assert.equal(result.error, null, `${name}: ${result.error?.message}`);
  return result.data;
}
async function denied(promise, name) {
  console.log(`CHECK ${name}`);
  const started=Date.now();
  const result = await promise;
  assert.ok(result.error, `${name}: operation unexpectedly succeeded`);
  assert.ok(result.error.code || result.error.status || result.error.statusCode, `${name}: network failure cannot prove authorization`);
  assert.ok(!/timeout|abort|fetch failed/i.test(result.error.message), `${name}: a timeout cannot prove rejection`);
  assert.ok(Date.now()-started<15000,`${name}: rejection must return promptly`);
  pass(name);
}
async function account(label, manager = false, member = true) {
  const email = `jobrun-qa-${label}-${crypto.randomUUID()}@example.com`;
  const password = `${crypto.randomUUID()}Aa7!`;
  const created = await ok(service.auth.admin.createUser({email, password, email_confirm: true, user_metadata: {display_name: `בדיקת מערכת · ${label}`, can_manage_tasks: true}}), `create ${label}`);
  const entry = {id: created.user.id, email, manager, client: client()};
  accounts.push(entry);
  entry.member=member;
  const signed = await ok(entry.client.auth.signInWithPassword({email, password}), `sign in ${label}`);
  entry.session = signed.session;
  return entry;
}
function report(id, subject = 'בדיקה אוטומטית — אפשר להתעלם') {
  return {p_id: id, p_subject: subject, p_description: 'Synthetic integration test: Y[3:0] and A[1:0]. No real user data.', p_category:'bug', p_language:'he', p_page_path:'/', p_question_key:null};
}
const out = resolve(root, '.impeccable/review/admin-support');
mkdirSync(out, {recursive:true});
const control=resolve(out,`control-${crypto.randomUUID()}`);
mkdirSync(control);
async function coordinate(phase) {
  writeFileSync(resolve(control,`${phase}-request.json`),JSON.stringify(accounts.map(({id,email,manager,member})=>({id,email,manager,member})),null,2));
  console.log(`QA_${phase.toUpperCase()} ${control}`);
  const deadline=Date.now()+300000;
  while(!existsSync(resolve(control,`${phase}.done`))) {
    if(Date.now()>deadline) throw new Error(`Privileged SQL ${phase} acknowledgement required: ${control}`);
    await new Promise(resolve=>setTimeout(resolve,500));
  }
}
try {
  const founder = await account('founder', true);
  const learner = await account('learner');
  const outsider = await account('outsider', false, false);
  // Membership/admin-data grants deliberately exclude even the REST service
  // client. A trusted operator applies only these synthetic rows through SQL.
  await coordinate('setup');
  await denied(client().rpc('jr_admin_users'), 'anonymous admin directory blocked');
  await denied(learner.client.rpc('jr_admin_users'), 'learner admin directory blocked despite forged user metadata');
  await denied(outsider.client.rpc('jr_admin_users'), 'non-member admin directory blocked');
  const directory = await ok(founder.client.rpc('jr_admin_users', {p_query:learner.email,p_page:1,p_page_size:25}), 'founder directory');
  assert.equal(directory.total, 1);
  const initial = directory.users[0];
  assert.equal(initial.email, learner.email);
  assert.equal(initial.plan_tier, 'free');
  pass('founder directory searches auth users without exposing credentials');
  const changed = await ok(founder.client.rpc('jr_admin_update_user',{p_user_id:learner.id,p_plan_tier:'pro',p_pilot_access:true,p_expected_plan:'free',p_expected_access:true}), 'plan change');
  assert.equal(changed.plan_tier,'pro');
  await denied(founder.client.rpc('jr_admin_update_user',{p_user_id:learner.id,p_plan_tier:'team',p_pilot_access:true,p_expected_plan:'free',p_expected_access:true}), 'stale user edit cannot overwrite newer plan');
  await denied(founder.client.rpc('jr_admin_update_user',{p_user_id:founder.id,p_plan_tier:'free',p_pilot_access:false,p_expected_plan:'free',p_expected_access:true}), 'founder cannot lose management access');
  await denied(learner.client.rpc('jr_admin_update_user',{p_user_id:learner.id,p_plan_tier:'team',p_pilot_access:true,p_expected_plan:'pro',p_expected_access:true}), 'learner cannot assign own paid entitlement');
  const reportId = crypto.randomUUID();
  const saved = await ok(learner.client.rpc('jr_submit_support_report',report(reportId)), 'submit report');
  assert.equal(saved.id,reportId);
  const retried = await ok(learner.client.rpc('jr_submit_support_report',report(reportId)), 'idempotent report retry');
  assert.equal(retried.id,reportId);
  pass('learner report persisted and retry does not duplicate');
  await denied(outsider.client.rpc('jr_admin_support_detail',{p_id:reportId}), 'foreign report details blocked');
  await denied(learner.client.rpc('jr_admin_support_detail',{p_id:reportId}), 'learner cannot read internal administrative notes');
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jF1kAAAAASUVORK5CYII=','base64');
  const fileId = crypto.randomUUID();
  const file = await ok(learner.client.rpc('jr_reserve_support_file',{p_id:fileId,p_report_id:reportId,p_name:'qa-pixel.png',p_mime_type:'image/png',p_size_bytes:png.length}), 'reserve file');
  uploaded.push(file.storage_path);
  await ok(learner.client.storage.from('jr-support-files').upload(file.storage_path,png,{contentType:'image/png',upsert:false}), 'upload private image');
  await denied(outsider.client.storage.from('jr-support-files').createSignedUrl(file.storage_path,60), 'foreign attachment signed URL blocked');
  await denied(learner.client.storage.from('jr-support-files').upload(file.storage_path,png,{contentType:'image/png',upsert:true}), 'private file cannot be replaced');
  await denied(learner.client.rpc('jr_reserve_support_file',{p_id:crypto.randomUUID(),p_report_id:reportId,p_name:'unsafe.svg',p_mime_type:'image/svg+xml',p_size_bytes:20}), 'active SVG upload rejected');
  await denied(learner.client.rpc('jr_reserve_support_file',{p_id:crypto.randomUUID(),p_report_id:reportId,p_name:'large.pdf',p_mime_type:'application/pdf',p_size_bytes:5*1024*1024+1}), 'oversize file rejected by database');
  await denied(learner.client.from('jr_support_reports').select('internal_notes').eq('id',reportId), 'internal notes are not directly readable by learner');
  await denied(learner.client.from('jr_support_reports').update({status:'closed'}).eq('id',reportId), 'learner cannot directly close a report');
  for(let i=0;i<4;i++) await ok(learner.client.rpc('jr_reserve_support_file',{p_id:crypto.randomUUID(),p_report_id:reportId,p_name:`reserved-${i}.txt`,p_mime_type:'text/plain',p_size_bytes:12}), 'reserve bounded file slot');
  await denied(learner.client.rpc('jr_reserve_support_file',{p_id:crypto.randomUUID(),p_report_id:reportId,p_name:'sixth.txt',p_mime_type:'text/plain',p_size_bytes:12}), 'sixth attachment rejected by database');
  const detail = await ok(founder.client.rpc('jr_admin_support_detail',{p_id:reportId}), 'founder report detail');
  assert.equal(detail.report.id,reportId);
  assert.ok(detail.files.some(f=>f.storage_path===file.storage_path));
  const signed = await ok(founder.client.storage.from('jr-support-files').createSignedUrl(file.storage_path,60,{download:'qa-pixel.png'}), 'founder signed download');
  const downloaded = await fetch(signed.signedUrl);
  assert.equal(downloaded.status,200);
  assert.deepEqual(Buffer.from(await downloaded.arrayBuffer()),png);
  pass('private attachment uploads and authorized download returns original bytes');
  const updated = await ok(founder.client.rpc('jr_admin_update_support',{p_id:reportId,p_expected_version:detail.report.version,p_status:'in_progress',p_priority:'high',p_assigned_to:founder.id,p_internal_notes:'Synthetic private note',p_resolution:''}), 'triage report');
  assert.equal(updated.status,'in_progress');
  await denied(founder.client.rpc('jr_admin_update_support',{p_id:reportId,p_expected_version:detail.report.version,p_status:'closed',p_priority:'normal',p_assigned_to:null,p_internal_notes:'stale',p_resolution:''}), 'concurrent triage edit is rejected');
  const queue = await ok(founder.client.rpc('jr_admin_support_list',{p_query:reportId,p_status:'in_progress',p_page:1,p_page_size:25}), 'filter support queue');
  assert.ok(queue.reports.some(r=>r.id===reportId));
  pass('triage assignment status internal notes and version conflict verified');
  if (process.argv.includes('--browser')) {
    const {runBrowserChecks} = await import('./admin-support-browser.mjs');
    browser = await runBrowserChecks({root,url,founder,learner,outsider,reportId,out,pass});
  }
  writeFileSync(resolve(out,'e2e-report.json'),JSON.stringify({checks,passed:true,syntheticAccounts:accounts.length,privateUploadVerified:true,timestamp:new Date().toISOString()},null,2));
} catch(error) {
  failure=error;
  console.error(`QA_FAILURE ${error.message}`);
} finally {
  if (browser) await browser.close();
  const cleanupErrors=[];
  const paths=new Set(uploaded);
  async function collectFiles(prefix,depth=0) {
    if(depth>3) throw new Error('Unexpected QA storage depth');
    const result=await service.storage.from('jr-support-files').list(prefix,{limit:100});
    if(result.error) {cleanupErrors.push(`storage list ${result.error.statusCode}`);return;}
    for(const object of result.data || []) {
      const path=`${prefix}/${object.name}`;
      if(object.id) paths.add(path); else await collectFiles(path,depth+1);
    }
  }
  for(const a of accounts) await collectFiles(a.id);
  if(paths.size) {
    const removed=await service.storage.from('jr-support-files').remove([...paths]);
    if(removed.error) cleanupErrors.push(`storage removal ${removed.error.statusCode}`);
  }
  if(accounts.length) await coordinate('cleanup');
  for(const a of accounts.reverse()) {
    const deleted = await service.auth.admin.deleteUser(a.id);
    if(deleted.error) cleanupErrors.push(`account ${deleted.error.code}`);
  }
  assert.deepEqual(cleanupErrors,[], 'Every disposable QA account must be removed.');
  console.log('Disposable accounts, reports and uploaded files cleaned up.');
}
if(failure) throw failure;
