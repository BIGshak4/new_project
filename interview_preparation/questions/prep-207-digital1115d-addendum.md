# PREP-207 — זיהוי 0101 בחפיפה ומה פירוש „ללא FF”

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## זיהוי 0101 בחפיפה ומה פירוש „ללא FF”

א. ממשו מכונת מצבים לזיהוי 0101 בזרם ביטים. מה יקרה עבור 010101? ב. דונו במימוש בעזרת רכיבים לוגיים ללא FF. אם אתם מציעים FIFO, הגדירו במפורש את הנתון הנכתב, סדר הפעולות וממשק הקריאה.

הבהרות: ביט אחד מתקבל בכל חזית שעון; reset סינכרוני קודם לקליטה; המוצא נבדק לאחר החזית. בוחרים חפיפה, ולכן נדרשים שני זיהויים עבור 010101. חלק ב נבחן בשלושה חוזים נפרדים: קלט טורי עם שערים צירופיים חסרי זיכרון, חלון של ארבעה ביטים המוגש במקביל מבחוץ, או שימוש מפורש ברכיב זיכרון כדוגמת FIFO. איסור על רכיב FF אינו בהכרח איסור על כל זיכרון, אך אסור להסתיר זיכרון בתוך השם של רכיב אחר.

### וריאציה: זיהוי 1010 עם חפיפות
תכננו גלאי סינכרוני לרצף 1010 בזרם אינסופי. קבלו סיבית בכל חזית עולה והוציאו דופק רשום במשך מחזור אחד כאשר הסיבית שהתקבלה משלימה התאמה. חפיפות מותרות. איפוס סינכרוני פעיל־גבוה מוחק היסטוריה ופלט וגובר על הדגימה. המחרוזות נקראות בסדר זמן משמאל לימין. לדוגמה 0101010001 צריך להפיק 0000101000. הראו טבלת מעברים, זיכרון, שרטוט והוכחת נכונות.

### לא מאבדים את הסיומת אחרי זיהוי
נבחר Moore עם Q0=ללא התאמה, Q1=0, Q2=01, Q3=010, Q4=0101. z=1 ב־Q4 בלבד. המעברים הם:

| מצב | קלט 0 | קלט 1 |
|---|---|---|
| Q0 | Q1 | Q0 |
| Q1 | Q1 | Q2 |
| Q2 | Q3 | Q0 |
| Q3 | Q1 | Q4 |
| Q4 | Q3 | Q0 |

המצב זוכר באינדוקציה את הסיומת הארוכה ביותר שהיא קידומת המטרה. בפרט, אחרי זיהוי וקלט אפס, הסיומת היא 010 ולכן עוברים ל־Q3. עבור 010101 מתקבל מוצא 000101: זיהוי בחזית הרביעית והשישית. החזרה ל־Q0 אחרי זיהוי הייתה מתעלמת מהחפיפה. במימוש Moore הזה חמישה מצבים ושלושה FF בינאריים; Mealy יכול להשתמש בארבעה מצבים ובאירוע צירופי, בכפוף לחוזה פלט אחר.

### ללא FF אינו בהכרח ללא זיכרון
אם הכניסה היא רק הביט הנוכחי, והמעגל חסר זיכרון ומשוב, אין פתרון לזיהוי טורי: בסוף ההיסטוריות 0101 ו־0001 הקלט זהה, 1, אבל התוצאות הנדרשות שונות. גם שערים נוספים אינם מתקנים את הסתירה. אם שערים עם משוב מותרים, אפשר לבנות latches, אך אז יש זיכרון וצריך לפרט תזמון, אתחול ויציבות; זו אינה רשת צירופית חסרת זיכרון.

אם ארבעת הביטים האחרונים מוגשים במקביל מבחוץ כ־w[3:0], מהישן לחדש, אז valid AND NOT w[3] AND w[2] AND NOT w[1] AND w[0] מזהה את החלון. המעגל הזה אינו מאחסן היסטוריה, אבל מי שמייצר את החלון כן. valid חייב לאשר שכבר התקבלו ארבעה ביטים, כדי לא לזהות ריפוד אתחול כנתונים.

