"""Persist the gate-sharing solution and its explicitly scoped gate counts."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
he='''### צמצום מספר השערים באמצעות שיתוף חישובים

השרטוט המורחב הקודם מחשב מחדש OR של ביטים גבוהים בכל שורה. אפשר לחסוך באמצעות OR מצטבר: p7=x7, ולאחר מכן pi=xi OR p(i+1), עבור i=6 עד 0. למשל p6=x6 OR x7, ואילו p5=x5 OR p6; אין צורך לחשב שוב x6 OR x7. כל pi אומר האם יש לפחות 1 אחד מה־MSB ועד למיקום i, כולל.

כדי להשאיר רק את ה־1 הראשון, נחבר yi=pi XOR p(i+1), עבור i=6 עד 0, ואת y7 נחבר ישירות ל־x7.

למה זה נכון? מעל ה־1 הראשון שני אותות ה־p הם 0 ולכן XOR מחזיר 0. במקום ה־1 הראשון, לפני הכנסת הביט ל־OR המצטבר הערך הוא 0 ואחריה 1, ולכן XOR מחזיר 1. בכל מקום נמוך יותר כבר נמצא 1, ולכן שני האותות 1 וה־XOR מחזיר 0. בקלט שכולו אפסים כל המוצאים נשארים אפס. אין שעון או זיכרון; זו שרשרת קומבינטורית.

```text
x       = 00101011
p       = 00111111
p >> 1  = 00011111
y       = 00100000
```

**ספירת שערים:** השרשרת משתמשת ב־7 שערי OR וב־7 שערי XOR בעלי שתי כניסות: 14 שערים כאשר XOR הוא תא בסיסי יחיד וחיווט והסתעפויות אינם נספרים. זו אינה הוכחה ש־14 הוא המינימום המוחלט, וספירה זו אינה מדידת שטח סיליקון: XOR עשוי להיות יקר יותר מ־OR.

השוואה מפורשת, לאחר מיפוי שערים רחבים לשערים בסיסיים בעלי שתי כניסות:

| מימוש | שערים | סך הכול |
|---|---|---|
| התנאי לכל פלט בנפרד, ללא שיתוף | 21 OR + 7 NOT + 7 AND | 35 |
| שיתוף OR מצטבר, וחסימת כל ביט עם AND ו־NOT | 6 OR + 7 NOT + 7 AND | 20 |
| שיתוף OR מצטבר וזיהוי הגבול ב־XOR | 7 OR + 7 XOR | 14 |

המעבר מ־35 ל־20 משווה אותה ספריית AND/OR/NOT. בשורה האחרונה נוסף XOR כשער בסיסי. אם NOR רחב נחשב שער יחיד, הספירה של השרטוט הקודם שונה; אין להשוות מספר בלוקים מצוירים בלי להגדיר מספר כניסות ושערים מותרים. מימוש ה־14 הוא חלופה פשוטה וחסכונית בספירת תאים, ולא הוכחה למינימום טכנולוגי.

יש מחיר בעומק: השרשרת המצוירת כוללת מסלול של עד 7 OR ועוד XOR, לעומת לכל היותר 3 OR ועוד XOR במימוש המקביל. מספר שכבות אינו מדידת השהיה פיזית; ספריית התאים והעומסים משפיעים גם הם.

![מימוש משותף מלא: שבעה OR ושבעה XOR](../diagrams/prep-014-shared-prefix-xor.png)

[מחולל השרטוט](../solutions/draw_prep_014_shared_prefix.py) · [בדיקת המעגלים וספירת השערים](../checks/check_prep_014_gate_counts.py).

שלושת המימושים נבנו כרשימות שערים ונבדקו על כל 256 הקלטים מול המפרט. ספירת השערים נבדקה מתוך אותן רשימות, ולא מתוך מספר הבלוקים בתרשים. לא בוצעה סינתזה או מדידת שטח פיזי.
'''
en='''Gate-sharing alternative: define p7=x7 and pi=xi OR p(i+1) for i=6..0. Output y7=x7 and yi=pi XOR p(i+1). Prefixes are 0 above the highest 1, first change to 1 at that position, then remain 1, so XOR isolates exactly that boundary. This uses seven two-input OR and seven two-input XOR cells. With two-input AND/OR and one-input NOT, the independently expanded conditions use 35 cells (21 OR, 7 NOT, 7 AND), while shared higher-bit prefixes use 20 (6 OR, 7 NOT, 7 AND). The 14-cell alternative assumes XOR is a primitive cell; it is not an equal-area comparison or a globally minimal circuit proof. Wide NOR primitives change the counting model. The ripple construction has a path of seven OR plus XOR, trading depth against the parallel-prefix circuit. All three explicit gate netlists passed all 256 inputs; no synthesis or physical area measurement was performed.'''
p=root/'questions.json'
s=p.read_text(encoding='utf-8')
start=s.index('{\n      "id": "PREP-014"')
q,n=json.JSONDecoder().raw_decode(s[start:])
q['area_optimization']={
    'display_section':'הצעה לפתרון','he':he,'en':en,
    'diagram_path':'diagrams/prep-014-shared-prefix-xor.png',
    'diagram_generator':'solutions/draw_prep_014_shared_prefix.py',
    'verification_script':'checks/check_prep_014_gate_counts.py',
    'verification_status':'passed_all_256_inputs_for_all_three_netlists',
    'optimality_scope':'Improved explicit constructions under stated cell models; no global minimum or silicon-area claim.'}
asset={'type':'solution_schematic','path':'diagrams/prep-014-shared-prefix-xor.png',
       'display_section':'הצעה לפתרון','description':'Shared ripple prefix: 7 two-input OR and 7 two-input XOR cells; direct MSB output.'}
if not any(a['path']==asset['path'] for a in q['media_assets']): q['media_assets'].append(asset)
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path']
t=md.read_text(encoding='utf-8')
if he not in t:
    t=t.replace('### קוד ובדיקה',he+'\n### קוד ובדיקה')
    t=t.replace('התוכן נוצר בסיוע AI',en+'\n\nהתוכן נוצר בסיוע AI')
md.write_text(t,encoding='utf-8')
data=json.loads(p.read_text(encoding='utf-8'))
assert data['question_count']==len(data['questions'])==14
assert all((root/a['path']).exists() for a in q['media_assets'])
assert he in md.read_text(encoding='utf-8')
print('PREP-014 area solution, exact cell-count model and diagram saved; 14 records; all media exist.')
