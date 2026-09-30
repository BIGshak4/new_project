"""Register the supplied tri-state component question without chat usage tracking."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
prompt='''נתונים רכיבי A ו־B בעלי טבלת האמת הבאה:

| In 1 | In 2 | Out A | Out B |
|---|---|---|---|
| 0 | 0 | 1 | Z |
| 0 | 1 | Z | Z |
| 1 | 0 | Z | Z |
| 1 | 1 | Z | 0 |

Z הינו מצב של High-impedance ואינו יכול להוות כניסה לשום רכיב (זהו אינו ערך לוגי חוקי).
במצב של פגישה בין שתי יציאות, כאשר אחת מהן במצב Z והשנייה בעלת ערך לוגי תקף, יתפוס הערך הלוגי התקף.
לדוגמא: חיבור יציאה במצב Z ליציאה במצב 1 נותן 1, כמוצג בשרטוט שבצילום.
יש ליצור בעזרת רכיבים אלו את השער XOR.'''
en_prompt='''Given two component types A and B with this truth table: for inputs 00, A outputs 1 and B outputs Z; for 01 and 10 both output Z; for 11, A outputs Z and B outputs 0. Z denotes high impedance and cannot be an input to any component. When outputs are joined and one is Z while the other drives a valid logic value, the valid value prevails. The source illustrates Z joined with 1 yielding 1. Construct an XOR gate using these components.'''
hints=[
    'Z אינו 0: הוא אומר שהיציאה אינה קובעת את ערך החוט. כדי ליצור חוט שאפשר להזין לרכיב אחר, צריך שבכל צירוף קלט לפחות יציאה אחת תקבע לו 0 או 1, בלי שיציאה אחרת תקבע את ההפך.',
    'מותר לחבר את אותו אות לשתי כניסות של רכיב. בדוק מתי B(x,x) מוציא 0, ומתי B(y,y) מוציא 0. האם יחד עם A(x,y) אפשר ליצור אות פנימי שתמיד מוגדר?',
    'בחיבור היציאות A(x,y), B(x,x), B(y,y) מתקבל n=NOT(x OR y). השתמש ב־n כדי להפריד את 00 מהמקרים 01 ו־10. כעת תכנן מי מוציא 1 בשני המקרים השונים, ומי מוציא 0 ב־00 וב־11.'
]
en_hints=[
    'Z is not zero: that output is not driving the wire. Every net feeding another component must have at least one valid driver in every input case, without an opposing driver.',
    'You may connect one signal to both inputs of a component. When do B(x,x) and B(y,y) drive zero? Can they be joined with A(x,y) to form an always-defined intermediate net?',
    'Joining A(x,y), B(x,x), B(y,y) produces n=NOT(x OR y). Use n to distinguish 00 from 01 and 10, then provide 1 drivers for the unequal cases and 0 drivers for 00 and 11.'
]
solution='''נסמן את שני הקלטים של המעגל x,y, כדי שלא לבלבל בינם לבין שמות הרכיבים A,B. רכיב A מוציא 1 רק כששתי כניסותיו 0; רכיב B מוציא 0 רק כששתי כניסותיו 1. בשאר המקרים היציאה אינה מניעה את החוט (Z). חיבור יציאות כאן הוא חיבור חשמלי לפי כללי השאלה, לא שער OR.

**שלב 1 — יוצרים אות פנימי חוקי n בשלושה רכיבים.** מחברים לאותו חוט את יציאות A(x,y), B(x,x), B(y,y).

- כאשר x=y=0: רק A מוציא 1 ושני רכיבי B במצב Z; לכן n=1.
- כאשר x=1: הרכיב B(x,x) מוציא 0, ורכיב A במצב Z; לכן n=0.
- כאשר y=1: הרכיב B(y,y) מוציא 0, ורכיב A במצב Z; לכן n=0.
- כאשר שניהם 1: שני רכיבי B מוציאים 0, כלומר מסכימים על אותו ערך.

לכן n=NOT(x OR y). זה אינו שער NOR נוסף: שלושת רכיבי A/B מממשים אותו. בכל צירוף קלט החוט n הוא 0 או 1, אף שביציאות הבודדות יכול להיות Z. רק החוט המשותף והמוגדר מחובר לכניסות בשלב הבא.

**שלב 2 — ארבעה רכיבים מחוברים לאותו חוט פלט f.**

| רכיב | הכניסות | מתי הוא מניע את הפלט? |
|---|---|---|
| A2 | x,n | מוציא 1 רק עבור x=0,y=1 |
| A3 | y,n | מוציא 1 רק עבור x=1,y=0 |
| B3 | x,y | מוציא 0 רק עבור x=y=1 |
| B4 | n,n | מוציא 0 רק עבור x=y=0 |

למה A(x,n) מתאים ל־01? הוא מוציא 1 כש־x=0 וגם n=0. העובדה ש־n=0 אומרת שלפחות אחד מבין x,y הוא 1. מאחר שכבר ידוע ש־x=0, בהכרח y=1. באותה דרך A(y,n) מזהה את 10. הרכיב B(n,n) מוציא 0 כש־n=1, וזה קורה רק ב־00.

**בדיקה מלאה של הנהגים:**

| x | y | n | A2(x,n) | A3(y,n) | B3(x,y) | B4(n,n) | f |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 1 | Z | Z | Z | 0 | 0 |
| 0 | 1 | 0 | 1 | Z | Z | Z | 1 |
| 1 | 0 | 0 | Z | 1 | Z | Z | 1 |
| 1 | 1 | 0 | Z | Z | 0 | Z | 0 |

זהו XOR. בפלט הסופי יש בדיוק נהג פעיל אחד בכל שורה; אין פלט צף ואין מאבק בין 0 ל־1. סך הכול 3 רכיבי A ו־4 רכיבי B: **7 רכיבים**, בשתי שכבות של חוטים לוגיים מוגדרים. אין צורך בשערים נוספים או בקבועים.

**יעילות והנחות:** שבעה הוא מספר הרכיבים המינימלי במודל שנבדק: מעגל קומבינטורי ללא משוב, שכל כניסה לרכיב מחוברת לקלט ראשי או לחוט פנימי המוגדר 0/1 בכל ארבעת הצירופים; מותר לחבר כמה יציאות, לפצל חוט ולהזין אותו לשתי כניסות. אסורים משיכות חיצוניות, רכיבים נוספים וקלט משלים חופשי. חיפוש ממצה של מעגלים במודל הזה מצא מינימום 7, גם כאשר קבועים 0/1 זמינים בחינם. זו הוכחה חישובית מוגבלת למודל המוצהר, ולא טענה על מעגלי משוב, מעגלים אנלוגיים או שטח טרנזיסטורים.

החיפוש מייצג כל חוט חוקי באמצעות טבלת אמת בת ארבעה ביטים. מכל קבוצת פונקציות זמינה הוא בודק את כל זוגות הקלטים לכל רכיב ואת מספר הנהגים המינימלי הדרוש כדי לכסות את שורות ה־1 ושורות ה־0 של כל פונקציה חדשה, ללא התנגשות. חיפוש בעלות עולה על קבוצות הפונקציות מוצא את XOR לראשונה בעלות 7. שיתוף חוטים נכלל במודל; חוט נוסף עם אותה פונקציה אינו מועיל כאשר הסתעפות חופשית.

הבדיקה היא של מצבים יציבים בטבלת אמת. השאלה לא מספקת השהיות, ולכן אין כאן הבטחה להיעדר מצבי מעבר צפים או התנגשויות רגעיות בזמן שינוי קלטים.'''
en_solution='''Let the external inputs be x,y. Join A(x,y), B(x,x), B(y,y) to make n. At 00, A drives 1; at any other input at least one B drives 0 and A is Z. Thus n=NOT(x OR y), always defined without conflicting drivers. Both B cells may drive the same zero at 11.

Join four more outputs for f: A(x,n), A(y,n), B(x,y), B(n,n). These drive respectively 1 at 01, 1 at 10, 0 at 11, and 0 at 00. In every input case the other three are Z. Hence f=x XOR y with exactly one active final driver. Only the resolved, fully driven n feeds component inputs, never an isolated Z output. Total: three A and four B cells, seven overall; no extra gates or constants.

Exhaustive truth-table checks verify all intermediate and final nets. An exact increasing-cost search over sets of available two-input Boolean functions establishes a seven-cell minimum for acyclic circuits whose component inputs are always-valid Boolean nets, with free fanout and allowed tied inputs. It enumerates all A/B driver masks and their minimum covers for each new function. The same minimum holds with or without free constants. No extra components, free complemented inputs, pull resistors or feedback are allowed. This is a scoped computational minimum, not a claim about transistor area or arbitrary analog/sequential circuits. Static correctness does not establish hazard-free behavior during physical input transitions.'''

record={
    'id':'PREP-015','key':'xor-from-high-impedance-components','version':1,'created_on':'2026-09-27',
    'category':'hardware','topic':'combinational_circuits',
    'topics':['hardware','logic-design','combinational_circuits','tri_state','high_impedance','xor','truth_tables'],
    'source_topic_tags':['hardware','logic-design'],
    'added_topic_tags':['combinational_circuits','tri_state','high_impedance','xor','truth_tables'],
    'source_tags':['amazon','arm','nvidia','hardware','samsung','csr','apple','marvell','intel','logic-design'],
    'reported_companies':['Amazon','Arm','NVIDIA','Samsung','CSR','Apple','Marvell','Intel','Zoran'],
    'source_company_badge':'צורן',
    'company_attribution_status':'reported_by_supplied_source_not_independently_verified',
    'company_attribution_note':'Zoran is transcribed from the Hebrew source badge צורן; CSR appears separately as a tag.',
    'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'circuit_design',
    'status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון',
    'origin':'user_supplied_screenshot','authorship':'Source transcribed; AI-assisted translations, hints, solution, diagram and verification.','reviewed_by':None,
    'sources':[{'type':'user_supplied_image','path':'sources/prep-015.png','received_on':'2026-09-27'}],
    'original_prompt':prompt,
    'component_truth_table':[
        {'in1':0,'in2':0,'A':1,'B':'Z'},{'in1':0,'in2':1,'A':'Z','B':'Z'},
        {'in1':1,'in2':0,'A':'Z','B':'Z'},{'in1':1,'in2':1,'A':'Z','B':0}],
    'translations':{
        'he':{'title':'מימוש XOR באמצעות רכיבי A/B עם יציאות High-impedance','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':solution},
        'en':{'title':'XOR using high-impedance A/B components','prompt':en_prompt,'hint':en_hints[0],'hints':en_hints,'reference_solution':en_solution}},
    'prepared_hints':[{'id':f'PREP-015-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
    'assumptions':[
        'External inputs are binary; resolved intermediate nets must be binary for all stable input cases.',
        'Multiple copies of A/B, free wires and fanout, and connecting one signal to both inputs are permitted.',
        'Compatible active drivers agree; opposite active values are prohibited; an all-Z net cannot feed another component.',
        'Combinational acyclic Boolean-net model; no pull devices, extra gates or free complementary inputs.',
        'No physical timing specification is provided; verify stable-state behavior.'],
    'optimality':{'criterion':'A/B component count in acyclic circuits with fully resolved Boolean nets',
        'result':'7 components: 3 A + 4 B',
        'proof':'Exact minimum-cover transitions and increasing-cost search over sets of 4-bit Boolean functions; minimum 7 with and without free constants. See check_prep_015.py.',
        'scope':'Static acyclic fully driven Boolean nets; not a physical area or transition-safety claim.'},
    'edge_cases':['00: n=1,f=0','01: n=0,f=1','10: n=0,f=1','11: n=0,f=0; two same-zero drivers on n',
                  'Z is neither zero nor a Boolean wildcard; never feed an unresolved Z into a cell.'],
    'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_015.py',
        'method':'All four inputs checked with explicit A/B output resolution, rejecting floating and conflicting nets. Exact minimum search settled 43 states without constants and 25 with constants, both minimum 7. Diagram visually inspected.',
        'scope':'Python static discrete model and scoped combinational enumeration; no HDL simulation, synthesis or analog timing analysis.'},
    'solution_diagram_path':'diagrams/prep-015-tristate-xor.png',
    'solution_diagram_generator':'solutions/draw_prep_015_tristate_xor.py',
    'media_assets':[{'type':'source_image','path':'sources/prep-015.png'},
        {'type':'solution_schematic','path':'diagrams/prep-015-tristate-xor.png','display_section':'הצעה לפתרון'}],
    'interview_answer':'אבנה תחילה n=NOT(x OR y) מחיבור A(x,y), B(x,x), B(y,y). אחר כך אחבר A(x,n), A(y,n), B(x,y), B(n,n) לפלט אחד. הם מכסים בהתאמה את 01,10,11,00 עם הערכים 1,1,0,0. כל חוט פנימי חוקי וכל מצב מכוסה ללא התנגשות; סך הכול שבעה רכיבים.',
    'common_mistakes':['Treating Z as 0','Feeding an individual floating output to a component','Joining A(x,y) and B(x,y) alone leaves 01/10 floating',
        'Allowing opposing active drivers','Using an ordinary OR gate instead of the specified output joining','Using NOT/NOR for free instead of building them from A/B'],
    'related_question_ids':['VHW-001'],
    'related_question_links':[{'id':'VHW-001','path':'../verify_example_questions/hardware/digital_logic_and_clocking/vhw-001-mux-functions.md','relationship':'Another XOR construction task, with different primitives and constraints; not a duplicate.'}],
    'markdown_path':'questions/prep-015-xor-high-impedance.md'
}
p=root/'questions.json'; s=p.read_text(encoding='utf-8'); data=json.loads(s)
assert not any(q['id']=='PREP-015' for q in data['questions']), 'Already registered'
pos=s.rfind('\n  ]')
assert pos>0
entry='    '+json.dumps(record,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=s[:pos]+',\n'+entry+s[pos:]
s=s.replace('"question_count": 14','"question_count": 15',1)
check=json.loads(s); assert len(check['questions'])==check['question_count']==15
p.write_text(s,encoding='utf-8')
md='# PREP-015 — מימוש XOR באמצעות רכיבי A/B עם High-impedance\n\n## השאלה המקורית\n\n'+prompt
md+='\n\n![צילום השאלה, טבלת האמת והשרטוט](../sources/prep-015.png)\n\n## קטגוריות וחברות\n\n'
md+='תגיות מקור: hardware, logic-design. סיווג נוסף: מעגלים קומבינטוריים, tri-state, עכבה גבוהה, XOR וטבלאות אמת.\n\n'
md+='חברות לפי תגיות המקור: Amazon, Arm, NVIDIA, Samsung, CSR, Apple, Marvell, Intel. התווית הראשית היא צורן (Zoran). השיוך מהצילום בלבד ולא אומת עצמאית.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
md+='\n\n## הצעה לפתרון\n\n'+solution
md+='\n\n![מעגל XOR בשבעה רכיבי A/B](../diagrams/prep-015-tristate-xor.png)\n\n'
md+='[בדיקת נכונות וחיפוש מינימום](../checks/check_prep_015.py) · [מחולל השרטוט](../solutions/draw_prep_015_tristate_xor.py).\n\n'
md+='## תשובה קצרה לראיון\n\n'+record['interview_answer']+'\n\n## English\n\n'+en_prompt+'\n\n'
md+='\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(en_hints,1))+'\n\n'+en_solution
md+='\n\nשאלה קשורה: VHW-001 — מימוש XOR באמצעות MUX; רכיבים ואילוצים שונים.\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/record['markdown_path']).write_text(md,encoding='utf-8')
readme=root/'README.md'
with readme.open('a',encoding='utf-8') as f:
    f.write('\n- [PREP-015 — מימוש XOR באמצעות רכיבי A/B עם High-impedance](questions/prep-015-xor-high-impedance.md) — נשמרו צילום המקור והשרטוט, טבלת האמת, חברות, קטגוריות, שלושה רמזים והצעה לפתרון עם שרטוט; נבדקו כל ארבעת הקלטים ומינימום רכיבים במודל קומבינטורי מוגדר.\n')
assert all((root/a['path']).exists() for a in record['media_assets'])
assert solution in (root/record['markdown_path']).read_text(encoding='utf-8')
print('PREP-015 saved: source image, full prompt/table, tags, companies, hints, solution, schematic and verification. Total: 15.')
