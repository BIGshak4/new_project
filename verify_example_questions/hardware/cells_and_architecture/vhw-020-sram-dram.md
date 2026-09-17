# VHW-020 — SRAM versus DRAM memory design

**כותרת מקורית:** תכנון זיכרון SRAM לעומת DRAM

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Cells and hardware architecture / מבנה תאים וארכיטקטורת חומרה |
| Company label from supplied text | Apple |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

הסבר את המבנה של תא 6T SRAM לעומת תא 1T DRAM. מדוע רגיסטרים ו-L1 Caches ממומשים ב-SRAM, ומהן פעולות ה-Precharge וה-Sense Amplifier במהלך קריאה?

## Question — English translation

Explain the structure of a 6T SRAM cell versus a 1T DRAM cell. Why are registers and L1 caches implemented in SRAM, and what do precharge and the sense amplifier do during a read?

## מה בודקים — לפי הטקסט המקורי

זיכרונות פנימיים בשבב, זמני גישה, ומגבלות שטח מול מהירות.

## Assessed skills — English translation

On-chip memories, access times, and area-versus-speed constraints.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

לתא DRAM קונבנציונלי יש לציין 1T1C. האמירה שאוגרים ממומשים ב־SRAM רחבה מדי: יש להבחין בין אוגרי מצב רגילים, register files ומערכי cache. יש להפריד בין מנגנוני precharge וקריאה של הטכנולוגיות.

## Editorial review notes — separate from the original question

Use 1T1C for the conventional DRAM cell. The claim that registers are implemented in SRAM is too broad: distinguish ordinary state registers, register files, and cache arrays. Clarify the precharge/read mechanism separately for each memory technology.

Technical background: [MIT: memory technologies and caches](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c14/c14s1/). This is not company-attribution evidence.

## Provenance / מקור

Supplied Hebrew collection, hardware question 20. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
