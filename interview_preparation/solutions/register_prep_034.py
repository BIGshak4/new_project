"""Register FA, 32-bit ripple and conditional recursive carry-select analysis."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prompt='''1. תכנן מחבר מלא (2 כניסות ונשא כניסה) ורשום טבלת אמת שלו
2. ממש באמצעות FA מחבר של 2 כניסות בנות 32 סיביות.
3. בהנחה וכל מחבר בעל זמן חישוב t ושטח s.
מהו זמן החישוב של המוצא? כמה שטח תופס הרכיב? רכז בטבלה.
4. כעת נרצה לקצר את זמן החישוב — הצע דרך מהירה יותר.
5. כמה זמן יקח למוצא כעת? כמה שטח יתפוס הרכיב? הוסף לטבלה.
6. מצא דרך מהירה אף יותר. חזור על 4–5.
7. נסה להכליל: כמה זמן יקח למוצא עבור חלוקה ל־n רמות. בטא באמצעות n את ה־delay
8. מהו ה־n האופטימלי?'''
ep='''1. Design a full adder (two inputs and carry-in) and write its truth table.
2. Use FAs to build an adder for two 32-bit inputs.
3. Assume each FA has computation delay t and area s. What are the output delay and total area? Summarize in a table.
4. Propose a faster implementation.
5. Give its output delay and area; add it to the table.
6. Find an even faster implementation; repeat 4–5.
7. Generalize the delay for division into n levels.
8. What is the optimal n?'''
hints=[
 'במחבר שרשרת, איזה מידע צריך לעבור מהביט הפחות משמעותי לביט הבא, ומדוע הוא גורם להמתנה מצטברת?',
 'אפשר לחשב את החצי העליון מראש פעמיים: פעם בהנחה שהנשא מהחצי התחתון יהיה 0 ופעם בהנחה שיהיה 1. כשהנשא מגיע, איזו פעולה קצרה נשארה?',
 'אפשר להפעיל את אותו רעיון בתוך כל תת־מחבר. בכל רמת חלוקה חוצים את אורך שרשרת הנשאים, אבל מוסיפים שלב בחירה ומגדילים שטח. הגדירו את השהיית המוקס בנפרד מהשהיית FA.'
]
eh=[
 'In a ripple adder, which signal must travel from a less significant bit to the next, causing cumulative delay?',
 'Precompute the upper half twice, once for carry-in zero and once for one. Once the real lower carry arrives, what short operation remains?',
 'Apply the same idea inside each sub-adder. Every level halves the leaf ripple length but adds selection delay and area. Define MUX delay separately from FA delay.'
]
he='''הנחות וחוסר נתונים: t ו־s מתייחסים למחבר מלא של ביט אחד. לצורך חישוב השרשרת נשתמש במודל פשטני של השהיה t לכל תא עד Sum/Carry, בלי זמני חוטים, fanout או רגיסטרים. שתי הכניסות הן 32 ביט, נשא הכניסה C0 ניתן או מחובר ל־0; הפלט המלא הוא 32 ביטי סכום ונשא יציאה (33 ביט). התמונה אינה מגדירה ארכיטקטורת שיפור, השהיית/שטח MUX או משמעות מדויקת ל״n רמות״. לכן אין מספר יחיד ל־n האופטימלי מנתוני המקור בלבד. הפתרון להלן הוא הצעה עקבית באמצעות carry-select רקורסיבי; אין להציגו כארכיטקטורה היחידה או כשטח מינימלי.

סעיף 1 — Full Adder:

```text
S    = A XOR B XOR Cin
Cout = (A AND B) OR (A AND Cin) OR (B AND Cin)

A B Cin | S Cout
0 0  0  | 0  0
0 0  1  | 1  0
0 1  0  | 1  0
0 1  1  | 0  1
1 0  0  | 1  0
1 0  1  | 0  1
1 1  0  | 0  1
1 1  1  | 1  1
```

Sum הוא זוגיות של שלוש הכניסות; Carry הוא 1 אם לפחות שתיים מהן 1. נשמר A+B+Cin=S+2*Cout. אפשר לממש עם שני Half-Adders ושער OR לנשאים, או ישירות במשוואות. משוואות אלה מתארות שערים בתוך תא FA; בהמשך סופרים תאים שלמים לפי השטח הנתון.

סעיפים 2–3 — Ripple Carry: מחברים 32 תאי FA. תא i מקבל Ai,Bi,Ci ומוציא Si,C(i+1). מחברים נשא של כל תא לנשא הכניסה של הבא, מה־LSB ל־MSB. זמן worst-case במודל: 32t. שטח: 32s. חיבור נשאים הוא תלות קומבינטורית ולא 32 מחזורי שעון. בספריית תאים אמיתית זמני Cin->Sum ו־Cin->Cout יכולים להיות שונים; כאן הם אוחדו לצורך המודל.

סעיפים 4–5 — רמת Carry-Select אחת: מחלקים לביטים 0–15 ולביטים 16–31. מחבר אחד בן 16 ביט מחשב את החצי התחתון עם הנשא האמיתי. במקביל שני מחברים בני 16 ביט מחשבים את החצי העליון, אחד עם Cin=0 ואחד עם Cin=1. כשהנשא התחתון ידוע, בוחרים את התוצאה העליונה המתאימה בעזרת 17 מוקסי 2:1 חד־ביטיים: 16 עבור הסכום ואחד לנשא הסופי. נסמן השהיית מוקס d ושטחו u. זמן: 16t+d. שטח: 48s+17u. בלי תוספת זו של נתוני מוקס אפשר למסור נוסחה, אך לא מספר מדויק המבוסס רק על t,s. רוחב בחירת 17 כולל נשא יציאה; אם מבקשים סכום מודולו 2^32 בלבד אפשר להשמיט את מוקס הנשיאה העליון, ואין להשתמש באותה טבלת שטח ללא התאמה.

סעיף 6 — שתי רמות: מחליפים כל אחד משלושת מחברי 16 הביט באותו מבנה, הפעם שלושה מחברי 8 ביט ו־9 מוקסים. מתקבלים תשעה מחברי 8 ביט, כלומר 72 FA, ו־17+3*9=44 מוקסים. המסלול עובר שרשרת של 8 FA ועוד שתי בחירות: 8t+2d. שטח: 72s+44u. המהירות משתפרת לעומת רמה אחת רק אם d<8t; עלות הבחירה אינה אפסית בהכרח.

סעיפים 7–8 — נגדיר n כמספר רמות פיצול בינארי, כאשר n=0 פירושו שרשרת רגילה, ו־0<=n<=5. כל תת־מחבר, כולל עותקים המחושבים לנשא 0/1, משוכפל לפי אותה תבנית ללא שיתוף לוגיקה או פישוט קבועים. זהו מימוש קונקרטי נוח לניתוח, לא המימוש החסכוני ביותר של carry-select.

```text
leaf_width = 32 / 2^n
D(n) = (32 / 2^n)*t + n*d

FA_count(n)  = 32*(3/2)^n
MUX_count(n) = 32*((3/2)^n - 1) + (3^n - 1)/2
Area(n) = FA_count(n)*s + MUX_count(n)*u
```

הזמן נובע מכך שכל העותקים עובדים במקביל, ועל המסלול הארוך יש תת־מחבר עלה ואחריו מוקס אחד בכל רמת עץ. נסיגת השטח היא A(W,n)=3*A(W/2,n-1)+(W/2+1)*u, עם A(W,0)=W*s. האיבר W/2+1 סופר את ביטי הסכום העליונים ואת נשא היציאה. ממנו מתקבלות הנוסחאות הסגורות.

| n | רוחב עלה | זמן | שטח |
|---|---|---|---|
| 0 | 32 | 32t | 32s |
| 1 | 16 | 16t+d | 48s+17u |
| 2 | 8 | 8t+2d | 72s+44u |
| 3 | 4 | 4t+3d | 108s+89u |
| 4 | 2 | 2t+4d | 162s+170u |
| 5 | 1 | t+5d | 243s+332u |

בחירת n: מחשבים את שש אפשרויות הזמן ובוחרים את הקטנה, בכפוף למגבלת שטח אם יש. רמה נוספת כדאית לזמן רק כאשר:

```text
D(n+1) - D(n) = d - (32 / 2^(n+1))*t
```

אם ההפרש שלילי משתפרים; אם חיובי נעשים איטיים יותר; אם אפס מקבלים אותו זמן ויותר שטח. לדוגמה בלבד, בהנחה הנוספת d=t, הזמנים הם 32t,17t,10t,7t,6t,6t. גם n=4 וגם n=5 מינימליים בזמן; n=4 עדיף בשטח ולכן נבחר אם שוברים שוויון באמצעות שטח. אין להניח d=t או u=s בלי לומר זאת. כשהמוקס מהיר יותר, למשל d=t/2, n=5 עדיף בזמן במודל הזה. יש הבדל בין n רמות רקורסיביות לבין k בלוקים בטור: חלוקת carry-select רגילה ל־k בלוקים שווים נותנת מודל אחר, בקירוב (32/k)t+(k−1)d. אין לערבב את שני המשתנים והארכיטקטורות.

חלופה אפשרית לשיפור היא carry-lookahead או עץ prefix: מחשבים לכל ביט generate ו־propagate ומצרפים אותם בקבוצות. אפשר לקבל עומק לוגי לוגריתמי במקום שרשרת, אך לחישוב זמן ושטח מספריים נדרש מודל עלות לשערים/לקבוצות. משום כך גם חלופה זו אינה קובעת n יחיד מהנתונים t,s בלבד. אין צורך ב־FF לשיפור הקומבינטורי המוצע; pipeline משנה את latency במחזורים ודורש ניסוח דרישות אחר.

בדיקות: כל שמונה שורות FA, כל 1608 צירופי נתונים/נשא/עומק עבור רוחבי 1,2,4, ועוד 6036 מקרי 32 ביט/עומק (קצוות ואקראיות עם seed קבוע). הושוו לחיבור שלם מדויק כולל נשא. נסיגת ספירת הרכיבים הושוותה לנוסחה הסגורה בכל עומק, ונבדקו שלוש דוגמאות ליחס השהיות. אלה בדיקות פונקציונליות ואלגבריות בלבד, ללא HDL, סינתזה או מדידת השהיה/שטח פיזיים.

תעדוף: גבוה במיוחד להכנה — חשבון בינארי, נשא, מסלול קריטי, חישוב מראש, בחירה ופשרת שטח/מהירות הם יסודות מועילים להבנת חומרה ולוולידציה. זו הערכת הכנה לפי התפקיד, לא תחזית לראיון ב־Marvell. השיוך ל־Apple נשמר כפי שמופיע בצילום.'''
en='''Assume t,s are the delay and area of a one-bit FA, with a simplified common delay for sum/carry, ignoring wire delay, fanout and registers. Inputs are two 32-bit words and a carry-in (or tie it to zero). Include 32 sum bits plus carry-out. MUX cost and the meaning of n levels are absent from the source, so there is no unique numeric optimum from t,s alone. The following is an explicit unpruned recursive carry-select proposal, not a claimed global area optimum.
FA: S=A XOR B XOR Cin; Cout=AB OR A*Cin OR B*Cin. For inputs 000,001,010,011,100,101,110,111 the (S,Cout) outputs are 00,10,10,01,10,01,01,11. The invariant is A+B+Cin=S+2*Cout. A 32-FA ripple chain has modeled delay 32t and area 32s.
One carry-select level uses a lower 16-bit adder with the real carry-in plus two upper 16-bit adders for carry-in 0 and 1, computed in parallel. Seventeen one-bit 2:1 MUXes select upper sum and final carry. With MUX delay d and area u, delay is 16t+d and area 48s+17u. Recursing each of the three 16-bit sub-adders yields 72 FAs and 44 MUXes, delay 8t+2d and area 72s+44u. The second level is faster only if d<8t.
Define n as binary recursion levels, n=0..5, with no constant simplification or shared speculative logic. Leaf width=32/2^n; D(n)=(32/2^n)t+n*d. FA count=32*(3/2)^n. MUX count=32*((3/2)^n-1)+(3^n-1)/2, from A(W,n)=3*A(W/2,n-1)+(W/2+1)u and A(W,0)=Ws. Count pairs (FA,MUX) for n=0..5: (32,0),(48,17),(72,44),(108,89),(162,170),(243,332). Delay sequence: 32t,16t+d,8t+2d,4t+3d,2t+4d,t+5d. One extra level changes delay by d-(32/2^(n+1))t. Choose the minimum over valid n, respecting any area budget. If d=t is additionally assumed, n=4 and 5 tie at 6t; choose 4 for lower area. If d=t/2, n=5 is fastest in this model. Neither d=t nor u=s follows from the prompt. Omitting carry-out changes area; counting k serial equal-sized blocks gives a different model, roughly (32/k)t+(k-1)d, and must not be confused with recursion levels.
Carry-lookahead/parallel-prefix is another possible architecture, requiring its own gate cost model for timing/area. No pipeline/registers are needed here; a pipeline changes latency semantics. Verified 8 FA rows, 1608 exhaustive small-width configurations, 6036 32-bit/depth cases, recursive component counts and algebraic model optima. No HDL, synthesis or measured timing/area. High preparation priority for arithmetic, carry paths and area/speed reasoning; source reports Apple, not independently verified.'''
q={
 'id':'PREP-034','key':'full-adder-32-bit-area-delay-recursive-carry-select','version':1,'created_on':'2026-09-29','category':'hardware','topic':'adder_architectures',
 'topics':['hardware','full_adder','ripple_carry','carry_select','critical_path','area_delay_tradeoff','recursive_design'],
 'source_topic_tags':['hardware'],'added_topic_tags':['full_adder','ripple_carry','carry_select','critical_path','area_delay_tradeoff','recursive_design'],
 'source_tags':['hardware','apple'],'reported_companies':['Apple'],'source_company_badge':'אפל','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'circuit_design_and_optimization','status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-034.png','received_on':'2026-09-29'}],'original_prompt':prompt,
 'translations':{'he':{'title':'מחבר 32 ביט — נשאים, שטח, השהיה וחלוקה לרמות','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'32-bit adder: carry, area, delay and recursive levels','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-034-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['t,s describe a one-bit FA under a simplified uniform delay model.','32 sum bits plus carry-out included; Cin provided or tied to zero.','MUX delay d and area u are additional unknowns.','n means binary carry-select recursion levels in this proposal, 0..5.','No speculative logic sharing, constant simplification, wire/fanout costs or pipelining in modeled counts.'],
 'ambiguities':['Source does not specify MUX delay or area.','Source does not define the improvement architecture or n-level partition convention.','Optimal n depends on component delay ratio, area budget and chosen architecture.'],
 'optimality':{'criterion':'Modeled worst-case combinational delay over n=0..5; area as optional tie-breaker','result':'Conditional argmin of (32/2^n)t+n*d; with d=t, n=4 or 5 tie, and 4 uses less area.','scope':'Specified recursive unpruned architecture only; no global minimal-area or physically fastest-adder claim.'},
 'verification':{'status':'passed','checked_on':'2026-09-29','script_path':'checks/check_prep_034.py','method':'8 FA rows, 1608 exhaustive small-width cases, 6036 32-bit/depth cases, structural counts and conditional delay optima.','scope':'Functional and algebraic model, no synthesis/physical measurements.'},
 'solution_code_path':'solutions/prep_034_recursive_carry_select.py','media_assets':[{'type':'source_image','path':'sources/prep-034.png','description':'Complete eight-part question with hardware and Apple tags.'}],
 'interview_relevance':{'priority':'high','label_he':'עדיפות גבוהה במיוחד — מחברים ומסלול קריטי','basis':'Binary arithmetic, signal dependencies, speculative parallel computation and area/delay tradeoffs support digital-hardware and validation reasoning.','assessment_scope':'Preparation judgment, not exact interview prediction.'},
 'related_question_ids':['PREP-001','PREP-018','PREP-020'],'common_mistakes':['Counting ripple stages as clock cycles','Ignoring MUX delay and area','Counting one bit-wide MUX instead of a bus of MUXes','Dropping carry-out without changing the specification','Confusing recursion levels with serial blocks','Claiming more levels always improve time','Presenting conditional area formulas as technology-independent minima'],
 'markdown_path':'questions/prep-034-adder-area-delay.md'
}
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
assert before['question_count']==33 and all(x['id']!=q['id'] for x in before['questions'])
pos=raw.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
updated=(raw[:pos]+',\n'+entry+raw[pos:]).replace('"question_count": 33','"question_count": 34',1)
after=json.loads(updated);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==34
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-6734d003-8bb0-4ee8-bd00-5d689618a073.png',root/'sources/prep-034.png')
p.write_text(updated,encoding='utf-8')
md='# PREP-034 — מחבר 32 ביט: שטח, השהיה ורמות חלוקה\n\n## נוסח המקור\n\n'+prompt+'\n\n![צילום המקור](../sources/prep-034.png)\n\nתגית מקור hardware; חברה Apple ותווית אפל. השיוך לא אומת עצמאית. עדיפות גבוהה במיוחד להכנה, כהערכת רלוונטיות בלבד.\n\n## שלושה רמזים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he+'\n\n[מודל המחבר](../solutions/prep_034_recursive_carry_select.py) · [בדיקות](../checks/check_prep_034.py)\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(eh,1))+'\n\n'+en+'\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-034 — מחבר 32 ביט: שטח, השהיה וחלוקה לרמות](questions/prep-034-adder-area-delay.md) — **עדיפות גבוהה במיוחד**; שמונת הסעיפים, רמזים, טבלת אמת, מודל שיפור רקורסיבי ובדיקות; נתוני MUX חסרים סומנו כתנאי לפתרון האופטימלי.\n',encoding='utf-8')
print('PREP-034 saved; 34 questions; complete bilingual proposed solution with explicit cost assumptions.')
