# Editorial review notes / הערות לבדיקה

These notes flag ambiguity, technical premises, or missing constraints. They do not replace the original questions, establish company attribution, or constitute an expert-approved answer bank.

הערות אלה מצביעות על עמימות, הנחות טכניות ואילוצים חסרים. הן אינן מחליפות את המקור, אינן מאמתות שיוך לחברות ואינן מאגר פתרונות מאושר.

## Company evidence / אימות שיוך לחברות

The supplied text associates questions with companies, but provides no per-question interview report, job role, date, or primary company evidence. General interview guides linked in company profiles do not establish that any individual question was asked. Preserve labels as reported_company, not verified_company.

בטקסט שסופק אין דיווח ראיון, תפקיד, תאריך או ראיה ישירה לכל שאלה. קישורים למדריכי הכנה כלליים אינם מאמתים ששאלה מסוימת נשאלה. יש לשמור את שם החברה כשִיוך מדווח ולא כשִיוך מאומת.

## VHW-001 — Implementing functions with multiplexers

החלק הראשון אינו ניתן למימוש ב־MUX רגיל 2:1 ללא פלט מהופך, כאשר כל פין יכול לקבל רק A, B, 0 או 1. בדיקה ממצה של כל 64 השמות הקלט מאשרת זאת. יש לאפשר קלט מהופך או רכיב נוסף, או לבקש במפורש הוכחת אי־אפשרות. גם בחלק על שני רכיבי MUX 4:1 יש להגדיר אם קלטים מהופכים זמינים.

The first part is not realizable with a standard non-inverting 2:1 MUX whose pins can receive only A, B, 0, or 1. Exhaustive enumeration of all 64 pin assignments confirms this. Allow an inverted input or another component, or explicitly ask the candidate to prove impossibility. The two-4:1-MUX full-adder part also needs a clear rule about availability of complemented inputs.

## VHW-002 — Parity generator

יש להגדיר fan-in מותר ומודל השהיות לפני בקשת עומק מינימלי. בשערי XOR בעלי שני קלטים, לעץ מאוזן של שמונה קלטים יש שלוש רמות XOR.

Specify permitted gate fan-in and the delay model before asking for minimum depth. With two-input XOR gates, a balanced eight-input parity tree has three XOR levels.

## VHW-003 — Address decoding and priority encoding

יש להגדיר מספור ביטים, פלט במצב שכל הקלטים אפס ומודל עלות לשערים או לתאים. אין העדפה מוחלטת למימוש טורי או מקבילי.

Define bit numbering, outputs when all inputs are zero, and the gate/cell cost model. Neither serial nor parallel implementation is universally best.

## VHW-004 — Frequency division without a phase-locked loop

יש להגדיר duty cycle של הקלט, התנהגות איפוס והאם מדובר במודל תזמון אידאלי או במימוש פיזי. הדרישה ל־50% תלויה בהנחות אלה; שימוש בשתי חזיתות יוצר גם מסלולי תזמון של חצי מחזור.

Specify input duty cycle, reset behavior, and an ideal timing model versus real implementation tolerances. The 50% output claim depends on these assumptions; using both edges also introduces half-cycle timing paths.

## VHW-005 — Glitch-free clock multiplexer

יש לציין אם שני השעונים רציפים, אם מותר מרווח נמוך ממושך ואם החלפה חייבת להסתיים גם כששעון נעצר. יש להגדיר רכיבי סנכרון ומיתוג שעון מותרים.

State whether both clocks run continuously, whether an extended low interval is allowed, and whether completion is required when a clock stops. Define the synchronization and clock-gating cells permitted.

## VHW-006 — Overlapping and non-overlapping sequence detection

הכותרת מזכירה זיהוי חופף ולא חופף, אך גוף השאלה אינו דורש במפורש את שניהם. יש להגדיר מדיניות חפיפה ומועד דגימת הפלט לפני השוואת זמן תגובה ומספר מצבים.

The heading mentions overlapping and non-overlapping detection, but the prompt does not explicitly request both. Specify overlap policy and exactly when outputs are sampled before comparing latency and state count.

## VHW-007 — Memory control / FIFO controller

יש להגדיר עומק FIFO, קריאה וכתיבה בו־זמנית, האם שגיאות הן פולסים או דגלים נשמרים, ומודל תקלה. Empty/Full הם לעיתים דגלים נגזרים ולא מצבים נשמרים נפרדים. יש להגדיר אם התאוששות רשאית לאבד נתונים.

