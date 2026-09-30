"""Register the maximum-of-two circuit question and its checked solution."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-a20901d6-18c0-43cd-9caf-d4c0d362c68a.png',root/'sources/prep-018.png')
prompt='תכנן מערכת המקבלת כקלט שני מספרים, ומוציאה כפלט את הגדול ביניהם. ניתן להשתמש ברכיבי זיכרון ורכיבים אריתמטיים (מסכמים, מחסרים) וכמובן בשערים לוגיים.'
ep='Design a system that accepts two numbers and outputs the larger one. Memory elements, arithmetic components (adders, subtractors), and logic gates may be used.'
hints=[
 'אפשר להפריד את הבעיה לשניים: קודם להחליט איזה מספר גדול יותר, ואחר כך להעביר את המספר הזה לפלט. אין צורך לחשב מחדש את הערך שלו.',
 'מה אפשר ללמוד מההפרש A−B? חשוב כיצד מייצרים ממנו ביט בחירה, ואיזה מעגל יכול לבחור בין שני קלטים לפי ביט אחד.',
 'אפשר להרחיב את המספרים בביט אחד לפני החיסור, כדי שההפרש לא יגלוש. ביט הסימן של ההפרש יבחר בין A ל־B ב־MUX. חשוב להבחין בין הרחבת אפס למספרים לא מסומנים לבין הרחבת סימן למספרים במשלים ל־2.'
]
eh=[
 'Separate the task into deciding which number is larger and routing that original number to the output.',
 'What does A−B tell you? Consider a comparison flag and a circuit that selects one of two inputs using that flag.',
 'Extend the operands by one bit before subtracting so the difference cannot overflow. Use its sign as a mux select. Unsigned inputs need zero extension; two\'s-complement signed inputs need sign extension.'
]
he='''**הרעיון:** מחליטים מי גדול באמצעות חיסור, ואז בוחרים את אחד המספרים המקוריים ומעבירים אותו לפלט. הפלט הוא המספר עצמו, ולא רק ביט שאומר מי גדול. אין צורך בזיכרון או בשעון; די במעגל קומבינטורי.

המקור אינו מגדיר רוחב או סוג מספרים. נתחיל משני מספרים שלמים לא מסומנים A,B ברוחב N ביטים. רוצים פלט M=max(A,B) באותו רוחב. במקרה שוויון נבחר A; שתי הבחירות נותנות אותו ערך.

**1. מרחיבים בביט אפס:** Aext={0,A}, Bext={0,B}. כעת כל אחד ברוחב N+1. זה אינו משנה את ערך המספרים.

**2. מחסרים ברוחב N+1:** D=Aext−Bext. אם A קטן מ־B, ההפרש שלילי; אם A גדול או שווה ל־B, ההפרש אינו שלילי. הטווח של ההפרש הוא מ־−(2^N−1) ועד 2^N−1, ולכן כולו ניתן לייצוג במשלים ל־2 ב־N+1 ביטים. אין כאן גלישה חתומה. הביט העליון D[N] הוא 1 בדיוק כאשר A<B.

**3. בוחרים את הפלט:** נגדיר S=D[N]. נחבר ל־MUX 2:1 ברוחב N ביטים את A לכניסה 0 ואת B לכניסה 1, ואת S לכניסת הבחירה. אם S=0, המוצא הוא A; אם S=1, המוצא הוא B. ה־MUX מעביר את המספר המקורי, לא את ההפרש.

```text
A,B -> הרחבה ל־N+1 -> מחסר -> S = D[N]
A   -> כניסת נתונים 0 של MUX
B   -> כניסת נתונים 1 של MUX
S   -> כניסת הבחירה
MUX -> M = max(A,B)
```

השאלה מתירה שערים לוגיים ולכן אין צורך להניח MUX כרכיב נוסף שניתן בחינם: עבור כל ביט i מממשים Mi=(Ai AND NOT S) OR (Bi AND S). NOT S משותף לכל הביטים. אם S=0, הענף של A פתוח ושל B חסום; אם S=1, להפך.

**דוגמאות:** ב־N=4, A=9,B=5: ההפרש בחמישה ביטים הוא 00100 (4), ולכן S=0 ונבחר A=1001. אם A=5,B=9: ההפרש הוא 11100, כלומר −4 במשלים ל־2, ולכן S=1 ונבחר B=1001. אם A=B ההפרש אפס ו־S=0; הפלט A הוא גם B.

**למה לא להסתכל פשוט על הביט העליון של חיסור ב־N ביטים?** במספרים לא מסומנים זו אינה בדיקת A<B. לדוגמה A=15,B=1 ברוחב 4: התוצאה 1110 היא 14. הביט העליון הוא 1, אבל A דווקא גדול מ־B! אחרי הרחבה התוצאה היא 01110, והסימן הנכון 0. לחלופין, מחסר ברוחב N עם דגל borrow תקין יכול לספק את ביט הבחירה ישירות. אם מממשים חיסור כמחבר A+NOT(B)+1 ברוחב N, carry-out=1 פירושו שאין borrow, ולכן S=NOT(carry-out). יש להגדיר את מוסכמת הדגל, ולא לבלבל carry עם סימן.

**אם המספרים מסומנים במשלים ל־2:** מרחיבים בסימן במקום באפס: Aext={A[N−1],A}, Bext={B[N−1],B}. שוב מחסרים ב־N+1 ביטים ומשתמשים ב־D[N]. ההרחבה משמרת את הערכים השליליים וגם מאפשרת לייצג כל הפרש בין שני מספרים ברוחב N. אין להסתמך על סימן הפרש ברוחב N ללא טיפול בגלישה: למשל 7−(−8)=15 אינו נכנס בארבעה ביטים חתומים. נוסחה חלופית להשוואה חתומה עם מחסר N ביטים היא sign(D) XOR overflow, אך הרחבה מפורשת ברורה יותר להסבר.

**יעילות:** מערכת של מחסר/משווה ומבחר ברוחב N היא בנייה ישירה. אפשר לשתף את אות הבחירה בכל הביטים, ואין צורך ב־FF. במימוש ripple מספר השערים גדל כ־O(N) והעומק יכול להיות O(N); משווה או חישוב carry/borrow מאוזן יכולים להשיג O(log N) עומק בשערים בעלי fan-in מוגבל. ייתכן שאפשר לוותר על יציאות ההפרש הנמוכות ולהפיק רק דגל השוואה. השאלה אינה מגדירה ספריית תאים או יעד שטח/תזמון, ולכן אין טענה שמחסר N+1 הוא מינימום שערים מוחלט. ההרחבה נבחרה להבטחת נכונות ולהסבר פשוט.

**בדיקה:** נבדקו באופן ממצה כל זוגות הקלטים ברוחבים 1 עד 8, גם בפורמט לא מסומן וגם במשלים ל־2: 174,760 זוגות. בכל זוג נבדקו ביט הבחירה, המקסימום, והפרש מתמטי מדויק לאחר פענוח N+1 ביטים. נכללו שוויון, קצוות הטווח ודוגמאות הממחישות טעות עקב קיצוץ ההפרש. מודל Python עבר; לא בוצעו סימולציית HDL, סינתזה או בדיקת תזמון פיזי.'''
en='''Assume two unsigned N-bit integers A,B; the source leaves width and signedness unspecified. Zero-extend both to N+1 bits and subtract D={0,A}−{0,B}. The exact mathematical difference lies in [−(2^N−1),2^N−1], which fits signed N+1-bit two\'s complement. Thus S=D[N] is 1 exactly when A<B. Route A to a width-N mux data input 0, B to input 1, and S to select. The output is max(A,B); ties choose A. No memory or clock is required.

The mux can be made using allowed gates: Mi=(Ai AND NOT S) OR (Bi AND S), sharing NOT S. Do not route the difference as the result. Do not use the MSB of a truncated N-bit unsigned subtraction as a comparison flag: 15−1=1110 at width 4 has MSB 1 although A>B. An N-bit borrow flag can instead select B; with A+NOT(B)+1, carry-out=1 means no borrow, so S=NOT(carry-out).

For signed two\'s-complement inputs, sign-extend instead of zero-extending, subtract at N+1 bits, and again select using the difference sign. This avoids signed subtraction overflow. With only an N-bit signed subtractor, signed less-than is sign(D) XOR overflow.

This is a direct combinational compare-and-select design, not a universal minimum-cell claim. A ripple implementation has O(N) area and potentially O(N) depth; a balanced comparator/borrow computation can reduce depth to O(log N). Only the comparison flag is needed, so unused difference outputs can be omitted by an appropriate implementation. Exhaustive exact-bit-vector tests passed 174,760 pairs over widths 1..8, both unsigned and signed, checking comparison, output and the extended mathematical difference. No HDL simulation or synthesis is claimed.'''
q={
'id':'PREP-018','key':'maximum-of-two-numbers-circuit','version':1,'created_on':'2026-09-27',
'category':'hardware','topic':'combinational_circuits',
'topics':['hardware','logic-design','asic','combinational_circuits','comparators','binary_arithmetic','multiplexer','signed_unsigned','overflow'],
'source_topic_tags':['hardware','logic-design','asic'],
'added_topic_tags':['combinational_circuits','comparators','binary_arithmetic','multiplexer','signed_unsigned','overflow'],
'source_tags':['hardware','ibm','apple','broadcom','intel','logic-design','asic'],
'reported_companies':['IBM','Apple','Broadcom','Intel'],'source_company_badge':'אינטל',
'company_attribution_status':'reported_by_supplied_source_not_independently_verified',
'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'circuit_design','status':'in_review',
'solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
'authorship':'Source transcribed; AI-assisted translations, hints, solution and bit-vector verification.','reviewed_by':None,
'sources':[{'type':'user_supplied_image','path':'sources/prep-018.png','received_on':'2026-09-27'}],
'original_prompt':prompt,
'translations':{'he':{'title':'מעגל המחזיר את הגדול מבין שני מספרים','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},
                'en':{'title':'Circuit returning the maximum of two numbers','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
'prepared_hints':[{'id':f'PREP-018-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
'assumptions':['Two equal-width N-bit integers, N>=1; width and numeric format are unspecified in the source.',
               'Unsigned is the primary explanation; signed two\'s-complement alternative is included.',
               'Combinational output is sufficient; permission to use memory does not require it.',
               'Output is the larger original number; equality selects A.',
               'MUX behavior can be implemented from permitted gates.'],
'optimality':{'criterion':'Simple correct combinational compare-and-select construction',
              'result':'Extended subtractor for comparison plus N-bit selector; no state.',
              'scope':'No exact cell/area/depth minimum without a gate library and objective. Ripple and balanced comparison tradeoffs documented.'},
'edge_cases':['A=B','A=0 or B=0 in unsigned mode','Unsigned maximum versus a small operand',
              'Both signed negative','Opposite signed signs','Minimum signed value versus maximum signed value',
              'Truncated subtractor sign is not generally a valid comparison flag'],
'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_018.py',
                'method':'174,760 pairs: exhaustive widths 1..8, signed/unsigned; exact extended difference, comparison flag and result checked.',
                'scope':'Python fixed-width bit-vector arithmetic; no HDL simulation, synthesis or physical timing.'},
'solution_model_path':'solutions/prep_018_maximum_two.py',
'media_assets':[{'type':'source_image','path':'sources/prep-018.png'}],
'interview_answer':'ארחיב את שני הקלטים בביט אחד ואחשב A−B. ביט הסימן של ההפרש יבחר ב־MUX את B אם ההפרש שלילי ואת A אחרת. ללא סימן מרחיבים באפס, ובמשלים ל־2 מרחיבים בסימן. ההרחבה מונעת גלישה; אין צורך בזיכרון.',
'common_mistakes':['Using the sign of a truncated unsigned difference','Ignoring signed overflow','Zero-extending negative signed inputs',
                   'Selecting the smaller input by reversing mux data wiring','Returning the comparison flag instead of the number','Adding state without a requirement'],
'related_question_ids':['PREP-005'],
'related_question_links':[{'id':'PREP-005','path':'questions/prep-005-sorting-networks.md','relationship':'Related max/min two-input building block; PREP-005 assumes it exists, while this task implements maximum selection.'}],
'markdown_path':'questions/prep-018-maximum-two-numbers.md'
}
p=root/'questions.json'; s=p.read_text(encoding='utf-8'); data=json.loads(s)
assert data['question_count']==17 and not any(a['id']==q['id'] for a in data['questions'])
pos=s.rfind('\n  ]'); assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 17','"question_count": 18',1)
data=json.loads(s); assert len(data['questions'])==data['question_count']==18
p.write_text(s,encoding='utf-8')
md='# PREP-018 — מעגל המחזיר את הגדול מבין שני מספרים\n\n## השאלה המקורית\n\n'+prompt
md+='\n\n![צילום השאלה והתגיות](../sources/prep-018.png)\n\n## קטגוריות וחברות\n\n'
md+='תגיות מקור: hardware, logic-design, asic. סיווג נוסף: מעגלים קומבינטוריים, משווים, חיסור בינארי, MUX, מספרים מסומנים ולא מסומנים וגלישה. חברות לפי המקור: IBM, Apple, Broadcom, Intel. התווית הראשית היא אינטל. השיוך מהצילום בלבד, ללא אימות עצמאי.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
md+='\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[מודל Python](../solutions/prep_018_maximum_two.py) · [בדיקה ממצה](../checks/check_prep_018.py).\n\n'
md+='## תשובה קצרה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'
md+='\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\nשאלה קשורה: [PREP-005 — רשתות מיון](prep-005-sorting-networks.md); שם רכיב max/min נתון מראש, וכאן מממשים את בחירת המקסימום.\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
with (root/'README.md').open('a',encoding='utf-8') as f:
    f.write('\n- [PREP-018 — מעגל המחזיר את הגדול מבין שני מספרים](questions/prep-018-maximum-two-numbers.md) — נשמרו המקור, תגיות, חברות, שלושה רמזים והצעה לפתרון; תועדו רוחב, סימן וגלישה ונבדקו כל זוגות הקלטים ברוחבים 1–8.\n')
assert (root/'sources/prep-018.png').exists()
assert he in (root/q['markdown_path']).read_text(encoding='utf-8')
print('PREP-018 saved: full question, source image, categories/companies, three hints, bilingual solution and checked model. Total: 18.')
