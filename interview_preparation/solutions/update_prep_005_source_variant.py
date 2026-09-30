"""Preserve a clearer three-part source variant without duplicating PREP-005."""
import json
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source='sources/prep-005-mellanox-variant-2026-09-29.png'
prompt='''נתון רכיב הממיין 2 מספרים (ראה תמונה):
1) ממש באמצעותו רכיב הממיין 4 מספרים.
2) ממש באמצעות הרכיבים שבנית, רכיב הממיין 6 מספרים.
3) האם ניתן לייעל את המימוש מסעיף 2?'''
ep='''Given a component that sorts two numbers (see image):
1) Use it to implement a component sorting four numbers.
2) Use the components you built to implement a component sorting six numbers.
3) Can the implementation from part 2 be improved?'''
tags=['arm','nvidia','hardware','sandisk','apple','marvell','mellanox','intel']
companies=['Arm','NVIDIA','SanDisk','Apple','Marvell','Mellanox','Intel']
he='''זו וריאציית ניסוח של PREP-005, עם אותם שלושה סעיפים. בניגוד למקור הראשון, לא מופיעה דרישת מינימום מפורשת בסעיפים 1–2 ולא מופיע הרמז לחישוב חוזר בסעיף 3. אין בכך שינוי בפתרון השמור: ממיין ארבעה באמצעות חמישה משווים, ממיין שישה באמצעות שלושה ממייני ארבעה, והסרת השוואות שיחסי הסדר שלהן כבר מובטחים לאחר פתיחת הבלוקים. שלושת הרמזים והפתרון המלא בעברית ובאנגלית מופיעים ברשומה הראשית ובקובץ זה; לא נוצרה שאלה כפולה.

בתרשים המקור החדש מוצא Max מעל Min. אין דרישה לסדר הפלט הכולל. הפתרון השמור משתמש בסדר עולה ומגדיר במפורש חיווט Min לקו בעל האינדקס הקטן ו־Max לקו בעל האינדקס הגדול. אפשר גם להפוך באופן עקבי את כל ההשוואות לקבלת סדר יורד. יש להבחין בין חיווט רכיב תקין כאן לבין מודל התקלה של PREP-030.

השוואת התוכן למקור הקודם הושלמה. בדיקות המימוש הקיימות נשמרות בתוקף משום שלא שונה המימוש: checks/check_prep_005.py. אין טענה שנערכה סינתזה או בדיקה פיזית. הוכחת חסם 12 המשווים נשענת על מקור המחקר שכבר מצוטט בפתרון המקורי, לא על בדיקת נכונות בלבד.

תעדוף: חזרה מועילה על רשתות מיון ועל ניצול יחסי סדר לביטול רכיבים מיותרים; בזמן מוגבל זו חזרה על נושא שכבר נשמר, ולא תוספת נושא חדש. השיוכים לחברות הם כפי שמופיעים בצילום ולא אומתו עצמאית.'''
en='''Same three-part problem as PREP-005. The new wording does not explicitly require minimum components in parts 1–2 and omits the original repeated-computation clue in part 3. The existing five-comparator four-sorter, three-four-sorter six-sorter, and pruning of redundant comparisons remain applicable. Reuse the complete bilingual solution and three prepared hints of the canonical record. The pictured cell outputs MAX above MIN; the saved ascending network explicitly wires MIN to the lower-index channel, or every comparison may be consistently reversed for descending order. This is not the fault model of PREP-030. The existing implementation checks remain applicable because its netlist is unchanged; no new physical synthesis/testing is claimed. Known minimum size 12 is supported by the research source already cited in the canonical solution. Useful revision rather than a new topic; company attribution remains source-reported, unverified.'''
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-005"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
assert not any(s.get('path')==source for s in q['sources'])
for field in ['source_tags','reported_companies','source_topic_tags','source_company_badge']:
    if field in q:
        q['sources'][0].setdefault(field,q[field])
q['sources'].append({'type':'user_supplied_image','path':source,'received_on':'2026-09-29','role':'same_three_parts_clearer_wording','source_tags':tags,'source_topic_tags':['hardware'],'reported_companies':companies,'source_company_badge':'מלאנוקס','company_attribution_status':'reported_by_supplied_source_not_independently_verified'})
q.setdefault('media_assets',[]).append({'type':'source_image','path':source,'description':'Full three-part sorting question, two-input MAX/MIN cell and company tags.'})
q.setdefault('prompt_variants',[]).append({'key':'mellanox-four-six-sorter-variant','source_path':source,'original_prompt':prompt,'translation_en':ep,'source_tags':tags,'reported_companies':companies,'source_company_badge':'מלאנוקס','prepared_hints_reference':'PREP-005 canonical three prepared hints','solution_reference':'PREP-005 canonical bilingual full solution','clarification_he':he,'clarification_en':en,'verification_reference':'checks/check_prep_005.py; unchanged existing circuit verification'})
for field,values in [('source_tags',tags),('reported_companies',companies)]:
    q[field]=list(dict.fromkeys(q[field]+values))
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
after=json.loads(updated)
assert before['question_count']==after['question_count']==31
assert all(a==b for a,b in zip(before['questions'],after['questions']) if a['id']!='PREP-005')
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-43ceec13-fed8-4bbb-9caf-c188a858c8a8.png',root/source)
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path']
md.write_text(md.read_text(encoding='utf-8')+'\n\n## מקור נוסף — נוסח מלאנוקס, 29 בספטמבר 2026\n\n'+prompt+'\n\n![גרסת השאלה עם תרשים Max/Min](../'+source+')\n\nחברות לפי צילום המקור: '+', '.join(companies)+'. תגית: hardware. תווית ראשית: מלאנוקס.\n\n'+he+'\n\n### English source variant\n\n'+ep+'\n\n'+en+'\n',encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\nהרחבה ל־PREP-005: נשמר צילום מקור נוסף עם שלושת סעיפי מיון 4, מיון 6 וייעול. אותו פתרון קיים; השיוך לפי המקור נשמר בנפרד. מספר השאלות השונות נשאר 31.\n',encoding='utf-8')
print('PREP-005 source variant saved; original prompt, solution and other 30 records preserved. Total: 31.')
