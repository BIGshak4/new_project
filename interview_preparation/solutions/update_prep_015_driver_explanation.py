"""Preserve the supplied explanation screenshot and clarify local cell inputs."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source='sources/prep-015-driver-table-clarification.png'
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-74120d47-01d3-446c-9d05-db69593f6721.png',root/source)
explanation='''### למה כל קופסה פעילה דווקא במצב שמופיע בטבלה?

צריך להבחין בין קלט המעגל כולו x,y ובין שתי הכניסות של קופסה מסוימת. A(x,n) אינה מקבלת x,y אלא x,n. לכן כאשר קלט המעגל הוא 01, הקופסה הזאת מקבלת דווקא 00: x=0 וגם n=0, כי n הוא 1 רק כאשר x,y שניהם אפס. הסימון A(x,n) מתאר חיבור חוטים, ולא קופסה חדשה עם טבלת אמת אחרת.

תמיד משתמשים באותם שני כללים: A מוציאה 1 על זוג הכניסות המקומי 00, ובשאר הזוגות Z; B מוציאה 0 על זוג הכניסות המקומי 11, ובשאר הזוגות Z.

נבחן קודם רק את A(x,n):

| קלט המעגל x,y | n | מה נכנס בפועל ל־A(x,n)? | יציאתה |
|---|---|---|---|
| 00 | 1 | 01 | Z |
| 01 | 0 | 00 | 1 |
| 10 | 0 | 10 | Z |
| 11 | 0 | 10 | Z |

כך רואים שהיא מוציאה 1 רק כשהמעגל מקבל 01. למה הבחירה הזאת הגיונית? כאשר x=0 יש רק שתי אפשרויות: 00 או 01. n מבדיל ביניהן: הוא 1 ב־00 ו־0 ב־01. A דורשת גם x=0 וגם n=0, ולכן בוחרת בדיוק את 01. החלפת x ב־y נותנת את A(y,n), שבוחרת בדיוק את 10.

כעת מציבים בכל ארבע הקופסאות. בכל תא רשום זוג הכניסות המקומי ואחריו ערך היציאה:

| x,y | n | B(x,y) | B(n,n) | A(x,n) | A(y,n) | הפלט המשותף |
|---|---|---|---|---|---|---|
| 00 | 1 | 00 → Z | 11 → 0 | 01 → Z | 01 → Z | 0 |
| 01 | 0 | 01 → Z | 00 → Z | 00 → 1 | 10 → Z | 1 |
| 10 | 0 | 10 → Z | 00 → Z | 10 → Z | 00 → 1 | 1 |
| 11 | 0 | 11 → 0 | 00 → Z | 10 → Z | 10 → Z | 0 |

למשל ב־01 רק A(x,n) מקבלת 00 ומוציאה 1. הקופסה B(x,y) מקבלת 01 ולכן Z, הקופסה B(n,n) מקבלת 00 ולכן Z, והקופסה A(y,n) מקבלת 10 ולכן Z. חיבור ארבע היציאות נותן 1. בכל שאר השורות פועלת בדיוק קופסה אחת באותו אופן. לכן אין התנגשות או פלט צף, והפלט המשותף הוא XOR.

[צילום טבלת ההסבר שסופק](../sources/prep-015-driver-table-clarification.png).
'''
p=root/'questions.json'; s=p.read_text(encoding='utf-8')
start=s.index('{\n      "id": "PREP-015"'); q,n=json.JSONDecoder().raw_decode(s[start:])
q['driver_explanation_he']=explanation
if not any(a['path']==source for a in q['media_assets']):
    q['media_assets'].append({'type':'user_supplied_clarification_image','path':source,'description':'Screenshot of the existing solution table supplied for explanation; not a new question.'})
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path']; t=md.read_text(encoding='utf-8')
if explanation not in t: md.write_text(t.replace('## תשובה קצרה לראיון',explanation+'\n## תשובה קצרה לראיון'),encoding='utf-8')
assert len(json.loads(p.read_text(encoding='utf-8'))['questions'])==15
print('PREP-015: local-input explanation and supplied clarification image saved. Question count unchanged: 15.')
