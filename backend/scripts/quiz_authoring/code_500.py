"""Seventy-five source-linked, bilingual software cases; authoring stays draft.

Cases specify inputs and semantic alternatives. Independent tests derive answers
without reading the authored expected value or the correct-choice index. C++
lifetime cases model the stated ordinary scope semantics; they are not a claim
that a native C++ compiler or an arbitrary terminating process was tested.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "backend/seeds/duel_quiz_batches"
CARDS = json.loads((ROOT / "apps/web/src/content/fundamentals-code-500.json").read_bytes())
SOURCES = {q["id"]: q for q in CARDS}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def label(value):
    if value is None:
        return "None"
    if isinstance(value, str):
        return value if value.strip() else json.dumps(value)
    return canonical(value)


def named(value, he, en):
    return (value, he, en)


def build():
    rows, checks = [], []

    def emit(n, variant, task, inputs, he, en, options, expected, eh, ee):
        source = f"quick-sw-{n}"
        assert source in SOURCES
        choices = [x if isinstance(x, tuple) else (x, label(x), label(x)) for x in options]
        assert len(choices) == len({canonical(x[0]) for x in choices}) == 4
        assert sum(canonical(x[0]) == canonical(expected) for x in choices) == 1
        # Rotate the right answer evenly without tying its index to option length.
        correct_original = next(i for i, x in enumerate(choices) if canonical(x[0]) == canonical(expected))
        desired = len(rows) % 4
        shift = (correct_original - desired) % 4
        choices = choices[shift:] + choices[:shift]
        key = f"{source}-v{variant}"
        rows.append(dict(key=key, source_key=source, variant=variant, topic=SOURCES[source]["topic"],
                         status="draft", prompt=dict(he=he, en=en),
                         choices=[dict(he=h, en=e) for _, h, e in choices], correct=desired,
                         explanation=dict(he=eh, en=ee)))
        checks.append(dict(key=key, task=task, inputs=inputs, options=[x[0] for x in choices],
                           expected=expected, method="Independent input-derived oracle in backend/tests/test_fundamentals_code_500.py"))

    emit(236, 1, "distance2", {"a": [0, 0], "b": [3, 4]},
         "בחשבון שלם מדויק, מה המרחק בריבוע בין (0,0) ובין (3,4)? אין להוציא שורש.",
         "With exact integer arithmetic, what is the squared distance between (0,0) and (3,4)? Do not take a square root.",
         [5, 7, 25, 49], 25, "ריבועי ההפרשים נותנים 3²+4²=25.", "The squared differences give 3²+4²=25.")
    emit(236, 2, "closest_distance2", {"points": [[0, 0], [3, 0], [1, 0]]},
         "לנקודות (0,0),(3,0),(1,0), מה המרחק המזערי בריבוע בין שתי רשומות שונות?",
         "For points (0,0),(3,0),(1,0), what is the minimum squared distance between different records?",
         [0, 1, 4, 9], 1, "הזוג (0,0),(1,0) נותן 1; שני המרחקים האחרים בריבוע הם 9 ו־4.",
         "Pair (0,0),(1,0) gives 1; the other squared distances are 9 and 4.")
    emit(236, 3, "closest_distance2", {"points": [[2, -1], [7, 3], [2, -1]]},
         "מותרות רשומות שונות באותן קואורדינטות. מה המרחק המזערי בריבוע ברשומות (2,-1),(7,3),(2,-1)?",
         "Different records may have identical coordinates. What is the minimum squared distance in (2,-1),(7,3),(2,-1)?",
         [0, 5, 16, 41], 0, "שתי הרשומות בקואורדינטות (2,-1) יוצרות זוג במרחק 0.",
         "The two records at (2,-1) form a pair at distance 0.")
    emit(236, 4, "closest_indices", {"points": [[-1, -1], [2, 3], [3, 3]]},
         "אינדקסים מתחילים ב־0. בנקודות [(-1,-1),(2,3),(3,3)], איזה זוג אינדקסים קרוב ביותר? אין תיקו.",
         "Indices start at 0. For [(-1,-1),(2,3),(3,3)], which index pair is closest? There is no tie.",
         [[0, 1], [0, 2], [1, 2], [1, 1]], [1, 2], "רק אינדקסים 1 ו־2 מרוחקים יחידה; זוג של רשומה עם עצמה אינו מותר.",
         "Only indices 1 and 2 are one unit apart; pairing a record with itself is disallowed.")
    emit(236, 5, "distance2", {"a": [10, -7], "b": [13, -3]},
         "מזיזים את שני קצות הווקטור (3,4) לאותה נקודת מוצא: (10,-7),(13,-3). מה המרחק בריבוע לאחר ההזזה?",
         "Translate both endpoints of displacement (3,4) to (10,-7),(13,-3). What is their squared distance after translation?",
         [5, 25, 49, 250], 25, "הזזה משותפת אינה משנה הפרשים: עדיין מתקבל 3²+4²=25.",
         "A common translation preserves differences: 3²+4² remains 25.")

    emit(237, 1, "coordinate", {"width": 3, "index": 5},
         "מסך ממוספר בשורות משמאל לימין, רוחב 3, אינדקסים מ־0. איזו קואורדינטה (x,y) מתאימה לאינדקס 5?",
         "A screen is row-major, left to right, width 3, with indices starting at 0. Which (x,y) coordinate corresponds to index 5?",
         [[2, 1], [1, 2], [0, 5], [5, 0]], [2, 1], "5%3=2 ו־5//3=1, ולכן הקואורדינטה היא (2,1).", "5%3=2 and 5//3=1, so the coordinate is (2,1).")
    emit(237, 2, "flatten", {"width": 4, "x": 2, "y": 1},
         "מיפוי שורות ברוחב 4 משתמש באינדקס y*4+x. מה אינדקס הפיקסל (2,1), כשכל המספור מתחיל ב־0?",
         "A width-4 row-major map uses index y*4+x. What is the index of pixel (2,1), with all numbering starting at 0?",
         [3, 4, 6, 9], 6, "מדלגים על שורה אחת בת 4 תאים ומוסיפים x=2: מתקבל 6.", "Skip one row of 4 cells and add x=2: index 6.")
    emit(237, 3, "remaining_pixels", {"width": 3, "height": 2, "used": 5},
         "במסך 3 על 2 נבחרו 5 פיקסלים שונים מתוך פרמוטציה ללא חזרות. כמה בחירות חוקיות נוספות נותרו?",
         "In a 3-by-2 screen, 5 different pixels have been selected from a permutation without repetition. How many further valid selections remain?",
         [0, 1, 2, 5], 1, "יש 6 פיקסלים, ולכן אחרי 5 נשאר פיקסל אחד.", "There are 6 pixels; after 5 selections, one remains.")
    emit(237, 4, "next_pixel", {"width": 2, "height": 2, "permutation": [2, 0, 3, 1], "used": 4},
         "במסך 2 על 2 הסתיימה הפרמוטציה [2,0,3,1]. הממשק מחזיר None במיצוי. מה מוחזר בבקשה הבאה בלי לאפס את המסך?",
         "For a 2-by-2 screen, permutation [2,0,3,1] is exhausted. The interface returns None on exhaustion. What does another request return without a reset?",
         [None, [0, 0], [1, 0], [1, 1]], None, "כל 4 הפיקסלים כבר נוצלו; בחירה נוספת תפר את דרישת היעדר החזרות.", "All 4 pixels are used; another pixel selection would violate nonrepetition.")
    emit(237, 5, "coordinate_sequence", {"width": 2, "indices": [3, 0, 2, 1]},
         "אינדקסים [3,0,2,1] הם פרמוטציה למסך ברוחב 2 וגובה 2. מה סדר הקואורדינטות (x,y) בשיטת שורות?",
         "Indices [3,0,2,1] permute a width-2, height-2 screen. What is the row-major sequence of (x,y) coordinates?",
         [[[1, 1], [0, 0], [0, 1], [1, 0]], [[1, 1], [0, 0], [1, 0], [0, 1]], [[0, 0], [1, 0], [0, 1], [1, 1]], [[1, 1], [0, 0], [0, 1], [0, 1]]],
         [[1, 1], [0, 0], [0, 1], [1, 0]], "מחשבים לכל אינדקס שארית ומנה בחלוקה ב־2; כל זוג מופיע פעם אחת.",
         "Map each index using remainder and quotient by 2; every coordinate pair occurs once.")

    for v, text, operation, expected, options, he, en in [
        (1, "red blue", "words", "blue red", ["blue red", "der eulb", "eulb der", "red blue"],
         "מה סדר המילים אחרי היפוך כל התווים ואז היפוך התווים בכל מילה ב־red blue?", "After reversing all characters and then each word's characters in red blue, what is returned?"),
        (2, "ab cd", "whole", "dc ba", ["ab cd", "cd ab", "dc ba", "ba dc"],
         "בשיטת היפוך סדר מילים, מהו מצב הביניים של ab cd מיד אחרי היפוך כל התווים, לפני תיקון כל מילה?", "In word-order reversal, what intermediate string follows reversing all characters of ab cd, before repairing each word?"),
        (3, "ab cd", "each", "ba dc", ["ab cd", "ba dc", "cd ab", "dc ba"],
         "הופכים רק את התווים בכל מילה של ab cd, ומשאירים את סדר המילים. מה מתקבל בשלב הזה?", "Reverse only each word's characters in ab cd while preserving word order. What does this stage produce?"),
        (4, "", "words", "", ["", "None", " ", "error"],
         "החוזה מאפשר מחרוזת ריקה. מה מחזיר היפוך סדר המילים שלה? האפשרות עם זוג מרכאות מייצגת מחרוזת ריקה.", "The contract allows empty input. What does word-order reversal return for it? The quote-pair option represents an empty string."),
        (5, "single", "words", "single", ["single", "elgnis", "", "single extra"],
         "למחרוזת single יש מילה אחת. מה מחזיר היפוך כל המחרוזת ואז היפוך כל מילה?", "String single contains one word. What follows reversing the whole string and then each word?"),
    ]:
        emit(238, v, "word_reverse", {"text": text, "operation": operation}, he, en, options, expected,
             "היפוך סדר מילים דורש לבטל גם את היפוך האותיות המקומי; כאן התוצאה היא " + (expected if expected else '""') + ".",
             "Word-order reversal must also undo the local letter reversal; this case produces " + (expected if expected else '""') + ".")

    for v, n, kind, expected, options in [(1, 4, "concat", 6, [4, 6, 10, 16]), (2, 1, "concat", 0, [0, 1, 2, 3]),
                                         (3, 8, "concat", 28, [8, 16, 28, 64]), (4, 8, "prepend", 8, [0, 7, 8, 28]),
                                         (5, 200, "concat", 19900, [200, 9900, 19900, 40000])]:
        concat = kind == "concat"
        emit(239, v, "reversal_work", {"n": n, "kind": kind},
             (f"ב־reverse(Tail(L))@[Head(L)], השרשור מעתיק רק את צד שמאל. בכמה חוליות מסתכמות כל ההעתקות ברשימה באורך {n}? לא סופרים יצירת יחידונים." if concat else
              f"היפוך רשימה באורך {n} מעביר כל איבר לצובר באמצעות הוספה לראש בעלות קבועה. כמה פעולות הוספה מתבצעות?"),
             (f"In reverse(Tail(L))@[Head(L)], concatenation copies only its left side. How many nodes are copied in total for length {n}? Exclude singleton creation." if concat else
              f"Reversing a length-{n} list moves each item into an accumulator using constant-time prepending. How many prepend operations occur?"),
             options, expected,
             (f"סכום האורכים המועתקים הוא 0 עד {n-1}, כלומר {expected}." if concat else f"כל אחד מ־{n} האיברים נוסף לראש פעם אחת."),
             (f"Copy lengths sum from 0 through {n-1}, giving {expected}." if concat else f"Each of the {n} items is prepended once."))

    emit(240, 1, "list_prepend", {"list": [], "value": 7, "success": True},
         "מכניסים בהצלחה ערך 7 לראש רשימה ריקה. הפונקציה מחזירה את הראש החדש. מה סדר הערכים ברשימת הקורא אחרי שהראש הוחלף?",
         "Successfully prepend value 7 to an empty list. The function returns the new head. What values are in the caller's list after assigning that head?",
         [[], [7], [0, 7], [7, 7]], [7], "חוליה אחת מצביעת next ל־NULL; היא הראש החדש.", "One node points next to NULL and becomes the new head.")
    emit(240, 2, "new_next", {"old_head": "B", "new_node": "A"},
         "הראש הישן הוא B, וחוליה חדשה A עומדת להתפרסם כראש. מה צריך להיות A.next כדי לשמר את הרשימה הישנה?",
         "Old head is B and new node A will become the head. What must A.next be to preserve the old list?",
         ["A", "B", "NULL", "uninitialized"], "B", "A.next חייב להצביע לראש הישן B לפני עדכון הראש.", "A.next must point to old head B before publishing A.")
    emit(240, 3, "list_prepend", {"list": [4, 8], "value": 7, "success": False},
         "הכנסה לראש [4,8] נכשלת בהקצאת החוליה 7. החוזה מבטיח כשל ללא שינוי. מה נשאר ברשימת הקורא?",
         "Prepending 7 to [4,8] fails during allocation. The contract guarantees no change on failure. What remains in the caller's list?",
         [[4, 8], [7, 4, 8], [], [8]], [4, 8], "לא מפרסמים ראש חדש לפני הצלחה; הרשימה הישנה נשמרת.", "No new head is published before success; the old list stays intact.")
    emit(240, 4, "local_head", {"caller_head": "B", "local_assignment": "A"},
         "ב־C ראש B נמסר כמצביע לפי ערך. הפונקציה מציבה רק בעותק המקומי head=A, אינה משנה חוליות ואינה מחזירה ראש. מה ראש הקורא?",
         "In C, head B is passed as a pointer by value. The function only assigns its local head=A, changes no nodes and returns no head. What is the caller's head?",
         ["A", "B", "NULL", "A then B"], "B", "המצביע המקומי הוא עותק; צריך להחזיר ראש או לעדכן דרך מצביע לראש.", "The local pointer is a copy; return the head or update through a pointer to it.")
    emit(240, 5, "insertion_link", {"before": "P", "after": "Q", "new": "N"},
         "מכניסים N בין P ל־Q ברשימה. לפני שמציבים P.next=N, מה צריך להציב ב־N.next?",
         "Insert N between P and Q in a list. Before assigning P.next=N, what must be assigned to N.next?",
         ["P", "Q", "N", "NULL"], "Q", "N חייב לשמור קישור ליורש הישן Q כדי שהמשך הרשימה לא יאבד.", "N must link to former successor Q so the rest of the list is not lost.")

    for v, events, expected, he, en, options in [
        (1, [["construct", "A"], ["construct", "B"], ["exit", None]], ["B", "A"],
         "ב־C++ אובייקטים מקומיים A ואז B נבנו בהצלחה באותו תחום. ביציאה רגילה, מה סדר ההורסים?", "C++ local objects A then B finish construction in one scope. What is the destructor order on normal scope exit?", [["B", "A"], ["A", "B"], ["A"], []]),
        (2, [["construct", "A"], ["construct", "B"], ["throw", None]], ["B", "A"],
         "לאחר בנייה מלאה של A ואז B, חריגה גורמת לפריקת מחסנית רגילה אל catch חיצוני. שני ההורסים אינם זורקים. מה סדרם?", "After A then B fully construct, an exception unwinds normally to an outer catch. Both destructors are nonthrowing. What is their order?", [["A", "B"], ["B", "A"], ["B"], []]),
        (3, [["construct", "A"], ["enter", None], ["construct", "B"], ["exit", None], ["exit", None]], ["B", "A"],
         "A מקומי בתחום חיצוני. B נבנה בתחום פנימי שמסתיים, ואחר כך מסתיים החיצוני. איזה רצף הריסה מלא מתקבל?", "A is local to an outer scope. B constructs in an inner scope that ends before the outer one. What is the complete destruction sequence?", [["B", "A"], ["A", "B"], ["B", "B"], ["A"]]),
        (4, [["construct", "A"], ["fail_construct", "B"]], ["A"],
         "A נבנה במלואו; בניית B זורקת לפני שהושלמה. בפריקת המחסנית, אילו הורסי אובייקטים שלמים A או B רצים? התעלמו מתתי־אובייקטים של B.", "A fully constructs; B's construction throws before completion. During unwinding, which complete-object destructors of A or B run? Ignore B's subobjects.", [["A"], ["B"], ["B", "A"], []]),
        (5, [["construct", "A"], ["construct", "B"], ["construct", "C"], ["throw", None]], ["C", "B", "A"],
         "A,B,C נבנים לפי הסדר באותו תחום, ואז מתבצעת פריקת מחסנית רגילה. לכל אחד משאב ייחודי והורס שאינו זורק. מה סדר שחרור המשאבים?", "A,B,C construct in that order in one scope, followed by ordinary unwinding. Each owns a distinct resource and has a nonthrowing destructor. In what order are resources released?", [["A", "B", "C"], ["C", "B", "A"], ["C"], []]),
    ]:
        emit(241, v, "destruction_trace", {"events": events}, he, en, options, expected,
             "הורסים רק אובייקטים שבנייתם הושלמה, בסדר הפוך בכל תחום: " + label(expected) + ".",
             "Destroy only fully constructed objects, in reverse order within each scope: " + label(expected) + ".")

    ub = named("undefined", "התנהגות לא מוגדרת", "Undefined behavior")
    emit(242, 1, "delete_trace", {"chain": ["Base", "Derived"], "pointer": "Base", "virtual": True},
         "delete של Derived דרך Base* מותר, ולהורס Base יש virtual ונגישות ציבורית. מה סדר ההורסים?",
         "Deleting Derived through Base* is permitted; Base has a public virtual destructor. What is the destructor order?",
         [["Derived", "Base"], ["Base", "Derived"], ["Base"], ub], ["Derived", "Base"],
         "ההורס הווירטואלי מתחיל בנגזר, ואז ההריסה מגיעה לבסיס.", "Virtual destruction starts with Derived and then destroys Base.")
    emit(242, 2, "delete_trace", {"chain": ["Base", "Middle", "Leaf"], "pointer": "Base", "virtual": True},
         "Leaf יורש מ־Middle שיורש מ־Base. מוחקים דרך Base* עם הורס וירטואלי ציבורי. מה סדר שלושת ההורסים?",
         "Leaf derives from Middle, which derives from Base. Delete through Base* with a public virtual destructor. What is the three-destructor order?",
         [["Base", "Middle", "Leaf"], ["Leaf", "Middle", "Base"], ["Leaf", "Base"], ub], ["Leaf", "Middle", "Base"],
         "ההריסה עולה בהיררכיה מהנגזר ביותר: Leaf,Middle,Base.", "Destruction climbs from the most derived type: Leaf,Middle,Base.")
    emit(242, 3, "delete_trace", {"chain": ["Base", "Derived"], "pointer": "Base", "virtual": False},
         "Base רגיל, עם הורס ציבורי שאינו וירטואלי. Base* מצביע ל־new Derived ומבצעים delete דרכו. מה קובע התקן במקרה הרגיל הזה?",
         "Ordinary Base has a public nonvirtual destructor. A Base* points to new Derived and is deleted through that pointer. What applies in this ordinary case?",
         [["Base"], ["Derived", "Base"], [], ub], "undefined", "זהו מקרה של התנהגות לא מוגדרת; אין סדר הורסים מובטח.",
         "This is undefined behavior; no destructor sequence is guaranteed.")
    emit(242, 4, "delete_trace", {"chain": ["Base"], "pointer": "Base", "virtual": False},
         "Base* מצביע ל־new Base עצמו, וההורס ציבורי ולא וירטואלי. מוחקים דרך Base*. מה סדר ההריסה?",
         "A Base* points to new Base itself; its destructor is public and nonvirtual. Delete through Base*. What is the destruction sequence?",
         [["Base"], ["Derived", "Base"], [], ub], ["Base"], "אין כאן אי־התאמה בין טיפוס דינמי לבסיס; Base עצמו נהרס.",
         "There is no dynamic-type/base mismatch here; Base itself is destroyed.")
    emit(242, 5, "delete_trace", {"chain": ["Base", "Derived"], "pointer": "Derived", "virtual": False},
         "Derived* מצביע ל־new Derived ומוחקים דרך אותו Derived*. שני ההורסים ציבוריים; Base אינו וירטואלי. מה סדרם?",
         "A Derived* points to new Derived and deletion uses that Derived*. Both destructors are public; Base's is nonvirtual. What is their order?",
         [["Base"], ["Derived", "Base"], ["Base", "Derived"], ub], ["Derived", "Base"], "המחיקה מתחילה בטיפוס הנכון Derived; לאחריו נהרס תת־אובייקט Base.",
         "Deletion starts at the correct type Derived, followed by its Base subobject.")

    trees = [
        (1, [[1, 2], [3, 4], [5, 6], [], [], [], []], "depth", 3, [2, 3, 6, 7]),
        (2, [[1], [2], [3], [4], [5], [6], []], "depth", 7, [1, 3, 6, 7]),
        (3, [], "depth", 0, [0, 1, 2, 3]),
        (4, [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [], [], [], [], [], [], [], []], "depth", 4, [3, 4, 7, 15]),
        (5, [[1, 2], [3, 4], [5, 6], [], [], [], []], "work_and_depth", [7, 3], [[7, 3], [3, 7], [7, 7], [3, 3]]),
    ]
    for v, children, kind, expected, options in trees:
        shape = "ריק" if not children else "שרשרת בת 7 צמתים" if v == 2 else f"עץ בינארי מושלם בן {len(children)} צמתים (כל הרמות מלאות)"
        english = "an empty tree" if not children else "a chain of 7 nodes" if v == 2 else f"a perfect binary tree of {len(children)} nodes (every level is full)"
        emit(243, v, "tree_stack", {"children": children, "kind": kind},
             f"רקורסיית עומק מבקרת כל צומת פעם אחת ב{shape}. ללא קריאות NULL או אופטימיזציית זנב, " + ("מה הצמד [ביקורים כוללים,מסגרות פעילות בשיא]?" if kind == "work_and_depth" else "מה מספר מסגרות הצמתים הפעילות המרבי?"),
             f"Depth-first recursion visits every node once in {english}. Exclude NULL calls and tail-call optimization. " + ("What is [total visits,peak active frames]?" if kind == "work_and_depth" else "What is the peak number of active node frames?"),
             options, expected, "מסגרות פעילות עוקבות אחר מסלול שטרם חזר; ענפים שהסתיימו כבר יצאו מהמחסנית.",
             "Active frames follow an unfinished path; completed branches have already left the stack.")

    expression_cases = [
        (1, [2, "+", 3, "*", 4, "="], "value", 14, [14, 20, 24, 9]),
        (2, [2, "*", 3, "+", 4, "="], "value", 10, [10, 14, 20, 24]),
        (3, [2, "+", 0, "*", 9, "="], "value", 2, [0, 2, 9, 18]),
        (4, [5, "*", 0, "+", 7, "*", 2, "="], "value", 14, [0, 7, 14, 24]),
        (5, [2, "+", 3, "*", 4, "="], "state", [2, 12], [[2, 12], [14, 0], [5, 4], [0, 20]]),
    ]
    for v, tokens, kind, expected, options in expression_cases:
        expr = "".join(map(str, tokens))
        emit(244, v, "expression", {"tokens": tokens, "kind": kind},
             f"הביטוי הוא {expr}, עם קדימות כפל רגילה וחשבון מדויק. " + ("מה הצמד [סכום איברים שסוימו,מכפלה נוכחית] מיד לפני =?" if kind == "state" else "מה התוצאה לפני סימן הסיום?"),
             f"Expression {expr} uses normal multiplication precedence and exact arithmetic. " + ("What is [sum of completed terms,current product] immediately before =?" if kind == "state" else "What is its value at the terminator?"),
             options, expected, "משלימים את איברי הכפל לפני צירופם לסכום; במקרה זה מתקבל " + label(expected) + ".",
             "Finish product terms before adding them to the sum; this case gives " + label(expected) + ".")

    classifications = [named("number", "חסר מספר במקום הנוכחי", "A number is missing at this position"),
                       named("trailing", "יש אסימון אחרי סימן הסיום", "A token follows the terminator"),
                       named("terminator", "חסר סימן הסיום =", "The = terminator is missing"),
                       named("valid", "הביטוי חוקי", "The expression is valid")]
    for v, tokens, expected in [(1, [2, "+", "="], "number"), (2, [2, "=", 3], "trailing"),
                                (3, ["="], "number"), (4, [2, "*", 3], "terminator"), (5, [0, "="], "valid")]:
        text = " ".join(map(str, tokens))
        emit(245, v, "grammar", {"tokens": tokens},
             f"בדקדוק NUMBER ((+|*) NUMBER)* =, המספרים הם אסימונים לא שליליים. מה האבחנה עבור האסימונים: {text}?",
             f"Under grammar NUMBER ((+|*) NUMBER)* =, numbers are nonnegative tokens. Classify tokens: {text}.",
             classifications, expected, "הבדיקה שומרת האם צפוי מספר, צפוי אופרטור או שכבר התקבל סימן סיום; אין לקבל אסימונים אחריו.",
             "Validation tracks number expectation, operator expectation and completion; tokens after completion are forbidden.")

    for v, values, expected, options in [
        (1, [9, 9, 7, 7, 7], [[9, 2], [7, 3]], [[[9, 2], [7, 3]], [[9, 1], [9, 1]], [[7, 3], [9, 2]], [[9, 2], [7, 1]]]),
        (2, [-3, -1, -1, -2], [[-1, 2], [-2, 1]], [[[-1, 2], [-2, 1]], [[0, 0], [-1, 2]], [[-1, 1], [-1, 1]], [[-3, 1], [-2, 1]]]),
        (3, [5, 5, 5], [[5, 3]], [[[5, 3]], [[5, 3], [0, 0]], [[5, 1], [5, 2]], []]),
        (4, [4, 4, 8, 8, 6], [[8, 2], [6, 1]], [[[8, 2], [6, 1]], [[8, 2], [4, 2]], [[8, 1], [8, 1]], [[6, 1], [4, 2]]]),
        (5, [], [], [[], [[0, 0]], [[0, 1]], [[-1, 1]]]),
    ]:
        emit(246, v, "top_two", {"values": values},
             f"למערך {label(values)}, החזירו עד שני ערכים שונים בסדר יורד, כל אחד כ־[ערך,שכיחות]. אין להוסיף ערך חסר. מה הפלט?",
             f"For array {label(values)}, return up to two distinct values in descending order as [value,frequency]. Do not invent a missing value. What is returned?",
             options, expected, "סופרים הופעות לכל ערך, בוחרים את שני המפתחות הגדולים ביותר ומשמרים את מוניהם.",
             "Count each value's occurrences, select the two greatest keys and retain their counts.")

    for v, values, expected, options in [(1, [4, 2, 4, 2], 2, [2, 4, 0, None]),
                                        (2, [-1, -3, -1, -3], -3, [-3, -1, 0, None]),
                                        (3, [0, 0, 2], 0, [0, 2, -1, None]),
                                        (4, [], None, [None, 0, -1, 1]),
                                        (5, [8, 2, 8, 2, 8], 8, [2, 8, 0, None])]:
        emit(247, v, "mode", {"values": values},
             f"ב־{label(values)} מחפשים ערך שכיח. בשוויון בוחרים את הערך הקטן ביותר; ריק מחזיר None. מה התוצאה?",
             f"Find the mode of {label(values)}. Break frequency ties by the smallest value; empty input returns None. What is returned?",
             options, expected, "כלל ההכרעה משווה תחילה שכיחות ורק אחר כך ערך; None שמור לקלט ריק.",
             "The tie policy compares frequency first and value second; None is reserved for empty input.")

    for v, counts, expected, options in [(1, [[4, 1], [9, 3]], 4, [4, 9, 0, None]),
                                        (2, [[2, 4], [5, 6]], 2, [2, 4, 5, None]),
                                        (3, [[-7, 4], [-1, 3], [8, 6]], -7, [-7, -1, 8, None]),
                                        (4, [[3, 7], [6, 9]], 3, [3, 6, 7, None]),
                                        (5, [[0, 1], [1, 6]], 0, [0, 1, 6, None])]:
        emit(248, v, "residual_triple", {"counts": counts},
             f"השכיחויות לאחר מחיקת שתי הופעות של ערך אחד הן {label(counts)}, כל זוג [ערך,כמות]. במקור כל כמות התחלקה ב־3. איזה ערך נפגע?",
             f"After deleting two occurrences of one value, frequencies are {label(counts)}, each pair [value,count]. Every original count was divisible by 3. Which value was affected?",
             options, expected, "לערך שנפגע יש שכיחות השקולה ל־1 מודולו 3; כל שאר השכיחויות שקולות ל־0 מודולו 3.",
             "The affected frequency is 1 modulo 3; all other frequencies are 0 modulo 3.")

    for v, row, x, length, expected, options in [
        (1, [0], 1, 3, [14], [[14], [7], [15], [0]]),
        (2, [255], 2, 0, [255], [[255], [0], [251], [4]]),
        (3, [128, 1], 6, 4, [192, 3], [[192, 3], [192, 192], [255, 255], [64, 3]]),
        (4, [85], 2, 2, [93], [[93], [12], [85], [89]]),
        (5, [0, 0], 7, 2, [128, 1], [[128, 1], [1, 128], [255, 255], [128, 0]]),
    ]:
        emit(249, v, "draw_line", {"row": row, "x": x, "length": length},
             f"בייטי השורה הם {label(row)}. פיקסל p הוא ביט p%8 מה־LSB בבייט p//8. מדליקים {length} פיקסלים החל מ־x={x}, בלי לשנות אחרים. מה הבייטים החדשים בעשרוני?",
             f"Row bytes are {label(row)}. Pixel p is LSB-based bit p%8 in byte p//8. Set {length} pixels starting at x={x}, preserving other pixels. What are the new decimal bytes?",
             options, expected, "מפעילים OR רק עם מסכת הטווח; גם ביטים שכבר דלקו מחוץ לטווח נשמרים.",
             "OR only the target mask; previously set bits outside the range are preserved.")

    triggers = [named(True, "כן, פעם אחת", "Yes, exactly once"), named(False, "לא", "No"),
                named("twice", "כן, פעמיים", "Yes, twice"), named("error", "הקלט אינו חוקי", "Invalid input")]
    for v, n, expected in [(1, 14, False), (2, 77, True), (3, 70, True), (4, 0, False)]:
        emit(250, v, "contains_seven", {"number": n},
             f"מדפיסים boom פעם אחת למספר אם כתיבו העשרוני מכיל 7; התחלקות ב־7 אינה תנאי. האם {n} מפעיל, וכמה הדפסות?",
             f"Print boom once per number if its decimal representation contains 7; divisibility by 7 is irrelevant. Does {n} trigger, and how many prints?",
             triggers, expected, "מחפשים נוכחות של הספרה, לא מספר מופעיה ולא שארית בחלוקה ב־7.",
             "Test digit presence, not occurrence count or remainder modulo 7.")
    emit(250, 5, "seven_outputs", {"start": 1, "stop": 20},
         "עוברים מ־1 עד 20 כולל, ומדפיסים את המספר פעם אחת רק אם כתיבו מכיל 7. אילו מספרים מודפסים?",
         "Scan 1 through 20 inclusive, printing each number once only if its decimal representation contains 7. Which numbers are printed?",
         [[7, 17], [7, 14], [7, 14, 17], [7]], [7, 17], "7 ו־17 מכילים 7; 14 מתחלק ב־7 אך אינו מכיל את הספרה.",
         "7 and 17 contain 7; 14 is divisible by 7 but lacks the digit.")

    assert len(rows) == len(checks) == 75
    assert {row["source_key"] for row in rows} == set(SOURCES)
    for source in SOURCES:
        source_rows = [row for row in rows if row["source_key"] == source]
        assert {row["variant"] for row in source_rows} == set(range(1, 6))
        for lang in ("he", "en"):
            assert len({row["prompt"][lang] for row in source_rows}) == 5
            assert all(len({choice[lang] for choice in row["choices"]}) == 4 for row in source_rows)
    return rows, checks


if __name__ == "__main__":
    questions, evidence = build()
    (OUT / "code_500.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "code_500.checks.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(questions)} draft variants and {len(evidence)} independent-oracle specifications.")
