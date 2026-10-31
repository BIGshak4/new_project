# PREP-220 — זיכרון סינכרוני בן ארבע מילים עם יציאת קריאה תקפה

מצב: הצעה לפתרון בסיוע AI; ביקורת מקצועית אנושית ממתינה.

## מקורות מקוריים / Original sources

- [sources/2026-10-31-batch20-20.png](../sources/2026-10-31-batch20-20.png)

## נוסח המקור / Original wording

בנה רכיב זיכרון המכיל זיכרון בעל 4 מקומות, באמצעות רכיבים נתונים: FF, וזיכרון בעל 4 מקומות. לרכיב 6 כניסות: wr_addr באורך 2 סיביות - כתובת לכתיבה; wr_data באורך מספר ביטים נתון - מידע לכתיבה; wr_en באורך סיבית אחת - 1 בכתיבה ו-0 אחרת; re_en באורך סיבית אחת - 1 בקריאה ו-0 אחרת; re_addr באורך 2 סיביות - כתובת לקריאה; clk באורך סיבית אחת - שעון סינכרוני. שתי יציאות: read_data באורך מילה, והסיבית Valid שהיא 1 כשהמידע ביציאת הקריאה הוא מה שרצינו להוציא וחשוב לנו, ו-0 אחרת.

## עברית

תכננו זיכרון סינכרוני בן4 מילים ברוחב W בעזרת FF ולוגיקה. הכניסות הן wr_addr[1:0], wr_data[W−1:0], wr_en, re_en, re_addr[1:0], clk; היציאות read_data[W−1:0] (במקור re_data) ו־Valid. מותר להוסיף reset מוגדר. בחוזה שנבחר יש פורט כתיבה אחד ופורט קריאה אחד, ושניהם מתקבלים באותה חזית. קריאה נרשמת; בהתנגשות לאותה כתובת מוחזר הערך הישן. איפוס מאתחל את כל ארבע המילים ואת היציאות ל־0.

### רמזים / Hints

1. ארבע כתובות דורשות כמה ביטי כתובת וכמה FF לאחסון? כיצד בוחרים רק מילה אחת לכתיבה?
2. פענחו wr_addr ל־4 enables, ובחרו את מילת הקריאה במרבב4:1. החליטו מה יקרה אם קוראים וכותבים יחד.
3. באותה חזית read_data←mem[re_addr] לפי המצב הישן, ואז עדכנו את הכתיבה. Valid←re_en בכל מחזור; כשאין קריאה שמרו read_data.

### הצעה לפתרון / Proposed solution

נבנה ארבעה רגיסטרים M0..M3, כל אחד ברוחב W. מפענח2 ל־4 בונה enable_i=wr_en AND (wr_addr==i). לכל ביט יש mux בכניסת D שבוחר בין הערך הישן ל־wr_data, או תא FF בעל enable שקול. כל ה־FF מחוברים לאותו clk. אין לגדר שעון עם שער AND נאיבי.

מרבב4:1 ברוחב W בוחר את M[re_addr]. הפלט שלו נקלט ברגיסטר read_data רק בחזית שבה re_en=1. דגל Valid מתעד אם באותה חזית התקבלה קריאה; לכן Valid הבא הוא re_en, לא פונקציה של כתובת או של נתון שאינו אפס. במחזור ללא קריאה Valid=0 והנתון הקודם מחזיק אך אינו תגובה חדשה.

| wr_en | re_en | פעולה בחזית | Valid אחרי החזית |
|---|---|---|---|
| 0 | 0 | אין שינוי מילים; read_data נשמר | 0 |
| 1 | 0 | כתיבה ל־wr_addr; read_data נשמר | 0 |
| 0 | 1 | read_data מקבל מילה ישנה מ־re_addr | 1 |
| 1 | 1 | קריאה ישנה וכתיבה מתקבלות יחד | 1 |

אם שתי הכתובות שוות, nonblocking assignments בבלוק השעון קוראות את אותה תמונת מצב ישנה: read_data מקבל את הערך שלפני הכתיבה, ואחרי החזית הזיכרון מכיל wr_data. למשל M2=5, כתיבה9 וקריאה2 יחד מחזירות5; הקריאה הבאה תחזיר9. זהו read-first שנבחר בעריכה. write-first עם bypass ו־no-change הם חוזים אפשריים אחרים, אך אין להחליף ביניהם בשקט. ממשק עם כתובות read/write נפרדות אינו בהכרח single-port; כאן זהו 1R1W, ולא נדרשת ארביטרציה בין בקשה אחת מכל סוג.

באיפוס סינכרוני מגדירים את ארבע המילים, read_data ו־Valid ל־0, והוא קודם לכל בקשה. כך גם קריאה מכתובת שמעולם לא נכתבה מחזירה0 חוקי. חלופה ללא איפוס נתונים צריכה דגל initialized לכל מילה או חוזה שאוסר קריאה לפני כתיבה; אין להכריז על תוכן לא מאותחל כתגובה תקפה צפויה.

