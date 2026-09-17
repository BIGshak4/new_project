# VHW-004 — Frequency division without a phase-locked loop

**כותרת מקורית:** חלוקת תדר ללא Phase Locked Loop (PLL)

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Digital logic and clocking / לוגיקה ספרתית ושעונים |
| Company label from supplied text | Amazon (Annapurna Labs) |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

נתון שעון ראשי בתדר $F$. תכנן מעגל סינכרוני המייצר שעון חדש בתדר $F/3$ עם Duty Cycle של בדיוק 50%. (רמז: שימוש בשני קצוות השעון – חיובי ושלילי).

## Question — English translation

Given a main clock of frequency F, design a synchronous circuit that generates a new clock of frequency F/3 with an exactly 50% duty cycle. Hint: use both the rising and falling edges of the clock.

## מה בודקים — לפי הטקסט המקורי

עבודה עם שני קצוות שעון (posedge/negedge), מעגלי חלוקה אי-זוגיים, ומניעת גליצ'ים.

## Assessed skills — English translation

Working with both clock edges (posedge/negedge), odd clock dividers, and glitch prevention.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר duty cycle של הקלט, התנהגות איפוס והאם מדובר במודל תזמון אידאלי או במימוש פיזי. הדרישה ל־50% תלויה בהנחות אלה; שימוש בשתי חזיתות יוצר גם מסלולי תזמון של חצי מחזור.

## Editorial review notes — separate from the original question

Specify input duty cycle, reset behavior, and an ideal timing model versus real implementation tolerances. The 50% output claim depends on these assumptions; using both edges also introduces half-cycle timing paths.

## Provenance / מקור

Supplied Hebrew collection, hardware question 4. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
