"""Save the user-proposed eight-cell construction as an intuitive alternative."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### חלופה שהובאה בשיחה: שמונה רכיבים עם שלילות מפורשות

החלופה תקינה ומממשת את אותו XOR, אך אינה אותו מעגל: היא משתמשת בשמונה רכיבים במקום שבעה. השאלה המקורית אינה דורשת במפורש מינימום רכיבים, ולכן היא עונה על הדרישה. לצורך לימוד זו דרך ישירה יותר: קודם מייצרים את ההפכים של שני הקלטים, ואחר כך מקצים קופסה לכל שורה בטבלת האמת. ההסבר הזה עצמאי ואינו משתמש באות העזר n של המימוש הקודם.

**יצירת ההפכים:** נחבר יחד את A(x,x) ואת B(x,x) כדי לקבל nx=NOT(x). אם x=0, הראשון מוציא 1 והשני Z, ולכן nx=1. אם x=1, הראשון Z והשני מוציא 0, ולכן nx=0. באותה דרך A(y,y) ו־B(y,y) יוצרים ny=NOT(y). בסך הכול ארבעה רכיבים, ושני החוטים nx,ny תמיד מוגדרים.

**מה מנסים לעשות בפלט?** להוציא 1 במקרים 01 ו־10, ו־0 במקרים 00 ו־11. A מסוגלת להוציא 1, לכן נשתמש בה לשני המקרים הראשונים. B מסוגלת להוציא 0, לכן נשתמש בה לשני האחרונים.

למקרה 01: צריך רכיב A שמקבל 00 דווקא כאשר x=0,y=1. x כבר 0, וההפך של y הוא 0, ולכן מחברים A(x,ny). התנאים להפעלתו הם x=0 וגם ny=0; מאחר ש־ny הוא ההפך של y, זה אומר בדיוק x=0,y=1.

למקרה 10: x=1 ולכן nx=0, ו־y=0 כבר. מחברים A(nx,y); היא מקבלת 00 ומוציאה 1 רק במצב הזה.

למקרה 11: מחברים B(x,y), שמקבלת 11 ומוציאה 0 בדיוק במצב הזה.

למקרה 00: שני ההפכים nx,ny הם 1. מחברים B(nx,ny), שמקבלת 11 ומוציאה 0 בדיוק במצב הזה.

מחברים את ארבע היציאות לחוט הפלט Y. A1,A2,B1,B2 כאן הם ארבעת רכיבי שלב הפלט בלבד; ארבעת רכיבי המהפכים נוספים עליהם.

| x | y | nx | ny | A1(x,ny) | A2(nx,y) | B1(x,y) | B2(nx,ny) | Y |
|---|---|---|---|---|---|---|---|---|
| 0 | 0 | 1 | 1 | Z | Z | Z | 0 | 0 |
| 0 | 1 | 1 | 0 | 1 | Z | Z | Z | 1 |
| 1 | 0 | 0 | 1 | Z | 1 | Z | Z | 1 |
| 1 | 1 | 0 | 0 | Z | Z | 0 | Z | 0 |

למשל עבור x=0,y=1 נקבל nx=1,ny=0. הזוגות שנכנסים לארבע קופסאות הפלט הם בהתאמה 00,11,01,10. רק A1 מוציאה 1; היתר Z. בפרט A2 שמקבלת 11 אינה מוציאה 0 אלא Z: כל סוג רכיב פועל רק לפי טבלת האמת המקורית שלו.

בכל שורה בדיוק אחד מארבעת רכיבי הפלט פעיל. כל שאר היציאות Z, ולכן אין התנגשות או פלט צף. גם חוטי ההיפוך nx ו־ny תמיד בעלי ערך חוקי. הספירה: שני A ושני B למהפכים, ועוד שני A ושני B לפלט — ארבעה מכל סוג, שמונה בסך הכול.

בדיקת Python ממצה לכל ארבעת הקלטים אימתה גם את שתי השלילות, גם את ארבע היציאות הבודדות, גם נהג פעיל יחיד בפלט וגם את התאמת Y ל־XOR. החלופה נוספה ל־checks/check_prep_015.py. זו בדיקת מצבים יציבים ולא בדיקת תזמון פיזי.
'''
en='''User-proposed alternative: join A(x,x) with B(x,x) to produce nx=NOT(x), and A(y,y) with B(y,y) to produce ny=NOT(y). These use four cells and always resolve to binary signals. Join A(x,ny), A(nx,y), B(x,y), B(nx,ny) for the final output. They respectively drive 1 at 01, 1 at 10, 0 at 11, and 0 at 00, with exactly one active final driver per case. Total eight cells (four A, four B). This is functionally equivalent to the seven-cell solution but a different, more direct construction; the source does not explicitly request a minimum. Exhaustive Python checks cover both inversions, individual drivers, unique final driver and XOR output on all four input cases. Static correctness only.'''
p=root/'questions.json'; s=p.read_text(encoding='utf-8')
start=s.index('{\n      "id": "PREP-015"'); q,n=json.JSONDecoder().raw_decode(s[start:])
q['eight_cell_alternative']={'origin':'user_proposed_construction_in_chat','display_section':'הצעה לפתרון',
    'he':he,'en':en,'component_count':8,'counts_by_type':{'A':4,'B':4},
    'verification':{'status':'passed','script_path':'checks/check_prep_015.py',
    'method':'Four input cases, both inversions, active-driver count and resolved output checked.'}}
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path']; t=md.read_text(encoding='utf-8')
if he not in t: md.write_text(t.replace('## תשובה קצרה לראיון',he+'\n'+en+'\n\n## תשובה קצרה לראיון'),encoding='utf-8')
data=json.loads(p.read_text(encoding='utf-8'))
assert len(data['questions'])==data['question_count']==15
print('PREP-015: user-proposed eight-cell alternative saved in Hebrew and English, with verification; count unchanged.')
