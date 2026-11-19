# PREP-014 — השארת ה־1 המשמעותי ביותר במספר בן 8 ביטים

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## השארת ה־1 המשמעותי ביותר במספר בן 8 ביטים

תכננו מעגל צירופי המקבל וקטור בן שמונה ביטים ומשאיר בפלט רק את ביט ה־1 המשמעותי ביותר בקלט. כל יתר ביטי הפלט יהיו 0. אם הקלט כולו 0, גם הפלט יהיה 0.

לדוגמה: `00101011 → 00100000`. הפלט הוא וקטור בן שמונה ביטים, ולא מספר המיקום של הביט. השתמשו בשערים לוגיים והסבירו את המימוש.

### וריאציית השהיה משוקללת: רק AND עולה זמן
למעגל שמבודד את האחד השמאלי ב־8 סיביות, השיגו השהיה קטנה מ־5.5τ במקום מימוש שדווח עליו 11τ. במודל התרגיל כל שער AND בעל שתי כניסות עולה 1τ; לשערי OR, NOT ו־XOR השהיה אפס. כל שערי שתי הכניסות מוגבלים לשתי כניסות, חיווט ופיצול אות חופשיים, וכל שמונה הקלטים מגיעים בזמן אפס. בחרו רשת קומבינטורית חסרת משוב. החזירו אפס עבור קלט אפס. הציגו רשת והוכחת זמן לפי המודל הזה, והבחינו בינו לבין מודל שבו לכל שער השהיה אחידה.

**מה מבקשים?** להשאיר רק את ה־1 המשמעותי ביותר בקלט בן שמונה ביטים, ולאפס את כל הביטים שמתחתיו. הפלט נשאר וקטור בן שמונה ביטים. למשל 00101011 הופך ל־00100000. הדוגמה מבהירה שה־1 הראשון עצמו נשמר, למרות הביטוי ״והחל ממנו״ בנוסח. עבור 00000000 נגדיר פלט 00000000.

נסמן את הקלט x[7:0] ואת הפלט y[7:0], כאשר x7 הוא הביט השמאלי, ה־MSB.

**הכלל לכל ביט:** מותר ל־yi להיות 1 רק אם xi=1 ואין אף 1 במקומות המשמעותיים יותר.

לכן:
```text
y7 = x7
y6 = x6 AND NOT(x7)
y5 = x5 AND NOT(x7 OR x6)
y4 = x4 AND NOT(x7 OR x6 OR x5)
...
y0 = x0 AND NOT(x7 OR x6 OR x5 OR x4 OR x3 OR x2 OR x1)
```

כל מעבר כאן נובע מאותו כלל: קודם דורשים שהביט עצמו יהיה 1, ואז חוסמים אותו אם כבר יש 1 משמאלו. זהו בורר עדיפות בעל מוצא one-hot, כלומר לכל היותר ביט אחד דולק. הפלט אינו האינדקס של הביט; לדוגמה לא מחזירים 5 אלא את המסכה 00100000.

**למה הכלל נכון?** כל ביט מעל ה־1 הראשון הוא 0 מלכתחילה. ה־1 הראשון עובר כי אין מעליו אף 1. כל ביט שמתחתיו נחסם כי יש מעליו לפחות את ה־1 הראשון. אם אין בכלל אחדים, כל ביט פלט 0.

**מימוש פשוט עם שיתוף חישובים:** נגדיר H7=0, ונחשב מהמקום הגבוה לנמוך:
`yi = xi AND NOT(Hi)`, `H(i−1) = Hi OR xi`.
הדגל Hi מציין אם יש 1 מעל מקום i. זו שרשרת קומבינטורית, לא סדר פעולות בשעון ולא FF. השטח גדל לינארית ברוחב, אך מסלול ההשהיה הארוך עלול להיות לינארי.

**מימוש מקביל יעיל יותר מבחינת עומק לוגי:** מחשבים את ה־OR המצטבר בשלוש שכבות בעזרת הזזות קבועות ו־OR, ואז מבודדים את הגבול בעזרת XOR.

```text
s1 = x  OR (x  >> 1)
s2 = s1 OR (s1 >> 2)
s3 = s2 OR (s2 >> 4)
y  = s3 XOR (s3 >> 1)
```

ההזזות הן ימינה, ממולאות באפסים, והפעולות הן לכל ביט בנפרד. בכל שלב משתמשים בתוצאה של השלב הקודם, ולא שוב בקלט המקורי.

