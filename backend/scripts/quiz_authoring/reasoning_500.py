"""35 interview-linked reasoning cards and 175 bilingual, draft MCQ cases.

Only the new 500-expansion files are written. No publication approval is granted.
Independent finite-world checks live in test_fundamentals_reasoning_500.py.
"""

from __future__ import annotations

import itertools
import json
import math
from collections import deque
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "apps/web/src/content/fundamentals-reasoning-500.json"
OUT = ROOT / "backend/seeds/duel_quiz_batches"


def pair(he, en=None):
    return {"he": str(he), "en": str(he if en is None else en)}


def alternatives(value, task):
    value = F(value)
    probabilities = {"nested_joint", "nested_cdf", "right_neighbor", "overlapping_neighbors",
                     "unseen_target", "majority_error", "sample_miss", "all_visited", "urn_optimum"}
    candidates = (
        [F(0), F(1), F(1, 2), F(1, 3), F(2, 3), F(1, 4), F(3, 4), F(1, 5)]
        if task in probabilities
        else [F(1), F(3), F(5)] if value < 0
        else [value + 1, max(value - 1, 0), value + 2, value * 2, F(0), value + 3]
    )
    return [str(x) for x in dict.fromkeys(candidates) if x != value][:3]


def ferry_distance(wolves, sheep, forward, backward):
    def safe(w, s):
        return (s == 0 or w <= s) and (sheep - s == 0 or wolves - w <= sheep - s)

    start = (0, 0, 0)
    queue, seen = deque([(start, 0)]), {start}
    while queue:
        (w, s, side), distance = queue.popleft()
        if s == sheep:
            return distance
        sizes = forward if side == 0 else backward
        for dw in range(wolves + 1):
            for ds in range(sheep + 1):
                if dw + ds not in sizes:
                    continue
                nw, ns = (w + dw, s + ds) if side == 0 else (w - dw, s - ds)
                nxt = (nw, ns, 1 - side)
                if 0 <= nw <= wolves and 0 <= ns <= sheep and safe(nw, ns) and nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, distance + 1))
    return -1


