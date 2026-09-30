"""Save the explicit AND/OR/NOT explanation with the question."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### פירוט המימוש באמצעות AND, OR ו־NOT בלבד

נגדיר Hi: האם יש לפחות 1 אחד בביטים שמעל xi, בלי לכלול את xi עצמו? זה שונה מה־pi במימוש XOR, שכלל גם את הביט הנוכחי. מספיק ש־Hi=1 כדי לחסום את xi. לכן yi=xi AND NOT(Hi): ה־NOT מחזיר 1 כאשר אין שום 1 גבוה יותר, וה־AND דורש שגם xi עצמו יהיה 1.

```text
y7 = x7                 H6 = x7
y6 = x6 AND NOT(H6)      H5 = H6 OR x6
y5 = x5 AND NOT(H5)      H4 = H5 OR x5
y4 = x4 AND NOT(H4)      H3 = H4 OR x4
y3 = x3 AND NOT(H3)      H2 = H3 OR x3
y2 = x2 AND NOT(H2)      H1 = H2 OR x2
y1 = x1 AND NOT(H1)      H0 = H1 OR x1
y0 = x0 AND NOT(H0)
```

כל דגל H מחושב פעם אחת בלבד ומשמש גם את הפלט באותה שורה וגם את שער ה־OR שמחשב את הדגל הבא. לדוגמה H5=x7 OR x6, ולכן H4=H5 OR x5 חוסך חישוב מחדש של x7 OR x6. אין צורך לחשב דגל אחרי x0, כי אין ביט נוסף לחסום.

בדוגמה 00101011: H6=0 ולכן y6=0 AND 1=0; H5=0 ולכן y5=1 AND 1=1. כעת H4=H5 OR x5=0 OR 1=1. גם כל דגלי H שמתחתיו יהיו 1, ולכן ה־NOT שלהם מחזיר 0 וכל הפלטים התחתונים נחסמים. y7=x7=0, ולכן התוצאה 00100000.

הספירה היא 6 OR לבניית H5 עד H0, ועוד 7 NOT ו־7 AND עבור y6 עד y0: בסך הכול 20 שערים. y7 ו־H6 הם חיבורים ישירים. זהו מעגל קומבינטורי; המילה ״הבא״ מתייחסת לביט הבא ולא למחזור שעון.

![מימוש מלא של 20 שערים עם שמות חוטים](../diagrams/prep-014-shared-and-or-not.png)

בשרטוט, הופעות של אותו שם H מציינות את אותו חוט. בצד שמאל מחשבים את ששת הדגלים המשותפים, ובצד ימין מחשבים את שבעת הפלטים הנמוכים. [מחולל השרטוט](../solutions/draw_prep_014_shared_basic.py). מימוש shared_basic בבדיקת רשימות השערים עבר את כל 256 הקלטים.
'''
p=root/'questions.json'; s=p.read_text(encoding='utf-8')
start=s.index('{\n      "id": "PREP-014"')
q,n=json.JSONDecoder().raw_decode(s[start:])
q['area_optimization']['and_or_not_explanation_he']=he
asset={'type':'solution_schematic','path':'diagrams/prep-014-shared-and-or-not.png',
       'display_section':'הצעה לפתרון','description':'Explicit shared higher-bit flags: 6 OR, 7 NOT, 7 AND. Repeated net labels denote the same signal.'}
if not any(a['path']==asset['path'] for a in q['media_assets']): q['media_assets'].append(asset)
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path']; t=md.read_text(encoding='utf-8')
if he not in t: md.write_text(t.replace('### קוד ובדיקה',he+'\n### קוד ובדיקה'),encoding='utf-8')
data=json.loads(p.read_text(encoding='utf-8'))
assert len(data['questions'])==data['question_count']==14
assert all((root/a['path']).exists() for a in q['media_assets'])
print('PREP-014: AND/OR/NOT explanation and schematic saved; all media paths valid.')
