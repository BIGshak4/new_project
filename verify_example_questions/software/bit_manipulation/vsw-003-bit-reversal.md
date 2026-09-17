# VSW-003 — Bit reversal

**כותרת מקורית:** הפיכת סדר ביטים (Bit Reversal)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Company label from supplied text | NVIDIA |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

נתון משתנה בגודל 32 ביט. הפוך את סדר הביטים שלו (ביט 0 מתחלף עם ביט 31, ביט 1 עם 30 וכו'). פתור את הבעיה בגישת Divide and Conquer באמצעות מסכות (Masks) והזזות (Shifts) ב-$O(\log(\text{word\_size}))$.

## Question — English translation

Given a 32-bit variable, reverse its bit order: bit 0 swaps with bit 31, bit 1 with bit 30, and so on. Solve the problem with a divide-and-conquer approach using masks and shifts in O(log(word_size)) time.

## מה בודקים — לפי הטקסט המקורי

חשיבה מקבילית של מניפולציות ביטים ללא לולאות איטיות.

## Assessed skills — English translation

Parallel thinking about bit manipulation without slow per-bit loops.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להשתמש באופרנדים ללא סימן וברוחב מפורש של 32 ביטים. באלגוריתם הכללי מספר השלבים לוגריתמי ברוחב; עבור 32 ביטים יש חמישה שלבי מסכות והחלפות.

## Editorial review notes — separate from the original question

Use unsigned operands and an explicit 32-bit width. The generalized algorithm has logarithmic stages in word width; for the fixed 32-bit exercise there are five mask/swap stages.

## Provenance / מקור

Supplied Hebrew collection, software question 3. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