def build_bundle():
    cards, rows, checks = [], [], []

    def add(number, refs, title, takeaway, task, cases, prompts, explanations, method):
        assert len(cases) == 5
        local = []
        for variant, (data, value) in enumerate(cases, 1):
            prompt = pair(*(text.format(**data) for text in prompts))
            explanation = pair(*(text.format(**data) for text in explanations))
            good = str(F(value))
            values = [good, *alternatives(value, task)]
            if task == "agenda":
                values = [good, *[str(i) for i in range(3) if str(i) != good], "no_winner"]
            elif task == "nested_mean":
                values = [good, "0", str(F(data["n"], 2)), str(data["n"])]
            elif task == "overlapping_neighbors":
                size = data["n"]
                values = [good, str(F(1, size*size)), str(F(1, size)), str(F(1, size-1))]
            assert len(values) == len(set(values)) == 4
            shift = (number + variant) % 4
            values = values[-shift:] + values[:-shift] if shift else values
            key = f"quick-sw-{number}-v{variant}"
            row = dict(key=key, source_key=f"quick-sw-{number}", variant=variant,
                       topic="reasoning", status="draft", prompt=prompt,
                       choices=[pair("אין מנצח", "No winner") if x == "no_winner" else pair(x) for x in values],
                       correct=shift, explanation=explanation)
            rows.append(row)
            local.append(row)
            checks.append(dict(key=key, task=task, inputs=data, options=values,
                               expected=good, method=method, professional_review="pending"))
        first = local[0]
        cards.append(dict(id=f"quick-sw-{number}", topic="reasoning",
                          interviewIds=[f"PREP-{x:03d}" for x in refs], title=pair(*title),
                          prompt=first["prompt"], answer={lg: first["choices"][first["correct"]][lg] + ". " + first["explanation"][lg] for lg in ("he", "en")},
                          takeaway=pair(*takeaway)))

    add(201, [198], ("הסתברות משותפת אינה אחידה", "Joint outcomes need not be uniform"),
        ("התניה משנה את משקלן של תוצאות אפשריות.", "Conditioning changes the weights of possible outcomes."),
        "nested_joint", [(dict(n=n, a=a, b=b), F(1, (n + 1) * (a + 1)) if b <= a else 0)
                         for n, a, b in [(3, 2, 1), (2, 0, 0), (4, 3, 2), (3, 1, 2), (5, 5, 5)]],
        ("מגרילים A באופן אחיד בשלמים 0..{n}, ואז B באופן אחיד ב־0..A. מה ההסתברות המשותפת A={a}, B={b}? הגבולות כלולים.",
         "Draw integer A uniformly from 0..{n}, then B uniformly from 0..A. What is the joint probability A={a}, B={b}? Both endpoints are included."),
        ("מכפילים את הסתברות A בהסתברות המותנית של B; אם B גדול מ־A התוצאה בלתי אפשרית.",
         "Multiply the probability of A by the conditional probability of B; B above A is impossible."),
        "Multiply conditional probabilities; independently enumerate weighted outcomes.")

    add(202, [198], ("ממוצע של ממוצעים מותנים", "Average the conditional averages"),
        ("לתוחלת מותנית אין צורך בהנחת אי־תלות.", "Conditional expectation does not require independence."),
        "nested_mean", [(dict(n=n), F(n, 4)) for n in [4, 2, 6, 1, 8]],
        ("A אחיד בשלמים 0..{n}; לאחריו B אחיד בשלמים 0..A, כולל הגבולות. מהי תוחלת B?", 
         "A is uniform over integers 0..{n}; B is then uniform over integers 0..A, including endpoints. What is the expectation of B?"),
        ("לכל A=a, הממוצע של B הוא a/2. ממוצעים שוב לפי התפלגות A; אי־תלות אינה נדרשת.",
         "For A=a the mean of B is a/2. Average again over A; independence is unnecessary."),
        "Law of total expectation, checked by exact weighted outcome enumeration.")

    add(203, [184], ("שארית עלולה להטות הגרלה", "A remainder can bias a draw"),
        ("אחידות נשמרת כשמספר המקורות לכל פלט שווה.", "Uniform output needs equal numbers of input outcomes per result."),
        "modulo_fibers", [(dict(base=b, m=m), math.ceil(b / m) - b // m) for b, m in [(5, 3), (6, 3), (7, 4), (8, 4), (9, 5)]],
        ("X אחיד בשלמים 0..{base} לא כולל {base}. מחזירים X modulo {m}. מה ההפרש בין מספר ערכי X שמובילים לשארית הנפוצה ביותר ולשארית הנדירה ביותר?",
         "X is uniform over integers 0..{base}, excluding {base}. Return X modulo {m}. What is the difference between the largest and smallest numbers of X values mapping to one remainder?"),
        ("מחלקים את ערכי הקלט בין השאריות. אם החלוקה אינה שלמה, חלק מהשאריות מקבלות מקור נוסף ולכן ההגרלה מוטה.",
         "Partition input values by remainder. An incomplete division gives some outputs an extra preimage, causing bias."),
        "Count the exact fibers of the remainder map.")

    add(204, [184], ("דחייה הוגנת עולה ניסיונות", "Fair rejection costs attempts"),
        ("דחיית תוצאות משמרת אחידות אך מגדילה עלות צפויה.", "Rejection preserves uniformity while increasing expected cost."),
        "rejection_cost", [(dict(base=b, m=m), F(2 * b * b, (b * b // m) * m)) for b, m in [(5, 7), (3, 4), (4, 5), (6, 9), (2, 3)]],
        ("כל ניסיון משתמש ב־2 הגרלות עצמאיות אחידות 0..{base} לא כולל {base}, ויוצר מספר דו־ספרתי בבסיס {base}. מקבלים רק את הקידומת שאורכה הכפולה הגדולה ביותר של {m}, ומנסים שוב בדחייה. מה תוחלת מספר ההגרלות עד קבלה?",
         "Each attempt uses 2 independent uniform draws from 0..{base}, excluding {base}, forming a two-digit base-{base} number. Accept only the longest initial range whose size is divisible by {m}; otherwise retry. What is the expected number of primitive draws until acceptance?"),
        ("מחשבים את שיעור הקבלה מתוך כל הזוגות. תוחלת הניסיונות היא ההופכי שלו, וכל ניסיון צורך 2 הגרלות.",
         "Find the accepted fraction of all pairs. Expected attempts equal its reciprocal, and every attempt costs 2 primitive draws."),
        "Geometric stopping cost from exact accepted-pair count.")

    add(205, [198], ("יותר דרכים לערך קטן", "Small values have more routes"),
        ("בחירה אחידה בכל שלב אינה מחייבת פלט סופי אחיד.", "Uniform choices at each stage need not give a uniform final output."),
        "nested_cdf", [(dict(n=n, k=k), sum((F(min(a, k) + 1, (n + 1) * (a + 1)) for a in range(n + 1)), F())) for n, k in [(3, 0), (3, 1), (2, 2), (4, 1), (1, 0)]],
        ("A אחיד בשלמים 0..{n}; אז B אחיד בשלמים 0..A. הגבולות כלולים. מה ההסתברות B≤{k}?",
         "A is uniform over integers 0..{n}; B is then uniform over integers 0..A. Endpoints are included. What is the probability B≤{k}?"),
        ("לכל ערך של A סופרים את ערכי B המותרים שמתאימים, ומשקללים בהסתברות של אותו A.",
         "For each A, count qualifying B values among its allowed values, then weight by that A's probability."),
        "Exact conditional counting of a cumulative event.")

    add(206, [192], ("הקצה משפיע על שכנות", "An endpoint affects adjacency"),
        ("קיבוץ זוג בסדר קבוע שונה מקיבוץ זוג בכל סדר.", "A fixed-order pair differs from an unordered adjacent pair."),
        "right_neighbor", [(dict(n=n), F(1, n)) for n in [6, 3, 4, 2, 7]],
        ("{n} אנשים שונים יושבים בשורה בסידור אחיד. מה ההסתברות ש־B יושב צמוד מימין ל־A? אין התניה על מושבו של A.",
         "{n} distinct people sit in a uniformly random row. What is the probability B sits immediately right of A? A's seat is not conditioned on."),
        ("הזוג AB הוא יחידה אחת בסדר קבוע. מסדרים אותה עם שאר האנשים, ביחס לכל סידורי הישיבה.",
         "Treat AB as one fixed-order block. Compare arrangements of that block and the others with all seatings."),
        "Fixed-order block count, checked against all seat permutations.")

    add(207, [192], ("שתי שכנויות חולקות אדם", "Two adjacencies share a person"),
        ("אירועי שכנות שמשתפים אדם אינם בהכרח בלתי תלויים.", "Adjacency events sharing a person need not be independent."),
        "overlapping_neighbors", [(dict(n=n), F(1, n * (n - 1))) for n in [5, 3, 4, 6, 7]],
        ("{n} אנשים שונים יושבים בשורה באחידות. מה ההסתברות שבאותו סידור B צמוד מימין ל־A וגם C צמוד מימין ל־B?",
         "{n} distinct people sit uniformly in a row. What is the probability B is immediately right of A and C is immediately right of B in the same seating?"),
        ("שני התנאים מחייבים מקשה ABC. סופרים את המקשה פעם אחת, במקום להכפיל הסתברויות כאילו האירועים עצמאיים.",
         "Both conditions force one ABC block. Count that block once rather than assuming the adjacency events are independent."),
        "Three-person block count and full permutation enumeration.")

    add(208, [190], ("סדר העימותים בוחר מנצח", "An agenda selects the winner"),
        ("מעגל רוב מאפשר לסדר ההצבעות להשפיע על התוצאה.", "A majority cycle makes the voting agenda consequential."),
        "agenda", [(dict(bye=b, reverse=r), b) for b, r in [(0, 0), (1, 0), (2, 0), (0, 1), (2, 1)]],
        ("מועמדים מקודדים 0,1,2. אם reverse=0, הרוב מעדיף 0 על 1, 1 על 2, ו־2 על 0; אם reverse=1 כל הכיוונים הפוכים. כאן reverse={reverse}. מועמד {bye} ממתין לגמר מול מנצח עימות שני האחרים. מי זוכה?",
         "Candidates are 0,1,2. With reverse=0, majorities prefer 0 over 1, 1 over 2, and 2 over 0; reverse=1 reverses every edge. Here reverse={reverse}. Candidate {bye} waits for the winner between the other two. Who wins the final?"),
        ("בכל כיוון של המעגל, המנצח בעימות הראשון הוא דווקא מי שהממתין בגמר מנצח בעימות זוגי.",
         "In either cycle direction, the first-round winner is precisely the opponent whom the waiting finalist beats."),
        "Enumerate the two pairwise rounds for each cycle orientation.")

    add(209, [190], ("תיקו כללי אינו תיקו זוגי", "Overall ties are not pairwise ties"),
        ("סכומי דירוגים אינם קובעים לבדם את עוצמת הרוב הזוגי.", "Ranking totals do not alone determine pairwise majority strength."),
        "voting_margin", [(dict(m=m, x=x), abs(2 * x - m)) for m, x in [(5, 1), (5, 4), (3, 0), (4, 2), (7, 5)]],
        ("מספרי המצביעים לפי הדירוגים ABC, ACB, BAC, BCA, CAB, CBA הם בהתאמה x,m−x,m−x,x,x,m−x. כאן m={m}, x={x}. כל מצביע מעדיף מועמד מוקדם בדירוג. מה ההפרש המוחלט בקולות בעימות A מול B?",
         "Voter counts for rankings ABC, ACB, BAC, BCA, CAB, CBA are x,m−x,m−x,x,x,m−x. Here m={m}, x={x}. Earlier means preferred. What is the absolute vote margin in A versus B?"),
        ("מסכמים בנפרד את הדירוגים שמציבים A לפני B ואת אלה שמציבים B לפני A. תיקו בסיכומי מקומות אינו מספיק.",
         "Sum rankings putting A before B separately from those putting B before A. Tied position totals do not settle this comparison."),
        "Count sincere pairwise preferences across the six ranking classes.")

    add(210, [195], ("כמה מחזורים ארוכים יכולים להתקיים", "How many long cycles can coexist"),
        ("חסם על עצמים זרים נובע מתקציב כולל משותף.", "Disjoint structures share a finite total budget."),
        "long_cycles", [(dict(n=n, limit=k), n // (k + 1)) for n, k in [(100, 50), (12, 4), (9, 3), (8, 8), (15, 6)]],
        ("תמורה של {n} פתקים מתפרקת למחזורים זרים. מה מספר המחזורים המרבי שאורכם גדול מ־{limit}? אין מגבלות נוספות על התמורה.",
         "A permutation of {n} notes decomposes into disjoint cycles. What is the maximum number of cycles longer than {limit}? No other constraints apply."),
        ("כל מחזור כזה צורך לפחות limit+1 פתקים נפרדים. החסם מושג במחזורים הקצרים ביותר שמקיימים את התנאי, עם שארית כרצוננו.",
         "Each such cycle consumes at least limit+1 distinct notes. Use cycles of that minimum length to attain the bound; arrange leftovers freely."),
        "Disjoint-size lower bound with an attaining partition witness.")

    add(211, [195], ("לפצל קרוב ככל האפשר לחצי", "Split as close to half as possible"),
        ("מזעור המקרה הגרוע דורש איזון בין שני הענפים.", "Minimizing the worst case requires balancing the two branches."),
        "cycle_split", [(dict(length=n), (n + 1) // 2) for n in [9, 10, 7, 3, 12]],
        ("מחזור יחיד באורך {length} מפוצל בהחלפת שני חצים יוצאים. אפשר לקבל כל שני אורכים חיוביים שסכומם {length}. מה האורך המרבי הקטן ביותר שניתן להבטיח בין שני המחזורים החדשים?",
         "Swapping two outgoing links splits one length-{length} cycle into two positive lengths summing to {length}. Any such split is allowed. What is the smallest achievable length of the larger resulting cycle?"),
        ("אחד החלקים חייב להכיל לפחות חצי מהאורך הכולל, בעיגול מעלה. חלוקה לשני חלקים שהפרשם לכל היותר 1 משיגה זאת.",
         "One part must contain at least half the total, rounded upward. Two parts differing by at most 1 attain the bound."),
        "Minimax over every legal positive split.")

    add(212, [195], ("החלפה יכולה גם לחבר מחזורים", "A swap can also merge cycles"),
        ("יש לבדוק אם שני הקצוות שייכים לאותו מחזור לפני שמשנים חצים.", "Check whether the chosen positions belong to the same cycle before swapping links."),
        "cycle_merge", [(dict(a=a, b=b), a + b) for a, b in [(3, 4), (1, 5), (2, 2), (4, 6), (1, 1)]],
        ("בתמורה יש שני מחזורים זרים באורכים {a} ו־{b}. מחליפים את הפתקים בשתי קופסאות, אחת מכל מחזור. מה אורך המחזור החדש שמכיל את שתיהן?",
         "A permutation has disjoint cycles of lengths {a} and {b}. Swap the notes in two boxes, one from each cycle. What is the length of the new cycle containing both boxes?"),
        ("החלפת החצים מעבירה את ההליכה דרך שני המחזורים לפני החזרה להתחלה. היא מחברת אותם, בניגוד להחלפה בתוך מחזור יחיד.",
         "The redirected walk traverses both cycles before returning. This merges them, unlike a swap within one cycle."),
        "Trace an explicit pair of cycles after swapping their outgoing links.")

    add(213, [8, 201], ("סימטריה מקטינה את מספר המצבים", "Symmetry reduces the state count"),
        ("תיאורים מסובבים עשויים לייצג אותו מצב פיזי אנונימי.", "Rotated descriptions can represent one anonymous physical state."),
        "necklaces", [(dict(n=n), sum(2 ** math.gcd(n, k) for k in range(n)) // n) for n in [3, 4, 5, 6, 7]],
        ("במעגל אנונימי של {n} חדרים לכל חדר מנורה בינארית. שני מצבי מנורות נחשבים זהים רק אם סיבוב מעביר אחד לשני; שיקוף אינו מותר. כמה מצבים שונים קיימים?",
         "An anonymous ring of {n} rooms has one binary lamp per room. Two lamp configurations count as identical exactly when a rotation maps one to the other; reflections are not allowed. How many distinct configurations exist?"),
        ("מקבצים את כל המילים הבינאריות לפי סיבוב. מצבים סימטריים יוצרים קבוצות קטנות יותר, ולכן חלוקה פשוטה של מספר המילים במספר החדרים אינה מספיקה.",
         "Group binary words by rotation. Symmetric words have smaller groups, so simply dividing the number of words by the room count is insufficient."),
        "Burnside rotation count; independently enumerate canonical rotation representatives.")

    add(214, [201, 178], ("חזרות מגבילות אך לא תמיד מזהות", "Returns constrain without always identifying"),
        ("כל תצפית צריכה לצמצם קבוצת מועמדים, ולא רק להתאים להשערה אחת.", "An observation must narrow candidate worlds rather than merely fit one hypothesis."),
        "ring_candidates", [(dict(bound=b, distances=ds), sum(all(d % n == 0 for d in ds) for n in range(1, b + 1))) for b, ds in [(10, [6, 9]), (12, [8, 12]), (8, [5, 10]), (10, [12, 18]), (5, [4, 8])]],
        ("מעגל מכיל N חדרים, 1≤N≤{bound}. הולכים באותו כיוון, חדר לצעד. זיהוי אמין של חדר ההתחלה מאשר חזרה לאחר מרחקי הצעדים {distances}; לא ידוע אם היו חזרות נוספות. כמה ערכי N עדיין אפשריים?",
         "A ring has N rooms, 1≤N≤{bound}. Move one room per step in one direction. Reliable start-room identification confirms returns after step distances {distances}; other returns may have occurred. How many N values remain possible?"),
        ("כל מרחק חזרה חייב להתחלק במספר החדרים. בודקים את כל המחלקים המשותפים בטווח; לא מניחים שהתצפית הייתה החזרה הראשונה.",
         "Every return distance is divisible by the room count. Retain common divisors in range; the observations need not be first returns."),
        "Divisibility constraints over every candidate ring size.")

    ferry_cases = [(3, 3, [2], [1]), (1, 1, [2], [1]), (2, 2, [2], [1]), (3, 3, [1, 2], [1, 2]), (0, 3, [2], [1])]
    add(215, [203], ("כלל הפלגה משנה נגישות", "A crossing rule changes reachability"),
        ("פתרון של גרסה מוכרת אינו הוכחה לגרסה בעלת כללים אחרים.", "A familiar variant's solution does not prove reachability under different rules."),
        "ferry", [(dict(w=w, s=s, forward=f, backward=b), ferry_distance(w, s, f, b)) for w, s, f, b in ferry_cases],
        ("{w} זאבים, {s} כבשים וסירה מתחילים משמאל. מספר נוסעים מותר בהלוך: {forward}; בחזור: {backward}. בגדה עם כבשים אסור רוב זאבים; גדה בלי כבשים מותרת. מה מספר ההפלגות המזערי להעברת כל הכבשים ימינה? החיות בסירה נספרות ביעד. החזירו −1 אם בלתי אפשרי.",
         "Start with {w} wolves, {s} sheep and a boat left. Allowed passenger counts: outward {forward}, return {backward}. A bank with sheep cannot have more wolves; a sheep-free bank is allowed. Minimum crossings moving all sheep right? Boat occupants count at destination. Return −1 if impossible."),
        ("מחפשים רק במצבים ובהפלגות החוקיים. המטרה עוסקת בכבשים; אין דרישה שכל הזאבים יועברו. חיפוש מלא מבחין בין מסלול ארוך לבין חוסר מסלול.",
         "Search legal states and crossings only. The goal concerns sheep, without requiring every wolf to cross. Exhaustive reachability distinguishes a long route from no route."),
        "Breadth-first search; independently check shortest paths by repeated reachable-set expansion.")

    add(216, [203], ("איסור מותנה אינו איסור גורף", "A conditional prohibition is not universal"),
        ("אין כבשים הוא מקרה נפרד מתנאי בטיחות כאשר יש כבשים.", "A sheep-free bank is a separate case from safety when sheep are present."),
        "safe_bank", [(dict(w=w, s=s), (w + 1) + sum(min(w, k) + 1 for k in range(1, s + 1))) for w, s in [(3, 3), (2, 3), (4, 2), (1, 4), (0, 3)]],
        ("בגדה בודדת עשויים להיות 0..{w} זאבים ו־0..{s} כבשים. מצב בטוח אם אין כבשים, או שמספר הזאבים אינו גדול ממספר הכבשים. כמה זוגות ספירות בטוחים קיימים? אין כאן אילוץ על גדה שנייה.",
         "One bank may contain 0..{w} wolves and 0..{s} sheep. It is safe if sheep are absent or wolves do not outnumber sheep. How many safe count pairs exist? No second-bank constraint applies."),
        ("סופרים בנפרד את כל המצבים בלי כבשים. לכל כמות כבשים חיובית מגבילים את מספר הזאבים לכמות זו ולמלאי הקיים.",
         "Count all sheep-free states separately. With a positive sheep count, bound wolves by both that count and available stock."),
        "Disjoint case count for the stated logical implication.")

    add(217, [183], ("פורסים משטח לפני שמקצרים", "Unfold a surface before shortening"),
        ("מרחק דרך גוף אינו בהכרח מסלול שמותר על פניו.", "A through-body distance need not be a permitted surface route."),
        "box_surface", [(dict(a=a, b=b, c=c), min((a+b)**2+c*c, (a+c)**2+b*b, (b+c)**2+a*a)) for a, b, c in [(1, 1, 1), (1, 2, 3), (2, 2, 3), (2, 3, 4), (1, 1, 4)]],
        ("תיבה מלבנית בעלת מקצועות {a},{b},{c}. יש לעבור בין קודקודים נגדיים רק על המשטח. משווים את שלוש הפריסות המלבניות עם צלעות (a+b,c), (a+c,b), (b+c,a). מה ריבוע אורך המסלול הקצר מביניהן?",
         "A rectangular box has edge lengths {a},{b},{c}. Travel between opposite vertices on its surface. Compare the three rectangular unfoldings with sides (a+b,c), (a+c,b), (b+c,a). What is the squared length of the shortest route among them?"),
        ("בכל פריסה הקטע הישר הוא הקצר ביותר. משווים ריבועי אורכים לפי פיתגורס, בלי להתבלבל עם אלכסון פנימי שאינו מסלול על המשטח.",
         "A straight segment is shortest in each unfolding. Compare squared lengths by Pythagoras, excluding the interior diagonal from surface routes."),
        "Compare the three valid unfolding diagonals exactly.")

    add(218, [22], ("ללא החזרה משתנה המכנה", "Without replacement the denominator changes"),
        ("כישלון ללא החזרה מסיר מועמד; דגימה עם החזרה אינה עושה זאת.", "A miss without replacement removes a candidate; sampling with replacement does not."),
        "unseen_target", [(dict(n=n, misses=k), F(1, n-k)) for n, k in [(10, 3), (8, 0), (6, 5), (12, 8), (5, 2)]],
        ("יעד אחד מוסתר באחידות בין {n} תאים. בודקים תאים שונים ללא החזרה, ו־{misses} בדיקות נכשלו. מה הסיכוי שהתא הבא, שנבחר באחידות מהתאים שלא נבדקו, מכיל את היעד?",
         "One target is uniform among {n} cells. Check distinct cells without replacement; {misses} checks have missed. What is the chance the next uniformly selected unchecked cell contains the target?"),
        ("אחרי הכישלונות היעד נמצא באחידות בין התאים שנותרו. אין סיבה להשאיר במכנה תאים שכבר נשללו.",
         "After the misses the target is uniform among remaining cells. Excluded cells no longer belong in the denominator."),
        "Condition on the observed misses; enumerate remaining target positions.")

    add(219, [22], ("בדיקה חוזרת יכולה לבזבז הגרלה", "Repeated sampling can waste a draw"),
        ("דגימה ללא החזרה מונעת את עלות החזרות של דגימה עצמאית.", "Sampling without replacement avoids the repeat cost of independent draws."),
        "coupon_remaining", [(dict(n=n, seen=k), sum((F(n, n-i) for i in range(k, n)), F())) for n, k in [(4, 2), (3, 0), (5, 4), (2, 1), (4, 3)]],
        ("בכל הגרלה עצמאית נבחר תא אחיד מתוך {n}, עם החזרה. כבר נראו {seen} תאים שונים. מה תוחלת מספר ההגרלות הנוספות עד שכל התאים נראו?",
         "Each independent draw selects a uniform cell among {n}, with replacement. Already {seen} distinct cells have been seen. What is the expected number of additional draws until all cells have appeared?"),
        ("כאשר ידועים i תאים, ההסתברות לתא חדש היא (n−i)/n. סוכמים את תוחלות ההמתנה לתא חדש בכל שלב שנותר.",
         "With i cells known, a new cell arrives with probability (n−i)/n. Add the expected waiting times for all remaining discovery stages."),
        "Sum geometric-stage expectations; independently solve finite-state expectation equations.")

    order_cases = [(3, [[0,1]]), (3, [[0,1],[1,2]]), (4, [[0,1],[0,2]]), (4, [[0,1],[2,3]]), (4, [])]
    add(220, [9], ("סדר חלקי משאיר כמה דירוגים", "A partial order leaves several rankings"),
        ("השוואות ידועות אינן בהכרח מגדירות סדר מלא.", "Known comparisons need not determine a complete order."),
        "linear_orders", [(dict(n=n, edges=e), sum(all(p.index(a)<p.index(b) for a,b in e) for p in itertools.permutations(range(n)))) for n,e in order_cases],
        ("יש {n} סוסים שונים במהירויות שונות. כל זוג [a,b] ברשימה {edges} אומר ש־a מהיר מ־b. אין מידע נוסף. כמה דירוגי מהירות מלאים מתאימים לכל ההשוואות?",
         "There are {n} horses with distinct speeds. Each pair [a,b] in {edges} states that a is faster than b. Nothing else is known. How many complete speed rankings satisfy all comparisons?"),
        ("סופרים רק סדרים שמכבדים כל השוואה, כולל השלכות מעבריות. אין להפוך היעדר השוואה לשוויון או לקבוע סדר שרירותי בין הבלתי ידועים.",
         "Count orders respecting every comparison and its transitive consequences. Missing comparisons imply neither equality nor an arbitrary fixed order."),
        "Enumerate linear extensions of the comparison relation.")

    add(221, [161], ("מסלול פתוח אינו דורש חזרה", "An open route need not return"),
        ("יש להגדיר אם חוזרים להתחלה לפני שממזערים מרחק כולל.", "Specify whether a return is required before minimizing travel."),
        "elevator_distance", [(dict(start=s, low=lo, high=h), h-lo+min(abs(s-lo),abs(s-h))) for s,lo,h in [(4,1,8),(1,1,8),(9,2,6),(0,3,7),(5,2,9)]],
        ("מעלית מתחילה בקומה {start} וחייבת לבקר בקומות {low} ו־{high}. העלות היא מרחק בקומות; עצירה חינם, ואין צורך לחזור להתחלה. מה המרחק הכולל המזערי?",
         "An elevator starts at floor {start} and must visit floors {low} and {high}. Cost is floor distance; stops are free and no return is required. What is the minimum total distance?"),
        ("חייבים לכסות את הקטע בין שתי קומות היעד. נוסף עליו המרחק מההתחלה לקצה הראשון שנבחר; בוחרים את הקצה הקרוב יותר.",
         "The entire interval between destinations must be covered. Add the distance from the start to the first chosen endpoint; choose the nearer endpoint."),
        "Compare both endpoint visitation orders; use interval coverage as a lower bound.")

    add(222, [161, 149], ("עדיפות משנה את סדר השירות", "Priority changes the service order"),
        ("הסדר הטוב תלוי בפונקציית העלות, לא רק במשך הפעולות.", "The best order depends on the objective, not just processing time."),
        "weighted_completion", [(dict(a=a,b=b,wa=wa,wb=wb),min(wa*a+wb*(a+b),wb*b+wa*(a+b))) for a,b,wa,wb in [(1,4,1,10),(2,3,2,1),(3,1,4,1),(2,2,1,3),(4,5,3,2)]],
        ("שרת יחיד מבצע ללא הפסקה שתי משימות זמינות בזמן 0. משכי A,B הם {a},{b}; משקלי החשיבות שלהם {wa},{wb}. אם CA,CB זמני הסיום, מה הערך המזערי של wa·CA+wb·CB?",
         "One server processes two jobs available at time 0 without preemption. Durations A,B are {a},{b}; importance weights are {wa},{wb}. If CA,CB are completion times, what is the minimum wa·CA+wb·CB?"),
        ("מחשבים את זמני הסיום בשני הסדרים ואת העלות המשוקללת שלהם. משימה קצרה אינה בהכרח ראשונה כשמשקלי ההמתנה שונים.",
         "Compute completion times and weighted cost for both orders. A shorter job need not go first when waiting carries different weights."),
        "Exact comparison of the two nonpreemptive schedules.")

    cover_cases = [(3, [[0,1],[1,2],[0],[2]]),(3,[[0,1,2],[0],[1],[2]]),(4,[[0,1],[2,3],[0,2],[1,3]]),(3,[[0],[1],[2]]),(4,[[0,1,2],[1,2,3],[0],[3]])]
    def cover_size(n,sets):
        return next(k for k in range(len(sets)+1) if any(set().union(*(set(sets[i]) for i in sub))==set(range(n)) for sub in itertools.combinations(range(len(sets)),k)))
    add(223,[159],("פחות בדיקות עם כיסוי מלא", "Fewer tests with complete coverage"),
        ("מספר הבדיקות אינו מדד לכיסוי; יש לחשב את איחוד הדרישות.", "Test count is not coverage; inspect the union of covered requirements."),
        "set_cover",[(dict(n=n,sets=s),cover_size(n,s)) for n,s in cover_cases],
        ("דרישות מוצר ממוספרות 0..{n} לא כולל {n}. הבדיקות מכסות את קבוצות הדרישות {sets}. מה מספר הבדיקות המזערי שאיחוד הכיסוי שלהן כולל את כל הדרישות?",
         "Product requirements are numbered 0..{n}, excluding {n}. Available tests cover requirement sets {sets}. What is the minimum number of tests whose combined coverage includes every requirement?"),
        ("בוחנים צירופי בדיקות לפי גודלם, ומאחדים את הדרישות שהן מכסות. בדיקות חופפות אינן מוסיפות כיסוי חדש באזורים החופפים.",
         "Consider subsets of tests by size and union their covered requirements. Overlapping tests add no new coverage in the overlap."),
        "Exhaustive minimum cover with a smaller-subset impossibility check.")

    measure_cases = [[[0,0],[0,1],[1,0],[1,1]], [[0,0,0],[0,0,1],[1,1,0]], [[0,0,0],[1,1,1]], [[0,0,0],[0,1,1],[1,0,1],[1,1,0]], [[0,0,0],[0,0,1],[0,1,0],[1,0,0]]]
    def measurements(patterns):
        return next(k for k in range(len(patterns[0])+1) if any(len({tuple(row[i] for i in cols) for row in patterns})==len(patterns) for cols in itertools.combinations(range(len(patterns[0])),k)))
    add(224,[159,154],("לבחור מדידות שמבדילות כל זוג", "Choose measurements distinguishing every pair"),
        ("כיסוי דרישות וזיהוי מצבים הן שתי מטרות שונות של בדיקה.", "Requirement coverage and state identification are different testing objectives."),
        "measurement_cover",[(dict(patterns=p),measurements(p)) for p in measure_cases],
        ("כל שורה ב־{patterns} היא תוצאות בינאריות חזויות של מצב נסתר, אחת לכל מדידה. המדידות אמינות ונבחרות מראש. מה מספר העמודות המזערי שמאפשר לזהות בוודאות איזו שורה נכונה?",
         "Each row of {patterns} lists predicted binary measurement results for one hidden state. Measurements are reliable and chosen in advance. What minimum number of columns guarantees identifying the correct row?"),
        ("בקבוצת העמודות הנבחרת לכל מצב חייבת להיות חתימה שונה. מספיק להבדיל כל זוג מצבים; כמות המדידות לבדה אינה מבטיחה זאת.",
         "Every state needs a distinct signature on selected columns. Distinguish every state pair; the measurement count alone is insufficient."),
        "Find the smallest column subset with distinct row projections.")

    add(225,[159],("חזרה עצמאית מפחיתה טעות", "Independent repetition reduces error"),
        ("שיפור ברוב מדידות דורש הנחת עצמאות של הטעויות.", "Majority-vote improvement depends on independent errors."),
        "majority_error",[(dict(trials=n,p=str(p)),sum((F(math.comb(n,k))*p**k*(1-p)**(n-k) for k in range(n//2+1,n+1)),F())) for n,p in [(3,F(1,4)),(3,F(1,3)),(5,F(1,4)),(3,F(1,2)),(5,F(1,3))]],
        ("בדיקה של מוצר תקין מחזירה טעות בהסתברות {p} בכל הפעלה, באופן בלתי תלוי. מפעילים {trials} פעמים ומחליטים לפי רוב. מה הסתברות ההכרעה השגויה?",
         "A test of a conforming product independently gives a wrong result with probability {p} on each run. Run it {trials} times and decide by majority. What is the probability of a wrong final verdict?"),
        ("שגיאה סופית דורשת רוב של תוצאות שגויות. סוכמים את הסתברויות כל מספרי השגיאות האלה; ללא עצמאות אותו חישוב אינו מוצדק.",
         "A wrong verdict requires a majority of erroneous runs. Sum those error-count probabilities; without independence this calculation is unjustified."),
        "Exact binomial tail, checked by enumerating all outcome words.")

    add(226,[159],("דגימה תקינה אינה הוכחת שלמות", "A passing sample does not prove perfection"),
        ("ללא החזרה, הסתברות מדגם מחושבת מתוך קבוצות ולא מניסיונות עצמאיים.", "Without replacement, sample probabilities count subsets rather than independent trials."),
        "sample_miss",[(dict(n=n,d=d,k=k),F(math.comb(n-d,k),math.comb(n,k)) if k<=n-d else 0) for n,d,k in [(10,2,3),(6,1,2),(5,2,4),(8,3,2),(7,0,3)]],
        ("חבילה מכילה {n} דפים, מהם בדיוק {d} פגומים. בוחרים באחידות {k} דפים שונים ללא החזרה ובודקים אותם בצורה מושלמת. מה ההסתברות שלא יימצא פגם?",
         "A pack contains {n} sheets, exactly {d} defective. Uniformly sample {k} distinct sheets without replacement and inspect perfectly. What is the probability no defect is found?"),
        ("מונה ההסתברות הוא מספר המדגמים שכל דפיהם תקינים; המכנה הוא מספר כל המדגמים בגודל הנתון. הצלחת המדגם אינה מבטיחה ששאר החבילה תקינה.",
         "Count samples containing only conforming sheets over all samples of the given size. A passing sample does not certify the untested remainder."),
        "Hypergeometric zero-defect probability with exhaustive subset oracle.")

    preferences = [[[0,1],[0,1]], [[0,1],[0,2],[1,2]], [[0,1],[0,1],[1,2]], [[1,0],[2,1],[0,2]], [[0,1,2],[0,1,2],[0,1,2]]]
    def assignments(prefs):
        return [x for x in itertools.product(*prefs) if len(set(x))==len(x)]
    add(227,[148],("מלא אינו בהכרח מועדף", "Complete does not mean most preferred"),
        ("היתכנות ואיכות העדפות הן פונקציות מטרה שונות.", "Feasibility and preference quality are different objectives."),
        "first_choices",[(dict(prefs=p),max(sum(v==p[i][0] for i,v in enumerate(a)) for a in assignments(p))) for p in preferences],
        ("כל אדם צריך פריט שונה. רשימות הפריטים {prefs} מסודרות מהעדיף ביותר לפחות עדיף; פריט שאינו ברשימה אסור. מבין הקצאות מלאות חוקיות, מה המספר המרבי של אנשים שמקבלים את הבחירה הראשונה שלהם?",
         "Each person needs a different item. Allowed-item lists {prefs} run from most to least preferred; unlisted items are forbidden. Among legal complete assignments, what maximum number of people can receive their first choice?"),
        ("מסננים תחילה הקצאות מלאות ללא התנגשות, ואז ממקסמים את מספר הבחירות הראשונות. עצם קיום הקצאה מלאה אינו קובע את ציונה.",
         "First retain complete collision-free assignments, then maximize first-choice satisfaction. A complete matching's existence does not determine its preference score."),
        "Enumerate full assignments and optimize the declared first-choice score.")

    add(228,[148],("הקצאה אפשרית אינה בהכרח יחידה", "A feasible assignment may not be unique"),
        ("מספר הפתרונות מבחין בין אפשרות, כפייה ואי־אפשרות.", "The solution count distinguishes feasibility, forced choices, and impossibility."),
        "matching_count",[(dict(prefs=p),len(assignments(p))) for p in [[[0,1],[0,1]],[[0],[0]],[[0,1],[1,2],[0,2]],[[0],[1],[2]],[[0,1,2],[0,1,2],[0,1,2]]]],
        ("כל אדם צריך בדיוק פריט אחד, ואסור לשני אנשים לקבל אותו פריט. הרשימות {prefs} מכילות את כל הפריטים המותרים לכל אדם. כמה הקצאות מלאות שונות קיימות? אנשים ופריטים נבדלים זה מזה.",
         "Each person needs exactly one item, with no item shared. Lists {prefs} give all allowed items for each person. How many distinct complete assignments exist? People and items are distinguishable."),
        ("מונים הקצאות חוקיות ולא בחירות מקומיות נפרדות. שתי בחירות שמתנגשות באותו פריט אינן יוצרות פתרון מלא.",
         "Count legal complete assignments rather than independent local choices. Two choices colliding on one item do not form a solution."),
        "Count injective allowed assignments by exhaustive finite search.")

    add(229,[57],("סיכוי גבוה אינו ודאות", "High probability is not certainty"),
        ("הבטחה הסתברותית בחלון סופי שונה מהבטחה לכל רצף בחירות.", "A finite-window probability differs from a guarantee for every selection sequence."),
        "all_visited",[(dict(n=n,visits=k),sum((-1)**j*math.comb(n,j)*F(n-j,n)**k for j in range(n+1))) for n,k in [(2,3),(3,3),(3,4),(2,5),(4,3)]],
        ("בכל ביקור בוחרים אסיר אחד באופן אחיד ועצמאי מתוך {n}. מה ההסתברות שאחרי בדיוק {visits} ביקורים כל אסיר נבחר לפחות פעם אחת? אין מידע על בחירות קודמות.",
         "Each visit independently chooses one prisoner uniformly from {n}. What is the probability every prisoner has been selected after exactly {visits} visits? There is no prior selection history."),
        ("סופרים רצפי ביקורים שמכסים את כל האסירים מתוך כל הרצפים האפשריים. גם סיכוי גבוה אינו שולל רצף שחוזר רק לאותו אסיר.",
         "Count visit sequences covering all prisoners among all possible sequences. Even a high probability does not exclude repeated selection of one prisoner."),
        "Inclusion-exclusion, independently enumerate visit sequences.")

    add(230,[96],("לינאריות ללא עצמאות הצלחות", "Linearity without independent successes"),
        ("לתוחלת סכום מספיקות תוחלות האיברים; אין צורך בעצמאות ביניהם.", "The expectation of a sum needs individual expectations, not their independence."),
        "hat_expectation",[(dict(n=n,colors=k),F(n,k)) for n,k in [(6,3),(5,2),(4,4),(7,3),(3,2)]],
        ("ל־{n} אנשים כובעים עצמאיים ואחידים מתוך {colors} צבעים. כל אחד רואה רק את האחרים ומנחש יחד איתם לפי כלל דטרמיניסטי מוסכם. מה תוחלת מספר הניחושים הנכונים, לכל כלל כזה? אין תקשורת אחרי הנחת הכובעים.",
         "{n} people have independent uniform hats of {colors} colors. Each sees only the others and simultaneously guesses using any agreed deterministic rule. What is the expected number correct, for every such rule? There is no communication after hats are placed."),
        ("לאחר קיבוע כל הכובעים שאדם רואה, צבעו שלו עדיין אחיד. לכל אדם סיכוי שווה להצליח; סוכמים תוחלות גם כשההצלחות תלויות זו בזו.",
         "After fixing every hat a person sees, their own color remains uniform. Add individual correctness expectations even if the success events are dependent."),
        "Condition on visible hats, then apply linearity; enumerate a dependent copy-neighbor policy as a check.")

    def urn_best(red,white):
        total=red+white
        return max(F(r,a)/2+F(red-r,total-a)/2 for a in range(1,total) for r in range(red+1) if 0<=a-r<=white and 0<=red-r<=total-a)
    add(231,[169],("ממקסמים את ההסתברות הכוללת", "Optimize the complete probability"),
        ("אופטימום מקומי בקבוצה אחת אינו מספיק בלי לחשב את שתי הקבוצות.", "Improving one group alone does not replace calculating the total objective."),
        "urn_optimum",[(dict(red=r,white=w),urn_best(r,w)) for r,w in [(3,3),(2,4),(1,4),(4,2),(2,1)]],
        ("מחלקים {red} כדורים אדומים ו־{white} לבנים בין שני כדים לא ריקים, ללא הוספה או השמטה. בוחרים כד אחיד ואז כדור אחיד מתוכו. מה ההסתברות המרבית לקבל אדום?",
         "Split {red} red and {white} white balls between two nonempty urns without loss. Choose an urn uniformly, then a ball uniformly within it. What is the maximum probability of red?"),
        ("מחשבים ממוצע של שני השברים האדומים בכל חלוקה חוקית. אפשר לבדוק את כל החלוקות הקטנות, ולא להחליף בחירה אחידה של כד בבחירה אחידה של כדור.",
         "Average the two red fractions for each legal split. Enumerate these small allocations; uniform urn selection is not uniform selection among all balls."),
        "Exhaust all integer urn allocations, including every nonempty-size boundary.")

    vectors = [[[1,0],[-1,0],[0,1]], [[1,0],[0,1]], [[1,1],[-1,-1]], [[0,0],[1,0]], [[1,0],[0,1],[1,1],[1,-1]]]
    add(232,[49],("קודים נגדיים מבלבלים כבד וקל", "Opposite codes confuse heavy and light"),
        ("ספירת תוצאות אינה מספיקה כאשר שתי השערות חולקות חתימה.", "Outcome capacity is insufficient when hypotheses share signatures."),
        "signed_codes",[(dict(vectors=vs),len({tuple(sign*x for x in v) for v in vs for sign in (-1,1)})) for vs in vectors],
        ("מטבע מזויף יחיד יכול להיות כבד או קל. חתימות המדידה המנורמלות של המטבעות הכבדים הן {vectors}; חתימת קל היא היפוכה. שקילות מאוזנות במטבעות תקינים ידועים. כמה חתימות תוצאה שונות יש לכל השערות מיקום וכיוון יחד?",
         "One counterfeit coin may be heavy or light. Normalized measurement signatures for heavy coins are {vectors}; a light coin gives the negative signature. Known normal coins balance the weighings. How many distinct outcome signatures exist across all position-and-direction hypotheses?"),
        ("מוסיפים לכל וקטור גם את הווקטור הנגדי, וסופרים חתימות שונות בלבד. וקטורים נגדיים או וקטור אפס יוצרים התנגשויות בין השערות.",
         "Include every vector and its negative, counting distinct signatures only. Opposite vectors and zero vectors cause hypothesis collisions."),
        "Union of signed signature vectors with explicit collision witnesses.")

    add(233,[73],("זמן התוצאה הוא מידע נוסף", "Outcome timing adds information"),
        ("קיבולת הערוץ תלויה גם בתזמון שניתן להבחין בו לפני המועד.", "Channel capacity also depends on distinguishable outcome times before the deadline."),
        "timed_patterns",[(dict(tasters=t,rounds=r), (r+1)**t) for t,r in [(2,2),(3,2),(2,3),(1,4),(3,1)]],
        ("יש {tasters} טועמים ו־{rounds} סבבים עוקבים. תוצאת כל סבב ידועה לפני הבא. לכל טועם תוצאה מובחנת: מוות בסבב מסוים, או הישרדות בכולם. מניחים מימוש חופשי של כל צירופי התוצאות. כמה חתימות זמן שונות אפשר לקודד?",
         "There are {tasters} tasters and {rounds} sequential rounds, each resolved before the next. A taster's distinguishable outcome is death in one round or survival through all. Assume every outcome combination is realizable. How many distinct timing signatures can be encoded?"),
        ("לכל טועם יש תוצאה לכל סבב מוות אפשרי ועוד תוצאת הישרדות. כופלים את מספר האפשרויות בין טועמים; אין להניח שרואים סבב שטרם הסתיים.",
         "Each taster has one outcome per possible death round plus survival. Multiply across tasters; unresolved future rounds provide no observations."),
        "Cartesian product of per-taster terminal outcome times.")

    add(234,[49],("מאזנים גם את ענפי ההשערות", "Balance hypothesis branches too"),
        ("תכנון שקילה צריך למזער את הענף הקשה, לא רק לאזן משקלים.", "A weighing plan should minimize its hardest hypothesis branch, not merely balance pan loads."),
        "unknown_weight_minimax",[(dict(n=n),min(max(2*a,2*(n-2*a)) for a in range(1,n//2+1))) for n in [9,6,8,12,5]],
        ("מתוך {n} מטבעות בדיוק אחד כבד או קל מהתקין, ולא יודעים איזה כיוון. בשקילה ראשונה שוקלים a מול a, בלי מטבעי ייחוס. איזה מספר השערות מזערי ניתן להשאיר בענף הגדול ביותר, בבחירה הטובה ביותר של a חיובי?",
         "Among {n} coins exactly one is heavy or light, direction unknown. First weigh a against a, without reference coins. By choosing positive a optimally, what minimum number of hypotheses remains in the largest outcome branch?"),
        ("באי־איזון יש אפשרויות כבד בצד אחד וקל בשני. באיזון המזויף בין מי שלא נשקלו, בשני כיווני המשקל. משווים את גודלי שלושת הענפים.",
         "An imbalance allows heavy on one pan or light on the other. Balance leaves each unweighed coin with both directions. Compare all three branch sizes."),
        "Enumerate every first-pan size and each counterfeit position/direction outcome.")

    game_cases=[(8,[1,3,4]),(7,[1,2]),(10,[1,4]),(9,[2,3]),(6,[1,3])]
    def losing_count(n,moves):
        wins=[False]*(n+1)
        for remaining in range(1,n+1):
            wins[remaining]=any(not wins[remaining-m] for m in moves if m<=remaining)
        return sum(not wins[x] for x in range(1,n+1))
    add(235,[60],("שינוי מהלכים משנה את המצבים המפסידים", "Different moves change losing positions"),
        ("חוק מודולרי מוכר דורש הוכחה מחדש כשהמהלכים המותרים משתנים.", "A familiar modular strategy needs a new proof when permitted moves change."),
        "subtraction_game",[(dict(n=n,moves=ms),losing_count(n,ms)) for n,ms in game_cases],
        ("משחק אבנים: בכל תור מסירים כמות מתוך {moves}, בלי להסיר יותר מהנותר. מי שאין לו מהלך מפסיד. מבין כמויות ההתחלה 1..{n}, כמה הן מצבים מפסידים לשחקן בתורו כששניהם משחקים מיטבית?",
         "In a stone game each turn removes a count from {moves}, never more than remains. A player with no legal move loses. Among starting counts 1..{n}, how many are losing positions for the player to move under optimal play?"),
        ("מצב מנצח אם יש ממנו מהלך למצב מפסיד; אחרת הוא מפסיד. מתחילים מהמצב הריק ובונים בהדרגה, במקום להניח את המחזור של משחק אחר.",
         "A position wins if some legal move reaches a losing one; otherwise it loses. Build from the empty position instead of assuming another game's period."),
        "Finite minimax recurrence, checked independently by full game-tree recursion.")

    assert len(cards)==35 and len(rows)==len(checks)==175
    return cards,rows,checks


def build():
    _,rows,checks=build_bundle()
    return rows,checks


if __name__ == "__main__":
    cards,rows,checks=build_bundle()
    CONTENT.write_text(json.dumps(cards,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for filename,data in (("reasoning_500.json",rows),("reasoning_500.checks.json",checks)):
        (OUT/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("35 reasoning cards / 175 draft variants / 175 case records")
