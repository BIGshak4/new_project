"""Review and preserve the supplied third-party mux answer as source material."""
import json
import shutil
from itertools import product
from pathlib import Path
from prep_011_mux_function import mux, part_b

root=Path(__file__).resolve().parents[1]
source='sources/prep-011-external-answer-2026-09-27.png'
he='''### פתרון חיצוני נוסף: AND באמצעות MUX ואז בחירה לפי התוצאה

צילום הפתרון שסופק נשמר כמקור לדיון, ולא כהוראות. במקור טענה כללית על אי־שלמות MUX ללא קבועים ושרטוט חלופה בשני רכיבים. נבחין בין המעגל התקין לבין ניסוחים שדורשים תיקון.

**המעגל תקין**, בהנחה שהכניסה העליונה בכל MUX היא I0 והתחתונה I1 (המספרים לא סומנו בציור). ברכיב התחתון S=b, I0=0, I1=a, ולכן t=MUX(b,0,a)=a AND b. כאשר b=0 המוצא 0; כאשר b=1 הוא a. הרכיב העליון משתמש ב־t ככניסת בחירה, עם I0=1 ו־I1=c. לכן אם a AND b=0 הוא מחזיר 1, ואם a AND b=1 הוא מחזיר c. זה בדיוק f=NOT(a AND b AND NOT(c)). החיבור בין הרכיבים מגיע לכניסת הבחירה של הרכיב העליון, בשונה מהפתרון הקודם שבו המוצא הפנימי הגיע לכניסת נתונים.

המעגל שקול פונקציונלית לפתרון השמור MUX(a,1,MUX(b,1,c)), אבל החיווט שונה: בפתרון המצורף מחשבים קודם a AND b, ומשתמשים בתוצאה לבחירת 1 או c. בשניהם שני MUX 2:1, וזה מינימום תחת המודל שכבר הוגדר והוכח. כאן משתמשים בקבועים 0 ו־1, בעוד הפתרון הקודם זקוק לקבוע 1 בלבד. אין להסיק מי מהיר יותר בלי השהיות מסלולי בחירה ונתונים של הרכיב ומידע על הגעת הקלטים; אין להסיק חיסכון שטח פיזי מקבוע אחד לעומת שניים בלבד.

**תיקון לטענות מעל הציור:** בלי קבועים, MUX רגיל אינו מערכת שלמה פונקציונלית. לדוגמה אי אפשר לייצר NOT עם MUX בלבד מקלט גולמי x: כש־x=0 כל הרשת חייבת להוציא 0, אף ש־NOT(x)=1. אך אי־שלמות אינה אומרת שלא ניתן לממש AND או OR! לפי MUX(S,I0,I1):

* AND(a,b)=MUX(a,a,b): אם a=0 מועבר a=0; אם a=1 מועבר b.
* OR(a,b)=MUX(a,b,a): אם a=0 מועבר b; אם a=1 מועבר a=1.

אלה חיבורים של חוטי a,b בלבד, בלי חוט קבוע 0 או 1. הערכים 0 ו־1 בהסבר הם ערכי הקלט a במקרים השונים, ולא חיבורים לקבועים. בנוסף השוויון MUX(s,a,b)=MUX(s,s,s)=s אינו זהות כללית: למשל s=0,a=1,b=0 נותן MUX=1 ולא s. הניסוח הנכון הוא שאם כל שלושת הפינים מקבלים את אותו אות x, אז MUX(x,x,x)=x; אפשר להרחיב זאת באינדוקציה לרשת שכל כניסותיה הראשוניות שוות ל־x. כדי להראות שהפונקציה המסוימת אינה ניתנת למימוש ללא קבועים, משתמשים בעדות a=b=c=0 ו־f=1, ולא מסתפקים באמירה שהמערכת אינה שלמה.

עם MUX וקבועי 0,1 ניתן לממש NOT, AND ו־OR, ולכן זו מערכת שלמה פונקציונלית. אין צורך במונח ״חצי שלמה״ שמופיע במקור. אין דרך להסיק מהצילום בלבד שהשאלה המקורית אכן חולקה לשני שלבים; זו השערת הכותב.

**בדיקה:** כל שמונת הקלטים נבדקו למעגל החיצוני מול הפונקציה המבוקשת והמימוש הקודם; כל ארבעת הקלטים נבדקו לחיבורי AND/OR ללא קבועים. טבלת האמת בצילום תואמת לפונקציה. המיפוי I0/I1 הונח לפי הסידור המקובל העליון/התחתון, כי אינו מצוין בציור.
'''
en='''### Review of supplied external answer

Assuming the upper data pin is I0 and the lower I1, the drawn circuit is correct: t=MUX(b,0,a)=a AND b, followed by f=MUX(t,1,c). Unlike the previous circuit, the first mux output drives the second mux's select, not a data input. This gives exactly NOT(a AND b AND NOT(c)) on all eight inputs. Both circuits use the proven minimum two ordinary 2:1 muxes under the raw-input/constant model. The new version uses constants 0 and 1; the previous version needs only 1. No physical timing/area advantage follows without cell and arrival data.

Some prose in the supplied answer is inaccurate. MUX without constants is not functionally complete, but it CAN implement AND(a,b)=MUX(a,a,b) and OR(a,b)=MUX(a,b,a) without any constant wires. It cannot implement NOT from raw inputs alone in an acyclic non-inverting mux network. MUX(s,a,b)=s is not a general identity; only MUX(x,x,x)=x when the inputs are identified. A counterexample to the asserted general identity is s=0,a=1,b=0. The specific target's impossibility follows from its value 1 at input 000 versus zero preservation of all such networks. MUX with both 0 and 1 constants is functionally complete, so describing that set as half-complete is misleading. The original interview having two stages is the external author's speculation.

Verified all eight circuit inputs against both the target and prior solution, and all four inputs for the constant-free AND/OR realizations. The source truth table matches the target; unlabeled data-pin orientation remains a stated assumption.'''

