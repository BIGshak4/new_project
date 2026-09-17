# VHW-017 — CMOS gate and transition characteristics

**כותרת מקורית:** שער CMOS ומאפייני מעבר

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Cells and hardware architecture / מבנה תאים וארכיטקטורת חומרה |
| Company label from supplied text | Qualcomm |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

שרטט שער NAND של 2 כניסות ברמת הטרנזיסטור (CMOS: רשת Pull-Up ורשת Pull-Down). מדוע הטרנזיסטורים ב-PMOS מחוברים במקביל וה-NMOS בטור? מדוע טרנזיסטור PMOS מתוכנן ברוחב (W) כפול מ-NMOS?

## Question — English translation

Draw a two-input NAND gate at transistor level, including the CMOS pull-up and pull-down networks. Why are the PMOS transistors connected in parallel and the NMOS transistors in series? Why is a PMOS transistor designed with a width W twice that of an NMOS transistor?

## מה בודקים — לפי הטקסט המקורי

הבנת ניידות נושאי מטען (Mobility של אלקטרונים מול חורים) ואיזון זמני Rise/Fall.

## Assessed skills — English translation

Understanding carrier mobility (electrons versus holes) and balancing rise and fall times.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יחס רוחב PMOS ל־NMOS של בדיוק שתיים אינו כלל אוניברסלי, בפרט ב־NAND עם NMOS בטור. יש לשאול על חוזק הנעה תלוי־תהליך ועל sizing יחסי לפי מודל ייחוס מוגדר.

## Editorial review notes — separate from the original question

A PMOS-to-NMOS width ratio of exactly two is not a universal rule, particularly in a NAND with series NMOS devices. Ask about process-dependent drive strength and relative sizing under a stated reference model.

Technical background: [MIT: CMOS technology](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c3/c3s1/). This is not company-attribution evidence.

## Provenance / מקור

Supplied Hebrew collection, hardware question 17. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
