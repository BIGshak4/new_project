# VHW-015 — Clock recovery and clock gating

**כותרת מקורית:** שחזור שעון ו-Clock Gating

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Timing, STA, and CDC / תזמון, ניתוח תזמון ומעבר בין שעונים |
| Company label from supplied text | Marvell |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

כיצד פועל תא Integrated Clock Gating (ICG)? מדוע לא מומלץ לחבר ישירות שער AND בין קו השעון לאות ה-Enable? שרטט את מבנה ה-Latch-based ICG ומנע גליצ'ים.

## Question — English translation

How does an integrated clock-gating (ICG) cell work? Why is directly connecting an AND gate between the clock and an Enable signal not recommended? Draw a latch-based ICG structure that prevents glitches.

## מה בודקים — לפי הטקסט המקורי

אופטימיזציית הספק (Dynamic Power Reduction) ללא פגיעה בשלמות השעון.

## Assessed skills — English translation

Reducing dynamic power without compromising clock integrity.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

הכותרת מזכירה שחזור שעון, אך השאלה עוסקת ב־clock gating. יש להגדיר קוטביות שעון ואת שלב השקיפות של ה־latch; עדיין חלים אילוצי תזמון של clock gating.

## Editorial review notes — separate from the original question

The heading mentions clock recovery, but the prompt is about clock gating. Specify clock polarity and latch transparency phase; clock-gating setup/hold checks still apply.

## Provenance / מקור

Supplied Hebrew collection, hardware question 15. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
