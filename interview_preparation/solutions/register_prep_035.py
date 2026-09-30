"""Preserve the supplied register-machine question and a checked proposal."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = '''OUTER:
    if r2 == 0: jump DONE
    r2--
ADD:
    if r1 == 0: jump RESTORE
    r1--
    r3++
    r4++
    if r1 != 0: jump ADD
RESTORE:
    if r3 == 0: jump OUTER
    r3--
    r1++
    if r3 != 0: jump RESTORE
    if r3 == 0: jump OUTER
DONE:
'''

# Tuple program: branches are zero/nonzero tests only; no copy/add/multiply.
OPS = [('z',1,13), ('dec',1), ('z',0,7), ('dec',0), ('inc',2),
       ('inc',3), ('nz',0,2), ('z',2,0), ('dec',2), ('inc',0),
       ('nz',2,7), ('z',2,0), ('halt',)]

def run(a,b):
    regs = [a,b,0,0]
    pc = steps = updates = 0
    while pc < len(OPS):
        op = OPS[pc]
        steps += 1
        assert steps < 100 * (a+1)*(b+1)
        if op[0] == 'halt':
            break
        if op[0] in ('z','nz'):
            cond = (regs[op[1]] == 0)
            if op[0] == 'nz':
                cond = not cond
            pc = op[2] if cond else pc+1
        else:
            regs[op[1]] += 1 if op[0] == 'inc' else -1
            assert min(regs) >= 0
            updates += 1
            pc += 1
    return regs, updates

def verify():
    cases = [(a,b) for a in range(31) for b in range(31)]
    cases += [(1,1000),(1000,1),(37,53),(53,37)]
    for a,b in cases:
        regs,updates = run(a,b)
        assert regs == [a,0,0,a*b], (a,b,regs)
        assert updates == 5*a*b+b
    return len(cases)

def main():
    count = verify()
    source = 'sources/prep-035.png'
    prompt = '''נתונים 4 רגיסטרים r[1-4]. מאתחלים אותם למצב הבא:
r1=a
r2=b
r3=0
r4=0
ניתן להשתמש רק בפקודות r++ (קידום ב־1), r-- (הפחתת 1), ו־jump(condition) — קפיצה לחלק קוד בתנאי.
בסוף הקוד צ״ל r4=ab.
(a,b חיוביים ושלמים)'''
    en_prompt = 'Four registers start at r1=a, r2=b, r3=0, r4=0, where a and b are positive integers. Using only register increment, decrement and conditional jumps, finish with r4=a*b.'
    hints = ['איך אפשר לפרק כפל לפעולה פשוטה שחוזרת כמה פעמים?', 'כיצד תוסיף את ערכו של רגיסטר לתוצאה בעזרת הגדלות והקטנות ב־1 בלבד? מה יקרה לערכו המקורי?', 'השתמש ברגיסטר השלישי כדי לזכור כמה יחידות העברת, ואז שחזר את הרגיסטר שנצרך לפני הסיבוב הבא.']
    en_hints = ['Express multiplication as a repeated simpler operation.', 'How can unit increments and decrements add a register value to the result? What happens to the source?', 'Use the third register to track transferred units and restore the consumed source before the next repetition.']
    he = '''הצעה לפתרון: כפל הוא חיבור חוזר. נבצע b סבבים, ובכל סבב נוסיף a יחידות ל־r4. אסור להשתמש בפקודת חיבור או העתקה, ולכן בכל צעד מקטינים את r1 ומגדילים גם את r4 וגם את r3. כך r3 זוכר את ערכו של a לאחר ש־r1 מתאפס. אחר כך מעבירים את היחידות מ־r3 חזרה ל־r1 בעזרת הקטנה והגדלה. r2 סופר כמה סבבים נשארו. אין במימוש רגיסטר חמישי, פקודת השמה, חיבור או כפל; האתחול היחיד הוא זה שנתון בשאלה. תוויות וכתובות קוד אינן רגיסטרי נתונים.

הנחות: מותר לבדוק אם רגיסטר שווה או שונה מאפס בפקודת הקפיצה. הרגיסטרים גדולים מספיק למכפלה ואין גלישה. אין דרישה לשמור את r2. הפעולות מתבצעות בטור. אם נדרש לשמור גם את b, זו דרישה נוספת שאינה נכללת בקוד הזה.

```text
'''+PROGRAM+'''```

כל if בקוד הוא פקודת קפיצה מותנית אחת, ולא פקודת עיבוד נוספת. שתי הקפיצות האחרונות משלימות את בקרת הלולאה בלי צורך בפקודת קפיצה לא מותנית. DONE מציין את סיום התוכנית, לא פעולה אריתמטית.

נכונות: בכניסה לסבב מספר k, אחרי k סבבים שהושלמו, מתקיים r1=a, r2=b-k, r3=0, r4=k*a. בסבב מקטינים את r2. אחרי j צעדי ADD מתקיים r1=a-j, r3=j, r4=k*a+j. אחרי a צעדים מתקבל r4=(k+1)*a, r1=0, r3=a. RESTORE מחזיר את r1 ל־a ואת r3 לאפס. כך נשמר התנאי לקראת הסבב הבא. אחרי b סבבים r2=0 והתוצאה ab. כל לולאה פנימית מסתיימת כי מונה טבעי קטן עד אפס.

למשל a=3,b=2: תחילה (3,2,0,0). אחרי הפחתת מונה ושלב ההוספה הראשון (0,1,3,3), אחרי השחזור (3,1,0,3). בסיום הסבב השני (3,0,0,6).

בסיום r1=a,r2=0,r3=0,r4=ab. הרחבה: אותו קוד מטפל גם באפס, אף שהמקור מבטיח חיוביים. אין ירידה לערכים שליליים. בקלטים חיוביים הזמן Theta(ab), והמקום ארבעה רגיסטרים, כלומר O(1) רגיסטרים במודל הנתון; אין זו טענת O(1) ביטים לערכים לא חסומים. מספר פקודות ההגדלה וההקטנה הוא 5ab+b, בנוסף לקפיצות. הזמן מיטבי אסימפטוטית במודל הזה: r4 מתחיל מאפס, ורק r4++ יכול להגדילו, ביחידה אחת בלבד; כדי להגיע ל־ab חייבים לפחות ab הגדלות שלו. אין טענה למינימום המדויק של כלל הפקודות או לאופטימליות תחת פקודות חזקות יותר.

תשובה קצרה לראיון: אממש חיבור חוזר. r2 סופר סבבים, r1 נסרק עד אפס תוך הגדלת התוצאה ו־r3, ואז משחזרים מ־r3 את r1 לסבב הבא. ההעתק הזמני חיוני כי החיבור צורך את ערך המקור.

טעויות נפוצות: כתיבת r4+=r1 או r3=r1 למרות האיסור; אי־שחזור r1; שכחת איפוס רגיסטר העזר; שימוש במשתנה לולאה נוסף שאינו אחד מארבעת הרגיסטרים; הנחת רוחב שמאפשר מכפלה ללא בדיקה.'''
    en = '''Proposed solution: repeat addition b times using only unit operations. Decrement r2 once per outer iteration. Transfer r1 down to zero while incrementing both r4 and temporary r3, then restore r1 by decrementing r3 and incrementing r1. No assignments beyond the supplied initial state and no fifth data register are needed. Labels are code addresses. Assume zero/nonzero branch tests are allowed, registers are wide enough without overflow, and r2 need not be preserved.

```text
'''+PROGRAM+'''```

At the outer boundary after k iterations the invariant is (r1,r2,r3,r4)=(a,b-k,0,k*a). After j ADD steps, r1=a-j,r3=j,r4=k*a+j. Restoration leaves (a,b-k-1,0,(k+1)*a). After b rounds the result is (a,0,0,ab). Each loop has a decreasing natural counter. Example a=3,b=2: (3,2,0,0), then (0,1,3,3) after first transfer, (3,1,0,3) after restoration, and (3,0,0,6) finally. Both zero inputs also work as an extension. No decrement below zero occurs.

Exactly 5ab+b increment/decrement instructions plus branch overhead. For positive inputs time is Theta(ab), space four registers (O(1) registers, not O(1) bits for unbounded values). This is asymptotically time-optimal for the specified instruction set: starting r4 at zero and only modifying it by one means at least ab increments of r4 are necessary. No claim of exact minimum instruction count. Each if is a conditional branch; DONE is program completion. Do not replace transfers with forbidden assignments or additions, forget restoration, or use hidden extra counters. Interview summary: count repetitions in r2, preserve consumed r1 through temporary r3, restore it after each repeated addition.'''
    p = ROOT/'questions.json'
    raw = p.read_text(encoding='utf-8')
    before = json.loads(raw)
    assert before['question_count']==34 and len(before['questions'])==34
    assert not any(q['id']=='PREP-035' for q in before['questions'])
    q = dict(id='PREP-035',key='multiply-four-registers-unit-instructions',version=1,created_on='2026-09-29',category='software',topic='restricted_instruction_programming',topics=['registers','loops','conditional_jumps','invariants','arithmetic'],source_topic_tags=['verification'],added_topic_tags=['registers','loops','conditional_jumps','invariants','arithmetic'],source_tags=['amazon','quantum-machines','maxlinear','nvidia','altair','samsung','apple','intel','verification'],reported_companies=['Amazon','Quantum Machines','MaxLinear','NVIDIA','Altair','Samsung','Apple','Intel'],source_company_badge='Samsung',company_attribution_status='reported_by_supplied_source_not_independently_verified',difficulty=None,estimated_minutes=None,format='coding',status='in_review',solution_status='proposed',solution_display_label='הצעה לפתרון',origin='user_supplied_screenshot',reviewed_by=None,ai_assisted=True,sources=[dict(type='user_supplied_image',path=source,received_on='2026-09-29')],original_prompt=prompt,translations={'he':dict(title='כפל באמצעות ארבעה רגיסטרים ופקודות הגדלה והקטנה בלבד',prompt=prompt,hint=hints[0],hints=hints,reference_solution=he),'en':dict(title='Multiplication with four registers and unit instructions',prompt=en_prompt,hint=en_hints[0],hints=en_hints,reference_solution=en)},prepared_hints=[dict(id=f'PREP-035-H{i+1:02}',level=i+1,language='he',content=h) for i,h in enumerate(hints)],assumptions=['Zero/nonzero conditional jumps are allowed.','Positive integers in source; zero tested as extension.','No overflow; sufficient register widths.','No requirement to preserve r2.'],optimality=dict(criterion='Asymptotic unit-instruction execution time',result='Theta(ab), matching the ab output-increment lower bound for positive inputs.',scope='Not minimum exact instruction count; four-register machine model.'),verification=dict(status='passed',checked_on='2026-09-29',script_path='solutions/register_prep_035.py',method=f'Interpreter using only increment/decrement and zero/nonzero branches: {count} input pairs, final register values, nonnegative intermediate values, update count and termination budget.'),media_assets=[dict(type='source_image',path=source)],interview_relevance=dict(priority='medium_high',label_he='כדאי לתרגל — תכנות בסיסי ומעקב אחרי מצב',basis='Preparation judgment based on the supplied system-validation role: loops, state tracking and careful constraint handling; no prediction of actual questions.'),related_question_ids=[],duplicate_check='No same four-register multiplication problem found in example_question or verify_example_questions.',markdown_path='questions/prep-035-register-multiplication.md')
    insert = raw.rfind('\n  ]')
    assert insert!=-1
    updated=raw[:insert]+',\n    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[insert:]
    updated=updated.replace('"question_count": 34','"question_count": 35',1)
    after=json.loads(updated)
    assert after['questions'][:-1]==before['questions'] and len(after['questions'])==35
    shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-9d89f241-a8ad-41a3-9947-5b94bf1f066c.png',ROOT/source)
    (ROOT/q['markdown_path']).write_text('# PREP-035 — '+q['translations']['he']['title']+'\n\n![מקור](../'+source+')\n\n'+prompt+'\n\n## סיווג ומקור\n\nתכנות, רגיסטרים, לולאות וקפיצות מותנות. עדיפות בינונית־גבוהה לפי התפקיד שסופק. חברות לפי הצילום בלבד, ללא אימות: '+', '.join(q['reported_companies'])+'. תגית המקור: verification; תג חברה ראשית: Samsung.\n\n## רמזים\n\n'+'\n'.join(f'{i+1}. {h}' for i,h in enumerate(hints))+'\n\n## הצעה לפתרון\n\n'+he+'\n\n## English\n\n'+en_prompt+'\n\n'+'\n'.join(en_hints)+'\n\n'+en+f'\n\nVerification: {count} interpreted cases passed. AI-assisted proposal; no expert review.\n',encoding='utf-8')
    p.write_text(updated,encoding='utf-8')
    with (ROOT/'README.md').open('a',encoding='utf-8') as f:
        f.write('\n- [PREP-035 — כפל באמצעות ארבעה רגיסטרים](questions/prep-035-register-multiplication.md) — נשמרו המקור, תגיות וחברות, שלושה רמזים ופתרון בשתי שפות עם בדיקת מפרש לפקודות המותרות.\n')
    print(f'PREP-035 saved; {count} cases passed; all 34 earlier question records unchanged.')

if __name__=='__main__':
    main()
