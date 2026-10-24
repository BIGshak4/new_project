# PREP-110 — משווה ביט אחד והרחבה למשווה ארבעה ביטים

פתרון מוצע בסיוע AI. ביקורת מקצועית אנושית ממתינה; הקושי לא כויל.

## מקור

[צילום מקורי](../sources/2026-10-24-batch10-05.png)

א. ממש רכיב המקבל שני ביטים ומוציא שלושה ביטים כפי שמתואר בתמונה.
ב. בעזרת רכיב זה, ממש רכיב המתאר יחס בין שתי כניסות, כל אחת בעלת 4 ביט.
האיור המקורי מסמן a>b, a==b, b<a; הסימון האחרון כפול לראשון ונשמר כאן כלשונו.

חברות מדווחות מהצילום בלבד, ללא אימות עצמאי: Marvell, Apple

## משווה ביט אחד והרחבה למשווה ארבעה ביטים

א. ממשו בשערים רכיב עם שתי כניסות ביט a,b ושלוש יציאות: G המציינת a>b, E המציינת a=b ו־L המציינת a<b. הציגו טבלת אמת ומשוואות.
ב. בעזרת ארבעה רכיבים כאלה ולוגיקה משלימה, השוו שתי מילים A[3:0],B[3:0] ללא סימן. החזירו את שלוש תוצאות ההשוואה והסבירו איזה ביט קובע כאשר כמה ביטים שונים.

הבהרות עריכה: באיור המקור מסומנים a>b, a==b, b<a. הסימון השלישי זהה לראשון, ולכן אינו נותן שלוש אפשרויות השוואה שונות; כאן הוא מתוקן במפורש ל־a<b. אם מפרשים את האיור מילולית, שתי יציאותיו הקיצוניות הן אותו אות. הקלטים בגרסה הערוכה הם בינאריים וללא סימן, ביט 3 הוא המשמעותי ביותר. זהו רכיב קומבינטורי; אין שעון או מחזורי השהיה מוגדרים. מותרות לוגיקה בסיסית וחיווט. אין דרישה למספר שערים מינימלי.

### שלושה רמזים

1. התחילו מארבע אפשרויות הקלט של ביט אחד. באילו מהן יש שוויון, ובאילו יש יתרון לאחד הצדדים?
2. השוו מהביט המשמעותי ביותר. מתי מותר לביט נמוך יותר להשפיע על התוצאה?
3. שמרו אות המציין שכל הביטים הגבוהים שווים. אפשר להוסיף הכרעה מהביט הבא רק כשהאות הזה הוא 1; עדכנו גם את אות השוויון.

### פתרון מוצע

### למה ביט גבוה קודם לביט נמוך?
במספר ללא סימן, משקל ביט גבוה גדול מסכום משקלי כל הביטים שמתחתיו. לכן הביט הגבוה הראשון שבו A ו־B שונים מכריע את כל ההשוואה. אם כל הביטים שווים, המספרים שווים. למשל 1000 גדול מ־0111, למרות שבמספר הימני יש יותר אחדים.

### רכיב של ביט אחד
| a | b | G: a>b | E: a=b | L: a<b |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 0 |
| 0 | 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 0 | 0 |
| 1 | 1 | 0 | 1 | 0 |

המשוואות הן g=a AND NOT b, ‏e=NOT(a XOR b), ‏l=NOT a AND b. בדיוק יציאה אחת דולקת בכל קלט חוקי. שער XNOR הוא דרך ישירה לשוויון, ואפשר לפרקו לשערים בסיסיים אם הספרייה דורשת זאת. אלו אינן יציאות מספריות בנות כמה ביטים, אלא שלושה דגלים.

### ארבעה רכיבים ולוגיקת קדימות
לכל זוג Ai,Bi בונים רכיב ומקבלים gi,ei,li. מתחילים ב־G=0,E=1,L=0, כלומר עדיין לא נבדק הבדל. עוברים i=3,2,1,0 ומעדכנים בו־זמנית לפי הערכים הישנים:

```text
G_next = G OR (E AND gi)
L_next = L OR (E AND li)
E_next = E AND ei
```

אם כבר נמצא הבדל גבוה, E=0 ושום ביט נמוך אינו משנה G או L. אם הגבוהים שווים, E=1 והביט הנוכחי רשאי להכריע. אין כאן שעון: 'עוברים' מתאר חיבור מדורג של ארבעה מקטעים קומבינטוריים. בקוד זהו חישוב המודל.

