"""Persist the switch/observer riddle with explicit observation/channel assumptions."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prompt='''יש שני חדרים, באחד יש 100 מתגים ובשני יש מנורה אחת. רק מתג אחד מדליק את המנורה. בחדר עם המנורה עומד בן אדם, ואפשר לשאול אותו שאלה אחת. אי אפשר לראות ולשמוע מה קורה בחדרים. כיצד תגלה איזה מתג מדליק את המנורה?'''
ep='''There are two rooms: one has 100 switches and the other has one lamp. Only one switch controls the lamp. A person stands in the lamp room and may be asked one question. You cannot see or hear what happens in the rooms. How can you identify the switch controlling the lamp?'''
hints=[
 'האם שאלה אחת חייבת לקבל תשובה של כן או לא? חשוֹב איזה מידע האדם שבחדר יכול למסור בתשובה אחת.',
 'האדם יכול אולי לצפות במה שקרה למנורה לאורך זמן, ולא רק במצב שלה ברגע האחרון. איך תוכל לתת לכל מתג התנהגות מזוהה משלו?',
 'מספר את המתגים. נסה להפעיל כל מתג מספר פעמים שונה, ובדוק איזה מספר יחיד האדם יכול למסור בסוף כדי לזהות את המתג.'
]
eh=[
 'Does one question necessarily imply a yes/no answer? What information could the observer convey in one reply?',
 'If the person watches over time, the lamp has a history, not just a final state. Can each switch have a distinct observable signature?',
 'Number the switches and operate each a different number of times. What one count could identify the controlling switch?'
]
he='''**הנחות שבלעדיהן השאלה אינה מוגדרת היטב:** מותר להפעיל את המתגים מספר פעמים; לכל מתג מצב ON/OFF ידוע וניתן להתחיל כשכולם OFF; המתג היחיד השולט מתנהג באופן רגיל (ON מדליק ו־OFF מכבה), ללא תקלות. האדם ליד המנורה מסוגל לראות אותה לאורך הניסוי, סופר או מתעד לפי פרוטוקול מוסכם ומשיב בכנות. איסור הראייה והשמיעה מפורש כאיסור עלינו לקבל תצפית ישירה/אותות מהחדר השני, מלבד השאלה והתשובה המותרות; אם האיסור חל גם על האדם ליד המנורה או אוסר אפילו קבלת תשובתו, צריך הבהרה. ״שאלה אחת״ אינה מוגבלת במקור לשאלת כן/לא. אפשר לתת את ההנחיה כחלק מאותה שאלה לפני תחילת הניסוי, ולבקש את התשובה רק בסופו, עם התחלה/סיום מוסכמים; אין צורך לשאול שאלות ביניים.

**פתרון פשוט ומדויק:** מספר את המתגים 1..100 והתחל מכולם כבויים. שאל את האדם פעם אחת: ״במהלך הניסוי שאבצע עכשיו, כמה פעמים המנורה תעבור מכבוי לדלוק? מנה ודווח לי בסיום.״ כעת הפעל את מתג 1 במחזור הדלקה־כיבוי אחד, את מתג 2 בשני מחזורי הדלקה־כיבוי, וכן הלאה, ואת מתג 100 במאה מחזורים. המתן מספיק זמן בכל מצב כדי שאפשר יהיה להבחין בו, וסיים כל מחזור במצב כבוי. כל המתגים חוץ מהמתג המחובר אינם משפיעים על המנורה. לכן אם המתג המחובר הוא k, האדם יראה בדיוק k הדלקות, ותשובתו היא מספר המתג. לדוגמה, 37 הדלקות פירושן מתג 37.

יש לספור מעברים OFF→ON או מחזורי הבהוב שלמים, לא מספר נגיעות במתג. כדי להבהב k פעמים עושים k הדלקות ו־k כיבויים: 2k שינויי מצב. לכן בתכנית הפשוטה יש 1+2+...+100=5050 מחזורים ו־10100 שינויי מצב בסך הכול, מעבר להעמדה ההתחלתית. זו דרך להוכיח היתכנות, לא מינימום פעולות או זמן. זמן כולל עולה גם לפי משך המתנה בין פעולות. ההנחות על תיאום ותצפית נדרשות ואינן פרטים שנאמרו במפורש בצילום.

**חלופה יעילה במספר סבבי תצפית — קידוד בינארי:** אם מותר פרוטוקול של זמנים ידועים מראש, שבעה סבבים מספיקים. רשום כל מספר מתג 1..100 בשבעה ביטים. בסבב הראשון הדלק בדיוק את המתגים שהביט המשמעותי ביותר במספרם הוא 1; בסבב הבא לפי הביט הבא, וכן הלאה. האדם רושם 1 אם המנורה דולקת ו־0 אם כבויה בכל חלון תצפית, ומחזיר בתשובה אחת את כל שבע התוצאות. הרצף הוא המספר הבינארי של המתג המחובר. לדוגמה, 0100101 הוא 37. מצבי המתגים נקבעים בכל סבב לפי הקוד, ולא מחליפים אוטומטית את כל מצביהם. ממתינים עד שהשינויים הסתיימו לפני התצפית; מה שנראה בזמן מעבר בין סבבים אינו ביט בקוד. הסבבים חייבים להיות מתואמים גם אם שני סבבים סמוכים נותנים אותה תוצאה ואי אפשר לזהות ביניהם שינוי מנורה.

שבעה סבבים הם מינימום תחת מודל מוגדר של תצפית בינארית אחת לכל סבב: שישה מספקים לכל היותר 2^6=64 רצפים, ושבעה 2^7=128, מספיק למאה מתגים. אלה שבע תצפיות ותשובה אחת, ולא שבע שאלות לאדם. אין טענה למינימום שינויי מצב ידניים, דקות או לכל פרוטוקול המשתמש בזמן רציף/ספירה; עבור מספר מתגים משתנה N מדובר ב־ceil(log2 N) סבבים. הכנת תכניות המתגים והפעלתן אינן בחינם.

**אם מותרת רק תשובת כן/לא אחת:** אי אפשר לזהות בוודאות אחד ממאה מתגים ללא מידע נוסף או ערוץ צד. לשתי תשובות יש רק שתי אפשרויות, בעוד צריך להבחין בין מאה. גם היסטוריה שהאדם ראה לא מועילה לנו אם הוא רשאי להעביר רק ביט אחד. שימוש בזמן ההמתנה לתשובה כקידוד מוסיף ערוץ צד ואינו עומד במודל ביט יחיד. אם מותר רק לדווח על מצב המנורה ברגע אחד, אותה אי־אפשרות תקפה. זו הסיבה להבחין בין מספר השאלות לבין כמות המידע בתשובה.

**בדיקה:** נבדקו במודל אידאלי כל מאה המתגים האפשריים; ספירת ההדלקות שווה למספר המתג, וכל שבעת ביטי התצפיות מייצרים קוד ייחודי. לא נעשתה בדיקה פיזית של מנורה, זמני תגובה או שגיאות ספירה. לא נדרש שימוש בחום המנורה או כניסה לחדר השני.'''
en='''The prompt is underspecified. Assume repeated switch operation is allowed, switches have known ON/OFF states and start OFF, exactly one ordinary switch controls a reliable lamp, and the nearby person can observe over time and report truthfully. Interpret the no-see/hear restriction as no direct cross-room observations except the permitted question/reply, not as blinding the observer or forbidding the reply itself. One question need not mean a yes/no answer. Instructions can be included in the single question before a prearranged experiment, with a reply afterward; observation start/end must be agreed.

Simple protocol: number switches 1..100, ask once how many OFF-to-ON transitions occur during the experiment, and cycle switch i ON then OFF exactly i times. All unconnected switches have no effect; if switch k controls the lamp the observer reports k illuminations, identifying it. Leave each cycle OFF and allow perceptible pauses. Count complete illuminations, not toggles: this uses 5050 cycles/10100 state changes, excluding initialization, so it demonstrates feasibility rather than minimum action count or time.

If synchronized observation slots are allowed, seven binary rounds suffice. Encode each switch number in seven bits and set each switch ON in the rounds where its corresponding bit is one. The observer samples only after each configuration stabilizes and returns all seven states in one answer; 0100101 identifies 37. Framing is essential even if consecutive bits match. Seven is minimum for one binary sample per round because 2^6<100<=2^7. It is not a minimum for arbitrary analog/timing or pulse-count encodings, nor for manual switching operations. These are seven observations but only one question/reply.

If the only permitted communication is a single yes/no answer (and no timing side channel), identification among 100 candidates is impossible: only two response outcomes are available. A single final lamp-state observation has the same limitation. The source does not explicitly resolve these constraints, so state them rather than silently assume them. Abstract tests cover all 100 candidates for each protocol; no physical lamp, timing or observer-reliability test was performed.'''
q={
 'id':'PREP-028','key':'hundred-switches-one-observer-question','version':1,'created_on':'2026-09-28','category':'logic','topic':'information_encoding',
 'topics':['logic','information_encoding','binary_representation','experiment_design','assumptions'],
 'source_topic_tags':['logic'],'added_topic_tags':['information_encoding','binary_representation','experiment_design','assumptions'],
 'source_tags':['logic','intel'],'reported_companies':['Intel'],'source_company_badge':'אינטל','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'puzzle','status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
 'authorship':'Prompt transcribed; AI-assisted translations, hints, conditional protocols and abstract checks.','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-028.png','received_on':'2026-09-28'}],'original_prompt':prompt,
 'translations':{'he':{'title':'100 מתגים, מנורה ושאלה אחת לאדם בחדר','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'100 switches, one lamp and one question to an observer','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-028-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Repeated switch operation allowed; known OFF initial positions.','One reliable switch directly controls lamp ON/OFF.','Observer can watch lamp history, count/record and answer truthfully.','A single unrestricted reply can convey a number or bit sequence, not necessarily one bit.','Instructions and observation framing may be agreed within the single-question protocol.','No direct cross-room view/sound beyond permitted communication.','Binary-round alternative requires synchronized stable observation slots.'],
 'optimality':{'criterion':'Identify switch with one observer reply; optional minimize binary observation rounds.','result':'Count protocol succeeds using one integer reply; seven framed binary rounds suffice and are minimal for one binary sample per round.','scope':'Count protocol is not minimum switching/time; one yes/no reply is impossible; arbitrary timing codes use a different model.'},
 'edge_cases':['Switch 1','Switch 100','Known initial state','Counts vs toggles','Consecutive identical binary samples','Transient switching between slots','Yes/no-only reply','Observer unable to observe or report'],
 'verification':{'status':'passed','checked_on':'2026-09-28','script_path':'checks/check_prep_028.py','method':'All 100 controlling-switch identities for pulse count and seven-bit round reports; unique codes and action count checked.','scope':'Abstract ideal model only; physical timing and human reliability not tested.'},
 'media_assets':[{'type':'source_image','path':'sources/prep-028.png','description':'Full original question and Intel/logic tags.'}],
 'interview_answer':'בהנחה שמותרת תשובה מספרית והאדם צופה בניסוי: מספר את המתגים, הפעל את מתג i ב־i מחזורי הדלקה־כיבוי ושאל פעם אחת כמה פעמים נדלקה המנורה. התשובה היא מספר המתג. אם מותרת רק תשובת כן/לא אחת, אי אפשר לזהות אחד ממאה. אפשר גם לקודד בשבע תצפיות בינאריות מתואמות ולמסור את כולן בתשובה אחת.',
 'common_mistakes':['Equating one question with one bit','Assuming count protocol minimizes operations','Confusing toggle count with illuminations','Ignoring initial switch state','Leaving observers without start/end framing','Treating seven observations as necessarily seven questions','Using unsupplied heat/access/timing channels'],
 'interview_relevance':{'priority':'low','label_he':'שאלת העשרה — עדיפות נמוכה בזמן מוגבל','basis':'Useful for clarifying assumptions and encoding observations, but less directly aligned with the supplied role than Python, bit operations, validation/debugging and networking fundamentals.','assessment_scope':'Preparation judgment, not an interview prediction.'},
 'related_question_ids':[],'markdown_path':'questions/prep-028-hundred-switches-one-question.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
assert before['question_count']==27 and not any(x['id']==q['id'] for x in before['questions'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-d6ab6e83-2c94-4e12-84ac-592724e01444.png',root/'sources/prep-028.png')
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 27','"question_count": 28',1)
after=json.loads(s);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==28
p.write_text(s,encoding='utf-8')
md='# PREP-028 — 100 מתגים ושאלה אחת\n\n## השאלה המקורית\n\n'+prompt+'\n\n![צילום המקור](../sources/prep-028.png)\n\n'
md+='## קטגוריות וחברות\n\nתגית מקור: logic. סיווג נוסף: קידוד מידע, ייצוג בינארי, תכנון ניסוי ובירור הנחות. חברה ותווית לפי המקור: Intel/אינטל; השיוך לא אומת עצמאית.\n\n## רלוונטיות להכנה\n\nעדיפות נמוכה בזמן מוגבל: חידת העשרה על הנחות וכמות מידע. הערכת הכנה בלבד, לא תחזית לראיון.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[בדיקת הפרוטוקולים](../checks/check_prep_028.py)\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en+'\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-028 — 100 מתגים ושאלה אחת](questions/prep-028-hundred-switches-one-question.md) — מקור, חברה, שלושה רמזים ופתרונות מותנים; נשמרה ההבחנה בין שאלה אחת לתשובה בת ביט אחד.\n',encoding='utf-8')
print('PREP-028 saved; 28 questions; observer/communication assumptions and scoped optimality documented.')
