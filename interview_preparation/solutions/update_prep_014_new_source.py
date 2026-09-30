"""Add the same highest-set-bit exercise's handwritten source variant."""
import json
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source='sources/prep-014-variant-2026-09-27.png'
prompt='''ממש בעזרת שערים לוגיים קופסא אשר מקבלת 8 ביטים בכניסה, ומוציאה אחד בביט השמאלי ביותר (MSB) ואפס באחרים (ראה דוגמא).'''
ep='Implement with logic gates a box receiving 8 input bits and outputting one at the leftmost set-bit position and zeros elsewhere, as illustrated by the example.'
tags=['amazon','nvidia','rachip','hardware','cisco','samsung','apple','mellanox','intel']
companies=['Amazon','NVIDIA','Rachip','Cisco','Samsung','Apple','Mellanox','Intel']
he='''## נוסח נוסף עם שרטוט — 27 בספטמבר 2026

'''+prompt+'''

![צילום השאלה והשרטוט שנוספו](../sources/prep-014-variant-2026-09-27.png)

**קריאת הדוגמה בשרטוט:** 00110101 → 00100000. לכן הכוונה להשאיר את ה־1 השמאלי ביותר שקיים בקלט, ולא להוציא תמיד 10000000. המוצא הוא וקטור בן שמונה ביטים ולא אינדקס מקודד. זהה לפונקציה של PREP-014; נשמר מקור נוסף בלי ליצור שאלה כפולה. ההנחה לקלט אפס נשארת 00000000, שכן המקרה לא הוגדר במקור החדש.

הצילום החדש מבקש במפורש שערים לוגיים. פתרון AND/OR/NOT שכבר נשמר ברשומה מתאים ישירות: y7=x7 ולכל i<7 הביט yi הוא xi AND NOT של OR כל הביטים שמשמאלו. חישובי OR משותפים מונעים שכפול עבודה. גם שאר החלופות הקומבינטוריות והשרטוטים שכבר נשמרו נשארים זמינים, בכפוף לספריית השערים והעדפת שטח לעומת עומק. אין כאן טענה חדשה למינימום שערים מוחלט.

**קטגוריות:** תגית מקור hardware. סיווג נוסף שלנו: מערכות לוגיות ספרתיות, לוגיקה קומבינטורית, עדיפות ובידוד הביט המשמעותי ביותר. **חברות בתמונה הזאת:** Amazon, NVIDIA, Rachip, Cisco, Samsung, Apple, Mellanox, Intel. תווית ראשית: מלאנוקס. השיוך מהמקור בלבד ולא אומת עצמאית; חברות ותגיות מהצילום הישן אינן מיוחסות אוטומטית לצילום החדש.

**עדיפות גבוהה להכנה:** השאלה מתרגלת יסודות חומרה, פירוק תנאי לביט בודד, שיתוף לוגיקה ובדיקת מקרי קצה, הרלוונטיים להכנה לתפקיד ולידציית שבבים. זו הערכת הכנה לפי תיאור המשרה, לא תחזית לשאלות הראיון.

שלושת הרמזים, הפתרונות, השרטוטים ובדיקת כל 256 הקלטים ברשומה הקיימת חלים גם על הנוסח הזה. הדוגמה החדשה נבדקה ישירות בעת הקליטה.
'''
en='''Alternate supplied source: the handwritten example is 00110101 → 00100000, identifying the highest set bit rather than forcing the physical MSB to one. This is the same PREP-014 function with an explicit logic-gate requirement. Existing AND/OR/NOT solutions, hints, diagrams and exhaustive checks apply. Zero input is assumed to yield zero, not explicitly specified in the new source. New source tag: hardware; reported companies: Amazon, NVIDIA, Rachip, Cisco, Samsung, Apple, Mellanox, Intel; badge Mellanox. These are unverified source reports. Original-source companies remain separately attributed. High preparation relevance is an assessment of digital-hardware foundations, not an interview prediction.'''
x=int('00110101',2)
y=0
for i in range(8):
    if (x>>i)&1 and not (x>>(i+1)):
        y|=1<<i
assert f'{y:08b}'=='00100000'
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-014"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
assert q['id']=='PREP-014' and all(x['path']!=source for x in q['sources'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-e18af401-052b-4a7c-987b-82aaf70c90e7.png',root/source)
q['sources'][0].update({'reported_companies':['Amazon','Arm','NVIDIA','SolarEdge','Apple','Intel'],'source_topic_tags':['hardware','verification'],'source_company_badge':'Amazon'})
q['sources'].append({'type':'user_supplied_image','path':source,'received_on':'2026-09-27','role':'alternate_wording_same_function_with_diagram','source_tags':tags,'source_topic_tags':['hardware'],'reported_companies':companies,'source_company_badge':'מלאנוקס','attribution_status':'reported_by_supplied_source_not_independently_verified'})
q['media_assets'].append({'type':'source_image','path':source,'description':'Full supplied handwritten eight-bit input/output diagram, prompt and company tags.'})
for field,values in [('reported_companies',companies),('source_tags',tags)]:
    q[field]=list(dict.fromkeys(q[field]+values))
q.setdefault('prompt_variants',[]).append({'source_path':source,'received_on':'2026-09-27','original_prompt':prompt,'translation_en':ep,'example':{'input':'00110101','output':'00100000'},'source_topic_tags':['hardware'],'reported_companies':companies,'source_company_badge':'מלאנוקס','interpretation':'Keep the highest set bit, not necessarily bit 7. Existing gate-based solution and hints apply. Zero input is assumed to yield zero.','solution_reference':'PREP-014 canonical proposed solution and existing gate diagrams.'})
q['interview_relevance']={'priority':'high','label_he':'עדיפות גבוהה להכנה ביסודות חומרה','basis':'Combinational logic, priority and per-bit reasoning with corner cases align with digital foundations for the supplied validation role.','assessment_scope':'Preparation assessment only; not a prediction of Marvell interview questions.'}
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==before['question_count']==22
assert all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-014')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\nהרחבה ל־PREP-014: נשמר נוסח נוסף עם שרטוט ידני ותגיות חברות מ־27 בספטמבר; אותה פונקציה, ולכן מספר השאלות השונות נשאר 22.\n',encoding='utf-8')
print('PREP-014 source/diagram/company variant saved; new example verified; 22 unique questions; other records unchanged.')
