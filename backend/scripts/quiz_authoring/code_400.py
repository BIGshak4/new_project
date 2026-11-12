"""115 substantive bilingual cases for the 23 new code fundamentals.

Author records stay draft. Independent oracles in test_fundamentals_code_400.py
check every recorded case and the actual short-card Python snippets. This file
does not edit old shards, release approvals, the assembler or browser fixtures.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "backend/seeds/duel_quiz_batches"
SOURCES = {q["id"]: q for q in json.loads((ROOT / "apps/web/src/content/fundamentals-code-400.json").read_bytes())}
QUESTIONS, CHECKS = [], []
RET = [("true", "מחזיר true", "Returns true"), ("false", "מחזיר false", "Returns false"),
       ("error", "זורק שגיאה", "Raises an error"), ("loops", "אינו מסתיים", "Does not terminate")]


def value_key(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def emit(n, v, task, args, he, en, options, expected, eh, ee):
    source = f"quick-sw-{n}"
    assert source in SOURCES
    if n == 189:
        he += " בהרחבה מפורשת מותרות כמה כתיבות בתהליך. התגים ייחודיים ואינם ממוחזרים באצווה; ACK מאשר השלמה ונראות. אין forwarding."
        en += " Explicit extension: several writes may be outstanding. Tags are unique and never reused within the batch; ACK confirms completion and visibility. No forwarding exists."
    if n == 193:
        # Half-open intervals intentionally use unlike brackets, not a prose typo.
        he = re.sub(r"\[\d+,\d+\)", lambda match: f"`{match[0]}`", he)
        en = re.sub(r"\[\d+,\d+\)", lambda match: f"`{match[0]}`", en)
        eh = re.sub(r"\[\d+,\d+\)", lambda match: f"`{match[0]}`", eh)
        ee = re.sub(r"\[\d+,\d+\)", lambda match: f"`{match[0]}`", ee)
    choices = [item if isinstance(item, tuple) else (item, "None" if item is None else value_key(item), "None" if item is None else value_key(item)) for item in options]
    assert len(choices) == len({value_key(item[0]) for item in choices}) == 4, (n, v)
    assert sum(value_key(item[0]) == value_key(expected) for item in choices) == 1, (n, v)
    shift = (n + v) % 4
    choices = choices[shift:] + choices[:shift]
    correct = next(i for i, item in enumerate(choices) if value_key(item[0]) == value_key(expected))
    key = f"{source}-v{v}"
    QUESTIONS.append(dict(key=key, source_key=source, variant=v, topic=SOURCES[source]["topic"], status="draft",
                          prompt=dict(he=he, en=en), choices=[dict(he=h, en=e) for _, h, e in choices], correct=correct,
                          explanation=dict(he=eh, en=ee)))
    CHECKS.append(dict(key=key, task=task, inputs=args, options=[item[0] for item in choices], expected=expected,
                       method="Independent case oracle and counterexample checks in backend/tests/test_fundamentals_code_400.py"))


def early_groups():
    emit(178, 1, "matrix_count", {"a": [[-5, -2, 0], [-1, 2, 4]]},
         "השורות והעמודות של [[-5,-2,0],[-1,2,4]] ממוינות בסדר לא יורד. כמה תאים שליליים יש? אפס אינו שלילי.",
         "Rows and columns of [[-5,-2,0],[-1,2,4]] are nondecreasing. How many cells are negative? Zero is not negative.",
         [2, 3, 4, 5], 3, "בשורה העליונה 2 שליליים ובתחתונה 1; יחד 3.", "The upper row has 2 negatives and the lower row 1: total 3.")
    emit(178, 2, "matrix_count", {"a": [[0, 0], [0, 1]]},
         "במטריצה ממוינת [[0,0],[0,1]] סופרים ערכים הקטנים ממש מאפס. מה מוחזר?",
         "For sorted matrix [[0,0],[0,1]], count values strictly below zero. What is returned?",
         [0, 1, 3, 4], 0, "אפס אינו שלילי; כל 4 התאים אינם שליליים, ולכן מוחזר 0.", "Zero is not negative; all 4 cells are nonnegative, so return 0.")
    emit(178, 3, "negative_row_certificate", {"row": [-7, -3, -1, 4], "j": 2},
         "שורה ממוינת היא [-7,-3,-1,4]. בסריקת מדרגות נבדק התא השלילי באינדקס 2. כמה תאים בשורה עד אליו אפשר לספור בלי השוואות נוספות?",
         "A sorted row is [-7,-3,-1,4]. A staircase scan checks the negative cell at index 2. How many row cells through it are certified without further comparisons?",
         [1, 2, 3, 4], 3, "האינדקס מבוסס אפס, ולכן הקידומת כוללת 2+1=3 תאים שליליים.", "The index is zero-based, so the prefix contains 2+1=3 negative cells.")
    emit(178, 4, "staircase_visits", {"a": [[-5, -2, 0], [-1, 2, 4]]},
         "ב־[[-5,-2,0],[-1,2,4]] מתחילים מימין למעלה: בערך שלילי יורדים שורה, ובאחר זזים שמאלה. כמה תאים נבדקים עד יציאה מהגבולות?",
         "For [[-5,-2,0],[-1,2,4]], start top-right: move down on a negative value and left otherwise. How many cells are checked before leaving the matrix?",
         [3, 4, 5, 6], 4, "נבדקים 0,-2,2,-1: בסך הכול 4 תאים, ללא סריקת כל המטריצה.", "The checked values are 0,-2,2,-1: 4 cells, without scanning the entire matrix.")
    emit(178, 5, "matrix_missing_order", {"a": [[1, -1], [2, 0]]},
         "העמודות של [[1,-1],[2,0]] ממוינות, אבל השורות אינן. ספירת כל הקידומת בשורה בגלל ‎-1 בפינה העליונה־ימנית שגויה. איזו הבטחה חסרה?",
         "Columns of [[1,-1],[2,0]] are sorted but rows are not. Counting the entire row prefix from top-right value -1 is wrong. Which missing guarantee invalidates that step?",
         [("rows", "מיון השורות", "Sorted rows"), ("unique", "ערכים שונים", "Distinct values"), ("square", "מטריצה ריבועית", "A square matrix"), ("positive", "כל הערכים חיוביים", "All values positive")], "rows",
         "‎-1 אינו מוכיח שהתא 1 שמשמאלו שלילי; חסר מיון השורות.", "Value -1 cannot certify that the preceding 1 is negative; row ordering is missing.")

    emit(179, 1, "merge_last", {"a": [1, 7], "b": [3, 5]},
         "ממזגים במקום מהסוף את a=[1,7] ואת שני נתוני b=[3,5], עם 2 תאים פנויים בסוף b. מה הערך הראשון שנכתב לתא האחרון?",
         "Merge a=[1,7] into b's two data values [3,5], with 2 spare slots at b's end. Working backward, which value is written first into the last slot?",
         [1, 3, 5, 7], 7, "הגדול מבין שני הזנבות הוא 7; הוא שייך למקום הימני ביותר.", "The larger unread tail is 7, which belongs in the rightmost position.")
    emit(179, 2, "merge_b_prefix", {"a": [8, 9], "b": [1, 2]},
         "אחרי מיזוג אחורי של a=[8,9] לתוך b=[1,2,_,_], כל איברי a נכתבו. איזו קידומת של b אפשר להשאיר בלי העתקה נוספת?",
         "After backward-merging a=[8,9] into b=[1,2,_,_], all a values have been written. Which b prefix can stay without another copy?",
         [[1, 2], [8, 9], [1], []], [1, 2], "הקידומת [1,2] כבר במקומה; רק הנתונים שהגיעו מ־a מילאו את הזנב.", "Prefix [1,2] is already placed; values from a filled only the tail.")
    emit(179, 3, "merge_all", {"a": [0, 3], "b": [0, 2]},
         "ב־b שני נתוני קלט [0,2] ועוד 2 תאים פנויים; a=[0,3]. אפס הוא נתון חוקי. מה כל הפלט הממוזג?",
         "Array b has two data values [0,2] and 2 spare slots; a=[0,3]. Zero is valid data. What is the complete merged output?",
         [[0, 0, 2, 3], [0, 2, 3], [0, 2], [0, 0, 0, 3]], [0, 0, 2, 3],
         "סופרים את m נתוני b לפי האורך, לא לפי ערכם; שני מופעי 0 נשמרים.", "Use m to identify b's data, not their values; both occurrences of 0 survive.")
    emit(179, 4, "forward_overwrite", {"a": [1, 3], "b": [2, 4]},
         "מיזוג שגוי מתחיל לכתוב קדימה לתוך b=[2,4,_,_] מתוך a=[1,3], בלי לשמור נתונים שנדרסים. כתיבת 1 ב־b[0] מאבדת איזה נתון שטרם נקרא?",
         "A faulty forward merge writes into b=[2,4,_,_] from a=[1,3], without saving overwritten data. Writing 1 into b[0] destroys which unread value?",
         [1, 2, 3, 4], 2, "התא b[0] הכיל 2 שעדיין צריך למזג; כתיבה אחורית מגינה על קלט זה.", "Slot b[0] held the still-needed 2; backward writing protects that input.")
    emit(179, 5, "merge_all", {"a": [2, 2], "b": [2]},
         "ממזגים a=[2,2] ונתון b=[2] לתוך b בעל 2 תאים נוספים. מותרות כפילויות. מה הפלט?",
         "Merge a=[2,2] and b's data [2] into b with 2 additional slots. Duplicates are allowed. What is the output?",
         [[2], [2, 2], [2, 2, 2], [0, 2, 2]], [2, 2, 2], "מיזוג שומר הופעות; שוויון אינו רשות למחוק נתון.", "Merging preserves occurrences; equality does not authorize dropping data.")

    emit(180, 1, "triple_index_count", {"a": [0, 0, 0, 0], "target": 0},
         "כמה שלשות אינדקסים i<j<k במערך [0,0,0,0] סכומן 0? כאן סופרים הופעות, לא שלשות ערכים ייחודיות.",
         "How many index triples i<j<k in [0,0,0,0] sum to 0? Count occurrences, not distinct value triples.",
         [1, 3, 4, 6], 4, "בוחרים 3 מתוך 4 אינדקסים; יש 4 בחירות למרות שלשת ערכים יחידה.", "Choose 3 of 4 indices: 4 choices despite a single value triple.")
    emit(180, 2, "triple_unique", {"a": [-1, -1, 2], "target": 0},
         "מחפשים שלשות ערכים ייחודיות מסכום 0 ב־[-1,-1,2], תוך שימוש באינדקסים שונים. כמה שלשות יאבדו אם נהפוך את הקלט לקבוצת ערכים לפני החיפוש?",
         "Seek distinct value triples summing to 0 in [-1,-1,2], using different indices. How many valid triples disappear if the input is deduplicated before searching?",
         [0, 1, 2, 3], 1, "השלשה (-1,-1,2) זקוקה לשתי הופעות של ‎-1; קבוצה מוחקת אחת מהן.", "Triple (-1,-1,2) requires two occurrences of -1; a set removes one.")
    emit(180, 3, "next_anchor", {"a": [-2, -2, -2, 0, 1], "i": 0},
         "במערך ממוין [-2,-2,-2,0,1] הסתיים הטיפול בעוגן באינדקס 0. כדי להימנע משלשות ערכים כפולות, מה אינדקס העוגן הבא בעל ערך חדש?",
         "In sorted [-2,-2,-2,0,1], processing anchor index 0 is finished. To avoid repeated value triples, which index is the next anchor with a new value?",
         [1, 2, 3, 4], 3, "האינדקסים 1 ו־2 חוזרים על ערך העוגן; הערך הבא מתחיל באינדקס 3.", "Indices 1 and 2 repeat the anchor value; the next value starts at index 3.")
    emit(180, 4, "triple_value_count", {"a": [-1, 0, 1, 2, -1, -4], "target": 0},
         "כמה שלשות ערכים ייחודיות מסכום 0 יש ב־[-1,0,1,2,-1,-4]? כל שלשה משתמשת בשלושה אינדקסים שונים.",
         "How many distinct value triples sum to 0 in [-1,0,1,2,-1,-4]? Each uses three different indices.",
         [1, 2, 3, 4], 2, "רק (-1,-1,2) ו־(-1,0,1) מתאימות; כפילות של אינדקסים אינה פלט נוסף.", "Only (-1,-1,2) and (-1,0,1) qualify; repeated index realizations do not add outputs.")
    emit(180, 5, "triple_value_count", {"a": [2, 3, 4, 5], "target": 6},
         "במערך הממוין [2,3,4,5] אפילו סכום שלושת הקטנים גדול מ־6. כמה שלשות מסכום 6 יכולות להישאר לחיפוש?",
         "In sorted [2,3,4,5], even the three smallest values sum above 6. How many sum-6 triples can remain to search?",
         [0, 1, 2, 4], 0, "הסכום המזערי הוא 2+3+4=9, ולכן אין שלשה מסכום 6.", "The minimum sum is 2+3+4=9, so no sum-6 triple exists.")

    emit(181, 1, "first_free", {"used": 11, "n": 4},
         "במסכה בת 4 ביטים 1011, ביט 1 תפוס ו־0 פנוי. האינדקסים מתחילים מ־0 ב־LSB. מה אינדקס התא הפנוי הראשון?",
         "In 4-bit bitmap 1011, 1 is occupied and 0 free. Indices start at 0 at the LSB. What is the first free index?",
         [0, 1, 2, 3], 2, "הביט הפנוי היחיד הוא באינדקס 2.", "The only free bit has index 2.")
    emit(181, 2, "first_free", {"used": 15, "n": 4},
         "מוצאים תא פנוי רק בתחום 4 הביטים של 1111. מה מחזירה first_free, שמחזירה None כשאין מקום?",
         "Find a free slot only within the 4 bits of 1111. What does first_free return, using None when full?",
         [None, 0, 3, 4], None, "כל הביטים החוקיים תפוסים; ביטים מחוץ לרוחב אינם תאים נוספים.", "All valid bits are occupied; bits outside the width are not extra slots.")
    emit(181, 3, "first_free", {"used": 0, "n": 0},
         "מקצה מאפשר n=0 תאים ומשתמש במסכה 0. מה מחזיר חיפוש התא הפנוי הראשון: אינדקס חוקי או None?",
         "An allocator permits n=0 slots and uses bitmap 0. What does first-free search return: a valid index or None?",
         [None, 0, 1, -1], None, "אין תחום תאים; המסכה המוגבלת אפס ולכן אין אינדקס פנוי.", "There are no slots; the bounded free mask is zero, so no free index exists.")
    emit(181, 4, "bounded_complement", {"used": 0, "n": 3},
         "בפייתון ~0 הוא ‎-1. מהו (~0)&((1<<3)-1), כשמגבילים את התאים הפנויים לרוחב 3?",
         "In Python ~0 is -1. What is (~0)&((1<<3)-1), restricting free slots to width 3?",
         [-1, 0, 3, 7], 7, "מסכת הרוחב היא 7, ולכן נשארים בדיוק 3 הביטים הנמוכים.", "The width mask is 7, retaining exactly the lowest 3 bits.")
    emit(181, 5, "bounded_complement", {"used": 240, "n": 8},
         "מסכת תפוסה בת 8 ביטים היא 11110000. מה ערך מסכת הפנויים לאחר משלים מוגבל לאותו רוחב, ולא אינדקס של תא?",
         "The 8-bit occupied mask is 11110000. What is the bounded free-mask value, rather than a slot index?",
         [0, 4, 15, 240], 15, "המסכה הפנויה היא 00001111, שערכה 15; זהו דפוס ביטים ולא אינדקס.", "The free mask is 00001111, value 15; it is a bit pattern, not an index.")

    emit(182, 1, "palindrome", {"s": "Aa"},
         "בדיקת פלינדרום של אותיות ASCII רגישה לאותיות גדולות וקטנות. מה היא מחזירה עבור Aa?",
         "An ASCII-letter palindrome check is case-sensitive. What does it return for Aa?",
         RET, "false", "A שונה מ־a, ולכן הזוג הסימטרי נכשל.", "A differs from a, so the symmetric pair fails.")
    emit(182, 2, "palindrome", {"s": ""},
         "לפי החוזה, מחרוזת ריקה היא פלינדרום. מה מחזירה בדיקה שמשווה את כל הזוגות הסימטריים של הקלט הריק?",
         "By contract, the empty string is a palindrome. What does a check of all its symmetric pairs return?",
         RET, "true", "אין זוג מפר; all על קבוצת בדיקות ריקה מחזיר true.", "There is no violating pair; all over an empty set of checks returns true.")
    emit(182, 3, "palindrome_pairs", {"s": "abcba"},
         "כמה זוגות סימטריים שונים צריך לבדוק במחרוזת abcba, בלי להשוות את התו האמצעי לעצמו?",
         "How many distinct symmetric pairs must be checked in abcba, excluding a self-comparison of the middle character?",
         [1, 2, 3, 5], 2, "באורך 5 יש 5//2=2 זוגות; התו האמצעי אינו מוסיף תנאי.", "Length 5 gives 5//2=2 pairs; the middle character adds no condition.")
    emit(182, 4, "palindrome_checks", {"s": "abcda"},
         "בדיקת פלינדרום ב־abcda מתחילה מהקצוות ועוצרת באי־שוויון הראשון. כמה השוואות בין תווים היא מבצעת?",
         "A palindrome check on abcda starts at the ends and stops at the first mismatch. How many character comparisons does it make?",
         [1, 2, 3, 5], 2, "תחילה a מול a, ואחר כך b מול d. ההשוואה השנייה פוסלת.", "First compare a with a, then b with d. The second comparison rejects.")
    emit(182, 5, "palindrome", {"s": "abYba"},
         "בפלינדרום abXba מחליפים רק את התו האמצעי X ב־Y. מה מחזירה אותה בדיקה רגישה לאותיות עבור abYba?",
         "Replace only the central X of palindrome abXba with Y. What does the same case-sensitive check return for abYba?",
         RET, "true", "הזוגות החיצוניים לא השתנו; התו האמצעי יכול להיות כל אות.", "The outer pairs are unchanged; the middle can be any letter.")

    emit(183, 1, "free_allocate_head", {"free": [2, 4, 6]},
         "רשימת התאים החופשיים היא 2→4→6. מקצים את התא 2, קוראים תחילה את קישורו, ואז המשתמש רשאי לדרוס אותו. מה הראש החדש?",
         "The free list is 2→4→6. Allocate slot 2, first reading its link; the caller may then overwrite it. What is the new head?",
         [2, 4, 6, None], 4, "הראש מתקדם לקישור 4 לפני העברת הבעלות על התא 2.", "Advance the head to link 4 before transferring ownership of slot 2.")
    emit(183, 2, "free_prepend_link", {"free": [4, 6], "slot": 1},
         "הראש החופשי הוא 4. משחררים תא מוקצה 1 ומכניסים אותו לראש הרשימה. איזה קישור כותבים בתא 1 לפני עדכון הראש?",
         "The free head is 4. Free allocated slot 1 and prepend it. Which link is written in slot 1 before updating the head?",
         [1, 4, 6, None], 4, "התא ששוחרר מצביע לראש הקודם 4; אחר כך הראש נהיה 1.", "The freed slot points to the previous head 4; the head then becomes 1.")
    emit(183, 3, "free_allocate_result", {"free": []},
         "מקצה מחזיר None כשאין תא חופשי. הראש כבר None. מה מוחזר מניסיון הקצאה בלי גישה לתוכן של תא כלשהו?",
         "An allocator returns None when no slot is free. Its head is already None. What does allocation return without reading any slot payload?",
         [None, 0, -1, 1], None, "ראש ריק פירושו מיצוי התאים; אין לקרוא תא דרך None.", "An empty head means exhaustion; no slot may be read through None.")
    emit(183, 4, "free_ownership", {"free": [3, 5], "allocated": 2, "payload": 99},
         "רק התאים 3→5 חופשיים. המשתמש כותב 99 בתא המוקצה 2. מה סדר התאים החופשיים אחרי הכתיבה, אם הבעלות מנוהלת נכון?",
         "Only slots 3→5 are free. A caller writes 99 into allocated slot 2. What is the free-list order afterward under correct ownership?",
         [[3, 5], [2, 3, 5], [99, 5], [5]], [3, 5], "תוכן תא מוקצה אינו קישור חופשי; הרשימה 3→5 אינה משתנה.", "Allocated payload is not a free link; list 3→5 remains unchanged.")
    emit(183, 5, "double_free_link", {"slot": 2},
         "מימוש ללא בדיקת double-free משחרר את תא 2, ואז משחרר אותו שוב כשהראש כבר 2. בכל שחרור כותבים בתא את הראש הישן. לאן יפנה הקישור שבתא 2?",
         "Without double-free validation, slot 2 is freed and then freed again when the head is already 2. Each free stores the old head in the slot. Where does slot 2's link point?",
         [None, 0, 1, 2], 2, "הקישור נהיה 2→2, מעגל עצמי; זו הדגמת תקלה ולא פעולה חוקית.", "The link becomes 2→2, a self-cycle; this demonstrates a fault, not a valid free.")

    for v, tokens, expected, he, en, eh, ee, options in [
        (1, [8, 3, "-"], 5, "מה תוצאת ביטוי postfix: 8 3 -?", "What is the result of postfix expression 8 3 -?", "שולפים ימין 3 ושמאל 8; התוצאה 5.", "Pop right 3 and left 8; the result is 5.", [5, -5, 11, 24]),
        (2, [8, 2, "/"], 4, "חילוק מדויק: מה תוצאת postfix של 8 2 /?", "Using exact division, what is postfix 8 2 /?", "הסדר הוא 8/2=4, ולא 2/8.", "The order is 8/2=4, not 2/8.", [4, 0.25, 6, 16]),
        (3, [2, 3, 4, "*", "+"], 14, "מה תוצאת postfix של 2 3 4 * +?", "What is the result of postfix 2 3 4 * +?", "קודם 3*4=12, ואז 2+12=14.", "First 3*4=12, then 2+12=14.", [14, 20, 9, 24]),
        (4, [8, "-"], "underflow", "מעריך postfix דורש שני אופרנדים לחיסור. איזו בעיה מתגלה ב־8 -?", "A postfix evaluator requires two operands for subtraction. What fails in 8 -?", "יש רק אופרנד אחד; מדובר במחסור במחסנית.", "Only one operand is available: stack underflow.", [("underflow", "חסר אופרנד", "Missing operand"), ("extra", "נשאר עודף", "Extra result"), ("valid", "ביטוי חוקי", "Valid expression"), ("zero", "תוצאה אפס", "Zero result")]),
        (5, [1, 2], "extra", "בסוף postfix תקין נשאר ערך אחד. מה הבעיה בביטוי 1 2 ללא פעולה?", "A valid postfix expression ends with one value. What fails in expression 1 2 with no operator?", "נשארים שני ערכים ולא תוצאה יחידה.", "Two values remain rather than one result.", [("extra", "עודף תוצאות", "Extra results"), ("underflow", "חסר אופרנד", "Missing operand"), ("valid", "ביטוי חוקי", "Valid expression"), ("division", "חילוק באפס", "Division by zero")]),
    ]:
        emit(184, v, "postfix", {"tokens": tokens}, he, en, options, expected, eh, ee)

    emit(185, 1, "stack_min", {"push": [5, 2, 2], "pops": 1},
         "דוחפים למחסנית מינימום 5,2,2 ושולפים פעם אחת. מה FindMin מחזירה?",
         "Push 5,2,2 into a minimum stack and pop once. What does FindMin return?",
         [2, 5, None, 0], 2, "מופע נוסף של 2 עדיין במחסנית; שליפה אחת אינה מוחקת את שניהם.", "Another occurrence of 2 remains; one pop does not remove both.")
    emit(185, 2, "stack_min", {"push": [4], "pops": 1},
         "במחסנית הוגדר ש־FindMin מחזירה None כשהיא ריקה. דוחפים 4 ושולפים אותו. מה מוחזר?",
         "FindMin is defined to return None for an empty stack. Push 4 and pop it. What is returned?",
         [None, 4, 0, -1], None, "לא נשאר איבר; אין להחזיר מינימום היסטורי של קידומת שכבר הוסרה.", "No item remains; a removed prefix's historical minimum must not be returned.")
    emit(185, 3, "stack_min", {"push": [3, 7], "pops": 0},
         "דוחפים 3 ואחריו 7. Top מחזירה 7; מה FindMin צריכה להחזיר?",
         "Push 3 followed by 7. Top returns 7; what should FindMin return?",
         [3, 7, 10, None], 3, "ראש המחסנית והערך המזערי הם שאילתות שונות; המינימום הוא 3.", "The top and minimum are different queries; the minimum is 3.")
    emit(185, 4, "stack_min_after_replace", {"first": 2, "next": 3},
         "דוחפים 2, שולפים אותו, ואז דוחפים 3. אין איברים אחרים. מה FindMin מחזירה?",
         "Push 2, pop it, then push 3. No other items exist. What does FindMin return?",
         [2, 3, None, 0], 3, "הערך 2 כבר אינו חלק מהמחסנית; המינימום החדש 3.", "Value 2 is no longer in the stack; the new minimum is 3.")
    emit(185, 5, "prefix_minima", {"a": [4, 1, 3]},
         "ליד כל איבר במחסנית [4,1,3] שומרים את מינימום הקידומת עד אליו. מה רצף ערכי העזר, מלמטה למעלה?",
         "Beside each item of stack [4,1,3], store its prefix minimum. What are the auxiliary values from bottom to top?",
         [[4, 1, 1], [4, 1, 3], [1, 1, 1], [3, 1, 4]], [4, 1, 1], "הקידומות הן [4], [4,1], [4,1,3]; מינימיהן 4,1,1.", "Prefixes are [4], [4,1], [4,1,3]; their minima are 4,1,1.")


def middle_groups():
    emit(186, 1, "filter_below", {"a": [3, 4, 20], "t": 19},
         "מוחקים מרשימת Python [3,4,20] את כל הערכים שמתחת ל־19, בסריקה מהסוף. מה נשאר?",
         "Delete all values below 19 from Python list [3,4,20], scanning backward. What remains?",
         [[20], [4, 20], [3, 20], []], [20], "שני הערכים הסמוכים 3 ו־4 נמחקים; אין דילוג לאחר הזזה.", "Adjacent values 3 and 4 are both removed; shifting causes no skip.")
    emit(186, 2, "naive_forward_delete", {"a": [3, 4, 20], "t": 19},
         "ב־[3,4,20] מוחקים ערך מתחת ל־19 ואז תמיד מגדילים אינדקס, גם לאחר מחיקה. מה נשאר במימוש קדמי שגוי זה?",
         "In [3,4,20], delete values below 19, always incrementing the index even after deletion. What remains in this faulty forward implementation?",
         [[4, 20], [20], [3, 20], []], [4, 20], "אחרי מחיקת 3, הערך 4 זז לאינדקס שכבר לא ייבדק.", "After deleting 3, value 4 shifts into an index that will not be checked.")
    emit(186, 3, "backward_indices", {"n": 3},
         "מה רצף האינדקסים ב־range(len(a)-1,-1,-1) כאשר אורך הרשימה 3, לפני השפעת מחיקות?",
         "What indices does range(len(a)-1,-1,-1) produce for a list of length 3, before accounting for deletion effects?",
         [[2, 1, 0], [3, 2, 1], [2, 1], [0, 1, 2]], [2, 1, 0], "תחילת הסריקה באינדקס 2; הגבול ‎-1 אינו נכלל ולכן גם 0 נבדק.", "Start at index 2; excluded bound -1 ensures index 0 is still checked.")
    emit(186, 4, "filter_below", {"a": [20, 3, 21, 4], "t": 19},
         "דחיסה יציבה שומרת מ־[20,3,21,4] רק ערכים שלפחות 19. מה סדר הפלט?",
         "Stable compaction retains only values at least 19 from [20,3,21,4]. What is the output order?",
         [[20, 21], [21, 20], [3, 4], [20, 3, 21]], [20, 21], "יציבות שומרת את סדר 20 לפני 21; הערכים 3 ו־4 נמחקים.", "Stability preserves 20 before 21; values 3 and 4 are removed.")
    emit(186, 5, "delete_shifts", {"n": 8, "i": 0},
         "במערך רציף באורך 8 מוחקים את התא באינדקס 0 ושומרים סדר באמצעות הזזת הזנב. כמה איברים חייבים לזוז בפעולה הזאת?",
         "In a contiguous array of length 8, delete index 0 while preserving order by shifting the suffix. How many elements move in this operation?",
         [0, 1, 7, 8], 7, "כל 7 האיברים שמימין למחיקה זזים; נכונות סריקה אינה הופכת מחיקה לזמן קבוע.", "All 7 elements after the deletion move; traversal correctness does not make deletion constant-time.")

    emit(187, 1, "first_equal", {"a": [1, 2, 2, 4], "x": 2},
         "חיפוש מדויק במערך ממוין [1,2,2,4] צריך להחזיר את המופע הראשון של 2. מה האינדקס מבוסס האפס?",
         "Exact search in sorted [1,2,2,4] must return the first occurrence of 2. What is its zero-based index?",
         [0, 1, 2, 3], 1, "lower_bound מגיע לאינדקס 1, הראשון שערכו לפחות 2 ושווה לו.", "lower_bound reaches index 1, the first value at least 2 and equal to it.")
    emit(187, 2, "first_equal", {"a": [1, 3, 5], "x": 2},
         "lower_bound של 2 במערך [1,3,5] הוא 1. פונקציית חיפוש מדויק מחזירה ‎-1 בהיעדר התאמה. מה היא צריכה להחזיר?",
         "The lower_bound of 2 in [1,3,5] is 1. An exact-search function returns -1 when absent. What must it return?",
         [-1, 0, 1, 2], -1, "באינדקס 1 נמצא 3 ולא 2; מקום הכנסה אינו התאמה.", "Index 1 contains 3 rather than 2; an insertion position is not a match.")
    emit(187, 3, "first_equal", {"a": [], "x": 4},
         "חיפוש מדויק מחזיר ‎-1 כשאין ערך. מה תוצאת חיפוש 4 במערך הריק, בלי לקרוא תא כלשהו?",
         "Exact search returns -1 when absent. What is the result of searching for 4 in an empty array without reading any cell?",
         [-1, 0, 4, None], -1, "האינדקס שווה לאורך 0; בדיקת הגבול מונעת גישה לא חוקית.", "The candidate index equals length 0; the bounds check prevents invalid access.")
    emit(187, 4, "lower_bound", {"a": [1, 3, 5], "x": 9},
         "מה lower_bound מחזיר עבור 9 במערך [1,3,5], כאשר אין איבר שערכו לפחות 9? זו שאילתת גבול, לא חיפוש מדויק.",
         "What does lower_bound return for 9 in [1,3,5] when no item is at least 9? This asks for the boundary, not exact-search failure.",
         [-1, 0, 2, 3], 3, "גבול ההכנסה הוא אורך המערך 3; אין לקרוא a[3].", "The insertion boundary is array length 3; a[3] must not be read.")
    emit(187, 5, "first_equal", {"a": [5, 5, 5, 5], "x": 5},
         "כל הערכים ב־[5,5,5,5] שווים ליעד 5. חיפוש שמחזיר את המופע הראשון חייב להחזיר איזה אינדקס?",
         "Every value in [5,5,5,5] equals target 5. Which index must a first-occurrence search return?",
         [0, 1, 2, 3], 0, "גם כאשר כל הבדיקות פוגשות שוויון, הגבול השמאלי נשאר 0.", "Even when every comparison finds equality, the left boundary remains 0.")

    for v, n, capacity, he, en in [
        (1, 0, 2, "כמה תאי char דרושים לטקסט בינארי מינימלי של 0, כולל NUL?", "How many char slots hold minimal binary text for 0, including NUL?"),
        (2, 8, 5, "כמה תאי char דרושים לטקסט 1000 של המספר 8, כולל NUL?", "How many char slots hold text 1000 for number 8, including NUL?"),
        (3, 255, 9, "מה קיבולת המחרוזת הדרושה ל־255 בלתי מסומן, בייצוג בינארי מינימלי כולל NUL?", "What string capacity is needed for unsigned 255 in minimal binary, including NUL?"),
    ]:
        opts = [capacity, capacity - 1, capacity + 1, capacity + 2]
        emit(188, v, "binary_capacity", {"n": n}, he, en, opts, capacity,
             "סופרים לפחות ספרה אחת, ומוסיפים תא אחד ל־NUL.", "Count at least one digit, then add one slot for NUL.")
    emit(188, 4, "binary_fits", {"n": 255, "capacity": 8},
         "ממיר מספר 255 לטקסט בינארי מינימלי עם NUL, ובודק קיבולת לפני כתיבה. למאגר יש 8 תאי char בלבד. האם הוא יכול לכתוב את כל המחרוזת?",
         "A converter writes minimal binary text for 255 with NUL, checking capacity first. The buffer has only 8 char slots. Can it write the complete string?",
         [("no", "לא, חסר תא לסיום", "No, the terminator lacks a slot"), ("yes", "כן, מספיק בדיוק", "Yes, it fits exactly"), ("skip", "כן, אם מתעלמים מ־NUL", "Yes, ignoring NUL is allowed"), ("negative", "לא, כי 255 שלילי", "No, because 255 is negative")], "no",
         "נדרשים 8 תווי ספרה ועוד NUL: סך הכול 9 תאים.", "There are 8 digit characters plus NUL: 9 slots total.")
    emit(188, 5, "fixed_binary_capacity", {"width": 8},
         "כעת החוזה דורש תמיד 8 ספרות בינאריות, כולל אפסים מובילים, ואחריהן NUL. כמה תאי char נדרשים גם לקלט 1?",
         "Now the contract always requires 8 binary digits, including leading zeros, followed by NUL. How many char slots are required even for input 1?",
         [2, 8, 9, 10], 9, "ברוחב קבוע הקיבולת היא 8+1=9, בלי קשר לאורך המינימלי של 1.", "For fixed width, capacity is 8+1=9, independent of the minimal length of 1.")

    emit(189, 1, "tagged_read_blocked", {"writes": [["A", 7], ["B", 7]], "acked": ["A"], "read": 7},
         "התגים A ו־B מזהים כתיבות לכתובת 7. מגיע ACK רק ל־A. האם קריאה ל־7 עדיין חסומה בגלל כתיבה בתהליך?",
         "Tags A and B identify writes to address 7. Only A is ACKed. Is a read of 7 still blocked by an outstanding write?",
         [("yes", "כן, B עדיין פעילה", "Yes, B remains outstanding"), ("no", "לא, כל הכתובת נפרשה", "No, the whole address was retired"), ("drop", "יש למחוק את הקריאה", "The read must be discarded"), ("clock", "חייבים לעצור את השעון", "The clock must stop")], "yes",
         "ACK של A אינו פורש את B, אף ששתיהן פונות ל־7.", "ACK for A does not retire B, even though both target 7.")
    emit(189, 2, "tagged_read_blocked", {"writes": [["A", 7], ["B", 8]], "acked": ["B"], "read": 7},
         "A כותבת ל־7 ו־B ל־8. B משלימה ראשונה ומקבלת ACK. האם קריאה ל־7 חייבת עדיין לחכות ל־A?",
         "A writes 7 and B writes 8. B completes first and is ACKed. Must a read of 7 still wait for A?",
         [("yes", "כן", "Yes"), ("no", "לא", "No"), ("clear", "כל השלמה פורשת את כל הכתיבות", "Any completion retires all writes"), ("fifo", "ACK של B בהכרח מאשר גם A", "B's ACK necessarily acknowledges A too")], "yes",
         "השלמה מחוץ לסדר מותאמת לתג B בלבד; A נשארת פעילה ב־7.", "The out-of-order completion matches only tag B; A remains outstanding at 7.")
    emit(189, 3, "tagged_read_blocked", {"writes": [["A", 7], ["B", 8]], "acked": ["A"], "read": 7},
         "A כותבת ל־7 ו־B ל־8. מתקבל ACK של A. הבדיקה כאן היא רק התנגשות עם כתיבות שטרם הושלמו: האם קריאה ל־7 עדיין חסומה?",
         "A writes 7 and B writes 8. A is ACKed. Checking only outstanding-write conflicts, is a read of 7 still blocked?",
         [("no", "לא, נותרה רק B ב־8", "No, only B at 8 remains"), ("yes", "כן, עד שכל הכתיבות יושלמו", "Yes, until all writes complete"), ("lost", "A נמחקה ולכן הנתון אבד", "Retiring A loses its data"), ("reuse", "צריך למחזר מיד את A", "A must immediately be reused")], "no",
         "אין עוד כתיבה בתהליך ל־7; הכתיבה B ל־8 אינה אותה התנגשות.", "No outstanding write targets 7; B at 8 is a different address.")
    emit(189, 4, "tagged_pending", {"writes": [["A", 7], ["B", 8]], "acked": ["Z"]},
         "A ל־7 ו־B ל־8 בתהליך. מגיע ACK עם תג לא מוכר Z, ואין למחוק שום רשומה שאינה מותאמת. אילו תגים נשארים פעילים?",
         "A at 7 and B at 8 are outstanding. An unknown-tag Z ACK arrives; no unmatched entry may be removed. Which tags remain active?",
         [["A", "B"], ["A"], ["B"], []], ["A", "B"],
         "Z אינו מפתח קיים; הוא אינו אישור של A או B.", "Z is not an existing key; it acknowledges neither A nor B.")
    emit(189, 5, "tagged_read_blocked", {"writes": [["B", 7]], "acked": ["A"], "read": 7},
         "A כבר נפרשה; B לכתובת 7 עדיין בתהליך. מגיע שוב ACK ישן של A. האם קריאה ל־7 חייבת להישאר חסומה?",
         "A is already retired; B at address 7 remains outstanding. A duplicate old ACK for A arrives. Must a read of 7 remain blocked?",
         [("yes", "כן", "Yes"), ("no", "לא", "No"), ("decrement", "מקטינים מונה בלי בדיקת תג", "Decrement without matching the tag"), ("reuse", "חייבים להחליף את התג של B", "B's tag must be replaced")], "yes",
         "A אינה פעילה ואינה ממוחזרת באצווה; האישור הישן אינו מסיר את B ל־7.", "A is inactive and not reused within the batch; its old ACK cannot remove B at 7.")

    emit(190, 1, "cycle_entry", {"next": [1, 2, 3, 4, 2]},
         "ברשימה 0→1→2→3→4→2, המפגש הראשון של Floyd הוא בצומת 3. מהי כניסת המעגל, שהיא הצומת הראשון אליו נכנסים במעגל מהראש?",
         "In list 0→1→2→3→4→2, Floyd first meets at node 3. What is the cycle entry, the first cyclic node reached from the head?",
         [0, 2, 3, 4], 2, "הכניסה היא 2; צומת מפגש 3 אינו בהכרח הכניסה.", "The entry is 2; meeting node 3 need not be the entry.")
    emit(190, 2, "floyd_reset_next_pair", {"next": [1, 2, 3, 4, 2]},
         "אחרי מפגש ב־3 ברשימה 0→1→2→3→4→2, מצביע אחד מאופס לראש 0 והאחר נשאר ב־3. מה הזוג אחרי שמקדמים את שניהם צעד אחד?",
         "After meeting at 3 in 0→1→2→3→4→2, reset one pointer to head 0 and leave the other at 3. What is the pair after advancing both one step?",
         [[1, 4], [1, 3], [2, 4], [1, 2]], [1, 4], "הקישורים נותנים 0→1 ו־3→4; בשלב השחזור שניהם זזים באותה מהירות.", "Links give 0→1 and 3→4; both pointers use equal speed during recovery.")
    emit(190, 3, "floyd_recovery_steps", {"next": [1, 2, 3, 4, 2]},
         "ברשימה 0→1→2→3→4→2, משאירים מצביע ב־3 ומאפסים אחר ל־0. כמה צעדים שווים יידרשו עד מפגשם בכניסת המעגל? משווים גם לפני צעד ראשון.",
         "For 0→1→2→3→4→2, leave one pointer at 3 and reset the other to 0. How many equal-speed steps are needed to meet at cycle entry? Also compare before the first step.",
         [0, 1, 2, 3], 2, "מתקבלים (1,4) ואחר כך (2,2), ולכן 2 צעדים.", "The pairs become (1,4), then (2,2), requiring 2 steps.")
    emit(190, 4, "floyd_reset_both_bug", {"next": [1, 2, 3, 4, 2]},
         "אחרי זיהוי מעגל ברשימה 0→1→2→3→4→2, מאפסים בטעות את שני המצביעים לראש ומשווים מיד. איזה צומת יוחזר בטעות ככניסה?",
         "After detecting the cycle in 0→1→2→3→4→2, a bug resets both pointers to the head and compares immediately. Which node is incorrectly returned as entry?",
         [0, 2, 3, 4], 0, "שניהם כבר ב־0, אף שהכניסה 2. חייבים לשמר מצביע אחד במפגש.", "Both are already at 0 although entry is 2. One pointer must retain the meeting position.")
    emit(190, 5, "floyd_meeting_phase", {"next": [1, 2, 3, 4, 1]},
         "ברשימה 0→1→2→3→4→1, אורך המעגל 4. במפגש ראשון האיטי עבר 4 קישורים והמהיר 8. מה שארית מרחק האיטי מודולו אורך המעגל? זהו קשר המופע המשמש לשחזור הכניסה.",
         "In 0→1→2→3→4→1, cycle length is 4. At first meeting slow traveled 4 links and fast 8. What is slow's distance modulo cycle length? This phase relation supports entry recovery.",
         [0, 1, 2, 4], 0, "מרחק האיטי הוא כפולה של אורך המעגל: 4 מודולו 4 הוא 0.", "Slow's distance is a cycle-length multiple: 4 modulo 4 is 0.")

    for v, n, expected in ((1, 6, 7), (2, 1, 0), (3, 5, 6)):
        emit(191, v, "pair_minmax_count", {"n": n},
             f"מוצאים מינימום ומקסימום של {n} ערכים בשיטת הזוגות, כולל אתחול. כמה השוואות מתבצעות? בקלט אי־זוגי מאתחלים בערך הראשון.",
             f"Find minimum and maximum of {n} values by pairing, including initialization. How many comparisons are performed? For odd input, initialize from the first value.",
             [expected, expected + 1, expected + 2, expected + 3], expected,
             "זוג אתחול דורש השוואה אחת, וכל זוג אחר שלוש; ערך אתחול יחיד אינו דורש השוואה.",
             "An initial pair needs one comparison and every later pair three; a single initial value needs none.")
    emit(191, 4, "minmax_savings", {"n": 6},
         "ל־6 ערכים, חיפוש מינימום ומקסימום בנפרד צורך 10 השוואות. שיטת הזוגות צורכת 7. כמה השוואות נחסכות?",
         "For 6 values, separate minimum and maximum scans use 10 comparisons. Pairwise processing uses 7. How many comparisons are saved?",
         [1, 2, 3, 5], 3, "החיסכון הוא 10-7=3; אין צורך במיון כדי למצוא שני קצוות.", "The saving is 10-7=3; finding both extremes does not require sorting.")
    emit(191, 5, "later_pair_comparisons", {"pair": [2, 8], "min": 1, "max": 9},
         "המינימום 1 והמקסימום 9 כבר אותחלו. מגיע זוג (2,8). בשיטת הזוגות משווים בתוך הזוג, ואז כל מועמד לקצה המתאים. כמה השוואות נוספות נדרשות?",
         "Minimum 1 and maximum 9 are initialized. Pair (2,8) arrives. Pairwise processing compares within the pair, then each candidate against its appropriate extreme. How many further comparisons are made?",
         [1, 2, 3, 4], 3, "השוואה פנימית ועוד בדיקת מינימום ובדיקת מקסימום: 3.", "One internal comparison, one minimum check and one maximum check: 3.")

    emit(192, 1, "lex_score", {"scores": [[3, 3], [4, 2]]},
         "ממקסמים לקסיקוגרפית (מספר מקבלי העדפה, מספר מקבלי העדפה ראשונה). איזה ציון עדיף: (3,3) או (4,2)?",
         "Maximize lexicographically (people receiving an acceptable choice, people receiving their first choice). Which score wins: (3,3) or (4,2)?",
         [[3, 3], [4, 2], [3, 2], [4, 3]], [4, 2], "יותר מקבלים קודם: 4 עדיף על 3 גם עם פחות בחירות ראשונות.", "More served takes priority: 4 beats 3 even with fewer first choices.")
    emit(192, 2, "lex_score", {"scores": [[4, 2], [4, 3]]},
         "בהשוואה לקסיקוגרפית של (מקבלים,בחירות ראשונות), שני ציונים הם (4,2) ו־(4,3). איזה מהם נבחר?",
         "Using lexicographic (served,first choices), scores are (4,2) and (4,3). Which is selected?",
         [[4, 2], [4, 3], [3, 4], [2, 4]], [4, 3], "מספר המקבלים שווה, ולכן מכריעות 3 בחירות ראשונות לעומת 2.", "Served counts tie, so 3 first choices beat 2.")
    emit(192, 3, "assignment_unique", {"assigned": ["a", "a"]},
         "יש תחפושת יחידה מכל סוג. הקצאה נותנת את a לשני אנשים, ושניהם מרוצים. האם מותר להשוות את ציונה להקצאות חוקיות ולבחור בה?",
         "There is one costume of each type. An assignment gives a to two satisfied people. May it compete with feasible assignments and be selected by score?",
         [("no", "לא, היא אינה חוקית", "No, it is infeasible"), ("yes", "כן, כי שניהם מרוצים", "Yes, both are happy"), ("first", "כן, אם זו העדפה ראשונה", "Yes, if it is a first choice"), ("tie", "רק בשוויון ציונים", "Only for tied scores")], "no",
         "ציון גבוה אינו מתקן שימוש כפול במשאב יחיד.", "A high score does not repair assigning a single resource twice.")
    emit(192, 4, "lex_score", {"scores": [[1, 1], [2, 1]]},
         "שתי הקצאות חוקיות מקבלות ציונים (1,1) ו־(2,1), לפי מספר מקבלים ואז בחירות ראשונות. איזה ציון מנצח?",
         "Two feasible assignments score (1,1) and (2,1), ordered by served count then first choices. Which score wins?",
         [[1, 1], [2, 1], [1, 2], [2, 0]], [2, 1], "אותו מספר בחירות ראשונות אינו מצדיק להשאיר אדם נוסף ללא העדפה.", "Equal first-choice counts do not justify leaving another person unserved.")
    emit(192, 5, "safe_score_weight", {"n": 4, "candidates": [0, 1, 5, -1]},
         "יש לכל היותר 4 אנשים, והציון החוקי מקיים 0≤first≤served≤4. איזו משקולת מבין 0,1,5,-1 ב־W*served+first מבטיחה שיותר מקבלים תמיד עדיף? אין טענת מינימום למשקולת.",
         "At most 4 people give valid scores 0≤first≤served≤4. Which listed weight 0,1,5,-1 in W*served+first guarantees that more served always wins? No minimal-weight claim is made.",
         [0, 1, 5, -1], 5, "תוספת 5 לרכיב הראשון גדולה מכל הפרש אפשרי של בחירות ראשונות בתחום 0..4.", "An added 5 outweighs any possible first-choice difference within 0..4.")

    emit(193, 1, "worker_peak", {"intervals": [[1, 3, 2], [3, 5, 3]], "closed": False},
         "משימות דורשות 2 עובדים ב־[1,3) ו־3 ב־[3,5). החלפה מיידית מותרת, ללא מעבר. מה מינימום מספר העובדים?",
         "Tasks need 2 workers in [1,3) and 3 in [3,5). Immediate reassignment is allowed, without travel. What is the minimum headcount?",
         [2, 3, 5, 6], 3, "הקטעים חצי־פתוחים ואינם חופפים; שיא הדרישה 3.", "The half-open intervals do not overlap; peak demand is 3.")
    emit(193, 2, "worker_peak", {"intervals": [[1, 3, 2], [3, 5, 3]], "closed": True},
         "הפעם שתי הדרישות כוללות את שני הקצוות: 2 עובדים ב־[1,3] ו־3 ב־[3,5]. גם רגע יחיד נחשב. כמה עובדים דרושים בזמן 3?",
         "Now both endpoints are included: 2 workers in [1,3] and 3 in [3,5]. Even one instant counts. How many workers are required at time 3?",
         [2, 3, 5, 6], 5, "בזמן 3 שתי המשימות פעילות, ולכן 2+3=5.", "At time 3 both tasks are active, requiring 2+3=5.")
    emit(193, 3, "event_delta", {"starts": [3], "ends": [2]},
         "באותו זמן מסתיימת דרישה של 2 עובדים ומתחילה דרישה של 3, בקטעים חצי־פתוחים. מה השינוי נטו בדרישה לאחר קיבוץ האירועים?",
         "At one time, demand for 2 workers ends and demand for 3 starts under half-open intervals. What is the net change after grouping the events?",
         [-1, 0, 1, 5], 1, "מחברים שינויים חתומים: ‎-2+3=1, בלי שיא ביניים מלאכותי.", "Add signed changes: -2+3=1, without an artificial intermediate peak.")
    emit(193, 4, "spurious_peak", {"old": 2, "starts": 3, "ends": 2},
         "בקטעים חצי־פתוחים העומס לפני זמן מעבר הוא 2. מתחילים בטעות את 3 העובדים החדשים לפני שחרור 2 הישנים, ומודדים 5 במקום 3. בכמה גדל השיא המדומה?",
         "For half-open intervals, load before a boundary is 2. A bug adds 3 new workers before releasing the old 2, measuring 5 instead of 3. By how much is the apparent peak inflated?",
         [0, 1, 2, 3], 2, "סדר העיבוד יצר תוספת מדומה של 5-3=2.", "The event order created an artificial increase of 5-3=2.")
    emit(193, 5, "worker_peak", {"intervals": [[5, 5, 9]], "closed": False},
         "החוזה מאפשר קטעים ריקים ומגדיר דרישה בקטע [5,5) של 9 עובדים. מה התרומה לשיא הדרישה?",
         "The contract allows empty intervals and specifies demand for 9 workers during [5,5). What does this contribute to peak demand?",
         [0, 1, 9, 18], 0, "אין זמן ששייך לקטע הריק [5,5), ולכן תרומתו 0.", "No time belongs to empty interval [5,5), so its contribution is 0.")


def late_groups():
    emit(194, 1, "zero_matrix", {"a": [[1, 0], [3, 4]]},
         "מאפסים שורות ועמודות שמכילות אפס במטריצה המקורית [[1,0],[3,4]]. אפסים שנוצרים אינם מפיצים שינוי נוסף. מה התוצאה?",
         "Zero rows and columns containing an original zero in [[1,0],[3,4]]. Newly written zeros trigger no further change. What is the result?",
         [[[0, 0], [3, 0]], [[0, 0], [0, 0]], [[1, 0], [3, 4]], [[0, 0], [0, 4]]], [[0, 0], [3, 0]],
         "רק השורה העליונה והעמודה הימנית מסומנות; 3 נשאר.", "Only the top row and right column are marked; 3 remains.")
    emit(194, 2, "zero_matrix", {"a": [[1, 2], [3, 4]]},
         "אותו כלל מאפס לפי אפסים מקוריים בלבד. מה קורה ל־[[1,2],[3,4]] שבה אין אפס?",
         "The same rule zeros only from original zeros. What happens to [[1,2],[3,4]], containing no zero?",
         [[[1, 2], [3, 4]], [[0, 0], [0, 0]], [[1, 0], [0, 4]], [[0, 2], [3, 0]]], [[1, 2], [3, 4]],
         "אין שורה או עמודה מסומנת, ולכן כל הנתונים נשמרים.", "No row or column is marked, so every value is preserved.")
    emit(194, 3, "zero_matrix", {"a": [[1, 0], [0, 4]]},
         "במטריצה [[1,0],[0,4]] מאפסים לפי כל האפסים המקוריים יחד. מה הפלט?",
         "In matrix [[1,0],[0,4]], apply zeroing from all original zeros together. What is the output?",
         [[[0, 0], [0, 0]], [[1, 0], [0, 4]], [[0, 0], [0, 4]], [[1, 0], [0, 0]]], [[0, 0], [0, 0]],
         "כל שורה וכל עמודה מכילה אפס מקורי, ולכן כל התאים מתאפסים.", "Every row and column contains an original zero, so all cells become zero.")
    emit(194, 4, "zero_markers", {"a": [[1, 0], [3, 4]]},
         "לפני כתיבה ב־[[1,0],[3,4]], אוספים זוג רשימות: (אינדקסי שורות עם אפס, אינדקסי עמודות עם אפס). מהן הרשימות, בבסיס אפס?",
         "Before writing into [[1,0],[3,4]], collect (row indices containing zero, column indices containing zero). What are the zero-based lists?",
         [[[0], [1]], [[0, 1], [0, 1]], [[1], [0]], [[0], [0]]], [[0], [1]],
         "האפס המקורי נמצא בשורה 0 ובעמודה 1, לפני שנכתבו אפסים חדשים.", "The original zero is at row 0, column 1, before any new zeros are written.")
    emit(194, 5, "zero_matrix", {"a": []},
         "מימוש החזרה־בעותק מאפשר גם מטריצה ריקה []. מה יחזיר כלל איפוס השורות והעמודות במקרה זה?",
         "A copy-returning implementation also permits empty matrix []. What does row-and-column zeroing return for it?",
         [[], [[]], [[0]], None], [], "אין תאים ואין שורות לסמן; הצורה הריקה נשמרת.", "There are no cells or rows to mark; the empty shape is preserved.")

    emit(195, 1, "lookup_entries", {"width": 8},
         "טבלת popcount כוללת תשובה לכל קלט בלתי מסומן בן 8 ביטים. כמה כניסות דרושות, כולל הקלט 0?",
         "A popcount table stores an answer for every unsigned 8-bit input. How many entries are needed, including input 0?",
         [8, 255, 256, 257], 256, "יש 2^8=256 דפוסי קלט, כולל כל האפסים.", "There are 2^8=256 input patterns, including all zeros.")
    emit(195, 2, "lookup_bytes", {"width": 8, "bytes_per_entry": 1},
         "טבלת ספירת ביטים מכילה 256 תשובות, כל אחת בבית אחד. כמה בתי מטען דרושים? התעלמו מתקורת אובייקט ויישור.",
         "A bit-count table contains 256 answers, each in one byte. How many payload bytes are required? Ignore object and alignment overhead.",
         [32, 256, 512, 2048], 256, "256 כניסות כפול בית אחד נותנות 256 בתי מטען.", "256 entries times one byte give 256 payload bytes.")
    emit(195, 3, "lookup_entries", {"width": 16},
         "במקום לחלק לבתים בונים טבלה מלאה לכל קלט בן 16 ביטים. כמה כניסות דרושות?",
         "Instead of splitting into bytes, build a complete table for every 16-bit input. How many entries are needed?",
         [16, 256, 512, 65536], 65536, "מרחב הקלט גדל ל־2^16=65536; הוא אינו נשאר בגודל טבלת בית.", "The domain grows to 2^16=65536; it does not remain byte-table sized.")
    emit(195, 4, "byte_lookups", {"width": 32},
         "מילה בת 32 ביטים מפוצלת למקטעים של 8 ביטים. לכל מקטע מבצעים lookup אחד ומחברים את התשובות. כמה גישות לטבלה נעשות?",
         "A 32-bit word is split into 8-bit chunks. Each chunk needs one lookup, then results are summed. How many table accesses occur?",
         [1, 4, 8, 32], 4, "32/8=4 מקטעים, ולכן 4 גישות, לא גישה יחידה לכל רוחב.", "32/8=4 chunks require 4 accesses, not one access for every width.")
    emit(195, 5, "popcount", {"n": 178},
         "טבלת הבית מחזירה את מספר הביטים הדלוקים. מה הערך עבור קלט 10110010, שערכו העשרוני 178?",
         "A byte table returns the number of set bits. What value corresponds to input 10110010, decimal 178?",
         [3, 4, 5, 178], 4, "בדפוס 10110010 יש 4 ביטים דלוקים; ערך האינדקס אינו התשובה.", "Pattern 10110010 has 4 set bits; the table index is not the answer.")

    emit(196, 1, "sort_transfers", {"n": 2000, "model": "internal"},
         "מיון 2000 ערכים שומר קלט ופלט מיזוג בזיכרון פנימי מספיק. קוראים כל ערך פעם אחת וכותבים פעם אחת לפלט חדש. כמה העברות ערך חיצוניות יש?",
         "Sorting 2000 values has enough internal storage for input and merge output. Read each value once and write each once to fresh output. How many external value transfers occur?",
         [2000, 4000, 6000, 8000], 4000, "2000 קריאות ועוד 2000 כתיבות: 4000 העברות במודל הנתון.", "2000 reads plus 2000 writes give 4000 transfers in this model.")
    emit(196, 2, "sort_transfers", {"n": 2000, "model": "roundtrip"},
         "ממיינים שני חצאים של 2000 ערכים, קוראים וכותבים כל חצי לזיכרון חיצוני. אחר כך המיזוג קורא וכותב שוב כל ערך. כמה העברות יש בבנייה הזאת?",
         "Sort two halves totaling 2000 values, reading and writing each half externally. Merging then reads and writes every value again. How many transfers does this construction use?",
         [2000, 4000, 8000, 10000], 8000, "שני שלבים, בכל אחד קריאה וכתיבה של 2000: סך הכול 8000.", "Two stages each read and write 2000 values: 8000 total.")
    emit(196, 3, "sorter_call_transfers", {"calls": 5, "capacity": 1000},
         "בנייה מפעילה קופסת מיון 5 פעמים. כל הפעלה קוראת 1000 ערכים חיצוניים וכותבת 1000, בלי שימור בין הפעלות. כמה העברות היא מבצעת? אין כאן טענת מינימום.",
         "A construction invokes a sorter 5 times. Each call externally reads 1000 values and writes 1000, without retention between calls. How many transfers occur? No minimum is claimed.",
         [5000, 8000, 10000, 20000], 10000, "5 כפול (1000+1000) הוא 10000 העברות בבנייה המוגדרת.", "5 times (1000+1000) gives 10000 transfers for the stated construction.")
    emit(196, 4, "transfer_bytes", {"transfers": 4000, "value_bytes": 4},
         "ספירה מצאה 4000 העברות ערך. כל ערך בן 4 בתים; מתעלמים מהשפעות cache ועסקאות בלוק. כמה בתים מועברים?",
         "A count gives 4000 value transfers, each value 4 bytes. Ignore cache and block-transaction effects. How many bytes are transferred?",
         [1000, 4000, 8000, 16000], 16000, "מכפילים יחידות: 4000 ערכים כפול 4 בתים נותנים 16000 בתים.", "Convert units: 4000 values times 4 bytes give 16000 bytes.")
    emit(196, 5, "memory_model_unique", {"n": 2000},
         "שאלת מיון אינה מגדירה קיבולת פנימית, יחידת העברה או מיקום פלט. מודלים חוקיים נותנים 4000 או 8000 העברות. האם מותר להסיק מספר אופטימלי יחיד בלי הנחות נוספות?",
         "A sorting problem omits internal capacity, transfer unit and output location. Valid models give 4000 or 8000 transfers. May one unconditional optimal count be inferred without more assumptions?",
         [("no", "לא, מודל העלות חסר", "No, the cost model is incomplete"), ("4000", "כן, תמיד 4000", "Yes, always 4000"), ("8000", "כן, תמיד 8000", "Yes, always 8000"), ("average", "כן, הממוצע 6000", "Yes, the average 6000")], "no",
         "4000 ו־8000 מבוססים על אילוצים שונים; אין למצע ביניהם כדי להגדיר אופטימום.", "4000 and 8000 assume different constraints; averaging them cannot define an optimum.")

    emit(197, 1, "permutation_count", {"s": "aab"},
         "מדפיסים כל תמורה נראית שונה של aab פעם אחת. כמה פלטים יש?",
         "Print each distinct visible permutation of aab once. How many outputs exist?",
         [2, 3, 6, 9], 3, "הפלטים הם aab,aba,baa: בדיוק 3.", "The outputs are aab,aba,baa: exactly 3.")
    emit(197, 2, "permutation_count", {"s": ""},
         "בחוזה המתמטי של מחולל תמורות, למחרוזת ריקה יש תמורה ריקה אחת. כמה פלטים המחולל צריך להחזיר?",
         "Under the mathematical permutation-generator contract, the empty string has one empty permutation. How many outputs should the generator yield?",
         [0, 1, 2, None], 1, "יש דרך אחת לבחור סידור של אפס תווים; מקרה הבסיס מפיק מחרוזת ריקה.", "There is one ordering of zero characters; the base case emits an empty string.")
    emit(197, 3, "restore_count", {"s": "aab", "char": "a"},
         "ב־aab ספירת a היא 2. ענף צורך a אחד, מסיים, וחוזרים לאחור לפני ניסיון הענף הבא. לאיזה ערך חייבת ספירת a לחזור?",
         "In aab, count(a)=2. A branch consumes one a, finishes, and backtracks before the next branch. What must count(a) be restored to?",
         [0, 1, 2, 3], 2, "מחזירים את העותק שנצרך, ולכן המלאי הקודם 2 משוחזר.", "Restore the consumed copy, returning to the previous inventory of 2.")
    emit(197, 4, "permutation_outputs", {"s": "abb"},
         "מה קבוצת התמורות השונות של abb? סדר הרשימה אינו חשוב, אבל כל פלט צריך להופיע פעם אחת.",
         "What is the set of distinct permutations of abb? List order is irrelevant, but each output appears once.",
         [["abb", "bab", "bba"], ["abb", "abb", "bba"], ["ab", "ba"], ["aab", "aba", "baa"]], ["abb", "bab", "bba"],
         "בכל פלט נשמרים a אחד ושני b, והכפילויות בין עותקי b אינן ענפים נוספים.", "Each output retains one a and two b; identical b copies do not add branches.")
    emit(197, 5, "distinct_root_branches", {"s": "aab"},
         "מחולל תמורות בוחר לפי ערך תו בעל ספירה חיובית. כמה בחירות שונות יש לתו הראשון של aab, לפני הרקורסיה?",
         "A permutation generator branches by character value with positive count. How many distinct first-character choices does aab have before recursion?",
         [1, 2, 3, 6], 2, "רק a או b: יש 2 סוגי תווים, למרות 3 הופעות.", "Only a or b: 2 character values despite 3 occurrences.")

    emit(198, 1, "earliest_distance", {"previous": [0, 4], "end": 7},
         "אותה שארית סכום הופיעה באינדקסים 0 ו־4, וכעת באינדקס 7. איזה אורך מרבי מתקבל משמירת ההופעה המוקדמת? מדובר באינדקסי קידומות.",
         "The same prefix-sum remainder occurred at indices 0 and 4 and now at index 7. What maximum length follows from retaining the earliest occurrence? These are prefix indices.",
         [3, 4, 7, 8], 7, "הפרש האינדקסים הוא 7-0=7; הבחירה ב־4 הייתה נותנת 3 בלבד.", "The distance is 7-0=7; choosing 4 would give only 3.")
    emit(198, 2, "longest_mod3", {"a": [1, 2]},
         "במערך [1,2] מחפשים קטע רציף שסכומו מתחלק ב־3. רושמים מראש שארית 0 באינדקס ‎-1. מה האורך המרבי?",
         "In [1,2], seek a contiguous sum divisible by 3. Initialize remainder 0 at index -1. What is the maximum length?",
         [0, 1, 2, 3], 2, "כל הקלט מתאים: הסכום 3 והאורך 1-(-1)=2.", "The entire input qualifies: sum 3 and length 1-(-1)=2.")
    emit(198, 3, "longest_mod3", {"a": [1]},
         "במערך [1] אין חובה לבחור קטע אם אין התאמה. מה אורך הקטע הרציף הארוך שסכומו מתחלק ב־3, כאשר בהיעדרו מחזירים 0?",
         "In [1], no interval is required when none qualifies. What is the longest contiguous length with sum divisible by 3, returning 0 when absent?",
         [0, 1, 2, -1], 0, "הקטע הלא־ריק היחיד סכומו 1; אין התאמה ולכן מוחזר 0.", "The only nonempty interval sums to 1; none qualifies, so return 0.")
    emit(198, 4, "overwrite_earliest_loss", {"a": [3, 3]},
         "ב־[3,3], אלגוריתם שגוי מעדכן את אינדקס שארית 0 בכל הופעה, לאחר מדידת האורך. בכמה קטן האורך שהוא ימצא לעומת שמירת אינדקס ‎-1 המקורי?",
         "For [3,3], a faulty algorithm overwrites remainder 0's index after measuring each length. By how much does its result fall short of keeping the original index -1?",
         [0, 1, 2, 3], 1, "השגוי מוצא 1 במקום 2, כי ההופעה המוקדמת נמחקה.", "The faulty result is 1 instead of 2 because the earliest occurrence was lost.")
    emit(198, 5, "longest_mod3", {"a": [-1, 1]},
         "בהרחבה מפורשת המתירה גם מספרים שליליים, משתמשים בשאריות מנורמלות. מה האורך המרבי ב־[-1,1] שסכומו מתחלק ב־3?",
         "In an explicit extension allowing negative integers, use normalized remainders. What is the longest qualifying length in [-1,1] with sum divisible by 3?",
         [0, 1, 2, 3], 2, "הסכום הכולל הוא 0, שמתחלק ב־3, ולכן כל 2 האיברים מתאימים.", "The total is 0, divisible by 3, so all 2 items qualify.")

    emit(199, 1, "recover_moments", {"s": 7, "q": 25},
         "לשני חסרים חיוביים שונים מתקבלים S=a+b=7 ו־Q=a²+b²=25. מהם שני החסרים, בסדר עולה?",
         "Two distinct positive omissions give S=a+b=7 and Q=a²+b²=25. What are the omissions in ascending order?",
         [[3, 4], [2, 5], [1, 6], [0, 7]], [3, 4], "2Q-S²=50-49=1, ולכן ההפרש 1 והמספרים 3 ו־4.", "2Q-S²=50-49=1, giving difference 1 and values 3 and 4.")
    emit(199, 2, "moment_discriminant", {"s": 119, "q": 8093},
         "אם S=119 ו־Q=8093 הם סכום וסכום ריבועי שני חסרים, מה ערך D=2Q-S²? אין צורך בשורש נקודה צפה.",
         "If S=119 and Q=8093 are two omissions' sum and squared sum, what is D=2Q-S²? No floating-point square root is needed.",
         [45, 2025, 8093, 14161], 2025, "2*8093-119²=2025=45²; החישוב כולו שלם ומדויק.", "2*8093-119²=2025=45²; all arithmetic is exact integer arithmetic.")
    emit(199, 3, "recover_moments", {"s": 119, "q": 8093},
         "בזרם חסרים בדיוק שני ערכים שונים מתוך 1..100, ללא חזרות. ההפרשים המדויקים הם S=119,Q=8093. איזה זוג משוחזר?",
         "A stream omits exactly two distinct values from 1..100, without duplicates. Exact differences are S=119,Q=8093. Which pair is recovered?",
         [[37, 82], [38, 81], [36, 83], [45, 74]], [37, 82], "השורש המדויק הוא 45, ולכן (119-45)/2=37 ו־(119+45)/2=82.", "The exact root is 45, giving (119-45)/2=37 and (119+45)/2=82.")
    emit(199, 4, "moment_square_valid", {"s": 3, "q": 6},
         "קלט פגום נותן S=3,Q=6, ולכן D=3. האם D יכול להיות ריבוע ההפרש של שני מספרים שלמים? בדיקה זו אינה ולידציה מלאה של הזרם.",
         "Malformed summaries give S=3,Q=6, hence D=3. Can D be the squared difference of two integers? This check is not full stream validation.",
         [("no", "לא, אינו ריבוע שלם", "No, it is not an integer square"), ("yes", "כן, מעגלים את השורש", "Yes, round the root"), ("zero", "כן, ההפרש אפס", "Yes, the difference is zero"), ("negative", "רק אם שניהם שליליים", "Only if both are negative")], "no",
         "אין מספר שלם שריבועו 3; עיגול אינו הופך סיכומים פגומים לפתרון.", "No integer square equals 3; rounding cannot turn malformed summaries into a solution.")
    emit(199, 5, "moment_collision", {"a": [1, 4, 6, 7], "b": [2, 3, 5, 8]},
         "לרשימות השונות [1,4,6,7] ו־[2,3,5,8] סכום 18 וסכום ריבועים 102. האם שני הסיכומים לבדם מזהים איזו רשימה התקבלה?",
         "Different lists [1,4,6,7] and [2,3,5,8] both have sum 18 and squared sum 102. Do those two summaries alone identify which list was received?",
         [("no", "לא", "No"), ("yes", "כן", "Yes"), ("first", "בהכרח הרשימה הראשונה", "Necessarily the first list"), ("second", "בהכרח הרשימה השנייה", "Necessarily the second list")], "no",
         "אותם 18 ו־102 מתקבלים משתי רשימות; פענוח תחת הבטחה אינו אימות קלט מלא.", "The same 18 and 102 arise from both lists; promise-based recovery is not full validation.")

    emit(200, 1, "parenthesis_valid", {"s": ")("},
         "מוסיפים לזרם רק סוגריים עגולים, ובודקים תקינות כל הקידומת. מה מוחזר אחרי הטקסט `)(`, למרות שוויון הכמויות?",
         "Append round parentheses and test the entire prefix. What is returned after text `)(`, despite equal totals?",
         RET, "false", "סגירה קדמה לפותח; הוספה מאוחרת אינה מתקנת את הסדר.", "A close preceded its opener; later appending cannot repair that order.")
    emit(200, 2, "parenthesis_valid", {"s": "(a)"},
         "בזרם רק סוגריים עגולים נספרים; תווים אחרים מתעלמים. מה מחזירה בדיקת תקינות הקידומת (a)?",
         "Only round parentheses matter in a stream; other characters are ignored. What does whole-prefix validity return for (a)?",
         RET, "true", "התעלמות מ־a משאירה זוג סוגריים מסודר וסגור.", "Ignoring a leaves a correctly ordered, closed parenthesis pair.")
    emit(200, 3, "parenthesis_valid", {"s": ""},
         "מאתחלים מוניטור סוגריים בעומק 0 ובדגל שגיאה כבוי. טרם התקבל תו. מה תקינות הקידומת הריקה?",
         "Initialize a parenthesis monitor with depth 0 and error flag false. No character has arrived. What is the empty prefix's validity?",
         RET, "true", "אין פתיחות חסרות ואין הפרת סדר; הקידומת הריקה חוקית.", "There are no unmatched openings or ordering violations; the empty prefix is valid.")
    emit(200, 4, "parenthesis_completable", {"s": "(("},
         "הקידומת `((` אינה עדיין ביטוי שלם. האם אפשר להפוך אותה לביטוי סוגריים חוקי באמצעות הוספה בסוף בלבד? זו שאלת אפשרות השלמה, לא תקינות נוכחית.",
         "Prefix `((` is not yet a complete expression. Can appending only at the end make it valid? This asks about completability, not current validity.",
         RET, "true", "אפשר להוסיף `))`; עומק חיובי ללא הפרת סדר ניתן להשלמה.", "Append `))`; positive depth without an ordering violation is completable.")
    emit(200, 5, "parenthesis_reset", {"before": ")(", "after": "()"},
         "מוניטור קרא `)(` ונכנס לשגיאה. מתחילים סשן חדש ומאפסים גם עומק וגם דגל שגיאה, ואז מזינים (). מה תקינות הסשן החדש?",
         "A monitor read `)(` and became invalid. Start a new session, resetting both depth and the error flag, then feed (). What is the new session's validity?",
         RET, "true", "השגיאה דביקה בתוך סשן, אך איפוס מפורש מתחיל מצב חדש ונקי.", "The error is sticky within a session; explicit reset starts fresh state.")


def build():
    QUESTIONS.clear()
    CHECKS.clear()
    early_groups()
    middle_groups()
    late_groups()
    assert len(QUESTIONS) == len(CHECKS) == 115
    assert {q["source_key"] for q in QUESTIONS} == set(SOURCES)
    for source in SOURCES:
        rows = [q for q in QUESTIONS if q["source_key"] == source]
        assert {q["variant"] for q in rows} == set(range(1, 6))
        for language in ("he", "en"):
            assert len({q["prompt"][language] for q in rows}) == 5
            assert all(len({c[language] for c in q["choices"]}) == 4 for q in rows)
    return QUESTIONS, CHECKS


if __name__ == "__main__":
    rows, checks = build()
    OUT.mkdir(exist_ok=True)
    (OUT / "code_400.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (OUT / "code_400.checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"Wrote {len(rows)} proposed code variants and {len(checks)} independent-oracle case specifications.")
