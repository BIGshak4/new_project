"""Record the two-bit compare/select circuit and recursive comparison interface."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### חלופת הפרד ומשול: מעגל בסיסי עבור N=2

הפתרון המקורי שהוכן משתמש במחסר מורחב וב־MUX. החלופה כאן משווה קודם את החלק העליון, ופונה לחלק התחתון רק במקרה של שוויון. זהו המבנה של משווה רקורסיבי; במקרה של שני ביטים כל חלק הוא ביט יחיד. נניח מספרים ללא סימן A=A1A0 ו־B=B1B0, שערכיהם 0..3. הפלט M=M1M0 הוא המספר הגדול בשלמותו.

הביטים A1,B1 שווים במשקלם ל־2, ואילו A0,B0 שווים במשקלם ל־1. לכן אם B1=1 ו־A1=0, B בהכרח גדול יותר: הוא לפחות 2 ואילו A לכל היותר 1. אם A1=1 ו־B1=0, A בהכרח גדול יותר. רק כאשר הביטים העליונים שווים צריך להשוות את התחתונים.

נגדיר E1=XNOR(A1,B1), שמחזיר 1 עבור 00 או 11 ו־0 עבור 01 או 10. אם משתמשים רק ב־AND/OR/NOT, אפשר לממש E1=(A1 AND B1) OR (NOT A1 AND NOT B1).

נבנה אות בחירה S שמשמעותו A<B, כלומר צריך לבחור את B:

```text
T1 = NOT(A1) AND B1
T0 = E1 AND NOT(A0) AND B0
S  = T1 OR T0
```

T1 מזהה שהביט העליון של B גדול מזה של A. T0 מזהה שהביטים העליונים שווים, ובביט התחתון B גדול מ־A. ה־E1 חוסם הכרעה שגויה של הביט התחתון כאשר כבר יש הכרעה למעלה. למשל A=10,B=01: למטה B0=1 ו־A0=0, אבל E1=0 ולכן T0=0, וגם T1=0. מתקבל S=0 ונבחר A=10, כפי שנדרש. עבור A=10,B=11 הביטים העליונים שווים, E1=1, ולכן T0=1 ונבחר B=11. בשוויון מלא T1=T0=0 ולכן בוחרים A, שערכו זהה ל־B.

נחבר שני MUX 2:1 של ביט אחד עם אותו S: בראשון D0=A1,D1=B1 והמוצא M1; בשני D0=A0,D1=B0 והמוצא M0. כך שני הביטים נלקחים יחד מאותו מספר. אין לבחור בנפרד את הביט הגדול מכל זוג: עבור A=10,B=01 בחירה כזאת תייצר 11, שאינו אף אחד מהקלטים.

```text
M1 = (A1 AND NOT S) OR (B1 AND S)
M0 = (A0 AND NOT S) OR (B0 AND S)
```

![מעגל השוואה ובחירת מקסימום לשני מספרים בני שני ביטים](../diagrams/prep-018-two-bit-maximum.png)

השרטוט כולל XNOR, שני מהפכים, שני תנאי AND, OR ושני MUX עם אות בחירה משותף. AND בעל שלוש כניסות ניתן לפצל לשני AND בעלי שתי כניסות. שמות חוטים חוזרים מתייחסים לאותו חיבור. זהו מימוש ישיר לצורך ההסבר, ללא טענת מינימום שערים מדויק.

**ממשק שימושי להמשך הרקורסיה:** יחידת ההשוואה צריכה להוציא LT=(A<B), שהוא S, וגם EQ=(A=B). כאן EQ=E1 AND XNOR(A0,B0). שרשור שני ערכי מקסימום מקומיים אינו מספיק; צריך מידע על תוצאת ההשוואה ועל השוויון. בחיבור חצי עליון H וחצי תחתון L, מחשבים LT=LT_H OR (EQ_H AND LT_L), ו־EQ=EQ_H AND EQ_L. מקרה הבסיס המתמטי הוא ביט אחד, שבו LT=NOT A AND B ו־EQ=XNOR(A,B). עץ מאוזן של יחידות השוואה נותן O(N) שערים ועומק O(log N) במודל שערים בעלי מספר כניסות חסום; בחירת שני המספרים המלאים נעשית לפי LT הסופי. אין צורך בשעון או בזיכרון.

בדיקות: כל 16 זוגות הקלטים ב־N=2 נבדקו עבור המשוואות המדויקות בשרטוט, כולל השוואה, שוויון והפלט. נוסחת החיבור הרקורסיבית נבדקה באופן ממצה ב־87,380 זוגות ברוחבים 1 עד 8. מדובר בבדיקת מודל Python ולא בסימולציית HDL או סינתזה.

[מחולל השרטוט](../solutions/draw_prep_018_two_bit.py) · [מודל ובדיקה רקורסיבית](../checks/check_prep_018_recursive.py).
'''
en='''Two-bit unsigned alternative: E1=XNOR(A1,B1), T1=NOT(A1) AND B1, T0=E1 AND NOT(A0) AND B0, and S=T1 OR T0. S means A<B. Feed A1/B1 to data inputs 0/1 of one mux and A0/B0 to another, both selected by S. Thus the entire original A or B is returned; ties select A. For recursive composition also export EQ=E1 AND XNOR(A0,B0). Larger blocks combine LT=LT_H OR (EQ_H AND LT_L), EQ=EQ_H AND EQ_L; one-bit base LT=NOT(A) AND B and EQ=XNOR(A,B). A balanced comparator has O(N) size and O(log N) bounded-fan-in depth. Do not concatenate independent local maxima. All 16 two-bit gate cases and all 87,380 unsigned pairs at widths 1..8 passed. No HDL simulation or synthesis claimed.'''
p=root/'questions.json';s=p.read_text(encoding='utf-8');start=s.index('{\n      "id": "PREP-018"')
q,n=json.JSONDecoder().raw_decode(s[start:])
q['recursive_two_bit_alternative']={'display_section':'הצעה לפתרון','he':he,'en':en,
    'verification_script':'checks/check_prep_018_recursive.py','verification_status':'passed',
    'diagram_generator':'solutions/draw_prep_018_two_bit.py','diagram_path':'diagrams/prep-018-two-bit-maximum.png'}
path='diagrams/prep-018-two-bit-maximum.png'
if not any(a['path']==path for a in q['media_assets']):
    q['media_assets'].append({'type':'solution_schematic','path':path,'display_section':'הצעה לפתרון','description':'Unsigned two-bit priority comparison and two muxes sharing select; optional EQ for recursive composition documented.'})
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path']; t=md.read_text(encoding='utf-8')
if he not in t: md.write_text(t.replace('## תשובה קצרה לראיון',he+'\n'+en+'\n\n## תשובה קצרה לראיון'),encoding='utf-8')
assert all((root/a['path']).exists() for a in q['media_assets'])
data=json.loads(p.read_text(encoding='utf-8'));assert len(data['questions'])==data['question_count']==18
print('PREP-018: two-bit circuit, recursive LT/EQ interface, drawing and checked alternative saved.')
