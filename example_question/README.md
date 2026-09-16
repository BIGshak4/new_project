# Example question bank / מאגר שאלות לדוגמה

**30 distinct questions: 20 hardware and 10 software. Each question includes Hebrew and English prompts, a hint, a reference solution, and technical sources.**

**30 שאלות שונות: 20 בחומרה ו־10 בתוכנה. לכל שאלה נוסח בעברית ובאנגלית, רמז, כיוון פתרון ומקורות מקצועיים.**

## Scope and review status / היקף ומצב בדיקה

The set targets students and junior candidates, with digital hardware first and relevant foundational programming. Difficulty and time estimates are provisional. Questions are original AI-assisted practice exercises based on standard concepts, not a harvested interview bank or verified company-specific questions. Source pages were consulted on September 17, 2026.

השאלות מותאמות לסטודנטים ולמועמדי ג׳וניור, בדגש על יסודות דיגיטליים ותכנות רלוונטי. רמות הקושי והזמנים הם הערכות ראשוניות. אלה תרגילים בניסוח מקורי שנוצרו בסיוע בינה מלאכותית על בסיס מושגים מקובלים, ולא שאלות שמיוחסות לחברה מסוימת. המקורות משמשים רקע מקצועי.

All items are `in_review`. No human expert or translation reviewer is claimed. Before publishing: verify technical correctness and Hebrew/English parity, assign catalog skill IDs, and add a reviewed rubric and accepted alternative approaches. These seeds intentionally do not alter the database or existing schema.

כל הפריטים במצב בדיקה. לפני פרסום יש לבצע בדיקה מקצועית ובדיקת התאמה בין השפות, למפות למיומנויות ולהוסיף מחוון ודרכי פתרון חלופיות מאושרות. הקבצים אינם משנים את בסיס הנתונים.

## Files / קבצים

- `hardware/<topic>/`: 20 bilingual Markdown questions.
- `software/<topic>/`: 10 bilingual Markdown questions.
- `questions.json`: complete UTF-8 structured seed with stable IDs and both translations. This is a review format, not a direct Supabase insert script.
- Markdown files are rendered from `questions.json`; keep the two representations in sync when editing.
- Reference solutions are internal authoring material; expose prompts and solutions separately in the application.

## Topic distribution / חלוקה לנושאים

| Category | Topic | נושא | Count |
|---|---|---|---|
| hardware | Boolean logic | אלגברה בוליאנית | 3 |
| hardware | Combinational circuits | מעגלים קומבינטוריים | 4 |
| hardware | Binary arithmetic | אריתמטיקה בינארית | 3 |
| hardware | Sequential circuits | מעגלים סינכרוניים | 3 |
| hardware | Finite state machines | מכונות מצבים | 3 |
| hardware | Timing and clock-domain crossing | תזמון ומעבר בין תחומי שעון | 2 |
| hardware | HDL reasoning | ניתוח קוד תיאור חומרה | 2 |
| software | Bit manipulation | פעולות על ביטים | 3 |
| software | Arrays and search | מערכים וחיפוש | 3 |
| software | Data structures | מבני נתונים | 3 |
| software | Code debugging | איתור שגיאות בקוד | 1 |

## Hardware / חומרה

