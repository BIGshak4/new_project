import fs from 'node:fs';
const data=JSON.parse(fs.readFileSync(new URL('../example_question/questions.json',import.meta.url),'utf8'));
const quote=v=>v==null?'NULL':"'"+String(v).replaceAll("'","''")+"'";
const json=v=>quote(JSON.stringify(v))+'::jsonb';
const sql=[];
for(const q of data.questions){
 const domain=q.topic.includes('fsm')||q.topic.includes('state')?'fsms':q.topic.includes('timing')||q.topic.includes('clock')||q.topic.includes('sequential')?'sequential_logic':q.category==='software'||q.topic.includes('verilog')||q.topic.includes('hdl')?'relevant_programming':'digital_fundamentals';
 const assets={collection:'jobrun_example_v1',category:q.category,topic:q.topic,topic_title:q.topic_title,titles:{he:q.translations.he.title,en:q.translations.en.title},shared_code:q.shared_code,code_language:q.code_language,sources:q.sources,source_id:q.id};
 sql.push(`insert into public.question(key,status,origin,format,practice_modes,subject_id,difficulty,estimated_minutes,requirements,reference_solution,hints,rubric,assets,source_name,source_url,reuse_status,review_notes) values(${quote('example-'+q.key)},'in_review','original',${quote(q.format)},ARRAY[${q.practice_modes.map(quote).join(',')}]::public.practice_mode[],(select id from public.skill where key=${quote(domain)}),${q.difficulty},${q.estimated_minutes},${quote(q.translations.en.prompt)},${quote(q.translations.en.reference_solution)},${json([q.translations.en.hint])},'{}'::jsonb,${json(assets)},${quote(q.sources[0]?.name)},${quote(q.sources[0]?.url)},'pending_review','Private beta seed; technical review, rubric and translation parity pending.') on conflict(key) do nothing;`);
 for(const lang of ['he','en']){const t=q.translations[lang];sql.push(`insert into public.question_translation(question_id,language,prompt,hints,reference_solution) select id,${quote(lang)},${quote(t.prompt)},${json([t.hint])},${quote(t.reference_solution)} from public.question where key=${quote('example-'+q.key)} on conflict(question_id,language) do nothing;`);}
}
fs.writeFileSync(new URL('../supabase/seed-example-questions.sql',import.meta.url),sql.join('\n'),'utf8');
console.log(`Prepared ${data.questions.length} review-only questions and 60 translations.`);
