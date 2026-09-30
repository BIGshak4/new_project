"""Register timing/critical-path exercise and persist preparation-priority preference."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-d95d55ed-4045-4265-8f30-860332ad962e.png',root/'sources/prep-020.png')
prompt='''בהינתן המעגל הבא:
כאשר A,B,C,D,E,F הם רגיסטרים וזמני ההשהיה של הרכיבים הם כדלקמן:
קופסה שחורה: 3 ננו שניות
מכפל: 2.7 ננו שניות
מוקס: 1.5 ננו שניות
מהפך: 0.1 ננו שניות
א) מצא את המסלול הקריטי.
ב) בהינתן אותם רכיבים, שפר את המסלול הקריטי.
המעגל נתון בתרשים המצורף.'''
ep='''Given the circuit in the attached diagram, A,B,C,D,E,F are registers. Component delays are: black box 3 ns; multiplier 2.7 ns; mux 1.5 ns; inverter 0.1 ns. (a) Find the critical path. (b) Using the same components, improve the critical path.'''
hints=[
 'מסלול יכול להגיע למוצא דרך כניסת נתונים של MUX או דרך כניסת הבחירה שלו. עקוב מכל רגיסטר עד המוצא, וחבר רק השהיות שנמצאות זו אחרי זו באותו מסלול.',
 'שני ה־MUX עובדים במקביל, אך הקלטים לבחירה שלהם מגיעים מהקופסה השחורה. בדוק גם את ההיפוך בכניסת הבחירה של ה־MUX הימני: האם הוא מוסיף השהיה למסלול אחד?',
 'כתוב מה המכפל מחשב כאשר אות הבחירה 0 וכאשר הוא 1. אפשר להסיר היפוך בכניסת בחירה אם מחליפים את שתי כניסות הנתונים של אותו MUX. אם מותר להוסיף מכפל נוסף, בדוק גם חישוב שתי התוצאות במקביל ובחירה ביניהן בסוף.'
]
eh=[
 'A path can reach a mux output through a data input or its select input. Trace each register-to-output path and add only delays in series.',
 'The two muxes work in parallel, but their select comes from the black box. Account for the inversion shown on the right mux select.',
 'Write the function for select 0 and 1. Swapping a mux\'s data inputs removes a select inversion. If an extra multiplier is allowed, also consider computing both possible products before the final selection.'
]
he='''**קריאת התרשים והנחות:** נסמן S כמוצא הקופסה השחורה המוזנת מ־E,F. ה־MUX השמאלי מקבל C בכניסה 0 ו־D בכניסה 1, ובחירתו S. בכניסת הבחירה של ה־MUX הימני מופיעה בועת היפוך קטנה; נפרש אותה כמהפך בעל ההשהיה שניתנה, כך שבחירתו NOT S, והוא מקבל A בכניסה 0 ו־B בכניסה 1. פלטי ה־MUX מוזנים במקביל לשתי כניסות מכפל אחד. בקו היורד מה־MUX השמאלי יש גשר מעל קו הבחירה: זו חציית חוטים ללא חיבור. התמונה המקורית נשמרה, והמספרים להלן מותנים בפירוש בועת הבחירה כמהפך. אם אין שם היפוך, ההשהיה המקורית היא 7.2 ns והפונקציה אחרת.

נניח שההשהיות שניתנו הן השהיות התפשטות מקסימליות, ול־MUX אותה השהיה מנתונים ומבחירה. זמני clock-to-Q, חיווט ועומס אינם נתונים ולכן לא מוסיפים להם ערכים מומצאים. אין בתרשים רגיסטר קליטה במוצא. אנו מחשבים השהיה קומבינטורית מבנית מהמוצאים של הרגיסטרים אל המוצא, ולא תדר שעון מובטח או בדיקת setup/hold מלאה. תפקוד הקופסה השחורה אינו ידוע, לכן גם אי אפשר להוכיח שהמסלול רגיש לכל שינוי קלט או לשלול false paths לפי הפונקציה הפנימית.

**א. המסלול הקריטי:**

| מקור ומסלול | חישוב | השהיה |
|---|---|---|
| A או B → כניסת נתונים של MUX ימני → מכפל | 1.5+2.7 | 4.2 ns |
| C או D → כניסת נתונים של MUX שמאלי → מכפל | 1.5+2.7 | 4.2 ns |
| E או F → קופסה שחורה → בחירת MUX שמאלי → מכפל | 3+1.5+2.7 | 7.2 ns |
| E או F → קופסה שחורה → מהפך → בחירת MUX ימני → מכפל | 3+0.1+1.5+2.7 | **7.3 ns** |

המסלול הקריטי המבני הוא האחרון. אין לחבר את השהיות שני ה־MUX: הם עובדים במקביל. מוצא המכפל מוכן אחרי המאוחר משני קלטיו ועוד 2.7 ns. מוצא ה־MUX השמאלי זמין לאחר max(0,3)+1.5=4.5 ns, והימני לאחר max(0,3.1)+1.5=4.6 ns. לכן מוצא המכפל זמין לאחר max(4.5,4.6)+2.7=7.3 ns.

**ב. שיפור ללא הוספת רכיבים:** נחליף את מיקומי A,B בכניסות ה־MUX הימני ונחבר את S ישירות לכניסת הבחירה, ללא מהפך:

```text
לפני: MUX(select=NOT S, data0=A, data1=B)
אחרי: MUX(select=S,     data0=B, data1=A)
```

כאשר S=0, לפני השינוי NOT S=1 ולכן נבחר B; אחרי השינוי בחירה 0 מעבירה את B שחובר לכניסה 0. כאשר S=1, לפני השינוי NOT S=0 ולכן נבחר A; אחרי השינוי בחירה 1 מעבירה את A שחובר לכניסה 1. ההתנהגות זהה בכל מצב. ה־MUX השמאלי והמכפל אינם משתנים. אין חובה להשתמש במהפך שהתייתר; השיפור אינו דורש רכיב חדש.

ההשהיה לאחר שינוי החיבור היא 3+1.5+2.7=**7.2 ns**: שיפור של 0.1 ns. זהו שיפור מוכח תחת מגבלת מלאי של מכפל אחד וללא הוספת רכיבים, ולא הוכחת מינימום לכל ארכיטקטורה אפשרית. כלים יכולים לעיתים לספוג היפוך בבחירת MUX גם בזמן מיפוי; כאן עובדים במודל הרכיבים הנתון.

**חלופה מהירה יותר, רק אם מותר להוסיף עותק של מכפל:** נחשב את הפונקציה לפי S. אם S=0, נבחרים C ו־B ולכן התוצאה BC. אם S=1, נבחרים D ו־A ולכן התוצאה AD. לכן ניתן לחשב במקביל P0=B×C ו־P1=A×D, ולהשתמש ב־MUX אחד במוצא: כניסה 0 מקבלת P0, כניסה 1 מקבלת P1, ו־S בוחר ביניהן.

בחלופה זו הכפל והקופסה השחורה עובדים במקביל, במקום שהכפל ימתין לבחירה. שתי המכפלות מוכנות לאחר 2.7 ns, ואות הבחירה לאחר 3 ns. המוצא מוכן לאחר max(2.7,3)+1.5=**4.5 ns**. זמן מסלול הנתונים דרך מכפל ו־MUX הוא 4.2 ns, וזמן מסלול הבחירה דרך קופסה שחורה ו־MUX הוא 4.5 ns. משתמשים בשני מכפלים במקום אחד וב־MUX אחד במקום שניים; יש מחיר משאבים ואפשרות ליותר פעילות מיתוג בכפלים. אין לקבוע שטח או הספק מדויקים מהתרשים.

הניסוח ״בהינתן אותם רכיבים״ עמום: אם הכוונה לאותו מלאי, אסור להציג הכפלת מכפלים כאילו לא הוספנו רכיב. אם הכוונה לאותם סוגי רכיבים ללא מגבלת כמות, חלופת 4.5 ns מתאימה. רצוי להציג את שתי הפרשנויות ולציין את המחיר במפורש. רוחב ה־MUX הסופי צריך להתאים לרוחב תוצאת הכפל; הנחת השהיית 1.5 ns מחייבת שהנתון חל גם על רוחב זה. אין כאן הוכחה ש־4.5 ns הוא מינימום מוחלט לכל מימוש אפשרי, במיוחד כשהקופסה השחורה אטומה.

אי אפשר פשוט להעביר MUX אחד אחרי המכפל בלי לחשב את שתי המכפלות או לשנות את התפקוד. הוספת רגיסטרי pipeline היא גם שינוי של משאבים ולטנטיות; היא אינה אותה מערכת קומבינטורית תחת מגבלת המלאי הנתונה. אין להפוך כניסות של הקופסה השחורה כדי לקבל את היפוך מוצאה בלי לדעת את הפונקציה שלה.

**בדיקות:** נבדקו 8,192 צירופי A,B,C,D בטווח 0..7 ו־S בשני המצבים. הפונקציה המקורית, החלפת כניסות ה־MUX והחלופה עם שני מכפלים נותנות אותו פלט. נבדקו גם חשבונות ההשהיה במודל max-plus עם שברים מדויקים. זו בדיקת פונקציה ומודל השהיות אידאלי; לא הורצו STA, סימולציית HDL, סימולציה פיזית או בדיקות גליצ׳ים.'''
en='''Interpret the small bubble on the right mux select as the given 0.1 ns inverter. Let S be the black-box output. Left mux is MUX(S,C,D); right mux is MUX(NOT S,A,B). Their outputs feed one multiplier in parallel. The crossover bridge is not a wire junction. If the bubble is not inversion, the interpretation and result change; preserve the source image.

Assume the given delays apply to all relevant paths, including mux select, and omit unspecified register clock-to-Q, wiring/load and output setup. No capture register is drawn, so this is structural combinational delay, not a guaranteed clock frequency or complete setup/hold result. Unknown black-box functionality prevents functional false-path analysis.

Data paths from A..D are 1.5+2.7=4.2 ns. From E/F through black box and left mux: 3+1.5+2.7=7.2 ns. Through the right select inverter: 3+0.1+1.5+2.7=7.3 ns, the structural critical path. The two mux delays are not added together; multiplier output arrival is max(4.5,4.6)+2.7.

Without adding components, swap A and B on the right mux and drive its select directly with S: MUX(NOT S,A,B)=MUX(S,B,A). This preserves the function and removes the inverter delay, giving 7.2 ns. This is a valid improvement, not an unconditional global minimum proof.

If adding a multiplier copy is allowed, the function is BC for S=0 and AD for S=1. Compute both products in parallel and select them with one output mux controlled by S. Delay becomes max(2.7,3)+1.5=4.5 ns. This uses two multipliers instead of one and assumes the 1.5 ns mux delay also applies to the product width. It is valid only if 'same components' means permitted component types, not the original inventory. Adding pipeline stages changes latency/resources. Neither exact area/power nor absolute optimum is established.

8,192 operand/select combinations verified equivalence of the three constructions. Exact-rational arrival-time checks confirm 7.3, 7.2 and 4.5 ns under the stated model. No physical STA or HDL timing simulation was performed.'''
q={
'id':'PREP-020','key':'critical-path-mux-multiplier','version':1,'created_on':'2026-09-27',
'category':'hardware','topic':'timing_and_optimization',
'topics':['hardware','logic-design','semi-conductors','vlsi','critical_path','propagation_delay','multiplexer','combinational_optimization','area_delay_tradeoff'],
'source_topic_tags':['hardware','logic-design','semi-conductors','vlsi'],
'added_topic_tags':['critical_path','propagation_delay','multiplexer','combinational_optimization','area_delay_tradeoff'],
'source_tags':['hardware','ibm','ceva','marvell','logic-design','semi-conductors','vlsi'],
'reported_companies':['IBM','CEVA','Marvell'],'source_company_badge':'Ceva',
'company_attribution_status':'reported_by_supplied_source_not_independently_verified',
'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'circuit_analysis','status':'in_review',
'solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
'authorship':'Source text and circuit transcribed; AI-assisted hints, interpretation, solution and exact-model checks.','reviewed_by':None,
'sources':[{'type':'user_supplied_image','path':'sources/prep-020.png','received_on':'2026-09-27'}],
'original_prompt':prompt,
'circuit_interpretation':{'registers':['A','B','C','D','E','F'],
 'black_box_inputs':['E','F'],'black_box_output':'S','left_mux':{'data0':'C','data1':'D','select':'S'},
 'right_mux':{'data0':'A','data1':'B','select':'NOT S'},'output':'product of the two mux outputs',
 'note':'The small right-select bubble is interpreted as inversion, consistent with the listed inverter delay; crossover bridge is not a junction.'},
'component_delays_ns':{'black_box':3,'multiplier':2.7,'mux':1.5,'inverter':0.1},
'translations':{'he':{'title':'מסלול קריטי במעגל MUX ומכפל ושיפור ההשהיה','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},
                'en':{'title':'Critical path and timing improvement in a mux/multiplier circuit','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
'prepared_hints':[{'id':f'PREP-020-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
'assumptions':['Right-select bubble is a NOT with 0.1 ns delay; function is BC if S=0, AD if S=1.',
 'MUX delay applies to data and select paths; wire/load and register delays are unspecified.',
 'Structural max-delay analysis; black-box false paths cannot be determined.',
 'No output capture register drawn; no complete fmax/setup/hold conclusion.',
 'Same component inventory and same allowed component types are separate interpretations.',
 'Two-multiplier option assumes output-width mux has the given delay; no pipeline latency changes.'],
'optimality':{'criterion':'Reduce structural combinational maximum delay while preserving functionality under stated resource assumptions',
 'result':'Original 7.3 ns; same-inventory simplification 7.2 ns; extra-multiplier speculative computation 4.5 ns.',
 'scope':'Explicit improvements, not a proof of globally minimum delay or physical area/power. Resource and bubble interpretation stated.'},
'edge_cases':['Select path can dominate data paths','MUXes are parallel','Inverted select swaps operand pairing',
 'A black-box input change may be a functional false path; function unknown','No receiver register given','Product width may exceed input width'],
'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_020.py',
 'method':'8,192 operand/select tuples compare original, swapped-mux and two-multiplier functions; exact-rational max-plus arrival checks.',
 'scope':'Conditional static function and given-delay model; no STA, HDL simulation or glitch analysis.'},
'media_assets':[{'type':'source_image','path':'sources/prep-020.png','description':'Original register/black-box/mux/multiplier diagram and delays; preserve for inversion and crossing interpretation.'}],
'interview_answer':'אבדוק מסלולים גם דרך כניסות הבחירה. בהנחת הבועה כמהפך, המסלול דרך הקופסה השחורה, המהפך, המוקס הימני והמכפל הוא 7.3 נ״ש. החלפת כניסות המוקס מסירה את הצורך במהפך ונותנת 7.2. אם מותר להוסיף מכפל, מחשבים BC ו־AD במקביל ובוחרים בסוף, לקבלת 4.5 נ״ש, במחיר מכפל נוסף.',
'common_mistakes':['Ignoring mux select timing','Adding parallel mux delays in series','Missing the right-select inversion',
 'Treating crossed wires as a junction','Duplicating the multiplier while claiming unchanged inventory',
 'Computing AC/BD instead of BC/AD under the inversion interpretation','Claiming a clock frequency without register timing constraints',
 'Assuming black-box inversion identities without knowing its function'],
'interview_relevance':{'priority':'high','label_he':'עדיפות גבוהה להכנה',
 'basis':'Core digital-hardware timing, mux behavior, debugging and function-preserving optimization relevant to the supplied System Chip Validation Intern role.',
 'assessment_scope':'Assistant preparation recommendation, not a prediction of the interview or a verified Marvell question.',
 'source_attribution':'Marvell appears among source tags; attribution unverified.',
 'learning_targets':['Trace data and select paths','Distinguish series and parallel arrival times','Preserve function when rewiring','State resource/latency assumptions']},
'related_question_ids':['HW-017','VHW-011','HW-004'],
'related_question_links':[
 {'id':'HW-017','path':'../example_question/hardware/timing_and_cdc/hw-017-setup-hold-calculation.md','relationship':'Register timing context; this source lacks capture timing.'},
 {'id':'VHW-011','path':'../verify_example_questions/hardware/timing_and_cdc/vhw-011-setup-hold.md','relationship':'Related delay and setup/hold fundamentals.'},
 {'id':'HW-004','path':'../example_question/hardware/combinational_circuits/hw-004-mux-tree-eight-inputs.md','relationship':'Related mux path-delay reasoning.'}],
'markdown_path':'questions/prep-020-critical-path-mux-multiplier.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');data=json.loads(s)
assert data['question_count']==19 and not any(a['id']==q['id'] for a in data['questions'])
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 19','"question_count": 20',1)
data=json.loads(s);assert len(data['questions'])==data['question_count']==20
p.write_text(s,encoding='utf-8')
md='# PREP-020 — מסלול קריטי במעגל MUX ומכפל\n\n## השאלה המקורית\n\n'+prompt
md+='\n\n![צילום השאלה והמעגל](../sources/prep-020.png)\n\n## קטגוריות וחברות\n\n'
md+='תגיות מקור: hardware, logic-design, semi-conductors, vlsi. סיווג נוסף: מסלול קריטי, זמני התפשטות, MUX, אופטימיזציה קומבינטורית ופשרות משאבים/השהיה. חברות לפי המקור: IBM, CEVA, Marvell. תווית ראשית: Ceva. השיוך מהצילום בלבד, ללא אימות עצמאי.\n\n'
md+='## רלוונטיות להכנה לראיון\n\n**עדיפות גבוהה להכנה.** זו הערכת חשיבות על בסיס יסודות החומרה ותיאור משרת הוולידציה שסופק, ולא תחזית לשאלות הראיון. מטרות: לזהות מסלולים דרך נתונים ובחירה, לחשב זמני הגעה, להסביר שינוי תפקודי שקול ולדייק באילוצי משאבים. Marvell מופיעה בתגיות, אך השיוך לא אומת.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
md+='\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[בדיקת פונקציה והשהיות](../checks/check_prep_020.py).\n\n'
md+='## תשובה קצרה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'
md+='\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
readme=root/'README.md';t=readme.read_text(encoding='utf-8')
preference='הנחיה נוספת של הראל: בעת קליטת שאלות חדשות, לציין במפורש אם הן בעדיפות גבוהה במיוחד להכנה לראיון System Chip Validation ב־Marvell, ולהסביר בקצרה מדוע. זו הערכת רלוונטיות לפי התפקיד, לא תחזית לשאלה שתישאל; תגיות חברות נשארות ייחוס לא מאומת מהמקור.\n\n'
if preference not in t:t=t.replace('## הקשר מקצועי מתוך התיאור שסופק',preference+'## הקשר מקצועי מתוך התיאור שסופק')
t+='\n- [PREP-020 — מסלול קריטי במעגל MUX ומכפל](questions/prep-020-critical-path-mux-multiplier.md) — **עדיפות גבוהה להכנה**; נשמרו הנוסח והתרשים, תגיות וחברות, שלושה רמזים, פתרון ובדיקות; תועדו פירוש ההיפוך ומגבלות משאבים.\n'
readme.write_text(t,encoding='utf-8')
assert (root/'sources/prep-020.png').exists()
assert he in (root/q['markdown_path']).read_text(encoding='utf-8')
print('PREP-020 saved; 20 questions. High-priority role assessment and standing preference preserved.')
