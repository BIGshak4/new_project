"""Attach N=2 schematics and a scoped efficiency comparison with borrow proof."""
import json
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'solutions'))
from prep_018_maximum_two import select_max

for a in range(4):
    for b in range(4):
        a1,a0=a>>1,a&1; b1,b0=b>>1,b&1
        lt1=(1-a1)&b1; lt0=(1-a0)&b0; eq1=int(a1==b1)
        recursive=lt1|(eq1&lt0)
        # Lower-bit borrow and upper-bit borrow propagation, no incoming borrow.
        borrow0=(1-a0)&b0
        borrow1=((1-a1)&b1)|((1^(a1^b1))&borrow0)
        result,s,d=select_max(a,b,2)
        assert recursive==borrow1==s==int(a<b)
        assert result==max(a,b)

he='''### השוואת שני המעגלים עבור N=2: הפרד ומשול מול מחסר

בשני השרטוטים מניחים A=A1A0,B=B1B0 ללא סימן, בטווח 0..3. אות הבחירה S הוא 1 כאשר A<B. אותו S מפעיל את שני ה־MUX של המוצא: כניסה 0 היא ביט מ־A וכניסה 1 היא הביט המקביל מ־B. לכן מתקבל מספר מקורי שלם; בשוויון נבחר A. אין שעון או FF.

**המעגל בשיטת הפרד ומשול:** שני תתי־משווים מטפלים בזוגות הביטים. LT1=NOT(A1) AND B1 מציין שהביט העליון של A קטן יותר, EQ1=XNOR(A1,B1) מציין שוויון למעלה, ו־LT0=NOT(A0) AND B0 מציין שהביט התחתון של A קטן יותר. מחברים S=LT1 OR (EQ1 AND LT0). פירושו: B מנצח אם הוא גדול למעלה, או אם למעלה יש שוויון והוא גדול למטה. עבור המקסימום הסופי ברוחב 2 לא צריך EQ0 או EQ של המספר כולו, ולכן הם אינם ממומשים בשרטוט. כאשר היחידה משמשת כתת־משווה בתוך רקורסיה גדולה יותר, יש להחזיר גם EQ=EQ1 AND XNOR(A0,B0).

![N=2: השוואה בהפרד ומשול ומבחר](../diagrams/prep-018-n2-recursive.png)

**המעגל עם מחסר:** מוסיפים אפס משמאל לשני המספרים ומחסרים D[2:0]={0,A1,A0}−{0,B1,B0}. זה מחסר ברוחב שלושה ביטים, לא שניים. טווח ההפרש הוא −3..3, ולכן הוא נכנס בשלושה ביטים במשלים ל־2. S=D2, ושני ביטי ההפרש האחרים אינם משמשים לתוצאה. לדוגמה A=01,B=10 נותן 001−010=111, כלומר −1, ולכן S=1 ובוחרים B=10. הרחבת אפס מתאימה כאן כי המספרים ללא סימן.

![N=2: מחסר מורחב ומבחר](../diagrams/prep-018-n2-subtractor.png)

**איזה פתרון יעיל יותר?** הבחירה הסופית בשני הפתרונות זהה, לכן משווים בעיקר את חישוב S. תכנון משווה ייעודי מבטא ישירות את המידע הדרוש — מי גדול — ואינו מחייב לחשב את כל ביטי ההפרש. אם משתמשים במחסר מלא כמכלול קבוע שאינו מפושט, חלק מהיציאות והלוגיקה שלו מיותרות למשימה. אבל אין להסיק מכך שהגישה הרקורסיבית תמיד קטנה או מהירה יותר: כאשר כלי סינתזה יכול לפשט את המחסר לפי היציאה היחידה שנצרכת, הלוגיקה יכולה להיות זהה.

אפשר לראות את השקילות במפורש. בחיסור A−B, ההשאלה מהביט התחתון היא borrow0=NOT(A0) AND B0, בדיוק LT0. ההשאלה מהביט העליון היא:

```text
borrow1 = (NOT(A1) AND B1) OR (XNOR(A1,B1) AND borrow0)
```

כאשר A1=0,B1=1 צריך השאלה בלי קשר לביט הקודם. כאשר A1=B1, השאלה שנכנסת ממשיכה הלאה. כאשר A1=1,B1=0 אין צורך בהשאלה יוצאת. לכן borrow1 הוא בדיוק LT1 OR (EQ1 AND LT0), כלומר S של המעגל הרקורסיבי. הביט D2 של המחסר המורחב שווה להשאלה הזאת. למשימה אין צורך לחשב D0,D1 כלל.

במימוש המפורש של המשווה בשרטוט, ובהנחה ש־XNOR הוא תא אחד, יש 2 NOT, 3 AND בעלי שתי כניסות, OR אחד ו־XNOR אחד לחישוב S — שבעה שערים — ועוד שני MUX של ביט אחד לבחירת המספר. זו ספירת המימוש המוצג, לא הוכחת מינימום ל־N=2 ולא השוואת שטח טרנזיסטורים. אפשר לפשט עוד או למפות אחרת לפי ספריית התאים. לדוגמה, בפונקציית max הלא מסומנת הביט העליון M1 שווה A1 OR B1, אך שני השרטוטים משאירים במכוון את אותה דרגת MUX כדי להשוות את שיטות ההכרעה בלי לשנות גם את צד הנתונים.

ברוחב כללי N, עץ השוואה מאוזן לפי LT/EQ נותן O(log N) עומק ו־O(N) גודל במודל שערים בעלי מספר כניסות חסום. מחסר ripple יכול לתת O(N) עומק, אך מחסר עם carry/borrow lookahead או חישוב prefix יכול גם הוא להשיג O(log N) עומק. לכן ההשוואה היא בין מבנים מסוימים, ולא בין המילים ״רקורסיה״ ו״חיסור״. קביעת שטח או השהיה בפועל דורשת ספריית תאים וסינתזה, שלא בוצעו כאן.

שני השרטוטים נבדקו חזותית, וכל 16 צירופי שני המספרים נבדקו לשקילות של נוסחת ההשוואה, השאלה בחיסור, ביט הסימן המורחב והפלט. [מחולל השרטוטים](../solutions/draw_prep_018_comparison.py). בדיקת השקילות נמצאת בתחילת [סקריפט העדכון](../solutions/update_prep_018_comparison.py).
'''
en='''For unsigned N=2, the divide-and-conquer comparator produces LT1=~A1&B1, EQ1=XNOR(A1,B1), LT0=~A0&B0, then S=LT1|(EQ1&LT0). EQ0 is unnecessary for this top-level maximum; a reusable recursive comparator also exports whole-word equality. The alternative zero-extends both operands to three bits, subtracts, and selects using D2. Both diagrams use the same two one-bit muxes to select the original A or B, ties choosing A.

An unpruned full subtractor computes unused D1,D0, whereas a dedicated comparator only needs S. However, borrow-only subtraction yields borrow0=~A0&B0 and borrow1=(~A1&B1)|(XNOR(A1,B1)&borrow0), exactly the recursive comparator equation. Synthesis can therefore make the designs identical; no unconditional area or delay superiority is claimed. The drawn comparator uses seven primitive cells if XNOR counts as one (2 NOT, 3 AND, 1 OR, 1 XNOR), plus two muxes; this is not a minimum-cell or physical-area proof. Balanced recursive comparison has O(log N) depth versus O(N) for ripple subtraction, but lookahead/prefix subtraction can also have O(log N) depth. Actual physical efficiency needs a concrete library and synthesis. All 16 two-bit cases passed equivalence checks; both schematics visually reviewed.'''
p=root/'questions.json';s=p.read_text(encoding='utf-8');start=s.index('{\n      "id": "PREP-018"')
q,n=json.JSONDecoder().raw_decode(s[start:])
q['n2_design_comparison']={'display_section':'הצעה לפתרון','he':he,'en':en,
    'diagram_generator':'solutions/draw_prep_018_comparison.py',
    'verification':'All 16 N=2 cases: recursive comparator, borrow-only logic, extended sign and maximum equivalent; schematics visually reviewed.'}
for suffix,desc in [('recursive','Two one-bit comparisons with LT/EQ merge and two shared-select muxes.'),('subtractor','Zero-extended 3-bit subtraction for N=2 inputs; D2 selects original operands, D1/D0 unused.')]:
    path=f'diagrams/prep-018-n2-{suffix}.png'
    if not any(a['path']==path for a in q['media_assets']):
        q['media_assets'].append({'type':'solution_schematic','path':path,'display_section':'הצעה לפתרון','description':desc})
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path'];t=md.read_text(encoding='utf-8')
if he not in t:md.write_text(t.replace('## תשובה קצרה לראיון',he+'\n'+en+'\n\n## תשובה קצרה לראיון'),encoding='utf-8')
assert all((root/a['path']).exists() for a in q['media_assets'])
data=json.loads(p.read_text(encoding='utf-8')); assert len(data['questions'])==data['question_count']==18
print('PREP-018: both N=2 diagrams, efficiency comparison and 16-case equivalence proof saved. 18 questions retained.')
