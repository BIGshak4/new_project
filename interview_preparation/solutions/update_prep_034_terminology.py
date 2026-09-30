"""Clarify the proposed FA/RCA/Carry-Select/Compound learning sequence."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
url='https://www-wjp.cs.uni-saarland.de/lehre/vorlesung/rechnerarchitektur/ws0304/uebungen/ueb2.pdf'
he='''הבהרת מינוחים בעקבות הכיוון שהציע המשתמש: הרצף FA -> RCA -> Carry-Select -> Compound Adder הוא כיוון טבעי לשאלה, אם CSA פירושו Carry-Select Adder. CSA משמש גם ל־Carry-Save Adder, ולכן אין לפרש את הקיצור בלי הקשר. אם מחברים אלה נלמדו בקורס מערכות לוגיות ספרתיות, כל השאלה עשויה להיות יישום של חומר הקורס; הסעיפים המאוחרים עדיין דורשים מודל עלויות ברור. אין לדעת בוודאות שזהו הפתרון שהמחבר התכוון אליו מתוך הצילום בלבד.

Compound Adder במינוח של מקור ההוראה המצורף מחשב במקביל A+B ו־A+B+1, ונבנה רקורסיבית ממחברים כאלה ומוקסים. זו מסגרת מתאימה להמשך ההסבר. השם לבדו אינו מבטיח יתרון מהירות; צריך לבדוק את המבנה והמסלול הקריטי.

חשוב: ספירת 3^n תתי־מחברים בפתרון הראשוני מתארת שכפול לא משותף של שלושה תתי־מחברים בכל צעד. אין להעתיק ממנה את נוסחת השטח למימוש Compound שמשתף את שני החישובים ומרכיב שני תתי־בלוקים דו־מוצאיים. הפתרון הראשוני נשאר הצעה תקינה תחת הנחותיו, אך אינו טבלת עלות כללית של Compound. בדיון עתידי על המימוש של הקורס צריך לחשב מחדש עלות לפי החיווט המדויק. המקור הטכני מאמת את המינוח והמבנה בלבד, ולא את מקור שאלת הראיון או את הסילבוס של המשתמש.'''
en='''The proposed FA -> RCA -> Carry-Select -> Compound sequence is a natural interpretation, conditional on CSA meaning carry-select rather than carry-save. If covered in the user's digital-logic course, all parts can be applications of that course. A compound adder in the cited teaching material simultaneously computes A+B and A+B+1 using recursive compound blocks and MUXes. The existing 3^n-area model is explicitly an unshared three-sub-adder recursion, not the area formula for a shared dual-result compound structure; do not transplant those counts. Timing/area require the actual topology and MUX/base-cell cost assumptions. The source validates terminology, not the interview author's intent or the user's syllabus.'''
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.rfind('{',0,s.index('"id": "PREP-034"'))
q,length=json.JSONDecoder().raw_decode(s[start:])
q['terminology_clarification']={'he':he,'en':en,'source_url':url,'checked_on':'2026-09-29'}
if not any(x.get('url')==url for x in q['sources']):
    q['sources'].append({'type':'technical_background','name':'Saarland University, Computer Architecture I, Exercise 3: Compound Adder','url':url,'checked_on':'2026-09-29','supports':'Dual-result recursive compound-adder definition, not interview/company attribution.'})
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated);assert before['questions'][:-1]==after['questions'][:-1]
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];text=md.read_text(encoding='utf-8')
if '## הבהרת מינוחים: Compound Adder' not in text:
    md.write_text(text+'\n\n## הבהרת מינוחים: Compound Adder\n\n'+he+'\n\n'+en+'\n\n[מקור הוראה ראשוני — אוניברסיטת זארלנד]('+url+')\n',encoding='utf-8')
print('PREP-034 terminology clarified; original proposal distinguished from shared compound-adder construction.')
