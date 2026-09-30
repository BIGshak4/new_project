"""Register ladder counting source, gradual hints and exact solutions."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prompt='חרגול מטפס על סולם, ועולה בכל פעם שלב אחד או שניים. בכמה דרכים שונות יכול החרגול להגיע לשלב ה־n?'
ep='A grasshopper climbs a ladder, ascending one or two rungs at a time. In how many different ways can it reach rung n?'
hints=[
 'נסה לרשום את כל הדרכים להגיע לשלב 2 ואז לשלב 3. דרך היא סדרת קפיצות: האם קפיצה של 1 ואחריה 2 היא אותה דרך כמו 2 ואחריה 1?',
 'הסתכל דווקא על הקפיצה האחרונה בדרך לשלב n: מאיזה שלב החרגול היה יכול להגיע, אם מותר לקפוץ רק 1 או 2?',
 'חלק את הדרכים לשתי קבוצות לפי גודל הקפיצה האחרונה. אם כבר ידוע כמה דרכים יש להגיע לכל אחד משני השלבים הקודמים, איך תקבל את מספר הדרכים לשלב הנוכחי? קבע גם את מקרי הבסיס.'
]
eh=[
 'List the paths to rung 2 and rung 3. Is jumping 1 then 2 the same path as jumping 2 then 1?',
 'Consider the final jump into rung n. From which rung can it originate if jumps have length 1 or 2?',
 'Partition paths by final jump size. Combine the counts for the two possible previous rungs, and specify the base cases.'
]
he='''**הנחות:** החרגול מתחיל על הקרקע, כלומר בשלב 0. n הוא מספר שלם אי־שלילי, ומגיעים בדיוק לשלב n באמצעות עליות של 1 או 2 בלבד. סדר הקפיצות חשוב: (1,2) ו־(2,1) הן דרכים שונות. המקור לא מציין במפורש את שלב ההתחלה; אם מתחילים בשלב 1, צריך לספור מרחק n−1 במקום n. אין מגבלת יעילות מפורשת בשאלה.

**דוגמאות קטנות:** לשלב 1 יש דרך אחת: (1). לשלב 2 יש שתיים: (1,1), (2). לשלב 3 יש שלוש: (1,1,1), (1,2), (2,1). לשלב 4 יש חמש: (1,1,1,1), (1,1,2), (1,2,1), (2,1,1), (2,2).

**הרעיון:** נסמן W(n) כמספר הדרכים לשלב n. הקפיצה האחרונה היא או קפיצה של 1 מהשלב n−1, או קפיצה של 2 מהשלב n−2. לכל דרך שמגיעה ל־n−1 אפשר להוסיף קפיצה אחת של 1, ולכל דרך שמגיעה ל־n−2 אפשר להוסיף קפיצה אחת של 2. שתי הקבוצות זרות, משום שהקפיצה האחרונה שלהן שונה, והן כוללות את כל הדרכים האפשריות. לכן מחברים ולא מכפילים:

W(n)=W(n−1)+W(n−2), עבור n≥2.

מקרי הבסיס: W(0)=1 — דרך ריקה אחת, כלומר לא לקפוץ; W(1)=1. מכאן W(2)=2, W(3)=3, W(4)=5, W(5)=8. הגדרת W(0)=1 אינה אומרת שקפצנו קפיצה: היא מאפשרת לספור נכון את הדרך היחידה (2) לשלב 2. עבור n=0 התשובה היא אחת לפי הגדרת המסלול הריק.

**התשובה הכללית:** W(n)=F(n+1), כאשר F(0)=0 ו־F(1)=1 הם מספרי פיבונאצ׳י. לכן זו נוסחת נסיגה, ולא מספר יחיד שאפשר לתת בלי ערך n. דרך ההגעה לנסיגה חשובה יותר משם הסדרה.

**מימוש ברור ויעיל לראיון:** מחשבים מלמטה למעלה, ושומרים רק את שני הערכים האחרונים. מתחילים previous=W(0)=1,current=W(1)=1; לכל שלב מ־2 ועד n מחליפים בו־זמנית ל־previous=current,current=previous+current. ההשמה המקבילית בפייתון משתמשת בשני הערכים הישנים לפני ההחלפה. הפונקציה count_ways בקובץ הקוד מממשת זאת. זמן O(n) פעולות חיבור ומספר קבוע של משתני ספירה; אין צורך במערך של כל התוצאות. רקורסיה נאיבית מחשבת שוב את אותן תת־בעיות ועולה בזמן מעריכי; memoization מצמצם לחישוב לכל שלב אך דורש אחסון O(n) ערכים ועומק קריאות עד O(n).

**אופטימליות ודיוק:** O(n) הוא פתרון בסיסי יעיל וברור, אבל אינו מינימום מוחלט במספר פעולות אריתמטיות. אם n גדול מאוד אפשר להשתמש בהכפלה מהירה של פיבונאצ׳י: כאשר a=F(k),b=F(k+1), אז F(2k)=a(2b−a), ו־F(2k+1)=a²+b². סריקת הביטים של n+1 ובניית הזוג המתאים נותנות O(log n) פעולות אריתמטיות; count_ways_fast מממשת זאת בדיוק במספרים שלמים. הזהויות נובעות מנוסחת החיבור F(p+q)=F(p−1)F(q)+F(p)F(q+1), ובפרט F(k−1)=b−a. קוד ההכפלה אינו דרוש כדי להסביר את החידה.

בפייתון ערך התשובה מכיל Θ(n) ביטים עבור n גדול. לכן שני משתני ספירה אינם O(1) ביטים, ופעולות אריתמטיות עליהם אינן זמן קבוע. הפתרון הלינארי מבצע O(n) חיבורים, אך עלות הביטים המצטברת היא O(n²) במודל חיבור לינארי; גרסת ההכפלה מבצעת O(log n) פעולות על מספרים הולכים וגדלים ולא מבטיחה זמן פיזי O(log n). סריקת bin בקוד ההכפלה משתמשת בנוסף ב־O(log n) תווי אינדקס. אין טענת מינימום זמן פיזי או מספר הוראות. לא משתמשים בנוסחת פיבונאצ׳י בנקודה צפה בלי טיפול בשגיאות עיגול.

**נוסחה קומבינטורית נוספת לבדיקה:** אם יש k קפיצות של 2, יש n−2k קפיצות של 1, ובסך הכול n−k קפיצות. בוחרים את k המקומות לקפיצות של 2 מתוך n−k, ולכן W(n)=Σ C(n−k,k), עבור k=0..⌊n/2⌋. זו חלופה נכונה, אבל הנסיגה פשוטה יותר להסבר.

**בדיקות:** נמנו כל המסלולים ל־n=0..16 ונבדקו ייחודיות והגעה מדויקת; שני המימושים הושוו לסכום הבינומי לכל n=0..300 וביניהם גם ל־n=1000,10000. נבדקו קלטים לא תקינים.'''
en='''Assume the grasshopper starts at ground level 0, n is a nonnegative integer, and paths are ordered sequences of upward jumps of size 1 or 2 reaching exactly n. Starting on rung 1 would instead require counting distance n-1. The source leaves the starting point implicit. Order matters: (1,2) and (2,1) differ.

Let W(n) count paths. Partition them by final jump: append a 1-jump to every path to n-1, or a 2-jump to every path to n-2. These classes are disjoint and exhaustive, hence W(n)=W(n-1)+W(n-2), n>=2. Base values are W(0)=1 (the empty path) and W(1)=1. Counts for n=0..5 are 1,1,2,3,5,8. Thus W(n)=F(n+1), with F(0)=0,F(1)=1. There is no single numerical answer until n is given.

The recommended basic interview implementation iterates bottom-up keeping two previous counts: O(n) additions, a constant number of count variables, no full DP array. Naive recursion repeats subproblems exponentially; memoization retains O(n) counts and can use O(n) call depth. Linear iteration is not an absolute arithmetic-operation optimum: fast doubling uses F(2k)=a(2b-a), F(2k+1)=a²+b² for a=F(k),b=F(k+1). Scanning the bits of n+1 produces F(n+1) in O(log n) arithmetic operations, implemented as count_ways_fast. These identities follow from the Fibonacci addition identity.

Exact result size is Θ(n) bits, so arbitrary-precision operations are not constant time and a constant number of big integers is not constant bit-space. Linear iteration costs O(n²) bit operations under linear-cost addition; fast doubling's bit cost depends on multiplication, not merely its O(log n) operation count. The implementation's binary index string uses O(log n) characters. No global physical-time optimum is claimed.

Independent combinatorial formula: W(n)=sum_{k=0..floor(n/2)} C(n-k,k), choosing positions of k double jumps among n-k total jumps. Exhaustive path enumeration for n=0..16, independent binomial comparisons for n=0..300, and cross-checks at n=1000/10000 passed, plus invalid-input checks.'''
code=(root/'solutions/prep_024_grasshopper_stairs.py').read_text(encoding='utf-8')
q={
 'id':'PREP-024','key':'grasshopper-ladder-one-two-steps','version':1,'created_on':'2026-09-28',
 'category':'logic','topic':'counting_and_dynamic_programming',
 'topics':['logic','combinatorics','recurrence','recursion','dynamic_programming','fibonacci'],
 'source_topic_tags':['logic'],'added_topic_tags':['combinatorics','recurrence','recursion','dynamic_programming','fibonacci'],
 'source_tags':['logic','apple','marvell','mellanox','intel'],
 'reported_companies':['Apple','Marvell','Mellanox','Intel'],'source_company_badge':'אינטל',
 'company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'counting_problem','status':'in_review',
 'solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
 'authorship':'Prompt transcribed from supplied image; AI-assisted translation, hints, mathematical solution and tested code.','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-024.png','received_on':'2026-09-28'}],
 'original_prompt':prompt,
 'translations':{'he':{'title':'חרגול על סולם — קפיצות של שלב אחד או שניים','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he+'\n\n```python\n'+code+'```'},'en':{'title':'Grasshopper climbing one or two rungs','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en+'\n\n```python\n'+code+'```'}},
 'prepared_hints':[{'id':f'PREP-024-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Start at ground/rung zero; initial position unspecified in source.','n is a nonnegative integer.','Ordered 1/2-jump sequences count as different paths; upward motion only and exact arrival.','The empty path counts once at n=0.','Operation-count complexity differs from bit complexity for exact large results.'],
 'optimality':{'criterion':'Exact count with clear recurrence and reduced storage; optional faster arithmetic-operation count.','result':'W(n)=F(n+1). Basic DP: O(n) additions and two count values; fast doubling: O(log n) arithmetic operations.','scope':'Linear DP is not claimed globally fastest; big-integer time/space depends on result length, Θ(n) bits.'},
 'edge_cases':['n=0 empty path','n=1','n=2','Order of jumps matters','Starting rung 1 instead of 0 shifts index','Negative or noninteger n','Large exact counts'],
 'verification':{'status':'passed','checked_on':'2026-09-28','script_path':'checks/check_prep_024.py','method':'Enumerate all paths for n=0..16; compare both implementations with binomial sum for n=0..300; cross-check n=1000/10000 and invalid input.'},
 'solution_code_path':'solutions/prep_024_grasshopper_stairs.py',
 'media_assets':[{'type':'source_image','path':'sources/prep-024.png','description':'Full original question and company/topic tags.'}],
 'interview_answer':'בהנחה שמתחילים בשלב 0, הקפיצה האחרונה לשלב n מגיעה מ־n−1 או מ־n−2. לכן W(n)=W(n−1)+W(n−2), עם W(0)=W(1)=1. זו F(n+1). אפשר לחשב בלולאה עם שני משתנים בלי לחזור על תתי־בעיות.',
 'common_mistakes':['Confusing F(n) and F(n+1)','Not specifying starting position','Multiplying rather than adding disjoint last-jump cases','Treating (1,2) and (2,1) as identical','Setting W(0)=0 inside the recurrence','Using naive exponential recursion','Claiming constant bit memory for large counts'],
 'interview_relevance':{'priority':'medium','label_he':'תרגול מועיל של חשיבה אלגוריתמית','basis':'Recurrence, small-case reasoning and simple Python implementation support general problem solving in the supplied automation/validation role.','assessment_scope':'Preparation judgment, not a prediction; Marvell appears in source tags but attribution is unverified.'},
 'related_question_ids':[],'markdown_path':'questions/prep-024-grasshopper-ladder.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
assert before['question_count']==23 and not any(x['id']==q['id'] for x in before['questions'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-1a37b60c-5761-4807-9fd3-a9a4c4d97848.png',root/'sources/prep-024.png')
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 23','"question_count": 24',1)
after=json.loads(s);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==24
p.write_text(s,encoding='utf-8')
md='# PREP-024 — חרגול על סולם\n\n## השאלה המקורית\n\n'+prompt+'\n\n![צילום המקור](../sources/prep-024.png)\n\n'
md+='## קטגוריות וחברות\n\nתגית מקור: logic. סיווג נוסף: קומבינטוריקה, נוסחאות נסיגה, רקורסיה, תכנון דינמי ופיבונאצ׳י. חברות לפי התמונה: Apple, Marvell, Mellanox, Intel; תווית ראשית אינטל. השיוך מהמקור בלבד, ללא אימות עצמאי.\n\n## רלוונטיות לראיון\n\nעדיפות בינונית: תרגול חשיבה אלגוריתמית וקוד Python פשוט. הערכת הכנה לפי התפקיד, לא תחזית לשאלה שתישאל.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+q['translations']['he']['reference_solution']
md+='\n\n[קוד](../solutions/prep_024_grasshopper_stairs.py) · [בדיקות](../checks/check_prep_024.py)\n\n## תשובה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-024 — חרגול על סולם](questions/prep-024-grasshopper-ladder.md) — מקור, תגיות וחברות, שלושה רמזים, הוכחת נסיגה, קוד ובדיקות; תועדו הנחת שלב ההתחלה וסיבוכיות במספר פעולות לעומת ביטים.\n',encoding='utf-8')
print('PREP-024 saved; 24 questions; prior records preserved.')
