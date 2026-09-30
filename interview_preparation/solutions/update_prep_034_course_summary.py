"""Use the user's actual RCA/Conditional-Sum/Compound course definitions."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source='sources/prep-034-course-adder-summary.png'
he='''הבהרה מחייבת לפי סיכום הקורס שסיפק המשתמש: CSA כאן פירושו Conditional Sum Adder, ולא Carry-Select Adder כפי שהונח בתשובה הקודמת. יש להשתמש מעתה במינוח המדויק של הקורס. שמות אלה קשורים ברעיון חישוב מראש ובחירה אך אין להחליף ביניהם בלי לציין את המימוש.

כדי להפריד בין מספר הביטים לבין מספר הרמות, נסמן כאן N כרוחב המספר ו־k כמספר רמות החלוקה. בתמונת הקורס n הוא רוחב המספר; בשאלת הראיון n מתייחס למספר רמות. עבור 32 ביט N קבוע 32.

תמלול סיכום הקורס:

```text
Ripple Carry Adder (N)
Inputs: A[N-1:0], B[N-1:0], C[0]
Outputs: S[N-1:0], C[N]
Function: concatenation(C[N],S) = A + B + C[0]
Delay: Theta(N)
Cost:  Theta(N)

Conditional Sum Adder (N)
Inputs: A[N-1:0], B[N-1:0], C[0]
Outputs: S[N-1:0], C[N]
Function: concatenation(C[N],S) = A + B + C[0]
Delay: Theta(log2(N))
Cost:  Theta(N^(log2(3)))

Compound Adder (N)
Inputs: A[N-1:0], B[N-1:0]
Outputs: S[N:0], T[N:0]
S = A + B
T = A + B + 1
Delay: Theta(log2(N))
Cost:  Theta(N*log2(N))
```

הסבר להתאמה: המבנה הלא־משותף שנותח בפתרון הראשוני, עם שלושה תתי־מחברים בכל חלוקה, תואם את חסם העלות של Conditional Sum שבסיכום: נסיגת השטח היא 3A(N/2)+Theta(N), והשהיה D(N/2)+Theta(1). ב־Compound הרקורסיבי כל תת־בלוק מחזיר מראש שתי אפשרויות, ולכן ניתן להרכיב את שתי התוצאות משני תתי־בלוקים דו־מוצאיים וממוקסים. נסיגת השטח 2A(N/2)+Theta(N) נותנת Theta(N log N), ואותה צורת נסיגת השהיה נותנת Theta(log N).

המעבר RCA -> Conditional Sum משפר את סדר הגודל של ההשהיה, במחיר שטח. המעבר Conditional Sum -> Compound משפר את סדר הגודל של השטח, ושומר על השהיה לוגריתמית. אין להסיק מהטבלה לבדה ש־Compound מהיר יותר בפועל או קבוע פעמים יותר מהיר, ובפרט לא שהוא עונה בהכרח לדרישת ״מהירה אף יותר״ בסעיף 6 בלי ניתוח מדויק.

ממשקי הרכיבים אינם זהים: Compound שבתמונה אינו מקבל נשא כניסה ומוציא את שתי התוצאות. אם צריך מחבר עם Cin משתנה, אפשר לבחור ביניהן באמצעות בנק מוקסים ברוחב N+1; יש לספור גם את השהיית ושטח הבחירה. כש־Cin קבוע 0 אפשר להשתמש ישירות ב־S. סימוני Theta אינם נותנים את הקבועים הדרושים לטבלת t,s ולבחירת מספר הרמות האופטימלי. לכן עדיין יש צורך בעלות מוקסים ובחירת מימוש מדויקת.

מבחינת היכרות עם החומר, התמונה מראה שהרצף שהציע המשתמש מופיע בסיכום הלימוד שלו; אין צורך להציג אותו כחומר שחייב לדרוש קורס נוסף. לא נערכה בדיקת מימוש חדשה: זהו תיעוד הגדרות ותיקון מינוח, והבדיקות הפונקציונליות של המבנה הקודם נשארות בתוקף תחת ההנחות שלהן.'''
en='''The user's supplied course summary resolves the acronym: CSA means Conditional Sum Adder here, not Carry-Select as previously assumed. Use N for operand width and k for partition depth; the slide's n is width while the interview's n refers to levels. The slide states RCA delay/cost Theta(N)/Theta(N); Conditional Sum Theta(log N)/Theta(N^log2(3)); Compound Theta(log N)/Theta(N log N). The original unshared three-sub-adder recursion matches the course's Conditional Sum model (area recurrence 3A(N/2)+Theta(N)). Shared dual-output Compound uses two dual-result sub-blocks (2A(N/2)+Theta(N)); both have logarithmic modeled delay. Thus Compound improves asymptotic area relative to Conditional Sum, not the asymptotic delay, and the slide does not establish lower concrete latency. Compound has no carry-in in this interface; it returns S=A+B,T=A+B+1. A variable Cin interface needs an additional N+1-bit MUX bank to select the result, which adds area/delay. A fixed zero carry may use S directly. Theta bounds do not supply constants for t,s or an exact optimal partition depth. No new circuit verification is claimed for this terminology/material update.'''
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-034"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
assert not any(s.get('path')==source for s in q['sources'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-5f236e41-63fd-4b31-a492-fe6ac06a73a5.png',root/source)
q['sources'].append({'type':'user_supplied_study_material','path':source,'received_on':'2026-09-29','description':'Course summary defining RCA, Conditional Sum Adder and Compound Adder, with asymptotic delay/cost. Not additional company attribution.'})
q['media_assets'].append({'type':'study_reference_image','path':source,'description':'Exact course terminology, interfaces and complexity summary.'})
q['course_terminology']={'CSA':'Conditional Sum Adder','operand_width_symbol':'N','partition_level_symbol':'k','explanation_he':he,'explanation_en':en,'source_path':source}
q['terminology_clarification']['superseded_acronym_assumption']='CSA was provisionally interpreted as Carry-Select; supplied course material establishes Conditional Sum. Use course_terminology.'
q['topics']=list(dict.fromkeys(q['topics']+['conditional_sum','compound_adder']))
q['added_topic_tags']=list(dict.fromkeys(q['added_topic_tags']+['conditional_sum','compound_adder']))
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
after=json.loads(updated);assert before['questions'][:-1]==after['questions'][:-1]
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n## תיקון לפי סיכום הקורס: CSA הוא Conditional Sum\n\n![סיכום הקורס שסיפק המשתמש](../'+source+')\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\nהבהרה ל־PREP-034 לפי סיכום הקורס: CSA פירושו Conditional Sum Adder. יש להבדיל מרוחב המילה N ומספר הרמות k, ולהבחין בין שיפור שטח ב־Compound לבין שיפור השהיה. תמונת הסיכום נשמרה.\n',encoding='utf-8')
print('Course summary preserved; CSA corrected to Conditional Sum, interfaces and area-vs-delay distinction documented.')
