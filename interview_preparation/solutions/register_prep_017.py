"""Preserve the clock-angle question, progressive hints and checked answer."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-fde58b75-ff82-4f18-83e8-8f1ffb741371.png',root/'sources/prep-017.png')
prompt='יש לנו שעון מחוגים, בת כמה מעלות הזווית בין מחוגי השעון בשעה 6 וחצי? (לא צריך להתייחס למחוג של השניות)'
ep='An analog clock shows 6:30. What is the angle in degrees between the clock hands? Ignore the seconds hand.'
hints=[
    'מחוג הדקות קל למיקום בשעה וחצי. אבל האם מחוג השעות נשאר בדיוק על הספרה 6 במשך כל השעה?',
    'בשעון יש 12 מרווחים שווים סביב מעגל של 360 מעלות. חשב כמה מעלות מפרידות בין שתי ספרות סמוכות, ואז חשוב איזה חלק מהמרווח הזה עובר מחוג השעות בחצי שעה.',
    'בשעה 6:30 מחוג הדקות מצביע על 6, ומחוג השעות נמצא בדיוק באמצע בין 6 ל־7. לכן הזווית הקטנה ביניהם היא חצי מהזווית שבין שתי ספרות סמוכות.'
]
eh=[
    'The minute hand is easy to locate at half past the hour. Does the hour hand stay exactly on 6 for the entire hour?',
    'The dial divides 360 degrees into 12 equal hour intervals. Find the angle per interval, then the fraction the hour hand travels in half an hour.',
    'At 6:30 the minute hand points to 6 while the hour hand is halfway between 6 and 7. The smaller angle is half an hour-mark interval.'
]
he='''הזווית הקטנה היא **15 מעלות**.

בשעה 6:30 מחוג הדקות מצביע על הספרה 6, כי עברו 30 דקות, שהן חצי מסיבוב של 60 דקות. אבל מחוג השעות אינו נשאר על 6: הוא נע בהדרגה לכיוון 7. בחצי שעה הוא עובר חצי מהדרך בין 6 ל־7.

סיבוב מלא הוא 360 מעלות ובשעון יש 12 מרווחים שווים בין סימוני השעות. לכן כל מרווח הוא 360/12=30 מעלות. מחוג השעות נמצא באמצע המרווח בין 6 ל־7, ולכן הוא במרחק 30/2=15 מעלות מהספרה 6. מחוג הדקות נמצא בדיוק על 6. מכאן שהזווית ביניהם היא 15 מעלות.

בדיקה באמצעות מיקום כל מחוג, בכיוון השעון מהספרה 12: מחוג הדקות נמצא ב־30×6=180 מעלות. מחוג השעות נמצא ב־6×30+30×0.5=195 מעלות. ההפרש הוא 195−180=15 מעלות. הקצב של מחוג השעות הוא 30 מעלות בשעה, כלומר חצי מעלה בדקה; בחצי שעה הוא מתקדם 15 מעלות.

ההנחה היא שעון רגיל בעל תנועת שעות רציפה. כשאומרים ״הזווית בין המחוגים״ נבחר בדרך כלל בזווית הקטנה. הזווית האחרת, הגדולה, היא 360−15=345 מעלות. אין צורך להתייחס למחוג השניות. הטעות הנפוצה היא למקם את שני המחוגים על 6 ולהשיב 0, כאילו מחוג השעות קופץ רק בתחילת כל שעה.

לזמן כללי h:m: מיקום מחוג הדקות הוא 6m מעלות ומיקום מחוג השעות הוא 30(h mod 12)+m/2 מעלות. מחשבים d כהפרש המוחלט ביניהם, והזווית הקטנה היא min(d,360−d). עבור זמן אחד זו נוסחה ישירה, O(1) בזמן ובזיכרון; אין צורך בסימולציה. שאלת המקור עצמה דורשת רק את הערך ב־6:30.

בדיקת Python בחשבון שברים מדויק אימתה את 6:30 ואת מיקום שני המחוגים, דוגמאות נוספות, ואת כל 720 מיקומי הדקות במחזור של 12 שעות מול חישוב נפרד של המהירות היחסית (5.5 מעלות בדקה). נבדקה גם מחזוריות של 12 שעות.'''
en='''The smaller angle is 15 degrees. At 6:30 the minute hand points at 6. The hour hand moves continuously and is halfway from 6 to 7. Adjacent hour marks are 360/12=30 degrees apart, so half an interval is 15 degrees.

Measured clockwise from 12, the minute hand is at 30*6=180 degrees. The hour hand is at 6*30+30*0.5=195 degrees. Their difference is 15 degrees. The other, reflex angle is 345 degrees. Assuming an ordinary continuous hour hand is essential; treating it as fixed at 6 incorrectly gives zero.

Generally, for h:m, minute angle=6m, hour angle=30(h mod 12)+m/2; let d be their absolute difference and return min(d,360-d). This takes O(1) time and space per query. Exact-fraction Python checks cover the source time, additional examples, all 720 minute positions against relative angular motion at 5.5 degrees per minute, and 12-hour periodicity.'''
q={
 'id':'PREP-017','key':'clock-hands-angle-six-thirty','version':1,'created_on':'2026-09-27',
 'category':'logic','topic':'geometry','topics':['hardware','logic','geometry','clock_angles','relative_motion'],
 'source_topic_tags':['hardware'],'added_topic_tags':['logic','geometry','clock_angles','relative_motion'],
 'source_tags':['nvidia','hardware','intel'],'reported_companies':['NVIDIA','Intel'],
 'source_company_badge':'Nvidia','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'reasoning','status':'in_review',
 'solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
 'authorship':'Source transcribed; AI-assisted translations, hints, solution and verification.','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-017.png','received_on':'2026-09-27'}],
 'original_prompt':prompt,
 'translations':{'he':{'title':'הזווית בין מחוגי השעון בשעה 6:30','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},
                 'en':{'title':'Angle between clock hands at 6:30','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-017-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Standard 12-hour analog dial with uniform, continuous hour-hand motion.',
                'Exactly 6:30; seconds hand is ignored.','Smaller undirected angle requested by convention; reflex angle documented separately.'],
 'optimality':{'criterion':'Direct calculation for one time value','result':'15 degrees; O(1) time and space',
               'proof':'Half of the 30-degree interval between adjacent hour marks; no simulation required.'},
 'edge_cases':['Distinguish continuously moving hour hand from a hand fixed at the numeral.',
               'Smaller angle 15 degrees versus reflex angle 345 degrees.',
               '06:30 and 18:30 have the same hand positions.'],
 'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_017.py',
                 'method':'Exact fractions; source hand positions (195,180); six examples; all 720 minute positions vs relative-motion formula; 12-hour periodicity.'},
 'solution_model_path':'solutions/prep_017_clock_angle.py',
 'media_assets':[{'type':'source_image','path':'sources/prep-017.png'}],
 'interview_answer':'ב־6:30 מחוג הדקות על 6, אבל מחוג השעות כבר באמצע הדרך ל־7. בין שתי ספרות יש 30 מעלות, ולכן חצי המרווח הוא 15 מעלות.',
 'common_mistakes':['Answering zero by assuming the hour hand stays at 6.','Ignoring that an undirected angle conventionally means the smaller angle.'],
 'related_question_ids':[],'related_question_links':[],
 'markdown_path':'questions/prep-017-clock-angle-six-thirty.md'
}
p=root/'questions.json'; s=p.read_text(encoding='utf-8'); data=json.loads(s)
assert data['question_count']==16 and not any(a['id']==q['id'] for a in data['questions'])
pos=s.rfind('\n  ]'); assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 16','"question_count": 17',1)
data=json.loads(s); assert len(data['questions'])==data['question_count']==17
p.write_text(s,encoding='utf-8')
md='# PREP-017 — הזווית בין מחוגי השעון בשעה 6:30\n\n## השאלה המקורית\n\n'+prompt
md+='\n\n![צילום השאלה והתגיות](../sources/prep-017.png)\n\n## קטגוריות וחברות\n\n'
md+='תגית מקור: hardware. סיווג נוסף: חידות היגיון, גאומטריה, זוויות בשעון ותנועה יחסית. חברות לפי המקור: NVIDIA, Intel. תווית ראשית: Nvidia. שיוך החברות מהצילום בלבד, ללא אימות עצמאי.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
md+='\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[מודל Python](../solutions/prep_017_clock_angle.py) · [בדיקה](../checks/check_prep_017.py).\n\n'
md+='## תשובה קצרה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'
md+='\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
with (root/'README.md').open('a',encoding='utf-8') as f:
    f.write('\n- [PREP-017 — הזווית בין מחוגי השעון בשעה 6:30](questions/prep-017-clock-angle-six-thirty.md) — נשמרו צילום המקור, הנוסח, קטגוריות, חברות, שלושה רמזים והצעה לפתרון עם בדיקת חישוב מדויקת.\n')
assert (root/'sources/prep-017.png').exists()
assert he in (root/q['markdown_path']).read_text(encoding='utf-8')
print('PREP-017 saved with image, metadata, three hints, bilingual solution and checks. Total: 17.')
