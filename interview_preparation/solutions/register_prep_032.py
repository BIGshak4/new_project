"""Register the linked-list merge-point question, sources, proof and checks."""
import json
import shutil
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN

root=Path(__file__).resolve().parents[1]
prompt='''יש 2 רשימות מקושרות נפרדות. בשלב מסויים, עקב טעות של מהנדס, הרשימות מתאחדות. לא ידוע באיזה איבר בכל אחת מהרשימות זה קורה.
האיברים יכולים להיות שונים.
כתוב אלגוריתם שמוצא מתי הרשימות מתאחדות.'''
ep='''There are two separate linked lists. At some point, due to an engineer's mistake, the lists merge. It is not known at which element in either list this occurs. The elements may be different. Write an algorithm that finds where the lists merge.'''
hints=[
 'איחוד פירושו שהמצביעים מגיעים לאותו צומת בזיכרון, לא לשני צמתים בעלי אותו ערך. מרגע זה, האם המשך הרשימות יכול להיות שונה?',
 'אם לשתי הרשימות היה אותו אורך, שני מצביעים שמתחילים בראשיהן ומתקדמים יחד היו מגיעים לנקודת החיבור באותו זמן. מה מפריע כשאורכיהן שונים?',
 'חשב את שני האורכים. קדם רק את המצביע ברשימה הארוכה במספר צעדים השווה להפרש האורכים; אחר כך קדם את שניהם יחד והשווה זהות צמתים.'
]
eh=[
 'Merging means reaching the very same node object, not equal data values. Can the remaining tails differ after sharing a node?',
 'With equal list lengths, two pointers advancing together would reach the merge point simultaneously. What changes with unequal lengths?',
 'Count both lengths, advance the longer list by the difference, then move both pointers together and compare node identity.'
]
he='''הנחות: שתי רשימות חד־כיווניות, סופיות וללא מעגלים, כמתואר בציור המסתיים ב־NULL. יש גישה לשני הראשים ולשדה next של כל צומת, ואין שינוי מקביל ברשימות. אין צורך שהערכים יהיו ממוינים, למרות האזכור של טעות הנדסית. האיחוד הוא אותו צומת פיזי בזיכרון, שממנו ואילך יש זנב משותף: לצומת יחיד יש שדה next יחיד. שני צמתים שערכם שווה אינם בהכרח אותו צומת. אם בצומת המשותף רואים שתי רשימות, גם ערכו הוא אותו ערך משום שזה אותו אובייקט, אבל הערכים לפניו יכולים להיות שונים או שווים.

הצעה לפתרון — יישור לפי האורכים:
1. עוברים על כל רשימה וסופרים את אורכה, n ו־m.
2. מתחילים מצביע בראש כל רשימה. מקדמים רק את הארוכה בהפרש האורכים.
3. כעת לשני המצביעים נותר אותו מספר צמתים עד הסוף. כל עוד אינם מצביעים לאותו אובייקט, מתקדמים צעד בכל רשימה.
4. הצומת הזהה הראשון הוא נקודת האיחוד. אם שניהם מגיעים ל־None, אין איחוד. הקוד מטפל גם ברשימות ריקות ובאיחוד כבר בראש. הרשימות אינן משתנות.

היגיון: כל ההפרש באורכי הרשימות מגיע מהקטעים שלפני נקודת החיבור; הזנב המשותף מוסיף לשתיהן בדיוק אותו אורך. נסמן אורכי קטעים פרטיים p,q ואורך זנב משותף c. אורכי הרשימות הם p+c ו־q+c, ולכן הפרשם p−q. כשמדלגים על ההפרש בקטע הפרטי הארוך, לשני המצביעים נותר מרחק זהה עד החיבור. הליכה משותפת תביא אותם לצומת המשותף הראשון באותו צעד. לפניו אינם יכולים להיות זהים, לפי הגדרת הקטעים הפרטיים.

```text
A: A1 -> A2 -> A3 -> C1 -> C2 -> None   (length 5)
B:             B1 -> C1 -> C2 -> None   (length 3)

Advance A by 2:  p=A3, q=B1
One step each:   p=C1, q=C1  => first shared node
```

C1 ו־C2 בשתי השורות הם אותם צמתים ממש. זו אינה העתקה של שני צמתים בעלי אותו שם או ערך. בפייתון משווים באמצעות is; אין להשוות value או להסתמך על == שעשוי להיות מוגדר להשוואת תוכן.

סיבוכיות: O(n+m) זמן ו־O(1) זיכרון עזר במודל מצביעים/מילות מכונה. אלה כמה מעברים ליניאריים, לא לולאה מקוננת. זהו זמן מיטבי במקרה הגרוע ברשימות כלליות ללא מטא־דאטה או מבני עזר; ייתכן שהחיבור יתגלה רק בסוף קטעים פרטיים ארוכים. קוד נתון ב־solutions/prep_032_list_intersection.py. אפשרות פשוטה יותר משתמשת בקבוצת כתובות הצמתים של הרשימה הראשונה ובודקת שייכות תוך מעבר בשנייה, אך דורשת O(n) זיכרון ובדרך כלל O(n+m) זמן צפוי במימוש hash. אין צורך בה לצורך המימוש בזיכרון קבוע.

בדיקות: כל 343 שילובי האורכים 0..6 של שני קטעים פרטיים וזנב משותף, בשני סדרי הארגומנטים; שני מקרים ארוכים נוספים עם קטע פרטי באורך 10000. כל הערכים בכוונה זהים (7), כדי לוודא שימוש בזהות ולא בשוויון ערכים. נבדק שאין שינוי בשדות next או בערכים. מעגלים ומוטציות מקבילות אינם מכוסים ואינם חלק מהמודל שבתמונה.

תעדוף: בינוני כחזרה קצרה על מצביעים, זהות אובייקטים ובדיקת מקרי קצה. בתקופת הכנה קצרה אין צורך להעמיק מעבר להבנת השיטה. אין להסיק מכך שהמראיינים לא יודעים על קורס מסוים שלא ישאלו על תכנות בסיסי; זו הערכת הכנה לפי תיאור המשרה ולא תחזית לראיון.'''
en='''Assume finite acyclic singly linked lists, as the source's NULL-terminated drawing indicates, with two head pointers, readable next links and no concurrent mutation. Lists need not be sorted. Intersection means the identical physical node, not equal data values. Once a node is shared, the suffix is shared because that node has one next pointer.
Count lengths n,m. Advance the longer list's pointer by abs(n-m). Both pointers now have the same remaining length. Move them together until they are identical; return that node, or None if both reach the end. Empty lists and sharing at either head are supported without mutation. In Python use is, not value equality or an overloaded ==.
Proof: with private prefixes p,q and common suffix c, lengths are p+c,q+c. Their difference p-q is entirely due to the private prefixes. Removing the excess prefix aligns distances to the first shared node, which is reached simultaneously. Example: A1->A2->A3->C1->C2 and B1->C1->C2 have lengths 5 and 3; advance A twice, then A3/B1 step together to C1.
O(n+m) time and O(1) auxiliary machine words; worst-case optimal for general pointer-access lists without metadata/indexing. A hash set of node identities is a simpler expected-linear alternative but uses O(n) space. The saved Python code is tested on all 343 prefix/prefix/suffix length triples in 0..6, in both argument orders, plus two long cases. Every node deliberately contains the same value to catch identity mistakes; all links and values are checked for immutability. Cycles/concurrent mutation are outside scope. Medium preparation priority as a short pointer/identity/edge-case revision, not a forecast of interview questions; undisclosed coursework does not rule out basic programming questions.'''

