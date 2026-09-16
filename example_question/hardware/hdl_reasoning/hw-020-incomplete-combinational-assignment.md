# HW-020 — Find the unintended latch

**כותרת בעברית:** איתור Latch לא מכוון

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | HDL reasoning / ניתוח קוד תיאור חומרה |
| Difficulty | 3/10 (provisional) |
| Estimated time | 7 minutes |
| Format | hdl |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

The shared Verilog block is intended to implement y = en ? d : 0, with four-bit y and d. What happens when en=0 in the current code, and what hardware behavior is inferred? Fix it as combinational logic and explain why adding a clock would change the specification.

## שאלה — עברית

קטע Verilog המשותף אמור לממש y = en ? d : 0, כאשר y ו־d הם בני ארבעה ביטים. מה קורה בקוד הקיים כאשר en=0, ואיזו התנהגות חומרה מתקבלת? תקנו ללוגיקה קומבינטורית והסבירו מדוע הוספת שעון תשנה את המפרט.

## Shared code / קוד משותף

```verilog
always @(*) begin
  if (en)
    y = d;
end
```

## Hint — English

Check whether every output receives a value on every path.

## רמז — עברית

בדקו האם כל פלט מקבל ערך בכל מסלול ביצוע.

## Reference solution — English

When en=0, y is not assigned and retains its previous value: latch behavior. Add else y=4'b0000, or set a default y=0 before the if. A clocked register would update only on clock edges and would not implement the intended combinational function.

## כיוון פתרון — עברית

כאשר en=0 אין השמה ל־y ולכן הוא שומר את ערכו הקודם: התנהגות של latch. מוסיפים else y=4'b0000, או ברירת מחדל y=0 לפני ה־if. אוגר עם שעון היה מתעדכן רק בחזיתות ולא היה מממש את הפונקציה הקומבינטורית שנדרשה.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: incomplete assignments and latches](https://hdlbits.01xz.net/wiki/Always_nolatches)