**למה שלוש שכבות ה־OR עובדות?** בשכבה הראשונה כל ביט רואה את עצמו ואת השכן מעליו. בשנייה כל ביט רואה עד ארבעה ביטים מהקלט המקורי; בשלישית עד שמונה. לכן בסוף s3 כל הביטים החל מה־1 המשמעותי ביותר ועד ה־LSB הופכים ל־1, וכל הביטים שמעליו נשארים 0.

למשל:
```text
x       = 10000000
s1      = 11000000
s2      = 11110000
s3      = 11111111
s3 >> 1 = 01111111
XOR     = 10000000
```

**למה XOR משאיר בדיוק את הביט הרצוי?** אחרי המילוי, בתוך רצף האחדים שני הווקטורים מכילים 1, ו־1 XOR 1 הוא 0. מעל הרצף שניהם 0, ו־0 XOR 0 הוא 0. רק במקום של ה־1 הגבוה ביותר יש 1 ב־s3 ו־0 בעותק המוזז, ולכן רק שם מתקבל 1. גם בקלט אפס שני הווקטורים אפס. באותה נקודה אפשר גם לחשב `s3 AND NOT(s3 >> 1)`, אך ה־XOR מבטא ישירות את זיהוי הגבול.

בדוגמה המקורית x=00101011, כבר אחרי השכבה הראשונה מתקבל 00111111; גם אחרי השנייה והשלישית הוא נשאר כך. ה־XOR מול 00011111 מחזיר 00100000.

**מה יש בחומרה?** שלוש שכבות של שערי OR לכל ביט ושכבת XOR סופית. הזזה במרחק קבוע היא חיווט בין מיקומים וחיבור אפסים בקצוות; אין צורך במחולל הזזה משתנה, בשעון או בזיכרון. הווקטורים הם חוטים קומבינטוריים ברוחב שמונה ביטים.

**מה פירוש יעיל כאן?** במודל שערים בעלי שתי כניסות, המימוש נותן לכל היותר שלוש שכבות OR ועוד XOR. בהרחבה לרוחב N העומק הוא O(log N), לעומת שרשרת פשוטה בעומק O(N). זה סדר גודל מיטבי לעומק: y0 תלוי בכל N הקלטים, ואחרי d שכבות של שערים בעלי שתי כניסות אפשר להיות תלויים לכל היותר ב־2^d קלטים, ולכן נדרש לפחות log2(N) עומק. עבור שמונה ביטים הטיעון נותן חסם תחתון של שלוש שכבות; אין כאן הוכחה שארבע שכבות הן המינימום המדויק לכל ספריית שערים.

הרשת המקבילית המפורשת יכולה להשתמש ב־O(N log N) שערים לפני פישוט, בעוד שרשרת ה־OR המשותפת היא O(N) בשטח. לכן זו בחירה לטובת עומק לוגי, ולא טענת מינימום שטח. רוחב השערים המותרים וספריית התאים יכולים לשנות את ההשוואה.

**זהירות בשרשור NOR:** אם `N5=NOR(x7,x6)`, ההמשך הוא `N4=N5 AND NOT(x5)`, או באופן שקול `NOR(NOT(N5),x5)`. הביטוי `NOR(N5,x5)` שגוי משום שהוא הופך שוב את משמעות תנאי הביניים. NOR אינו אסוציאטיבי כמו OR. מספר השערים תלוי ברוחב הכניסות ובספרייה המותרת.

### חשבו זמני הגעה, לא רק את מספר השערים
בנו אותות higher המכילים OR של כל הסיביות הגבוהות: h6=x7; עבור i=5..0 הגדירו hi=h(i+1) OR x(i+1). כעת y7=x7, ולכל i=0..6 הגדירו ni=NOT hi ואז yi=xi AND ni. כל OR הוא דו־כניסתי; אין כאן OR רחב בעל מספר כניסות לא מוגבל.

זמן הגעה של צומת הוא המקסימום של זמני קלטיו ועוד שיהוי הצומת. באינדוקציה כל hi וכל ni מגיעים בזמן 0, מפני שכל צמתי OR/NOT עולים אפס במודל הנתון. כל yi הנמוך מגיע לכל המאוחר ב־1τ; y7 בחיווט מגיע ב־0. לכן זמן ההתייצבות הגרוע הוא 1τ<5.5τ, אף שיש שרשרת OR. הרשת כוללת שישה OR, שבעה NOT ושבעה AND; אין טענה למספר שערים מינימלי.

