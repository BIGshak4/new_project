# VHW-012 — Fixing timing violations

**כותרת מקורית:** תיקון הפרות תזמון (Violations Fixing)

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Timing, STA, and CDC / תזמון, ניתוח תזמון ומעבר בין שעונים |
| Company label from supplied text | NVIDIA |
| Company attribution | Unverified; not evidence that this company asked this question |
| Status | In review; original prompt preserved; not approved for publication |

## השאלה המקורית — עברית

קיבלת דו"ח STA המציג Hold Violation במסלול מסוים לאחר ה-Place & Route, ו-Setup Violation במסלול אחר. אילו פעולות תבצע לתיקון כל אחת מההפרות? האם העלאת תדר השעון תשפיע על הפרת Hold?

## Question — English translation

After place and route, an STA report shows a hold violation on one path and a setup violation on another. What actions would you take to fix each violation? Would increasing the clock frequency affect the hold violation?

## מה בודקים — לפי הטקסט המקורי

הבנה עקרונית שהפרת Hold אינה תלויה בזמן המחזור ($T_{clk}$) אלא במבנה המעגל והאינברטרים, לעומת Setup שתלוי בתדר.

## Assessed skills — English translation

The principle that a hold violation does not depend on the clock period (T_clk) but on circuit structure and inverters, whereas setup depends on frequency.

## הערות עריכה לבדיקה — אינן חלק מהשאלה המקורית

יש להסביר את עצמאות hold מזמן המחזור בהנחה שמבנה השעון והמסלול נשאר קבוע. תיקון פיזי נבדק מחדש בכל פינות setup/hold, כי שיפור אילוץ אחד עלול לפגוע באחר.

## Editorial review notes — separate from the original question

Keep the hold-versus-period distinction under an explicitly fixed clock/path model. Physical fixes must be rechecked across setup/hold corners; a useful fix for one constraint can worsen another.

## Provenance / מקור

Supplied Hebrew collection, hardware question 12. English translated for this collection. No question-specific external source or verified company evidence was supplied.

הנוסח העברי נשמר מהטקסט שסופק. התרגום שומר גם הנחות או עמימויות שבמקור; הערות הדיוק נפרדות. אין כאן אישור שהשאלה נשאלה בחברה המסומנת.
