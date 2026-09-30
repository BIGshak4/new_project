"""Record binary-tree question and time-limited role-specific study assessment."""
import json
import shutil
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prompt='''1) what is the different between binary tree to binary search tree?
2) given a binary tree, find its biggest value. write a code in java / c++'''
hp='''1. מה ההבדל בין עץ בינארי לעץ חיפוש בינארי?
2. בהינתן עץ בינארי, מצא את הערך הגדול ביותר בו. כתוב קוד ב־Java או C++.'''
hints=[
 'הפרד בין מגבלה על מספר הילדים של צומת לבין כלל שמסדר את הערכים בעץ. האם עץ בינארי רגיל מבטיח משהו על מיקום הערך הגדול?',
 'בסעיף השני כתוב עץ בינארי, ולא בהכרח עץ חיפוש. האם אפשר לפסול תת־עץ בלי לבדוק את הערכים שבתוכו? חשוב על מעבר שמבקר בכל צומת.',
 'במהלך המעבר שמור את הערך הגדול ביותר שנראה עד עכשיו. אתחל מערך קיים בעץ ולא מאפס, וחשוב מה מחזירים כשהעץ ריק ואיך מנהלים את הצמתים שעוד צריך לבקר.'
]
eh=[
 'Distinguish the limit on children per node from an ordering rule on values. Does an ordinary binary tree constrain where its largest value lies?',
 'Part two says binary tree, not necessarily BST. Can you discard a subtree without examining it? Consider visiting every node.',
 'Track the largest visited value, initialized from an actual node rather than zero. Specify empty-tree behavior and how to keep unvisited nodes.'
]
he='''**סעיף 1 — ההבדל:** עץ בינארי הוא עץ שבו לכל צומת לכל היותר שני ילדים, לרוב מסומנים שמאל וימין. אין דרישה שהערכים מסודרים. עץ חיפוש בינארי (BST) הוא עץ בינארי עם אינווריאנט סדר: בהנחת מפתחות ייחודיים, כל הערכים בכל תת־העץ השמאלי קטנים מערך הצומת וכל הערכים בכל תת־העץ הימני גדולים ממנו. הכלל חל על כל תת־העץ, לא רק על הילדים הישירים, וחל בכל צומת. אם מותרות כפילויות צריך לקבוע מדיניות; במימוש מקובל אפשר למשל לשמור מונה באותו צומת. BST אינו בהכרח עץ מאוזן.

**סעיף 2:** נתון עץ בינארי כללי, לכן אין הצדקה ללכת רק ימינה. לדוגמה שורש 3, ילד שמאלי 99 וילד ימני 4: המקסימום דווקא משמאל. צריך לבקר בכל הצמתים ולשמור מקסימום. מימוש DFS איטרטיבי משתמש במחסנית: מכניסים שורש, מוציאים צומת, מעדכנים מקסימום ומכניסים ילדים קיימים; ממשיכים עד שהמחסנית מתרוקנת. סדר שמאל/ימין אינו משנה את המקסימום.

**הנחות ומקרי קצה:** עץ סופי תקין ללא מעגלים, ערכים שלמים בני השוואה, ולא גרף עם שיתוף צמתים. לעץ ריק אין מקסימום; נחזיר optional ריק במקום מספר שעלול להיות ערך חוקי. בעץ לא ריק מאתחלים best לערך השורש, לא ל־0, כדי לטפל בעץ שכל ערכיו שליליים וגם ב־INT_MIN. כפילויות אינן מפריעות למציאת המקסימום. מחסנית מפורשת חוסכת את מגבלת עומק מחסנית הקריאות ברקורסיה, אך עדיין צורכת זיכרון.

**נכונות:** אחרי כל ביקור best הוא המקסימום בין כל הצמתים שבוקרו. כל ילד קיים מוכנס פעם אחת, וכל צומת בעץ נגיש מהשורש. עם סיום המעבר כולם בוקרו, לכן best הוא המקסימום בכל העץ. בעץ כללי ללא מידע נוסף, אם אלגוריתם לא קורא ערך של צומת כלשהו, ניתן לשנות אותו לערך גדול מכל האחרים מבלי לשנות את מה שהאלגוריתם ראה. לכן נדרשות Ω(n) קריאות במקרה הגרוע, והמעבר Θ(n) מיטבי בזמן. זיכרון מחסנית DFS הוא O(h) כחסם עליון, כאשר h גובה העץ, ובמקרה הגרוע O(n). אין כאן הוכחת מינימום זיכרון מוחלט; קיימות שיטות שעוברות דרך שינוי זמני של קישורים, שאינן נדרשות כאן.

**אם במקום זאת היה נתון BST:** המקסימום הוא הצומת הימני ביותר. מתחילים בשורש וממשיכים לילד ימני עד שאין כזה. זה O(h) זמן ו־O(1) זיכרון עזר באיטרציה. בעץ מאוזן h=O(log n), אבל ב־BST מנוון h=O(n); אין להבטיח O(log n) בלי איזון.

נשמרו קוד C++17 עם std::optional<int>, קוד Java עם OptionalInt ו־ArrayDeque, ומודל Python שנבדק. לא נמצאו g++, clang++ או javac ב־PATH בעת ההכנה: קוד C++ ו־Java לא קומפל ולא הורץ. מודל Python המקביל נבדק על כל צורות העצים בגודל 0..5 עם ערכים −1,0,1 (11,497 עצים מסומנים), דוגמאות שליליות ולא־BST, גבולות int ועץ בעומק 3,000. בדיקות המודל אינן תחליף לקומפילציה של המקורות האחרים.'''
en='''A binary tree has at most two children per node, with no value-order guarantee. A BST additionally maintains a global subtree ordering: with unique keys, every key in the left subtree is smaller than the node and every key in the right subtree is larger, recursively. State a duplicate-key policy if needed. BST does not imply balanced.

For the general binary tree in part two, traverse every node and track the maximum, initializing from the root rather than zero. An iterative DFS stack avoids recursion-depth limits. Return an empty optional for an empty tree, not an ambiguous sentinel. Assume a finite proper acyclic tree with comparable integer values. Non-BST counterexample: root 3, left 99, right 4; rightmost is not the maximum. Negative-only trees and INT_MIN are handled by root initialization.

The invariant is that best equals the maximum of visited nodes. Traversal reaches every node once, so at termination it is the maximum. Time Θ(n) is optimal for unrestricted unaugmented binary trees: an unseen node could contain a larger value. Explicit DFS stack has O(h) auxiliary-space upper bound, O(n) worst case. No globally optimal-space claim is made. For a BST only, walk right to the rightmost node: O(h) time and O(1) iterative space, O(log n) time only if balanced.

Stored C++17 optional/vector and Java OptionalInt/ArrayDeque implementations were reviewed but not compiled or run: g++, clang++ and javac were not found on PATH. A Python reference was checked on all 11497 labelled binary trees of sizes 0..5 with labels -1,0,1, plus non-BST, all-negative, int-boundary and depth-3000 cases. Reference tests do not establish compiled-language execution.'''
cpp=(root/'solutions/prep_026_tree_max.cpp').read_text(encoding='utf-8')
java=(root/'solutions/Prep026TreeMax.java').read_text(encoding='utf-8')
code='\n\n```cpp\n'+cpp+'```\n\n```java\n'+java+'```'
q={
 'id':'PREP-026','key':'binary-tree-vs-bst-maximum','version':1,'created_on':'2026-09-28','category':'software','topic':'trees',
 'topics':['software','c','java','cpp','binary_tree','binary_search_tree','depth_first_search','complexity'],
 'source_topic_tags':['software','c','java'],'added_topic_tags':['cpp','binary_tree','binary_search_tree','depth_first_search','complexity'],
 'source_tags':['amazon','software','c','java'],'reported_companies':['Amazon'],'source_company_badge':'Amazon','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'concept_and_code','status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot','authorship':'Source English wording transcribed; AI-assisted Hebrew translation, hints, code and analysis.','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-026.png','received_on':'2026-09-28'}],'original_prompt':prompt,
 'translations':{'he':{'title':'עץ בינארי מול BST ומציאת מקסימום','prompt':hp,'hint':hints[0],'hints':hints,'reference_solution':he+code},'en':{'title':'Binary tree versus BST and finding the maximum','prompt':prompt,'hint':eh[0],'hints':eh,'reference_solution':en+code}},
 'prepared_hints':[{'id':f'PREP-026-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Finite proper binary tree, no cycles or shared-node graph.','Comparable int values; empty tree returns an absent optional.','Part two does not guarantee BST ordering.','BST definition uses unique keys; duplicate policy would need specification.','No extra subtree-maximum metadata.'],
 'optimality':{'criterion':'Worst-case time for maximum in a general unaugmented binary tree.','result':'Θ(n) traversal time, O(h) auxiliary DFS-stack bound.','scope':'Reading every node necessary in worst case; not globally minimum auxiliary space. BST-only variant is O(h), not necessarily O(log n).'},
 'edge_cases':['Empty tree','Single node','All negative values','INT_MIN / INT_MAX','Maximum in left subtree','Duplicates','Highly skewed tree','BST global ordering versus child-only checks'],
 'verification':{'status':'python_reference_passed_cpp_java_not_executed','checked_on':'2026-09-28','script_path':'checks/check_prep_026.py','method':'11497 small labelled-tree cases and explicit deep/negative/non-BST/boundary cases in Python reference.','limitations':'C++ and Java sources were not compiled or run; no g++, clang++ or javac found on PATH.'},
 'solution_code_paths':['solutions/prep_026_tree_max.cpp','solutions/Prep026TreeMax.java','solutions/prep_026_tree_max.py'],
 'media_assets':[{'type':'source_image','path':'sources/prep-026.png','description':'Full English question and source company/language tags.'}],
 'interview_answer':'בעץ בינארי לכל צומת עד שני ילדים, בלי סדר ערכים מחייב. BST מוסיף סדר על כל תתי־העצים. בסעיף 2 מדובר בעץ כללי, ולכן עוברים על כל הצמתים ושומרים מקסימום, בזמן Θ(n). אם מובטח BST, אפשר ללכת לצומת הימני ביותר בזמן O(h).',
 'common_mistakes':['Assuming general binary tree is BST','Checking ordering only against direct children','Assuming BST is balanced','Starting maximum at zero','Using a valid integer as an empty-tree sentinel','Ignoring recursion depth','Claiming tested compiled code from Python model tests'],
 'interview_relevance':{'priority':'low','label_he':'עדיפות נמוכה יחסית בזמן הכנה מוגבל','basis':'Supplied System Chip Validation role emphasizes Python automation, networking-switch system tests and debugging. Trees are useful fundamentals but less directly tied to that stated work.','recommendation':'Spend at most 5–10 minutes on concepts if feasible; defer deeper tree study/Java-specific coding. Prioritize Python basics, validation/debugging and networking foundations, then relevant digital logic.','assessment_scope':'Assistant prioritization judgment, not a forecast or exemption from coding questions; interviewer awareness of coursework is unknown and does not determine relevance.','external_context':{'url':'https://marvell.wd1.myworkdayjobs.com/en-US/MarvellCareers/job/Hardware-Design-Intern_2502459','title':'Hardware Validation Intern','note':'Official related Marvell role corroborates Python/C++ and test automation, not the exact user position or its interview content.','checked_on':'2026-09-28'}},
 'related_question_ids':[],'markdown_path':'questions/prep-026-binary-tree-bst-maximum.md'
}
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
assert before['question_count']==25 and not any(x['id']==q['id'] for x in before['questions'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-6ab21ad9-7ec2-41d6-9a1f-2fb7f08be43b.png',root/'sources/prep-026.png')
pos=s.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=(s[:pos]+',\n'+entry+s[pos:]).replace('"question_count": 25','"question_count": 26',1)
after=json.loads(s);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==26
p.write_text(s,encoding='utf-8')
md='# PREP-026 — עץ בינארי מול BST ומציאת מקסימום\n\n## השאלה המקורית\n\n'+prompt+'\n\n'+hp+'\n\n![צילום המקור](../sources/prep-026.png)\n\n'
md+='## קטגוריות וחברות\n\nתגיות מקור software,c,java; בנוסח עצמו C++ ולכן נשמר גם cpp כסיווג נוסף. עצים בינאריים, BST, DFS וסיבוכיות. חברה לפי המקור: Amazon; תווית Amazon. השיוך לא אומת עצמאית.\n\n## תעדוף לראיון\n\nעדיפות נמוכה יחסית בזמן הכנה קצר. כדאי להכיר את העקרונות בחזרה של 5–10 דקות אם מתאפשר, ולא לפתוח עכשיו לימוד עצים מעמיק או Java. עדיפות לתרגול Python, תכנון בדיקות ודיבוג, יסודות רשתות ולוגיקה רלוונטית לפי המשרה שסופקה. אין להניח שהמראיין יודע או לא יודע על קורס מסוים, ואין בכך הבטחה שלא תופיע שאלת קוד. גם [משרת ולידציה קשורה באתר הרשמי של Marvell](https://marvell.wd1.myworkdayjobs.com/en-US/MarvellCareers/job/Hardware-Design-Intern_2502459) מזכירה Python/C++ ואוטומציה; זה מקור הקשר בלבד, לא המשרה המדויקת או מידע על שאלות הראיון.\n\n'
md+='## שלושה רמזים מדורגים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he+code
md+='\n\n[בדיקת מודל Python](../checks/check_prep_026.py) — Java ו־C++ לא קומפלו או הורצו.\n\n## English\n\n'+'\n\n'.join(f'Hint {i}: {h}' for i,h in enumerate(eh,1))+'\n\n'+en+'\n\nהתוכן נוצר בסיוע AI וממתין לסקירה; טרם פורסם באתר.\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-026 — עץ בינארי מול BST ומציאת מקסימום](questions/prep-026-binary-tree-bst-maximum.md) — נשמרו מקור, חברות, שלושה רמזים ופתרון; עדיפות נמוכה יחסית להכנה מוגבלת בזמן. קוד Java/C++ נשמר אך לא קומפל; מודל Python נבדק.\n',encoding='utf-8')
print('PREP-026 saved; 26 questions; source, hints, solutions and low-priority rationale stored with verification limits.')
