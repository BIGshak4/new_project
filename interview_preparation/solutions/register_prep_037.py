"""Preserve and verify the mixed-text bracket validation question."""
import itertools
import json
import random
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATCH={'(':')','[':']','{':'}'}

def valid_brackets(text):
    stack=[]
    for char in text:
        if char in MATCH:
            stack.append(char)
        elif char in ')]}':
            if not stack or MATCH[stack.pop()] != char:
                return False
    return not stack

def reduction_oracle(text):
    brackets=''.join(c for c in text if c in '()[]{}')
    while True:
        reduced=brackets.replace('()','').replace('[]','').replace('{}','')
        if reduced==brackets:
            return not reduced
        brackets=reduced

def verify():
    cases=0
    for length in range(7):
        for chars in itertools.product('()[]{}',repeat=length):
            text=''.join(chars)
            assert valid_brackets(text)==reduction_oracle(text),text
            cases+=1
    rng=random.Random(37)
    for _ in range(1000):
        text=''.join(rng.choice('()[]{}abc 123') for _ in range(rng.randrange(201)))
        assert valid_brackets(text)==reduction_oracle(text),text
        cases+=1
    examples={'':True,'abc':True,'aa()aa':True,'aa)a(a':False,'([]{})':True,'([)]':False,']':False,'((':False,'a{b[c](d)}':True,'()[]{}':True}
    for text,answer in examples.items():
        assert valid_brackets(text)==answer
        cases+=1
    assert valid_brackets('('*10000+')'*10000)
    assert not valid_brackets('('*10000+')'*9999)
    assert not valid_brackets('('*10000+']'+')'*9999)
    return cases+3

PSEUDO='''stack = empty stack

for each character c in the string:
    if c is '(' or '[' or '{':
        push(stack, c)

    else if c is ')' or ']' or '}':
        if stack is empty:
            return FALSE

        opening = pop(stack)
        if opening and c are not a matching pair:
            return FALSE

return (stack is empty)'''

