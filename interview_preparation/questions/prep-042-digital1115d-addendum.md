# PREP-042 — גלאי עלייה עם פולס של מחזור שעון אחד

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## גלאי עלייה עם פולס של מחזור שעון אחד

תכננו רכיב המפיק `1` במשך מחזור שעון אחד כאשר מזוהה עלייה בקלט מ־`0` ל־`1`. בשאר המחזורים הפלט יהיה `0`. קלט שנשאר גבוה אינו יוצר פולסים נוספים, וירידה מ־`1` ל־`0` אינה יוצרת פולס.

למימוש זה הניחו קלט בינארי `x` הסינכרוני לשעון ונדגם בחזית העולה. הפלט `pulse` רשום ומתעדכן לאחר חזית הדגימה. הדגימה הקודמת מתחילה ב־`0`, ולכן דגימה ראשונה גבוהה נחשבת עלייה.

הציגו מעגל, משוואות מצב ודוגמת תזמון. אפשר להציג איפוס סינכרוני פעיל בגבוה לקביעת מצב ההתחלה.

הנחות והגדרות: סינכרוניות הקלט, אופי הפלט הרשום, מצב ההתחלה ופרטי האיפוס לא הוגדרו בצילום. הם נכתבו כאן במפורש כדי להגדיר מימוש חד־משמעי. אין דרישה לזהות באופן מיידי כל מעבר אסינכרוני בין דגימות.

### הרחבה: הארכת הדופק ל־N מחזורים
השתמשו בזיהוי העלייה כדי להפיק y שנשאר1 במשך N מחזורי שעון, כולל המחזור שמתחיל בחזית שזיהתה את העלייה. N הוא פרמטר שלם וחיובי בזמן בנייה. עלייה חדשה בזמן ש־y=1 מתחילה מחדש חלון מלא של N מחזורים. הקלט ממשיך להידגם בכל מחזור, ולכן רמה גבוהה מתמשכת אינה טריגר חדש. איפוס סינכרוני פעיל־גבוה מאפס את ההיסטוריה ואת הפלט וגובר על טריגר. קלט ראשון1 לאחר איפוס נחשב עלייה. הציגו מעגל, מצב, דוגמת תזמון ועלות.

**הצעה לפתרון — זיהוי עלייה בין דגימות, עם פלט רשום**

הרעיון הוא להפריד בין שתי שאלות: האם הקלט עכשיו `1`, והאם הוא היה `0` בדגימה הקודמת. רק כאשר שתי התשובות נכונות, נרצה פולס. רמה גבוהה לבדה אינה אירוע חדש: אם הקלט נשאר `1` במשך חמישה מחזורים, צריכה להיווצר רק פעימה אחת.

**הבהרות לפני המימוש**

המקור אינו מגדיר יחס לשעון, אתחול או איפוס. במימוש כאן מניחים שהקלט `x` סינכרוני לשעון, עומד בדרישות זמני הכנה והחזקה, ונדגם בחזית העולה. הפלט `pulse` הוא פלט רשום: הוא מתעדכן לאחר חזית הדגימה ונשמר עד החזית הבאה. לאחר אתחול הדגימה הקודמת היא `0`, ולכן דגימה ראשונה שערכה `1` נחשבת עלייה. נציג איפוס סינכרוני פעיל בגבוה כדרך לקבוע מצב התחלה; זו הבהרת מימוש שהוספנו, ולא דרישה שהופיעה בתמונה.

**1. צריך לזכור את העבר**

אי אפשר להחליט לפי `x` הנוכחי בלבד. כאשר הוא `1`, יש הבדל בין מצב שבו זה עתה עלה מ־`0` לבין מצב שבו הוא כבר גבוה מזמן. לכן שומרים באוגר חד־ביטי בשם `previous` את הדגימה הקודמת של הקלט.

בכל חזית פעילה, לפני עדכון האוגרים, התנאי לעלייה הוא:

```text
rising = x AND NOT(previous)
```

התנאי אינו XOR: XOR מזהה גם ירידה, ואילו כאן ירידה אינה אמורה ליצור פולס.

**2. רושמים גם את תוצאת הזיהוי**

