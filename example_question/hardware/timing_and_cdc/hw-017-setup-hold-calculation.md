# HW-017 — Setup and hold constraints

**כותרת בעברית:** חישוב אילוצי Setup ו־Hold

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Timing and clock-domain crossing / תזמון ומעבר בין תחומי שעון |
| Difficulty | 5/10 (provisional) |
| Estimated time | 10 minutes |
| Format | short_answer |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

For a register-to-register path, clock-to-Q max/min are 0.12/0.05 ns, combinational delay max/min are 1.10/0.08 ns, setup is 0.18 ns, and hold is 0.10 ns. Assume zero skew, zero jitter, and no additional uncertainty. Find the minimum clock period, maximum frequency, and hold slack. Does reducing frequency repair a hold violation?

## שאלה — עברית

במסלול בין שני אוגרים, זמני clock-to-Q המרבי והמזערי הם 0.12/0.05 ננו־שניות, והשהיות הלוגיקה המרבית והמזערית הן 1.10/0.08 ננו־שניות. זמן setup הוא 0.18 ננו־שניות וזמן hold הוא 0.10 ננו־שניות. הניחו skew ואי־ודאות אפס, ללא jitter. חשבו זמן מחזור מזערי, תדר מרבי ו־hold slack. האם הורדת התדר מתקנת הפרת hold?

## Hint — English

Use maximum delays for setup and minimum delays for hold.

## רמז — עברית

השתמשו בהשהיות מרביות ל־setup ובמזעריות ל־hold.

## Reference solution — English

Tmin=0.12+1.10+0.18=1.40 ns; fmax is about 714.3 MHz. Hold slack=0.05+0.08-0.10=+0.03 ns, so this path passes hold. Hold concerns the same capture edge; lowering frequency does not repair such a minimum-delay violation under these assumptions.

## כיוון פתרון — עברית

זמן המחזור המזערי הוא 0.12+1.10+0.18=1.40 ננו־שניות; התדר המרבי כ־714.3 מגה־הרץ. מרווח hold הוא 0.05+0.08-0.10=+0.03 ננו־שניות, ולכן האילוץ מתקיים. בדיקת hold מתייחסת לאותה חזית קליטה; הורדת התדר אינה מתקנת הפרת השהיה מזערית בהנחות האלה.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [MIT 6.004: sequential logic and timing](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c5/c5s1/)
