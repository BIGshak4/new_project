# VSW-002 — Power-of-two test and highest set bit

**כותרת מקורית:** זיהוי חזקה של 2 ומציאת הביט הגבוה ביותר (MSB)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Company label from supplied text | Google |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

כתוב ביטוי בוליאני בשורה אחת הבודק האם מספר שלם הוא חזקה מדויקת של 2. בנוסף, מצא את האינדקס של ה-Most Significant Bit הדולק ב-$O(1)$ או $O(\log N)$.

## Question — English translation

Write a one-line Boolean expression that determines whether an integer is an exact power of two. Also find the index of its most significant set bit (MSB) in O(1) or O(log N) time.

## מה בודקים — לפי הטקסט המקורי

אלגנטיות קוד, הבנת ייצוג בינארי ומספרים שליליים (משלים ל-2).

## Assessed skills — English translation

Code clarity, binary representation, and negative numbers in two's complement.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר סימן, רוחב מילה W, טיפול באפס ומספור אינדקס MSB מאפס או מאחד. יש להבהיר האם N הוא הערך המספרי או רוחב המילה והאם מותרות פקודות bit-scan מובנות.

## Editorial review notes — separate from the original question

Define signedness, word width W, zero handling, and whether MSB indexing starts at zero. Clarify whether N means the numeric value or word width and whether hardware bit-scan intrinsics are permitted.

## Provenance / מקור

Supplied Hebrew collection, software question 2. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
