# VHW-019 — Synchronous versus asynchronous reset

**כותרת מקורית:** מנגנון איפוס – Synchronous vs. Asynchronous Reset

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Cells and hardware architecture / מבנה תאים וארכיטקטורת חומרה |
| Company label from supplied text | NVIDIA |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

השווה בין Reset סינכרוני ל-Reset אסינכרוני עם שחרור סינכרוני (Asynchronous Assert, Synchronous Deassert). מה הסכנה בשחרור אסינכרוני של איפוס בסמוך לקצה שעון (Recovery and Removal Violations)?

## Question — English translation

Compare a synchronous reset with a reset that asserts asynchronously and deasserts synchronously. What is the danger of asynchronously releasing reset near a clock edge, in terms of recovery and removal violations?

## מה בודקים — לפי הטקסט המקורי

אמינות תהליך ה-Boot וה-Power-On של המערכת.

## Assessed skills — English translation

Reliability of system boot and power-on behavior.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר זמינות שעון בזמן האיפוס ושחרור בכל תחום שעון. שחרור מסונכרן דורש סנכרון מתאים בכל תחום יעד.

## Editorial review notes — separate from the original question

Specify clock availability during reset and per-domain reset release. A synchronously deasserted reset requires appropriate synchronization in each destination domain.

## Provenance / מקור

Supplied Hebrew collection, hardware question 19. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