### FIFO: כותבים את הנתון, ומצהירים על הממשק
המודל המצורף מתיר במפורש rolling FIFO בעומק ארבע וברוחב ביט אחד, עם צפייה מקבילה בארבעת האיברים ומצב full. בכל חזית שאינה reset כותבים DIN=x, הביט החדש. כשהרכיב מלא מפנים את האיבר הישן באותה חזית ואז מכניסים את החדש; ב־reset מרוקנים. אחרי העדכון, כאשר full=1, משווים את ארבעת האיברים מהישן לחדש ל־0101. כך מתקבל אותו מוצא בדיוק כמו ה־FSM, לרבות שני זיהויים ב־010101.

FIFO רגיל שמציג רק head אינו בהכרח מאפשר ארבעה taps או פינוי אוטומטי; אין להניח אותם בלי מפרט. FIFO ומצב המילוי שלו מכילים זיכרון, גם כאשר אין FF מפורש בסכימה החיצונית. אם נאסר כל זיכרון וגם אין חלון חיצוני, החלק הטורי נשאר בלתי אפשרי. המימוש מראה חלופה מותנית ומדויקת, ולא עוקף את האיסור בשם של רכיב.

### מודל לוגי בפייתון שהורץ

```python
"""Moore FSM and explicitly stateful four-tap rolling FIFO abstraction."""

from collections import deque

TRANSITIONS = ((1, 0), (1, 2), (3, 0), (1, 4), (3, 0))


def detect_moore(bits, resets=()):
    state = 0
    reset_edges = set(resets)
    result = []
    for edge, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("binary serial input required")
        state = 0 if edge in reset_edges else TRANSITIONS[state][bit]
        result.append(int(state == 4))
    return result


def detect_rolling_fifo(bits, resets=()):
    # Requires a rolling overwrite policy and simultaneous four-entry peek.
    # These are extra contracts, not properties of every ordinary FIFO IP.
    history = deque(maxlen=4)
    reset_edges = set(resets)
    result = []
    for edge, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("DIN is the current serial input bit, not a constant")
        if edge in reset_edges:
            history.clear()
        else:
            history.append(bit)
        result.append(int(len(history) == 4 and tuple(history) == (0, 1, 0, 1)))
    return result
```


### שומרים את הסיומת שיכולה להתחיל התאמה נוספת
נחזיק מצב p שהוא אורך הקידומת הארוכה ביותר של 1010, באורך קטן מארבע, שהיא סיומת ההיסטוריה: 0=ריק, 1=1, 2=10, 3=101. הפלט hit הוא ביט רשום נוסף. טבלת התא הבא, כולל hit החדש:

|p|x=0: pnext,hit|x=1: pnext,hit|
|---|---|---|
|0|0,0|1,0|
|1|2,0|1,0|
|2|0,0|3,0|
|3|2,1|1,0|

אחרי השלמת 1010 עוברים ל־p=2, כי הסיומת 10 היא תחילת התאמה נוספת. לכן 101010 מפיק 000101. חזרה עיוורת למצב אפס הייתה מפספסת את ההתאמה השנייה. בביט הבא מאפסים hit אלא אם הושלמה התאמה חדשה; input גבוה רצוף אינו התאמות רצופות.

דוגמת המקור: עבור 0101010001, האחדות מופיעות בפלט אחרי הביטים החמישי והשביעי, ולכן 0000101000. לאחר איפוס, שלושה ביטים לכל היותר אינם יכולים להשלים התאמה; האיפוס עצמו אינו סיבית בזרם.

האינווריאנט של p מתקיים בתחילה; בכל שורה בוחרים את הסיומת הארוכה ביותר של ההיסטוריה החדשה השווה לקידומת מותרת. hit=1 בדיוק כשנוסף 0 אחרי סיומת 101, ולכן כל התאמה מתגלה, כולל חופפות, וללא התראות שווא. המימוש משתמש בשני ביטי מצב וביט פלט רשום, ובעבודה קבועה לכל דגימה. זה אינו חסם מינימלי לכל מודל פלט. אפשר גם להפוך את הקלט ולהשתמש בגלאי 0101 הקיים, בתנאי שאיפוס ומועד צפיית הפלט נשמרים.

