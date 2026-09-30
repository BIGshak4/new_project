"""Preserve 100-person sword variant of the existing step-two Josephus exercise."""
import json
import shutil
from pathlib import Path
from prep_012_josephus import survivor, simulate

root=Path(__file__).resolve().parents[1]
source='sources/prep-012-hundred-people-2026-09-28.png'
prompt='''במעגל עומדים 100 אנשים ממוספרים (99,100,......,1,2,3) כאשר 100 נושק ל־1 מצד אחד ול־99 מהצד השני — מעגל.
אצל מספר 1 נמצאת חרב. הוא לוקח את החרב, הורג את מספר 2 ומעביר למספר 3. מספר 3 הורג את מספר 4 ומעביר למספר 5, וכך הלאה. כל אחד הורג את הבא שלידו ומעביר לזה שאחריו. מי ימצא לבד ואחרון עם החרב?'''
ep='''100 people numbered 1..100 stand in a circle, with 100 next to 99 and 1. Person 1 holds a sword, eliminates person 2 and passes it to 3. Person 3 eliminates 4 and passes it to 5, and so on among those still present. Who is the last remaining person holding the sword?'''
tags=['nvidia','hardware','broadcom','mellanox']
companies=['NVIDIA','Broadcom','Mellanox']
he='''## וריאציה: 100 אנשים וחרב במעגל

'''+prompt+'''

![צילום וריאציית מאה האנשים](../sources/prep-012-hundred-people-2026-09-28.png)

זו אותה בעיית יוספוס עם צעד 2 כמו PREP-012, אך עם 100 אנשים במקום 43. אין ליצור שאלה עצמאית כפולה. הנוסח מבהיר שהסדר בתחילה 1 מוציא את 2, התור עובר ל־3 שמוציא את 4; בהמשך מדלגים על מי שכבר הוצא, והתור עובר תמיד לחי הבא אחרי מי שהוצא. שינוי בכיוון, במתחיל או בסדר העברת החרב היה משנה את התשובה.

**הצעה לפתרון לווריאציה:** האחרון הוא **73**. חזקת 2 הגדולה ביותר שאינה עולה על 100 היא 64. צריך להוציא 100−64=36 אנשים כדי להישאר עם מעגל בגודל חזקת 2. 36 ההוצאות הראשונות הן 2,4,6,...,72. לאחר הוצאת 72 החרב עוברת ל־73. עכשיו יש 64 אנשים חיים, והמתחיל בתת־הבעיה הוא 73. במעגל בגודל חזקת 2, כאשר כל שני מוצא, המתחיל הוא השורד; לכן 73 נשאר אחרון. המספרים המקוריים של החיים כבר אינם רציפים, אבל מספורם מחדש לפי סדרם במעגל אינו משנה את המשחק.

לפי הנוסחה השמורה: J(n)=2(n−2^floor(log2 n))+1, ולכן J(100)=2(100−64)+1=73. אין להסיק זאת מספירת ההוצאות בלבד בלי להוכיח את מקרה חזקת 2: בסבב מלא יוצאים הזוגיים, נשאר חצי מספר האנשים, והתור חוזר למתחיל המקורי, שוב ושוב עד אדם אחד.

שלושת הרמזים הקיימים מתאימים גם כאן: להתחיל ממעגלים קטנים, לזהות התנהגות בחזקות של 2, ולצמצם את 100 לחזקה הקרובה מלמטה. התשובה לווריאציה נפרדת מהתשובה 23 לשאלה המקורית עם 43 אנשים.

**ייחוס המקור החדש:** תגית hardware; חברות NVIDIA, Broadcom, Mellanox; תווית ראשית מלאנוקס. תגית hardware נשמרת כפי שהופיעה, אך הסיווג התוכני שלנו הוא חידת היגיון/אלגוריתמים, יוספוס, מעגלים וחזקות של 2. אין בכך הוכחה לשאלה על תכנון חומרה. השיוך לחברות לא אומת עצמאית; חברות מהמקור הקודם נשארות מיוחסות למקור ההוא.

**בדיקה:** סימולציית כל 99 ההוצאות עבור n=100 הושוותה לנוסחה והחזירה 73; כל הוצאה ייחודית, 36 הראשונות 2..72 בצעדים של 2, ויחד עם השורד מכסות את כל 1..100. נעשה שימוש בקוד המקורי שכבר נבדק ל־n=1..2048.

**תעדוף לראיון:** עדיפות נמוכה בזמן מוגבל, בעיקר כחזרה על חידה שכבר נלמדה. הערכת הכנה בלבד, לא תחזית לשאלות הראיון.
'''
en='''100-person variant of existing PREP-012, same step-two turn order: 1 removes 2, then 3 removes 4, continuing among living participants. Survivor is 73. The largest power of two <=100 is 64; eliminate the first 36 even labels 2..72, leaving 64 participants with 73 as next actor. In a power-of-two circle the actor starting that subproblem survives, since each round halves the circle while preserving its first actor. Hence J(100)=2(100-64)+1=73. The original n=43 answer remains 23; do not replace it with the variant's answer. Existing hints and proof apply.

New source reports hardware and companies NVIDIA, Broadcom, Mellanox, with Mellanox badge, unverified. Content classification remains a Josephus/algorithmic reasoning puzzle despite the source hardware tag. Simulation of all 99 removals verifies final survivor, uniqueness, first 36 removals and full participant coverage. Preparation priority is low under limited time, primarily revision of an already covered puzzle.'''
removed,last=simulate(100)
assert last==survivor(100)==73
assert len(removed)==len(set(removed))==99
assert removed[:36]==list(range(2,73,2))
assert set(removed)|{last}==set(range(1,101)) and last not in removed
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-012"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
assert all(x['path']!=source for x in q['sources'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-ce180bdc-05de-4738-929a-98f9a5b3d1f3.png',root/source)
q['sources'][0].update({'reported_companies':['Arm','NVIDIA','Mellanox'],'source_topic_tags':['logic','verification'],'source_company_badge':'מלאנוקס'})
q['sources'].append({'type':'user_supplied_image','path':source,'received_on':'2026-09-28','role':'same_algorithm_different_participant_count','source_tags':tags,'source_topic_tags':['hardware'],'reported_companies':companies,'source_company_badge':'מלאנוקס'})
q['media_assets'].append({'type':'source_image','path':source,'description':'Complete 100-person sword variant with source tags.'})
for field,values in [('source_tags',tags),('source_topic_tags',['hardware']),('reported_companies',companies)]:
    q[field]=list(dict.fromkeys(q[field]+values))
q.setdefault('prompt_variants',[]).append({'key':'hundred-people-sword','source_path':source,'original_prompt':prompt,'translation_en':ep,'participants':100,'survivor':73,'source_topic_tags':['hardware'],'reported_companies':companies,'source_company_badge':'מלאנוקס','hint_reference':'PREP-012 canonical three hints','solution_he':he,'solution_en':en,'verification_script':'solutions/update_prep_012_hundred_people.py','verification_status':'passed'})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
q['interview_relevance']={'priority':'low','label_he':'חזרה על חידה מוכרת — עדיפות נמוכה בזמן מוגבל','basis':'Specialized Josephus puzzle, already covered; prioritize role-specific coding, digital logic and validation under time pressure.','assessment_scope':'Preparation judgment, not an interview prediction.'}
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==29 and all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-012')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\nהרחבה ל־PREP-012: נשמרה וריאציית 100 האנשים עם חרב, תמונה וחברות מקור. אותו מנגנון יוספוס; התשובה לווריאציה נבדקה בנפרד. מספר השאלות השונות נשאר 29.\n',encoding='utf-8')
print('PREP-012 hundred-person variant saved and simulated; 29 unique questions retained; original 43-person record preserved with extension.')