Define FIFO depth, simultaneous read/write behavior, whether overflow/underflow are pulses or sticky errors, and the fault model. Empty/full are often derived flags rather than separate stored FSM states. Specify whether recovery may discard buffered data.

## VHW-008 — Pattern detector allowing one bit error

מספר המצבים המינימלי תלוי בזיהוי בחלון נע או במילים מיושרות, בחפיפה, בתזמון הפלט ובאיפוס. יש לקבע זאת לפני דרישת מינימליות, ולבקש נימוק למינימליות אם נותנים עליה ציון.

Minimal state count depends on sliding-window versus aligned-word detection, overlap, output timing, and reset semantics. Fix these before requiring a minimal machine; require a minimality argument if minimality is scored.

## VHW-009 — Packet header parser

הניסוח המקורי "Length (N בייטים)" עמום: האם N הוא אורך המטען או רוחב שדה האורך? יש להגדיר רוחב שדה, N=0, אלגוריתם checksum והכיסוי שלו, escaping של 0xAA במטען ומדיניות סנכרון מחדש. התרגום לאנגלית שומר את העמימות המקורית.

The original phrase "Length (N bytes)" is ambiguous: N may be the payload length or the byte width of the length field. Define field width, N=0, checksum algorithm and coverage, escaping of 0xAA in payload, and the resynchronization policy. The English translation preserves this ambiguity.

## VHW-010 — Gray-code counter and state machine

קוד Gray אינו מבטל metastability. יש להפריד בין תכונת שינוי ביט יחיד לבין סנכרון ואילוצי הפרשי השהיה בין ביטים. לא כל מעבר של bus בין שעונים דורש קוד Gray.

Gray coding does not eliminate metastability. Distinguish the one-bit-change property from synchronization and bus-skew constraints. Not every multibit clock-domain crossing should use Gray code.

## VHW-011 — Basic setup and hold calculations

יש להגדיר skew כהפרש בין זמן הגעת שעון הקליטה לזמן הגעת שעון השיגור, ולהבחין בין clock-to-Q מינימלי ומקסימלי ובין השהיות לוגיקה מינימליות ומקסימליות. אם skew בטווח [-0.8,+0.8] ננו־שניות ו־clock-to-Q הוא בדיוק 2 ננו־שניות במודל הפשוט, setup דורש T_comb,max <= 5.7 ננו־שניות ו־hold דורש T_comb,min >= -0.2 ננו־שניות; כל השהיה מינימלית לא שלילית מקיימת hold. פירושים אחרים משנים את התוצאה.

Define signed skew as capture-clock arrival minus launch-clock arrival, and distinguish minimum from maximum clock-to-Q and combinational delays. If skew can be anywhere in [-0.8,+0.8] ns and clock-to-Q is exactly 2 ns in this simplified model, setup gives T_comb,max <= 5.7 ns and hold gives T_comb,min >= -0.2 ns; any nonnegative minimum delay passes hold. Other interpretations change the answer.

Technical background: [MIT: sequential logic and timing](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c5/c5s1/).

## VHW-012 — Fixing timing violations

יש להסביר את עצמאות hold מזמן המחזור בהנחה שמבנה השעון והמסלול נשאר קבוע. תיקון פיזי נבדק מחדש בכל פינות setup/hold, כי שיפור אילוץ אחד עלול לפגוע באחר.

Keep the hold-versus-period distinction under an explicitly fixed clock/path model. Physical fixes must be rechecked across setup/hold corners; a useful fix for one constraint can worsen another.

## VHW-013 — Two-stage synchronizer and MTBF

בגרסה מתוקנת יש להחליף "פותר מטא־סטביליות" ב־"מקטין את ההסתברות להתפשטות מטא־סטביליות". מסנכרנים נפרדים לכל ביט אינם משמרים קוהרנטיות של bus שרירותי; זה מדויק יותר מאיסור גורף על כל שימוש רב־ביטי. יש להגדיר יציבות אות ודרישות קליטת אירועים.

Replace "solves metastability" in a future reviewed revision with "reduces the probability of metastability propagating." Independent per-bit synchronizers do not preserve arbitrary bus coherence; this is more precise than a blanket prohibition on all multibit uses. Specify signal stability and event-capture requirements.

