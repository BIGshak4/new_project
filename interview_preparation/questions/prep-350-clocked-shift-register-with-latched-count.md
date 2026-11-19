# PREP-350 — רגיסטר שמבצע מספר הזזות לפי פקודה

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## רגיסטר שמבצע מספר הזזות לפי פקודה

ממשו רגיסטר שמקבל מילה ואות בקרה שאומר כמה הזזות לבצע.

חוזה שנבחר לתרגיל המקוצר. המילה בת שמונה ביטים. בחזית עולה שבה start=1 ו־busy=0 טוענים data ולוכדים amount בטווח 0..7. לאחר מכן מבצעים בכל חזית הזזה לוגית אחת ימינה, עם אפס בביט הגבוה, עד השלמת מספר ההזזות. busy מציין עבודה ו־done הוא פולס מחזור אחד בהשלמה. amount=0 מסתיים בחזית הטעינה. פקודות start בזמן busy אינן מתקבלות. reset סינכרוני מאפס וגובר על הכול. הסבירו את הנתיב והבקר ותנו דוגמת תזמון.

### פקודה אחת נשמרת עד ההשלמה
הנתיב כולל רגיסטר R בן שמונה ביטים, חיווט להזזה אחת, מונה remaining בן שלושה ביטים, ו־busy ו־done. רק start שמתקבל במצב פנוי לוכד את המילה ואת הכמות. אין לקרוא מחדש את amount במהלך העבודה.

בחזית טעינה קובעים R=data ו־remaining=amount. אם amount אפס, מפיקים done ומשאירים busy אפס. אחרת busy נעשה 1. בכל חזית שבה busy הישן 1, קובעים Rnext={0,R[7:1]} ומקטינים remaining. אם remaining הישן היה 1, קובעים busy=0 ו־done=1. בכל מחזור אחר done מתאפס. עדכונים נבחנים לפי המצב הישן, כפי שעושות השמות לא־חוסמות ב־RTL.

למשל, פקודת data=B5h ו־amount=3 טוענת B5. בחזיתות הבאות מתקבלים 5A,2D,16. עם16 מתקבל done. פקודה חדשה בזמן שלוש ההזזות אינה מחליפה את הנתונים או המונה.

האינווריאנט אחרי j הזזות הוא R=floor(data/2^j) ו־remaining=amount−j. הוא נכון בטעינה, נשמר בהזזה, וב־j=amount נותן את התוצאה. אין ירידה מתחת לאפס כי busy נשמר רק כשנותרה הזזה. אחרי חזית טעינה נדרשים amount מחזורי עבודה, ולכן זמן הפקודה תלוי בכמות. הנפח הוא שמונה FF לנתונים, שלושה למונה ושניים לדגלים בבנייה זו, נוסף ללוגיקת הבקרה. לא נטענת מינימליות בשטח.

אם דורשים את כל ההזזה במחזור יחיד, בוחרים מבנה אחר של barrel shifter עם שלבי מוקסים. זו פשרת שטח והשהיה לעומת המימוש האיטרטיבי. נתוני בקרה אסינכרוניים דורשים ממשק סנכרון מתאים מעבר לחוזה הנוכחי.

```systemverilog
// One logical right-shift per cycle after an accepted start; eight-bit word.
module prep350(input wire clk, rst, start,
               input wire [7:0] data,
               input wire [2:0] amount,
               output reg [7:0] result,
               output reg busy, done);
  reg [2:0] remaining;
  always @(posedge clk) begin
    if (rst) begin
      result <= 8'b0;
      remaining <= 3'b0;
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (busy) begin
        result <= {1'b0, result[7:1]};
        remaining <= remaining - 3'd1;
        if (remaining == 3'd1) begin
          busy <= 1'b0;
          done <= 1'b1;
        end
      end else if (start) begin
        result <= data;
        remaining <= amount;
        busy <= (amount != 3'd0);
        done <= (amount == 3'd0);
      end
    end
  end
endmodule
```

## A clocked shift register with a latched shift count

Implement a register that receives a word and a control specifying how many shifts to perform.

Chosen contract for the abbreviated source. Use an eight-bit word. On a rising edge with start=1 and busy=0, load data and latch amount in0..7. Subsequently perform one logical right shift per edge, inserting zero at the MSB, until the captured count completes. busy indicates work and done pulses for one cycle on completion. amount=0 completes on the load edge. Ignore starts while busy. Synchronous reset clears state and takes priority. Explain datapath/control and give a timing example.

### Retain one command until completion
The datapath contains an eight-bit R register, one-position shift wiring, three-bit remaining counter, and busy/done state. Only an accepted start while idle captures word and amount. Do not reread the external amount during work.

At load set R=data and remaining=amount. Zero amount pulses done and leaves busy clear; otherwise set busy. Each edge whose old busy is one sets Rnext={0,R[7:1]} and decrements remaining. When old remaining is one, clear busy and pulse done. Clear done on other cycles. All decisions use old state, matching nonblocking RTL assignments.

For data=B5h and amount=3, load B5, then emit5A,2D,16 on the next three edges. done accompanies16. A new start during those shifts cannot replace word or count.

After j shifts the invariant is R=floor(data/2^j), remaining=amount−j. Loading establishes it; one shift preserves it; j=amount yields the result. The count cannot underflow because busy holds only when a shift remains. An accepted load is followed by amount processing cycles, so latency depends on the request. This construction stores eight data bits, three count bits and two flags, plus control logic. It makes no minimum-area claim.

A one-cycle complete-shift requirement calls for a different datapath, such as MUX-based barrel-shifter stages. This trades area against latency. Asynchronous command inputs need a separate synchronization protocol beyond this contract.

```systemverilog
// One logical right-shift per cycle after an accepted start; eight-bit word.
module prep350(input wire clk, rst, start,
               input wire [7:0] data,
               input wire [2:0] amount,
               output reg [7:0] result,
               output reg busy, done);
  reg [2:0] remaining;
  always @(posedge clk) begin
    if (rst) begin
      result <= 8'b0;
      remaining <= 3'b0;
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (busy) begin
        result <= {1'b0, result[7:1]};
        remaining <= remaining - 3'd1;
        if (remaining == 3'd1) begin
          busy <= 1'b0;
          done <= 1'b1;
        end
      end else if (start) begin
        result <= data;
        remaining <= amount;
        busy <= (amount != 3'd0);
        done <= (amount == 3'd0);
      end
    end
  end
endmodule
```

[he diagram](../diagrams/prep-350-solution-1115b-he.png)

[en diagram](../diagrams/prep-350-solution-1115b-en.png)

[he diagram](../diagrams/prep-350-waveform-1115b-he.png)

[en diagram](../diagrams/prep-350-waveform-1115b-en.png)

[Implementation](../solutions/prep_350_programmable_shift_1115b.sv)

[Private source](../sources/2026-11-15-batch20b-11.png)
