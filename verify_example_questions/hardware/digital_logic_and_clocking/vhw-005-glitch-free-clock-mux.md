# VHW-005 — Glitch-free clock multiplexer

**כותרת מקורית:** מניעת גליצ'ים (Glitch-free Clock Mux)

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Digital logic and clocking / לוגיקה ספרתית ושעונים |
| Company label from supplied text | Google |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

נתונים שני שעונים אסינכרוניים, $Clk_A$ ו-$Clk_B$, וסיגנל בחירה $Select$. תכנן מעגל הממתג בין השעונים ללא ייצור שברי שעון (runt pulses) או גליצ'ים במוצא.

## Question — English translation

Given two asynchronous clocks, Clk_A and Clk_B, and a Select signal, design a circuit that switches between the clocks without generating runt pulses or glitches at the output.

## מה בודקים — לפי הטקסט המקורי

הבנה עמוקה של שעוני חומרה, סנכרון רב-שלבי, ומניעת תופעות מעבר הרסניות.

## Assessed skills — English translation

A deep understanding of hardware clocks, multistage synchronization, and prevention of destructive switching transients.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש לציין אם שני השעונים רציפים, אם מותר מרווח נמוך ממושך ואם החלפה חייבת להסתיים גם כששעון נעצר. יש להגדיר רכיבי סנכרון ומיתוג שעון מותרים.

## Editorial review notes — separate from the original question

State whether both clocks run continuously, whether an extended low interval is allowed, and whether completion is required when a clock stops. Define the synchronization and clock-gating cells permitted.

## Provenance / מקור

Supplied Hebrew collection, hardware question 5. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