אפשר גם לפרוש משוואה: G=g3 OR(e3 AND g2) OR(e3 AND e2 AND g1) OR(e3 AND e2 AND e1 AND g0). ל־L אותה משוואה עם li, ו־E=e3 AND e2 AND e1 AND e0. הפירוק מראה מדוע OR של כל gi ללא תנאי שוויון אינו נכון: ביט נמוך לא רשאי לבטל הכרעה גבוהה הפוכה.

### הוכחת נכונות ועלות
אחרי כל תחילית ביטים, שלושת האותות משווים בדיוק את התחיליות שנבדקו. אם התחיליות כבר שונות, הביטים הבאים אינם מכריעים. אם הן שוות, ההשוואה החדשה היא זו של הביט הבא. בסיס הריק הוא שוויון, ולכן באינדוקציה ההשוואה הסופית נכונה. הקלטים 0000,1111, השוויון וההבדל בביט התחתון נכללים באותו כלל.

לרוחב n, שרשרת משתמשת ב־n תאי ביט וב־O(n) לוגיקת צירוף, ועומק לוגי O(n) בספריית שערים בעלת מניפה קבועה. אפשר לשלב קבוצות של (G,E,L) בעץ מאוזן ולקבל O(log n) עומק עם O(n) תאים וצירופים. אין טענה למינימום שטח, הספק או זמן בספרייה פיזית. עבור ארבעה ביטים העלות קבועה.

### תיקון המקור והגבול לחתומים
האיור המקורי מכיל שתי תוויות זהות במשמעות. התיקון מפורש; לא מתיימרים שהמקור כבר ביקש L נפרד. במספרים חתומים במשלים לשתיים, אי אפשר להפעיל השוואה ללא סימן על כל המילה: למשל 1111 הוא 15 ללא סימן אך ‎-1 בחתום. כשביטי הסימן שונים, הסימן מכריע; כשזהים אפשר להשתמש בהשוואת הביטים המתאימה. זו הרחבה, לא החוזה הראשי.

### מה נבדק?
המודל הורץ מול השוואת שלמים עצמאית בכל 5,460 זוגות הקלט לרוחבים 1..6, ובפרט כל 256 הזוגות של ארבעה ביטים. אומתו גם ארבע שורות תא הביט, תנאי בדיוק־אחד ודחיית קלט לא תקין. זו בדיקת לוגיקה בינארית בפייתון, ללא HDL, סינתזה או בדיקת תזמון פיזי.

```python
"""Two-state gates and most-significant-first unsigned comparator cascade."""


def compare_bit(a, b):
    if any(type(v) is not int or v not in (0, 1) for v in (a, b)):
        raise ValueError("expected integer bits")
    return a & (b ^ 1), (a ^ b) ^ 1, (a ^ 1) & b


def compare_words(a, b, width=4):
    if type(width) is not int or width < 1:
        raise ValueError("positive width required")
    if any(type(v) is not int or not 0 <= v < (1 << width) for v in (a, b)):
        raise ValueError("unsigned words outside width")
    greater, equal, less = 0, 1, 0
    for i in range(width - 1, -1, -1):
        gi, ei, li = compare_bit((a >> i) & 1, (b >> i) & 1)
        greater, less = greater | (equal & gi), less | (equal & li)
        equal &= ei
    return greater, equal, less
```

![משווה ביט אחד והרחבה למשווה ארבעה ביטים (prompt)](../diagrams/prep-110-prompt-comparator-he.png)

![משווה ביט אחד והרחבה למשווה ארבעה ביטים (solution)](../diagrams/prep-110-comparator-cascade-he.png)

## One-bit comparator and a four-bit unsigned cascade

A. Build a gate-level component with input bits a,b and outputs G for a>b, E for a=b and L for a<b. Give its truth table and equations.
B. Using four such cells and combining logic, compare unsigned words A[3:0],B[3:0]. Produce the three comparison results and explain which bit decides when several bit positions differ.

