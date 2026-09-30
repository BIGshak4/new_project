"""Record the full intuitive AND/NOR derivation and scope of gate efficiency."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
he='''### הפתרון המלא לפי AND עם NOR של הביטים הקודמים

הרעיון נכון: yi=xi AND NOR של כל הביטים שמשמאלו. שני התנאים חייבים להתקיים יחד: הביט עצמו 1, ואף ביט משמעותי יותר אינו 1. y7=x7 כי אין ביט שמשמאל ל־x7. אין לערבב בין שמו של ביט הקלט xi לבין שמו של ביט הפלט yi.

```text
y7 = x7
y6 = x6 AND NOT(x7)
y5 = x5 AND NOT(x7 OR x6)
y4 = x4 AND NOT(x7 OR x6 OR x5)
y3 = x3 AND NOT(x7 OR x6 OR x5 OR x4)
y2 = x2 AND NOT(x7 OR x6 OR x5 OR x4 OR x3)
y1 = x1 AND NOT(x7 OR x6 OR x5 OR x4 OR x3 OR x2)
y0 = x0 AND NOT(x7 OR x6 OR x5 OR x4 OR x3 OR x2 OR x1)
```

כדי לחסוך שערים, לא בונים את כל הביטויים הארוכים בנפרד. נגדיר Hi בתור OR של כל הביטים שמשמאל ל־xi: הוא 1 אם כבר יש שם אחד. נשתף את תוצאות הביניים:

```text
H6 = x7
H5 = H6 OR x6
H4 = H5 OR x5
H3 = H4 OR x4
H2 = H3 OR x3
H1 = H2 OR x2
H0 = H1 OR x1
yi = xi AND NOT(Hi)   for i=6..0
y7 = x7
```

למשל H4=x7 OR x6 OR x5, ולכן H3=H4 OR x4 מוסיף רק את x4 לבדיקה הקיימת. y3=x3 AND NOT(H3) הוא בדיוק ה־AND עם NOR של ארבעת הביטים הקודמים שהוצע. Hi הוא שם חוט, לא רגיסטר או תא זיכרון. זה מעגל קומבינטורי ללא שעון.

![מימוש מלא עם שיתוף OR ויציאות AND/NOT](../diagrams/prep-014-shared-and-or-not.png)

קריאת השרטוט: צד שמאל מייצר את חוטי H המשותפים; צד ימין משתמש בהם לפלטים. כל הופעה של אותו שם H היא אותו חוט. החיבורים H6=x7 ו־y7=x7 ישירים, ומצוינים בכותרת ובתחתית.

בדוגמה 00110101: x7=x6=0 ולכן y7=y6=0. x5=1 ואין אחד משמאלו, ולכן y5=1. לכל ביט מתחת ל־x5 כבר יש אחד משמאל (x5), ולכן ה־NOT של Hi נותן 0 וה־AND חוסם את הביט. מתקבל 00100000. בקלט 00000000 כל yi=0 כי כל xi=0.

**דיוק לגבי אופטימליות:** בתנאי ששערי AND/OR הם בעלי שתי כניסות ו־NOT שער נפרד, המימוש המשותף משתמש ב־6 OR, 7 NOT ו־7 AND: עשרים שערים, לעומת 35 בבנייה עצמאית של כל ביטוי עם שרשראות OR נפרדות. הספירה נבדקה ברשימת שערים על כל 256 הקלטים. זה מימוש חסכוני עם שיתוף חישובים, לא הוכחה למינימום שערים מוחלט. NOR רחב כשער בסיסי משנה את הספירה; XOR כשער בסיסי מאפשר את חלופת 14 התאים שכבר נשמרה; ועץ OR מקביל יכול להקטין עומק לעומת השרשרת. אין להכריז על מינימום שטח או השהיה בלי להגדיר ספריית שערים ומטרת האופטימיזציה. לראיון, הפתרון מבוסס AND/NOR עונה ישירות על המפרט ושיתוף OR מדגים צמצום לוגיקה בלי להחליף את דרך החשיבה.
'''
en='''Full AND/NOR explanation: yi=xi AND NOT(OR of all more significant bits), with y7=x7. To avoid duplicating each prefix, define H6=x7 and H(i-1)=Hi OR xi for i=6..1. Then yi=xi AND NOT(Hi), i=6..0. For example H3=H4 OR x4=x7 OR x6 OR x5 OR x4. H labels are shared combinational wires, not registers. The existing full 20-gate diagram shows their generation on the left and output masking on the right. Example 00110101 yields 00100000 because bit 5 is the first one and blocks every lower bit; all-zero input yields zero.

Under two-input AND/OR and separate NOT cells, shared implementation costs 6 OR+7 NOT+7 AND=20 gates versus 35 for independently expanded outputs, as previously exhaustively verified for all 256 inputs. This is an efficient shared construction, not a proof of globally minimum area or delay. Wide NOR primitives, XOR primitives (existing 14-cell alternative) and parallel-prefix topology change the tradeoffs. The unspecified source gate library does not establish one uniquely optimal implementation.'''

x=int('00110101',2)
ys=[((x>>i)&1) & int((x>>(i+1))==0) for i in range(8)]
assert sum(y<<i for i,y in enumerate(ys))==int('00100000',2)
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-014"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
q.setdefault('solution_extensions',[]).append({'key':'and-nor-shared-full-explanation','created_on':'2026-09-28','content_he':he,'content_en':en,'diagram_path':'diagrams/prep-014-shared-and-or-not.png','verification_reference':'Existing exhaustive shared_basic netlist check in checks/check_prep_014_gate_counts.py; supplied example rechecked in this update script.'})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==22 and all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-014')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
print('PREP-014 full AND/NOR derivation and shared-gate diagram linked in both languages; gate-count optimality scoped; example checked.')
