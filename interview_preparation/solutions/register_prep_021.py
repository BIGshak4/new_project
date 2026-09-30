"""Persist the supplied frog/lamp puzzle and its independently checked answer."""
import json
import shutil
from math import isqrt
from pathlib import Path

root = Path(__file__).resolve().parents[1]
prompt = '''קיימות 100 נורות עם מתג כיבוי והדלקה. קיימות 100 צפרדעים הקופצות על המתגים ומשנות את מצבן. הצפרדע הראשונה קופצת על כל מתג, השנייה על כל מתג שני וכן הלאה.
אם נתון כי כל הנורות כבויות בתחילת התהליך, אילו נורות יישארו דלוקות בסופו?'''
ep = '''There are 100 lamps with on/off switches, and 100 frogs that toggle them. The first frog jumps on every switch, the second on every second switch, and so on. All lamps are initially off. Which lamps remain on at the end?'''
hints = [
    'במקום לעקוב אחרי כל הצפרדעים יחד, בחר נורה אחת ושאל: אחרי מספר זוגי של לחיצות מה מצבה, ואחרי מספר אי־זוגי?',
    'אילו צפרדעים מגיעות לנורה שמספרה 12? בדוק את הקשר בין מספר הצפרדע למספר הנורה. עכשיו נסה נורה שמספרה 9.',
    'אפשר לסדר את המחלקים של מספר בזוגות שהמכפלה שלהם היא המספר עצמו. מתי שני המחלקים בזוג הם בעצם אותו מספר, ולכן סופרים אותו פעם אחת בלבד?'
]
eh = [
    'Focus on one lamp. What happens after an even number of toggles, and after an odd number?',
    'Which frogs visit lamp 12? Relate each frog number to the lamp number, then try lamp 9.',
    'Pair each divisor d of a number with n/d. When do both members of a pair coincide and count as just one divisor?'
]
he = '''**תשובה:** הנורות שמספריהן **1, 4, 9, 16, 25, 36, 49, 64, 81, 100** יישארו דלוקות — עשר נורות.

**כך מגיעים לזה:** נמספר את הנורות ואת הצפרדעים מ־1 עד 100. צפרדע מספר k קופצת על הנורות k, 2k, 3k וכן הלאה, וכל קפיצה הופכת את המצב: כבוי נהפך לדלוק ודלוק נהפך לכבוי. לכן שתי קפיצות מבטלות זו את זו. נורה שהתחילה כבויה תישאר דלוקה רק אם מספר הקפיצות עליה אי־זוגי.

מי מגיע לנורה מספר n? בדיוק הצפרדעים שמספרן מחלק את n ללא שארית. לדוגמה, על נורה 12 קופצות צפרדעים 1, 2, 3, 4, 6, 12: שש קפיצות, ולכן בסוף היא כבויה. את המחלקים אפשר לצמד: (1,12), (2,6), (3,4). כל זוג תורם שתי קפיצות.

על נורה 9 קופצות צפרדעים 1, 3, 9: שלוש קפיצות, ולכן היא דלוקה. הזוג (1,9) תורם שתי קפיצות, אבל 3×3=9: צפרדע 3 קיימת רק פעם אחת, ולא סופרים אותה פעמיים. נשארת קפיצה אחת ללא בת זוג.

זה קורה בדיוק בריבועים שלמים. לכל מחלק d יש בן זוג n/d. הם שונים, חוץ מהמקרה d=n/d, כלומר n=d². לכן מספר שאינו ריבוע שלם מקבל מספר זוגי של קפיצות, וריבוע שלם מקבל מספר אי־זוגי. הריבועים מ־1 עד 100 הם 1² עד 10², ואלה הנורות הדלוקות. גם 1 ו־100 נכללות.

**הכללה ויעילות:** עבור N נורות ו־N צפרדעים, הנורות הדלוקות הן k² עבור k=1..⌊√N⌋. אם צריך רק כמה נורות דלוקות, התשובה היא ⌊√N⌋. כדי להפיק את רשימת המספרים אין צורך לדמות את כל הקפיצות: יצירת הריבועים אורכת Θ(√N) פעולות במודל שבו אריתמטיקה על מספרים בגודל הקלט עולה זמן קבוע, וזה מיטבי לרשימה מפורשת בעלת Θ(√N) איברים. אפשר להפיק איבר־איבר עם O(1) זיכרון עזר, מעבר לפלט. סימולציה ישירה מבצעת Σ⌊N/k⌋=Θ(N log N) החלפות ודורשת O(N) זיכרון. אם נדרש דווקא מערך מצב של כל N הנורות, עצם הפלט דורש Θ(N) מקום וכתיבות. החידה המקורית מבקשת זיהוי של הנורות, לא מימוש או ניתוח סיבוכיות.

**בדיקה:** סימולציית כל הקפיצות הושוותה לרשימת הריבועים לכל N מ־0 עד 200, ובנוסף ל־N=255,256,257,999,1000. עבור N=100 התקבלו בדיוק עשר הנורות הרשומות. נבדקו גם מספרי ריבוע ושכניהם והקשר בין זוגיות מספר המחלקים לבין ריבוע שלם לכל מספר מ־1 עד 1000.'''
en = '''The lit lamps are 1, 4, 9, 16, 25, 36, 49, 64, 81, 100: ten lamps.

Number frogs and lamps from 1 to 100. Frog k toggles lamps k, 2k, 3k, etc. Since lamps start off, a lamp finishes on exactly when it is toggled an odd number of times. Lamp n is visited precisely by frogs whose numbers divide n.

Divisors come in pairs (d,n/d). Lamp 12 has pairs (1,12), (2,6), (3,4), hence six toggles and finishes off. Lamp 9 has divisors 1,3,9: (1,9) is a pair, while 3 is its own partner and is counted only once. Thus it receives three toggles and finishes on. An unpaired divisor exists exactly when d²=n, so precisely perfect-square-numbered lamps stay on, including 1 and 100.

For N lamps and N frogs the list is k² for k=1..floor(sqrt(N)), containing floor(sqrt(N)) entries. Explicitly generating that list costs Θ(sqrt(N)) word-arithmetic operations, optimal in its output size, with O(1) auxiliary space when streamed. Materializing the list requires output space. Direct simulation costs Θ(N log N) toggles and O(N) space. A full N-lamp state-vector output instead requires Θ(N) space/writes. Counting alone requires the integer square root, not generating the list.

The direct process was checked against generated squares for every N=0..200 and for 255,256,257,999,1000. Divisor parity was checked independently for n=1..1000. The original N=100 case yields exactly the ten listed lamps.'''