def main():
    cases=verify()
    source='sources/prep-037.png'
    prompt='בהינתן מחרוזת המכילה תווים וסוגריים מכל הסוגים: (), [], {} — בדוק שהמחרוזת תקינה מבחינת סוגריים. למשל aa)a(a לא תקין אבל aa()aa כן תקין.'
    en_prompt='Given a string containing text and all three bracket types (), [], {}, check whether its brackets are valid. For example aa)a(a is invalid, whereas aa()aa is valid.'
    hints=['מה חייב להתאים לסוגר הסוגר הבא: הפותח הראשון, או הפותח האחרון שעדיין לא נסגר?', 'איזה מבנה נתונים מאפשר להוציא קודם את האיבר שנכנס אחרון?', 'שמור פותחים במחסנית. בכל סוגר סוגר בדוק שיש פותח זמין ושהסוג מתאים; בסיום בדוק שלא נשארו פותחים.']
    en_hints=['Which opener must match the next closer: the first, or the most recent still unmatched one?', 'Which structure returns the last item inserted first?', 'Push openers. For a closer, require a nonempty stack with a matching top. At the end require no unmatched openers.']
    he='''הצעה לפתרון: משתמשים במחסנית — מבנה שבו האחרון שנכנס הוא הראשון שיוצא, כמו ערימת צלחות. הסיבה אינה רק מספר הפותחים והסוגרים: בסוגריים מקוננים, הפותח האחרון שעדיין לא נסגר חייב להיסגר ראשון. למשל ב־([ ]) צריך לסגור את הסוגריים המרובעים לפני העגולים.

עוברים על המחרוזת משמאל לימין. סוגר פותח נכנס למחסנית. בסוגר סוגר, אם המחסנית ריקה מחזירים שקר; אחרת מוציאים את הפותח האחרון ובודקים שסוגו מתאים לסוגר הנוכחי. אי־התאמה מחזירה שקר. מתעלמים מתווים שאינם סוגריים. בסוף מחזירים אמת רק אם המחסנית ריקה.

```text
'''+PSEUDO+'''
```

זוגות חוקיים הם רק (), [], {}. פעולות push ו־pop מוסיפות לראש המחסנית ומוציאות ממנו. אפשר לממש במחסנית שהיא מערך עם אינדקס לראש: אין צורך במבנה נתונים מתקדם. בדיקת סוגים היא השוואה בין שלושת הזוגות; מיפוי קבוע אינו גדל עם אורך המחרוזת.

דוגמה תקינה a{b[c](d)}: אחרי { המחסנית {; אחרי [ היא {[; אחרי ] היא {; אחרי ( היא {(; אחרי ) היא {; אחרי } היא ריקה. האותיות אינן משנות את המחסנית. ב־([)] הכמויות מאוזנות לכל סוג, אבל כשהגיע ) בראש המחסנית יש [, ולכן דוחים מיד. ב־] מחסנית ריקה כבר בתו הראשון; ב־(( אין שגיאה בזמן הסריקה אבל המחסנית אינה ריקה בסוף. לכן כל שלוש הבדיקות נדרשות: אין סגירה בלי פתיחה, התאמת סוג בסדר קינון, ואין פתיחות שנותרו בסוף.

נכונות: אחרי כל קידומת שלא נדחתה, המחסנית מכילה בדיוק את הפותחים שעדיין לא נסגרו, לפי סדר הופעתם; האחרון בראש. פותח מוסיף פריט; סוגר מתאים מסיר רק את הפותח שצריך להיסגר כעת. סוגר לא מתאים או ללא פותח מעיד על הפרת קינון שכבר אי אפשר לתקן בהמשך. בסוף מחסנית ריקה שקולה לכך שכל הפתיחות נסגרו באופן תקין. מחרוזת ריקה או מחרוזת בלי סוגריים תקינות בהנחה שמבקשים תקינות ולא קיום סוגריים.

סיבוכיות: זמן O(n), ובמקרה הגרוע Theta(n), כי כל תו נסרק פעם אחת וכל סוגר נדחף ונשלף לכל היותר פעם אחת. זה מיטבי בסדר הגודל לבדיקת מחרוזת כללית, שבה שינוי תו שלא נקרא עלול לשנות תקינות. זיכרון O(d), כאשר d הוא מספר הפותחים המרבי בו־זמנית במחסנית, עד O(n) במקרה הגרוע. בקלט תקין זה עומק הקינון המרבי. אין טענה למינימום זיכרון גלובלי תחת כל מודל מעברים או שינוי קלט. אם יש רק סוג אחד של סוגריים מספיק מונה, בתנאי שבודקים שאינו נעשה שלילי ושבסוף הוא אפס; עבור שלושה סוגים מונים בלבד אינם שומרים את סדר הסגירה הדרוש.

הנחות: שלושת סוגי הסוגריים בלבד מיוחדים; כל שאר התווים נחשבים טקסט רגיל. אין כאן ניתוח שפת תכנות: סוגריים בתוך מחרוזות מצוטטות או הערות עדיין נחשבים סוגריים, כי המקור לא הגדיר חוקי ציטוט/escape. אין צורך לשנות את הקלט או לבצע רקורסיה. אם נדרשים כללי שפה, יש להוסיף שלב לקסיקלי לפני בדיקת הסוגריים.

תשובה קצרה לראיון: אסרוק פעם אחת עם מחסנית של פותחים. בסוגר סוגר אבדוק שהמחסנית אינה ריקה ושהוא מתאים לפותח שבראשה. בסוף אדרוש מחסנית ריקה. זמן לינארי וזיכרון לפי עומק הקינון, עד לינארי.

טעויות נפוצות: הסתפקות בספירת פותחים וסוגרים; התעלמות מסוג הסוגר; pop ממחסנית ריקה; החזרת אמת למרות פותחים שנותרו בסוף; דחיית אותיות למרות שהמקור מתיר אותן; שימוש בחיתוכים/מחיקות חוזרות שמביא לזמן ריבועי. פתרון המחיקות החוזרות משמש כאן אורקל בדיקה עצמאי בלבד ואינו הפתרון המומלץ.

נמצאה שאלה מקבילה SW-008 במאגר example_question. שם הקלט מכיל סוגריים בלבד; צילום זה מתיר גם טקסט ומוסיף תגיות חברות. הרשומה כאן מקושרת אליה, ואין לייחס בדיעבד חברות לשאלת SW-008 שנכתבה באופן עצמאי. חברות בצילום הן דיווח לא מאומת: Amazon, NVIDIA, Rafael, Marvell. תגית תוכן: software; תג החברה הראשית NVIDIA. עדיפות בינונית־גבוהה לתרגול קצר לקראת התפקיד שסופק, כי זה תרגיל בסיסי בקוד, סדר פעולות ובדיקת מקרי קצה; אין בכך תחזית לשאלת הראיון.'''
    en='''Proposed solution: use a stack of unmatched opening brackets. Last-in-first-out matches nesting: the most recently opened, still unmatched bracket must close first. Scan left to right; push (, [ or {. For ), ] or }, reject if empty, otherwise pop and require the corresponding type. Ignore other characters. Accept at the end only when the stack is empty.

```text
'''+PSEUDO+'''
```

The stack can be an array with a top index. The only matching pairs are (), [], {}. Example a{b[c](d)} leaves successive stacks {, {[, {, {(, {, empty when considering bracket characters. ([)] has equal counts of every type but fails when ) encounters [ on top. ] fails immediately; (( fails at end. Empty text and text without brackets are valid under the stated assumption.

Invariant: after every nonrejected prefix the stack contains exactly unmatched openers in order. Push preserves it; a matching closer removes precisely the required opener. Empty-stack closing and type mismatch are irreparable prefix violations. Final emptiness proves all openers were properly closed. Complexity O(n) time, Theta(n) worst-case and asymptotically optimal for arbitrary input inspection. Auxiliary memory O(d), the maximum concurrent unmatched-openers count, up to O(n). No global space-minimality claim over alternate computational models. For one bracket type a nonnegative-prefix counter ending at zero suffices; several type counts alone lose nesting order.

Assume all nonbracket text is ignored; this is not a programming-language lexer, so no special treatment of quotes, comments or escapes is specified. No recursion or input mutation is needed. Typical bugs: counting only, wrong pair types, popping empty, forgetting final emptiness, rejecting allowed letters, or repeated deletions with quadratic runtime. Repeated adjacent-pair deletion is used only as an independent test oracle.

Interview answer: one pass, push openers, match/pop each closer, require final emptiness; linear time and depth-bounded stack space. Related existing SW-008 limits input to brackets; this source permits ordinary text and supplies unverified Amazon/NVIDIA/Rafael/Marvell tags. Do not transfer those tags to the independently authored original. Medium-high priority for a short basic coding/edge-case review, based on the supplied role rather than a prediction.'''
    p=ROOT/'questions.json'; raw=p.read_text(encoding='utf-8'); before=json.loads(raw)
    assert before['question_count']==36 and len(before['questions'])==36
    q=dict(id='PREP-037',key='balanced-brackets-mixed-text',version=1,created_on='2026-09-29',category='software',topic='data_structures',topics=['stacks','strings','nested_brackets','invariants','edge_cases'],source_topic_tags=['software'],added_topic_tags=['stacks','strings','nested_brackets','invariants','edge_cases'],source_tags=['amazon','nvidia','software','rafael','marvell'],reported_companies=['Amazon','NVIDIA','Rafael','Marvell'],source_company_badge='NVIDIA',company_attribution_status='reported_by_supplied_source_not_independently_verified',difficulty=None,estimated_minutes=None,format='code',status='in_review',solution_status='proposed',solution_display_label='הצעה לפתרון',origin='user_supplied_screenshot',reviewed_by=None,ai_assisted=True,sources=[dict(type='user_supplied_image',path=source,received_on='2026-09-29'),dict(type='related_local_question',path='../example_question/software/data_structures/sw-008-balanced-brackets.md',question_id='SW-008',description='Same stack concept; this screenshot also allows nonbracket text. Company attribution belongs only to the supplied screenshot.')],original_prompt=prompt,translations={'he':dict(title='בדיקת תקינות סוגריים במחרוזת עם טקסט',prompt=prompt,hint=hints[0],hints=hints,reference_solution=he),'en':dict(title='Validate brackets in mixed text',prompt=en_prompt,hint=en_hints[0],hints=en_hints,reference_solution=en)},prepared_hints=[dict(id=f'PREP-037-H{i+1:02}',level=i+1,language='he',content=h) for i,h in enumerate(hints)],assumptions=['Only (), [] and {} are brackets.','Ignore other characters; no language-specific quote/comment rules.','Empty string and bracket-free text are valid.'],optimality=dict(criterion='Worst-case traversal time',result='Theta(n) time; O(d) stack space, at most O(n).',scope='No claim of exact minimum operations or universally optimal auxiliary memory.'),verification=dict(status='passed',checked_on='2026-09-29',script_path='solutions/register_prep_037.py',method=f'{cases} cases: all bracket words of length 0..6 against independent pair-reduction oracle; 1000 seeded mixed strings; 10 explicit examples; 3 deeply nested cases with 10000 opening parentheses.'),media_assets=[dict(type='source_image',path=source)],interview_relevance=dict(priority='medium_high',label_he='תרגול קצר שימושי — מחסנית ומקרי קצה',basis='Basic coding and validation discipline under supplied role; company attribution is unverified and not a prediction.'),related_question_ids=['SW-008'],duplicate_check='Matched SW-008 in example_question. Added one preparation entry with source-specific nonbracket-text allowance and provenance; no duplicate within current preparation bank.',markdown_path='questions/prep-037-balanced-brackets.md')
    pos=raw.rfind('\n  ]'); assert pos!=-1
    updated=raw[:pos]+',\n    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[pos:]
    updated=updated.replace('"question_count": 36','"question_count": 37',1)
    after=json.loads(updated); assert before['questions']==after['questions'][:-1] and len(after['questions'])==37
    shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-51e1d261-52be-4ad5-935b-39c815ab05b0.png',ROOT/source)
    md='# PREP-037 — '+q['translations']['he']['title']+'\n\n![מקור](../'+source+')\n\n'+prompt+'\n\n## רמזים\n\n'+'\n'.join(f'{i+1}. {h}' for i,h in enumerate(hints))+'\n\n## הצעה לפתרון\n\n'+he+'\n\n## English\n\n'+en_prompt+'\n\n'+'\n'.join(en_hints)+'\n\n'+en+f'\n\nVerification: {cases} test cases passed. AI-assisted proposal, no independent expert review.\n'
    (ROOT/q['markdown_path']).write_text(md,encoding='utf-8'); p.write_text(updated,encoding='utf-8')
    r=ROOT/'README.md'; body=r.read_text(encoding='utf-8')
    body=body.replace('תאריך הראיון המדויק ומתכונתו עדיין לא נמסרו.','ב־29 בספטמבר 2026 הראל ציין שהראיון מחר, כלומר 30 בספטמבר 2026. מתכונת הראיון לא נמסרה.')
    body+='\n- [PREP-037 — בדיקת סוגריים במחרוזת עם טקסט](questions/prep-037-balanced-brackets.md) — מקור ותגיות חברות, שלושה רמזים, פתרון דו־לשוני בדוק ומקרי קצה; מקושרת לשאלה המקבילה SW-008.\n'
    r.write_text(body,encoding='utf-8')
    print(f'PREP-037 saved; {cases} tests passed; all earlier 36 records unchanged; linked SW-008.')

if __name__=='__main__':
    main()