נשתמש בשני תאי זיכרון חד־ביטיים: האחד שומר את `previous`, והשני שומר את הפלט `pulse`. בכל חזית עולה ללא איפוס מחשבים את שני ערכי המצב הבאים מתוך הקלט והמצב הישן:

```text
pulse_next    = x AND NOT(previous)
previous_next = x
```

החיבורים הם: `x` מגיע לכניסת הנתונים של אוגר `previous` ולכניסה אחת של שער AND. היציאה ההפוכה של `previous`, או שער NOT על יציאתו, מגיעה לכניסה השנייה של AND. תוצאת AND מגיעה לכניסת הנתונים של אוגר `pulse`. שני האוגרים מקבלים את אותו שעון. אם ספריית התאים אינה מספקת יציאה הפוכה, משתמשים במהפך נפרד.

חשוב: שני האוגרים מתעדכנים יחד. חישוב `pulse_next` משתמש ב־`previous` הישן, ולא ב־`x` שזה עתה יישמר בו. הנה טבלת המעבר כאשר האיפוס אינו פעיל:

```text
previous  x  | pulse_next  previous_next
    0     0  |     0            0
    0     1  |     1            1
    1     0  |     0            0
    1     1  |     0            1
```

כאשר האיפוס פעיל בחזית, שני ערכי המצב הבאים הם `0`, בלי קשר ל־`x`.

**3. מימוש ב־SystemVerilog**

```systemverilog
module rising_edge_detector (
    input  logic clk,
    input  logic rst,
    input  logic x,
    output logic pulse
);
    logic previous;

    always_ff @(posedge clk) begin
        if (rst) begin
            previous <= 1'b0;
            pulse    <= 1'b0;
        end else begin
            pulse    <= x & ~previous;
            previous <= x;
        end
    end
endmodule
```

השמות `<=` בתוך בלוק שעוני הן השמות לא חוסמות. אגפי ימין מחושבים מהמצב שלפני העדכון; לכן שתי השורות מקיימות את המשוואות יחד. אין כאן צורך להפיק שעון חדש מתוך הקלט, ואין להשתמש ב־`posedge x` במקום בשעון המערכת. לצורך האתחול יש להפעיל `rst` בחזית שעון אחת לפחות.

**4. עוקבים אחרי דוגמה**

לאחר איפוס, `previous=0` ו־`pulse=0`. בכל עמודה להלן מופיעים הקלט שנדגם והפלט הרשום לאחר אותה חזית:

```text
sample:    1  2  3  4  5  6  7  8  9 10 11 12
x:         0  0  0  1  1  1  0  1  0  0  1  1
pulse:     0  0  0  1  0  0  0  1  0  0  1  0
```

בדגימה הרביעית, הקלט הוא `1` והדגימה הקודמת הייתה `0`, ולכן נרשם פולס. בדגימה החמישית הקלט עדיין `1`, אך גם `previous` כבר `1`, ולכן הפלט חוזר ל־`0`. בדגימה השביעית הקלט יורד ל־`0`, ולכן אין פולס. בדגימה השמינית יש עלייה חדשה ונוצר פולס חדש.

**5. למה זה עובד ולמה הפולס נמשך מחזור אחד?**

לפני כל חזית ללא איפוס, `previous` שווה לדגימת הקלט שנשמרה בחזית הקודמת, או ל־`0` שנקבע באיפוס. לכן המשוואה מחזירה `1` בדיוק עבור מעבר דגימות `0→1`. במקביל שומרים את הדגימה הנוכחית כדי לשמור על הטענה גם בחזית הבאה.

אם נוצר פולס, באותה חזית נשמר `previous=1`. בחזית הבאה הפולס יהיה `0` בכל מקרה: אם הקלט נשאר `1`, התנאי `NOT(previous)` הוא `0`; ואם הקלט ירד ל־`0`, הכניסה `x` היא `0`. הפלט הרשום נשאר גבוה בין שתי החזיתות, למשך מחזור שעון אחד במודל הסינכרוני האידאלי. איפוס בחזית הבאה מוריד אותו גם הוא. כל עלייה חדשה אחרי דגימת `0` יכולה לייצר פולס נוסף.

