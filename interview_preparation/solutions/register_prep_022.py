"""Register random-permutation interview question without revealing in chat."""
import json
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
prompt='''נתון מספר N אי שלילי כלשהו. יש להדפיס פרמוטציה אקראית (סידור כלשהו) של כל המספרים מ־1 עד N בלי לחזור על מספר פעמיים. ממש בצורה היעילה ביותר.
לרשותך הפונקציה rand(m), המחזירה מספר שלם רנדומלי בין 1 ל־m.
א. ניתן לממש זאת בעזרת כל מבנה נתונים.
ב. יש לממש זאת בעזרת מערך בלבד.'''
ep='''Given a nonnegative integer N, print a random permutation of all integers from 1 through N without repeating a number, as efficiently as possible. You have rand(m), returning a random integer from 1 through m inclusive. (a) Any data structure may be used. (b) Use only an array.'''
hints=[
 'אם תגריל שוב ושוב מתוך 1 עד N, עלולים לצאת מספרים שכבר השתמשת בהם. איך אפשר להגריל רק מבין המספרים שעדיין זמינים?',
 'החזק במערך את המספרים שנותרו לבחירה. אחרי בחירה, אין צורך להזיז את כל האיברים כדי להסיר את המספר: החלפה עם איבר בקצה יכולה לעזור.',
 'חלק את המערך לחלק שכבר נקבע ולחלק שטרם נקבע. בכל צעד בחר באחידות אינדקס בחלק שנותר והחלף אותו עם התא הבא לקיבוע. שים לב ש־rand(m) מחזירה 1 עד m, בעוד אינדקסי פייתון מתחילים ב־0.'
]
eh=[
 'Repeatedly drawing from 1..N can yield duplicates. How could you draw only from values still available?',
 'Keep the remaining values in an array. Removing a selected value need not shift every element: an exchange with a boundary element can help.',
 'Partition the array into a fixed prefix and an unchosen suffix. Uniformly choose an index in that suffix and swap it into the next fixed slot. Convert the one-based rand(m) result to a zero-based index.'
]
he='''**הרעיון:** בתחילה כל המספרים זמינים. בכל שלב בוחרים באקראי אחד מהמספרים שנותרו, מקבעים אותו במקום הבא, וממשיכים רק עם השאר. זהו ערבוב Fisher–Yates.

**סעיף א:** מותר כל מבנה נתונים, ולכן מותר גם מערך. מערך מאפשר לבחור באינדקס אקראי ולהחליף שני איברים בזמן קבוע; הוא מספיק לפתרון מיטבי בזמן. אין דרישה להשתמש במבנה אחר מזה שבסעיף ב. אפשר לחשוב על המאגר כעל שק: בוחרים איבר, מחליפים אותו עם האיבר האחרון שעדיין בשק, ומקטינים את גודל השק ב־1. לא מוחקים מאמצע מערך ולא מזיזים את שאר האיברים. רשימה מקושרת רגילה אינה מאפשרת גישה לאינדקס אקראי בזמן קבוע.

**סעיף ב — מערך בלבד:** נאתחל arr=[1,2,...,N]. באיטרציה i התאים שלפני i כבר קבועים, והתאים i עד N−1 מכילים את המספרים שטרם נבחרו. נבחר j=i+rand(N−i)−1 ונחליף arr[i] עם arr[j]. עכשיו arr[i] קבוע ולא נוגעים בו שוב. בסוף מדפיסים את המערך. החלפת הקצה בתחילת החלק הפעיל שקולה לרעיון השק שבסעיף א.

**למה הנוסחה לאינדקס נכונה?** rand(N−i) מחזירה אחד מהמספרים 1..N−i. החסרת 1 נותנת היסט 0..N−i−1; הוספת i נותנת בדיוק את האינדקסים i..N−1. לדוגמה, אם N=5 ו־i=2, נגריל rand(3), ולכן j הוא 2, 3 או 4 בלבד. חייבים לאפשר גם j=i: זו בחירה חוקית שבה הערך הנוכחי נשאר במקומו.

**למה אין כפילויות?** מתחילים עם כל מספר פעם אחת, והחלפות לא יוצרות ולא מוחקות מספרים. בכל שלב מקבעים בדיוק ערך אחד מתוך החלק שנותר. אחרי N−1 בחירות נשאר מספר אחד, והוא כבר נמצא במקום האחרון. אין צורך להגריל אותו.

**למה ההתפלגות אחידה?** נוסח המקור אומר אקראי אך אינו מגדיר אחידות ועצמאות. כדי להבטיח שכל תמורה תתקבל באותה הסתברות, מניחים שכל קריאה ל־rand(m) מחזירה ערך אחיד ב־1..m, באופן בלתי תלוי בקריאות האחרות (די גם באחידות מותנית בכל ההיסטוריה). לכל תמורה מסוימת יש סיכוי 1/N לבחירת האיבר הראשון שלה, 1/(N−1) לבחירת השני מבין הנותרים וכן הלאה. לכן הסיכוי הכולל הוא 1/N!. אם המקור מוטה, עדיין לא יהיו כפילויות, אך אין הבטחה לתמורה אחידה.

**יעילות:** יצירת המערך, הערבוב וההדפסה עולים כל אחד O(N), לכן בסך הכול Θ(N) פעולות על איברים, בהנחת rand וגישה/החלפה במערך בזמן קבוע. זה אופטימלי בזמן כי צריך להפיק N מספרים. נדרשות max(N−1,0) קריאות ל־rand. המערך צורך Θ(N) מקום, והערבוב עצמו דורש O(1) זיכרון עזר מעבר למערך. אין לטעון O(1) זיכרון כולל או מינימום זיכרון מוחלט מבין כל שיטות הייצוג. ספירת זמן זו היא לפי איברים; עלות כתיבת הספרות בפועל תלויה גם באורך המספרים.

**מקרי קצה:** N=0 נותן פלט ריק ואינו קורא ל־rand(0). N=1 מדפיס 1 ללא הגרלה. קוד ההדפסה משתמש במערך יחיד ובמשתני אינדקס בלבד, בלי set או מילון.

**טעויות נפוצות:** הגרלה מחדש לאחר כפילויות היא פתרון עם זמן לא חסום במקרה הגרוע ותוחלת Θ(N log N) הגרלות תחת מקור אחיד; החלפת כל תא עם תא אקראי מכל המערך נותנת בדרך כלל התפלגות מוטה; מחיקה באמצע המערך עלולה להפוך את הפתרון לריבועי; אין לקרוא ל־rand(N−i−1) כשהחלק שנותר כולל N−i איברים.'''
en='''Use Fisher–Yates. Part (a) permits any structure, including an array, so the same optimal-time construction solves both parts. Model unchosen values as a bag: choose an index uniformly, exchange with a boundary element, and shrink the active range without shifting elements.

For part (b), initialize arr=[1,...,N]. At iteration i the prefix before i is fixed and the suffix i..N-1 holds unchosen values. Set j=i+rand(N-i)-1, swap arr[i] and arr[j], and advance i. Perform N-1 iterations; the final remaining value needs no draw. For N=5,i=2, rand(3) gives offsets 1..3, hence j=2,3,4. Allow j=i.

Swaps preserve the multiset and fixing one value per position prevents duplicates. Assuming uniform independent bounded draws (or conditional uniformity given prior draws), each particular permutation has probability 1/N × 1/(N-1) × ... × 1 = 1/N!. The supplied prompt does not explicitly promise uniformity or independence; those are stated assumptions for uniform output, not for avoiding duplicates.

Initialization, shuffle and output take Θ(N) item operations when bounded RNG and array access cost O(1), optimal because N items must be output. There are max(N-1,0) random calls. Total array storage is Θ(N), with O(1) extra shuffle storage. No absolute minimum-memory claim is made. Decimal-character I/O and arbitrary-precision costs are outside the item-operation model. N=0 gives an empty output, N=1 gives [1], and neither calls rand.

Repeated rejection of already-seen values requires Θ(N log N) expected draws and has no finite worst-case draw bound. Swapping each position with a random index from the whole array is generally biased. Deleting from the middle of an array can require O(N) shifts per choice. An ordinary linked list does not provide O(1) access to a uniformly selected index.'''
code=(root/'solutions/prep_022_random_permutation.py').read_text(encoding='utf-8')
he+='\n\n**מימוש פייתון:** הפרמטר rand הוא הפונקציה הנתונה בשאלה. random_permutation מחזירה את המערך, ו־print_random_permutation מדפיסה את איבריו.\n\n```python\n'+code+'```'
en+='\n\nPython implementation (rand is the supplied inclusive one-based function):\n\n```python\n'+code+'```'
q={
 'id':'PREP-022','key':'random-permutation-fisher-yates','version':1,'created_on':'2026-09-27',
 'category':'software','topic':'randomized_algorithms',
 'topics':['software','algorithms-software','randomized_algorithms','arrays','permutations','fisher_yates','complexity','uniform_sampling'],
 'source_topic_tags':['software','algorithms-software'],
 'added_topic_tags':['randomized_algorithms','arrays','permutations','fisher_yates','complexity','uniform_sampling'],
 'source_tags':['software','cisco','samsung','microsoft','applied-materials','apple','marvell','intel','algorithms-software','amazon','nvidia'],
 'reported_companies':['Cisco','Samsung','Microsoft','Applied Materials','Apple','Marvell','Intel','Amazon','NVIDIA'],
 'source_company_badge':'מארוול','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'algorithm_design',
 'status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון',
 'origin':'user_supplied_screenshot','authorship':'Source prompt transcribed; AI-assisted translations, hints, proposed solution and exhaustive model checks.','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-022.png','received_on':'2026-09-27'}],
 'original_prompt':prompt,
 'translations':{'he':{'title':'פרמוטציה אקראית ללא חזרות','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'Random permutation without duplicates','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-022-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['N is a nonnegative integer; values are 1..N inclusive.','rand(m) returns an integer in 1..m inclusive.','Uniform conditional draws are required for uniform permutations; not stated explicitly in source.','Complexity assumes O(1) bounded RNG and word-array operations; counts output items, not decimal characters.','Part (a) includes permission to use an array; solutions need not use different structures.'],
 'optimality':{'criterion':'Time to generate and print an explicit permutation of N values.','result':'Θ(N) time, Θ(N) total array space, O(1) extra shuffle space, max(N-1,0) RNG calls.','scope':'Output-size lower bound establishes time optimality under stated word-operation model; no universal memory or randomness-bit optimum claim.'},
 'edge_cases':['N=0','N=1','Self swaps must be allowed','Inclusive rand bounds vs zero-based indexing','Biased random source preserves uniqueness but not uniformity'],
 'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_022.py','method':'Exhaust all 5914 draw paths for N=0..7; verify exactly N! different outputs, preservation of 1..N and call bounds. Six larger deterministic boundary runs and invalid-input/contract tests.','scope':'Bijection of equiprobable draw paths to permutations, not a quality test of a physical or pseudorandom generator.'},
 'media_assets':[{'type':'source_image','path':'sources/prep-022.png','description':'Complete question and company/topic tags.'}],
 'solution_code_path':'solutions/prep_022_random_permutation.py',
 'interview_answer':'אמלא מערך ב־1 עד N. בכל מקום i אגריל אינדקס רק מתוך התאים שטרם נקבעו: j=i+rand(N−i)−1, ואחליף ביניהם. כך כל מספר נבחר פעם אחת וכל תמורה מתקבלת בהסתברות 1/N! בהנחת הגרלות אחידות. זמן Θ(N), מערך Θ(N) וזיכרון עזר O(1). אותו פתרון עונה על שני הסעיפים.',
 'common_mistakes':['Rejection sampling with duplicates','Biased swaps across full array','Off-by-one RNG mapping','Calling rand(0)','O(N) shifting deletion','Claiming O(1) total memory','Assuming random means uniform and independent without stating it'],
 'interview_relevance':{'priority':'medium','label_he':'רלוונטית לתרגול תכנות ואקראיות', 'basis':'Arrays, bounded random generation, avoidance of duplicate test scenarios and Python reasoning align with automation and validation in the supplied role.','assessment_scope':'Preparation judgment, not a claim about interview likelihood. Marvell tag/badge are source-reported and unverified.'},
 'related_question_ids':['PREP-019'],'markdown_path':'questions/prep-022-random-permutation.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');data=json.loads(s)
