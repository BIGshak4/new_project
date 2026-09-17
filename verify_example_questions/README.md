# Supplied interview questions — bilingual review collection

# מאגר השאלות שסופק — עברית ואנגלית

**30 questions: 20 hardware and 10 software. The Hebrew prompts and assessed-skill descriptions are preserved; each has an English translation. Company labels are unverified claims from the supplied text.**

**30 שאלות: 20 בחומרה ו־10 בתוכנה. השאלות ומה שהן בודקות נשמרו בעברית ולצדן תרגום לאנגלית. השיוכים לחברות נלקחו מהמקור ואינם מאומתים.**

## Reading order / סדר קריאה

1. [Original complete text / הטקסט המקורי המלא](source-original-he.md)
2. [Company profiles / פרופילי החברות](company-profiles-he.md)
3. [Product integration recommendations / המלצות לשילוב במוצר](product-integration-he.md)
4. [Editorial review notes / הערות דיוק לבדיקה](review-notes.md)
5. [Structured bilingual data / נתונים מובנים בשתי השפות](questions.json)

## How to use / שימוש

Every question file contains the original Hebrew prompt, English translation, assessed skills in both languages, and separate editorial notes. The company headings are preserved as reported metadata, not verified interview evidence. English translations intentionally retain assumptions from the original; suggested clarifications appear separately.

בכל קובץ: נוסח עברי מקורי, תרגום לאנגלית, מה בודקים בשתי השפות והערות עריכה נפרדות. נשמרו גם פרופילי כל שש קבוצות החברות והמלצות ההטמעה. Microsoft מופיעה רק בשאלה שסופקה ולא נוסף לה פרופיל מומצא.

All items remain in_review. This folder is a review collection and does not publish questions or apply database migrations. The earlier example_question bank remains a separate collection; related topics do not make these automatically unique additions to the 150-question target.

כל הפריטים במצב בדיקה. המאגר החדש נפרד מהתיקייה example_question. מאחר שיש חפיפה בנושאים ובחלק מהתרגילים, אין לספור אוטומטית את כל הפריטים בשני המאגרים כשאלות ייחודיות בדרך ל־150.

## Topics / נושאים

| Category | Topic | נושא | Count |
|---|---|---|---|
| hardware | Digital logic and clocking | לוגיקה ספרתית ושעונים | 5 |
| hardware | Finite state machines | מכונות מצבים | 5 |
| hardware | Timing, STA, and CDC | תזמון, ניתוח תזמון ומעבר בין שעונים | 5 |
| hardware | Cells and hardware architecture | מבנה תאים וארכיטקטורת חומרה | 5 |
| software | Bit manipulation | פעולות על ביטים | 6 |
| software | Queues and stacks | תורים ומחסניות | 2 |
| software | Linked lists | רשימות מקושרות | 1 |
| software | Intervals and sorting | טווחים ומיון | 1 |

## Hardware / חומרה