for a,b,c in product((0,1),repeat=3):
    assert mux(mux(b,0,a),1,c)==int(not(a and b and not c))==part_b(a,b,c)
for a,b in product((0,1),repeat=2):
    assert mux(a,a,b)==(a & b)
    assert mux(a,b,a)==(a | b)
assert mux(0,1,0)!=0
for x in (0,1):
    assert mux(x,x,x)==x

p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-011"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
assert q['id']=='PREP-011' and not any(x['path']==source for x in q['sources'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-14bd6ca5-b7d1-4d6d-aa59-d09d239378e1.png',root/source)
q['sources'].append({'type':'user_supplied_image','path':source,'received_on':'2026-09-27','role':'external_answer_for_review','note':'Correct circuit under stated pin orientation; prose includes claims corrected in review.'})
q['media_assets'].append({'type':'source_image','path':source,'description':'External two-MUX diagram, truth table and commentary supplied for review; preserve with corrections.'})
q.setdefault('solution_extensions',[]).append({'key':'external-and-select-implementation','content_he':he,'content_en':en,'source_image_path':source,'netlist':{'t':'MUX(b,0,a)','f':'MUX(t,1,c)'},'mux_convention':'MUX(select,data0,data1)','verification_script':'solutions/update_prep_011_external_answer.py'})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
q['verification'].setdefault('additional_checks',[]).append({'script_path':'solutions/update_prep_011_external_answer.py','status':'passed','method':'All 8 external-circuit tuples match target/prior design; all 4 AND/OR tuples verified without constants; diagonal identity and general-identity counterexample checked.'})
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==22
assert all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-011')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n![הפתרון החיצוני שנבדק](../'+source+')\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
print('PREP-011 external solution and source saved; 8 circuit tuples and 4 AND/OR tuples pass; no question-count change.')