asset='diagrams/prep-032-shared-list-tail.png'
d=Drawing('Two linked lists | One shared tail', 'C1 and C2 are the SAME node objects in both lists, not copies with equal values.', 620)
for x,y,name,color in [(160,180,'A1',BLUE),(470,180,'A2',BLUE),(780,180,'A3',BLUE),(780,440,'B1',BLUE),(1180,300,'C1',GREEN),(1490,300,'C2',GREEN)]:
    d.rect(x,y,180,80)
    d.text(x+90,y+40,name,34,color,True,anchor='mm')
for pts in [[(340,220),(470,220)],[(650,220),(780,220)],[(960,220),(1080,220),(1080,320),(1180,320)],[(960,480),(1120,480),(1120,360),(1180,360)],[(1360,340),(1490,340)],[(1670,340),(1790,340)]]:
    d.line(pts);d.arrow(*pts[-1])
d.text(1805,340,'None',27,anchor='lm')
d.text(70,175,'A',34,BLUE,True)
d.text(690,435,'B',34,BLUE,True)
d.text(65,560,'Length A = 5, length B = 3. Advance A by 2 nodes, then walk both lists together.',27)
d.im.resize((1900,620)).save(root/asset)

q={
 'id':'PREP-032','key':'linked-lists-first-shared-node','version':1,'created_on':'2026-09-29','category':'software','topic':'linked_lists',
 'topics':['software','linked_lists','pointers','object_identity','two_pointers','algorithms'],
 'source_topic_tags':['hardware','software'],'added_topic_tags':['linked_lists','pointers','object_identity','two_pointers','algorithms'],
 'source_tags':['amazon','arm','nvidia','hardware','software','checkpoint','microsoft','apple','broadcom'],'reported_companies':['Amazon','Arm','NVIDIA','Check Point','Microsoft','Apple','Broadcom'],'source_company_badge':'ברודקום','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'algorithm_design','status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-032.png','received_on':'2026-09-29'}],'original_prompt':prompt,
 'translations':{'he':{'title':'מציאת הצומת הראשון המשותף לשתי רשימות מקושרות','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'Find the first shared node of two linked lists','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-032-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Finite acyclic singly linked lists with None terminators.','Intersection means shared node identity, not equal values.','Access to head pointers and next fields; no concurrent mutation.','Ordering of stored values is irrelevant.'],
 'optimality':{'criterion':'Worst-case traversal time and auxiliary space','result':'O(n+m) time, O(1) machine words.','scope':'General acyclic pointer-linked lists without indexing or precomputed metadata; cycles excluded.'},
 'edge_cases':['Both heads empty','One head empty','Disjoint equal-value lists','Identical heads','One head within the other list','Single shared tail node','Different prefix lengths','Repeated data values'],
 'verification':{'status':'passed','checked_on':'2026-09-29','script_path':'checks/check_prep_032.py','method':'343 small prefix/prefix/suffix combinations in both orders, two long cases, equal values, identity and immutability checks.'},
 'solution_code_path':'solutions/prep_032_list_intersection.py','media_assets':[{'type':'source_image','path':'sources/prep-032.png','description':'Full original prompt, linked-list merge drawing and source company tags.'},{'type':'solution_diagram','path':asset,'description':'Box-and-arrow lists with private prefixes and identical shared suffix.'}],
 'interview_relevance':{'priority':'medium','label_he':'חזרה קצרה על מצביעים וזהות צמתים','basis':'Useful basic programming and edge-case reasoning; under time pressure, do not prioritize advanced linked-list variants over role-specific validation preparation.','assessment_scope':'Preparation judgment, not prediction; coursework visibility does not guarantee topic exclusion.'},
 'related_question_ids':['PREP-026'],'common_mistakes':['Comparing node values instead of identity','Advancing both original heads immediately despite unequal prefix lengths','Assuming the lists must be sorted','Mutating next pointers unnecessarily','Using the acyclic algorithm on lists with cycles'],
 'markdown_path':'questions/prep-032-linked-list-intersection.md'
}
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
assert before['question_count']==31 and not any(x['id']==q['id'] for x in before['questions'])
pos=raw.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
updated=(raw[:pos]+',\n'+entry+raw[pos:]).replace('"question_count": 31','"question_count": 32',1)
after=json.loads(updated);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==32
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-8a75ecf4-fad5-426b-b6c8-1499c68b31fe.png',root/'sources/prep-032.png')
p.write_text(updated,encoding='utf-8')
md='# PREP-032 — נקודת איחוד של רשימות מקושרות\n\n## נוסח המקור\n\n'+prompt+'\n\n![צילום השאלה והתרשים](../sources/prep-032.png)\n\nתגיות מקור: hardware, software. חברות לפי המקור: Amazon, Arm, NVIDIA, Check Point, Microsoft, Apple, Broadcom; תווית ראשית ברודקום. השיוך לא אומת עצמאית.\n\n## שלושה רמזים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he+'\n\n![דוגמת רשימות עם זנב משותף](../'+asset+')\n\n[קוד Python](../solutions/prep_032_list_intersection.py) · [בדיקות](../checks/check_prep_032.py)\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(eh,1))+'\n\n'+en+'\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-032 — נקודת איחוד של שתי רשימות מקושרות](questions/prep-032-linked-list-intersection.md) — מקור ותרשים, חברות, רמזים, יישור אורכים עם הוכחה וקוד בדוק; זהות צמתים ולא שוויון ערכים.\n',encoding='utf-8')
print('PREP-032 saved; 32 questions; source, bilingual solution, hints, code and diagram stored.')
