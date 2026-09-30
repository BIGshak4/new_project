"""Persist the intuitive parallel-product explanation and full schematic."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### הסבר אינטואיטיבי לשיפור ל־4.5 ns ושרטוט מלא

החלופה דורשת שני מכפלים במקום אחד. הרעיון הוא לחשב מראש את שתי התוצאות האפשריות בזמן שהקופסה השחורה מחליטה איזו מהן צריך. אין ניחוש של S ואין שינוי בפונקציה; עושים עבודה כפולה בחומרה ובוחרים בסוף תוצאה אחת.

ראשית נגזור את שתי התוצאות מהמעגל המקורי. כאשר S=0, ה־MUX השמאלי בוחר C, והימני מקבל NOT S=1 ובוחר B. לכן המכפל מחזיר B×C. כאשר S=1, השמאלי בוחר D והימני מקבל NOT S=0 ובוחר A. לכן התוצאה A×D. אין במעגל המקורי אפשרות של A×C או B×D עבור אות בחירה משותף זה.

נחבר B ו־C ישירות למכפל הראשון, ואת A ו־D ישירות למכפל שני. את מוצא הראשון P0=B×C נחבר לכניסה 0 של MUX במוצא, ואת מוצא השני P1=A×D לכניסה 1. אות S, שמגיע מאותה קופסה שחורה עם אותם קלטי E,F, מחובר ישירות לבחירת ה־MUX. S=0 מעביר P0; S=1 מעביר P1. שני ה־MUX שהיו לפני המכפל אינם נחוצים במבנה הזה, ואין צורך במהפך.

דוגמה: A=2,B=3,C=4,D=5. שני המכפלים מחשבים במקביל 3×4=12 ו־2×5=10. עוד לא צריך לדעת מה S. כאשר הוא מתייצב, ה־MUX מעביר 12 אם S=0 או 10 אם S=1. אלו אותן תוצאות שהמעגל המקורי היה מחשב לאחר בחירת זוג הכניסות.

**ציר הזמן במודל השאלה:** ברגע 0 קלטי הרגיסטרים זמינים ביציאותיהם; הקופסה השחורה ושני המכפלים מקבלים את קלטיהם במקביל. אחרי 2.7 ns שתי המכפלות מוכנות. אחרי 3 ns גם S מוכן, ובשלב הזה שתי כניסות הנתונים של ה־MUX כבר יציבות. מהמאוחר מבין זמני הנתונים והבחירה מוסיפים 1.5 ns של MUX. לכן המוצא יציב אחרי max(2.7,3)+1.5=4.5 ns.

לא מחברים 3+2.7, כי המכפלים אינם ממתינים לקופסה השחורה. לעומת זאת במימוש 7.2 ns המכפל ממתין לפלטי ה־MUX, שממתינים ל־S: קופסה שחורה 3, בחירה 1.5, כפל 2.7. במימוש החדש הכפל כבר הסתיים בזמן ההמתנה ל־S, ונשאר רק להעביר את התוצאה הנכונה דרך MUX.

![שני מכפלים במקביל ובחירה בסוף, כולל ציר זמן](../diagrams/prep-020-parallel-products.png)

הפסים בציר הזמן ממחישים מתי האותות מובטחים כיציבים במודל ההשהיות; הם אינם מחזורי שעון או פקודות התחלה של פעולות. כל המעגל קומבינטורי. ההנחות הקודמות נשמרות: השהיית MUX של 1.5 ns חלה גם על רוחב המכפלה, השהיות חיווט ו־clock-to-Q אינן נתונות, והוספת מכפל מותרת רק אם אילוצי המשאבים מאפשרים אותה. המסלול הקריטי החדש הוא E/F → קופסה שחורה → בחירת MUX → מוצא, באורך 4.5 ns. מסלול דרך כל אחד מהמכפלים אל המוצא הוא 2.7+1.5=4.2 ns.

[מחולל השרטוט](../solutions/draw_prep_020_parallel_products.py). השרטוט נבדק חזותית מול הפונקציה BC/AD ובדיקת ההשהיות הקיימת.
'''
en='''Compute both possible outputs while the black box computes S: P0=B*C and P1=A*D, using two multipliers. Feed P0/P1 to mux inputs 0/1, with direct select S. The original inverted right select produces BC for S=0 and AD for S=1, so this preserves behavior. Example A=2,B=3,C=4,D=5 gives candidate results 12 and 10; S chooses one after they have both been computed. Inputs are available at t=0, both products at 2.7 ns, and S at 3 ns; final output is stable after max(2.7,3)+1.5=4.5 ns. The timeline denotes combinational arrival times, not clocked steps. This adds a multiplier and assumes the given mux delay applies at product width. Figure includes all six source registers and the three parallel paths.'''
p=root/'questions.json';s=p.read_text(encoding='utf-8');start=s.index('{\n      "id": "PREP-020"')
q,n=json.JSONDecoder().raw_decode(s[start:])
q['parallel_products_explanation']={'display_section':'הצעה לפתרון','he':he,'en':en,
 'diagram_path':'diagrams/prep-020-parallel-products.png','diagram_generator':'solutions/draw_prep_020_parallel_products.py',
 'verification':'Visually checked source-register wiring, BC/AD pairing, mux 0/1/select pins and 2.7/3/4.5 ns timeline against previously verified model.'}
path='diagrams/prep-020-parallel-products.png'
if not any(a['path']==path for a in q['media_assets']):
    q['media_assets'].append({'type':'solution_schematic','path':path,'display_section':'הצעה לפתרון','description':'Two-multiplier conditional-resource optimization with full register wiring and arrival-time bars.'})
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path'];t=md.read_text(encoding='utf-8')
if he not in t:md.write_text(t.replace('## תשובה קצרה לראיון',he+'\n'+en+'\n\n## תשובה קצרה לראיון'),encoding='utf-8')
assert all((root/a['path']).exists() for a in q['media_assets'])
data=json.loads(p.read_text(encoding='utf-8')); assert len(data['questions'])==data['question_count']==20
print('PREP-020: full parallel-products schematic, intuitive example and timing explanation saved. 20 questions retained.')