נכונות: הביט הגבוה ביותר שווה1 ואין מעליו1 ולכן הוא עובר; לכל ביט נמוך ממנו יש1 גבוה ולכן הוא נחסם. בקלט0 הכול0. לדוגמה 00101011 מחזיר00100000. בדיקת זמני הגעה נעשית בנפרד מבדיקת הערכים, על DAG מפורש עם רשימת צמתים וקשתות.

במודל אחיד של1τ לכל שער, אותה שרשרת כבר עולה עד8τ: שישה OR, NOT ו־AND במסלול אל y0. עץ OR מאוזן לכל higher עולה לכל היותר שלוש שכבות, ועוד NOT ו־AND נותנים חסם5τ; רשתות prefix/XOR אחרות מותרות בסעיף המקורי. אין להעביר את חסם1τ בין המודלים. יתרה מכך, משום שגם XOR ו־NOT חינמיים, אפשר לממש AND באמצעות NOT((NOT a) OR (NOT b)) ולקבל זמן פורמלי0; לכן1τ הוא חסם בר־השגה של הרשת הישירה, ולא מינימום חיובי במודל הספרייה הזה. המודל האידאלי אינו מתאר תזמון סיליקון, עומס או חיווט.

תשובה קצרה: את איחוד הסיביות הגבוהות בונים משערים חינמיים ומבצעים שכבת AND אחת בלבד. המשך: אם OR ו־NOT מקבלים השהיה חיובית, חשבו מחדש זמני הגעה ועברו לעץ או prefix; זו בדיקה של ההנחה ולא של מספר סמלי השערים.

```systemverilog
module prep014_weighted_msb(input wire [7:0] x,output wire [7:0] y);
  wire [6:0] higher;
  assign higher[6]=x[7];
  genvar i;
  generate for(i=0;i<6;i=i+1) begin: prefix_or
    assign higher[i]=higher[i+1] | x[i+1];
  end endgenerate
  assign y[7]=x[7];
  assign y[6:0]=x[6:0] & ~higher;
endmodule
```

### בדיקות של וריאציית הזמן
כל 256 הקלטים עברו בדיקת DAG מול אורקל מספרי עצמאי; זמני ההגעה חושבו בנפרד והתקבל חסם1τ במודל המשוקלל ו־8τ באותה טופולוגיה במודל אחיד. המודול prep014_weighted_msb קוּמפל והורץ ב־Icarus לכל256 הקלטים. אין כאן אישור תזמון פיזי או הרצה חדשה של כל קטעי RTL מהווריאציות הישנות.

## Keep the highest set bit of an eight-bit input

Design a combinational logic-gate circuit that accepts an eight-bit vector and retains only its highest set bit. All other output bits must be 0; all-zero input produces all-zero output.

Example: `00101011 → 00100000`. Return an eight-bit vector, not the index of the bit. Explain the implementation.

### Weighted-delay variant: only AND consumes time
For eight-bit highest-one isolation, achieve delay strictly below 5.5τ, improving on a reported 11τ construction. In this exercise each two-input AND has delay 1τ; OR, NOT and XOR have zero delay. Every binary gate has at most two inputs, wiring/fanout is free, and all inputs arrive at time zero. Use an acyclic combinational network and return zero for zero input. Give its network and a timing proof for this model, distinguishing it from uniform per-gate delay.

Keep only the highest set bit of the eight-bit input, returning an eight-bit one-hot-or-zero mask. The example fixes the interpretation: the first 1 is retained; only lower bits are cleared. Define all-zero input to return zero. With x7 the MSB, yi=xi AND NOT(OR of x7 through x(i+1)); y7=x7. Bits above the first 1 are already zero, the first 1 has no asserted higher input and passes, and all lower bits are blocked. This returns a mask, not an encoded index.

