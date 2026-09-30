"""Save a step-by-step derivation of the upper priority encoder equations."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source='sources/prep-016-group-logic-clarification.png'
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-43428aa6-7dcf-4741-916b-1771b0ba43b7.png',root/source)
he='''### איך מגיעים למשוואות שמחליפות את הבקר החמישי?

כל Vg הוא ביט יחיד שאומר אם יש בקשה כלשהי בקבוצה g. הוא אינו מספר הפסיקה ולא מספר הקבוצה. רוצים לחשב שני ביטים G1,G0 שמייצגים את מספר הקבוצה הפעילה בעלת העדיפות הגבוהה ביותר. G1 הוא הביט השמאלי בקוד ו־G0 הימני. נניח שקבוצה 3 בעדיפות הגבוהה ביותר ואחריה 2,1,0.

| הקבוצה שנבחרת | G1 | G0 |
|---|---|---|
| 0 | 0 | 0 |
| 1 | 0 | 1 |
| 2 | 1 | 0 |
| 3 | 1 | 1 |

הבקר החמישי מקבל בדיוק את V0..V3 ומחשב את הטבלה הזאת עם עדיפות. לכן אפשר להחליפו במעגל קומבינטורי שמחשב את אותן יציאות.

**Y:** אנחנו רוצים לדעת אם לפחות קבוצה אחת פעילה. זו הגדרת OR: Y=V0 OR V1 OR V2 OR V3. כאשר כולן 0 נקבל Y=0; אחרת Y=1.

**G1:** מסתכלים על הביט השמאלי בקודים. הוא 1 רק לקבוצות 2 או 3. אם V3=1, קבוצה 3 מנצחת ולכן G1=1. אם V2=1, הזוכה היא קבוצה 2 או קבוצה 3 אם גם היא פעילה; בשני המקרים G1=1. אם שתיהן לא פעילות, אפשר לבחור רק קבוצה 0 או 1, שהביט השמאלי שלהן 0. לכן G1=V3 OR V2.

**G0:** הביט הימני הוא 1 לקבוצות 1 או 3, אבל 0 לקבוצות 0 או 2. אסור לכתוב רק V3 OR V1: אם קבוצות 1 ו־2 פעילות וקבוצה 3 אינה פעילה, הזוכה היא 2 והקוד חייב להיות 10, לא 11.

נכתוב קודם תנאים מלאים: קבוצה 3 מנצחת אם V3=1; קבוצה 1 מנצחת אם V1=1, V2=0 וגם V3=0. לכן:

```text
G0 = V3 OR (V1 AND NOT(V2) AND NOT(V3))
```

אפשר להשמיט את NOT(V3) מהסוגריים, אבל צריך להסביר למה. כאשר V3=1, האיבר הראשון של ה־OR כבר קובע G0=1, כך שערך הסוגריים לא משנה. כאשר V3=0, מתקיים NOT(V3)=1, ו־AND עם 1 אינו משנה את שאר הביטוי. לכן בשני המקרים נקבל אותה תוצאה אם נכתוב:

```text
G0 = V3 OR (V1 AND NOT(V2))
```

במילים: קבוצה 3 מדליקה את הביט הימני תמיד; קבוצה 1 יכולה להדליק אותו כשקבוצה 2 אינה פעילה. אם קבוצה 3 פעילה היא ממילא מנצחת ומדליקה את הביט הזה, ולכן אין צורך לחסום את האיבר של V1 בעזרתה.

**בדיקה מוחשית:** V3=0,V2=1,V1=1,V0=0. G1=0 OR 1=1. G0=0 OR (1 AND NOT(1))=0 OR (1 AND 0)=0. מתקבל G=10, כלומר קבוצה 2; זו הקבוצה הנכונה למרות שגם קבוצה 1 פעילה.

**למה V0 לא מופיע במשוואות של G?** קבוצה 0 מקודדת כ־00, ולכן אינה דורשת להדליק אף ביט בקוד. אם קבוצות 1,2,3 לא פעילות, G יוצא 00 בכל מקרה. אם V0=1 זו קבוצה 0 פעילה ו־Y=1; אם V0=0 אין בקשות בכלל ו־Y=0. אות Y הוא שמבדיל בין שני המצבים.

בחומרה: עבור G1 מחברים V3,V2 ל־OR. עבור G0 מעבירים V2 דרך NOT, את התוצאה עם V1 דרך AND, ואת תוצאת ה־AND עם V3 דרך OR. עבור Y עושים OR של ארבעת V. הפלט G ממשיך להפעיל את קווי הבחירה של ה־MUX וגם ליצור את שני הביטים העליונים של האינדקס; שאר המעגל אינו משתנה.

[צילום המשוואות שסופק לצורך ההסבר](../sources/prep-016-group-logic-clarification.png).
'''
# Verify the simplified and full equations directly on all group-valid patterns.
for v in range(16):
    v0,v1,v2,v3=[(v>>i)&1 for i in range(4)]
    g1=v3|v2
    full=v3|(v1&(1-v2)&(1-v3))
    simple=v3|(v1&(1-v2))
    assert full==simple
    assert ((g1<<1)|simple)==max(0,v.bit_length()-1)
    assert (v0|v1|v2|v3)==int(v!=0)
p=root/'questions.json'; s=p.read_text(encoding='utf-8'); start=s.index('{\n      "id": "PREP-016"')
q,n=json.JSONDecoder().raw_decode(s[start:])
q['group_logic_derivation_he']=he
q['group_logic_derivation_verification']='All 16 group-valid patterns checked; full and simplified G0 equations equivalent, group index and valid correct.'
if not any(a['path']==source for a in q['media_assets']):
    q['media_assets'].append({'type':'user_supplied_clarification_image','path':source,'description':'Existing group-selection equations supplied for explanation; not a new question.'})
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path']; t=md.read_text(encoding='utf-8')
if he not in t: md.write_text(t.replace('## תשובה קצרה לראיון',he+'\n## תשובה קצרה לראיון'),encoding='utf-8')
data=json.loads(p.read_text(encoding='utf-8'))
assert len(data['questions'])==data['question_count']==16
print('PREP-016: group-logic derivation and source image saved; all 16 group patterns PASS.')