| ID | English title | כותרת בעברית | Topic | Difficulty | Minutes |
|---|---|---|---|---|---|
| [HW-001](hardware/boolean_logic/hw-001-sensor-majority.md) | Two-out-of-three sensor vote | הכרעת רוב בין שלושה חיישנים | boolean_logic | 2/10 | 5 |
| [HW-002](hardware/boolean_logic/hw-002-nand-only-enable.md) | Enable logic using only NAND gates | לוגיקת הפעלה באמצעות שערי NAND בלבד | boolean_logic | 3/10 | 8 |
| [HW-003](hardware/boolean_logic/hw-003-masked-equality.md) | Compare only enabled bits | השוואת ביטים לפי מסכה | boolean_logic | 3/10 | 7 |
| [HW-004](hardware/combinational_circuits/hw-004-mux-tree-eight-inputs.md) | Build an eight-input multiplexer | בניית מרבב בעל שמונה קלטים | combinational_circuits | 3/10 | 8 |
| [HW-005](hardware/combinational_circuits/hw-005-interrupt-priority.md) | Interrupt priority with a valid flag | קידוד עדיפות לפסיקות | combinational_circuits | 3/10 | 8 |
| [HW-006](hardware/combinational_circuits/hw-006-enabled-decoder.md) | Enabled one-hot decoder | מפענח עם אות הפעלה | combinational_circuits | 2/10 | 5 |
| [HW-007](hardware/combinational_circuits/hw-007-rotate-versus-shift.md) | Rotate versus logical shift | סיבוב לעומת הזזה לוגית | combinational_circuits | 3/10 | 7 |
| [HW-008](hardware/binary_arithmetic/hw-008-full-adder-composition.md) | Compose a full adder | הרכבת מחבר מלא | binary_arithmetic | 3/10 | 8 |
| [HW-009](hardware/binary_arithmetic/hw-009-signed-overflow.md) | Carry and signed overflow | נשא וגלישה בחיבור מספרים מסומנים | binary_arithmetic | 3/10 | 5 |
| [HW-010](hardware/binary_arithmetic/hw-010-unsigned-saturating-adder.md) | Unsigned saturating addition | חיבור ללא סימן עם רוויה | binary_arithmetic | 4/10 | 8 |
| [HW-011](hardware/sequential_circuits/hw-011-mod-six-counter.md) | Enabled modulo-six counter | מונה מודולו שש עם הפעלה | sequential_circuits | 4/10 | 10 |
| [HW-012](hardware/sequential_circuits/hw-012-load-and-serial-shift.md) | Load and serial shift priorities | עדיפויות בטעינה ובהזזה טורית | sequential_circuits | 3/10 | 8 |
| [HW-013](hardware/sequential_circuits/hw-013-sampled-rising-edge.md) | One-cycle sampled rising-edge pulse | פולס של מחזור אחד לזיהוי עלייה | sequential_circuits | 3/10 | 8 |
| [HW-014](hardware/finite_state_machines/hw-014-overlapping-sequence-1011.md) | Overlapping 1011 detector | גלאי לרצף חופף 1011 | finite_state_machines | 5/10 | 15 |
| [HW-015](hardware/finite_state_machines/hw-015-credit-dispenser.md) | Credit dispenser state machine | מכונת מצבים לצבירת קרדיט | finite_state_machines | 4/10 | 12 |
| [HW-016](hardware/finite_state_machines/hw-016-request-acknowledge.md) | Request and acknowledgement controller | בקר בקשה ואישור | finite_state_machines | 4/10 | 12 |
| [HW-017](hardware/timing_and_cdc/hw-017-setup-hold-calculation.md) | Setup and hold constraints | חישוב אילוצי Setup ו־Hold | timing_and_cdc | 5/10 | 10 |
| [HW-018](hardware/timing_and_cdc/hw-018-asynchronous-pulse-transfer.md) | A pulse crossing into a slower clock | העברת פולס לתחום שעון איטי | timing_and_cdc | 5/10 | 10 |
| [HW-019](hardware/hdl_reasoning/hw-019-nonblocking-pipeline-trace.md) | Trace a nonblocking pipeline | מעקב אחר צינור עם השמות לא חוסמות | hdl_reasoning | 3/10 | 7 |
| [HW-020](hardware/hdl_reasoning/hw-020-incomplete-combinational-assignment.md) | Find the unintended latch | איתור Latch לא מכוון | hdl_reasoning | 3/10 | 7 |

## Software / תוכנה

| ID | English title | כותרת בעברית | Topic | Difficulty | Minutes |
|---|---|---|---|---|---|
| [SW-001](software/bit_manipulation/sw-001-count-set-bits.md) | Count asserted status bits | ספירת ביטים פעילים | bit_manipulation | 3/10 | 8 |
| [SW-002](software/bit_manipulation/sw-002-power-of-two-check.md) | Recognize a power of two | זיהוי חזקה של שתיים | bit_manipulation | 2/10 | 5 |
| [SW-003](software/bit_manipulation/sw-003-extract-register-field.md) | Extract a register field | חילוץ שדה מתוך אוגר | bit_manipulation | 4/10 | 8 |
| [SW-004](software/arrays_and_search/sw-004-first-greater-or-equal.md) | First element at least a target | האיבר הראשון שאינו קטן מהיעד | arrays_and_search | 4/10 | 12 |
| [SW-005](software/arrays_and_search/sw-005-merge-measurement-streams.md) | Merge sorted measurement lists | מיזוג רשימות מדידות ממוינות | arrays_and_search | 3/10 | 10 |
| [SW-006](software/arrays_and_search/sw-006-pair-sum-indices.md) | Find two distinct matching indices | מציאת שני אינדקסים שונים שסכומם נתון | arrays_and_search | 4/10 | 12 |
| [SW-007](software/data_structures/sw-007-bounded-circular-queue.md) | Fixed-capacity circular queue | תור מעגלי בקיבולת קבועה | data_structures | 4/10 | 12 |
| [SW-008](software/data_structures/sw-008-balanced-brackets.md) | Validate nested brackets | בדיקת תקינות סוגריים מקוננים | data_structures | 3/10 | 10 |
| [SW-009](software/data_structures/sw-009-reverse-singly-linked-list.md) | Reverse a linked list in place | היפוך רשימה מקושרת במקום | data_structures | 4/10 | 12 |
| [SW-010](software/code_debugging/sw-010-array-bound-off-by-one.md) | Find an array boundary error | איתור שגיאת גבול במערך | code_debugging | 2/10 | 5 |

## Provenance / מקוריות

Standard ideas such as multiplexers, linked-list reversal, and binary search are used as learning topics. No source text, diagrams, or solution code was bulk copied. Source references do not grant rights to unrelated material on those websites and do not imply endorsement. No company name or interview-frequency claim is attached to a question.

The sample bank preserves the repository specification's separation between practice content, expert review, and publication. It does not mark AI-assisted content as expert-reviewed.
