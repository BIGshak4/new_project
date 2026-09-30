"""Persist the array parity question, including impossible constant-time request."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prompt='''מערך בעל n איברים מכיל רק ספרות 0 עד 9.
ישנה רק ספרה אחת שמופיעה מספר אי זוגי של פעמים במערך, וכל שאר הספרות מופיעות מספר זוגי של פעמים.
כיצד ניתן לדעת מהי הספרה שמופיעה מס׳ אי זוגי של חזרות?
א. בסיבוכיות זמן o(n)
ב. בסיבוכיות זמן o(1)
הערה: הספרות יכולות להופיע בכל סדר שהוא, כולל חזרות (כלומר אין חשיבות לסדר הופעת הספרות במערך).'''
ep='''An array of n elements contains only digits 0 through 9. Exactly one digit occurs an odd number of times, and all other digits occur an even number of times. Find the odd-frequency digit: (a) in o(n) time; (b) in o(1) time. Digits can occur in any order with repetitions. The source uses lowercase o; the likely intended notation is big-O, discussed explicitly in the solution.'''
hints=[
 'נסה להתחיל מספירת הופעות: יש רק עשר ספרות אפשריות. איזה מידע על מספר ההופעות של כל ספרה באמת חשוב לשאלה?',
 'חפש פעולה על ביטים שבה שילוב של מספר עם עצמו מבטל אותו, ושינוי סדר השילוב אינו משנה את התוצאה. מה יישאר אחרי שכל הזוגות יתבטלו?',
 'שים לב שבסעיף ב׳ כתוב זמן קבוע, לא זיכרון קבוע. האם אפשר להבטיח תשובה נכונה בלי לקרוא תא כלשהו במערך? נסה לשנות רק את התא שלא נקרא, תוך שמירה על ההבטחה של השאלה.'
]
eh=[
 'Start by counting occurrences: only ten possible digits exist. Which aspect of each frequency matters?',
 'Find a bit operation where combining a value with itself cancels it and order does not matter. What remains after all pairs cancel?',
 'Part (b) asks for constant time, not constant space. Could an unread array cell change the answer while preserving the promise?'
]
he='''**קריאת הנוסח:** בצילום מופיע o קטן. לפי ההקשר נפרש את הבקשה כ־O(n) ו־O(1) במובן המקובל בשאלות ראיון, אך נשמור את המקור. אם הכוונה באמת ל־little-o(n), אז גם סעיף א בלתי אפשרי במודל מערך רגיל, בגלל חסם Ω(n). o(1) בזמן בדיד הוא דרישה חזקה אף יותר ואינו הפתרון המקובל. הסעיף השני מציין במפורש סיבוכיות זמן ולא מקום — אין להחליף את הדרישה בשקט.

**סעיף א — זמן Θ(n), מקום עזר O(1):** מבצעים XOR של כל איברי המערך, עם מצבר התחלתי 0. התכונות: x XOR x=0, x XOR 0=x, והפעולה אסוציאטיבית וקומוטטיבית. כל ספרה שמופיעה מספר זוגי של פעמים מתבטלת בזוגות. הספרה שמופיעה מספר אי־זוגי של פעמים משאירה עותק אחד, וזה הפלט. אין צורך שהזוגות יהיו צמודים או שהמערך יהיה ממוין. בפייתון:

```python
def odd_digit(values):
    result = 0
    for value in values:
        result ^= value
    return result
```

הסימן ^ הוא XOR ביטי, ו־result ^= value שקול ל־result = result ^ value. ^ אינו חזקה בפייתון. לדוגמה [2,7,2,4,7] מחזיר 4. גם הספרה 0 יכולה להיות התשובה: [0,6,6] מחזיר 0, ואין לפרש זאת כ״לא נמצא״. מספר ההופעות האי־זוגי יכול להיות 3,5,... ולא רק פעם אחת.

חלופה פשוטה: מערך של עשרה מונים או עשרה דגלי זוגיות. סורקים את הקלט, מעדכנים לפי הספרה ובסוף עוברים על עשר הספרות. זמן Θ(n)+O(10)=Θ(n), מקום O(10)=O(1) במודל מילות מכונה. עשרה דגלי זוגיות אינם גדלים עם n; מונים מדויקים דורשים O(log n) ביטים כל אחד אם מודדים ברמת ביטים. XOR משתמש במצבר בגודל קבוע כי כל הקלטים בני ארבעה ביטים. קוד odd_digit_checked עם מונים בודק גם תקינות תחום והבטחת יחידות, בניגוד לגרסת XOR המניחה את ההבטחה.

**סעיף ב — O(1) זמן אינו אפשרי לנתונים כפי שנמסרו.** העובדה שיש רק עשרה ערכים אפשריים אינה מבטלת את הצורך לקרוא n מקומות. הוכחה: קח n אי־זוגי ומערך שכולו אפסים. זהו קלט חוקי, והתשובה 0. נניח שהאלגוריתם לא קרא תא כלשהו. שנה רק אותו מ־0 ל־1. כעת יש n−1 אפסים (מספר זוגי) ו־1 אחד (אי־זוגי), ולכן גם זה קלט חוקי אבל התשובה 1. בכל התאים שהאלגוריתם קרא הערכים זהים, ולכן הוא לא יכול להבחין בין המקרים. מכאן שעל מסלול הקלט שכולו אפסים הוא חייב לקרוא את כל n התאים, אפילו אם הבחירה בתאים אדפטיבית. זה חסם Ω(n) בזמן תחת גישה לתא בודד בזמן קבוע. יחד עם XOR נקבל זמן מיטבי Θ(n).

יש להבחין בין זמן למקום: הפתרון הוא O(n) בזמן ו־O(1) במקום עזר. ייתכן שכוונת מחבר סעיף ב הייתה מקום קבוע, או בדיקה של היכולת לזהות דרישה בלתי אפשרית; אין דרך לדעת מהצילום ואין להציג השערה כעובדה. אם ניתן XOR מצטבר מראש, קריאת הסיכום היא O(1), אך בנייתו צורכת Θ(n) קריאות; זה מידע נוסף שאינו נתון. עיבוד מקבילי בחומרה עם כמות שערים הגדלה עם n הוא מודל שונה ואינו מוכיח זמן O(1) בתוכנה.

**מקרי קצה:** תחת ההבטחה n חייב להיות אי־זוגי ולפחות 1, כי סכום תדירויות זוגיות ותדירות אי־זוגית הוא אי־זוגי. מערך ריק או באורך זוגי אינו קלט חוקי לפי ההבטחה. אורך אי־זוגי לבדו לא מספיק להבטיח ספרה יחידה בתדירות אי־זוגית: [1,2,3] אינו עומד בהבטחה. בלי ההבטחה XOR לבדו אינו מזהה שגיאה ויכול להחזיר ספרה שלא מהווה תשובה תקפה. מותר לקרוא את הקלט בלי לשנות אותו.

**בדיקות:** לכל המערכים באורכים 1,3,5,7 מעל הספרות 0..3 נבדקה ההבטחה מול ספירה עצמאית; מקרים חוקיים הושוו לשני המימושים ומקרים לא חוקיים נדחו על ידי המימוש הבודק. נבדקו גם כל 1000 שלשות הספרות 0..9, כל עשר אפשרויות הספרה האי־זוגית, קלטים לא תקינים ודוגמאות לזוג הקלטים שבהוכחת התא שלא נקרא. החסם התחתון הוא הוכחה כללית, לא מסקנה סטטיסטית מבדיקות.'''
en='''The source prints lowercase o(n), o(1); likely intended as big-O interview notation, explicitly not silently corrected. Literal little-o(n) would also be impossible by the Ω(n) lower bound. Part (b) explicitly says time, not space.

Part (a): XOR all values starting from zero. Since x XOR x=0 and x XOR 0=x, and XOR is associative/commutative, all even-frequency digits cancel and the unique odd-frequency digit remains, regardless of ordering. Python uses ^= for XOR accumulation, not exponentiation. Example [2,7,2,4,7] returns 4; [0,6,6] returns 0. Odd frequency need not mean exactly once. Time Θ(n), constant auxiliary XOR state because values are digits. Ten frequency counters or ten parity flags are also linear-time/constant-word-space alternatives; exact counters grow in bit length, whereas parity flags do not. The checked implementation validates values and the promise; the XOR version assumes them.

Part (b), constant time, is impossible for an ordinary unsummarized array with constant-time single-cell access. For odd n, the all-zero array is valid with answer zero. If any cell remains unread, changing only that cell to one produces another valid input: n-1 zeroes and one one, answer one. All observations are identical, so any always-correct algorithm must inspect all n cells on this path, even with adaptive probing. Hence Ω(n), and the XOR solution is time-optimal. A constant alphabet limits state, not necessary input reads. Constant-space may have been intended or the impossibility may be deliberate; neither speculation is established by the source. A precomputed XOR summary supports constant-time lookup but requires linear preprocessing and additional input assumptions. Parallel hardware is a different model.

Valid input length is odd and positive, although odd length alone does not establish the promise (e.g. [1,2,3]). Without the promise XOR does not validate its own result. All arrays of lengths 1,3,5,7 over digits 0..3 were checked against independent counts, plus all 1000 triples of digits 0..9, all ten target digits, invalid inputs and unread-cell witness examples. The lower bound is mathematical, not inferred from the tests.'''
q={
 'id':'PREP-027','key':'unique-odd-frequency-digit','version':1,'created_on':'2026-09-28','category':'software','topic':'bit_manipulation',
 'topics':['software','arrays','bit_manipulation','xor','parity','complexity','lower_bounds'],
 'source_topic_tags':[],'added_topic_tags':['software','arrays','bit_manipulation','xor','parity','complexity','lower_bounds'],'source_tags':[],
 'reported_companies':[],'source_company_badge':None,'company_attribution_status':'no_company_information_in_supplied_image',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'algorithm_design_and_feasibility','status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
 'authorship':'Prompt transcribed with original complexity notation; AI-assisted translations, hints, proof and verified code.','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-027.png','received_on':'2026-09-28'}],'original_prompt':prompt,
 'translations':{'he':{'title':'מציאת הספרה שמופיעה מספר אי־זוגי של פעמים','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'Find the unique odd-frequency digit','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-027-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Exactly one digit has odd frequency; every value is in 0..9.','Ordinary array access, no precomputed aggregate or unbounded-width primitive.','Likely intended big-O notation distinguished from literal lowercase little-o.','Part (b) asks time; no silent replacement with space.'],
 'optimality':{'criterion':'Worst-case work to identify odd-frequency digit from an unsummarized arbitrary-order array.','result':'Θ(n) time and O(1) auxiliary state with XOR; O(1) time impossible.','proof':'All-zero valid odd-length array versus one unread zero replaced by one: indistinguishable observations, distinct valid answers.','scope':'Single-cell RAM access and exact correctness; preprocessing/parallel-hardware assumptions would change the model.'},
 'edge_cases':['Odd digit is zero','Single element','Odd count greater than one','Unsorted interleaving','Empty/even-length arrays violate promise','Several odd-frequency digits','Out-of-range/noninteger elements'],
 'verification':{'status':'passed','checked_on':'2026-09-28','script_path':'checks/check_prep_027.py','method':'All odd lengths 1..7 over alphabet 0..3, all ten-digit triples, target-digit and invalid-input checks, unread-cell witness examples.'},
 'solution_code_path':'solutions/prep_027_odd_digit.py','media_assets':[{'type':'source_image','path':'sources/prep-027.png','description':'Complete supplied source including both time requirements and arbitrary-order note; no company tags shown.'}],
 'interview_answer':'אעבור על המערך עם XOR מצטבר. זוגות מתבטלים והספרה בעלת מספר ההופעות האי־זוגי נשארת. זמן Θ(n) וזיכרון עזר O(1). סעיף ב כפי שנכתב, זמן O(1), אינו אפשרי בלי מידע נוסף: תא שלא נקרא יכול לשנות את התשובה גם תוך שמירה על ההבטחה.',
 'common_mistakes':['Confusing O(1) time with O(1) space','Assuming bounded alphabet eliminates input scan','Assuming equal values must be adjacent','Treating zero as missing result','Assuming odd-frequency means singleton','Using XOR as an input validator','Ignoring the lowercase o notation'],
 'interview_relevance':{'priority':'high','label_he':'עדיפות גבוהה לתרגול קצר','basis':'Simple array traversal, XOR/parity, Python coding and checking feasibility/edge cases connect software reasoning to digital-hardware foundations in the supplied validation role.','recommendation':'Worth a short focused attempt (roughly 10–15 minutes); no advanced data-structures course needed for the intended concepts.','assessment_scope':'Preparation judgment based on supplied job description, not a prediction of interview content.'},
 'related_question_ids':['PREP-023'],'markdown_path':'questions/prep-027-unique-odd-frequency-digit.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
assert before['question_count']==26 and not any(x['id']==q['id'] for x in before['questions'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-624a2dc6-eb23-44fa-9327-d8f66e2df2d7.png',root/'sources/prep-027.png')
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 26','"question_count": 27',1)
after=json.loads(s);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==27
p.write_text(s,encoding='utf-8')
md='# PREP-027 — הספרה בעלת מספר ההופעות האי־זוגי\n\n## השאלה המקורית\n\n'+prompt+'\n\n![צילום המקור](../sources/prep-027.png)\n\n'
md+='## קטגוריות וחברות\n\nאין תגיות נושא או חברות בתמונה. הסיווג שלנו: תוכנה, מערכים, XOR, זוגיות, פעולות ביטיות וסיבוכיות. אין להסיק שיוך לחברה מהמשרה שלקראתה מתכוננים.\n\n## רלוונטיות להכנה\n\nעדיפות גבוהה לתרגול קצר של 10–15 דקות: יסודות קוד וביטים ובדיקת דרישות. זו הערכת הכנה לפי תיאור התפקיד שסופק, לא תחזית לשאלות הראיון.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[קוד](../solutions/prep_027_odd_digit.py) · [בדיקות](../checks/check_prep_027.py)\n\n## תשובה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en+'\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-027 — הספרה בעלת מספר ההופעות האי־זוגי](questions/prep-027-unique-odd-frequency-digit.md) — מקור, שלושה רמזים, XOR והוכחת חסם תחתון; נוסח דרישות הזמן נשמר במפורש. עדיפות גבוהה לתרגול קצר.\n',encoding='utf-8')
print('PREP-027 saved; 27 questions; original time requirements preserved, lower bound documented, no invented company attribution.')