**6. עלות, תזמון והחלופה בעלת אוגר אחד**

המימוש המוצג משתמש בשני אוגרים חד־ביטיים, בתנאי AND ובהיפוך, לצד לוגיקת איפוס לפי התאים הזמינים. זמן העדכון קבוע בכל מחזור ומצב הזיכרון קבוע. אין כאן הוכחה למינימום שערים, שטח או השהיה. הפלט משקף עלייה בין דגימות לאחר חזית הדגימה שלה, בכפוף להשהיית השעון־למוצא; הוא אינו גלאי מיידי של כל שינוי פיזי בין חזיתות.

לעיתים מציעים אוגר יחיד וקשר צירופי `pulse = x & ~previous`. זו חלופה בעלת חוזה תזמון אחר: הפלט תלוי בקלט החי, וכאשר האוגר דוגם `1` גם `previous` נעשה `1` והפלט יורד. אין להציג אותה אוטומטית כפלט רשום שנותר גבוה במשך המחזור שאחרי דגימת העלייה. אם הקלט משתנה בזמן שרירותי, הפולס עלול להיות קצר ממחזור, להיחתך בחזית או להכיל הפרעות. אפשר לקבל התנהגות מתאימה תחת הנחות תזמון מוגדרות אחרות, אך צריך לכתוב אותן במפורש; אין להסיק מכאן ששני אוגרים הם מינימום בכל ניסוח של השאלה.

**אם הקלט אסינכרוני:** המעגל כפי שהוא מניח קלט סינכרוני. בדרך כלל מוסיפים סנכרון מתאים לפני הזיהוי, ומנתחים בנפרד את הסיכון למטא־יציבות ואת זמני הדגימה. שרשרת סנכרון מפחיתה את ההסתברות לכשל; היא אינה מבטלת מטא־יציבות לחלוטין ואינה מבטיחה לכידת פולס קצר שנופל בין דגימות. דרישה לתפיסת כל אירוע אסינכרוני עשויה לדרוש מתיחת פולס, החלפת ביט או פרוטוקול העברת אירועים אחר.

**תשובה קצרה לראיון:** אשמור את הדגימה הקודמת באוגר. בכל חזית אחשב פלט רשום שהוא הקלט הנוכחי AND היפוך הדגימה הקודמת, ובמקביל אשמור את הקלט לפעם הבאה. כך רק `0→1` נותן פולס; קלט שנשאר גבוה וירידה אינם מפעילים אותו. אבהיר שהקלט סינכרוני ושמצב ההתחלה הוא אפס.

אימות: מודל פייתון נבדק מול אורקל עצמאי שמחשב הפרש בין דגימות, לכל 16,382 הרצפים הבינאריים באורכים 0–12 עם שתי אפשרויות למצב קודם, ול־2,048 עקבות עם איפוס באמצע. נבדקו גם הדוגמה `0,1,1,0,1` וקלט גבוה במשך 100 מחזורים. קוד SystemVerilog צורף אך לא הורץ בסימולטור HDL ולא נמדד בתזמון פיזי.

### שמרו כמה מחזורים נשארו, ועדכנו היסטוריה תמיד
נחזיק previous ואת remaining בטווח0..N. לפני כל חזית חשבו rise=x AND NOT previous. אם rst=1 קבעו previous=0,remaining=0. אחרת עדכנו previous=x ובחרו: אם rise אז remaining=N; אחרת אם remaining>0 הפחיתו1; אחרת השאירו0. הפלט אחרי החזית הוא y=(remaining>0). חישוב rise משתמש ב־previous הישן, לא בחדש.

ל־N=3 וקלט0,1,1,0,1,0,0,0 מתקבל remaining=0,3,2,1,3,2,1,0 ופלט0,1,1,1,1,1,1,0. העלייה השנייה מפעילה מחדש את הספירה. אם אין טריגר נוסף, לאחר החזית המפעילה הערכים הם N,N−1,…,1,0; יש בדיוק N מרווחי שעון גבוהים. N=1 משחזר את הגלאי החד־מחזורי.

