"""Attach both hierarchy schematics and the step-by-step explanation."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### פתרון הפרד ומשול עם שרטוט מלא

נניח שכניסה בעלת מספר גבוה יותר מקבלת עדיפות גבוהה יותר. ארבעת הבקרים המקומיים C0..C3 מקבלים בהתאמה את In0..3, In4..7, In8..11, In12..15. נסמן את פלט Y של כל קבוצה ב־Vg, ואת קוד Z המקומי בן שני הביטים ב־Kg. שינוי השמות רק נועד להבחין בין החוטים של ארבעת הבקרים.

בקר חמישי C4 מקבל את V0..V3. כל כניסה שלו מייצגת קבוצה: 1 אומר שבקבוצה יש לפחות בקשה אחת. לכן קוד Z שלו, שנסמן G, מזהה את הקבוצה הפעילה בעלת המספר הגבוה ביותר. פלט Y שלו הוא אות Y הכללי: יש לפחות בקשה אחת באחת הקבוצות. אם קבוצה 3 פעילה היא עדיפה על כל קבוצה נמוכה יותר, גם אם הקוד המקומי של הקבוצה הנמוכה גדול יותר.

ארבעת הקודים K0..K3 מחוברים לארבע כניסות הנתונים של MUX 4:1, ברוחב שני ביטים לכל כניסה. קוד G מחובר לבחירה: G=00 מעביר K0; G=01 מעביר K1; G=10 מעביר K2; G=11 מעביר K3. נסמן את מוצא ה־MUX ב־L[1:0]. אפשר להשתמש בשני MUX 4:1 של ביט אחד, עם אותם קווי בחירה, במקום בבלוק אחד ברוחב שני ביטים.

ליצירת הקוד הסופי, G הוא שני הביטים העליונים ו־L הוא שני הביטים התחתונים. לכן P={G,L}. זה חיווט, לא שער חיבור. הסיבה היא שאינדקס הפסיקה שווה 4 כפול מספר הקבוצה ועוד המיקום המקומי. ארבע כפול G הוא הזזה בשני ביטים: GG00. המיקום המקומי בין 0 ל־3 ממלא את שני האפסים האלה, ללא נשא. למשל G=10 הוא קבוצה 2, ולכן בסיס הקבוצה הוא 1000 (8); L=01 מוסיף את המיקום 1 ונותן 1001 (9).

דוגמה נוספת: In2,In6,In13 פעילים. C0 מדווח V0=1,K0=10, ו־C1 מדווח V1=1,K1=10. C2 מדווח V2=0 והקוד שלו אינו רלוונטי. C3 מדווח V3=1,K3=01, כי In13 הוא במקום המקומי 1 בקבוצה שמתחילה ב־In12. C4 בוחר קבוצה 3: G=11,Y=1. ה־MUX מעביר את K3=01. הפלט P=1101 הוא 13.

![היררכיה עם חמישה בקרים ו־MUX](../diagrams/prep-016-five-controllers.png)

כל שמות החוטים החוזרים בשרטוט מציינים את אותו חיבור. קווי K,G,L הם בני שני ביטים. קו קבוצת הקלט הוא ארבעה חוטים נפרדים, לא OR ביניהם. אותות Y,Vg הם בני ביט אחד. כאשר Y=0, אפשר לאפס את ארבעת ביטי P באמצעות ארבעה AND עם Y, כפי שמצוין בבלוק האחרון. זו בחירה כדי לתת פלט מוגדר; השאלה אינה דורשת קוד מסוים כשאין פסיקה. Y נותר 0, וכך מבדילים מ־In0 פעיל שמחזיר גם הוא קוד 0000 אבל Y=1. אין FF ואין שעון.

**צמצום לארבעה בקרים במסגרת החלוקה לקבוצות:** מאחר שמותר להוסיף שערים, אפשר להחליף רק את C4 במעגל הבא, ולהשאיר את ארבעת הבקרים המקומיים, ה־MUX והשרשור ללא שינוי:

```text
Y  = V0 OR V1 OR V2 OR V3
G1 = V3 OR V2
G0 = V3 OR (V1 AND NOT(V2))
```

אם V3=1 נקבל G=11. אם V3=0,V2=1 נקבל G=10. אם שניהם אפס ו־V1=1 נקבל G=01. אחרת G=00; Y מבדיל בין קבוצה 0 פעילה לבין היעדר פסיקות. כך נוסחת G0 אינה מאפשרת לקבוצה 1 לעקוף את קבוצה 2.

![ארבעה בקרים ושערים לבחירת הקבוצה](../diagrams/prep-016-four-controllers.png)

חמישה בקרים הם מימוש היררכי תקין, וארבעה הם שיפור כששומרים בקר לכל קבוצה ומחליפים את הבחירה העליונה בשערים. אין לטעון שארבעה הם מינימום מוחלט לפי המקור: אם אין הגבלה על השערים הנוספים, אפשר לממש את כל הפונקציה בשערים ולהשתמש באפס בקרים, או באחד אם עצם השימוש בבקר הוא חובה. לפירוט מודלי העלות ראו את דיון המינימום לעיל.

שני השרטוטים נבדקו חזותית מול מודלי המשוואות שעברו בדיקה ממצה על כל 65,536 הקלטים. [מחולל השרטוטים](../solutions/draw_prep_016_hierarchy.py).
'''
p=root/'questions.json'; s=p.read_text(encoding='utf-8'); start=s.index('{\n      "id": "PREP-016"')
q,n=json.JSONDecoder().raw_decode(s[start:])
q['hierarchy_diagram_explanation_he']=he
q['solution_diagram_generator']='solutions/draw_prep_016_hierarchy.py'
q['solution_diagram_path']='diagrams/prep-016-five-controllers.png'
for stem,desc in [('five','Five controllers: four local groups, fifth for group selection, two-bit mux and concatenation.'),
                  ('four','Four local controllers plus explicit group-selection equations; same mux and concatenation.')]:
    path='diagrams/prep-016-'+stem+'-controllers.png'
    if not any(a['path']==path for a in q['media_assets']):
        q['media_assets'].append({'type':'solution_schematic','path':path,'description':desc,'display_section':'הצעה לפתרון'})
q['verification']['diagram_review']='Both net-labelled block schematics visually checked: input group mapping, valid and index buses, mux selector, concatenation and invalid-output masking.'
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path']; t=md.read_text(encoding='utf-8')
if he not in t: md.write_text(t.replace('## תשובה קצרה לראיון',he+'\n## תשובה קצרה לראיון'),encoding='utf-8')
data=json.loads(p.read_text(encoding='utf-8'))
assert len(data['questions'])==data['question_count']==16
assert all((root/a['path']).exists() for a in q['media_assets'])
print('PREP-016: both diagrams, generator and intuitive explanation saved; all links valid; 16 questions.')