Editorial clarifications: the source diagram labels a>b, a==b and b<a. The last is identical to the first, not a third comparison outcome; this edition explicitly corrects it to a<b. A literal implementation of the source would simply duplicate the first output. Inputs are binary and unsigned; bit 3 is most significant. The circuit is combinational, without a clock or specified cycle latency. Basic combining logic and wires are allowed. No minimum gate-count requirement is claimed.

### Three hints

1. Start with the four one-bit input combinations. Which represent equality, and which favor either operand?
2. Compare from the most significant bit. When may a lower bit influence the result?
3. Maintain an all-higher-bits-equal signal. Accept a decision from the next bit only when this signal is one; update equality too.

### Proposed solution

### Why do higher bits take priority?
For unsigned numbers, a high bit outweighs the sum of every lower bit. Therefore the highest differing bit decides the comparison. If no bit differs, the words are equal. For example, 1000 exceeds 0111 even though the latter contains more ones.

### A one-bit cell
| a | b | G: a>b | E: a=b | L: a<b |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 1 | 0 |
| 0 | 1 | 0 | 0 | 1 |
| 1 | 0 | 1 | 0 | 0 |
| 1 | 1 | 0 | 1 | 0 |

Use g=a AND NOT b, e=NOT(a XOR b), l=NOT a AND b. Exactly one output is high for every valid input. XNOR directly provides equality, or may be decomposed when the gate library requires it. These are three Boolean flags, not wider numeric outputs.

### Four cells and priority logic
Build one cell for each Ai,Bi, yielding gi,ei,li. Initialize G=0,E=1,L=0: no difference has yet been seen. Process i=3,2,1,0, updating simultaneously from the old signals:

```text
G_next = G OR (E AND gi)
L_next = L OR (E AND li)
E_next = E AND ei
```

Once a higher difference exists, E=0 and lower bits cannot change the decision. While the higher bits remain equal, E=1 and the current bit may decide. This is a combinational cascade, not four clock cycles; the loop only evaluates its logical model.

Equivalently, G=g3 OR(e3 AND g2) OR(e3 AND e2 AND g1) OR(e3 AND e2 AND e1 AND g0). Replace gi with li for L; E=e3 AND e2 AND e1 AND e0. Simply ORing all gi is wrong because a lower bit must not override an opposite higher-bit decision.

### Correctness and cost
After each prefix, G,E,L compare precisely the processed prefixes. Different prefixes preserve their higher decision; equal prefixes delegate to the next bit. The empty prefix is equal, proving the recurrence by induction. All-zero, all-one, equal words and a difference only at the lowest bit follow the same rule.

An n-bit chain uses n bit cells and O(n) combining logic with O(n) depth in a bounded-fan-in gate library. Combining groups of (G,E,L) in a balanced tree gives O(log n) depth using O(n) cells and combinations. No minimum physical area, power or delay is claimed. Four-bit width has constant cost.

### Source correction and signed values
The source diagram repeats one comparison under two labels. The correction is explicit rather than attributed to the original. Signed two's-complement comparison is a separate contract: 1111 is unsigned 15 but signed -1. Different sign bits decide immediately; matching signs permit the appropriate remaining comparison. The unsigned circuit is not automatically a signed comparator.

### Verification
The actual model was compared with an independent integer-comparison oracle on all 5,460 input pairs for widths 1..6, including all 256 four-bit pairs. Checks also cover all four bit-cell rows, exactly-one output and invalid-input rejection. These are two-state Python checks, not HDL simulation, synthesis or physical timing analysis.

```python
"""Two-state gates and most-significant-first unsigned comparator cascade."""


def compare_bit(a, b):
    if any(type(v) is not int or v not in (0, 1) for v in (a, b)):
        raise ValueError("expected integer bits")
    return a & (b ^ 1), (a ^ b) ^ 1, (a ^ 1) & b


def compare_words(a, b, width=4):
    if type(width) is not int or width < 1:
        raise ValueError("positive width required")
    if any(type(v) is not int or not 0 <= v < (1 << width) for v in (a, b)):
        raise ValueError("unsigned words outside width")
    greater, equal, less = 0, 1, 0
    for i in range(width - 1, -1, -1):
        gi, ei, li = compare_bit((a >> i) & 1, (b >> i) & 1)
        greater, less = greater | (equal & gi), less | (equal & li)
        equal &= ei
    return greater, equal, less
```

![One-bit comparator and a four-bit unsigned cascade (prompt)](../diagrams/prep-110-prompt-comparator-en.png)

