# VSW-009 — Unique value among duplicates

**כותרת מקורית:** איתור אלמנט יחיד במערך כפילויות (Single Number)

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Company label from supplied text | Marvell |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

נתון מערך שבו כל מספר מופיע בדיוק פעמיים, למעט מספר אחד שמופיע פעם אחת בלבד. מצא את המספר בסיבוכיות זמן של $O(N)$ וזיכרון נוסף של $O(1)$. כיצד תפתור אם כל מספר מופיע 3 פעמים והבודד מופיע פעם אחת?

## Question — English translation

An array contains each number exactly twice, except for one number that appears once. Find that number in O(N) time and O(1) extra space. How would you solve the variant in which every other number appears three times and the unique number appears once?

## מה בודקים — לפי הטקסט המקורי

שימוש בתכונות האלגבריות של XOR ($x \oplus x = 0$), וסכימת ביטים מודולו 3 למקרה המורחב.

## Assessed skills — English translation

The algebraic properties of XOR (x XOR x = 0) and bit sums modulo 3 for the extended variant.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר את הבטחות הקלט ורוחב השלמים, במיוחד למספרים שליליים בגרסת שלושת המופעים. זמן O(N) בגישת ספירת ביטים מניח רוחב מילה קבוע.

## Editorial review notes — separate from the original question

Specify input guarantees and fixed integer width, particularly for negative values in the three-occurrence variant. O(N) for the bit-count approach assumes word width is fixed.

## Provenance / מקור

Supplied Hebrew collection, software question 9. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
