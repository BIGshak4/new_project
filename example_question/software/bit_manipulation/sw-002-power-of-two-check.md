# SW-002 — Recognize a power of two

**כותרת בעברית:** זיהוי חזקה של שתיים

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Difficulty | 2/10 (provisional) |
| Estimated time | 5 minutes |
| Format | code |
| Modes | quick |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Write a test for whether an unsigned 32-bit integer x is a power of two, using a constant number of bitwise/arithmetic operations and no loop. Define 1 as a power of two and 0 as not. Explain your expression and evaluate 0,1,12,16, and 0x80000000.

## שאלה — עברית

כתבו בדיקה האם מספר שלם x ללא סימן ברוחב 32 ביטים הוא חזקה של שתיים, באמצעות מספר קבוע של פעולות ביטיות או חשבוניות וללא לולאה. הגדירו 1 כחזקה של שתיים ו־0 כלא. הסבירו את הביטוי ובדקו 0,1,12,16, 0x80000000.

## Hint — English

A power of two has exactly one 1 bit.

## רמז — עברית

לחזקה של שתיים יש בדיוק ביט 1 אחד.

## Reference solution — English

x!=0 && (x & (x-1))==0. A positive power of two has exactly one set bit. Results: false,true,false,true,true. The nonzero guard prevents accepting 0.

## כיוון פתרון — עברית

הביטוי הוא x!=0 && (x & (x-1))==0. לחזקה חיובית של שתיים יש בדיוק ביט 1 יחיד. התוצאות: false,true,false,true,true. התנאי השולל אפס מונע קבלה שגויה שלו.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [Python documentation: integer and bitwise operations](https://docs.python.org/3/library/stdtypes.html)