| ID | English title | כותרת בעברית | Reported company (unverified) |
|---|---|---|---|
| [VHW-001](hardware/digital_logic_and_clocking/vhw-001-mux-functions.md) | Implementing functions with multiplexers | מימוש פונקציות באמצעות Multiplexer | NVIDIA |
| [VHW-002](hardware/digital_logic_and_clocking/vhw-002-eight-bit-parity.md) | Parity generator | גלאי זוגיות (Parity Generator) | Apple |
| [VHW-003](hardware/digital_logic_and_clocking/vhw-003-priority-encoder.md) | Address decoding and priority encoding | פענוח כתובות ו-Priority Encoder | Intel |
| [VHW-004](hardware/digital_logic_and_clocking/vhw-004-divide-by-three.md) | Frequency division without a phase-locked loop | חלוקת תדר ללא Phase Locked Loop (PLL) | Amazon (Annapurna Labs) |
| [VHW-005](hardware/digital_logic_and_clocking/vhw-005-glitch-free-clock-mux.md) | Glitch-free clock multiplexer | מניעת גליצ'ים (Glitch-free Clock Mux) | Google |
| [VHW-006](hardware/finite_state_machines/vhw-006-sequence-detector.md) | Overlapping and non-overlapping sequence detection | גלאי רצף (Sequence Detector) חופף ולא חופף | Intel |
| [VHW-007](hardware/finite_state_machines/vhw-007-fifo-controller.md) | Memory control / FIFO controller | תכנון מכונת בקרת זיכרון / FIFO Controller | NVIDIA |
| [VHW-008](hardware/finite_state_machines/vhw-008-fault-tolerant-detector.md) | Pattern detector allowing one bit error | גלאי דפוס עם שגיאה אחת מותרת (Fault-Tolerant Detector) | Amazon (Annapurna Labs) |
| [VHW-009](hardware/finite_state_machines/vhw-009-packet-parser.md) | Packet header parser | מפענח חבילות פרוטוקול (Packet Header Parser) | Apple |
| [VHW-010](hardware/finite_state_machines/vhw-010-gray-code-counter.md) | Gray-code counter and state machine | מונה Gray Code ומכונת מצבים | Marvell |
| [VHW-011](hardware/timing_and_cdc/vhw-011-setup-hold.md) | Basic setup and hold calculations | חישובי Setup ו-Hold בסיסיים | Apple |
| [VHW-012](hardware/timing_and_cdc/vhw-012-timing-repair.md) | Fixing timing violations | תיקון הפרות תזמון (Violations Fixing) | NVIDIA |
| [VHW-013](hardware/timing_and_cdc/vhw-013-synchronizer-mtbf.md) | Two-stage synchronizer and MTBF | מסנכרן דו-שלבי ו-MTBF | Amazon (Annapurna Labs) |
| [VHW-014](hardware/timing_and_cdc/vhw-014-jitter-skew.md) | Clock jitter versus clock skew | תופעת Clock Jitter לעומת Clock Skew | Google |
| [VHW-015](hardware/timing_and_cdc/vhw-015-integrated-clock-gating.md) | Clock recovery and clock gating | שחזור שעון ו-Clock Gating | Marvell |
| [VHW-016](hardware/cells_and_architecture/vhw-016-latch-versus-flip-flop.md) | Latch versus flip-flop | Latch לעומת Flip-Flop | Intel |
| [VHW-017](hardware/cells_and_architecture/vhw-017-cmos-nand.md) | CMOS gate and transition characteristics | שער CMOS ומאפייני מעבר | Qualcomm |
| [VHW-018](hardware/cells_and_architecture/vhw-018-hardware-multiplier.md) | Hardware multiplier | מימוש מכפיל חומרתי (Hardware Multiplier) | Mobileye |
| [VHW-019](hardware/cells_and_architecture/vhw-019-reset-strategies.md) | Synchronous versus asynchronous reset | מנגנון איפוס – Synchronous vs. Asynchronous Reset | NVIDIA |
| [VHW-020](hardware/cells_and_architecture/vhw-020-sram-dram.md) | SRAM versus DRAM memory design | תכנון זיכרון SRAM לעומת DRAM | Apple |

## Software / תוכנה

| ID | English title | כותרת בעברית | Reported company (unverified) |
|---|---|---|---|
| [VSW-001](software/bit_manipulation/vsw-001-popcount.md) | Population count / Hamming weight | ספירת ביטים דולקים (Popcount / Hamming Weight) | Apple |
| [VSW-002](software/bit_manipulation/vsw-002-power-two-msb.md) | Power-of-two test and highest set bit | זיהוי חזקה של 2 ומציאת הביט הגבוה ביותר (MSB) | Google |
| [VSW-003](software/bit_manipulation/vsw-003-bit-reversal.md) | Bit reversal | הפיכת סדר ביטים (Bit Reversal) | NVIDIA |
| [VSW-004](software/queues_and_stacks/vsw-004-ring-buffer.md) | Ring buffer / circular queue | מימוש תור מעגלי (Ring Buffer / Circular Queue) | Amazon (Annapurna Labs) |
| [VSW-005](software/bit_manipulation/vsw-005-endianness.md) | Detecting endianness | בדיקת Endianness של מערכת | Intel |
| [VSW-006](software/queues_and_stacks/vsw-006-min-stack.md) | Stack with constant-time minimum | מימוש מחסנית עם תמיכה ב-Min ב-$O(1)$ (Min-Stack) | Mobileye |
| [VSW-007](software/linked_lists/vsw-007-floyd-cycle.md) | Floyd's cycle detection | זיהוי מעגל ברשימה מקושרת (Floyd's Cycle Detection) | Qualcomm |
| [VSW-008](software/bit_manipulation/vsw-008-compact-bitset.md) | Compact bitset / bitmap | מימוש מנגנון Bitset / Bitmap קומפקטי | Microsoft |
| [VSW-009](software/bit_manipulation/vsw-009-single-number.md) | Unique value among duplicates | איתור אלמנט יחיד במערך כפילויות (Single Number) | Marvell |
| [VSW-010](software/intervals_and_sorting/vsw-010-interval-merging.md) | Interval overlap and merging | בדיקת חפיפת טווחים (Interval Overlap & Merging) | Google |
