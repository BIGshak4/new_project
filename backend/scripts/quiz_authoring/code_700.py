"""Thirty original interview-linked cards and 150 bilingual draft variants.

The cases are deliberately small executable examples, boundary cases, and
counterexamples. Internal editorial difficulty is kept in the evidence shard,
not in learner content. These are AI-assisted drafts, not expert attestation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "backend/seeds/duel_quiz_batches"
CARD_PATH = ROOT / "apps/web/src/content/fundamentals-code-700.json"


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def label(value):
    if value is None:
        return "None"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    return canonical(value)


def build_cards():
    cards = []

    def add(n, prep, th, te, ph, pe, ah, ae, kh, ke, code=None, topic="algorithms"):
        card = dict(id=f"quick-sw-{n}", topic=topic, interviewIds=[f"PREP-{prep:03}"],
                    title=dict(he=th, en=te), prompt=dict(he=ph, en=pe),
                    answer=dict(he=ah, en=ae), takeaway=dict(he=kh, en=ke))
        if code:
            card["code"] = dict(language="python", text=code)
        cards.append(card)

    add(321, 224, "חזית המיזוג חושפת יורש אחד", "A merge frontier reveals one successor",
        "ממזגים רשימות ממוינות [1,8],[2,3],[4]. החזית מכילה רק את הראש שטרם נצרך מכל רשימה. אחרי הוצאת 1, מה החזית החדשה ומדוע לא מוסיפים את כל הרשימה?",
        "Merge sorted lists [1,8],[2,3],[4]. The frontier holds only each list's first unconsumed item. After removing 1, what is the new frontier, and why not add the entire list?",
        "החזית היא [2,4,8] בסדר ערכים. מוסיפים רק את יורשו של האיבר שנשלף. כל איבר אחר באותה רשימה אינו קטן מן היורש, ולכן עדיין אינו דרוש להחלטה הבאה. רשימה שמוצתה אינה תורמת נציג.",
        "The value-sorted frontier is [2,4,8]. Add only the removed item's successor. Later items in that list cannot be smaller than its successor, so they are unnecessary for the next decision. An exhausted list contributes no representative.",
        "במיזוג ממויין מספיק נציג אחד לכל מקור שטרם מוצה.", "Sorted merging needs one representative per unexhausted source.")
    add(322, 226, "מנרמלים אותיות לפני השוואת אנגרמות", "Normalize case before comparing anagrams",
        "מילים מכילות אותיות ASCII בלבד, והחוזה מתעלם מהבדל בין אות גדולה לקטנה. האם Silent ו־LISTEN אנגרמות? באיזה שלב מנרמלים את האותיות?",
        "Words contain ASCII letters only, and the contract ignores letter case. Are Silent and LISTEN anagrams? At which stage should case be normalized?",
        "כן. ממירים את שתי המילים לאותיות קטנות לפני יצירת חתימה ממוינת או ספירת שכיחויות. החתימות בשתיהן eilnst. מיון התווים המקוריים לפני השוואה אינו מקיים את חוזה ההתעלמות מגודל האות. נרמול אינו מסיר מופעים חוזרים.",
        "Yes. Convert both words to lowercase before building sorted signatures or frequency counts. Both signatures become eilnst. Comparing sorted original characters would violate the case-insensitive contract. Normalization does not remove repeated occurrences.",
        "כלל השקילות קובע איזה נרמול נדרש לפני ההשוואה.", "The equivalence rule determines normalization before comparison.",
        "def anagram(a, b):\n    return sorted(a.lower()) == sorted(b.lower())", topic="python")
    add(323, 229, "גבול הכתיבה מתקדם רק עבור ערך שנשמר", "The write boundary advances only for retained values",
        "מעבירים אפסים לסוף [0,5,0,2] ושומרים על סדר הערכים האחרים. מה התוצאה, ומה מייצג גבול הכתיבה במהלך הסריקה?",
        "Move zeros to the end of [0,5,0,2], preserving other values' order. What is returned, and what does the write boundary represent during scanning?",
        "מתקבל [5,2,0,0]. לפני גבול הכתיבה נמצאים בדיוק הערכים הלא־אפסיים שכבר נצפו, בסדרם המקורי. כל ערך כזה מקדם את הגבול פעם אחת. בסוף ממלאים באפס את יתר המערך.",
        "The result is [5,2,0,0]. Before the write boundary are exactly the nonzero values seen so far, in their original order. Each such value advances the boundary once. Finally fill the remaining suffix with zeros.",
        "סריקה וכתיבה נפרדות מאפשרות דחיסה יציבה.", "Separate scan and write positions enable stable compaction.",
        "def compact(a):\n    w = 0\n    for x in a:\n        if x != 0: a[w] = x; w += 1\n    a[w:] = [0] * (len(a)-w); return a")
    add(324, 238, "שומרים את ההמשך לפני היפוך הקישור", "Save the successor before reversing a link",
        "ברשימה A→B→C, ההיפוך כבר טיפל ב־A וכעת current=B, previous=A. אחרי הפיכת B.next ל־A, לאיזו חוליה צריך להתקדם וכיצד שומרים אותה?",
        "In A→B→C, reversal has processed A and now current=B, previous=A. After setting B.next to A, which node should become current, and how is it preserved?",
        "מתקדמים ל־C. שומרים את B.next הישן לפני כתיבה אליו; אחרת קריאה חוזרת תוביל ל־A, שכבר טופלה. אחרי השמירה הופכים את הקישור, מעדכנים previous ל־B ומתקדמים ליורש שנשמר.",
        "Advance to C. Save the old B.next before overwriting it; reading it afterward would lead back to already processed A. Then reverse the link, set previous to B, and advance to the saved successor.",
        "לפני דריסת קישור שומרים כל מידע שעוד דרוש לסריקה.", "Preserve future traversal information before overwriting a link.")
    add(325, 239, "מרכאות ב־CSV משנות את משמעות הפסיק", "CSV quotes change what a comma means",
        "ברשומת CSV תקינה, פסיק בתוך שדה מצוטט הוא תוכן וזוג מרכאות כפולות מייצג מרכאה אחת. אילו שדות מפיקה הרשומה \"a,b\",\"c\"\"d\",?",
        "In valid CSV, a comma inside quotes is content and doubled quotes encode one quote. What fields does the record \"a,b\",\"c\"\"d\", produce?",
        "שלושת השדות הם a,b ואז c\"d ואז מחרוזת ריקה. הפסיק האחרון פותח שדה ריק; אין להשמיטו. פיצול פשוט על כל פסיק שובר את השדה הראשון ואינו מפענח מרכאות כפולות.",
        "The three fields are a,b, then c\"d, then an empty string. The final comma introduces an empty field and must be preserved. Splitting on every comma breaks the first field and does not decode doubled quotes.",
        "מפריד הוא משמעות של מצב הפענוח, לא רק תו.", "A delimiter's meaning depends on parser state.", topic="python")
    add(326, 237, "בעלות על מפתח מונעת תלות במאגר הקורא", "Owning a key removes dependence on caller storage",
        "מילון ב־C מעתיק את תוכן מפתח הקורא בזמן הוספה. המפתח cat נוסף, ואז הקורא משנה את המאגר שלו ל־bat. תחת החוזה הזה, איזה מפתח נשמר במילון?",
        "A C dictionary copies the caller's key bytes during insertion. After inserting cat, the caller changes its buffer to bat. Under this contract, which key remains in the dictionary?",
        "cat נשאר. עותק בבעלות המילון אינו משתנה כשמאגר הקורא משתנה. שמירת מצביע בלבד הייתה יוצרת תלות בחיי המאגר ובשינויים בו. יש לשחרר את עותק המפתח בדיוק כשבעלות המילון עליו מסתיימת.",
        "cat remains. The dictionary-owned copy is unaffected by caller-buffer changes. Keeping only a pointer would depend on that buffer's lifetime and later mutations. Release the copied key when the dictionary's ownership ends.",
        "העתקת כתובת והעתקת תוכן יוצרות חוזי בעלות שונים.", "Copying an address and copying contents establish different ownership contracts.")
    add(327, 245, "מועמד בסודוקו חייב לעבור שלושה אילוצים", "A Sudoku candidate must pass three constraints",
        "בסודוקו רגיל מותרות הספרות 1..9. לשדה ריק יש בשורה {1,2}, בעמודה {3,4} ובתיבה {5,6,7}. אילו מועמדים נשארים?",
        "Standard Sudoku allows digits 1..9. An empty cell sees {1,2} in its row, {3,4} in its column and {5,6,7} in its box. Which candidates remain?",
        "{8,9}. ספרה מותרת רק אם היא חסרה בכל שלושת האזורים. מחסרים מטווח הספרות את איחוד הספרות שכבר מופיעות. קבוצת מועמדים ריקה מצביעה על סתירה בענף הנוכחי, לא בהכרח על היעדר פתרון ללוח המקורי.",
        "{8,9}. A digit is permitted only when absent from all three regions. Subtract their union from the digit domain. An empty candidate set signals a contradiction in the current branch, not necessarily an unsolvable original board.",
        "אילוצים מצטברים מסירים את איחוד הערכים האסורים.", "Combined constraints exclude the union of forbidden values.",
        "def candidates(row, col, box):\n    return sorted(set(range(1,10)) - set(row) - set(col) - set(box))")
    add(328, 246, "בין שני חציונים עשוי להיות מישור של מינימום", "Two middle positions can bound many optima",
        "אנשים נמצאים במיקומים 0,2,8,10 על רחוב ישר. נקודת המפגש היא מספר שלם וממזערת את סכום מרחקי ההליכה. האם רק נקודת האמצע 5 אופטימלית?",
        "People stand at 0,2,8,10 on a straight street. The integer meeting position minimizes total walking distance. Is only midpoint 5 optimal?",
        "לא. כל מספר שלם מ־2 עד 8 כולל נותן סכום 16. בתחום שבין שני האיברים האמצעיים, הזזה ביחידה מקרבת לשני אנשים ומרחיקה משניים. עבור כמות אי־זוגית, המיקום האמצעי הוא חציון אופטימלי.",
        "No. Every integer from 2 through 8 gives total distance 16. Between the two middle positions, moving one unit approaches two people and moves away from two. For an odd count, the middle position is an optimal median.",
        "סכום מרחקים מוחלטים מתמזער בחציון, ולעיתים בתחום שלם.", "Absolute-distance sums are minimized at medians, sometimes across an interval.")
    add(329, 247, "החיובי הראשון שחסר חסום באורך ועוד אחד", "The first missing positive is bounded by length plus one",
        "במערך [3,4,-1,1] מחפשים את המספר החיובי הקטן ביותר שאינו מופיע. למה אפשר להתעלם משליליים ומערכים הגדולים מאורך המערך בזמן סימון המועמדים?",
        "Find the smallest missing positive in [3,4,-1,1]. Why can candidate marking ignore negatives and values greater than the array length?",
        "התשובה היא 2. במערך באורך n, אם כל 1..n מופיעים התשובה n+1; אחרת חסר מספר בתחום הזה. לכן ערכים מחוץ ל־1..n אינם מסמנים מועמד נחוץ. כפילויות מסמנות אותו מועמד שוב ואינן ממלאות חוסר אחר.",
        "The answer is 2. For length n, either every value 1..n appears and the answer is n+1, or one is missing in that range. Values outside 1..n mark no needed candidate. Duplicates mark the same candidate again and cannot fill another gap.",
        "חסם על התשובה מצמצם את תחום הערכים שצריך לייצג.", "Bounding the answer narrows the values that need representation.",
        "def missing(a):\n    return next(x for x in range(1,len(a)+2) if x not in set(a))")
    add(330, 305, "מעבירים לתור היוצא רק כשהוא ריק", "Transfer only when the outgoing stack is empty",
        "תור משתמש בשתי מחסניות. בראש מחסנית היציאה נמצא 1 ומחסנית הכניסה מכילה את הערכים החדשים 2,3, כשהחדש בראש. מדוע אין להעביר את הכניסה לפני הוצאת 1?",
        "A queue uses two stacks. The outgoing stack has 1 on top; the incoming stack holds newer values 2,3, newest on top. Why must incoming items not transfer before removing 1?",
        "העברה כעת תניח את 2 מעל 1 ותוציא ערך חדש לפני הישן. מרוקנים את מחסנית היציאה לפני היפוך כל הכניסה לתוכה. כל איבר נכנס, מועבר ויוצא לכל היותר פעם אחת, ולכן העלות הממוצעת לפעולה קבועה.",
        "Transferring now puts 2 above 1 and removes a newer value first. Empty the outgoing stack before reversing all incoming items into it. Each item is pushed, transferred and removed at most once, giving constant amortized work per operation.",
        "גבול ההעברה משמר את סדר ההגעה בין קבוצות.", "The transfer boundary preserves arrival order between batches.")
    add(331, 304, "סביב סמן נשמרים שני סדרים הפוכים", "A cursor has two oppositely ordered sides",
        "סמן נמצא בין תווים. מחסנית L משמאלו בסדר תחתית־לראש [a,b], ומחסנית R מימינו [d,c]. מה הטקסט, ומה משתנה כשהסמן זז ימינה פעם אחת?",
        "A cursor lies between characters. Left stack L is [a,b] bottom-to-top and right stack R is [d,c] bottom-to-top. What is the text, and what changes after moving right once?",
        "הטקסט abcd. התו הקרוב מימין הוא c שבראש R; מעבירים אותו לראש L. נקבל L=[a,b,c],R=[d]. הטקסט נשמר, ורק נקודת הפיצול משתנה. אם R ריקה, תנועה ימינה אינה עושה דבר.",
        "The text is abcd. The nearest right character is c at R's top; move it to L's top. Then L=[a,b,c],R=[d]. Text stays unchanged while the split moves. When R is empty, moving right does nothing.",
        "קרבת איבר לסמן מתורגמת לראש מחסנית.", "Proximity to a cursor is represented by a stack top.")
    add(332, 285, "היפוך ספרות אינו מבטיח תוצאה ניתנת לייצוג", "Reversed digits may exceed the result type",
        "הופכים ספרות של signed int32 ושומרים סימן. החוזה מחזיר None בגלישה. מה מחזירים עבור ‎-120 ועבור 1534236469?",
        "Reverse decimal digits of signed int32 while preserving sign. Return None on overflow. What is returned for -120 and 1534236469?",
        "עבור ‎-120 מתקבל ‎-21; האפס המוביל בתוצאה אינו נשמר כמקום מספרי. עבור 1534236469 ההיפוך 9646324351 חורג מ־2147483647, ולכן מוחזר None. בודקים את התוצאה מול שני גבולות הטיפוס לפני המרה אליו.",
        "-120 gives -21; a leading result zero has no numeric place value. Reversing 1534236469 gives 9646324351, exceeding 2147483647, so return None. Check both type bounds before converting to the destination type.",
        "קלט חוקי אינו מבטיח שפלט טרנספורמציה ייכנס לאותו טיפוס.", "A valid input does not guarantee its transformation fits the same type.",
        "def reverse32(n):\n    r = int(str(abs(n))[::-1]) * (-1 if n < 0 else 1)\n    return r if -(2**31) <= r < 2**31 else None")
    add(333, 287, "מיון יחסי מחלק את הערכים למועדפים ולשאר", "Relative sorting separates priorities from the remainder",
        "ממיינים A=[3,1,3,2,4] לפי סדר העדיפות B=[3,2]. כפילויות נשמרות; ערכים שאינם ב־B באים אחרונים בסדר עולה. מה התוצאה?",
        "Sort A=[3,1,3,2,4] using priority order B=[3,2]. Preserve duplicates; values absent from B follow in ascending order. What is returned?",
        "[3,3,2,1,4]. תחילה מוציאים את כל מופעי 3, אחריהם את מופעי 2. לבסוף ממיינים את 1 ו־4. מפתח מיון יכול להכיל תחילה האם הערך בעדיפות, ואחר כך את דירוגו או את ערכו.",
        "[3,3,2,1,4]. Emit every 3 first, then every 2, then sort remaining 1 and 4. A sort key can first distinguish priority membership, then use priority rank or the value itself.",
        "מפתח מורכב מגדיר במפורש גם את סדר קבוצת השאר.", "A composite key explicitly orders the remainder too.")
    add(334, 289, "רצף מסתיים גם בגבול המערך", "A run can end at the array boundary",
        "מחפשים רצף אחדות ארוך ביותר ב־[0,1,0,1,1]. מחזירים [התחלה,סוף] כולל, ובתיקו את המוקדם. מדוע עדכון תשובה רק כשרואים אפס עלול להיכשל?",
        "Find the longest run of ones in [0,1,0,1,1], returning inclusive [start,end] and choosing the earliest tie. Why can updating the answer only upon seeing zero fail?",
        "הרצף הזוכה [3,4] מגיע לסוף בלי אפס שסוגר אותו. אפשר לעדכן את הטוב ביותר בכל אחד, או לבצע סגירה נוספת אחרי הלולאה. מעדכנים בתיקו רק אם המדיניות דורשת זאת; כאן שומרים את המוקדם.",
        "Winning run [3,4] reaches the end without a closing zero. Update the best result on every one, or finalize once after the loop. Update ties only as the policy requires; here retain the earlier run.",
        "תנאי סיום חיצוני חייב לטפל גם בקבוצה האחרונה.", "Termination must handle the final group as well.")
    add(335, 296, "קישור אלכסוני תלוי בהגדרת השכנות", "Diagonal connectivity depends on the neighborhood",
        "בתמונה [[1,0],[0,1]], אחד הוא שחור. כמה רכיבים שחורים יש בשכנות ארבעה וכמה בשכנות שמונה?",
        "In image [[1,0],[0,1]], one is black. How many black components exist with four-neighbor connectivity and with eight-neighbor connectivity?",
        "בשכנות ארבעה יש שני רכיבים: האלכסון אינו קישור. בשכנות שמונה יש רכיב אחד. לכן בחירת שכנות משנה גם את מספר המלבנים החוסמים, ויש לקבוע אותה לפני סריקת התמונה.",
        "Four-neighbor connectivity gives two components because diagonals do not connect. Eight-neighbor connectivity gives one. The neighborhood therefore changes the number of bounding boxes and must be specified before scanning the image.",
        "הגדרת הקשתות קודמת לחיפוש רכיבים.", "Define adjacency before searching for components.")
    add(336, 300, "תא חסום אינו מעביר מסלולים הלאה", "A blocked cell propagates no paths",
        "ברשת 3×3 נעים רק ימינה ולמטה מהפינה השמאלית העליונה לימנית התחתונה. התא המרכזי חסום. כמה מסלולים נשארים, ואיזה ערך מקבל תא חסום בטבלת הספירה?",
        "In a 3-by-3 grid, move only right and down from top-left to bottom-right. The center cell is blocked. How many paths remain, and what count does a blocked cell receive?",
        "נשארים שני מסלולים. תא חסום מקבל אפס; תא מותר מקבל את סכום הספירות שמעליו ומשמאלו. תא ההתחלה מקבל אחד רק אם הוא מותר. חסימה בהתחלה או ביעד מבטלת את כל המסלולים.",
        "Two paths remain. A blocked cell receives zero; an open cell sums counts from above and left. The start receives one only when open. Blocking the start or destination eliminates every path.",
        "מקרי הבסיס חייבים לכבד את אותם אילוצים כמו המעבר.", "Base cases must obey the same constraints as transitions.")
    add(337, 303, "רווח ASCII אינו כל תו לבן", "An ASCII space is not every whitespace character",
        "החוזה מסיר רק U+0020 ושומר על שאר התווים. מה נשאר במחרוזת \" a\\tb \"? ‎\\t מייצג טאב אחד.",
        "Remove only U+0020 and preserve every other character. What remains from \" a\\tb \"? \\t represents one tab.",
        "מתקבל a ואז טאב ואז b. רווחי ASCII נמחקים, אך הטאב נשמר. פונקציה כללית לפיצול על תווים לבנים עלולה למחוק יותר מן המותר ולשנות את התוכן.",
        "The result is a, then a tab, then b. ASCII spaces disappear but the tab remains. Generic whitespace splitting may remove more than the contract permits and change the content.",
        "בוחרים תנאי סינון לפי החוזה המדויק של התו.", "Choose character filtering according to the exact contract.",
        "def remove_spaces(text):\n    return ''.join(c for c in text if c != ' ')", topic="python")
    add(338, 295, "פענוח מספר נעצר בסוף הקידומת", "Integer parsing stops at the end of the prefix",
        "מפענח מדלג על רווחי ASCII בתחילה, קורא סימן אחד ואז ספרות ASCII רצופות. הוא עוצר בתו אחר, מחזיר אפס ללא ספרות ומרווה ל־int32. מה מתקבל מ־\" -12x34\"?",
        "A parser skips leading ASCII spaces, reads one sign and consecutive ASCII digits, stops at another character, returns zero without digits, and saturates to int32. What does \" -12x34\" produce?",
        "‎-12. האות x מסיימת את קידומת הספרות; אין לדלג עליה כדי לצרף 34. הסימן חל רק על הספרות שנקראו. מחרוזת עם סימן בלבד מחזירה אפס לפי החוזה.",
        "-12. The x ends the numeric prefix; do not skip it and append 34. The sign applies only to the consumed digits. A sign-only string returns zero under this contract.",
        "פענוח קידומת שונה מאיסוף כל הספרות במחרוזת.", "Parsing a prefix differs from collecting every digit in a string.")
    add(339, 278, "הזזה מעגלית יציבה מסיטה רק את התחום", "A stable circular move shifts only its traversed range",
        "במערך המעגלי [A,B,C,D], מעבירים את אינדקס 3 שני צעדים קדימה. מסירים את ערכו, וכל ערך בדרך זז תא אחורה; שאר הערכים נשמרים. מה התוצאה?",
        "In circular array [A,B,C,D], move index 3 forward two steps. Remove its value, shift each traversed value back one slot, and keep all others. What is the result?",
        "[B,D,C,A]. המסלול הוא 3→0→1. A עובר לאינדקס 3, B עובר ל־0 ו־D נכנס ל־1. זה אינו סיבוב של כל המערך. לפני הפעולה מצמצמים את מספר הצעדים מודולו האורך.",
        "[B,D,C,A]. The path is 3→0→1: A moves to index 3, B to 0 and D to 1. This is not rotation of the entire array. Normalize the step count modulo array length first.",
        "מודולו קובע את המסלול; יציבות קובעת אילו שכנים יזוזו.", "Modulo defines the path; stability determines how neighboring values shift.")
    add(340, 311, "השארית מגדירה מתי החילוק נגמר", "The remainder determines when division stops",
        "מחלקים 17 ב־5 בחיסור חוזר: מתחילים במנה 0 ובשארית 17; כל עוד השארית לפחות 5, מחסרים 5 ומגדילים מנה. מה המנה והשארית, ולמה המחלק חייב להיות חיובי?",
        "Divide 17 by 5 through repeated subtraction: start with quotient 0 and remainder 17; while the remainder is at least 5, subtract 5 and increment the quotient. What are quotient and remainder, and why must the divisor be positive?",
        "המנה 3 והשארית 2. לאורך התהליך 17=מנה×5+שארית, ובסיום 0≤שארית<5. מחלק חיובי מקטין את השארית ומבטיח עצירה. במחלק אפס החיסור אינו מקדם; בחוזה כאן מחזירים None לפני הלולאה. המחולק חייב להיות לא־שלילי.",
        "The quotient is 3 and remainder 2. Throughout, 17=quotient×5+remainder; on exit, 0≤remainder<5. A positive divisor decreases the remainder and guarantees termination. Subtracting zero makes no progress; this contract returns None before looping. The dividend must be nonnegative.",
        "אינווריאנט משמר את הערך ותנאי העצירה קובע שארית חוקית.", "The invariant preserves value and the stopping condition establishes a valid remainder.",
        "def divide(n, d):\n    if d <= 0: return None\n    q = 0\n    while n >= d: n -= d; q += 1\n    return [q, n]")
    add(341, 252, "עותק חיצוני עדיין עשוי לשתף משאב פנימי", "An outer copy can still share inner storage",
        "במודל Python, A=[[4],[7]]. יוצרים B כהעתק רדוד של הרשימה החיצונית, ואז מציבים B[0][0]=9. מה מכיל A? כיצד העתקה עמוקה הייתה משנה את התוצאה?",
        "In a Python model, A=[[4],[7]]. Create B as a shallow copy of the outer list, then set B[0][0]=9. What does A contain? How would a deep copy change the result?",
        "בהעתק רדוד A נעשה [[9],[7]]: הרשימות החיצוניות נפרדות אך מפנות לאותן רשימות פנימיות. בהעתק עמוק A נשאר [[4],[7]]. לעומת זאת, החלפת B[0] ברשימה חדשה משנה רק את הרשימה החיצונית של B, גם בהעתק רדוד.",
        "With a shallow copy A becomes [[9],[7]]: the separate outer lists reference the same inner lists. With a deep copy A stays [[4],[7]]. Replacing B[0] with a new list instead changes only B's outer list, even after shallow copying.",
        "עומק ההעתקה קובע אילו רמות אחסון נשארות משותפות.", "Copy depth determines which storage levels remain shared.", topic="python")
    add(342, 281, "TestAndSet מחזיר את הערך הישן", "TestAndSet returns the old value",
        "מנעול מתחיל ב־0. שתי פעולות TestAndSet אטומיות מתבצעות בזו אחר זו, וכל אחת כותבת 1 ומחזירה את הערך הישן. מה מוחזר ומי זוכה?",
        "A lock starts at 0. Two atomic TestAndSet operations occur in sequence; each writes 1 and returns the old value. What is returned and who acquires the lock?",
        "מוחזרים 0 ואז 1. הראשון רואה שהיה פנוי וזוכה; השני רואה שכבר תפוס. האטומיות מונעת משניהם לקרוא אפס לפני הכתיבה. זו הדגמה לסדר פעולות אטומי בלבד, לא הוכחה להוגנות או למודל זיכרון מלא.",
        "The returns are 0 then 1. The first sees an unlocked state and acquires; the second sees it occupied. Atomicity prevents both reading zero before writing. This demonstrates atomic ordering only, not fairness or a complete memory model.",
        "הערך המוחזר מתאר את המצב לפני השינוי האטומי.", "The return value describes the state before the atomic update.")
    add(343, 241, "אתחול מקומי סטטי מתרחש פעם אחת", "A static local initializes once",
        "פונקציה מתחילה עם static int n=0 ומחזירה ++n בכל קריאה. ללא מקביליות, מה מחזירות שלוש קריאות, ומה היה משתנה אם n היה אוטומטי?",
        "A function has static int n=0 and returns ++n per call. Without concurrency, what do three calls return, and how would an automatic local differ?",
        "משתנה סטטי נשמר בין הקריאות ולכן מתקבל 1,2,3. משתנה אוטומטי שמאותחל לאפס בכל כניסה נותן 1,1,1. תחום השם המקומי אינו קובע לבדו את משך החיים.",
        "The static variable persists, producing 1,2,3. An automatic local initialized to zero on each entry produces 1,1,1. Local name scope alone does not determine storage lifetime.",
        "תחום שם ומשך חיים הם שני מאפיינים נפרדים.", "Name scope and storage lifetime are separate properties.")
    add(344, 266, "ערוץ התוצר וסטטוס התהליך הם מידע שונה", "Product output and process status are different signals",
        "חוזה CLI דורש קוד יציאה 0 וגם תוצר stdout שאינו ריק. stderr מיועד לאבחון. תהליך יצא בקוד 0 אך stdout ריק. האם הוא עומד בחוזה?",
        "A CLI contract requires exit code 0 and nonempty stdout product data. stderr is diagnostic. A process exits with code 0 but empty stdout. Does it satisfy the contract?",
        "לא. קוד אפס לבדו אינו מוכיח שהתוצר נוצר. בודקים בנפרד את קוד היציאה ואת תנאי התוצר. הודעת אבחון ב־stderr אינה בהכרח כישלון; השפעתה נקבעת בחוזה.",
        "No. A zero status alone does not prove the product exists. Check exit status and product requirements separately. A diagnostic on stderr is not automatically failure; its meaning depends on the contract.",
        "הצלחה נמדדת לפי כל תנאי החוזה, לא לפי אות יחיד.", "Success requires every contractual condition, not a single signal.", topic="python")
    add(345, 267, "JSON תקין אינו מבטיח שדה במבנה הצפוי", "Valid JSON does not guarantee the expected field",
        "לאחר HTTP מוצלח ופענוח JSON, החוזה דורש אובייקט עם value מסוג מחרוזת. האם {\"value\":null} תקין, ואיך בודקים בלי להפוך null לטקסט?",
        "After successful HTTP and JSON decoding, require an object whose value field is a string. Is {\"value\":null} valid, and how can it be checked without converting null to text?",
        "לא. בודקים שהשורש מילון ושהערך הוא str לפני שמחזירים אותו. מפתח חסר, null ומספר אינם מחרוזת. מחרוזת ריקה מותרת לפי חוזה זה. הבדיקה כאן עוסקת בסכמה לאחר הפענוח, בלי לבצע בקשת רשת.",
        "No. Verify a dictionary root and a str field before returning it. Missing keys, null and numbers are not strings. An empty string is allowed by this contract. This checks the decoded schema without making a network request.",
        "אימות תחביר ואימות סכמה הם שלבים שונים.", "Syntax validation and schema validation are different stages.",
        "def extract(data):\n    v = data.get('value') if isinstance(data, dict) else None\n    return v if isinstance(v, str) else None", topic="python")
    add(346, 269, "רוויה אחרי כל פעולה אינה רוויה רק בסוף", "Saturating each step differs from saturating the final sum",
        "מהירות מתחילה ב־10, גז מוסיף 1 וברקס מחסיר 1. אחרי כל פעולה מרווים לטווח 0..10. מה התוצאה אחרי גז ואז ברקס, ומדוע סכימת השינויים קודם מטעה?",
        "Speed starts at 10; gas adds 1 and brake subtracts 1. Saturate to 0..10 after every action. What follows gas then brake, and why is summing changes first misleading?",
        "מתקבל 9: הגז נשאר ב־10, ואז הברקס יורד ל־9. סכימת ‎+1 ו־‎-1 קודם הייתה מחזירה 10. פעולה שנבלמה בגבול אינה נשמרת כחוב לפעולה הבאה.",
        "The result is 9: gas stays at 10, then brake reduces it to 9. Summing +1 and -1 before clamping would return 10. A change discarded at a boundary is not retained for the next action.",
        "בפעולות רוויות גם סדר הפעולות משפיע על התוצאה.", "With saturation, operation order affects the result.",
        "def speed(v, actions):\n    for delta in actions:\n        v = min(10, max(0, v + delta))\n    return v")
    add(347, 270, "תקרת ציון ידועה יכולה להצדיק עצירה מוקדמת", "A known score ceiling can certify early stopping",
        "ציוני פוקוס יציבים נמצאים תמיד בטווח 0..100, בלי הנחת צורה. שתי מדידות נתנו [20,100], ועוד שמונה מיקומים לא נמדדו. האם אפשר להחזיר ערך מקסימלי מובטח כבר עכשיו? אין דרישה למצוא את כל המיקומים הזוכים.",
        "Stable focus scores always lie in 0..100 with no shape assumption. Two measurements give [20,100] and eight positions remain unmeasured. Can a guaranteed maximum value already be returned? Finding every maximizing position is not required.",
        "כן, 100 מגיע לתקרה הידועה, ולכן שום מיקום לא נמדד אינו יכול לעבור אותו. ייתכנו זוכים נוספים, אבל ערך המקסימום מוכח. אם התוצאה הטובה ביותר נמוכה מהתקרה, דגימה מקומית לבדה אינה מספקת אותה הבטחה.",
        "Yes. 100 reaches the known ceiling, so no unmeasured position can exceed it. Other maximizing positions may exist, but the maximum value is certified. If the best observation is below the ceiling, local sampling alone cannot provide that guarantee.",
        "חסם ערכים מאפשר עצירה מוקדמת גם בלי הנחת צורת פונקציה.", "A value bound can justify early stopping without a function-shape assumption.")
    add(348, 245, "חזרה לאחור משחזרת רק את ניסיונות הענף", "Backtracking restores branch-local assignments",
        "לוח מיוצג כ־[5,0,0], כאשר 5 נתון ו־0 ריק. ענף מציב 2 ואז 7 בשני הריקים ונכשל. לאיזה מצב צריך לחזור לפני ניסיון חדש באותו עומק התחלתי?",
        "A board is [5,0,0], where 5 is fixed and 0 is empty. A branch assigns 2 then 7 to the empty cells and fails. What state must be restored before a new attempt at the original depth?",
        "[5,0,0]. מבטלים את ההשמות שהענף יצר, בסדר הפוך, ושומרים את הנתון 5. אם חוזרים רק עומק אחד, מבטלים רק את ההשמה האחרונה. גבול השחזור חייב להתאים לגבול הבחירה.",
        "Restore [5,0,0]. Undo the assignments created by the branch in reverse order and preserve given 5. Returning only one depth undoes only the last assignment. The restoration boundary must match the choice boundary.",
        "לכל בחירה זמנית יש פעולת ביטול באותו היקף.", "Every temporary choice needs an undo with matching scope.")
    add(349, 273, "מעבר מיזוג מכפיל את אורך הריצות", "A merge pass doubles the sorted run length",
        "במיון מיזוג מלמטה, [4,1,3,2,5] מתחיל בריצות באורך 1. מה המערך אחרי מעבר אחד הממזג זוגות ריצות סמוכות, ומה עושים לריצה האחרונה ללא בת זוג?",
        "In bottom-up merge sort, [4,1,3,2,5] starts with runs of length 1. What follows one pass merging adjacent run pairs, and what happens to the final unpaired run?",
        "מתקבל [1,4,2,3,5]. כל זוג הופך לריצה ממוינת באורך עד 2; הריצה [5] מועתקת ללא שינוי. המערך כולו עדיין אינו בהכרח ממוין. במעבר הבא ממזגים ריצות באורך 2.",
        "The result is [1,4,2,3,5]. Each pair becomes a sorted run of at most length 2; unpaired [5] stays unchanged. The full array need not yet be sorted. The next pass merges runs of length 2.",
        "מיון מקומי של ריצות אינו עדיין מיון גלובלי.", "Sorted local runs do not yet imply a globally sorted array.")
    add(350, 230, "סדר כתיבה וקריאה משנה את קבלת הבקשה", "Write-read ordering changes whether a request is accepted",
        "תור בקיבולת 2 מכיל [4,5], הישן ראשון. בכל קריאה מבצעים כתיבה לפני קריאה, וכתיבה לתור מלא נדחית. מבוקש לכתוב 9 ולקרוא יחד. מה נקרא ומה נשאר?",
        "A capacity-2 queue contains [4,5], oldest first. Each call processes write before read, rejecting writes when full. A call requests writing 9 and reading. What is read and what remains?",
        "הכתיבה נדחית כי התור מלא בזמן בדיקתה. אחר כך נקרא 4 ונשאר [5]. אין לחזור ולקבל את הכתיבה בגלל המקום שהתפנה מאוחר יותר, אלא אם החוזה מגדיר במפורש התנהגות כזאת.",
        "The write is rejected because the queue is full when checked. Then 4 is read and [5] remains. Do not retroactively accept the write because a later read frees space unless the contract explicitly requires that behavior.",
        "מצב הקיבולת נבחן בזמן הפעולה לפי הסדר המוגדר.", "Evaluate capacity at the operation's specified point in the sequence.")
    return cards


def build():
    cards = {c["id"]: c for c in build_cards()}
    rows, checks = [], []

    def emit(n, task, inputs, he, en, options, expected, eh, ee, difficulty=2):
        source = f"quick-sw-{n}"
        variant = 1 + sum(r["source_key"] == source for r in rows)
        choices = [x if isinstance(x, tuple) else (x, label(x), label(x)) for x in options]
        assert len(choices) == len({canonical(x[0]) for x in choices}) == 4, (n, variant)
        correct = next(i for i, x in enumerate(choices) if canonical(x[0]) == canonical(expected))
        desired = len(rows) % 4
        shift = (correct - desired) % 4
        choices = choices[shift:] + choices[:shift]
        key = f"{source}-v{variant}"
        rows.append(dict(key=key, source_key=source, variant=variant, topic=cards[source]["topic"], status="draft",
                         prompt=dict(he=he, en=en), choices=[dict(he=h, en=e) for _, h, e in choices],
                         correct=desired, explanation=dict(he=eh, en=ee)))
        checks.append(dict(key=key, task=task, inputs=inputs, options=[x[0] for x in choices], expected=expected,
                           method="Independent input-derived oracle in backend/tests/test_fundamentals_code_700.py",
                           difficulty=difficulty, difficulty_rationale=ee,
                           source_difficulty=3 if n in {324,325,330,338,339,348,350} else 2,
                           source_difficulty_rationale=cards[source]["takeaway"]["en"],
                           source_content_sha256=hashlib.sha256(canonical(cards[source]).encode()).hexdigest(),
                           provenance=dict(interview_ids=cards[source]["interviewIds"], authorship="original AI-assisted practice",
                                           professional_review="pending", calibration="editorial estimate")))

    for lists, consumed, expected, options in [
        ([[1,8],[2,3],[4]],1,[2,4,8],[[2,4,8],[2,3,4,8],[1,2,4],[3,4,8]]),
        ([[],[2],[3,5]],1,[3],[[3],[2,3],[3,5],[]]),
        ([[1,1,9],[1,4]],1,[1,1],[[1,1],[1,4],[1,9],[1]]),
        ([[7]],1,[],[[],[7],[0],[None]]),
        ([[1,6],[2,5],[3,4]],3,[4,5,6],[[4,5,6],[1,2,3],[3,5,6],[4,6]]),
    ]:
        emit(321,"merge_frontier",dict(lists=lists,consumed=consumed),
             f"החזית מכילה נציג אחד לכל רשימה שלא מוצתה. ברשימות {label(lists)}, אחרי הוצאת {consumed} איברים קטנים ביותר, מה ערכי החזית בסדר עולה? בתיקו מוציאים מהרשימה בעלת האינדקס הנמוך.",
             f"The frontier holds one representative per unexhausted list. For {label(lists)}, after removing {consumed} smallest items, what are the sorted frontier values? Break ties by the lower list index.",options,expected,
             "רק הרשימה שממנה נשלף איבר מקדמת את הנציג שלה; כפילויות ברשימות שונות נשארות נציגים נפרדים.",
             "Only the list supplying a removed item advances its representative; equal representatives from different lists remain separate.",3)

    anagram_options = [("same_counts","כן, כל השכיחויות שוות","Yes, every frequency matches"),
                       ("length","לא, האורכים שונים","No, the lengths differ"),
                       ("multiplicity","לא, אורך שווה אבל שכיחויות שונות","No, equal lengths but unequal frequencies"),
                       ("illegal","הקלט אינו חוקי","The input is invalid")]
    for a,b,expected in [("AaB","abB","multiplicity"),("Silent","LISTEN","same_counts"),("","","same_counts"),("AB","aaB","length"),("aAbB","BaBA","same_counts")]:
        emit(322,"anagram_verdict",dict(a=a,b=b),f"התווים הם אותיות ASCII; מתעלמים מהבדל בין אות גדולה לקטנה. איזו קביעה מסווגת נכון את {label(a)} ו־{label(b)} כאנגרמות אחרי נרמול? ריק מותר ויש לשמר שכיחויות.",
             f"Characters are ASCII letters; ignore letter case. Which statement correctly classifies {label(a)} and {label(b)} as anagrams after normalization? Empty strings are allowed and multiplicities must match.",
             anagram_options,expected,"מנרמלים את שתי המילים לאותיות קטנות ואז משווים מונים; שינוי גודל אות אינו משנה ריבוי או אורך.",
             "Normalize both words to lowercase, then compare counts; changing case does not change multiplicity or length.")

    for a,expected,options in [
        ([0,5,0,2],[5,2,0,0],[[5,2,0,0],[2,5,0,0],[0,0,5,2],[5,0,2,0]]),
        ([0,0],[0,0],[[0,0],[],[0],[1,1]]),
        ([-2,0,-2,1],[-2,-2,1,0],[[-2,-2,1,0],[-2,1,0,0],[1,-2,-2,0],[-2,0,-2,1]]),
        ([3,1],[3,1],[[3,1],[1,3],[3,1,0],[]]),
        ([],[],[[],[0],None,[0,0]]),
    ]:
        emit(323,"compact",dict(values=a),f"מעבירים רק אפסים לסוף {label(a)}, בלי לשנות אורך או סדר של ערכים אחרים. מה הפלט?",
             f"Move only zeros to the end of {label(a)}, preserving length and the order of all other values. What is returned?",options,expected,
             "שומרים כל מופע שאינו אפס בסדר הסריקה ומשלימים את אותו מספר האפסים בסוף.",
             "Keep every nonzero occurrence in scan order, then append the original number of zeros.")

    for links,prev,cur,expected,options in [
        ({"A":"B","B":"C","C":None},None,"A",["A","B",None],[["A","B",None],[None,"A","B"],["A",None,"B"],["B","C","A"]]),
        ({"A":None,"B":"C","C":None},"A","B",["B","C","A"],[["B","C","A"],["B","A","A"],["A","C","B"],["C",None,"B"]]),
        ({"A":None,"B":"A","C":None},"B","C",["C",None,"B"],[["C",None,"B"],["C","B",None],["B",None,"C"],[None,"C","B"]]),
        ({"X":None},None,"X",["X",None,None],[["X",None,None],[None,"X",None],["X","X",None],[None,None,"X"]]),
        ({"P":None,"Q":"R","R":"S","S":None},"P","Q",["Q","R","P"],[["Q","R","P"],["Q","S","P"],["P","R","Q"],["Q","P","R"]]),
    ]:
        emit(324,"reverse_step",dict(links=links,previous=prev,current=cur),
             f"קישורי next הם {label(links)}; previous={label(prev)},current={label(cur)}. מבצעים צעד היפוך: שומרים יורש, הופכים קישור ומקדמים. מה [previous החדש,current החדש,next של החוליה שטופלה]?",
             f"Next links are {label(links)}; previous={label(prev)},current={label(cur)}. One reversal step saves the successor, reverses the link and advances. What is [new previous,new current,processed node's next]?",options,expected,
             "היורש מגיע מהקישור הישן; הקישור החדש פונה ל־previous הישן, והחוליה שטופלה נעשית previous החדש.",
             "The successor comes from the old link; the new link targets old previous, and the processed node becomes new previous.",3)

    for record,expected,options in [
        ('"a,b",c',["a,b","c"],[["a,b","c"],["a","b","c"],['"a,b"',"c"],["a,b,c"]]),
        ('"a""b",c',['a"b',"c"],[['a"b',"c"],["ab","c"],['a""b',"c"],["a","b","c"]]),
        ('a,b,',["a","b",""],[["a","b",""],["a","b"],["a,b",""],["a","b",None]]),
        (',,',["","",""],[["","",""],["",""],[],[",,"]]),
        ('"a\nb",c',["a\nb","c"],[["a\nb","c"],["a","b","c"],["ab","c"],["a\nb,c"]]),
    ]:
        emit(325,"csv_record",dict(record=record),
             f"פענחו רשומת CSV תקינה {label(record)}. מרכאות כפולות חיצוניות תוחמות שדה; זוג פנימי מייצג מרכאה. \\n הוא ירידת שורה בתוך שדה. מה רשימת השדות, כולל ריקים?",
             f"Decode valid CSV record {label(record)}. Outer quotes delimit a field; doubled inner quotes encode one quote. \\n denotes a newline inside a field. What fields result, including empties?",options,expected,
             "בתוך מרכאות שומרים פסיקים וירידות שורה כתוכן, מפענחים זוג מרכאות, ומשמרים גם שדה ריק אחרון.",
             "Inside quotes retain commas and newlines as content, decode doubled quotes, and preserve a trailing empty field.",3)

    for mode,original,edited,expected in [("owned","cat","bat","cat"),("borrowed","cat","bat","bat"),("owned","","x",""),("owned","same","same","same"),("borrowed","key","","" )]:
        options=list(dict.fromkeys([expected,original,edited,"lost","unchanged-buffer","error"]))[:4]
        emit(326,"key_storage",dict(mode=mode,original=original,edited=edited),
             f"מודל אחסון מפתח: owned מעתיק תוכן, borrowed משתף מאגר חי. מצב {mode}; הוכנס {label(original)}, ואז המאגר השתנה ל־{label(edited)}. לפני שחרור כלשהו, מה קוראים מהמפתח השמור?",
             f"Key-storage model: owned copies bytes; borrowed shares a live buffer. Mode {mode}; insert {label(original)}, then change that buffer to {label(edited)}. Before any release, what does the stored key read?",options,expected,
             "עותק פרטי שומר את התוכן בזמן ההכנסה; הפניה למאגר חי רואה את התוכן הנוכחי שלו.",
             "A private copy retains insertion-time contents; a reference to a live buffer observes its current contents.")

    for row,col,box,expected,options in [
        ([1,2],[3,4],[5,6,7],[8,9],[[8,9],[1,2],[7,8,9],[]]),
        ([1,2,3],[4,5,6],[7,8,9],[],[[],[9],[1,2,3],list(range(1,10))]),
        ([1,2],[2,3],[3,4],[5,6,7,8,9],[[5,6,7,8,9],[1,2,3,4],[7,8,9],[2,3]]),
        ([],[],[],list(range(1,10)),[list(range(1,10)),[],[0],list(range(9))]),
        ([1,2,3,4],[5,6],[7,8],[9],[[9],[0],[8,9],[]]),
    ]:
        emit(327,"sudoku_candidates",dict(row=row,col=col,box=box),
             f"בסודוקו 1..9, ספרות נראות בשורה {label(row)}, בעמודה {label(col)} ובתיבה {label(box)}. אילו ספרות מותרות בתא הריק, בסדר עולה?",
             f"In Sudoku with digits 1..9, the row contains {label(row)}, column {label(col)}, and box {label(box)}. Which digits may fill the empty cell, sorted ascending?",options,expected,
             "מסירים מהתחום כל ספרה שמופיעה לפחות באחד משלושת האזורים; הופעה בכמה אזורים אינה מסירה ספרה נוספת.",
             "Exclude each digit present in any of the three regions; appearing in multiple regions does not exclude another digit.")

    for positions,expected,options in [
        ([0,2,8,10],[2,8],[[2,8],[5,5],[0,10],[2,2]]),
        ([1,3,9],[3,3],[[3,3],[1,9],[4,4],[1,3]]),
        ([4,4,4,10],[4,4],[[4,4],[4,10],[5,5],[7,7]]),
        ([-5,-1],[-5,-1],[[-5,-1],[-3,-3],[-5,-5],[-1,-1]]),
        ([7],[7,7],[[7,7],[0,7],[0,0],[6,8]]),
    ]:
        emit(328,"median_interval",dict(positions=positions),
             f"מיקומי אנשים ברחוב ישר: {label(positions)}. מחפשים את כל מיקומי המפגש השלמים שממזערים סכום מרחקים מוחלטים. מה [קצה שמאלי,קצה ימני] של תחום המינימום?",
             f"People's positions on a straight street are {label(positions)}. Find all integer meeting positions minimizing total absolute distance. What is [left endpoint,right endpoint] of the optimal interval?",options,expected,
             "ממיינים מיקומים; התחום נמצא בין שני האיברים האמצעיים, שהם אותו איבר בכמות אי־זוגית.",
             "Sort the positions; the optimum lies between the two middle entries, which coincide for an odd count.",3)

    for values,expected in [([3,4,-1,1],2),([1,2,3],4),([1,1,0,-3],2),([],1),([100,2,3],1)]:
        options=list(dict.fromkeys([expected,0,len(values)+1,1,2,3,5]))[:4]
        emit(329,"missing_positive",dict(values=values),f"מה המספר החיובי הקטן ביותר שאינו מופיע ב־{label(values)}? כפילויות, אפס ושליליים מותרים בקלט.",
             f"What is the smallest positive integer absent from {label(values)}? Duplicates, zero and negatives are allowed in the input.",options,expected,
             "בודקים חיוביים החל מ־1 עד החסר הראשון; כפילות אינה ממלאת מקום של מספר אחר.",
             "Check positives from 1 until the first absent value; a duplicate cannot fill another value's place.")

    for events,expected,options in [
        ([["put",1],["put",2],["get",None],["put",3],["get",None],["get",None]],[1,2,3],[[1,2,3],[1,3,2],[2,1,3],[3,2,1]]),
        ([["get",None]],[None],[[None],[],[0],[False]]),
        ([["put",5],["put",5],["get",None],["get",None],["get",None]],[5,5,None],[[5,5,None],[5,None,None],[None,5,5],[5,5,5]]),
        ([["put",4],["get",None],["put",8],["get",None]],[4,8],[[4,8],[8,4],[4,4],[None,8]]),
        ([["put",1],["put",2],["put",3],["get",None],["put",4],["get",None]],[1,2],[[1,2],[1,4],[3,2],[2,3]]),
    ]:
        emit(330,"two_stack_queue",dict(events=events),
             f"תור מתחיל ריק. put מכניס, get מוציא את הישן ומחזיר None בריק. האירועים הם {label(events)}. מעבירים בין המחסניות רק כשהיציאה ריקה. מה רצף תוצאות get?",
             f"A queue starts empty. put enqueues; get removes the oldest item, returning None when empty. Events: {label(events)}. Transfer stacks only when outgoing is empty. What are the get results?",options,expected,
             "היפוך הכניסה מתבצע רק לאחר מיצוי כל הערכים הישנים ביציאה; לכן get שומר סדר FIFO.",
             "Reverse incoming only after exhausting older outgoing values, so get preserves FIFO order.",3)

    for left,right,op,value,expected,options in [
        (["a","b"],["d","c"],"right",None,[["a","b","c"],["d"]],[[["a","b","c"],["d"]],[["a","b","d"],["c"]],[["a"],["d","c","b"]],[["a","b"],["d","c"]]]),
        (["a","b"],["c"],"left",None,[["a"],["c","b"]],[[["a"],["c","b"]],[["a"],["b","c"]],[[],["c","b","a"]],[["a","b","c"],[]]]),
        (["x"],[],"right",None,[["x"],[]],[[["x"],[]],[[],["x"]],[[],[]],[["x","x"],[]]]),
        (["a","b"],["c"],"backspace",None,[["a"],["c"]],[[["a"],["c"]],[["b"],["c"]],[["a","b"],[]],[[],["c"]]]),
        ([],["b","a"],"insert","x",[["x"],["b","a"]],[[["x"],["b","a"]],[[],["b","a","x"]],[["a","x"],["b"]],[["x"],["a","b"]]]),
    ]:
        emit(331,"cursor",dict(left=left,right=right,operation=op,value=value),
             f"מחסניות סמן רשומות מתחתית לראש: L={label(left)},R={label(right)}. right/left מעבירות תו קרוב; backspace מוחק משמאל; insert מוסיף משמאל. בקצה תנועה לא משנה. מבצעים {op} עם {label(value)}. מה [L,R]?",
             f"Cursor stacks bottom-to-top: L={label(left)},R={label(right)}. right/left transfer the nearest character; backspace deletes left; insert adds left. Movement at an edge does nothing. Apply {op} with {label(value)}. What is [L,R]?",options,expected,
             "התו הסמוך לסמן הוא ראש המחסנית המתאימה. העברה משנה את גבול הסמן, מחיקה מסירה תו והכנסה מוסיפה ל־L.",
             "The adjacent character is the appropriate stack top. Transfer moves the cursor boundary, deletion removes a character, and insertion pushes onto L.",3)

    for n,expected,options in [
        (-120,-21,[-21,21,-210,-120]),
        (0,0,[0,None,1,-1]),
        (1534236469,None,[None,9646324351,1534236469,2147483647]),
        (-2147483648,None,[None,-8463847412,-2147483648,0]),
        (1463847412,2147483641,[2147483641,None,2147483647,1463847412]),
    ]:
        emit(332,"reverse32",dict(number=n),f"הופכים את הספרות העשרוניות של {n}, שומרים סימן ומשמיטים אפסים מובילים בתוצאה. מחזירים None מחוץ לטווח ‎-2147483648..2147483647. מה הפלט?",
             f"Reverse the decimal digits of {n}, preserve sign, and drop leading result zeros. Return None outside -2147483648..2147483647. What is returned?",options,expected,
             "הופכים את ספרות הערך המוחלט, מחזירים סימן ובודקים את שני גבולות int32 לפני החזרת התוצאה.",
             "Reverse the magnitude's digits, restore the sign, and check both int32 bounds before returning.",3 if expected is None else 2)

    for a,b,expected,options in [
        ([3,1,3,2,4],[3,2],[3,3,2,1,4],[[3,3,2,1,4],[1,2,3,3,4],[3,2,1,4],[3,3,2,4,1]]),
        ([4,1,4],[],[1,4,4],[[1,4,4],[4,1,4],[4,4,1],[]]),
        ([2,1,2],[9,2],[2,2,1],[[2,2,1],[9,2,2,1],[2,1],[1,2,2]]),
        ([-1,0,-2,-1],[0,-1],[0,-1,-1,-2],[[0,-1,-1,-2],[-2,-1,-1,0],[0,-1,-2],[0,-2,-1,-1]]),
        ([],[2,1],[],[[],[2,1],[1,2],None]),
    ]:
        emit(333,"relative_sort",dict(values=a,priority=b),
             f"A={label(a)}, סדר עדיפות B={label(b)} ללא כפילויות. מוציאים את מופעי A לפי B, ואז את השאר בסדר עולה. אין להמציא ערך שאינו ב־A. מה הפלט?",
             f"A={label(a)}, duplicate-free priority B={label(b)}. Output A's occurrences in B order, then remaining values ascending. Never invent a value absent from A. What is returned?",options,expected,
             "סדר העדיפות חל רק על ערכים קיימים; המונים נשמרים, ושאר הערכים ממוינים לפי ערכם.",
             "Priority applies only to present values; retain counts and sort the remainder numerically.")

    for bits,expected,options in [
        ([0,1,0,1,1],[3,4],[[3,4],[1,1],[3,5],[1,4]]),
        ([1,1,0,1,1],[0,1],[[0,1],[3,4],[0,4],[0,2]]),
        ([0,0],None,[None,[0,0],[0,1],[]]),
        ([1,1,1],[0,2],[[0,2],[0,3],[1,2],None]),
        ([],None,[None,[0,-1],[0,0],[]]),
    ]:
        emit(334,"longest_ones",dict(bits=bits),
             f"במערך {label(bits)}, החזירו [התחלה,סוף] כולל של רצף האחדות הארוך ביותר. אינדקסים מ־0, תיקו מוכרע למוקדם, וללא אחדות מוחזר None. מה הפלט?",
             f"For {label(bits)}, return inclusive [start,end] of the longest ones run. Indices start at 0; choose the earliest tie and return None when there are no ones. What is returned?",options,expected,
             "מונים רק אחדות רצופות; אפס מסיים רצף, וגם הרצף האחרון נבדק. בתיקו נשמר הראשון.",
             "Count contiguous ones only; zero ends a run, and the final run is checked too. Keep the first tie.")

    for grid,neighbors,expected,options in [
        ([[1,0],[0,1]],4,2,[0,1,2,4]),
        ([[1,0],[0,1]],8,1,[0,1,2,4]),
        ([[1,1,1],[1,0,1],[1,1,1]],4,1,[1,2,4,8]),
        ([[0,0],[0,0]],8,0,[0,1,2,4]),
        ([[1,0,1],[0,0,0],[1,0,1]],8,4,[1,2,3,4]),
    ]:
        emit(335,"components",dict(grid=grid,neighbors=neighbors),
             f"בתמונה {label(grid)}, אחד הוא שחור ואפס לבן. בשכנות {neighbors}, כמה רכיבים שחורים יש? שכנות 4 היא צלע בלבד; 8 מוסיפה אלכסונים. אין גלישה מעבר לגבול התמונה.",
             f"In image {label(grid)}, one is black and zero white. How many black components exist with {neighbors}-neighbor connectivity? 4 uses shared sides; 8 also uses diagonals. Image boundaries do not wrap.",options,expected,
             "מאגדים רק פיקסלים שחורים המחוברים במסלול של שכנים מותרים; שטח לבן אינו יוצר רכיב שחור.",
             "Group black pixels connected by paths of permitted neighbors; white space contributes no black component.",3)

    for height,width,blocked,expected,options in [
        (3,3,[[1,1]],2,[0,2,4,6]),
        (1,1,[],1,[0,1,2,4]),
        (2,3,[[0,0]],0,[0,1,2,3]),
        (2,3,[[1,2]],0,[0,1,2,3]),
        (2,3,[[0,1]],1,[0,1,2,3]),
    ]:
        emit(336,"grid_paths",dict(height=height,width=width,blocked=blocked),
             f"רשת בגובה {height} וברוחב {width}; חסומים [שורה,עמודה]={label(blocked)} באינדקסים מ־0. כמה מסלולי ימינה/למטה קיימים מ־[0,0] לתא הימני התחתון, בלי להיכנס לחסום? מסלול ללא צעדים נספר.",
             f"Grid height {height}, width {width}; blocked [row,column]={label(blocked)} with indices from 0. How many right/down paths lead from [0,0] to bottom-right without entering blocked cells? A zero-step path counts.",options,expected,
             "סופרים רק מסלולים שנמצאים בתאים מותרים לכל אורכם; גם תא ההתחלה והיעד כפופים לחסימה.",
             "Count paths whose every cell is open; the start and destination obey blocking too.",3)

    for value,expected,options in [
        (" a\tb ","a\tb",["a\tb","ab"," a\tb ","a b"]),
        ("a\nb c","a\nbc",["a\nbc","abc","a\nb c","a bc"]),
        ("   ","",[""," ","   ",None]),
        ("a\u00a0 b","a\u00a0b",["a\u00a0b","ab","a b","a\u00a0 b"]),
        ("abc","abc",["abc","cba","",None]),
    ]:
        emit(337,"remove_spaces",dict(text=value),
             f"מסירים רק רווח ASCII U+0020 מ־{label(value)}. \\t הוא טאב, \\n ירידת שורה; U+00A0 הוא רווח קשיח שחייב להישמר. מה הפלט?",
             f"Remove only ASCII space U+0020 from {label(value)}. \\t denotes tab, \\n newline; U+00A0 is a nonbreaking space that must remain. What is returned?",options,expected,
             "מסננים תו רק כשהוא U+0020; שומרים את סדר כל שאר התווים ואת תוכנם המדויק.",
             "Filter a character only when it is U+0020; preserve every other character and its order.")

    for value,expected,options in [
        (" -12x34",-12,[-12,-1234,12,0]),
        ("+-7",0,[0,-7,7,None]),
        ("2147483648",2147483647,[2147483647,2147483648,-2147483648,0]),
        ("-9999999999",-2147483648,[-2147483648,-9999999999,2147483647,0]),
        ("\t12",0,[0,12,None,-12]),
    ]:
        emit(338,"atoi_prefix",dict(text=value),
             f"קלט {label(value)}. מדלגים רק על רווח ASCII בתחילה, קוראים סימן אחד ואז ספרות ASCII רצופות. עוצרים בתו אחר; ללא ספרות מחזירים 0; מרווים ל־‎-2147483648..2147483647. מה התוצאה?",
             f"Input {label(value)}. Skip leading ASCII spaces only, read one sign and consecutive ASCII digits, then stop at another character. Without digits return 0; saturate to -2147483648..2147483647. What is returned?",options,expected,
             "קוראים קידומת לפי הדקדוק בלבד, בלי לדלג על תו מפריע; לאחר החלת הסימן מגבילים לטווח.",
             "Consume only the grammatical prefix without skipping an interrupting character; apply sign, then clamp to the range.",3)

    for a,start,steps,expected,options in [
        ([0,1,2,3],3,2,[1,3,2,0],[[1,3,2,0],[2,3,0,1],[0,3,1,2],[3,0,1,2]]),
        ([0,1,2,3],1,0,[0,1,2,3],[[0,1,2,3],[1,0,2,3],[0,2,3,1],[3,0,1,2]]),
        ([0,1,2,3],1,4,[0,1,2,3],[[0,1,2,3],[0,2,3,1],[1,2,3,0],[3,0,1,2]]),
        ([0,1,2,3],0,3,[1,2,3,0],[[1,2,3,0],[3,0,1,2],[0,3,2,1],[1,0,2,3]]),
        ([0,1,0,1,1],4,2,[1,1,0,1,0],[[1,1,0,1,0],[1,0,1,0,1],[0,1,0,1,1],[1,0,0,1,1]]),
    ]:
        emit(339,"circular_move",dict(values=a,start=start,steps=steps),
             f"במערך מעגלי {label(a)} מעבירים את הערך באינדקס {start} קדימה {steps} צעדים מודולו האורך. כל איבר במסלול זז תא אחורה והערך שנשמר נכנס לסוף המסלול. אינדקסים מ־0. מה המערך?",
             f"In circular array {label(a)}, move index {start} forward {steps} steps modulo the length. Each traversed item shifts back one slot and the saved value enters the path's end. Indices start at 0. What results?",options,expected,
             "מחשבים מסלול אינדקסים מעגלי, מעתיקים כל יורש לקודמו ואז מציבים את הערך שנשמר ביעד.",
             "Form the circular index path, copy each successor into its predecessor, then place the saved value at the destination.",3)

    for dividend,divisor,expected,options in [
        (17,5,[3,2],[[3,2],[2,3],[4,-3],[3,0]]),
        (3,5,[0,3],[[0,3],[1,-2],[3,0],[0,0]]),
        (15,5,[3,0],[[3,0],[2,5],[0,3],[4,-5]]),
        (0,7,[0,0],[[0,0],[1,0],[0,7],None]),
        (5,0,None,[None,[0,5],[5,0],[0,0]]),
    ]:
        emit(340,"division",dict(dividend=dividend,divisor=divisor),
             f"מחולק לא־שלילי {dividend}, מחלק {divisor}. עבור מחלק חיובי מחסרים אותו כל עוד השארית לפחות המחלק, וסופרים חיסורים. מחלק שאינו חיובי מחזיר None לפני הלולאה. מה [מנה,שארית] או None?",
             f"Nonnegative dividend {dividend}, divisor {divisor}. For a positive divisor, subtract it while the remainder is at least the divisor, counting subtractions. A nonpositive divisor returns None before looping. What is [quotient,remainder] or None?",options,expected,
             "בחילוק תקף נשמר מחולק=מנה×מחלק+שארית, ובסוף השארית קטנה מהמחלק. מחלק אפס נדחה כדי שלא תיווצר לולאה ללא התקדמות.",
             "Valid division preserves dividend=quotient×divisor+remainder and ends with remainder below divisor. Reject zero to avoid a loop with no progress.")

    for values,mode,op,index,value,expected,options in [
        ([[4],[7]],"shallow","inner_set",0,9,[[[9],[7]],[[9],[7]]],[[[[9],[7]],[[9],[7]]],[[[4],[7]],[[9],[7]]],[[[4],[7]],[[4],[7]]],[[[9],[7]],[[4],[7]]]]),
        ([[4],[7]],"deep","inner_set",0,9,[[[4],[7]],[[9],[7]]],[[[[4],[7]],[[9],[7]]],[[[9],[7]],[[9],[7]]],[[[4],[7]],[[4],[7]]],[[[9],[7]],[[4],[7]]]]),
        ([[4],[7]],"shallow","outer_replace",0,[9],[[[4],[7]],[[9],[7]]],[[[[4],[7]],[[9],[7]]],[[[9],[7]],[[9],[7]]],[[[4],[7]],[[4],[7],[9]]],[[[4],[7]],[[4],[9]]]]),
        ([[4],[7]],"shallow","outer_append",None,[8],[[[4],[7]],[[4],[7],[8]]],[[[[4],[7]],[[4],[7],[8]]],[[[4],[7],[8]],[[4],[7],[8]]],[[[4],[7]],[[8],[7]]],[[[4],[7]],[[4],[7]]]]),
        ([[1,2],[]],"deep","inner_append",1,5,[[[1,2],[]],[[1,2],[5]]],[[[[1,2],[]],[[1,2],[5]]],[[[1,2],[5]],[[1,2],[5]]],[[[1,2],[]],[[1,2],[],[5]]],[[[1,2],[]],[[1,2,5],[]]]]),
    ]:
        operation = {"inner_set":f"B[{index}][0]={label(value)}", "outer_replace":f"B[{index}]={label(value)}",
                     "outer_append":f"B.append({label(value)})", "inner_append":f"B[{index}].append({label(value)})"}[op]
        emit(341,"copy_mutation",dict(values=values,mode=mode,operation=op,index=index,value=value),
             f"מודל Python: A={label(values)}. יוצרים B בהעתקת {mode}: shallow מעתיקה רק רשימה חיצונית; deep גם את הפנימיות. מבצעים {operation}. אינדקסים מ־0. מה [A,B] אחרי השינוי?",
             f"Python model: A={label(values)}. Create B using a {mode} copy: shallow duplicates only the outer list; deep also duplicates inner lists. Perform {operation}. Indices start at 0. What is [A,B] afterward?",options,expected,
             "עותק רדוד משתף רשימות פנימיות אך לא את החיצונית. עותק עמוק מפריד גם פנימיות; מזהים איזו רמה הפעולה משנה.",
             "A shallow copy shares inner lists but separates the outer list. A deep copy separates both; identify which storage level the operation changes.",3)

    for initial,events,expected,options in [
        (0,["tas","tas"],[[0,1],1],[[[0,1],1],[[0,0],1],[[1,1],1],[[0,1],0]]),
        (1,["tas"],[[1],1],[[[1],1],[[0],1],[[1],0],[[],1]]),
        (0,["tas","release","tas"],[[0,0],1],[[[0,0],1],[[0,1],1],[[1,0],1],[[0,0],0]]),
        (0,["tas","release"],[[0],0],[[[0],0],[[0],1],[[1],0],[[],0]]),
        (1,["tas","tas","release","tas"],[[1,1,0],1],[[[1,1,0],1],[[1,1,1],1],[[0,0,0],1],[[1,0,0],0]]),
    ]:
        emit(342,"test_and_set",dict(initial=initial,events=events),
             f"ביט מנעול מתחיל ב־{initial}. סדר אטומי {label(events)}: tas מחזיר ערך ישן וכותב 1; release חוקי כותב 0 ואינו מחזיר תוצאה. מה [תוצאות tas,הביט הסופי]? אין לנתח הוגנות.",
             f"Lock bit starts at {initial}. Atomic sequence {label(events)}: tas returns the old bit and writes 1; a valid release writes 0 without a result. What is [tas returns,final bit]? Do not analyze fairness.",options,expected,
             "מתקדמים בסדר האטומי הנתון; כל tas מדווח את המצב שלפני הכתיבה, וכל release מפנה את המנעול.",
             "Follow the stated atomic order; each tas reports the state before its write, and each release clears the lock.",3)

    for initial,deltas,mode,expected,options in [
        (0,[1,1,1],"static",[1,2,3],[[1,2,3],[1,1,1],[0,1,2],[3,3,3]]),
        (0,[1,1,1],"automatic",[1,1,1],[[1,1,1],[1,2,3],[0,0,0],[3,2,1]]),
        (5,[2,-1,0],"static",[7,6,6],[[7,6,6],[7,4,5],[5,7,6],[7,6,5]]),
        (5,[2,-1,0],"automatic",[7,4,5],[[7,4,5],[7,6,6],[5,5,5],[2,-1,0]]),
        (0,[],"static",[],[[],[0],[1],None]),
    ]:
        emit(343,"local_lifetime",dict(initial=initial,deltas=deltas,mode=mode),
             f"משתנה n מאותחל ל־{initial}. מצב {mode}: static מאתחל פעם אחת ושומר מצב; automatic מאתחל בכל קריאה. הקריאות מוסיפות בהתאמה {label(deltas)} ומחזירות n אחרי החיבור. מה רצף התוצאות? אין מקביליות.",
             f"Variable n initializes to {initial}. Mode {mode}: static initializes once and persists; automatic initializes each call. Calls add respective deltas {label(deltas)} and return n after addition. What results? There is no concurrency.",options,expected,
             "במצב סטטי כל חיבור מתחיל בתוצאה הקודמת; במצב אוטומטי כל חיבור מתחיל בערך האתחול.",
             "In static mode each addition starts from the previous result; in automatic mode it starts from the initializer.")

    cli_options = [("success","כל תנאי ההצלחה מתקיימים","All success conditions hold"),
                   ("status","קוד היציאה מפר את החוזה","The exit status violates the contract"),
                   ("output","תוצר stdout חסר","The stdout product is missing"),
                   ("stderr","stderr לבדו קובע כישלון","stderr alone establishes failure")]
    for status,stdout,stderr,expected in [(0,"data","","success"),(0,"","","output"),(2,"data","failure","status"),(0,"data","warning","success"),(0," ","","success")]:
        emit(344,"cli_contract",dict(status=status,stdout=stdout,stderr=stderr),
             f"חוזה הצלחה: קוד יציאה 0 וגם אורך stdout גדול מ־0; אפילו רווח נחשב תוצר. stderr אבחוני בלבד. קוד={status},stdout={label(stdout)},stderr={label(stderr)}. איזו קביעה נכונה?",
             f"Success requires exit code 0 and stdout length greater than 0; even a space counts as product. stderr is diagnostic only. Code={status},stdout={label(stdout)},stderr={label(stderr)}. Which statement is correct?",cli_options,expected,
             "בודקים צירוף של קוד אפס ותוצר שאורכו חיובי. תוכן stderr אינו משנה תנאים אלה בחוזה שנבחר.",
             "Check the conjunction of zero status and positive product length. Under this contract stderr contents do not change those conditions.")

    for data,expected,options in [
        ({"value":"hi","id":7},"hi",["hi",None,7,'{"value":"hi"}']),
        ({"value":None},None,[None,"null","None",""]),
        ({"id":7},None,[None,7,"id",""]),
        ({"value":""},"",["",None,"value","null"]),
        ([{"value":"hi"}],None,[None,"hi","value",""]),
    ]:
        emit(345,"extract_field",dict(data=data),
             f"HTTP ופענוח JSON כבר הצליחו. הנתון {label(data)}. מחזירים value רק אם השורש אובייקט והשדה מחרוזת, כולל ריקה; אחרת None. אין המרת טיפוסים ואין ירידה למבנים פנימיים. מה הפלט?",
             f"HTTP and JSON decoding already succeeded. Data is {label(data)}. Return value only if the root is an object and the field a string, including empty; otherwise None. Do not coerce types or search nested structures. What results?",options,expected,
             "מאמתים גם טיפוס שורש וגם טיפוס שדה; ערך חסר או null אינו מחרוזת, ואילו מחרוזת ריקה כן.",
             "Validate both root and field types; a missing or null field is not a string, whereas an empty string is.")

    for initial,actions,expected,options in [
        (10,[1,-1],9,[9,10,11,8]),
        (0,[-1,1],1,[0,1,-1,2]),
        (9,[1,1,-1],9,[9,10,11,8]),
        (5,[],5,[0,5,6,10]),
        (1,[-1,-1,1,1],2,[0,1,2,3]),
    ]:
        emit(346,"speed",dict(initial=initial,actions=actions),
             f"מהירות התחלתית {initial}, פעולות {label(actions)} כאשר 1 הוא גז ו־‎-1 ברקס. אחרי כל פעולה מרווים לטווח 0..10. מה המהירות הסופית?",
             f"Initial speed {initial}, actions {label(actions)} where 1 is gas and -1 brake. Clamp to 0..10 after every individual action. What is the final speed?",options,expected,
             "מבצעים חיבור ורוויה בכל צעד לפי הסדר; שינוי שנחתך בגבול אינו נשמר לצעד מאוחר יותר.",
             "Add and clamp at each step in order; a change discarded at a boundary is not retained for a later step.")

    certainty_options = [("unknown","אין הבטחה: מיקום לא ידוע יכול להיות גדול יותר","No guarantee: an unknown position could be greater"),
                         ("upper","יש הבטחה: נמדד החסם העליון","Guaranteed: the upper bound was observed"),
                         ("complete","יש הבטחה: כל המיקומים נמדדו","Guaranteed: every position was measured"),
                         ("local","יש הבטחה: ירידה מקומית מספיקה","Guaranteed: a local decrease suffices")]
    for observed,unknown,upper,expected in [([20,30,25],1,100,"unknown"),([20,100],8,100,"upper"),([5,2,4],0,100,"complete"),([9,8],2,10,"unknown"),([0],5,0,"upper")]:
        emit(347,"maximum_certainty",dict(observed=observed,unknown=unknown,upper=upper),
             f"ציונים בלתי תלויים יכולים להיות כל שלם בטווח 0..{upper}. נמדדו {label(observed)} ונשארו {unknown} מיקומים לא ידועים. אין הנחת צורה. איזו קביעה נכונה לגבי הבטחה למקסימום הגלובלי?",
             f"Independent scores may be any integer in 0..{upper}. Observed scores are {label(observed)} with {unknown} unmeasured positions. No shape assumption applies. Which statement correctly describes whether the global maximum is guaranteed?",certainty_options,expected,
             "הבטחה קיימת כשכל המיקומים נמדדו או כשהמדידה כבר מגיעה לחסם העליון; אחרת ערך לא ידוע יכול להיות גדול יותר.",
             "Guarantee holds when all positions are measured or the known upper bound is reached; otherwise an unknown score could be greater.",3)

    for board,assignments,undo,expected,options in [
        ([5,0,0],[[1,2],[2,7]],2,[5,0,0],[[5,0,0],[0,0,0],[5,2,0],[5,2,7]]),
        ([5,0,0],[[1,2],[2,7]],1,[5,2,0],[[5,2,0],[5,0,0],[5,0,7],[5,2,7]]),
        ([0,4],[[0,3]],0,[3,4],[[3,4],[0,4],[3,0],[0,0]]),
        ([8,0],[],0,[8,0],[[8,0],[0,0],[8,8],[0,8]]),
        ([0,0,6,0],[[0,1],[1,2],[3,3]],2,[1,0,6,0],[[1,0,6,0],[0,0,6,0],[1,2,6,0],[0,0,0,3]]),
    ]:
        emit(348,"undo_branch",dict(board=board,assignments=assignments,undo=undo),
             f"מצב התחלתי {label(board)}; אפס ריק וערכים אחרים נתונים קבועים. מבצעים השמות [אינדקס,ערך] {label(assignments)} באינדקסים מ־0, ואז מבטלים בדיוק {undo} השמות אחרונות. מה המצב? זהו רישום ענף, לא לוח סודוקו מלא.",
             f"Initial state {label(board)}; zero is empty and other values are fixed givens. Apply [index,value] assignments {label(assignments)} with indices from 0, then undo exactly the last {undo} assignments. What remains? This is a branch log, not a full Sudoku board.",options,expected,
             "מבטלים מהסוף רק את ההשמות שנכללות בהיקף החזרה; נתונים קבועים והחלטות של עומק קודם נשמרים.",
             "Undo from the end only assignments within the rollback scope; preserve fixed givens and earlier-depth choices.",3)

    for values,width,expected,options in [
        ([4,1,3,2,5],1,[1,4,2,3,5],[[1,4,2,3,5],[1,2,3,4,5],[4,1,3,2,5],[1,4,2,5,3]]),
        ([1,4,2,3,5],2,[1,2,3,4,5],[[1,2,3,4,5],[1,4,2,3,5],[2,3,1,4,5],[1,2,4,3,5]]),
        ([2,2,1,1],1,[2,2,1,1],[[2,2,1,1],[1,1,2,2],[2,1,2,1],[1,2,1,2]]),
        ([1,5,2,4,0],2,[1,2,4,5,0],[[1,2,4,5,0],[0,1,2,4,5],[1,5,0,2,4],[1,2,4,0,5]]),
        ([],1,[],[[],[0],None,[1]]),
    ]:
        emit(349,"merge_pass",dict(values=values,width=width),
             f"במיון מיזוג מלמטה, מחלקים את {label(values)} מאינדקס 0 לריצות באורך {width}; האחרונה עשויה להיות קצרה. כל ריצה ממוינת. ממזגים כל זוג ריצות סמוכות; ריצה ללא בת זוג נשארת. מה המערך אחרי מעבר אחד?",
             f"In bottom-up merge sort, partition {label(values)} from index 0 into runs of length {width}; the last may be shorter. Each run is sorted. Merge each adjacent pair; an unpaired run remains. What is the array after one pass?",options,expected,
             "ממזגים בתוך מקטעים באורך עד פי שניים מאורך הריצה; אין למיין יחד מקטעים שטרם נפגשו במעבר.",
             "Merge within chunks of at most twice the run length; do not combine chunks that this pass has not yet brought together.",3)

    for capacity,queue,write,read,expected,options in [
        (2,[4,5],9,True,[False,4,[5]],[[False,4,[5]],[True,4,[5,9]],[True,9,[4,5]],[False,5,[4]]]),
        (2,[],9,True,[True,9,[]],[[True,9,[]],[True,None,[9]],[False,None,[]],[True,None,[]]]),
        (1,[4],9,True,[False,4,[]],[[False,4,[]],[True,4,[9]],[True,9,[]],[False,None,[4]]]),
        (2,[],None,True,[False,None,[]],[[False,None,[]],[True,None,[]],[False,0,[]],[False,None,[0]]]),
        (3,[4],9,False,[True,None,[4,9]],[[True,None,[4,9]],[True,4,[9]],[False,None,[4]],[True,None,[9,4]]]),
    ]:
        emit(350,"queue_call",dict(capacity=capacity,queue=queue,write=write,read=read),
             f"תור FIFO ישן־ראשון {label(queue)}, קיבולת {capacity}. בקשת כתיבה {label(write)} (None משמע אין), בקשת קריאה {label(read)}. מבצעים כתיבה לפני קריאה; מלא דוחה כתיבה וריק מחזיר None. מה [הכתיבה התקבלה,הנקרא,התור שנותר]?",
             f"Oldest-first FIFO {label(queue)}, capacity {capacity}. Write request {label(write)} (None means absent), read request {label(read)}. Process write before read; full rejects writes and empty reads return None. What is [write accepted,read value,remaining queue]?",options,expected,
             "בודקים מקום לפני הכתיבה ורק אחר כך בודקים קריאה. בקשה חסרה אינה מתקבלת, והוצאת ערך שומרת סדר FIFO.",
             "Check space before writing, then process the read. An absent write is not accepted, and removal preserves FIFO order.",3)
    assert len(rows) == len(checks) == 150
    assert all(sum(r["source_key"] == c for r in rows) == 5 for c in cards)
    return rows, checks


if __name__ == "__main__":
    questions, evidence = build()
    for path, value in [(CARD_PATH, build_cards()), (OUT / "code_700.json", questions), (OUT / "code_700.checks.json", evidence)]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote 30 original cards, 150 draft variants, and 150 oracle specifications.")