Technical background: [Nandland: metastability](https://nandland.com/lesson-13-metastability/).

## VHW-014 — Clock jitter versus clock skew

יש להגדיר סימן skew, מודל jitter ואי־ודאות ואילו חזיתות מושוות. אין להניח שכל תרומות ה־jitter בלתי תלויות או שטופולוגיית השעון לבדה מבטלת skew.

Define the skew sign, jitter/uncertainty model, and which edges are compared. Do not assume all jitter contributions add independently or that clock topology alone eliminates skew.

## VHW-015 — Clock recovery and clock gating

הכותרת מזכירה שחזור שעון, אך השאלה עוסקת ב־clock gating. יש להגדיר קוטביות שעון ואת שלב השקיפות של ה־latch; עדיין חלים אילוצי תזמון של clock gating.

The heading mentions clock recovery, but the prompt is about clock gating. Specify clock polarity and latch transparency phase; clock-gating setup/hold checks still apply.

## VHW-016 — Latch versus flip-flop

יש להגדיר רמה פעילה וקוטביות חזית בשרטוט master-slave. תכנון מכוון מבוסס latches הוא תקין; הבעיה היא אגירה לא מכוונת או מודל תזמון שלא נותח.

Specify active level and edge polarity when drawing master-slave latches. Intentional latch-based design is valid; the concern is unintended storage or an unanalysed timing model.

Technical background: [MIT: latches and registers](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c5/c5s1/).

## VHW-017 — CMOS gate and transition characteristics

יחס רוחב PMOS ל־NMOS של בדיוק שתיים אינו כלל אוניברסלי, בפרט ב־NAND עם NMOS בטור. יש לשאול על חוזק הנעה תלוי־תהליך ועל sizing יחסי לפי מודל ייחוס מוגדר.

A PMOS-to-NMOS width ratio of exactly two is not a universal rule, particularly in a NAND with series NMOS devices. Ask about process-dependent drive strength and relative sizing under a stated reference model.

Technical background: [MIT: CMOS technology](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c3/c3s1/).

## VHW-018 — Hardware multiplier

קידוד Booth משנה או מקטין יצירת מכפלות חלקיות; עץ Wallace דוחס אותן. ניתן לשלב ביניהם. יש להגדיר סימן ורוחב ולהשוות שטח, השהיה ומורכבות בנפרד.

Booth recoding reduces or changes partial-product generation; a Wallace tree compresses partial products. They can be combined. Define signedness and bit width, and compare area, delay, and complexity separately.

## VHW-019 — Synchronous versus asynchronous reset

יש להגדיר זמינות שעון בזמן האיפוס ושחרור בכל תחום שעון. שחרור מסונכרן דורש סנכרון מתאים בכל תחום יעד.

Specify clock availability during reset and per-domain reset release. A synchronously deasserted reset requires appropriate synchronization in each destination domain.

## VHW-020 — SRAM versus DRAM memory design

לתא DRAM קונבנציונלי יש לציין 1T1C. האמירה שאוגרים ממומשים ב־SRAM רחבה מדי: יש להבחין בין אוגרי מצב רגילים, register files ומערכי cache. יש להפריד בין מנגנוני precharge וקריאה של הטכנולוגיות.

Use 1T1C for the conventional DRAM cell. The claim that registers are implemented in SRAM is too broad: distinguish ordinary state registers, register files, and cache arrays. Clarify the precharge/read mechanism separately for each memory technology.

Technical background: [MIT: memory technologies and caches](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2017/pages/c14/c14s1/).

## VSW-001 — Population count / Hamming weight

יש להגדיר טיפוס ללא סימן וטיפול באפס. זמן O(1) עם lookup table מניח רוחב קבוע של 32 ביטים; טבלה בת 256 ערכים דורשת ארבע גישות. יש להתייחס להכנה ולזיכרון הטבלה.

State unsigned input type and treatment of zero. Lookup-table O(1) assumes fixed 32-bit width; a 256-entry byte table uses four lookups. Account for preprocessing and table memory.

## VSW-002 — Power-of-two test and highest set bit

יש להגדיר סימן, רוחב מילה W, טיפול באפס ומספור אינדקס MSB מאפס או מאחד. יש להבהיר האם N הוא הערך המספרי או רוחב המילה והאם מותרות פקודות bit-scan מובנות.

Define signedness, word width W, zero handling, and whether MSB indexing starts at zero. Clarify whether N means the numeric value or word width and whether hardware bit-scan intrinsics are permitted.

## VSW-003 — Bit reversal

יש להשתמש באופרנדים ללא סימן וברוחב מפורש של 32 ביטים. באלגוריתם הכללי מספר השלבים לוגריתמי ברוחב; עבור 32 ביטים יש חמישה שלבי מסכות והחלפות.

Use unsigned operands and an explicit 32-bit width. The generalized algorithm has logarithmic stages in word width; for the fixed 32-bit exercise there are five mask/swap stages.

## VSW-004 — Ring buffer / circular queue

יש להגדיר שימוש חד־תהליכוני או מקבילי, מספר יצרנים וצרכנים, טיפול במלא וריק, קיבולת וכללי גלישה. קוד C מקבילי דורש מודל סנכרון וסדר זיכרון. מודולו בחזקה קבועה של שתיים אינו חייב להפוך לחילוק חומרתי.

Specify single-threaded versus concurrent use, producer/consumer count, full/empty behavior, capacity convention, and overflow rules. Concurrent C code needs a defined synchronization/memory-order model. Modulo by a compile-time power of two need not compile to hardware division.

## VSW-005 — Detecting endianness

יש להגדיר בייט בן שמונה ביטים וזמינות uint32_t, להשתמש בגישה חוקית דרך טיפוס תו לייצוג האובייקט ולהבחין בין byte swap לפרשנות בייטים בסריאליזציה. לא כל ארכיטקטורה אפשרית היא בהכרח little-endian או big-endian טהורה.

Specify eight-bit bytes and uint32_t availability, use permitted character access to inspect object representation, and distinguish byte swapping from interpreting serialized bytes. Do not assume every possible architecture is purely little- or big-endian.

## VSW-006 — Stack with constant-time minimum

יש להגדיר פעולות על מחסנית ריקה, מינימום שחוזר והנחות הקצאת זיכרון עבור O(1) במקרה הגרוע לעומת משוערך. קידוד הפרשים דורש טיפול בגלישה או טיפוס רחב יותר.

Define empty-stack behavior, duplicate minima, and allocation assumptions for worst-case versus amortized O(1). Difference encoding needs explicit overflow handling or a wider type.

## VSW-007 — Floyd's cycle detection

יש להבהיר שפגישת מצביעים מבוססת על זהות צומת ולא על שוויון הערכים שבו. יש לכלול רשימה ריקה, צומת יחיד ומעגל עצמי ולהסביר עצירה ללא מעגל.

Specify that node identity, not stored value equality, determines pointer meetings. Include empty, one-node, and self-loop cases, and explain termination when no cycle exists.

## VSW-008 — Compact bitset / bitmap

יש להגדיר אינדקסים חוקיים מ־0 עד 999999 וטיפול בקלט לא חוקי. המפה עצמה דורשת 1,000,000 ביטים, כלומר 125,000 בייטים בני שמונה ביטים או 31,250 מילים מסוג uint32_t, ללא מטא־נתונים ויישור. יש להגדיר אם הפעולות מקביליות.

Define valid indices 0 through 999999 and behavior on invalid input. The raw bitmap is 1,000,000 bits = 125,000 eight-bit bytes = 31,250 uint32_t words, excluding metadata and alignment. State whether operations are concurrent.

## VSW-009 — Unique value among duplicates

יש להגדיר את הבטחות הקלט ורוחב השלמים, במיוחד למספרים שליליים בגרסת שלושת המופעים. זמן O(N) בגישת ספירת ביטים מניח רוחב מילה קבוע.

Specify input guarantees and fixed integer width, particularly for negative values in the three-occurrence variant. O(N) for the bit-count approach assumes word width is fixed.

## VSW-010 — Interval overlap and merging

יש להגדיר טווחים סגורים או חצי פתוחים, איחוד טווחים נושקים, סדר הפלט ושינוי הקלט. מיון וסריקה הם גישה כללית בזמן O(n log n); טענת אופטימליות דורשת הנחות, ובקלט שכבר ממוין אפשר לסרוק בזמן ליניארי.

Define closed versus half-open intervals, whether touching intervals merge, output ordering, and whether input may be mutated. Sort-and-scan is a general O(n log n) approach; optimality requires assumptions and already sorted input admits a linear scan.

## Verification performed / מה נבדק בפועל

- Exact preservation of the source attachment in source-original-he.md.
- 20 hardware and 10 software items, in the supplied order, with both languages.
- Exact extraction of the original Hebrew questions and assessed-skill descriptions.
- Complete metadata and working local index links.
- Exhaustive two-input MUX pin assignment check for VHW-001; simple parity-depth, timing-assumption, and bitmap-size arithmetic checks.
- No independent verification of interview provenance, company culture claims, or all hardware-design solutions.
- English translation and editorial notes still require human review before publication.