![One-bit comparator and a four-bit unsigned cascade (solution)](../diagrams/prep-110-comparator-cascade-en.png)

## חומר משלים / Supporting material

```json
{
  "assumptions": {
    "he": [
      "קלט בינארי ללא סימן; ביט 3 הוא המשמעותי ביותר.",
      "L מוגדר במפורש a<b במקום התווית הכפולה b<a במקור.",
      "מותרות לוגיקה משלימה וחיווט; רכיב קומבינטורי ללא דרישת מינימום שערים."
    ],
    "en": [
      "Binary unsigned inputs; bit 3 is most significant.",
      "L explicitly means a<b, correcting the duplicated source label b<a.",
      "Combining logic and wires allowed; combinational circuit, no minimum gate-count claim."
    ]
  },
  "optimality": {
    "he": "מוצגת בנייה לינארית במספר תאי הביט; לא הוכחה למינימום שערים. עץ צירוף מאפשר עומק לוגריתמי במודל מניפה קבועה.",
    "en": "The construction uses a linear number of bit cells; it does not establish a minimum gate count. A balanced combination tree permits logarithmic depth with bounded fan-in."
  },
  "edge_cases": {
    "he": [
      "שוויון, אפסים, וכל הביטים אחד.",
      "הבדל בביט העליון מול הרבה הבדלים נמוכים בכיוון ההפוך.",
      "הבדל בביט התחתון בלבד; קלט חתום דורש חוזה אחר."
    ],
    "en": [
      "Equal words, all zero and all one.",
      "A highest-bit difference versus many opposite lower differences.",
      "A difference only at the lowest bit; signed input requires another contract."
    ]
  },
  "common_mistakes": {
    "he": [
      "לחבר את כל תוצאות גדול ב־OR בלי בדיקת שוויון של הגבוהים.",
      "לעדכן E לפני שחישבתם G_next,L_next מהערכים הישנים.",
      "לתאר ארבעה תאי השוואה קומבינטוריים כארבעה מחזורי שעון."
    ],
    "en": [
      "ORing all greater outputs without higher-bit equality.",
      "Updating E before computing G_next,L_next from the old values.",
      "Calling a four-cell combinational cascade four clock cycles."
    ]
  },
  "interview_answer": {
    "he": "לתא ביט: g=a·¬b, e=¬(a⊕b), l=¬a·b. מחברים ארבעה תאים מהמשמעותי לפחות משמעותי. כל הכרעה נמוכה מותנית בשוויון כל הגבוהים; בדיוק דגל אחד דולק.",
    "en": "For one bit use g=a·¬b, e=¬(a⊕b), l=¬a·b. Combine four cells from most to least significant, admitting a lower decision only if every higher bit is equal. Exactly one flag is high."
  },
  "source_ambiguities": {
    "he": "התווית b<a כפולה ל־a>b; תוקנה ל־a<b בעריכה. המקור לא קובע חתימות, ספריית שערים או עלות מינימלית. ההנחות נוספו במפורש.",
    "en": "The source label b<a duplicates a>b; this edition corrects it to a<b. Signedness, gate library and minimum cost were unspecified and are explicitly clarified."
  },
  "verification": {
    "he": "5,460 זוגות ברוחבים 1..6, בהם כל 256 זוגות ארבעת הביטים, הושוו להשוואות שלמים נפרדות; אומתו דגל יחיד וקלט שגוי. מודל Python בלבד.",
    "en": "5,460 pairs across widths 1..6, including all 256 four-bit pairs, matched independent integer comparisons; exactly-one and invalid inputs checked. Python model only."
  },
  "solution_extensions": {
    "he": {
      "question": "איך מקצרים את עומק השרשרת ברוחב גדול?",
      "direction": "הגדירו לכל קבוצת ביטים G,E,L; צירוף קבוצה גבוהה ונמוכה הוא G=Gh OR(Eh AND Gl), E=Eh AND El, L=Lh OR(Eh AND Ll). בנו עץ מאוזן."
    },
    "en": {
      "question": "How can a wide comparison avoid linear cascade depth?",
      "direction": "Represent each group by G,E,L. Combine high and low groups as G=Gh OR(Eh AND Gl), E=Eh AND El, L=Lh OR(Eh AND Ll), using a balanced tree."
    }
  }
}
```
