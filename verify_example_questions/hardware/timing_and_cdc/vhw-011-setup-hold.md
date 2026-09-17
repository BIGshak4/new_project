# VHW-011 — Basic setup and hold calculations

**כותרת מקורית:** חישובי Setup ו-Hold בסיסיים

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Timing, STA, and CDC / תזמון, ניתוח תזמון ומעבר בין שעונים |
| Company label from supplied text | Apple |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

נתונים שני פליפ-פלופים עם קו שעון משותף. נתון: $T_{clk}=10\text{ns}$, $T_{cq}=2\text{ns}$, $T_{setup}=1.5\text{ns}$, $T_{hold}=1\text{ns}$, ו-Skew מרבי של $0.8\text{ns}$.
מהו תחום הזמנים המותר (מינימלי ומקסימלי) עבור עיכוב הלוגיקה הקומבינטורית ($T_{comb}$) בין שני הפלופים למניעת Setup Violation ו-Hold Violation?

## Question — English translation

Two flip-flops share a clock source. Given T_clk = 10 ns, T_cq = 2 ns, T_setup = 1.5 ns, T_hold = 1 ns, and a maximum skew of 0.8 ns, what is the allowed range, minimum and maximum, of the combinational logic delay T_comb between the flip-flops to avoid setup and hold violations?

## מה בודקים — לפי הטקסט המקורי

הבנה מתמטית מדויקת של משוואות תזמון ומשמעות Clock Skew.

## Assessed skills — English translation

Precise mathematical understanding of timing equations and the meaning of clock skew.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להגדיר skew כהפרש בין זמן הגעת שעון הקליטה לזמן הגעת שעון השיגור, ולהבחין בין clock-to-Q מינימלי ומקסימלי ובין השהיות לוגיקה מינימליות ומקסימליות. אם skew בטווח [-0.8,+0.8] ננו־שניות ו־clock-to-Q הוא בדיוק 2 ננו־שניות במודל הפשוט, setup דורש T_comb,max <= 5.7 ננו־שניות ו־hold דורש T_comb,min >= -0.2 ננו־שניות; כל השהיה מינימלית לא שלילית מקיימת hold. פירושים אחרים משנים את התוצאה.

## Editorial review notes — separate from the original question

Define signed skew as capture-clock arrival minus launch-clock arrival, and distinguish minimum from maximum clock-to-Q and combinational delays. If skew can be anywhere in [-0.8,+0.8] ns and clock-to-Q is exactly 2 ns in this simplified model, setup gives T_comb,max <= 5.7 ns and hold gives T_comb,min >= -0.2 ns; any nonnegative minimum delay passes hold. Other interpretations change the answer.

Technical background: [MIT: sequential logic and timing](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c5/c5s1/). This is not company-attribution evidence.

## Provenance / מקור

Supplied Hebrew collection, hardware question 11. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
