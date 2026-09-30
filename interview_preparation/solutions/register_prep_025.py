"""Save the two-crystal-ball minimax exercise without revealing its answer."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prompt='''אתה עומד למרגלות גורד שחקים ובו 100 קומות. ברשותך 2 כדורי בדולח. עליך למצוא את מספר הקומה הנמוכה ביותר שאם זורקים ממנה כדור בדולח, הוא נשבר. עליך לעשות זאת במספר הזריקות המינימלי האפשרי (עבור המקרה הגרוע ביותר).'''
ep='You stand at a 100-floor skyscraper with two crystal balls. Find the lowest floor from which a dropped ball breaks, using the minimum possible number of drops in the worst case.'
hints=[
 'מה משתנה אחרי שהכדור הראשון נשבר? עם כדור אחד בלבד, איך תוכל לבדוק טווח קומות בלי להסתכן בכך שתאבד את היכולת למצוא את הקומה המדויקת?',
 'אם תקפוץ כל פעם באותו מספר קומות, מה יקרה למספר הזריקות הכולל כשהכדור הראשון יישבר מאוחר? איך כדאי לשנות את גודל הקפיצות כדי לפצות על הזריקות שכבר נוצלו?',
 'נניח שמותרות לכל היותר k זריקות. אם הכדור הראשון נשבר בבדיקה הראשונה, נשארות k−1 בדיקות לכדור השני. ואם הוא נשבר בבדיקה השנייה, נשארות k−2. נסה לבנות קפיצות הולכות וקטנות ולסכם כמה קומות אפשר לכסות.'
]
eh=[
 'After the first ball breaks, how can the remaining ball search an interval without losing the ability to identify the exact threshold?',
 'With equal floor gaps, late breakage increases total drops already spent. How could you adjust later gaps to compensate?',
 'Suppose the worst-case budget is k drops. Breakage on the first drop leaves k-1 tests, and on the second leaves k-2. Try decreasing gaps and sum the covered floors.'
]
he='''**התשובה: 14 זריקות במקרה הגרוע.** נניח ששני הכדורים זהים, שקיימת התנהגות מונוטונית ודטרמיניסטית: כדור נשבר החל מקומה F ומעלה, ומתחתיה אינו נשבר; כדור שלא נשבר ניתן לשימוש חוזר. קומה 0 בטוחה. המקור משתמע כמבטיח קומה שוברת בטווח 1..100; הפתרון שלהלן מטפל גם במקרה שבו אין קומה כזאת, באמצעות ערך F=101.

**למה חיפוש בינארי רגיל אינו מתאים?** אם הכדור הראשון נשבר בקומה 50, נשאר כדור אחד לטווח שמתחת ל־50. כדי להיות בטוחים בזיהוי הקומה המדויקת, צריך לבדוק מלמטה למעלה: דילוג עם הכדור האחרון עלול לשבור אותו ולהשאיר כמה קומות שלא ניתן להבחין ביניהן.

**האסטרטגיה:** זורקים את הכדור הראשון בקומות 14, 27, 39, 50, 60, 69, 77, 84, 90, 95, 99, 100, כל עוד הוא לא נשבר. הקפיצות המתוכננות הן 14,13,12,11,...; בסוף מקטינים את הקפיצה כדי לא לעבור את קומה 100. כשהכדור הראשון נשבר, לוקחים את השני ומתחילים קומה אחת מעל הקומה האחרונה שכבר נבדקה ונמצאה בטוחה. עולים קומה־קומה, עד שהכדור השני נשבר או שמגיעים לקומה שלפני זו שכבר ידוע ששברה את הכדור הראשון. אין לזרוק שוב מהקומה שכבר ידוע ששוברת.

**למה דווקא מקטינים את הקפיצה?** כל זריקה נוספת של הכדור הראשון צורכת חלק מהתקציב, ולכן צריך להשאיר פחות קומות לבדיקה עם הכדור השני. אם רוצים לכל היותר k זריקות:
* בבדיקה הראשונה מותר להיבחן בקומה k: אם נשבר, נשארות k−1 קומות לבדיקה ו־k−1 זריקות.
* אחרי הישרדות, בבדיקה השנייה מותר להתקדם לכל היותר k−1 קומות: אם נשבר, נשארו k−2 קומות לא ידועות בין שתי הבדיקות ו־k−2 זריקות.
* כך הלאה: המרווחים המקסימליים הם k,k−1,...,1.

דוגמאות: אם נשבר ב־14, משתמשים בכדור השני בקומות 1..13: לכל היותר 1+13=14 זריקות. אם שרד ב־14 ונשבר ב־27, בודקים 15..26: לכל היותר 2+12=14. אם נשבר ב־39 אחרי שתי הישרדות, בודקים 28..38: לכל היותר 3+11=14. אם הכדור השני נשבר מוקדם, עוצרים מוקדם. אם כל הקומות הפנימיות בטוחות, הקומה ששברה את הכדור הראשון היא התשובה, ואין צורך בזריקה נוספת.

**הוכחת מינימום:** עם כדור אחד ו־t זריקות אפשר לבדוק לכל היותר t קומות לא ידועות. לכן עם שני כדורים ו־k זריקות אפשר לכסות לכל היותר k+(k−1)+...+1=k(k+1)/2 קומות. באורח פורמלי, נסמן C(e,k) כמספר הקומות המקסימלי עם e כדורים ו־k זריקות: הזריקה הראשונה מחלקת לענף שבירה עם e−1 כדורים ולענף הישרדות עם e כדורים, ולכן C(e,k)=C(e−1,k−1)+1+C(e,k−1), עם C(1,k)=k ו־C(e,0)=0. מכאן C(2,k)=k(k+1)/2. עבור 13 זריקות הכיסוי 91 בלבד; עבור 14 הוא 105, מספיק ל־100. לכן 14 הוא מינימום, והאסטרטגיה משיגה אותו.

אם מניחים מראש שקומה 100 שוברת בוודאות, יש 100 ערכי סף אפשריים ולא 101. עדיין 13 זריקות אינן מספיקות: עץ אסטרטגיה עם שני כדורים ו־k זריקות יכול להבחין לכל היותר ב־1+k(k+1)/2 ערכי סף, ולכן 13 מאפשרות לכל היותר 92 אפשרויות <100. כך מסקנת המינימום אינה תלויה באפשרות ״אין שבירה״; ההבחנה הזו מונעת שגיאת off-by-one בהוכחה.

**הכללה:** עבור N קומות כשמותר גם שאין שבירה, מספר הזריקות המינימלי הוא המספר השלם הקטן ביותר k שעבורו k(k+1)/2≥N, כלומר ceil((sqrt(1+8N)−1)/2). בקוד נוח לחשב בסכום שלמים כדי להימנע מעיגול float. זו אופטימליות של מספר ניסויים פיזיים במקרה הגרוע, לא של תוחלת בהנחת הסתברות כלשהי. חישוב האסטרטגיה שונה ממספר הזריקות.

**בדיקה:** סימולציה לכל סף אפשרי, כולל ללא שבירה, לכל N=0..200; התוצאה הושוותה לתכנון דינמי minimax עצמאי. נבדק שאין שימוש חוזר בכדור שבור, שאין חריגה מהבניין, שהסף מוחזר בדיוק ושמספר הזריקות המקסימלי שווה לאופטימום. עבור 100 קומות כל 101 האפשרויות נפתרות בעד 14 זריקות, ויש מקרים הדורשים 14. שמירת trace בקוד היא לצורך המחשה ובדיקה, ואינה דרישה של האסטרטגיה.'''
en='''Answer: 14 drops in the worst case. Assume identical reusable-until-broken balls, deterministic monotone breakage at threshold F, ground level 0 safe. The source implies a threshold within 1..100; the construction also handles no breakage, represented by F=101.

Drop the first ball at floors 14,27,39,50,60,69,77,84,90,95,99,100 until it breaks. Intended gaps decrease as 14,13,12,...; cap the final floor at 100. After a break, scan with the second ball from one above the last known-safe floor to one below the known-breaking floor. Stop at its first break; if all interior floors survive, infer the already-known upper threshold without retesting it. A break at 14 costs at most 1+13=14 drops; at 27, at most 2+12=14; at 39, at most 3+11=14. Binary search is inappropriate after a break because only one ball remains.

Optimality: with one ball and t drops, cover at most t unknown floors. General coverage recurrence C(e,k)=C(e-1,k-1)+1+C(e,k-1) yields C(2,k)=k(k+1)/2. Thirteen drops cover only 91 floors, fourteen cover 105. Equivalently, the number of distinguishable threshold cases is at most 1+k(k+1)/2. Even if floor 100 is guaranteed breaking, 13 drops distinguish at most 92 cases, fewer than the 100 possibilities, so 14 remains necessary. The strategy attains this bound.

For N floors with a possible no-break case, minimum k is the least integer satisfying k(k+1)/2>=N, or ceil((sqrt(1+8N)-1)/2). Integer accumulation avoids floating-point rounding. The objective is worst-case physical drops, not expected drops under a prior distribution or minimum CPU time. All thresholds for N=0..200 were simulated and compared with independent minimax DP, validating exact answers, legal floors, no broken-ball reuse and attained worst-case bounds. Trace storage is only for teaching/testing.'''
q={
 'id':'PREP-025','key':'two-crystal-balls-hundred-floors','version':1,'created_on':'2026-09-28',
 'category':'logic','topic':'minimax_search','topics':['logic','worst_case_analysis','minimax_search','triangular_numbers','dynamic_programming','threshold_search'],
 'source_topic_tags':['logic'],'added_topic_tags':['worst_case_analysis','minimax_search','triangular_numbers','dynamic_programming','threshold_search'],
 'source_tags':['nvidia','applied-materials','logic','intel'],'reported_companies':['NVIDIA','Applied Materials','Intel'],'source_company_badge':'אינטל',
 'company_attribution_status':'reported_by_supplied_source_not_independently_verified','difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'puzzle',
 'status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
 'authorship':'Supplied prompt transcribed; AI-assisted translations, hints, minimax proof and tested simulation.','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-025.png','received_on':'2026-09-28'}],'original_prompt':prompt,
 'translations':{'he':{'title':'שני כדורי בדולח ו־100 קומות','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'Two crystal balls and 100 floors','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-025-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Identical balls with monotone deterministic break threshold.','An unbroken ball can be reused; a broken ball cannot.','Ground floor 0 safe; floors 1..100.','Source implies a breaking floor exists; solution also handles no breaking floor.','Optimize worst-case number of drops, not expected count.'],
 'optimality':{'criterion':'Worst-case physical drops with two balls.','result':'14, attained by shrinking gaps; 13 cannot distinguish all possible thresholds.','proof':'C(2,k)=k(k+1)/2 unknown floors or C(2,k)+1 threshold cases; 91/92 insufficient, 105/106 sufficient.','scope':'Deterministic monotone threshold and identical reusable balls; guaranteed-break variant also needs 14 for 100 floors.'},
 'edge_cases':['Breaks at floor 1','Breaks at floor 100','No breaking floor','Break exactly at a first-ball test','Final gap capped at top','Never retest known-breaking floor','Last remaining ball must scan safely'],
 'verification':{'status':'passed','checked_on':'2026-09-28','script_path':'checks/check_prep_025.py','method':'All thresholds for each N=0..200, independent minimax DP, legal ball lifecycle and exact 100-floor schedule.'},
 'solution_code_path':'solutions/prep_025_two_crystal_balls.py','media_assets':[{'type':'source_image','path':'sources/prep-025.png','description':'Full original question and source tags.'}],
 'interview_answer':'המינימום הוא 14. אבדוק עם הכדור הראשון בקפיצות 14,13,12,... קומות; אחרי שבירה אסרוק עם השני מהקומה הבטוחה האחרונה ומעלה. כך הזריקות שכבר נוצלו והסריקה שנותרה מסתכמות בעד 14. 13 זריקות מכסות רק 91 קומות, ו־14 מכסות 105, ולכן 14 מספיק וגם הכרחי.',
 'common_mistakes':['Using ordinary binary search with two consumable balls','Fixed gaps without counting previous drops','Confusing expected and worst-case cost','Retesting a known-breaking floor','Ignoring monotonicity or starting assumptions','Claiming 13 suffices from approximate square root','Off-by-one in possible threshold states'],
 'interview_relevance':{'priority':'medium','label_he':'תרגול מועיל של אסטרטגיית בדיקה ומקרה גרוע','basis':'Reasoning about experiments with limited resources and proving worst-case bounds supports problem solving; less directly tied to role than Python, digital logic and debugging.','assessment_scope':'Preparation judgment based on supplied role, not an interview prediction.'},
 'related_question_ids':[],'markdown_path':'questions/prep-025-two-crystal-balls.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
assert before['question_count']==24 and not any(x['id']==q['id'] for x in before['questions'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-da2209df-df51-44f5-aa56-a17a7a48223d.png',root/'sources/prep-025.png')
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 24','"question_count": 25',1)
after=json.loads(s);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==25
p.write_text(s,encoding='utf-8')
md='# PREP-025 — שני כדורי בדולח ו־100 קומות\n\n## השאלה המקורית\n\n'+prompt+'\n\n![צילום המקור](../sources/prep-025.png)\n\n'
md+='## קטגוריות וחברות\n\nתגית מקור: logic. סיווג נוסף: ניתוח מקרה גרוע, חיפוש סף, minimax, מספרים משולשיים ותכנון דינמי. חברות לפי המקור: NVIDIA, Applied Materials, Intel. תווית ראשית: אינטל. השיוך לא אומת עצמאית.\n\n## רלוונטיות להכנה\n\nעדיפות בינונית: תרגול ניסויים במשאבים מוגבלים ומקרה גרוע; הערכת הכנה, לא תחזית לראיון.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[קוד הסימולציה](../solutions/prep_025_two_crystal_balls.py) · [בדיקות](../checks/check_prep_025.py)\n\n## תשובה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-025 — שני כדורי בדולח ו־100 קומות](questions/prep-025-two-crystal-balls.md) — מקור, חברות, שלושה רמזים, אסטרטגיה והוכחת מינימום עם בדיקות לכל סף.\n',encoding='utf-8')
print('PREP-025 saved; 25 questions; prior records unchanged.')
