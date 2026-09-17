# VHW-008 — Pattern detector allowing one bit error

**כותרת מקורית:** גלאי דפוס עם שגיאה אחת מותרת (Fault-Tolerant Detector)

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Company label from supplied text | Amazon (Annapurna Labs) |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

תכנן FSM המקבל זרם ביטים ומזהה הגעת מילת סינכרון באורך 4 ביט (`1101`), כאשר מותרת שגיאה של לכל היותר ביט אחד (מרחק המינג $\le 1$). הגדר דיאגרמת מצבים מינימלית.

## Question — English translation

Design an FSM that receives a bit stream and detects a four-bit synchronization word, 1101, while allowing at most one bit error (Hamming distance <= 1). Define a minimal state diagram.

## מה בודקים — לפי הטקסט המקורי

פירוק בעיה לא טריוויאלית, הגדרת מרחב מצבים ללא פיצוץ קומבינטורי, ואימות תנאי גבול.

## Assessed skills — English translation

Decomposing a nontrivial problem, defining the state space without combinatorial explosion, and checking boundary conditions.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

מספר המצבים המינימלי תלוי בזיהוי בחלון נע או במילים מיושרות, בחפיפה, בתזמון הפלט ובאיפוס. יש לקבע זאת לפני דרישת מינימליות, ולבקש נימוק למינימליות אם נותנים עליה ציון.

## Editorial review notes — separate from the original question

Minimal state count depends on sliding-window versus aligned-word detection, overlap, output timing, and reset semantics. Fix these before requiring a minimal machine; require a minimality argument if minimality is scored.

## Provenance / מקור

Supplied Hebrew collection, hardware question 8. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