אינווריאנט: אם העלייה האחרונה אחרי האיפוס הייתה בחזית t, אז אחרי k חזיתות נוספות ללא עלייה remaining=max(N−k,0). איפוס מבטל את החלון; עלייה חדשה מאפסת את k ומקבלת עדיפות על הפחתה. כך מוכחת גם הארכה נכונה בחפיפות. יש לעדכן previous גם כשהמונה פעיל, אחרת רמה גבוהה ישנה יכולה להתפרש כעלייה נוספת.

המימוש משתמש בביט היסטוריה וב־ceil(log2(N+1)) ביטי מונה, עם מינימום ביט אחד כש־N=1. עלייה אחת מתחילה חלון, לא שעון חדש; כל הרכיבים נשארים על clk המקורי. אין כאן מדידת אורך הדופק הנכנס או תפיסה מובטחת של פולס אסינכרוני קצר. איפוס באמצע חלון מקצר אותו במכוון. השהיה וגליצ׳ים של פענוח הפלט דורשים טיפול רגיל אם הפלט מחובר לחוץ או משמש בקרה; אין להשתמש בו כשעון ללא תכנון מתאים.

תשובה קצרה: גלאי עלייה ומונה יורד הנטען ב־N, עם טעינה בעדיפות; הפלט1 כל עוד המונה אינו אפס. המשך: במדיניות שמתעלמת מטריגר בזמן פעילות, טענו רק כאשר rise AND remaining==0, אך עדיין עדכנו previous תמיד. גם כאן צריך להגדיר אם עלייה בחזית סיום מתקבלת; זו מדיניות אחרת ולא אותו מימוש.

```systemverilog
module prep042_stretch #(parameter integer N=3,
                         parameter integer CW=(N<2 ? 1 : $clog2(N+1)))
 (input wire clk,rst,x,output wire y);
  reg previous;
  reg [CW-1:0] remaining;
  initial if(N<1) $fatal(1,"N must be positive");
  always @(posedge clk) begin
    if(rst) begin previous<=0;remaining<=0;end
    else begin
      previous<=x;
      if(x && !previous) remaining<=N;
      else if(remaining!=0) remaining<=remaining-1'b1;
    end
  end
  assign y=(remaining!=0);
endmodule
```

### בדיקות של חלון N מחזורים
מודל החלון נבדק ב־51,480 צעדים ותקפי מעבר עבור N=1,2,3,8,16, מול אורקל המבוסס על זמן העלייה האחרונה. המודול החדש prep042_stretch קוּמפל והורץ ב־Icarus עבור N=1,3,8 על20,480 דגימות, כולל איפוס באמצע זרם. זהו אימות של מודול ההארכה החדש, ולא הרצה חדשה של קוד הגלאי המקורי; מצבי האימות הקודמים מתייחסים לקטעים הישנים. ללא סינתזה, ניתוח setup/hold או בדיקת חומרה.

## Rising-edge detector with a one-clock-cycle pulse

Design a component that outputs `1` for one clock cycle when the input rises from `0` to `1`, and outputs `0` otherwise. A held-high input must not generate repeated pulses, and a `1` to `0` fall must not generate a pulse.

For this implementation, assume a binary input `x` synchronous to the clock and sampled on its rising edge. The output `pulse` is registered and updates after the sampling edge. The previous sample starts at `0`, so the first high sample counts as a rise.

Give the circuit, next-state equations and a timing example. A synchronous active-high reset may be used to establish the initial state.

Clarification: the source does not define input synchrony, registered-output semantics, initialization or reset details. These are explicit assumptions for a well-defined implementation. Instant detection of every asynchronous transition between samples is not required.

### Follow-up: stretch the pulse to N cycles
Use rise detection to produce y that stays high for N clock periods, including the interval beginning at the edge detecting the rise. N is a positive integer construction-time parameter. A new rise while y is high restarts a complete N-cycle window. Continue sampling input every cycle, so a held high level is not a new trigger. Synchronous active-high reset clears history/output and overrides a trigger. A first high sample after reset counts as a rise. Give circuit/state, timing and cost.

**Proposed solution — sampled rising-edge detection with a registered output**

Separate two questions: is the input `1` now, and was its preceding sample `0`? A pulse is required only when both conditions hold. A high level is not itself a new event: five high samples should produce one pulse.

