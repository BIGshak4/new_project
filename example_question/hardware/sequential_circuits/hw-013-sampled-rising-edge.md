# HW-013 — One-cycle sampled rising-edge pulse

**כותרת בעברית:** פולס של מחזור אחד לזיהוי עלייה

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Sequential circuits / מעגלים סינכרוניים |
| Difficulty | 3/10 (provisional) |
| Estimated time | 8 minutes |
| Format | waveform |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Input x is synchronous to clk. At each rising edge, update registered pulse to 1 if the newly sampled x is 1 and the previous sample was 0; otherwise update it to 0. Store the current sample for next time. Reset both registers synchronously to 0. After reset, x samples are 0,1,1,0,1. Give pulse after each edge and explain why a continuously high x produces only one pulse.

## שאלה — עברית

הקלט x סינכרוני לשעון clk. בכל חזית עולה עדכנו פלט רשום pulse ל־1 אם הדגימה הנוכחית של x היא 1 והקודמת הייתה 0; אחרת עדכנו ל־0. שמרו את הדגימה הנוכחית לפעם הבאה. שני האוגרים מתאפסים סינכרונית ל־0. לאחר האיפוס דגימות x הן 0,1,1,0,1. תנו את pulse אחרי כל חזית והסבירו מדוע x שנשאר גבוה יוצר פולס יחיד.

## Hint — English

The stored previous value must refer to the preceding edge.

## רמז — עברית

הערך previous צריך להתייחס לחזית הקודמת.

## Reference solution — English

Use pulse <= x & ~previous and previous <= x with nonblocking assignments. The pulse trace is 0,1,0,0,1. A sustained high input has previous=1 after its first high sample.

## כיוון פתרון — עברית

משתמשים בהשמות לא חוסמות: pulse <= x & ~previous וגם previous <= x. עקבת pulse היא 0,1,0,0,1. לאחר הדגימה הגבוהה הראשונה, previous שווה 1 ולכן קלט שנשאר גבוה אינו יוצר פולס נוסף.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: edge detection background](https://hdlbits.01xz.net/wiki/Edgedetect)
