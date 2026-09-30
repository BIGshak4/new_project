"""Preserve the rephrased mux question as another source, not a duplicate."""
import json
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
prompt="""האם ניתן לממש באמצעות רכיבי mux את הביטוי (abc')' ?
אם לא — הסבר מדוע.
אם כן — ממש את הביטוי (במספר מינימלי של רכיבים)."""
ep="Can the expression (abc')' be implemented using mux components? If not, explain why. If so, implement it using the minimum number of components."
source='sources/prep-011-variant-2026-09-27.png'
note='''## נוסח נוסף שהתקבל ב־27 בספטמבר 2026

'''+prompt+'''

![צילום הנוסח הנוסף](../sources/prep-011-variant-2026-09-27.png)

זו אותה פונקציה של PREP-011: גרש אחרי c שולל את c, והגרש אחרי הסוגריים שולל את כל המכפלה. לכן הנוסח נוסף כמקור חלופי ולא כשאלה עצמאית נוספת. נשמרו שלושת הרמזים, ההצעה לפתרון והשרטוטים שכבר הוכנו.

בצילום החדש אין תגיות נושא או חברות. הסיווג שלנו הוא חומרה, מערכות לוגיות ספרתיות, לוגיקה קומבינטורית, MUX ואלגברה בוליאנית. שמות החברות ברשומה הראשית שייכים לצילום הקודם בלבד, ואין לייחס אותם לצילום הזה.

**הנחות לנוסח החדש:** הצילום אינו מפרט את גודל ה־MUX או זמינות הקבועים. התשובה השמורה — שני רכיבי MUX — מתייחסת ל־MUX מסוג 2:1, עם כניסות a,b,c וקבועים 0,1 זמינים וללא לוגיקה נוספת, כמו בשאלה המקורית. אי אפשר להציג מינימום רכיבים בלי להגדיר את סוג הרכיב. אם מותר MUX 4:1, רכיב אחד מספיק: קווי הבחירה a,b, כניסות נתונים I00=I01=I10=1 ו־I11=c. כאן החיבור הוכח בטבלת אמת לכל שמונת הקלטים. הבחירה היא בינארית לפי ab, ולכן רק כאשר ab=11 מועבר c. אין שינוי לפתרון ולמינימליות במודל 2:1 המקורי.

**רלוונטיות להכנה:** עדיפות גבוהה להבנת יסודות לוגיקה ספרתית ותכנון עם MUX, כחלק מהכנה לתפקיד שבבים. זו הערכת הכנה על סמך תיאור התפקיד, לא תחזית לשאלות ב־Marvell.
'''
for a in (0,1):
    for b in (0,1):
        for c in (0,1):
            assert (1,1,1,c)[2*a+b] == int(not(a and b and not c))
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-011"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
assert q['id']=='PREP-011' and all(x['path']!=source for x in q['sources'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-054cb89f-dd1e-45a8-baa1-0cd032c09195.png',root/source)
q['sources'].append({'type':'user_supplied_image','path':source,'received_on':'2026-09-27','role':'alternate_wording_same_function','source_tags':[],'reported_companies':[]})
q['media_assets'].append({'type':'source_image','path':source,'description':'Alternate formulation asking feasibility and minimum mux count; no company or topic tags shown.'})
q.setdefault('prompt_variants',[]).append({
    'received_on':'2026-09-27','source_path':source,'original_prompt':prompt,'translation_en':ep,
    'same_as_question_id':'PREP-011','formula_interpretation':'NOT(a AND b AND NOT(c))',
    'source_topic_tags':[],'reported_companies':[],
    'assumptions':['New source does not specify mux size or available constants.','Existing two-MUX minimum assumes 2:1 muxes and inputs a,b,c,0,1.','One 4:1 mux suffices if that component is allowed: select ab, data (1,1,1,c).'],
    'prepared_hint_ids':[h['id'] for h in q['prepared_hints']],
    'solution_reference':'Canonical two-MUX solution, diagrams and proof on PREP-011, under stated assumptions.',
    'verification':'Same Boolean function as original; alternative 4:1 realization checked on all eight input tuples in solutions/update_prep_011_new_source.py.'
})
q['interview_relevance']={'priority':'high','label_he':'עדיפות גבוהה להבנת יסודות MUX','basis':'Combinational logic, mux behavior and function-preserving circuit design are core hardware foundations relevant to the supplied chip-validation role.','assessment_scope':'Preparation judgment, not an interview prediction. New image contains no company attribution.'}
extra_en='The alternate screenshot received 2026-09-27 gives the same formula but omits mux size and constants. The existing two-component minimum assumes 2:1 muxes with a,b,c,0,1 available. If a 4:1 mux is allowed, one component suffices: select ab and data (1,1,1,c). All eight tuples verified. No company/topic tags appear in the new image; earlier reported companies belong only to the earlier source.'
q['translations']['he']['reference_solution']+='\n\nהבהרה לנוסח הנוסף: מינימום שני רכיבים מניח MUX 2:1 וקבועים זמינים. אם מותר MUX 4:1, מספיק אחד עם בחירה ab וכניסות (1,1,1,c). בצילום החדש סוג הרכיב אינו מוגדר.'
q['translations']['en']['reference_solution']+='\n\n'+extra_en
s=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(s)
assert after['question_count']==before['question_count']==22
assert all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-011')
p.write_text(s,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+note+'\n\n'+extra_en+'\n',encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\nהרחבה ל־PREP-011: נשמר צילום נוסף מ־27 בספטמבר עם אותו ביטוי וניסוח חלופי; אין כפילות במספר השאלות (22). הנוסח החדש לא מציין סוג MUX, קבועים או חברות; ההנחות וההבדל בין 2:1 ל־4:1 תועדו.\n',encoding='utf-8')
print('PREP-011 source variant saved; still 22 unique questions. 4:1 variant checked on all 8 inputs; other records preserved.')
