"""Save three-color partition question with source constraints and role relevance."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-cf8e5bf8-ae4d-40c5-a03b-42188f36a70b.png',root/'sources/prep-019.png')
prompt='''יש למיין מערך כדורים חד־ממדי בשלושה צבעים באורך סופי, כך שכל הכדורים האדומים בצד ימין, כל הכדורים הכחולים בצד שמאל וכל הכדורים הירוקים ביניהם.
מבחינת זיכרון וסיבוכיות: O(n), כלומר מותר להסתכל בכל תא במערך פעם אחת בלבד, ולהשתמש בזיכרון O(1) אשר לא תלוי במספר הכדורים במערך.'''
ep='''Rearrange a finite one-dimensional array of balls of three colors so all blue balls are on the left, all green balls are in the middle, and all red balls are on the right. Require O(n) time and O(1) extra memory independent of the number of balls. The source also says that each array cell may be looked at only once; this wording needs to be distinguished from linear-time or single-pass partitioning.'''
hints=[
 'לא צריך למיין לפי השוואות בין כל זוג כדורים. יש רק שלוש קבוצות, והסדר בתוך כל צבע אינו חשוב. אילו צבעים אפשר להעביר מיד לקצוות?',
 'נסה להחזיק גבול לאזור הכחול משמאל, גבול לאזור האדום מימין ואינדקס שסורק את האזור שטרם סווג. חשוב איזה אזור כבר ידוע כירוק.',
 'כחול מעבירים לגבול השמאלי, ירוק משאירים ומתקדמים, ואדום מחליפים עם סוף האזור הלא מסווג. אחרי החלפה עם הצד הימני, האם כבר ידוע הצבע של הכדור שהגיע למיקום הסריקה?'
]
eh=[
 'You have only three groups and need not preserve order within a color. Which colors can be placed immediately at the ends?',
 'Maintain a left blue boundary, a right red boundary and an index scanning the unclassified region. Identify which region is already known to be green.',
 'Move blue to the left boundary, advance past green, and swap red with the end of the unknown region. After a right-side swap, is the replacement at the scan position already classified?'
]
he='''זו בעיית חלוקה לשלושה צבעים (Dutch National Flag), על מערכים ואלגוריתמים במקום. הסדר הרצוי הוא כחול, ירוק, אדום. אין צורך לשמור על הסדר היחסי של כדורים מאותו צבע, אך נרצה לשמר את הכדורים עצמם ולא ליצור במקומם אובייקטים חדשים.

**הרעיון:** מחזיקים שלושה אינדקסים low,mid,high. בתחילה low=mid=0 ו־high=n−1. בכל שלב מתקיימת החלוקה:

```text
[0, low)       כחולים שכבר סודרו
[low, mid)     ירוקים שכבר סודרו
[mid, high]    כדורים שטרם סווגו
(high, n)      אדומים שכבר סודרו
```

כל עוד mid<=high בודקים את צבע הכדור במקום mid:

- כחול: מחליפים עם low ומקדמים גם low וגם mid. כאשר low<mid, הכדור שהיה ב־low הוא ירוק שכבר סווג, ולכן אין צורך לבדוק אותו שוב אחרי ההחלפה. כאשר low=mid זו החלפה של התא עם עצמו.
- ירוק: מקדמים רק mid. הכדור מצטרף לאזור הירוק.
- אדום: מחליפים עם high ומקטינים high. לא מקדמים mid! הכדור שהגיע מימין שייך לאזור הלא מסווג, ולכן צריך לבדוק אותו בסיבוב הבא.

בסיום mid>high ואין אזור לא מסווג. האזורים הידועים מכסים את כל המערך ומתקבל הסדר המבוקש.

```python
def sort_colors(a):
    low = mid = 0
    high = len(a) - 1
    while mid <= high:
        color = a[mid]
        if color == 'B':
            a[low], a[mid] = a[mid], a[low]
            low += 1
            mid += 1
        elif color == 'G':
            mid += 1
        elif color == 'R':
            a[mid], a[high] = a[high], a[mid]
            high -= 1
        else:
            raise ValueError('Expected B, G or R')
    return a
```

הקוד המלווה תומך גם באובייקטים באמצעות פונקציית key לקבלת הצבע. כל ההחלפות בתוך אותו מערך. הזיכרון הנוסף הוא שלושה אינדקסים ומשתנים זמניים קבועים בלבד: O(1), בהנחת מודל RAM שבו אינדקס נכנס במילת מכונה. אין מערך עזר ואין רקורסיה.

**הוכחת זמן ונכונות:** בכל איטרציה אורך האזור הלא מסווג high−mid+1 קטן בדיוק באחד: או שמקדמים mid, או שמקטינים high. לכן יש בדיוק n איטרציות, וכל אחת דורשת עבודה קבועה. הזמן O(n). תנאי החלוקה של ארבעת האזורים נשמר בכל אחד משלושת המקרים; הוא נכון בתחילה כי האזורים המסווגים ריקים, ובסיום כל הכדורים מסווגים. נשמר גם אוסף הכדורים כי מבצעים החלפות בלבד. יש חסם תחתון Omega(n) במקרה הגרוע: ללא בדיקה/טיפול בקלט כולו אין דרך להבטיח שהצבעים מסודרים עבור מערך שרירותי. לכן זמן הריצה מיטבי אסימפטוטית, והזיכרון הנוסף קבוע.

**דיוק בניסוח המקור:** O(n) אינו אומר שכל כתובת במערך נקראת פעם אחת בלבד. אחרי החלפת אדום עם כדור מימין, אפשר לבדוק שוב את אותו אינדקס mid, אבל נמצא בו כדור אחר. במימוש הזה כל כדור מקורי עובר בדיקת צבע אחת, ומספר האיטרציות הכולל n; פעולות החלפה עצמן כוללות קריאות וכתיבות, וכתובות יכולות להופיע שוב. לכן זה פתרון למעבר חלוקה יחיד בזמן לינארי, ולא הוכחה לעמידה באיסור מילולי על יותר מגישה אחת לכל תא פיזי. אם זו דרישה קשיחה, צריך לברר את מודל הקריאה והכתיבה; אין להציג את שתי הדרישות כשקולות.

פתרון של ספירת שלושת הצבעים ולאחר מכן כתיבה מחדש גם הוא O(n) זמן ו־O(1) זיכרון אם הערכים הם צבעים בלבד, אבל דורש שני מעברים ואינו משמר בהכרח זהות של אובייקטי כדורים. לכן אינו החלופה העיקרית כאן. האלגוריתם המוצע אינו יציב: אין הבטחה לשמור על הסדר היחסי של כדורים בעלי אותו צבע.

**בדיקות:** נבדקו כל 9,841 מערכי הצבעים באורכים 0 עד 8, דוגמת הצילום ומקרים ארוכים: צבע יחיד, מערך מסודר ומערך בסדר הפוך. נבדקו הסדר, זהות המערך, שימור כל אובייקטי הקלט, ובדיקת צבע אחת לכל אובייקט מקורי. הקוד עבר. אין מעקב אחר שימוש ברמזים בשיחה.'''
en='''Use Dutch National Flag three-way partition with blue left, green middle and red right. Maintain low=mid=0 and high=n−1. Invariant: [0,low) blue; [low,mid) green; [mid,high] unknown; (high,n) red. Blue at mid swaps with low and advances both; green advances mid; red swaps with high and decrements high without advancing mid, since the replacement is unknown. If low<mid, a blue swap brings a previously classified green from low, so advancing mid is safe.

Each iteration shrinks the unknown region by one, giving exactly n iterations and O(n) time, with O(1) auxiliary words and no recursion. Swaps preserve original objects; the algorithm is not stable. The worst-case linear bound is asymptotically optimal for arbitrary inputs. The source conflates O(n) with a literal single access to each array cell: array positions can be revisited after swaps. Every original ball is classified once, but reads/writes for swaps still occur. If a strict one-access-per-address restriction is intended, its access model needs clarification. Counting colors and overwriting uses constant space and linear time but two passes, and can lose object identity.

Exhaustive tests covered 9,841 arrays of lengths 0..8, the source example, monochrome and long sorted/reversed cases. Checks verify ordering, list identity, preservation of all original objects and exactly one key/color classification per original object.'''
q={
'id':'PREP-019','key':'three-color-in-place-partition','version':1,'created_on':'2026-09-27',
'category':'software','topic':'array_algorithms',
'topics':['software','algorithms-software','arrays','three_way_partition','dutch_national_flag','in_place','time_space_complexity','loop_invariants'],
'source_topic_tags':['software','algorithms-software'],
'added_topic_tags':['arrays','three_way_partition','dutch_national_flag','in_place','time_space_complexity','loop_invariants'],
'source_tags':['amazon','nvidia','software','cisco','applied-materials','apple','elbit','intel','algorithms-software'],
'reported_companies':['Amazon','NVIDIA','Cisco','Applied Materials','Apple','Elbit','Intel'],
'source_company_badge':'אינטל','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'algorithm','status':'in_review',
'solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot',
'authorship':'Source transcribed; AI-assisted hints, solution, translation and exhaustive tests.','reviewed_by':None,
'sources':[{'type':'user_supplied_image','path':'sources/prep-019.png','received_on':'2026-09-27'}],
'original_prompt':prompt,
'translations':{'he':{'title':'חלוקת מערך כדורים לשלושה צבעים בזמן לינארי ובזיכרון קבוע','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},
                'en':{'title':'In-place three-color array partition in linear time','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
'prepared_hints':[{'id':f'PREP-019-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
'assumptions':['Mutable random-access array; color lookup and swaps take O(1) time.',
               'Each item has exactly one of the three colors B/G/R. Preserve all original objects.',
               'No stability requirement; order inside one color is irrelevant.',
               'Interpret single pass as shrinking an unclassified region, not a literal one-access-per-physical-address rule.',
               'O(1) auxiliary machine words in the standard RAM model.'],
'optimality':{'criterion':'Worst-case time and auxiliary space for in-place three-way partition',
              'result':'Theta(n) time, O(1) auxiliary words, exactly n classification iterations',
              'proof':'Unknown-region size drops by one each iteration; arbitrary input requires Omega(n) worst-case processing.'},
'edge_cases':['Empty array','Single ball','One or two colors only','Already sorted','Reverse grouped order','Repeated red swaps at the same scan index','Low equals mid or mid equals high'],
'verification':{'status':'passed','checked_on':'2026-09-27','script_path':'checks/check_prep_019.py',
                'method':'All 9,841 arrays at lengths 0..8, source sequence, long edge cases; sorted colors, same list, preserved object identities and exactly one classification per item.'},
'solution_code_path':'solutions/prep_019_three_colors.py','code_language':'python',
'media_assets':[{'type':'source_image','path':'sources/prep-019.png','description':'Original question including colored-ball array and company tags.'}],
'interview_answer':'אחזיק גבול לכחולים, גבול לאדומים ומצביע לאזור הלא מסווג. אעביר כחול שמאלה, אדום ימינה וירוק אשאיר באמצע. אחרי החלפה מימין לא אקדם את הסורק, כי הגיע כדור שטרם נבדק. בכל צעד האזור הלא מסווג קטן באחד, ולכן הזמן לינארי והזיכרון קבוע.',
'common_mistakes':['Advancing mid after swapping with high','Treating O(n) as proof of exactly one physical-cell read','Allocating three lists despite O(1) memory','Returning a sorted copy','Claiming stable ordering','Replacing objects by colors and losing identity'],
'related_question_ids':[],'related_question_links':[],
'interview_relevance':{'assessment':'Recommended foundational Python/algorithm practice for the supplied System Chip Validation Intern role; not a prediction of the exact interview question.',
    'basis':'User-supplied role description explicitly emphasizes Python scripting, test automation and problem solving. Other official Marvell validation internship postings also mention Python automation.',
    'company_question_evidence':'Marvell is not among the supplied question tags; do not attribute this question to Marvell.',
    'suggested_practice':'A focused 15–20 minute attempt, then understand and implement the reasoning; avoid spending hours at the expense of Python fundamentals, debugging and test planning.',
    'supporting_role_source':{'url':'https://marvell.wd1.myworkdayjobs.com/en-US/MarvellCareers/job/Hardware-Validation-Intern---Master-s-Degree_2502387','title':'Hardware Validation Intern — Master’s Degree','scope':'Different Marvell validation internship, corroborates Python and automated testing relevance; not the user’s exact position.'}},
'markdown_path':'questions/prep-019-three-color-partition.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');data=json.loads(s)
assert data['question_count']==18 and not any(a['id']==q['id'] for a in data['questions'])
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 18','"question_count": 19',1)
data=json.loads(s);assert len(data['questions'])==data['question_count']==19
p.write_text(s,encoding='utf-8')
md='# PREP-019 — מיון שלושה צבעים בזמן לינארי ובזיכרון קבוע\n\n## השאלה המקורית\n\n'+prompt
md+='\n\n![צילום השאלה, המערך והתגיות](../sources/prep-019.png)\n\n## קטגוריות וחברות\n\n'
md+='תגיות מקור: software, algorithms-software. סיווג נוסף: מערכים, חלוקה לשלוש קבוצות, עבודה במקום, סיבוכיות זמן וזיכרון ואינווריאנטים של לולאה. חברות לפי המקור: Amazon, NVIDIA, Cisco, Applied Materials, Apple, Elbit, Intel. תווית ראשית: אינטל. השיוך לא אומת עצמאית; Marvell אינה מופיעה בתגיות.\n\n'
md+='## רלוונטיות להכנה לראיון\n\n'
md+='מומלץ לתרגל כשאלת יסוד בתכנות ומערכים, בהתבסס על Python ואוטומציית בדיקות בתיאור המשרה שסופק. אין מכאן ראיה שהשאלה עצמה תישאל. גם [משרת ולידציה אחרת ב־Marvell](https://marvell.wd1.myworkdayjobs.com/en-US/MarvellCareers/job/Hardware-Validation-Intern---Master-s-Degree_2502387) מזכירה Python ובדיקות אוטומטיות. זו תמיכה ברלוונטיות המיומנות, לא זיהוי של המשרה הספציפית. המלצה: ניסיון ממוקד של 15–20 דקות, ואז הבנה ומימוש; לא להקדיש שעות על חשבון יסודות Python, דיבוג ותכנון בדיקות.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))
md+='\n\n## הצעה לפתרון\n\n'+he
md+='\n\n[קוד Python](../solutions/prep_019_three_colors.py) · [בדיקות](../checks/check_prep_019.py).\n\n'
md+='## תשובה קצרה לראיון\n\n'+q['interview_answer']+'\n\n## English\n\n'+ep+'\n\n'
md+='\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en
md+='\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
with (root/'README.md').open('a',encoding='utf-8') as f:
    f.write('\n- [PREP-019 — חלוקת מערך לשלושה צבעים](questions/prep-019-three-color-partition.md) — נשמרו המקור והתרשים, קטגוריות, חברות, שלושה רמזים, פתרון וקוד בדוק; תועדה ההבחנה בין זמן לינארי לבין גישה יחידה לכל תא ורלוונטיות לתפקיד.\n')
assert (root/'sources/prep-019.png').exists()
assert he in (root/q['markdown_path']).read_text(encoding='utf-8')
print('PREP-019 saved: source, categories/companies, hints, checked solution and role assessment. Total: 19.')
