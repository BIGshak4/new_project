# HW-019 — Trace a nonblocking pipeline

**כותרת בעברית:** מעקב אחר צינור עם השמות לא חוסמות

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | HDL reasoning / ניתוח קוד תיאור חומרה |
| Difficulty | 3/10 (provisional) |
| Estimated time | 7 minutes |
| Format | waveform |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

In the shared Verilog block, a and b are one-bit registers and are initially 0 after synchronous reset. With reset=0, the next three sampled input values are 1,0,1. Give (a,b) after each edge. Then replace both <= operators inside the else block with = and give the values produced by this block in simulation. Explain the difference; assume no other process reads or writes these registers.

## שאלה — עברית

בקטע Verilog המשותף a ו־b הם אוגרים של ביט אחד, ששניהם אפס לאחר איפוס סינכרוני. כאשר reset=0, שלוש דגימות הקלט הבאות הן 1,0,1. תנו את (a,b) אחרי כל חזית. לאחר מכן החליפו את שני אופרטורי <= שבענף else באופרטור = ותנו את הערכים שמפיק קטע זה בסימולציה. הסבירו את ההבדל; הניחו שאין תהליך אחר שקורא או כותב את האוגרים.

## Shared code / קוד משותף

```verilog
always @(posedge clk) begin
  if (reset) begin
    a <= 1'b0;
    b <= 1'b0;
  end else begin
    a <= in_bit;
    b <= a;
  end
end
```

## Hint — English

Mark which value of a the second assignment reads.

## רמז — עברית

סמנו איזה ערך של a נקרא בהשמה השנייה.

## Reference solution — English

With nonblocking assignments: (1,0),(0,1),(1,0). With blocking assignments in this order: (1,1),(0,0),(1,1). Nonblocking right-hand sides use old register values; blocking updates a before b reads it within this block.

## כיוון פתרון — עברית

בהשמות לא חוסמות: (1,0),(0,1),(1,0). בהשמות חוסמות בסדר הנתון: (1,1),(0,0),(1,1). בהשמות לא חוסמות צד ימין משתמש בערכי האוגרים הישנים; בהשמות חוסמות a מתעדכן לפני ש־b קורא אותו בתוך הקטע.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [MIT 6.111: sequential assignments and FSMs](https://classes.csail.mit.edu/6.111/f2006/handouts/L06.pdf)
