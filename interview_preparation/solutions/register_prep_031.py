"""Register XOR with MUXes and the sole constant zero."""
import json
import shutil
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'checks'))
from check_prep_031 import check
check()

prompt="ממש XOR בעזרת MUX-ים וערך קבוע '0'."
ep="Implement XOR using MUXes and the constant value '0'."
hints=[
    'כתוב מה הפלט צריך להיות כאשר אחת הכניסות היא 0 ומה הוא צריך להיות כאשר היא 1. זכור שלרשותך רק קבוע 0, בלי קבוע 1 או שער NOT.',
    'אין צורך לייצר את השלילה של כניסה בכל המצבים: אפשר לייצר אות שמתנהג כמו השלילה רק כאשר המוקס הבא באמת בוחר בו.',
    'בחר a כסלקטור של המוקס האחרון. כש־a=0 צריך להעביר b. כש־a=1 צריך להעביר NOT b: האם a עצמו יכול לשמש ערך 1 בענף הזה בלבד?'
]
eh=[
    'Split the XOR truth table by one input. Only constant zero is available; no constant one or NOT gate.',
    'An intermediate signal need not equal an inverted input for every case, only when the final MUX selects it.',
    'Select the last MUX with a. At a=0 pass b; at a=1 pass NOT b. Could a itself serve as one within that selected case?'
]
he='''הנחה: MUX רגיל 2:1 בעל מוצא לא מהופך, כניסות הנתונים והסלקטור יכולים להיות a,b,0 או מוצא מוקס קודם. אין קבוע 1, כניסות משלימות, שערים נוספים או משוב. סוג המוקס לא צוין במקור, ולכן יש לציין הנחה זו ולא לטעון למינימום גורף לכל גודל MUX.

הצעה לפתרון: שני מוקסים. החיבורים נכתבים בנפרד מהעברית כדי למנוע היפוך כיווניות:

```text
Convention: MUX(S, I0, I1) = I0 when S=0; I1 when S=1
MUX1: S=b, I0=a, I1=0 -> t
MUX2: S=a, I0=b, I1=t -> Y
```

כאשר a=0, המוקס האחרון בוחר b, בדיוק כנדרש ב־XOR. כאשר a=1, המוקס הראשון מקבל בכניסות הנתונים 1 ו־0, ולכן מוציא את השלילה של b, והאחרון בוחר במוצא הזה. ה־1 אינו מקור קבוע שהוספנו; זהו ערכה של כניסת a במקרה הנדון. האות t אינו NOT b בכל המצבים: כאשר a=0 הוא 0, אבל אז המוקס האחרון אינו בוחר בו. זהו הרעיון המרכזי: לנצל תנאי שבו ענף נבחר, ולא לנסות לבנות NOT כללי שאין עבורו קבוע 1.

```text
t = a AND NOT b
Y = (NOT a AND b) OR (a AND t)
  = (NOT a AND b) OR (a AND b') = a XOR b

a b | t Y
0 0 | 0 0
0 1 | 0 1
1 0 | 1 1
1 1 | 0 0
```

מינימום בשימוש במוקסי 2:1: ללא מוקסים a,b,0 אינם XOR. במוקס יחיד הסלקטור הוא 0,a או b. עם סלקטור 0 נבחר חוט גולמי בלבד. עם סלקטור a, בענף a=1 צריך NOT b, אך הנתונים הזמינים בענף הם רק 0,1,b, ואף אחד אינו NOT b עבור שני ערכי b. עם סלקטור b ההוכחה סימטרית. לכן צריך לפחות שניים, והמימוש משיג שניים.

אם מותר MUX של 4:1, מספיק אחד: חבר את a ל־S1 ואת b ל־S0 ואת I0,I1,I2,I3 אל 0,b,a,0 בהתאמה. כאשר הבחירה 01, b כבר 1; כאשר 10, a כבר 1. גם כאן אין קבוע 1. לכן מספר הרכיבים האופטימלי תלוי בגודל הרכיב המותר.

בלי שום קבוע, רשת של מוקסים רגילים על a,b בלבד שומרת 1: בקלט 11 כל חוט וכל מוצא יהיו 1, בעוד XOR דורש 0. לכן קבוע 0 הוא מהותי כאן. אין סתירה לחוסר האפשרות לבנות NOT כללי עם מוקסים וקבוע 0 בלבד, כי כל הרשתות האלה שומרות 0; XOR עצמו שומר 0.

בדיקה: ארבע שורות טבלת האמת נבדקו בפייתון; נבדקו כל 27 החיווטים למוקס יחיד שכניסותיו נלקחות מ־0,a,b ואף אחד לא מממש XOR. נבדקה גם חלופת 4:1. אין בכך בדיקת השהיה, glitches או שערוך פיזי. תשובה קצרה לראיון: מחברים מוקס ראשון שבוחר a או 0 לפי b, ומוקס שני שבוחר b או מוצא הראשון לפי a. ההיפוך של b נדרש רק כש־a=1, ובתנאי זה a מספק את ה־1 הדרוש בלי קבוע 1.'''
en='''Assume ordinary non-inverting 2:1 MUXes with raw a,b, constant zero and earlier MUX outputs as wires, without extra gates, complements or feedback. The source does not specify MUX size.
With MUX(S,I0,I1) selecting I0 at S=0, use t=MUX(b,a,0), Y=MUX(a,b,t). At a=0 the output is b. At a=1, the first MUX has data 1 and 0 and outputs NOT b, which is selected by the last MUX. No constant-one source is introduced: a is one only in the relevant case. t=a AND NOT b globally, not NOT b. Truth rows (a,b,t,Y): (0,0,0,0),(0,1,0,1),(1,0,1,1),(1,1,0,0).
Two 2:1 MUXes are minimal. Zero MUXes provide only raw a,b,0. One MUX has select 0,a or b: select 0 chooses a raw wire; select a requires NOT b when a=1, but available raw data reduce to 0,1,b, none equal NOT b. Select b is symmetric. Exhaustively verified all four truth rows and rejected all 27 one-MUX raw-input wirings.
If a 4:1 MUX is permitted, one suffices with S1=a,S0=b and data (0,b,a,0); also verified on all four rows. Without any constants, ordinary MUX networks preserve the all-one input and cannot implement XOR. With only zero, general NOT is impossible by zero preservation, but XOR is zero-preserving and this conditional inversion is possible. No HDL/timing/glitch claim. Scope optimality to the allowed MUX size and count, not general physical area/delay.'''
q={
 'id':'PREP-031','key':'xor-mux-zero-only','version':1,'created_on':'2026-09-29','category':'hardware','topic':'mux_boolean_synthesis',
 'topics':['hardware','combinational_circuits','multiplexers','xor','boolean_algebra','conditional_reasoning'],
 'source_topic_tags':['hardware'],'added_topic_tags':['combinational_circuits','multiplexers','xor','boolean_algebra','conditional_reasoning'],
 'source_tags':['nvidia','hardware','apple','intel'],'reported_companies':['NVIDIA','Apple','Intel'],'source_company_badge':'אינטל','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'construct','status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot','reviewed_by':None,
 'authorship':'Original prompt/source tags transcribed; AI-assisted bilingual explanation and exhaustive functional verification.',
 'sources':[{'type':'user_supplied_image','path':'sources/prep-031.png','received_on':'2026-09-29'}],'original_prompt':prompt,
 'translations':{'he':{'title':'מימוש XOR באמצעות מוקסים וקבוע 0 בלבד','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'XOR using MUXes and only constant zero','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-031-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Ordinary non-inverting 2:1 MUXes for primary solution; source size unspecified.','Only raw a,b, constant zero and earlier MUX outputs available; combinational acyclic wiring.','Standard binary truth values and unrestricted fanout.'],
 'optimality':{'criterion':'Number of permitted MUX components','result':'Two 2:1 MUXes; one 4:1 MUX if allowed.','proof':'Case split on all possible one-MUX selects 0,a,b; none provides required complement cofactor with raw data.','scope':'Component count with specified MUX size, no complements or extra constants; not physical area/timing.'},
 'edge_cases':['00 must give 0','11 must give 0','01 and 10 must give 1','t is not globally NOT b','No hidden constant-one source','4:1 vs 2:1 ambiguity'],
 'verification':{'status':'passed','checked_on':'2026-09-29','script_path':'checks/check_prep_031.py','method':'All four input cases and all 27 one-MUX wirings; alternative 4:1 truth table.','scope':'Functional Python model only.'},
 'media_assets':[{'type':'source_image','path':'sources/prep-031.png','description':'Full XOR/MUX/zero question with company and hardware tags.'}],
 'related_question_ids':['PREP-011','PREP-015'],'relationship_note':'MUX synthesis with restricted constants and XOR from other primitives; distinct function/constraint combination.',
 'interview_relevance':{'priority':'high','label_he':'חזרה קצרה חשובה על מוקסים וחשיבה לפי תנאים','basis':'Digital logic, constraints and truth-table verification; useful foundations, though earlier MUX exercises cover related concepts.','assessment_scope':'Preparation judgment based on supplied role, not an interview prediction.'},
 'common_mistakes':['Using constant 1 or an unprovided inverted input','Assuming t must equal NOT b globally','Claiming impossibility merely because standalone NOT cannot be built','Giving a minimum without specifying MUX size'],
 'markdown_path':'questions/prep-031-xor-mux-zero-only.md'
}
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
assert before['question_count']==30 and all(v['id']!=q['id'] for v in before['questions'])
pos=raw.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
updated=(raw[:pos]+',\n'+entry+raw[pos:]).replace('"question_count": 30','"question_count": 31',1)
after=json.loads(updated);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==31
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-9dbf7fdf-9190-44ea-984b-fd73f6b60fbb.png',root/'sources/prep-031.png')
p.write_text(updated,encoding='utf-8')
md='# PREP-031 — XOR באמצעות MUX וקבוע 0\n\n## נוסח המקור\n\n'+prompt+'\n\n![צילום המקור](../sources/prep-031.png)\n\nחברות לפי המקור: NVIDIA, Apple, Intel; תווית ראשית אינטל. שיוך לא מאומת. תגית מקור: hardware. סיווג נוסף: מוקסים, XOR, לוגיקה קומבינטורית ומימוש תחת אילוצים.\n\nעדיפות גבוהה כחזרה קצרה על יסודות שכבר נלמדו, לא תחזית לראיון.\n\n## שלושה רמזים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he+'\n\n[בדיקות](../checks/check_prep_031.py)\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(eh,1))+'\n\n'+en+'\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-031 — XOR עם מוקסים וקבוע 0 בלבד](questions/prep-031-xor-mux-zero-only.md) — נשמרו מקור, חברות, רמזים, פתרון מותנה בגודל המוקס ובדיקת כל הקלטים.\n\nהעדפת כתיבה: להסביר בעברית, אך לרשום חיבורים וביטויים טכניים מורכבים בבלוק קוד נפרד משמאל לימין, כדי למנוע ערבוב סימונים ואינדקסים בכיווניות RTL.\n',encoding='utf-8')
print('PREP-031 saved: 31 questions, source preserved, bilingual hints/solution and minimality verified.')