תשובה קצרה לראיון: עקבו אחרי הקידומת שהיא סיומת, ובסיום חזרו ל־10 ולא לריק. המשך: אם הדרישה היא ללא חפיפות, שנו את המעבר לאחר התאמה ל־0; עבור 101010 תתקבל רק ההתאמה הראשונה. טעות נפוצה היא לזהות 1010 בחלון חיצוני בלי לציין היכן נשמרות ארבע הדגימות.

```systemverilog
module prep207_detect1010(input wire clk,rst,x,output reg hit);
  reg [1:0] prefix;
  // prefix is the longest proper prefix of 1010 that is a suffix of history.
  always @(posedge clk) begin
    if (rst) begin prefix<=0; hit<=0; end
    else begin
      hit<=0;
      case (prefix)
        0: prefix <= x ? 1 : 0;
        1: prefix <= x ? 1 : 2;
        2: prefix <= x ? 3 : 0;
        3: if(x) prefix<=1; else begin prefix<=2;hit<=1;end
      endcase
    end
  end
endmodule
```

### בדיקות של רצף 1010
גלאי1010 נבדק מול השוואת סיומת עצמאית ב־90,114 דגימות מכל הזרמים באורך0..12. גם הדוגמה0101010001→0000101000 אומתה. המודול prep207_detect1010 קוּמפל והורץ ב־Icarus על20,480 דגימות באורכי10, לרבות איפוס באמצע. זו הרצה של הגלאי החדש; הווריאציות הישנות נותרות עם היקף הבדיקה המתועד שלהן.

## Overlapping 0101 detection and the meaning of “no FFs”

(a) Implement an FSM detecting 0101 in a bit stream. What happens on 010101? (b) Discuss implementation with logic components and no FFs. If proposing a FIFO, explicitly specify written data, operation ordering and read interface.

Contract: accept one bit per rising clock edge; synchronous reset overrides sampling; observe output after the edge. Allow overlap, requiring two detections for 010101. Separate three interpretations of part (b): serial input with memoryless combinational gates, an externally supplied parallel four-bit window, and explicitly permitted storage such as a FIFO. Banning an FF component need not ban all storage, but storage cannot be hidden under another component name.

### Variant: overlapping 1010 detection
Design a synchronous detector for 1010 in an infinite bit stream. Accept one bit per rising edge and produce a registered one-cycle pulse when that accepted bit completes a match. Allow overlap. Synchronous active-high reset clears history/output and overrides sampling. Strings run chronologically left to right. For example 0101010001 must produce 0000101000. Give transitions, storage, a diagram and correctness argument.

### Retain the suffix after detection
Choose Moore states Q0=no match, Q1=0, Q2=01, Q3=010 and Q4=0101. Only Q4 outputs one:

| State | Input 0 | Input 1 |
|---|---|---|
| Q0 | Q1 | Q0 |
| Q1 | Q1 | Q2 |
| Q2 | Q3 | Q0 |
| Q3 | Q1 | Q4 |
| Q4 | Q3 | Q0 |

Inductively state retains the longest suffix that is a target prefix. In particular, after detection followed by zero, suffix 010 remains and state becomes Q3. Input 010101 produces 000101, detecting on edges four and six. Blindly returning to Q0 loses overlap. This five-state Moore implementation uses three binary FFs; a four-state Mealy machine can produce a combinational event under a different output-timing contract.

### No FF component need not mean no memory
With only the current input bit and memoryless, feed-forward gates, serial detection is impossible. Histories 0101 and 0001 both end with current input one but require different outputs. Additional combinational gates cannot resolve that contradiction. Feedback gates can implement latches if permitted, but then storage, timing, initialization and stability must be described; the network is no longer memoryless.

If the latest four bits are externally supplied in parallel as w[3:0], oldest to newest, then valid AND NOT w[3] AND w[2] AND NOT w[1] AND w[0] recognizes the window. This comparator stores no history, but its window producer does. valid must indicate four actual samples so initialization padding is not mistaken for data.

### FIFO: write data and declare the interface
The attached model explicitly permits a depth-four, one-bit rolling FIFO with simultaneous four-entry peek and a full indication. On each nonreset edge write DIN=x, the new input bit. When full, evict the oldest entry and insert the new bit on the same edge. Reset empties the FIFO. After update, if full, compare entries oldest-to-newest with 0101. This exactly matches the FSM output, including two detections for 010101.