הוכחה לפי חזיתות: נניח שהרגיסטרים מתארים את הזיכרון לפני החזית. רק ה־enable של כתובת הכתיבה יכול להשתנות, ולכן כל היתר נשמרים; הקריאה משתמשת בתמונה הישנה שנבחרת על ידי mux. האיפוס הוא בסיס האינדוקציה. עדכון Valid=re_en נותן בדיוק דגל תגובה לקריאה שהתקבלה, כולל שתי פעולות יחד, בלי תלות בתוכן.

העלות של המימוש הזה היא4W FF לאחסון, W FF לתגובה ו־FF אחד לתוקף: בסך הכל5W+1, עם מפענח כתיבה, לוגיקת load ומרבב קריאה. לא נדרשים רגיסטרי כתובת כי הממשק נדגם בחזית והתוצאה נרשמת ישירות. מספר טרנזיסטורים תלוי בטופולוגיית FF, reset, mux ו־library; אין מספר אוניברסלי ל־FF. הוספת תגובה/פלטים או שימוש בזיכרון מאקרו משנה את המדד.

16,384 מעברים ממצים עבור W=1 נבדקו מול אורקל עצמאי של מצב לפני חזית: כל16 תכני הזיכרון, enables, כתובות, נתוני כתיבה, מצבי יציאה ו־reset. נוסף trace64 ביט להתנגשות והחזקת פלט. קוד Python ו־RTL מצורפים; לא בוצע אימות סיליקון.

אימות RTL שבוצע בפועל: הזיכרון ברוחב1 קומפל והורץ מול assertions בכל16,384 מצבי המעבר המתוארים, כולל התנגשות, idle ו־reset. trace64 הביט הוא בדיקת Python נפרדת. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה.

### assumptions

[
  "W≥1; פורט1R1W על clk משותף; שני enables מתקבלים יחד; read-first בהתנגשות; תגובה רשומה; reset סינכרוני מאתחל כל הנתונים."
]

### optimality

"מימוש FF מפורש:4W לאחסון ועוד W לפלט ועוד1 ל־Valid, כלומר5W+1. מפענח/load/mux נוספים. אין מינימום טרנזיסטורים אוניברסלי או אופטימום מול מאקרו זיכרון."

### verification

"16,384 מעברי W=1 ממצים מול snapshot לפני חזית, כולל reset וכל תכני הזיכרון, כתובות, enables ומצבי יציאה; נוסף trace64 ביט. מודל Python. אימות RTL שבוצע בפועל: הזיכרון ברוחב1 קומפל והורץ מול assertions בכל16,384 מצבי המעבר המתוארים, כולל התנגשות, idle ו־reset. trace64 הביט הוא בדיקת Python נפרדת. זהו אימות סימולציה עם assertions, ללא סינתזה, מדידת תזמון/הספק או בדיקת חומרה פיזית. ההרצה הגדולה הראשונית הסתיימה ב־timeout; רק ההרצה המוגבלת הושלמה."

### edge_cases

[
  "קריאה/כתיבה סימולטניות לכתובת שווה או שונה; ללא פעולות; קריאה ראשונה אחרי reset; נתון0 תקף; reset עם שני enables; read_data נשמר כש־Valid0."
]

### common_mistakes

[
  "הנחת single-port למרות כתובות נפרדות.",
  "כתיבת blocking שמחליפה read-first ב־write-first.",
  "Valid שנשאר1 במחזור idle.",
  "ספירת4W FF ושכחת פלט רשום ודגל.",
  "קריאה מתוכן לא מאותחל בלי חוזה."
]

### interview_answer

"ארבעה רגיסטרי W ביט, מפענח כתיבה2ל־4 ומרבב קריאה4ל־1. הקריאה נרשמת, Valid מעוכב עם הבקשה; בחוזה שלי שני הפורטים עובדים יחד וקריאה בהתנגשות מקבלת ערך ישן. העלות5W+1 FF."

### source_ambiguities

[
  "המקור אינו מגדיר רוחב W, reset, תוכן התחלתי, התנגשות או השהיית תגובה. הושלם חוזה1R1W סינכרוני read-first עם אתחול0."
]

### solution_extensions

{
  "question": "איך משנים להתנגשות write-first?",
  "direction": "לפני רישום הקריאה בוחרים wr_data כאשר wr_en && re_en && wr_addr==re_addr; אחרת משתמשים ב־mux הזיכרון. יש לעדכן גם את האורקל והתיעוד.",
  "integration": "מוכן בתוכן; אינו מחובר לתור אינטראקטיבי."
}

## English

Build a synchronous four-word, W-bit memory from FFs and logic. Inputs: wr_addr[1:0], wr_data[W−1:0], wr_en, re_en, re_addr[1:0], clk. Outputs: read_data[W−1:0] (source name re_data) and Valid. An explicit reset may be added. Chosen contract: one write port and one read port, both accepted on the same edge; registered read response; a same-address read/write returns the old value. Reset initializes all four words and outputs to zero.

### רמזים / Hints

1. How many address bits and storage FFs are needed? How do you enable only the selected word for writing?
2. Decode wr_addr into four enables and select a read word with a4:1 mux. Define simultaneous read/write behavior.
3. At the edge capture old mem[re_addr] into read_data and update the write. Set Valid←re_en every cycle and hold read_data when no read occurs.

