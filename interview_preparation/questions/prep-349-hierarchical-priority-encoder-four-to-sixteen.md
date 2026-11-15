# PREP-349 — מקודד עדיפות מארבע כניסות עד שש־עשרה

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## מקודד עדיפות מארבע כניסות עד שש־עשרה

א. תכננו מקודד עדיפות 4 ל־2 משערים. כאשר יותר מקלט אחד הוא 1, הקלט בעל האינדקס הגבוה ביותר זוכה. הפיקו גם valid שמציין שלפחות קלט אחד דלוק. כאשר כל הקלטים אפס, קבעו code=00 ו־valid=0.
ב. השתמשו במקודדי 4 ל־2 כדי לבנות מקודד 16 ל־4. מותר להוסיף שערים ומוקסים לחיבור ההיררכיה. הסבירו כיצד מבחינים בין קבוצה ריקה לקבוצה שבה רק ביט 0 דלוק.

### מקודדים גם את הקבוצה וגם את המיקום בתוכה
נסמן x3 בעדיפות הגבוהה ביותר. טבלת העדיפות המקוצרת היא 1xxx→11, 01xx→10, 001x→01, 0001→00. בכל ארבע השורות valid=1. עבור 0000 מתקבל valid=0 וקוד 00. לכן

```text
valid = x3 OR x2 OR x1 OR x0
c1 = x3 OR x2
c0 = x3 OR ((NOT x2) AND x1)
```

x בסימון הטבלה פירושו שהקלט אינו משנה את התוצאה באותה שורה. הוא אינו ערך לא ידוע בסימולציה.

ב־16 כניסות חלקו את המילה לקבוצות x[3:0], x[7:4], x[11:8], x[15:12]. ארבעה מקודדים מפיקים קוד מקומי ושדה valid לכל קבוצה. מקודד חמישי מקבל את ארבעת אותות valid ומפיק את מספר הקבוצה הגבוהה ביותר שיש בה בקשה. שני ביטי הפלט הגבוהים הם קוד הקבוצה, ושני הנמוכים הם הקוד המקומי של אותה קבוצה. בוחרים אותו באמצעות מוקס 4 ל־1 ברוחב שני ביטים. כאשר valid הכללי אפס מכריחים את ארבעת ביטי הקוד לאפס.

למשל, עבור x=16'h1101 יש בקשות בביטים 12,8,0. קבוצה 3 זוכה, הקוד המקומי שלה 00, ולכן הפלט הוא 1100, כלומר 12.

אם הרכיב הנתון מוציא רק שני ביטי קוד, חייבים להפיק valid נוסף באמצעות OR של ארבע כניסות הקבוצה. קוד 00 לבדו אינו מבחין בין ריק לבין בקשה בביט הנמוך. ההיררכיה משתמשת בחמישה מקודדי 4 ל־2 ובבחירת קוד מקומי. לא נטענת מינימליות במספר שערים עבור ספריית תאים מסוימת. נכונות נובעת מבחירת הקבוצה הגבוהה ביותר ולאחריה הביט הגבוה ביותר בתוכה.

```systemverilog
// Combinational, unsigned, highest numbered asserted input wins.
module prep349_pe4(input wire [3:0] x, output wire valid, output wire [1:0] code);
  assign valid = |x;
  assign code[1] = x[3] | x[2];
  assign code[0] = x[3] | (~x[2] & x[1]);
endmodule

module prep349_pe16(input wire [15:0] x, output wire valid, output wire [3:0] code);
  wire [3:0] group_valid;
  wire [1:0] local_code [0:3];
  wire [1:0] group_code;
  genvar g;
  generate for (g=0; g<4; g=g+1) begin: groups
    prep349_pe4 cell4(x[4*g +: 4], group_valid[g], local_code[g]);
  end endgenerate
  prep349_pe4 group_encoder(group_valid, valid, group_code);
  assign code = valid ? {group_code, local_code[group_code]} : 4'b0000;
endmodule
```

## A priority encoder from four inputs to sixteen

A. Design a gate-level 4-to-2 priority encoder. If several inputs are one, the highest numbered input wins. Also produce valid, indicating at least one asserted input. Define code=00 and valid=0 for all-zero input.
B. Build a 16-to-4 encoder using the four-input cells, with gates and multiplexers allowed to connect them. Explain how an empty group differs from a group containing only bit zero.

### Encode the group and its local winner
With x3 highest priority, the compact table is 1xxx→11, 01xx→10, 001x→01, 0001→00, all with valid=1. Input 0000 gives valid=0 and code=00. Thus

```text
valid = x3 OR x2 OR x1 OR x0
c1 = x3 OR x2
c0 = x3 OR ((NOT x2) AND x1)
```

The x symbols are table don’t-care positions, not unknown simulation values.

Partition sixteen inputs into x[3:0], x[7:4], x[11:8], x[15:12]. Four encoders produce each local code and valid. A fifth four-input encoder processes the group-valid vector, selecting the highest nonempty group. Its group code forms the upper two result bits. A two-bit-wide 4-to-1 selector supplies the winning group’s local code as the lower two bits. Force all four code bits to zero when global valid is zero.

For x=16'h1101, asserted bits are 12,8,0. Group three wins with local code00, yielding code1100, or12.

If a supplied cell has only code outputs, derive its valid separately by ORing the group inputs. Code00 alone cannot distinguish empty from bit-zero asserted. This construction uses five four-input encoders plus local-code selection. It makes no technology-specific minimum-gate claim. Correctness follows by selecting the highest occupied group and then its highest occupied position.

```systemverilog
// Combinational, unsigned, highest numbered asserted input wins.
module prep349_pe4(input wire [3:0] x, output wire valid, output wire [1:0] code);
  assign valid = |x;
  assign code[1] = x[3] | x[2];
  assign code[0] = x[3] | (~x[2] & x[1]);
endmodule

module prep349_pe16(input wire [15:0] x, output wire valid, output wire [3:0] code);
  wire [3:0] group_valid;
  wire [1:0] local_code [0:3];
  wire [1:0] group_code;
  genvar g;
  generate for (g=0; g<4; g=g+1) begin: groups
    prep349_pe4 cell4(x[4*g +: 4], group_valid[g], local_code[g]);
  end endgenerate
  prep349_pe4 group_encoder(group_valid, valid, group_code);
  assign code = valid ? {group_code, local_code[group_code]} : 4'b0000;
endmodule
```

[he diagram](../diagrams/prep-349-given-1115b-he.png)

[en diagram](../diagrams/prep-349-given-1115b-en.png)

[he diagram](../diagrams/prep-349-solution-1115b-he.png)

[en diagram](../diagrams/prep-349-solution-1115b-en.png)

[Implementation](../solutions/prep_349_priority_encoder_1115b.sv)

[Private source](../sources/2026-11-15-batch20b-06.png)
