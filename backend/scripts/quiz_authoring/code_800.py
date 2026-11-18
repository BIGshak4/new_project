"""Build 15 bilingual algorithm drills, their game variants and worked checks."""

from __future__ import annotations

import hashlib
import json
from itertools import permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BATCHES = ROOT / "backend/seeds/duel_quiz_batches"


def localized(he, en):
    return {"he": he, "en": en}


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def build_content():
    cards, games, checks = [], [], []

    def lesson(number, prep, title, prompt, answer, takeaway, *, code=None, difficulty=3):
        card = {
            "id": f"quick-sw-{number}",
            "topic": "python" if code else "algorithms",
            "interviewIds": [f"PREP-{prep:03}"],
            "title": localized(*title),
            "prompt": localized(*prompt),
            "answer": localized(*answer),
            "takeaway": localized(*takeaway),
        }
        if code:
            card["code"] = {"language": "python", "text": code}
        cards.append(card)
        return card, difficulty

    def case(lesson_info, inputs, prompt, solution, calculated, options):
        card, difficulty = lesson_info
        variant = len(games) % 5 + 1
        expected, *others = options
        assert calculated == expected and len(set(options)) == 4, (card["id"], inputs, calculated, options)
        correct = (len(games) + variant // 3) % 4
        choices = others[:correct] + [expected] + others[correct:]
        key = f"{card['id']}-v{variant}"
        games.append(
            {
                "key": key,
                "source_key": card["id"],
                "variant": variant,
                "topic": card["topic"],
                "status": "draft",
                "prompt": localized(*prompt),
                "correct": correct,
                "choices": [localized(str(value), str(value)) for value in choices],
                "explanation": localized(*solution),
            }
        )
        checks.append(
            {
                "key": key,
                "task": card["id"],
                "inputs": inputs,
                "expected": expected,
                "options": choices,
                "method": "Evaluate the concrete case in scripts/quiz_authoring/code_800.py and compare with the authored answer.",
                "difficulty": difficulty,
                "difficulty_rationale": solution[1],
                "source_difficulty": difficulty,
                "source_difficulty_rationale": card["takeaway"]["en"],
                "source_content_sha256": hashlib.sha256(compact(card).encode()).hexdigest(),
                "provenance": {
                    "interview_ids": card["interviewIds"],
                    "authorship": "original AI-assisted practice",
                    "professional_review": "pending",
                    "calibration": "editorial estimate",
                },
            }
        )

    clone = lesson(
        386,
        371,
        ("אותו יעד אחרי העתקה עמוקה", "Following a shared target after cloning"),
        (
            "לשתי חוליות יש אותו ערך, ושתיהן מצביעות בשדה random לחוליה שלישית. כמה חוליות חדשות צריך ליצור, ולאן יפנו שני המצביעים בעותק?",
            "Two nodes have the same value and both random pointers lead to a third node. How many new nodes are needed, and where do the copied pointers lead?",
        ),
        (
            "יוצרים שלוש חוליות. כל מצביע בעותק פונה לעותק של החוליה השלישית. מיפוי לפי ערך היה מאחד בטעות את שתי החוליות הראשונות.",
            "Create three nodes. Both copied pointers reference the clone of the third node. A map keyed by value would mistakenly merge the first two nodes.",
        ),
        (
            "מעתיקים לפי זהות החוליה ושומרים על שיתוף היעדים.",
            "Clone by node identity to preserve shared targets.",
        ),
    )
    for targets, start, steps, options in [
        ([2, 2, 1], 0, 2, [1, 0, 2, -1]),
        ([0, 0], 0, 3, [0, 1, 3, -1]),
        ([2, 2, -1], 1, 2, [-1, 0, 1, 2]),
        ([1, 2, 0], 0, 4, [1, 2, 0, 4]),
        ([2, -1, 0], 1, 0, [1, -1, 2, 0]),
    ]:
        node = start
        trace = [node]
        for _ in range(steps):
            node = targets[node] if node != -1 else -1
            trace.append(node)
        path = " → ".join(map(str, trace))
        case(
            clone,
            [targets, start, steps],
            (
                f"אחרי שכפול, העותקים ממוספרים מאפס לפי סדר המקור. יעדי random לפי אינדקס הם {compact(targets)}. מתחילים בהעתק {start} ועוקבים אחר {steps} קישורים. מה אינדקס היעד? ‎-1 מסמן קישור ריק ונשאר ריק.",
                f"Clones are numbered from zero in original order. Their random targets by index are {compact(targets)}. Start at clone {start} and follow {steps} links. What index results? A null link is -1 and stays null.",
            ),
            (
                f"המסלול בעותק הוא {path}. כל צעד קורא את היעד של החוליה הנוכחית.",
                f"The cloned path is {path}. Each step reads the current node's target.",
            ),
            node,
            options,
        )

    bst = lesson(
        387,
        373,
        ("האב הראשון שמגיעים אליו משמאל", "The first ancestor reached from the left"),
        (
            "בעץ חיפוש, 20 הוא השורש, 8 בנו השמאלי ו־15 בנו הימני של 8. ל־15 אין ילדים. מי בא אחרי 15 בסדר עולה, ואיך מגיעים אליו באמצעות קישורי האב?",
            "In a search tree, 20 is the root, 8 its left child and 15 the right child of 8. Node 15 is a leaf. Which key follows 15 in ascending order, and how do parent pointers lead there?",
        ),
        (
            "עולים מ־15 אל 8 דרך קישור של בן ימני וממשיכים. מ־8 עולים אל 20 דרך קישור של בן שמאלי. 20 הוא היורש.",
            "Climb from 15 to 8 through a right-child link and continue. From 8 the climb reaches 20 through a left-child link. The successor is 20.",
        ),
        (
            "בלי תת־עץ ימני, היורש הוא האב הקדמון הראשון שעולים אליו משמאל.",
            "Without a right subtree, the successor is the first ancestor reached from its left child.",
        ),
    )
    for order, key, options in [
        ([9, 4, 7, 6], 7, [9, 6, 4, -1]),
        ([8, 12, 10, 9], 8, [9, 10, 12, -1]),
        ([4, 1, 6], 6, [-1, 4, 1, 6]),
        ([3], 3, [-1, 0, 3, 1]),
        ([10, 5, 12, 3], 3, [5, 10, 12, -1]),
    ]:
        larger = [v for v in sorted(order) if v > key]
        result = min(larger, default=-1)
        case(
            bst,
            [order, key],
            (
                f"מכניסים לעץ חיפוש ריק, לפי הסדר, את {compact(order)}. מה המפתח שיופיע מיד אחרי {key} בסריקה לפי סדר עולה? החזירו ‎-1 אם זה המפתח האחרון.",
                f"Insert {compact(order)} into an empty search tree in that order. Which key comes immediately after {key} during inorder traversal? Return -1 for the last key.",
            ),
            (
                f"סדר הביקור הוא {compact(sorted(order))}. מחפשים את המפתח הבא אחרי {key}, ולכן התוצאה היא {result}.",
                f"The traversal order is {compact(sorted(order))}. Looking just past {key} gives {result}.",
            ),
            result,
            options,
        )

    rand = lesson(
        388,
        372,
        ("הגרלה לפי מיקום בין הערכים המותרים", "Drawing a rank among eligible values"),
        (
            "מגרילים מתוך 10 עד 16 כולל. חמש התוצאות האחרונות היו 12, 16, 11, 15 ו־10. כיצד הגרלה אחת של ביט הוגן מספיקה לבחירת התוצאה הבאה?",
            "Draw from 10 through 16 inclusive. The last five results were 12, 16, 11, 15 and 10. How can one fair bit select the next result?",
        ),
        (
            "הערכים המותרים הם 13 ו־14. ממפים 0 ל־13 ו־1 ל־14. לכל ערך יש בדיוק תוצאת ביט אחת שמובילה אליו, ולכן ההסתברויות שוות.",
            "The eligible values are 13 and 14. Map 0 to 13 and 1 to 14. Each value has exactly one bit outcome leading to it, so their probabilities are equal.",
        ),
        (
            "הגרלה אחידה של מיקום ומיפוי חד־חד־ערכי שומרים על אחידות.",
            "A uniform rank and a one-to-one mapping give a uniform value.",
        ),
    )
    for lo, hi, history, rank, options in [
        (1, 7, [2, 5], 2, [4, 3, 5, 6]),
        (5, 10, [7, 9, 5, 10, 6], 0, [8, 5, 7, 9]),
        (2, 8, [], 6, [8, 6, 7, 2]),
        (0, 7, [4, 1, 5, 2, 6, 3], 1, [4, 0, 1, 7]),
        (8, 14, [14, 13, 12, 11, 10], 1, [9, 8, 10, 14]),
    ]:
        eligible = [v for v in range(lo, hi + 1) if v not in history[-5:]]
        case(
            rand,
            [lo, hi, history, rank],
            (
                f"בתחום {lo}..{hi} כולל, היסטוריית ההגרלות מהישנה לחדשה היא {compact(history)}. מסירים את חמש התוצאות האחרונות או את כולן אם היו פחות. איזה ערך נמצא באינדקס {rank} ברשימת המותרים הממוינת מאפס?",
                f"In inclusive range {lo}..{hi}, history from oldest to newest is {compact(history)}. Exclude the last five draws, or all draws so far if fewer. Which eligible value has zero-based index {rank} in sorted order?",
            ),
            (
                f"לאחר הסרת חלון ההיסטוריה מתקבלת הרשימה {compact(eligible)}. קוראים ממנה את האיבר באינדקס {rank}.",
                f"Removing the history window leaves {compact(eligible)}. Read the entry at index {rank}.",
            ),
            eligible[rank],
            options,
        )

    move = lesson(
        389,
        332,
        ("קריאה מטווח שעומד להידרס", "Reading a range before it is overwritten"),
        (
            "במערך [4,7,9,2], מעתיקים את שלושת התאים הראשונים אל התאים שמתחילים באינדקס 1. איך מתקבל [4,4,7,9] בלי מערך עזר?",
            "In [4,7,9,2], copy the first three cells into the range starting at index 1. How can you produce [4,4,7,9] without a temporary array?",
        ),
        (
            "מעתיקים מהסוף להתחלה. כותבים תחילה 9 בתא האחרון, אחר כך 7 ואחריו 4. כך כל ערך נקרא לפני שהכתיבה ליעד יכולה לשנות אותו.",
            "Copy backward. Write 9 into the last cell, then 7 and finally 4. Each source value is read before a destination write can overwrite it.",
        ),
        ("כיוון ההעתקה נקבע לפי מיקום החפיפה.", "The direction of copying depends on the overlap."),
    )
    for values, src, dst, count, idx, options in [
        ([4, 7, 9, 2], 0, 1, 3, 3, [9, 4, 2, 7]),
        ([3, 8, 4, 6], 1, 0, 3, 1, [4, 8, 6, 3]),
        ([9, 2, 7], 0, 2, 0, 2, [7, 9, 2, 0]),
        ([1, 5, 8, 2], 1, 1, 2, 2, [8, 5, 1, 2]),
        ([7, 9, 3, 2, 5], 0, 3, 2, 4, [9, 5, 7, 2]),
    ]:
        saved = values[src : src + count]
        after = values.copy()
        after[dst : dst + count] = saved
        case(
            move,
            [values, src, dst, count, idx],
            (
                f"המערך הוא {compact(values)} והאינדקסים מתחילים באפס. מעתיקים {count} ערכים מאינדקס {src} לאינדקס {dst} לפי ערכי המקור שלפני ההעתקה. איזה ערך יישב באינדקס {idx}?",
                f"Array {compact(values)} is indexed from zero. Copy {count} cells from index {src} to index {dst}, using the original source values. What value ends up at index {idx}?",
            ),
            (
                f"הערכים המועתקים הם {compact(saved)}. לאחר הכתיבה המערך הוא {compact(after)}.",
                f"The copied values are {compact(saved)}. After the writes the array is {compact(after)}.",
            ),
            after[idx],
            options,
        )

    grid = lesson(
        390,
        359,
        ("כשל שנמצא בין נקודות הדגימה", "A failure between sampling points"),
        (
            "בודקים מתח מ־0 עד 1 וולט בצעדים של 0.2, בלי נקודות הקצה. המדידה נכשלת ב־0.3 וב־0.8 בלבד. מהו הכשל הראשון שיתגלה?",
            "Test voltages between 0 and 1 volt in steps of 0.2, excluding both endpoints. A measurement fails only at 0.3 and 0.8. Which failure is observed first?",
        ),
        (
            "נקודות המדידה הן 0.2, 0.4, 0.6 ו־0.8. הכשל הראשון שנמדד הוא ב־0.8. אפשר לייצג את המתחים כעשיריות שלמות כדי להימנע משגיאת עיגול.",
            "The samples are 0.2, 0.4, 0.6 and 0.8. The first observed failure is at 0.8. Integer tenths represent this grid exactly.",
        ),
        ("מחפשים את הכשל הראשון שנדגם על הרשת.", "Find the first failure actually sampled on the grid."),
    )
    for start, stop, step, failed, options in [
        (0, 10, 3, [2, 6, 9], [6, 2, 3, 9]),
        (2, 12, 2, [2, 12], [-1, 2, 12, 10]),
        (0, 9, 2, [8, 2], [2, 8, 0, -1]),
        (5, 7, 4, [6], [-1, 5, 6, 7]),
        (1, 11, 3, [7], [7, 4, 10, -1]),
    ]:
        sampled = list(range(start + step, stop, step))
        result = next((v for v in sampled if v in failed), -1)
        case(
            grid,
            [start, stop, step, failed],
            (
                f"ביחידות mV, עוברים מ־{start} עד {stop} בצעד {step}, בלי לבדוק את שני הקצוות. המתחים הכושלים הם {compact(failed)}. מהו מתח הכשל הראשון שנמדד? החזירו ‎-1 אם לא נמדד כשל.",
                f"In mV, sweep from {start} to {stop} with step {step}, excluding both endpoints. Failing voltages are {compact(failed)}. Which failing voltage is measured first? Return -1 if none is measured.",
            ),
            (
                f"נקודות הרשת לפי סדר המדידה הן {compact(sampled)}. השוואה לרשימת הכשלים נותנת {result}.",
                f"The grid points in measurement order are {compact(sampled)}. Checking them against the failures gives {result}.",
            ),
            result,
            options,
        )

    distance = lesson(
        391,
        362,
        ("השכן הקרוב משני צדי נקודת ההכנסה", "Both neighbors of an insertion point"),
        (
            "מחפשים ל־13 את הערך הקרוב ביותר במערך הממוין [2,9,21,40]. חיפוש מחזיר את אינדקס 21, הערך הראשון שגדול מ־13. איזה ערך עוד צריך לבדוק?",
            "Find the value closest to 13 in sorted array [2,9,21,40]. A search locates 21, the first value above 13. Which other value should you check?",
        ),
        (
            "בודקים גם את 9, האיבר שמשמאל לנקודת ההכנסה. המרחקים הם 4 ו־8 ולכן 9 קרוב יותר. בקצה המערך ייתכן שקיים רק אחד משני השכנים.",
            "Check 9, immediately to the left of the insertion point. The distances are 4 and 8, so 9 is closer. At an array boundary only one neighbor may exist.",
        ),
        (
            "במערך ממוין הערך הקרוב הוא אחד השכנים של נקודת ההכנסה.",
            "In sorted order, a closest value is adjacent to the insertion point.",
        ),
    )
    for left, right, options in [
        ([1, 8], [3, 11], [2, 3, 5, 7]),
        ([4, 4], [4, 9], [0, 1, 4, 5]),
        ([-8, -1], [2, 12], [3, 1, 7, 10]),
        ([15], [1, 7], [8, 14, 6, 7]),
        ([17, 2, 30], [10, 28], [2, 7, 8, 13]),
    ]:
        pairs = [(abs(a - b), a, b) for a in left for b in right]
        result, a, b = min(pairs)
        case(
            distance,
            [left, right],
            (
                f"המערכים הם {compact(left)} ו־{compact(right)}. בוחרים ערך אחד מכל מערך. מהו ההפרש המוחלט הקטן ביותר שאפשר לקבל?",
                f"Arrays are {compact(left)} and {compact(right)}. Choose one value from each array. What is the smallest attainable absolute difference?",
            ),
            (
                f"אחרי שממיינים ומשווים שכנים ממערכים שונים, זוג קרוב ביותר הוא {a} ו־{b}. ההפרש המוחלט שלו הוא {result}.",
                f"Sorting and comparing neighbors from different arrays gives a closest pair of {a} and {b}. Its absolute difference is {result}.",
            ),
            result,
            options,
        )

    slots = lesson(
        392,
        333,
        ("כמה מקומות פנויים נשארו בעץ?", "Counting open slots in a tree encoding"),
        (
            "מתארים עץ בינארי בסדר תחילי. אות מסמנת צומת ו־# מסמן ילד חסר. נקראו האסימונים A B # #. כמה מקומות לילדים או לסמנים חסרים עדיין מחכים למילוי?",
            "A preorder binary-tree encoding uses letters for nodes and # for null children. The tokens A B # # have been read. How many slots still need a node or a null marker?",
        ),
        (
            "נשאר מקום אחד, לילד הימני של A. מתחילים במקום אחד לשורש. כל צומת תופס מקום ופותח שניים, וכל # סוגר מקום אחד.",
            "One slot remains, for the right child of A. Start with one root slot. A node consumes one slot and creates two, while each # closes one slot.",
        ),
        (
            "ספירת מקומות פתוחים מאפשרת לזהות מתי תיאור העץ הושלם.",
            "The open-slot count tells you when the tree encoding is complete.",
        ),
    )
    for tokens, options in [
        ("A B # #", [1, 0, 2, 3]),
        ("#", [0, 1, 2, -1]),
        ("A B C", [4, 3, 6, 1]),
        ("A # B # #", [0, 1, 2, 3]),
        ("A A #", [2, 1, 0, 3]),
    ]:
        nodes = sum(t != "#" for t in tokens.split())
        nulls = tokens.split().count("#")
        result = 1 + nodes - nulls
        case(
            slots,
            tokens,
            (
                f"בתיאור עץ בינארי בסדר תחילי, כל אות יוצרת צומת עם שני מקומות לילדים וכל # מציין מקום ריק. כמה מקומות נותרו פתוחים אחרי קריאת הרצף {tokens}?",
                f"In a preorder binary-tree encoding each letter creates a node with two child slots and # marks a null slot. How many slots are open after reading {tokens}?",
            ),
            (
                f"מתחילים במקום אחד. {nodes} צמתים מוסיפים מקום נטו כל אחד, ו־{nulls} סמנים ריקים סוגרים מקום כל אחד. נותרו {result}.",
                f"Start with one slot. Each of the {nodes} nodes adds one net slot, and each of the {nulls} null markers closes one. That leaves {result}.",
            ),
            result,
            options,
        )

    postfix = lesson(
        393,
        123,
        ("מי נמצא מימין לסימן החיסור?", "Which operand goes on the right?"),
        (
            "מחשבים את הביטוי בסימון סופי 8 3 2 * -. כשמגיעים לחיסור, מה שולפים קודם, ומהי התוצאה?",
            "Evaluate the postfix expression 8 3 2 * -. When you reach subtraction, which value do you pop first and what is the result?",
        ),
        (
            "שולפים תחילה 6, תוצאת הכפל, ואז 8. הערך הראשון שנשלף הוא האופרנד הימני. לכן מחשבים 8 פחות 6 ומקבלים 2.",
            "Pop 6, the product, then 8. The first pop is the right operand. Compute 8 minus 6 to get 2.",
        ),
        (
            "בחיסור ובחילוק צריך לשמור על סדר האופרנדים.",
            "Subtraction and division require the original operand order.",
        ),
    )
    for expression, options in [
        ("7 2 - 3 *", [15, 1, -15, 13]),
        ("9 6 2 / -", [6, -6, 1, 3]),
        ("2 7 - 3 +", [-2, 2, -8, 8]),
        ("12 3 / 2 /", [2, 8, 6, 4]),
        ("4 4 - 5 *", [0, 5, 20, -5]),
    ]:
        stack, workings = [], []
        for token in expression.split():
            if token.isdecimal():
                stack.append(int(token))
            else:
                rhs, lhs = stack.pop(), stack.pop()
                if token == "/":
                    assert rhs and lhs % rhs == 0
                    value = lhs // rhs
                else:
                    value = {"+": lhs + rhs, "-": lhs - rhs, "*": lhs * rhs}[token]
                workings.append(f"({lhs} {token} {rhs}) = {value}")
                stack.append(value)
        trace = ", ".join(workings)
        case(
            postfix,
            expression,
            (
                f"מה ערכו של הביטוי בסימון סופי {expression}? כל מספר הוא אסימון שלם וכל חילוק בביטוי מדויק.",
                f"What is the value of the postfix expression {expression}? Each number is one token and any division in the expression is exact.",
            ),
            (
                f"בכל פעולה שולפים קודם את האופרנד הימני. לפי סדר הפעולות מתקבל {trace}.",
                f"Pop the right operand first for each operator. The operations are {trace}.",
            ),
            stack[0],
            options,
        )

    perm = lesson(
        394,
        162,
        ("מקבעים את האות הראשונה בתמורה", "Fixing the first letter of a permutation"),
        (
            "מהמילה ABBA יוצרים את כל הסידורים השונים שמתחילים ב־A. כמה כאלה יש?",
            "How many distinct arrangements of ABBA start with A?",
        ),
        (
            "אחרי שמקבעים A נשארות האותיות A,B,B. יש שלוש אפשרויות למיקום A הנותרת. החלפה בין שני עותקי B לא יוצרת מילה נוספת.",
            "Fixing A leaves A,B,B. There are three positions for the remaining A. Swapping the two copies of B produces the same word.",
        ),
        (
            "בכל ענף רקורסיבי מעדכנים את השכיחויות אחרי בחירת האות.",
            "Each recursive branch uses the frequencies left after its letter choice.",
        ),
    )
    for word, prefix, options in [
        ("ABBA", "B", [3, 2, 6, 4]),
        ("ABCD", "AB", [2, 4, 6, 12]),
        ("AAAA", "AA", [1, 2, 4, 6]),
        ("AABC", "BB", [0, 1, 2, 3]),
        ("ABC", "ABC", [1, 0, 3, 6]),
    ]:
        matches = sorted({"".join(p) for p in permutations(word) if "".join(p).startswith(prefix)})
        proof = ", ".join(matches) or "∅"
        case(
            perm,
            [word, prefix],
            (
                f"כמה סידורים שונים של כל אותיות {word} מתחילים בקידומת {prefix}? עותקים של אותה אות נחשבים זהים.",
                f"How many distinct arrangements of all letters of {word} start with prefix {prefix}? Copies of the same letter are indistinguishable.",
            ),
            (
                f"מקבעים את הקידומת ומסדרים רק את האותיות שנותרו. קבוצת התוצאות היא {proof}.",
                f"Fix the prefix and arrange only the remaining letters. The resulting set is {proof}.",
            ),
            len(matches),
            options,
        )

    barrier = lesson(
        395,
        337,
        ("השכמה לפני שהחוט השני הגיע", "Waking before the other thread arrives"),
        (
            "חוט ממתין במחסום לשני חוטים וזוכר את מספר הסבב 6. הוא מתעורר ומגלה תחת המנעול שהסבב עדיין 6. האם הוא רשאי לצאת מהמחסום?",
            "A thread at a two-thread barrier saved generation 6. It wakes and reads generation 6 while holding the lock. May it leave the barrier?",
        ),
        (
            "עליו להמשיך להמתין. השכמה לבדה אינה מעידה שהחוט השני הגיע. החוט האחרון שמגיע מקדם את מספר הסבב תחת המנעול ומעיר את הממתין. שינוי המספר מעיד שהסבב המקורי הסתיים.",
            "It must keep waiting. A wakeup alone does not establish that the other thread arrived. The last arriving thread advances the generation under the lock and wakes the waiter. A changed generation marks completion of the original round.",
        ),
        (
            "אחרי השכמה בודקים שוב את תנאי ההמתנה תחת אותו מנעול.",
            "After a wakeup, recheck the waiting predicate under the same lock.",
        ),
        difficulty=3,
    )
    for saved, observations, options in [
        (5, [5, 5, 6], [2, 0, 1, -1]),
        (3, [4], [0, 1, 3, 4]),
        (0, [0, 0], [-1, 0, 1, 2]),
        (9, [], [-1, 0, 9, 1]),
        (12, [12, 13], [1, 0, 12, 13]),
    ]:
        result = next((i for i, value in enumerate(observations) if value != saved), -1)
        if result == -1:
            proof = (
                "באף בדיקה לא נצפה שינוי במספר הסבב, ולכן אין עדיין אישור להמשיך.",
                "No observation shows a changed generation, so the thread has no evidence yet that it may continue.",
            )
        else:
            proof = (
                f"באינדקס {result} נקרא הסבב {observations[result]}. זו הקריאה הראשונה ששונה מהסבב השמור {saved}.",
                f"Index {result} reads generation {observations[result]}, the first reading different from the saved generation {saved}.",
            )
        case(
            barrier,
            [saved, observations],
            (
                f"במחסום רב־פעמי חוט זוכר שהגיע בסבב {saved}. קריאות מספר הסבב תחת המנעול הן {compact(observations)}. מה האינדקס הראשון שבו מותר לחוט להמשיך? האינדקסים מתחילים באפס. החזירו ‎-1 אם טרם נצפה שינוי.",
                f"At a reusable barrier a thread saved generation {saved} on arrival. Its readings under the lock are {compact(observations)}. At what zero-based index may it first continue? Return -1 if it has yet to observe a change.",
            ),
            proof,
            result,
            options,
        )

    stack_lesson = lesson(
        396,
        309,
        ("מתי ערך ישן מפסיק להיות במחסנית?", "When is a stale value outside the stack?"),
        (
            "מחסנית משתמשת במערך [4,8,6,0] ובמונה גודל 2. חיפוש בכל המערך מוצא 6. האם 6 אכן במחסנית?",
            "A stack uses backing array [4,8,6,0] and size 2. Searching the whole array finds 6. Is 6 in the stack?",
        ),
        (
            "לא. שני התאים הפעילים הם 4 ו־8. תא שהוסר באמצעות הקטנת המונה יכול עדיין להכיל ערך ישן, ותא שלא נכתב עשוי להכיל ערך אתחול.",
            "No. The active entries are 4 and 8. Popping by reducing the size can leave an old value behind, and unused cells can contain default values.",
        ),
        ("סורקים רק את הטווח הפעיל של המבנה.", "Search only the data structure's active range."),
        code="def occurrences(buffer, size, key):\n    return sum(buffer[i] == key for i in range(size))",
        difficulty=2,
    )
    for buf, size, key, options in [
        ([0, 0, 0], 0, 0, [0, 1, 2, 3]),
        ([2, 2, 1, 2], 2, 2, [2, 3, 1, 0]),
        ([1, 3, 3], 1, 3, [0, 1, 2, 3]),
        ([5, 1, 5, 5], 4, 5, [3, 1, 2, 4]),
        ([2, 0, 9, 0], 3, 0, [1, 2, 0, 3]),
    ]:
        active = buf[:size]
        case(
            stack_lesson,
            [buf, size, key],
            (
                f"במערך האחסון של מחסנית מופיעים {compact(buf)} וגודלה הפעיל {size}. האיברים הפעילים מתחילים באינדקס אפס. כמה עותקים של {key} נמצאים במחסנית?",
                f"A stack's backing array is {compact(buf)} and its active size is {size}. Active entries start at index zero. How many occurrences of {key} are in the stack?",
            ),
            (
                f"סורקים את התחילית הפעילה {compact(active)} וסופרים רק את ההתאמות בתוכה.",
                f"Scan the active prefix {compact(active)} and count matches only inside it.",
            ),
            active.count(key),
            options,
        )

    span = lesson(
        397,
        353,
        ("כמה נקודות דגימה נכנסות בשורה?", "How many sampling points fit in a row?"),
        (
            "רוחב תמונה הוא 10 פיקסלים. מתחילים בעמודה 2 ודוגמים כל 4 עמודות. כמה נקודות נכנסות בשורה אם העמודה הראשונה היא 0?",
            "An image is 10 pixels wide. Start at column 2 and sample every 4 columns. How many points fit if columns start at 0?",
        ),
        (
            "שתי נקודות, בעמודות 2 ו־6. העמודה הבאה הייתה 10, אבל האינדקס האחרון בתמונה הוא 9.",
            "Two points fit, at columns 2 and 6. The next column would be 10, but the final image index is 9.",
        ),
        (
            "הנקודה האחרונה חייבת להיות באינדקס שקטן מרוחב התמונה.",
            "The last point must have an index strictly below the image width.",
        ),
        code="def count_columns(width, start, step):\n    return len(range(start, width, step))",
        difficulty=2,
    )
    for width, start, step, options in [
        (10, 1, 4, [3, 2, 4, 1]),
        (9, 1, 4, [2, 3, 1, 4]),
        (4, 3, 6, [1, 0, 2, 4]),
        (5, 5, 1, [0, 1, 4, 5]),
        (8, 0, 1, [8, 7, 9, 1]),
    ]:
        points = list(range(start, width, step))
        case(
            span,
            [width, start, step],
            (
                f"בשורת תמונה ברוחב {width}, העמודות ממוספרות מאפס. מתחילים בעמודה {start} ומתקדמים בצעד {step}. כמה נקודות דגימה נמצאות בשורה?",
                f"In a row of width {width}, columns start at zero. Sampling starts at column {start} and advances by {step}. How many sample points lie inside the row?",
            ),
            (
                f"העמודות הנדגמות בתוך התמונה הן {compact(points)}. עוצרים לפני עמודה {width}.",
                f"The sampled columns inside the image are {compact(points)}. Stop before column {width}.",
            ),
            len(points),
            options,
        )

    stars = lesson(
        398,
        347,
        ("כמה כוכבים יודפסו בפירמידה?", "Counting the stars printed in a pyramid"),
        (
            "בשורות של פירמידה ממורכזת יש 1, 3, 5 ו־7 כוכבים. כמה כוכבים יודפסו בסך הכול, ואיך מנבאים את הכמות לפי גובה הפירמידה?",
            "A centered pyramid prints rows of 1, 3, 5 and 7 stars. How many stars are printed in total, and how do you predict the count from its height?",
        ),
        (
            "יודפסו 16 כוכבים. אם יש h שורות, כל שורה מוסיפה את המספר האי־זוגי הבא. סכום h המספרים האי־זוגיים הראשונים הוא h בריבוע.",
            "There are 16 stars. With h rows, each row adds the next odd number. The sum of the first h odd numbers is h squared.",
        ),
        (
            "כמות התווים בפלט עשויה לגדול כריבוע מספר השורות.",
            "Output length can grow quadratically with the number of rows.",
        ),
        difficulty=2,
    )
    for base, skip, options in [
        (1, 0, [1, 0, 2, 3]),
        (5, 0, [9, 5, 6, 15]),
        (7, 2, [12, 10, 16, 9]),
        (9, 4, [9, 25, 16, 5]),
        (3, 2, [0, 2, 3, 4]),
    ]:
        widths = list(range(1, base + 1, 2))[skip:]
        case(
            stars,
            [base, skip],
            (
                f"רוחב הבסיס של פירמידת כוכבים הוא {base}. רוחבי השורות מלמעלה הם האי־זוגיים העוקבים שמתחילים ב־1. מדלגים על {skip} שורות ראשונות. כמה כוכבים מודפסים בפועל?",
                f"A star pyramid has base width {base}. Its row widths are consecutive odd numbers starting at 1. Skip the first {skip} rows. How many stars are actually printed?",
            ),
            (
                f"רוחבי השורות שמודפסות הם {compact(widths)}. סכומם הוא {sum(widths)}.",
                f"The printed row widths are {compact(widths)}. Their sum is {sum(widths)}.",
            ),
            sum(widths),
            options,
        )

    words = lesson(
        399,
        314,
        ("מילה אחת שמגיעה בשני מקטעים", "One word received in two chunks"),
        (
            "הטקסט מגיע בשני מקטעים, “a ca” ואחריו “t catfish”. המילה האסורה היא cat ונדרשת התאמה למילה שלמה. כמה התאמות יש?",
            "Text arrives in two chunks, “a ca” followed by “t catfish”. The forbidden word is cat and only full tokens count. How many matches are there?",
        ),
        (
            "יש התאמה אחת. הסיומת ca והתו t משלימים יחד את cat. המילה catfish היא אסימון אחר. שומרים את המילה החלקית עד רווח או סוף הזרם.",
            "There is one match. The suffix ca and the next t form cat. The word catfish is a different token. Keep the partial token until whitespace or end of input.",
        ),
        ("גבול מקטע שידור אינו בהכרח גבול מילה.", "A chunk boundary need not be a word boundary."),
    )
    for chunks, word, options in [
        (["re", "d red"], "red", [2, 1, 0, 3]),
        ([" cat", "alog cat"], "cat", [1, 2, 0, 3]),
        (["UP low up", "! Up"], "up", [0, 1, 2, 3]),
        (["to ", "to", " to"], "to", [3, 2, 1, 0]),
        (["no", " ", "no", "w"], "no", [1, 0, 2, 3]),
    ]:
        tokens = "".join(chunks).split()
        case(
            words,
            [chunks, word],
            (
                f"מקטעי הטקסט {compact(chunks)} מגיעים לפי הסדר. מחברים אותם בלי להוסיף תו ומפצלים למילים לפי רווחים. כמה מילים שוות בדיוק ל־{word}? גודל האות וסימני הפיסוק נשמרים.",
                f"Receive text chunks {compact(chunks)} in order. Concatenate them without adding characters, then split on whitespace. How many whole tokens equal {word}? Case and punctuation are significant.",
            ),
            (
                f"אחרי החיבור מתקבל רצף המילים {compact(tokens)}. סופרים רק התאמות מלאות למילה {word}.",
                f"After concatenation the tokens are {compact(tokens)}. Count only complete matches for {word}.",
            ),
            tokens.count(word),
            options,
        )

    transpose = lesson(
        400,
        318,
        ("מתי שחלוף משנה את ערכי התאים?", "Which swaps change a matrix during transposition?"),
        (
            "משחלפים במקום את המטריצה [[1,4,5],[4,2,8],[7,8,3]]. בכמה זוגות תאים ההחלפה תשנה את הערכים?",
            "Transpose [[1,4,5],[4,2,8],[7,8,3]] in place. For how many pairs does swapping actually change the cell values?",
        ),
        (
            "רק בזוג שבפינות הימנית העליונה והשמאלית התחתונה, שבו הערכים 5 ו־7. בשני הזוגות האחרים שמעבר לאלכסון הערכים שווים. תאי האלכסון נשארים במקומם.",
            "Only the top-right and bottom-left pair changes, with values 5 and 7. The other two off-diagonal pairs have matching values. The diagonal stays in place.",
        ),
        (
            "עוברים פעם אחת על כל זוג סימטרי באמצעות התנאי i<j.",
            "Visit each symmetric pair once by requiring i<j.",
        ),
    )
    for matrix, options in [
        ([[1]], [0, 1, 2, 3]),
        ([[1, 4], [3, 1]], [1, 2, 0, 4]),
        ([[1, 2], [2, 3]], [0, 1, 2, 4]),
        ([[1, 2, 3], [7, 4, 5], [8, 9, 6]], [3, 6, 2, 9]),
        ([[0, 1, 2], [1, 0, 3], [4, 5, 0]], [2, 4, 3, 1]),
    ]:
        pairs = [
            [i, j] for i, row in enumerate(matrix) for j in range(i + 1, len(row)) if row[j] != matrix[j][i]
        ]
        case(
            transpose,
            matrix,
            (
                f"משחלפים את המטריצה {compact(matrix)} סביב האלכסון הראשי. כמה זוגות סימטריים מחוץ לאלכסון מכילים ערכים שונים ולכן משנים את תוכנם בהחלפה? כל זוג נספר פעם אחת.",
                f"Transpose {compact(matrix)} across its main diagonal. How many off-diagonal symmetric pairs have unequal values, so swapping changes their contents? Count each pair once.",
            ),
            (
                f"באינדקסים מאפס, המיקומים מעל האלכסון ששונים מהתא המשתקף הם {compact(pairs)}.",
                f"With zero-based indices, the positions above the diagonal that differ from their reflections are {compact(pairs)}.",
            ),
            len(pairs),
            options,
        )

    return cards, games, checks


def build():
    _, games, checks = build_content()
    return games, checks


if __name__ == "__main__":
    cards, games, checks = build_content()
    for path, data in [
        (ROOT / "apps/web/src/content/fundamentals-code-800.json", cards),
        (BATCHES / "code_800.json", games),
        (BATCHES / "code_800.checks.json", checks),
    ]:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