### הצעה לפתרון / Proposed solution

Use four W-bit registers M0..M3. A2-to-4 decoder produces enable_i=wr_en AND (wr_addr==i). Each bit has a D-input mux selecting old data or wr_data, or an equivalent clock-enable FF. Every FF uses the common clk. Do not gate a clock with an ordinary AND.

A W-bit4:1 mux selects M[re_addr]. Capture it into the read_data register only at an edge with re_en=1. Valid records whether that edge accepted a read, so next Valid=re_en, independently of address or whether data are nonzero. Without a read, Valid=0 and old read_data holds but is not a new response.

| wr_en | re_en | Edge action | Valid after edge |
|---|---|---|---|
| 0 | 0 | hold words and read_data | 0 |
| 1 | 0 | write wr_addr; hold read_data | 0 |
| 0 | 1 | capture old word at re_addr | 1 |
| 1 | 1 | accept old-data read and write together | 1 |

If the addresses coincide, nonblocking assignments observe the same old state: read_data gets the pre-write value while memory gets wr_data after the edge. For example M2=5 with concurrent write9/read2 returns5; the next read returns9. This editorial contract is read-first. Bypassed write-first and no-change are other possible contracts, which must be stated separately. Separate read/write addresses do not imply a single port; this design is1R1W and needs no arbitration between its one read and one write request.

Synchronous reset sets all four words, read_data and Valid to zero and takes priority over requests. Thus reading a never-written address returns a valid zero. A design that does not reset data needs per-word initialized flags or a prohibition against reads before writes; uninitialized contents cannot be promised as a known valid response.

Induction over edges proves correctness: assume the registers represent the pre-edge memory. Only the decoded write-enable can change one word; all others hold. The read mux selects from the old snapshot. Reset establishes the base case. Valid=re_en marks exactly the accepted read response, even when both operations occur, independently of contents.

The shown realization uses4W storage FFs, W read-response FFs and one Valid FF:5W+1 total, plus write decoder, load logic and read mux. No address registers are needed because requests are sampled at the edge and data is captured directly. Transistor count depends on FF topology, reset, mux implementation and library; there is no universal transistor count per FF. Additional interface state or a memory macro changes the cost metric.

16,384 exhaustive W=1 transitions were checked against an independent pre-edge oracle, covering all16 memory contents, enables, addresses, write data, output states and reset. A64-bit collision/hold trace was added. Python and RTL are provided; no silicon test is claimed.

Actual RTL validation: width1 memory compiled and passed assertions on all16,384 described transitions, including collision, idle and reset. The64-bit trace is a separate Python model check. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed.

### assumptions

[
  "W≥1; common-clock1R1W; both enables accepted together; read-first collision; registered response; synchronous reset initializes all data."
]

### optimality

"Explicit FF design:4W storage plus W output plus1 Valid, totaling5W+1. Decoder/load/mux logic is additional. No universal transistor minimum or memory-macro optimum."

### verification

"16,384 exhaustive W=1 transitions against a pre-edge snapshot, including reset and all memory contents, addresses, enables and output states; extra64-bit trace. Python model. Actual RTL validation: width1 memory compiled and passed assertions on all16,384 described transitions, including collision, idle and reset. The64-bit trace is a separate Python model check. This is assertion-based simulation, without synthesis, physical timing/power measurement or hardware testing. An initial larger run timed out; only the bounded RTL run completed."

### edge_cases

[
  "Simultaneous same/different-address read/write; no operations; first read after reset; valid zero data; reset with both enables; read_data holds while Valid0."
]

### common_mistakes

[
  "Assuming single-port despite separate addresses.",
  "Blocking writes accidentally changing read-first to write-first.",
  "Leaving Valid high on idle.",
  "Counting4W FFs but forgetting registered output and flag.",
  "Reading uninitialized contents without a contract."
]

### interview_answer

"Four W-bit registers, a2-to-4 write decoder and4:1 read mux. Register the response and its validity. Both ports operate together; collision reads old data. The realization uses5W+1 FFs."

### source_ambiguities

[
  "W, reset, initial contents, collision behavior and response latency are unspecified. A synchronous1R1W read-first contract with zero initialization is supplied."
]

### solution_extensions

{
  "question": "How would you make collisions write-first?",
  "direction": "Bypass wr_data into the read register when wr_en && re_en && wr_addr==re_addr; otherwise use the memory mux. Update the oracle and contract too.",
  "integration": "Prepared in content; not connected to the interactive queue."
}

## קבצים / Files

- [solutions/prep_216_220_sequential.py](../solutions/prep_216_220_sequential.py)
- [solutions/prep_216_220_sequential.sv](../solutions/prep_216_220_sequential.sv)
- [solutions/prep_216_220_sequential_tb.sv](../solutions/prep_216_220_sequential_tb.sv)
- [diagrams/prep-220-batch20-sequential.png](../diagrams/prep-220-batch20-sequential.png)
- [diagrams/prep-220-batch20-sequential-he.png](../diagrams/prep-220-batch20-sequential-he.png)
