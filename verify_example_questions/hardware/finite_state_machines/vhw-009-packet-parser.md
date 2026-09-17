# VHW-009 — Packet header parser

**כותרת מקורית:** מפענח חבילות פרוטוקול (Packet Header Parser)

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Company label from supplied text | Apple |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

ממש FSM המקבל בייט בכל מחזור שעון ומפענח חבילה בעלת מבנה: Preamble (0xAA) $\to$ Length (N בייטים) $\to$ Payload (N בייטים) $\to$ Checksum (בייט אחד). כיצד המכונה מסתנכרנת מחדש אם ה-Checksum שגוי?

## Question — English translation

Implement an FSM that receives one byte per clock cycle and parses a packet with this structure: Preamble (0xAA), then Length (N bytes), then Payload (N bytes), then Checksum (one byte). How does the machine resynchronize if the checksum is incorrect?

## מה בודקים — לפי הטקסט המקורי

תכנון ממשקי תקשורת חומרתיים, שילוב מונה (Counter) עם בקרת מצבים, וטיפול בשגיאות מסגרת.

## Assessed skills — English translation

Designing hardware communication interfaces, combining a counter with state control, and handling framing errors.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

הניסוח המקורי "Length (N בייטים)" עמום: האם N הוא אורך המטען או רוחב שדה האורך? יש להגדיר רוחב שדה, N=0, אלגוריתם checksum והכיסוי שלו, escaping של 0xAA במטען ומדיניות סנכרון מחדש. התרגום לאנגלית שומר את העמימות המקורית.

## Editorial review notes — separate from the original question

The original phrase "Length (N bytes)" is ambiguous: N may be the payload length or the byte width of the length field. Define field width, N=0, checksum algorithm and coverage, escaping of 0xAA in payload, and the resynchronization policy. The English translation preserves this ambiguity.

## Provenance / מקור

Supplied Hebrew collection, hardware question 9. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
