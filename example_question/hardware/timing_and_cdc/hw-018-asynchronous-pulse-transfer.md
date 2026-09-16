# HW-018 — A pulse crossing into a slower clock

**כותרת בעברית:** העברת פולס לתחום שעון איטי

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Timing and clock-domain crossing / תזמון ומעבר בין תחומי שעון |
| Difficulty | 5/10 (provisional) |
| Estimated time | 10 minutes |
| Format | explain |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

A source clock is 100 MHz and a destination clock is 25 MHz with unrelated phase. A source event is high for one source cycle. Someone proposes two destination-clock flip-flops in series. Explain whether every event is guaranteed to arrive, distinguish pulse loss from metastability, and propose a handshake that guarantees delivery if the source waits for acknowledgement before sending another event.

## שאלה — עברית

שעון המקור הוא 100 מגה־הרץ ושעון היעד הוא 25 מגה־הרץ, עם מופע לא קשור. אירוע המקור גבוה במשך מחזור מקור יחיד. מוצע להעבירו דרך שני flip-flops בטור הפועלים בשעון היעד. האם כל אירוע מובטח להגיע? הבדילו בין אובדן פולס ל־metastability והציעו handshake המבטיח העברה אם המקור ממתין לאישור לפני האירוע הבא.

## Hint — English

Compare pulse width with destination sampling interval.

## רמז — עברית

השוו את רוחב הפולס למרווח בין דגימות היעד.

## Reference solution — English

A 10 ns pulse can fall entirely between 40 ns destination edges. Two flops reduce metastability propagation probability but do not guarantee pulse capture or eliminate metastability. Hold a request until a synchronized acknowledgement returns; synchronize each crossing and complete the return-to-zero handshake before reusing it.

## כיוון פתרון — עברית

פולס של 10 ננו־שניות יכול להופיע כולו בין חזיתות יעד המרוחקות 40 ננו־שניות. שני אוגרים מקטינים את הסתברות התפשטות metastability, אך אינם מבטיחים קליטת פולס או מבטלים metastability. מחזיקים בקשה עד שחוזר אישור מסונכרן; מסנכרנים כל מעבר ומשלימים handshake של חזרה לאפס לפני אירוע חדש.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [Nandland: metastability](https://nandland.com/lesson-13-metastability/)