q = {
    'id':'PREP-021', 'key':'hundred-frogs-lamps', 'version':1, 'created_on':'2026-09-27',
    'category':'logic', 'topic':'mathematical_reasoning',
    'topics':['logic','mathematical_reasoning','parity','divisors','perfect_squares','toggle'],
    'source_topic_tags':['logic'],
    'added_topic_tags':['mathematical_reasoning','parity','divisors','perfect_squares','toggle'],
    'source_tags':['nvidia','elta','logic','elbit'],
    'reported_companies':['NVIDIA','Elta','Elbit'], 'source_company_badge':'Elbit',
    'company_attribution_status':'reported_by_supplied_source_not_independently_verified',
    'difficulty':None, 'difficulty_scale':'1-10', 'estimated_minutes':None, 'format':'puzzle',
    'status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון',
    'origin':'user_supplied_screenshot', 'reviewed_by':None,
    'authorship':'Source prompt transcribed; translations, hints, mathematical proof and verification are AI-assisted.',
    'sources':[{'type':'user_supplied_image','path':'sources/prep-021.png','received_on':'2026-09-27'}],
    'original_prompt':prompt,
    'translations':{
        'he':{'title':'100 צפרדעים ו־100 נורות','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},
        'en':{'title':'100 frogs toggling 100 lamps','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
    'prepared_hints':[{'id':f'PREP-021-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
    'assumptions':['Lamps and frogs are indexed from 1 through 100.', 'Frog k toggles each positive multiple of k up to 100 once.', 'All lamps initially off; every visit flips state, rather than merely turning on.', 'Order does not change final parity.'],
    'optimality':{'criterion':'Identify lit lamps without simulating visits; explicit generalized output size.',
                  'result':'Exactly the perfect squares. Generating the list costs Θ(sqrt(N)) word operations and O(1) streamed auxiliary space.',
                  'scope':'Output-sensitive bound for a list of lamp numbers, not a claim about constant-time arbitrary-precision arithmetic or a full state-vector output.'},
    'edge_cases':['Lamp 1','Lamp 100','Perfect-square root divisor counted once','Generalized N=0 and N=1','Initially-on lamps would reverse the answer'],
    'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_021.py','method':'206 process simulations vs square generation; independent divisor-parity check for integers 1..1000.'},
    'media_assets':[{'type':'source_image','path':'sources/prep-021.png','description':'Complete original question screenshot including company/topic tags.'}],
    'interview_answer':'נורה n מתהפכת פעם לכל מחלק של n. מחלקים באים בזוגות, חוץ מהשורש כאשר n ריבוע שלם. לכן רק הריבועים 1,4,9,16,25,36,49,64,81,100 נשארים דלוקים.',
    'common_mistakes':['Counting visits instead of their parity','Treating toggle as set-on','Counting a square-root divisor twice','Returning lamp count instead of their numbers','Omitting 1 or 100'],
    'interview_relevance':{'priority':'low','label_he':'שאלת העשרה — אינה בעדיפות גבוהה במיוחד',
        'basis':'Short mathematical-reasoning exercise; less directly connected to the supplied validation role than timing, digital logic, Python and debugging.',
        'assessment_scope':'Preparation judgment based on the supplied job description, not a prediction of Marvell interview questions.'},
    'related_question_ids':[],
    'markdown_path':'questions/prep-021-hundred-frogs-lamps.md'
}

def main():
    p=root/'questions.json'
    s=p.read_text(encoding='utf-8')
    data=json.loads(s)
    assert data['question_count']==20 and not any(x['id']==q['id'] for x in data['questions'])
    shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-e591ed09-1a46-4332-87ed-7936d7fc8ab5.png',root/'sources/prep-021.png')
    pos=s.rfind('\n  ]')
    assert pos>0
    entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
    updated=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 20','"question_count": 21',1)
    result=json.loads(updated)
    assert result['questions'][:-1]==data['questions'] and len(result['questions'])==21
    p.write_text(updated,encoding='utf-8')
    md='# PREP-021 — 100 צפרדעים ו־100 נורות\n\n## השאלה המקורית\n\n'+prompt
    md+='\n\n![צילום השאלה](../sources/prep-021.png)\n\n## קטגוריות וחברות\n\nתגית מקור: logic. סיווג נוסף: חשיבה מתמטית, זוגיות, מחלקים, ריבועים שלמים והיפוך מצב. חברות לפי הצילום בלבד: NVIDIA, Elta, Elbit. תווית ראשית: Elbit. השיוך לא אומת עצמאית.\n\n'
    md+='## רלוונטיות לראיון\n\nשאלת העשרה בחשיבה מתמטית; אינה בעדיפות גבוהה במיוחד ביחס ללוגיקה ספרתית, תזמון, Python ודיבוג לפי תיאור המשרה שסופק. זו הערכת הכנה, לא תחזית לראיון.\n\n'
    md+='## הנחות\n\nמספור מ־1 עד 100; צפרדע k משנה פעם אחת את מצב כל מתג שמספרו כפולה של k. כל הנורות כבויות בהתחלה.\n\n'
    md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
    md+='\n\n## הצעה לפתרון\n\n'+he
    md+='\n\n## תשובה קצרה לראיון\n\n'+q['interview_answer']
    md+='\n\n[קוד בדיקה](../checks/check_prep_021.py)\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
    md+='\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
    (root/q['markdown_path']).write_text(md,encoding='utf-8')
    r=root/'README.md'
    r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-021 — 100 צפרדעים ו־100 נורות](questions/prep-021-hundred-frogs-lamps.md) — נשמרו המקור, קטגוריות וחברות, שלושה רמזים והצעה לפתרון עם הוכחה ובדיקות.\n',encoding='utf-8')
    print('PREP-021 saved; 21 questions. Prior records preserved exactly as data.')

if __name__=='__main__':
    main()