assert data['question_count']==21 and not any(x['id']==q['id'] for x in data['questions'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-6d61041d-ceca-4773-95d9-1612f023eea1.png',root/'sources/prep-022.png')
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
updated=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 21','"question_count": 22',1)
result=json.loads(updated);assert result['questions'][:-1]==data['questions'] and len(result['questions'])==22
p.write_text(updated,encoding='utf-8')
md='# PREP-022 — פרמוטציה אקראית ללא חזרות\n\n## השאלה המקורית\n\n'+prompt
md+='\n\n![צילום השאלה](../sources/prep-022.png)\n\n## קטגוריות וחברות\n\nתגיות מקור: software, algorithms-software. סיווג נוסף: אלגוריתמים אקראיים, מערכים, פרמוטציות, דגימה אחידה וסיבוכיות. חברות לפי הצילום: Cisco, Samsung, Microsoft, Applied Materials, Apple, Marvell, Intel, Amazon, NVIDIA. תווית ראשית: מארוול. השיוך לא אומת עצמאית.\n\n'
md+='## רלוונטיות להכנה\n\nעדיפות בינונית: רלוונטית לתרגול Python, מערכים ויצירת בדיקות אקראיות ללא חזרות. זו הערכת הכנה לפי תיאור התפקיד, לא תחזית לשאלה בראיון.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
md+='\n\n## הצעה לפתרון\n\n'+he
md+='\n\n## בדיקות\n\nנבדקו כל 5,914 מסלולי ההגרלה ל־N=0..7. בכל גודל התקבלו בדיוק N! תמורות שונות, ללא איברים חסרים או כפולים. נבדקו גם גבולות קריאות rand, שישה תרחישי קצה גדולים וקלטים לא תקינים. אין זו בדיקת איכות מקור האקראיות.\n\n[קוד בדיקה](../checks/check_prep_022.py) · [קוד פתרון](../solutions/prep_022_random_permutation.py)\n\n'
md+='## תשובה קצרה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-022 — פרמוטציה אקראית ללא חזרות](questions/prep-022-random-permutation.md) — מקור, תגיות וחברות, שלושה רמזים והצעה לפתרון לשני הסעיפים עם קוד ובדיקות ממצות לגדלים קטנים.\n',encoding='utf-8')
print('PREP-022 saved; 22 questions; prior question records preserved.')
