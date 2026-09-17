# VHW-002 — Parity generator

**כותרת מקורית:** גלאי זוגיות (Parity Generator)

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Digital logic and clocking / לוגיקה ספרתית ושעונים |
| Company label from supplied text | Apple |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

תכנן מעגל קומבינטורי שמקבל וקטור של 8 ביט ומפיק '1' אם מספר האחדות בוקטור הוא אי-זוגי. מהו עומק הלוגיקה (Logic Depth) המינימלי שניתן להשיג, וכיצד תבנה עץ שערים אופטימלי למהירות?

## Question — English translation

Design a combinational circuit that receives an eight-bit vector and outputs 1 if the number of set bits is odd. What is the minimum achievable logic depth, and how would you build a gate tree optimized for speed?

## מה בודקים — לפי הטקסט המקורי

הבנה של עצי שערים (XOR trees), השפעת עומק לוגי על Delay, ואיזון מסלולים.

## Assessed skills — English translation

Understanding XOR trees, the effect of logic depth on delay, and path balancing.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר fan-in מותר ומודל השהיות לפני בקשת עומק מינימלי. בשערי XOR בעלי שני קלטים, לעץ מאוזן של שמונה קלטים יש שלוש רמות XOR.

## Editorial review notes — separate from the original question

Specify permitted gate fan-in and the delay model before asking for minimum depth. With two-input XOR gates, a balanced eight-input parity tree has three XOR levels.

## Provenance / מקור

Supplied Hebrew collection, hardware question 2. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