A shared ripple implementation uses H7=0, yi=xi AND NOT(Hi), H(i-1)=Hi OR xi. It is combinational, with O(N) size and potentially O(N) depth. For logarithmic depth, use s1=x OR (x>>1), s2=s1 OR (s1>>2), s3=s2 OR (s2>>4), and y=s3 XOR (s3>>1). Shifts are fixed logical zero-filled wiring, and all operations are bitwise on eight-bit unsigned vectors. Each stage depends on the preceding one. After stages 1,2,3 each bit sees up to 2,4,8 original bits at or above it. Thus s3 is zero above the highest input 1 and all ones below and including it. XOR with its one-bit-right-shifted copy removes the overlapping ones and leaves only the leading boundary. The all-zero case remains zero. An equivalent final expression is s3 AND NOT(s3>>1).

Example 10000000 becomes 11000000,11110000,11111111, then XOR with 01111111 gives 10000000. For the source example 00101011, the first OR stage already yields 00111111 and the final result is 00100000.

The explicit parallel circuit has at most three two-input OR levels and one XOR level. For N bits it has O(log N) depth, asymptotically optimal under bounded fan-in: y0 depends on all N inputs, while depth d can cover at most 2^d inputs. This is not a claim of exact minimum four-level depth for N=8 or minimum cell area. The straightforward parallel network can have O(N log N) gates before simplification; the ripple version shares gates for O(N) area. No clock, FF, variable shifter or priority-index decoder is required. Python equation models were exhaustively verified for all 256 inputs; SystemVerilog is supplied but no HDL simulation or physical timing closure is claimed.

NOR polarity: if `N5=NOR(x7,x6)`, continue with `N4=N5 AND NOT(x5)`, equivalently `NOR(NOT(N5),x5)`. Using `NOR(N5,x5)` is incorrect. NOR is not associative like OR; gate counts depend on allowed fan-in and cell library.

### Propagate arrival times rather than counting symbols
Build higher-bit OR flags: h6=x7; for i=5..0 set hi=h(i+1) OR x(i+1). Then y7=x7 and for i=0..6 set ni=NOT hi and yi=xi AND ni. Every OR has two inputs; no unbounded-fan-in OR primitive is hidden here.

A node arrives at the maximum arrival of its inputs plus its delay. Inductively every hi and ni arrives at 0 because OR/NOT cost zero in the declared model. Each lower yi arrives by 1τ, while y7 is a wire at 0. Thus worst-case settling is 1τ<5.5τ despite the OR chain. The construction has six OR, seven NOT and seven AND cells, without a minimum-cell claim.

Correctness: the highest asserted bit passes because no higher input is asserted; every lower bit is blocked by a higher one. Zero remains zero. For example 00101011 returns 00100000. Value checks and arrival-time checks use separate oracles over an explicit acyclic node/edge list.

If every gate instead costs 1τ, this same chain can take8τ: six ORs, a NOT and an AND on the y0 path. A separate balanced OR tree for each higher flag takes at most three levels, with NOT and AND giving a5τ upper bound; the original prefix/XOR alternatives use their own topology. The1τ bound cannot be transferred between models. Moreover, with free OR/NOT one can replace AND by NOT((NOT a) OR (NOT b)) and obtain a formal 0 delay, so1τ is an achievable bound for the direct network, not a positive optimum of this library. This ideal exercise is not silicon, loading or routing timing.

Oral answer: combine higher bits using zero-cost gates, followed by just one timed AND layer. Follow-up: give OR/NOT positive delays, recompute arrival times and choose balanced trees or a prefix network; the critical issue is the model, not the number of drawn symbols.

```systemverilog
module prep014_weighted_msb(input wire [7:0] x,output wire [7:0] y);
  wire [6:0] higher;
  assign higher[6]=x[7];
  genvar i;
  generate for(i=0;i<6;i=i+1) begin: prefix_or
    assign higher[i]=higher[i+1] | x[i+1];
  end endgenerate
  assign y[7]=x[7];
  assign y[6:0]=x[6:0] & ~higher;
endmodule
```

### Weighted-variant checks
All 256 vectors passed an explicit DAG check against an independent integer oracle. Separate arrival-time propagation gave 1τ weighted delay and 8τ under uniform delay for that same topology. The prep014_weighted_msb module compiled and ran in Icarus on all 256 inputs. This is neither physical timing closure nor a new run of every older variant’s RTL.

[he diagram](../diagrams/prep-014-weighted-timing-1115d-he.png)

[en diagram](../diagrams/prep-014-weighted-timing-1115d-en.png)

[Implementation](../solutions/digital1115d.sv)

[Implementation](../solutions/digital1115d_models.py)

[Private source](../sources/2026-11-15-batch20d-10.png)
