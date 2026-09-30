"""Persist PREP-016 with the source ambiguity kept separate from the solution."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prompt='''נתון רכיב בקרת פסיקות.
In0–In3 הינם קווי פסיקות של 1 ביט כל אחד.
Y מבצע את פונקציית OR על כל הכניסות, כלומר מאותת שהתבצעה פסיקה.
Z1 ו־Z0 הינם קווי Priority, כלומר מראים מה הפסיקה הכי גבוהה ביותר שהתקבלה.
בנה בקר פסיקות בעל 16 כניסות ע״י שימוש במינימום רכיבי בקר פסיקות של 4 כניסות ובעזרת רכיבים לוגיים אחרים (מסכמים, מחסרים, MUX, FF, וכמובן שערים לוגיים).
בתרשים: ארבע כניסות In0, In1, In2, In3 לרכיב Interrupt Controller, ושלוש יציאות Y, Z0, Z1.'''
ep='''A four-input interrupt controller accepts one-bit interrupt lines In0 through In3. Y is the OR of all inputs, indicating an interrupt request. Priority outputs Z1 and Z0 identify the highest-priority asserted input. Build a sixteen-input interrupt controller using the minimum number of four-input controller components and other logic components (adders, subtractors, multiplexers, flip-flops and logic gates). The supplied diagram shows In0..In3 and outputs Y,Z0,Z1.'''
hints=[
    'נסה לחלק את 16 הכניסות לקבוצות. בכל קבוצה צריך לדעת שני דברים: האם יש בכלל פסיקה פעילה, ומה מיקומה של הפסיקה בעדיפות הגבוהה ביותר בתוך הקבוצה.',
    'אחרי שכל קבוצה נותנת אות Y משלה, אותות אלה יכולים לעזור לבחור את הקבוצה המנצחת. לא מספיק לקודד את הקבוצה: צריך להעביר גם את קוד הפסיקה המקומי של אותה קבוצה בלבד.',
    'מספר בין 0 ל־15 דורש ארבעה ביטים: שניים למספר הקבוצה ושניים למיקום בתוכה. בחר ב־MUX את הקוד המקומי לפי הקבוצה המנצחת. את בחירת הקבוצה אפשר לבצע בבקר נוסף או בשערים — וזה משנה את ספירת הבקרים.'
]
eh=[
    'Split the sixteen requests into groups. Each group must report both whether any request is active and the local index of its highest-priority request.',
    'Use the groups\' Y outputs to choose the winning group. Also route only that group\'s local priority code to the output.',
    'A 0..15 index has four bits: two for the group and two for the position within it. Use a mux to select the local code. Group priority can use another controller or logic gates, changing the controller count.'
]
he='''**פירוש הרכיב:** Y הוא אות תקפות, ו־Z הוא מספר הכניסה הפעילה בעלת העדיפות הגבוהה ביותר, לא וקטור one-hot. נניח ש־In3 בעדיפות הגבוהה ביותר ברכיב, ובהרחבה In15 היא הגבוהה ביותר. נסמן Z1 כביט המשמעותי ו־Z0 כביט הנמוך. סדר העדיפויות ומשמעות שמות הביטים אינם מוגדרים במפורש בצילום, ולכן זו הנחת עבודה. במקרה שאין פסיקות נדרוש Y=0 ונבחר קוד פלט 0000; המקור אינו מחייב קוד מסוים במצב זה. מדובר במעגל קומבינטורי, ללא צורך ב־FF או שעון.

**הבנייה ההיררכית:** נחלק את הכניסות לארבע קבוצות, ונחבר כל קבוצה לבקר בן ארבע כניסות:

| קבוצה g | הכניסות המקוריות | פלט הבקר |
|---|---|---|
| 0 | In0..In3 | V0, L0[1:0] |
| 1 | In4..In7 | V1, L1[1:0] |
| 2 | In8..In11 | V2, L2[1:0] |
| 3 | In12..In15 | V3, L3[1:0] |

Vg הוא פלט Y של הבקר המקומי: האם יש פסיקה בקבוצה g. Lg הוא הקוד המקומי 0..3. בתוך כל קבוצה מחברים את In(4g+j) לכניסה המקומית j, כדי לשמור על סדר העדיפויות.

כעת בוחרים את הקבוצה הגבוהה ביותר שעבורה Vg=1. לדוגמה, אם קבוצות 1 ו־3 פעילות, קבוצה 3 זוכה ללא קשר למיקום הפסיקה בתוך קבוצה 1: כל מספר בקבוצה 3 גבוה מכל מספר בקבוצה 1.

**בחירת הקבוצה באמצעות שערים — ארבעה בקרים מקומיים:** נסמן את קוד הקבוצה G1,G0. אז:

```text
Y  = V3 OR V2 OR V1 OR V0
G1 = V3 OR V2
G0 = V3 OR (V1 AND NOT(V2))
```

הסבר: אם V3=1 בוחרים 11; אחרת אם V2=1 בוחרים 10; אחרת אם V1=1 בוחרים 01; אחרת בוחרים 00. G1 דולק כאשר נבחרת אחת משתי הקבוצות העליונות. G0 דולק בקבוצה 3, או בקבוצה 1 בתנאי שקבוצה 2 אינה פעילה; אם קבוצה 3 פעילה האיבר V3 כבר מכריע לטובת 11.

נחבר MUX 4:1 ברוחב שני ביטים. כניסות הנתונים שלו הן L0,L1,L2,L3, וקווי הבחירה שלו הם G1,G0. פלטו L הוא הקוד המקומי של הקבוצה שנבחרה. אפשר לממשו גם כשני MUX של ביט אחד, בעלי אותם קווי בחירה.

```text
L = MUX(G, L0, L1, L2, L3)
אם Y=1: P[3:0] = {G1,G0,L1,L0}
אם Y=0: P[3:0] = 0000
```

כאן L1,L0 בשורת השרשור הם שני הביטים של מוצא ה־MUX, ולא הקודים המקומיים של קבוצות 1 ו־0. בכתיב חד־משמעי: P={G[1:0], L[1:0]}. זהו שרשור חוטים. אין צורך במחבר: האינדקס הוא 4g+l, והכפלה ב־4 מזיזה את g בשני ביטים למעלה; l ממלא את שני הביטים הנמוכים ללא נשא. אם רוצים קוד אפס כש־Y=0, אפשר לחסום את ארבעת ביטי P עם Y. אסור לעשות OR פשוט בין הקודים המקומיים במקום בחירה ב־MUX.

**דוגמה:** נניח In2, In6 ו־In13 פעילים. אז קבוצה 0 מדווחת קוד מקומי 2, קבוצה 1 קוד 2, קבוצה 2 אינה פעילה, וקבוצה 3 קוד 1. הקבוצה המנצחת היא 3, כלומר G=11; ה־MUX מעביר את הקוד המקומי 01 שלה; הפלט 1101 הוא 13. Y=1. עבור In0 בלבד נקבל Y=1,P=0000; כאשר כל הכניסות אפס נקבל Y=0,P=0000. לכן Y חיוני להבחנה בין שני המצבים.

**החלופה המקובלת עם חמישה בקרים:** במקום משוואות G ו־Y, מחברים V0..V3 לארבע כניסותיו של בקר חמישי, לפי אותו סדר. ה־Y שלו הוא Y הכללי, וה־Z שלו הוא G. שאר המעגל זהה: MUX בוחר את הקוד המקומי, ואז משרשרים. זה פתרון מודולרי תקין ופשוט, אך אינו מינימום מספר הבקרים כאשר מותר להחליף את הבקר החמישי בשערים.

**דיוק בנוגע למינימום — יש עמימות בשאלה:**

- בארכיטקטורה של בקר אחד לכל קבוצת ארבע כניסות משתמשים בארבעה בקרים ובשערים לבחירת הקבוצה. זה המינימום תחת ההגבלה שכל 16 הכניסות הגולמיות יכוסו ישירות בבקרים המקומיים: לכל בקר רק ארבע כניסות. זו אינה הגבלה שמופיעה במפורש במקור.
- אם דורשים שכל שלבי הכרעת העדיפות יתבצעו רק באמצעות בקרים במבנה עץ, הפתרון הוא חמישה: ארבעה מקומיים ואחד מעליהם. לעץ בעל לכל היותר ארבעה ילדים לכל צומת פנימי, B צמתים פנימיים מכסים לכל היותר 1+3B עלים. עבור 16 עלים נדרש B>=5. הטיעון חל על ארכיטקטורת עץ זו בלבד.
- אם שערים אחרים באמת מותרים ללא הגבלה, וממזערים רק את מספר רכיבי הבקר הנתונים, אפשר לבנות את כל המקודד בשערים בלבד: לכן המינימום במודל זה הוא **אפס בקרים**. אם מפרשים ״שימוש ברכיבי בקר״ כחובה להשתמש בלפחות אחד, אפשר להשתמש באחד ולממש את השאר בשערים. אין לטעון ש־4 או 5 הם מינימום מוחלט מהנוסח הנתון.

מימוש מפורש ללא בקרים: נגדיר לכל ביט Wi=Ini AND NOT(OR של כל הכניסות הגבוהות ממנו). W15=In15. לכל היותר Wi אחד הוא 1. Y הוא OR של כל הקלטים. לכל ביט קוד k, הפלט Pk הוא OR של כל Wi שעבורם ביט k במספר i הוא 1. למשל P3=OR(W8..W15), P0=OR(W1,W3,W5,W7,W9,W11,W13,W15). זה מממש את אותה פונקציה עם שערים בלבד ומוכיח שאפס בקרים אפשרי כאשר שערים אינם מוגבלים. לא נטען שמימוש זה ממזער שטח או השהיה.

בראיון כדאי להציג את החלוקה לקבוצות וה־MUX, ולהסביר במפורש מה נספר ומה מותר להחליף בשערים. הפתרון של ארבעה בקרים הוא הצעה הנדסית ישירה לשימוש בבקרים המקומיים; חמשת הבקרים הם חלופה היררכית, והמינימום המילולי תלוי בפרשנות האילוץ.

**בדיקה:** נבדקו כל 65,536 וקטורי הקלט מול האינדקס הפעיל הגבוה ביותר, בשלוש חלופות: ארבעה בקרים עם משוואות הקבוצה, חמישה בקרים, ושערים בלבד. בשתי החלופות ההיררכיות נבדקו גם כל ארבע אפשרויות הקוד המוחזר מבקר לא פעיל. רק קוד מקבוצה פעילה נבחר כאשר Y=1, ובמצב ללא בקשות הפלט מאופס במפורש. בדיקת Python עברה; לא בוצעה סימולציית HDL או סינתזה.'''
en='''Assume the highest numbered input has highest priority and Z1 is the MSB of the two-bit local index. The source leaves these conventions and the invalid index unspecified. Return a four-bit index P and valid Y; choose P=0 when Y=0. No sequential behavior or flip-flops are needed.

Split requests into four consecutive groups, each using one four-input controller. Group g receives In(4g)..In(4g+3), with preserved local ordering, and produces valid Vg and local index Lg. Choose the highest active group using G1=V3 OR V2, G0=V3 OR (V1 AND NOT V2), Y=V3 OR V2 OR V1 OR V0. A two-bit-wide 4:1 mux selected by G routes Lg to L. When valid, concatenate P={G,L}; otherwise force P=0. This encodes 4g+l without an adder. Example requests 2,6,13 select group 3 and local position 1, producing P=1101 (13).

An alternative uses a fifth controller on V0..V3 to produce G and Y; the same mux and concatenation follow. This is a valid modular hierarchy but not a minimum controller count with unrestricted auxiliary gates.

The minimum is ambiguous in the source. Four controllers are minimal only under the additional architecture constraint that every raw request be covered directly by a local four-input controller. Five are minimal in a tree where all priority decisions use these controller nodes: B nodes with fan-in at most four cover at most 1+3B leaves, so 16 leaves need B>=5. With unrestricted ordinary gates and an objective counting only the given controller components, zero controllers suffice. Explicitly form winner Wi=Ini AND NOT(any higher request), then each binary index bit is the OR of winners whose index contains that bit; valid is the OR of requests. If at least one controller must be used, one plus gates is possible. No universal four-/five-controller or minimum-area claim is justified by the source wording.

All 65,536 inputs were checked for the four-controller, five-controller and gates-only constructions against a highest-set-bit-index specification. All four possible invalid local output codes were covered; invalid final index is explicitly forced to zero. Python verification passed; no HDL simulation or synthesis was performed.'''
record={
'id':'PREP-016','key':'sixteen-input-interrupt-controller','version':1,'created_on':'2026-09-27',
'category':'hardware','topic':'combinational_circuits',
'topics':['hardware','logic-design','state-machines','combinational_circuits','priority_encoder','interrupt_controller','hierarchical_design','multiplexer'],
'source_topic_tags':['hardware','logic-design','state-machines'],
'added_topic_tags':['combinational_circuits','priority_encoder','interrupt_controller','hierarchical_design','multiplexer'],
'source_tags':['nvidia','hardware','qualcomm','samsung','apple','marvell','intel','logic-design','state-machines','amazon','maxlinear'],
'reported_companies':['NVIDIA','Qualcomm','Samsung','Apple','Marvell','Intel','Amazon','MaxLinear'],
'source_company_badge':'מארוול','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'circuit_design','status':'in_review',
'solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
'authorship':'Source transcribed; AI-assisted translations, hints, solution and exhaustive equation-model checks.','reviewed_by':None,
'sources':[{'type':'user_supplied_image','path':'sources/prep-016.png','received_on':'2026-09-27'}],
'original_prompt':prompt,
'translations':{'he':{'title':'בניית בקר פסיקות של 16 כניסות מבקרים של 4 כניסות','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},
                'en':{'title':'Sixteen-input interrupt controller from four-input controllers','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
'prepared_hints':[{'id':f'PREP-016-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
'assumptions':['Highest input index has highest priority; source does not specify the direction.',
               'Z1 is the local MSB and Z0 the LSB; preserve local/global input ordering.',
               'Output is a binary index plus valid, not a one-hot vector.',
               'No requests: Y=0; explicitly choose index=0. Local invalid codes may be arbitrary.',
               'Combinational, no clock/FF requirement.',
               'Auxiliary gates are permitted, so minimum dedicated-controller count needs a stated architecture constraint.'],
'optimality':{'criterion':'Number of dedicated four-input controllers under explicitly separated cost models',
              'result':'4 in the fixed four-local-group architecture; 5 in a pure controller priority tree; 0 with unrestricted gates (or 1 if use of at least one is mandatory).',
              'proof':'Four local groups cover 16 requests; four-ary tree leaf bound 1+3B yields B>=5; explicit gates-only winner/index construction establishes zero under unrestricted gates.',
              'scope':'No claim of technology-specific minimum area, delay, or an unconditional four/five-controller minimum.'},
'editorial_notes':['Source includes state-machines tag, but the described function is combinational.',
                   'Clarify priority order and the meaning of minimum; auxiliary gates can replace entire controller functions.'],
'edge_cases':['No requests: valid=0,index=0','Only In0: valid=1,index=0','All requests: index=15',
              'Several active groups: highest group wins','Several requests within one group: highest local index wins',
              'Codes from inactive groups must not influence a valid output'],
'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_016.py',
                'method':'All 65,536 inputs for four-/five-controller and gates-only models; all four invalid local codes for each hierarchical variant.',
                'scope':'Python Boolean models; no HDL simulation, synthesis or physical timing analysis.'},
'solution_model_path':'solutions/prep_016_interrupt_controller.py',
'media_assets':[{'type':'source_image','path':'sources/prep-016.png','description':'Original question text, controller block diagram and company/topic tags.'}],
'interview_answer':'אחלק לארבע קבוצות ואשתמש בבקר מקומי לכל אחת. אבחר את הקבוצה הפעילה הגבוהה לפי אותות Y, ואשתמש בקוד הקבוצה לבחירת הקוד המקומי ב־MUX. אשרשר את שני קודי שני הביטים לקבלת אינדקס בן ארבעה ביטים. בחירת הקבוצה דורשת בקר חמישי או שערים. מאחר ששערים אחרים מותרים, אין מינימום מוחלט של ארבעה או חמישה בקרים ללא אילוץ נוסף על הארכיטקטורה.',
'common_mistakes':['ORing local indices instead of muxing the winning group','Ignoring valid; confusing no request with request zero',
                   'Claiming five controllers are minimal despite allowing replacement with gates','Assuming undocumented priority order',
                   'Adding registers unnecessarily','Selecting highest local code across groups instead of highest group first',
                   'Counting concatenation as an adder'],
'related_question_ids':['HW-005','VHW-003','PREP-014'],
'related_question_links':[
    {'id':'HW-005','path':'../example_question/hardware/combinational_circuits/hw-005-interrupt-priority.md','relationship':'Four-input building block; new task scales to sixteen inputs.'},
    {'id':'VHW-003','path':'../verify_example_questions/hardware/digital_logic_and_clocking/vhw-003-priority-encoder.md','relationship':'Related four-input encoder and area/depth discussion.'},
    {'id':'PREP-014','path':'questions/prep-014-isolate-highest-one.md','relationship':'Related priority selection; returns one-hot mask rather than encoded index.'}],
'markdown_path':'questions/prep-016-sixteen-input-interrupt-controller.md'
}
p=root/'questions.json'; s=p.read_text(encoding='utf-8'); data=json.loads(s)
assert data['question_count']==15 and not any(q['id']=='PREP-016' for q in data['questions'])
pos=s.rfind('\n  ]'); assert pos>0
entry='    '+json.dumps(record,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 15','"question_count": 16',1)
data=json.loads(s); assert len(data['questions'])==data['question_count']==16
p.write_text(s,encoding='utf-8')
md='# PREP-016 — בניית בקר פסיקות של 16 כניסות\n\n## השאלה המקורית\n\n'+prompt
md+='\n\n![צילום השאלה ותרשים הרכיב](../sources/prep-016.png)\n\n## קטגוריות וחברות\n\n'
md+='תגיות מקור: hardware, logic-design, state-machines. סיווג נוסף: מעגלים קומבינטוריים, מקודדי עדיפות, בקרי פסיקות, תכנון היררכי ו־MUX. למרות תגית המקור state-machines, התפקוד המתואר אינו מחייב מכונת מצבים.\n\n'
md+='חברות לפי המקור: NVIDIA, Qualcomm, Samsung, Apple, Marvell, Intel, Amazon, MaxLinear. התווית הראשית: מארוול. שיוך מהצילום בלבד, ללא אימות עצמאי.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
md+='\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[מודל Python](../solutions/prep_016_interrupt_controller.py) · [בדיקה ממצה](../checks/check_prep_016.py).\n\n'
md+='## תשובה קצרה לראיון\n\n'+record['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'
md+='\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\n## שאלות קשורות\n\nHW-005 ו־VHW-003 עוסקות במקודד ארבע כניסות; PREP-014 עוסקת בבחירת הביט המשמעותי אך מחזירה one-hot. זו שאלת הרחבה ולא כפילות זהה.\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/record['markdown_path']).write_text(md,encoding='utf-8')
with (root/'README.md').open('a',encoding='utf-8') as f:
    f.write('\n- [PREP-016 — בניית בקר פסיקות של 16 כניסות](questions/prep-016-sixteen-input-interrupt-controller.md) — נשמרו צילום השאלה והתרשים, קטגוריות, חברות, שלושה רמזים ופתרון; נבדקו כל 65,536 הקלטים ותועדו הנחות העדיפות והעמימות בדרישת מינימום הבקרים.\n')
assert all((root/a['path']).exists() for a in record['media_assets'])
assert he in (root/record['markdown_path']).read_text(encoding='utf-8')
print('PREP-016 saved and linked; 16 questions; source and full bilingual solution present.')
