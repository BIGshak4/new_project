# VHW-016 — Latch versus flip-flop

**כותרת מקורית:** Latch לעומת Flip-Flop

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Cells and hardware architecture / מבנה תאים וארכיטקטורת חומרה |
| Company label from supplied text | Intel |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

מהו ההבדל המבני והתפקודי בין D-Latch (Level-sensitive) לבין D-Flip-Flop (Edge-triggered)? כיצד בונים Edge-triggered Flip-Flop מ-Master-Slave Latches? מהם הסיכונים בשימוש בלתי מכוון ב-Latches בקוד RTL?

## Question — English translation

What are the structural and functional differences between a level-sensitive D latch and an edge-triggered D flip-flop? How can an edge-triggered flip-flop be built from master-slave latches? What are the risks of unintentionally using latches in RTL?

## מה בודקים — לפי הטקסט המקורי

מניעת יצירת Latches לא רצויים בסינתזה כתוצאה מ-`if` או `case` לא מלאים.

## Assessed skills — English translation

Preventing unwanted latch inference during synthesis caused by incomplete if or case statements.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר רמה פעילה וקוטביות חזית בשרטוט master-slave. תכנון מכוון מבוסס latches הוא תקין; הבעיה היא אגירה לא מכוונת או מודל תזמון שלא נותח.

## Editorial review notes — separate from the original question

Specify active level and edge polarity when drawing master-slave latches. Intentional latch-based design is valid; the concern is unintended storage or an unanalysed timing model.

Technical background: [MIT: latches and registers](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c5/c5s1/). This is not company-attribution evidence.

## Provenance / מקור

Supplied Hebrew collection, hardware question 16. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
