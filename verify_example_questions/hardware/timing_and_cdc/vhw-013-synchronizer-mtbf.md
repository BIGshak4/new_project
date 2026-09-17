# VHW-013 — Two-stage synchronizer and MTBF

**כותרת מקורית:** מסנכרן דו-שלבי ו-MTBF

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Timing, STA, and CDC / תזמון, ניתוח תזמון ומעבר בין שעונים |
| Company label from supplied text | Amazon (Annapurna Labs) |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

מדוע מסנכרן של שני פליפ-פלופים (2-FF Synchronizer) פותר מטא-סטביליות עבור אות בקרה של ביט בודד? מהו MTBF (Mean Time Between Failures), ומדוע אסור להשתמש ב-2-FF Sync עבור אות מרובה ביטים (Bus)?

## Question — English translation

Why does a two-flip-flop synchronizer (2-FF synchronizer) solve metastability for a single-bit control signal? What is MTBF (mean time between failures), and why must a 2-FF synchronizer not be used for a multibit signal (bus)?

## מה בודקים — לפי הטקסט המקורי

פיזיקה של מטא-סטביליות, הסתברות לקריסת אות, ושיטות מבוססות Handshake / FIFO להעברת Bus.

## Assessed skills — English translation

The physics of metastability, the probability of signal failure, and handshake- or FIFO-based approaches for transferring a bus.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

בגרסה מתוקנת יש להחליף "פותר מטא־סטביליות" ב־"מקטין את ההסתברות להתפשטות מטא־סטביליות". מסנכרנים נפרדים לכל ביט אינם משמרים קוהרנטיות של bus שרירותי; זה מדויק יותר מאיסור גורף על כל שימוש רב־ביטי. יש להגדיר יציבות אות ודרישות קליטת אירועים.

## Editorial review notes — separate from the original question

Replace "solves metastability" in a future reviewed revision with "reduces the probability of metastability propagating." Independent per-bit synchronizers do not preserve arbitrary bus coherence; this is more precise than a blanket prohibition on all multibit uses. Specify signal stability and event-capture requirements.

Technical background: [Nandland: metastability](https://nandland.com/lesson-13-metastability/). This is not company-attribution evidence.

## Provenance / מקור

Supplied Hebrew collection, hardware question 13. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