An ordinary head-only FIFO need not provide four taps or automatic eviction; these features cannot be silently assumed. The FIFO and fill tracking contain storage even when no FF component is explicitly drawn outside. If all storage is forbidden and no external window exists, serial detection remains impossible. This is an explicit conditional alternative, not an evasion of the restriction through a component name.

### Executed Python logical model

```python
"""Moore FSM and explicitly stateful four-tap rolling FIFO abstraction."""

from collections import deque

TRANSITIONS = ((1, 0), (1, 2), (3, 0), (1, 4), (3, 0))


def detect_moore(bits, resets=()):
    state = 0
    reset_edges = set(resets)
    result = []
    for edge, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("binary serial input required")
        state = 0 if edge in reset_edges else TRANSITIONS[state][bit]
        result.append(int(state == 4))
    return result


def detect_rolling_fifo(bits, resets=()):
    # Requires a rolling overwrite policy and simultaneous four-entry peek.
    # These are extra contracts, not properties of every ordinary FIFO IP.
    history = deque(maxlen=4)
    reset_edges = set(resets)
    result = []
    for edge, bit in enumerate(bits):
        if bit not in (0, 1):
            raise ValueError("DIN is the current serial input bit, not a constant")
        if edge in reset_edges:
            history.clear()
        else:
            history.append(bit)
        result.append(int(len(history) == 4 and tuple(history) == (0, 1, 0, 1)))
    return result
```


### Keep a suffix that can begin the next match
Let p be the length of the longest proper prefix of 1010 that is a suffix of accepted history: 0=empty, 1=1, 2=10, 3=101. hit is an additional registered output bit. The table gives the next state and new hit:

|p|x=0: pnext,hit|x=1: pnext,hit|
|---|---|---|
|0|0,0|1,0|
|1|2,0|1,0|
|2|0,0|3,0|
|3|2,1|1,0|

Completing 1010 returns to p=2 because suffix 10 starts another match. Thus 101010 produces 000101. Blindly returning to empty loses the second occurrence. Clear hit on every other accepted sample; a held high input is not a stream of matches.

For 0101010001, detections occur after the fifth and seventh samples, yielding 0000101000. Fewer than four samples after reset cannot complete a match; reset itself is not stream data.

The state invariant holds initially; each transition chooses the longest permitted prefix that is a suffix of updated history. hit is one exactly when zero follows suffix 101, proving no missed or spurious match, including overlap. The implementation uses two prefix bits and one registered output bit, with constant work per sample. This is not a minimum across every output model. Complementing input and using the existing 0101 detector is another valid implementation when reset and output timing are preserved.

Oral answer: retain the matched-prefix suffix and return to 10 after a hit. Follow-up: for nonoverlapping matches return to 0 instead; 101010 then yields only the first hit. A common error is comparing an external four-bit window without identifying the memory that produces it.

```systemverilog
module prep207_detect1010(input wire clk,rst,x,output reg hit);
  reg [1:0] prefix;
  // prefix is the longest proper prefix of 1010 that is a suffix of history.
  always @(posedge clk) begin
    if (rst) begin prefix<=0; hit<=0; end
    else begin
      hit<=0;
      case (prefix)
        0: prefix <= x ? 1 : 0;
        1: prefix <= x ? 1 : 2;
        2: prefix <= x ? 3 : 0;
        3: if(x) prefix<=1; else begin prefix<=2;hit<=1;end
      endcase
    end
  end
endmodule
```

### 1010-detector checks
Independent whole-history suffix matching checked 90,114 samples over every stream of length 0..12, including the explicit 0101010001→0000101000 example. The prep207_detect1010 module compiled and ran in Icarus on 20,480 ten-sample-stream samples, including midstream reset. This runs the new detector; older variants retain their separately documented verification scope.

[he diagram](../diagrams/prep-207-overlap1010-1115d-he.png)

[en diagram](../diagrams/prep-207-overlap1010-1115d-en.png)

[Implementation](../solutions/digital1115d.sv)

[Implementation](../solutions/digital1115d_models.py)

[Private source](../sources/2026-11-15-batch20d-02.png)