**Clarify the timing and initial state**

The source does not define clock relationship, initialization or reset. Here `x` is synchronous to the clock, meets setup/hold requirements, and is sampled on the rising clock edge. `pulse` is registered: it updates after the sampling edge and holds until the next edge. The previous sample starts at `0`, so a first high sample counts as a rise. A synchronous active-high reset is shown as one implementation of initialization; it is an explicit assumption, not an original source requirement.

**1. Remember the preceding sample**

The current input alone is insufficient. If it is high, we must distinguish a new rise from a level that was already high. A one-bit register named `previous` stores the preceding sampled input.

At an active edge, before updating the registers, the rising condition is:

```text
rising = x AND NOT(previous)
```

Do not substitute XOR: XOR also detects a falling transition, whereas a falling input must not generate a pulse here.

**2. Register the detection result too**

Use two one-bit registers: one for `previous` and one for output `pulse`. At each rising clock edge without reset, compute both next-state values from the current input and old state:

```text
pulse_next    = x AND NOT(previous)
previous_next = x
```

Connect `x` to the data input of the `previous` register and one AND input. Connect the inverted `previous` output to the other AND input, using an inverter if the cell has no complementary output. Drive the data input of the `pulse` register with the AND output. Both registers use the same clock.

The registers update together: `pulse_next` uses the old `previous`, not the value that is about to replace it. With reset inactive, the transition table is:

```text
previous  x  | pulse_next  previous_next
    0     0  |     0            0
    0     1  |     1            1
    1     0  |     0            0
    1     1  |     0            1
```

When reset is high at a clock edge, both next-state values are `0`, independent of `x`.

**3. SystemVerilog implementation**

```systemverilog
module rising_edge_detector (
    input  logic clk,
    input  logic rst,
    input  logic x,
    output logic pulse
);
    logic previous;

    always_ff @(posedge clk) begin
        if (rst) begin
            previous <= 1'b0;
            pulse    <= 1'b0;
        end else begin
            pulse    <= x & ~previous;
            previous <= x;
        end
    end
endmodule
```

Nonblocking assignments `<=` in the clocked block evaluate their right-hand sides from the pre-update state. Both equations therefore take effect together. Do not derive a new clock from the input or replace the system-clock event with `posedge x`. Assert `rst` across at least one active clock edge to establish the initial state.

**4. Walk through a trace**

After reset, `previous=0` and `pulse=0`. Each column shows the input sampled at an edge and the registered output after that edge:

```text
sample:    1  2  3  4  5  6  7  8  9 10 11 12
x:         0  0  0  1  1  1  0  1  0  0  1  1
pulse:     0  0  0  1  0  0  0  1  0  0  1  0
```

At sample four the input is high and the preceding sample was low, so a pulse is stored. At sample five the input remains high but `previous` is already high, so output returns low. Sample seven is a fall and produces no pulse. Sample eight is a fresh rise and produces a new pulse.

**5. Correctness and one-cycle duration**

Before each nonreset edge, `previous` holds the input sampled at the preceding edge, or the zero established by reset. Thus the detection expression is one exactly for a sampled `0→1` transition. Saving the current input in parallel preserves this invariant for the next edge.

If a pulse is stored, that same edge stores `previous=1`. At the next edge the pulse is zero either way: a high input makes `NOT(previous)` zero, and a low input makes `x` zero. The registered output stays high between these two edges, for one clock period in the ideal synchronous model. A reset at the next edge also lowers it. A subsequent rise after a low sample can generate another pulse.

**6. Cost, timing and the one-register alternative**

This construction uses two one-bit registers, an AND condition and inversion, plus reset logic appropriate to the available cells. Per-edge work and state storage are constant. This is not a gate-count, area or delay minimality proof. Output represents a rise between samples after the corresponding sampling edge, subject to clock-to-output delay. It does not instantly detect every physical transition between edges.

A common alternative uses one register and combinational `pulse = x & ~previous`. It has a different timing contract: output depends on the live input, and goes low when the register samples a high input and updates `previous` to high. It is not automatically a registered pulse held throughout the cycle after sampling the rise. With arbitrary input timing it can be shorter than a cycle, be truncated at an edge or glitch. It can suit other explicit timing assumptions, but those assumptions must be stated. Accordingly, two registers are not claimed to be the universal minimum for every interpretation of the source.

**For an asynchronous input:** this circuit assumes a synchronous input. Add an appropriate synchronization strategy before detection and separately analyze metastability risk and sampling. A synchronizer reduces failure probability; it does not eliminate metastability or guarantee capture of a short pulse between samples. Capturing every asynchronous event may require pulse stretching, a toggle scheme or another event-transfer protocol.

**Interview answer:** Store the preceding input sample. At each clock edge register current input AND NOT previous sample as the pulse, and save the current input for next time. Only sampled `0→1` creates a pulse; held-high and falling inputs do not. State the synchronous-input and zero-initialization assumptions.

Verification: a Python clock-edge model matched an independent sample-difference oracle for 16,382 binary streams of lengths 0–12 across both initial previous values and 2,048 midstream-reset traces. The `0,1,1,0,1` example and a 100-cycle held-high trace were also checked. The supplied SystemVerilog has not been HDL-simulated or physically timed.

### Keep remaining intervals and always update history
Store previous and remaining in 0..N. Before an edge compute rise=x AND NOT previous. If rst, set previous=0 and remaining=0. Otherwise update previous=x and choose: on rise load remaining=N; else decrement if positive; otherwise hold zero. After the edge y=(remaining>0). rise uses the old previous sample, not its update.

For N=3 and samples 0,1,1,0,1,0,0,0, remaining is 0,3,2,1,3,2,1,0 and output 0,1,1,1,1,1,1,0. The second rise restarts the interval. With no later trigger, post-trigger values are N,N−1,…,1,0, giving exactly N high clock intervals. N=1 reproduces the one-cycle detector.

Invariant: if the latest post-reset rise was at edge t, then after k later edges without another rise remaining=max(N−k,0). Reset cancels the interval; a new rise resets k and takes priority over decrement. This also proves overlapping-trigger behavior. Update previous while busy, or an old high level can be mistaken for a new rise.

Storage is one history bit plus ceil(log2(N+1)) counter bits, with at least one counter bit at N=1. A rise starts a window rather than a new clock; every register stays on the source clock. This does not measure input pulse width or guarantee capture of short asynchronous pulses. Reset during a window deliberately truncates it. Decode delay/glitches need normal implementation treatment if output crosses an interface or controls logic; this is not an approved generated-clock construction.

Oral answer: a rise detector loads a down-counter with N, with load priority; y is one while the counter is nonzero. Follow-up: an ignore-while-active policy loads only on rise AND remaining==0 while still updating previous every cycle. Define whether a rise at the finishing edge is accepted; that is a different policy.

```systemverilog
module prep042_stretch #(parameter integer N=3,
                         parameter integer CW=(N<2 ? 1 : $clog2(N+1)))
 (input wire clk,rst,x,output wire y);
  reg previous;
  reg [CW-1:0] remaining;
  initial if(N<1) $fatal(1,"N must be positive");
  always @(posedge clk) begin
    if(rst) begin previous<=0;remaining<=0;end
    else begin
      previous<=x;
      if(x && !previous) remaining<=N;
      else if(remaining!=0) remaining<=remaining-1'b1;
    end
  end
  assign y=(remaining!=0);
endmodule
```

### N-cycle-window checks
The window model passed 51,480 trace/transition steps for N=1,2,3,8,16 against an independent last-rise timestamp oracle. The new prep042_stretch module compiled and ran in Icarus for N=1,3,8 across 20,480 samples, including midstream resets. This validates the new stretcher module rather than rerunning the original detector listing; earlier evidence applies to the older code. No synthesis, setup/hold closure or physical hardware test was performed.

[he diagram](../diagrams/prep-042-ncycle-window-1115d-he.png)

[en diagram](../diagrams/prep-042-ncycle-window-1115d-en.png)

[Implementation](../solutions/digital1115d.sv)

[Implementation](../solutions/digital1115d_models.py)

[Private source](../sources/2026-11-15-batch20d-12.png)
