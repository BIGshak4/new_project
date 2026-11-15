# PREP-001 — ספירת אחדות בכניסה בת 8 סיביות באמצעות מחברים

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## ספירת אחדות בכניסה בת 8 סיביות באמצעות מחברים

תכננו מעגל צירופי המקבל וקטור בן 8 ביטים ומחזיר בבינארי את מספר ביטי ה־1 שבו. השתמשו ברכיבי מחבר מלא (FA) ומחבר למחצה (HA). ציינו את רוחב הפלט והסבירו את משקל אותות הסכום והנשא.

### תרגיל נוסף: ספירת אחדות בחמישה ביטים באמצעות FA בלבד
ממשו בעזרת רכיבי Full-Adder בלבד מערכת המקבלת חמישה ביטים ומחזירה את מספר האחדות בהם בבינארי.

הנחות והגדרות: חמש הכניסות ניתנות יחד כווקטור x[4:0]; נבחר מעגל צירופי, לא ספירה של ביטים המגיעים לאורך זמן. התוצאה y[2:0] היא ללא סימן בטווח 0..5. כל FA מקבל שלושה ביטים ומוציא Sum,Carry לפי a+b+c=Sum+2·Carry. מותר חיווט, פיצול וקבוע 0. אין HA, שערים חיצוניים, קלטים מהופכים בחינם, קבוע 1 או רכיבי זיכרון; מותר לקבע מבוא FA לאפס, והוא עדיין נספר כ־FA. הציגו חיבורים, משקלים, הוכחה ועלות. מינימום רכיבים אינו דרישה במקור; אם טוענים לו, יש לתחום את מודל הרכיבים ולהצדיק את החסם.

### הרחבה: סכום האחדות בשלושה ביטים באמצעות HA בלבד
קבלו שלושה ביטים יחד והחזירו מספר בינארי בן שתי סיביות המייצג כמה מהם 1. מותר להשתמש ב־Half Adders בלבד, חיווט ופיצול אותות; ללא FA, שער נוסף או זיכרון. הבהרות: כל קלט תורם 0 או 1 לספירה, ולא את משקלו במספר המקורי. הפלט בטווח 0..3. אין צורך להוכיח מינימום רכיבים.

### וריאציה: שמונה סיביות באמצעות Full Adder בלבד
קבלו x[7:0] במקביל והחזירו בסיביות את מספר האחדות, 0..8. מותר להשתמש רק בתאי FA, בחיווט, בפיצול אות ובקבוע 0; אין תאי HA נפרדים, שערים חיצוניים או אוגרים. תא FA המחובר לאפס עדיין נספר כ־FA. הציגו חיבור לכל תא, משקלי סיביות ואת העלות. הבהרה שנבחרה: מימוש צירופי; אין תוספת של טענת מינימום כללית ללא מודל ספרייה והוכחה. הדרישה שונה מהחלק הישן המתיר גם HA.

### שבע כניסות ורק מחברים מלאים
קבלו שבע סיביות בו־זמנית והחזירו את מספר האחדות בשלוש סיביות. השתמשו רק ברכיבי FA, חיווט ופיצול אות. הראו את ארבעת הרכיבים, משקל כל חיבור ומספר שכבות התלות. אין צורך בזיכרון או בשעון. כל רכיב מקבל שלוש סיביות באותו משקל ומקיים a+b+c=Sum+2·Carry. סעיף זה מגדיר במפורש את וריאציית שבע הסיביות שכבר הוסברה בפתרון.

הנח שהקלט הוא x0..x7 ושפלט y0..y3 הוא מספר האחדות בבינארי. מימוש מינימלי במספר מחברים: (1) FA1(x0,x1,x2)→s0,c1a; (2) FA2(x3,x4,x5)→s1,c1b; (3) FA3(s0,s1,x6)→s2,c1c; (4) HA1(s2,x7)→y0,c1d; (5) FA4(c1a,c1b,c1c)→t1,c2a; (6) HA2(t1,c1d)→y1,c2b; (7) HA3(c2a,c2b)→y2,c3; ולבסוף y3=c3. כל Sum נשאר באותו משקל וכל Carry עובר למשקל כפול, לכן הסכום נשמר. ארבעה Full-Adders ו־שלושה Half-Adders הם מינימליים: יש 8 ביטי קלט ו־4 ביטי פלט, וכל Full-Adder הוא הרכיב היחיד שמפחית את מספר החוטים הכולל, בחוט אחד; לכן נדרשים לפחות 4 Full-Adders. בעמודת המשקל 1, כדי להפוך 8 אותות לאות אחד חייבים 2f0+h0=7, ולכן עם f0=3 נדרש לפחות Half-Adder אחד. המשך איזון העמודות מחייב לפחות HA אחד בעמודת 2 ולפחות HA אחד בעמודת 4; המימוש נותן בדיוק 3. התוצאה נכונה לכל קלט 8-ביטי והפלט הוא 4-ביטי בטווח 0..8.

**הצעה לפתרון — וריאציית 7 ביט:** הקלט x6..x0 והפלט y2..y0 הם בינאריים; התוצאה בטווח 0..7 ולכן דרושים שלושה ביטים. כל ביט קלט תורם 0 או 1 לספירה, ולא לפי משקלו במספר המקורי. הדוגמה 1001101 כוללת ארבע אחדות, ולכן הפלט 100 בבינארי.

מימוש קומבינטורי בארבעה Full-Adders, ללא צורך ב־FF או במחסר:
1. FA1(x0,x1,x2) -> (sA,cA).
2. FA2(x3,x4,x5) -> (sB,cB).
3. FA3(sA,sB,x6) -> (y0,cC).
4. FA4(cA,cB,cC) -> (y1,y2), כאשר y1 הוא Sum ו־y2 הוא Carry.

בכל זוג מוצאים נרשמו Sum ואז Carry. נשאי FA1,FA2,FA3 מייצגים יחידות במשקל 2; לכן מותר לחברם יחד ב־FA4. הוכחה: סכום שבעת ביטי הקלט הוא sA+sB+x6+2(cA+cB)=y0+2(cA+cB+cC)=y0+2y1+4y2. FA1 ו־FA2 פועלים במקביל, אחריהם FA3 ואחריו FA4; עומק תלות של שלוש שכבות מחברים, ללא הנחת זמני השהיה פנימיים שווים.

המימוש משתמש במינימום ארבעה מחברים במודל מוגבל של רשת הפחתת ביטים באמצעות FA/HA ששומרת את סכום עמודות המשקל: דרוש צמצום מ־7 אותות התחלתיים ל־3 אותות תוצאה; FA מצמצם אות אחד ו־HA אינו מצמצם. זו אינה הוכחה למינימום שטח/שערים/השהיה כשמותרים רכיבים שרירותיים, מחסרים או לוגיקה מותאמת. אין בשאלה דרישת מינימום מפורשת. FF מותרים אך אינם נדרשים: אם רוצים דגימה או pipeline, יש להגדיר שעון, latency וליישר אותות בין שלבים. חיבור כל הקלטים במקביל חוסך פרוטוקול סדרתי; אין סופרים רק ביטים השווים ל־1 לאורך זמן.

בדיקות: נבדקו כל 128 הקלטים מול bit_count בפייתון, כולל אפס, כל השבעה דלוקים, כל one-hot והדוגמה. זו בדיקת מודל פונקציונלי ולא HDL או timing פיזי. אין לפרש את פלט 100 כמאה עשרוני.

הסבר אינטואיטיבי: Full-Adder מחלק עד שלוש אחדות לזוג ולשארית. Carry=1 אומר שיש זוג אחד, ו־Sum=1 אומר שנותרה יחידה בודדת. לדוגמה 1+1+1=3 נותן C=1,S=1: זוג ועוד יחידה. FA1 ו־FA2 מטפלים בשתי שלשות קלט, ושומרים בנפרד זוגות cA,cB ושאריות sA,sB. FA3 אוסף את שתי השאריות ואת הביט השביעי; הוא מוציא את היחידה הסופית y0 ואולי זוג נוסף cC. FA4 סופר את שלושת הזוגות cA,cB,cC. משום שכל זוג שווה שתי אחדות מקוריות, Sum שלו שווה 2 במניין המקורי, ו־Carry שלו שווה 4. לכן אלה y1,y2, והמספר נקרא y2y1y0.
בדוגמה x6..x0=1001101: FA1 מקבל (1,0,1) ומוציא sA=0,cA=1; FA2 מקבל (1,0,0) ומוציא sB=1,cB=0; FA3 מקבל (0,1,1) ומוציא y0=0,cC=1; FA4 מקבל (1,0,1) ומוציא y1=0,y2=1. הפלט 100. חוטים בעלי אותו שם בשרטוט מחוברים פיזית, גם כאשר קו ארוך הוחלף בתוויות. כל Cin הוא ביט קלט במשקל השווה ל־A ול־B של אותו מחבר; מותר לחבר אליו ביט נתון, אין צורך שיהיה נשא ממחבר קודם.

### סופרים זוגות ושאריות
FA אינו חייב לקבל נשא ממחבר קודם: שלוש כניסותיו שוות במשקלן. הוא מחלק את מספר האחדות שבשלושתן לשארית Sum ולזוג Carry. לדוגמה, 1+1+1=3 נותן Sum=1,Carry=1, כלומר יחידה ועוד זוג.

### שלושה מחברים מלאים, ללא HA
בכל זוג מוצאים מופיעים Sum ואז Carry:

```text
(s1, c1) = FA(x0, x1, x2)
(y0, c2) = FA(s1, x3, x4)
(y1, y2) = FA(c1, c2, 0)
```

שני המחברים הראשונים עובדים במשקל יחידה. השני קובע את y0 הסופי ומשאיר יחד עם הראשון שני זוגות אפשריים c1,c2, כל אחד במשקל שתיים. ה־FA השלישי מקבל את שני הנשאים באותו משקל ואפס: Sum שלו הוא y1 במשקל שתיים ו־Carry שלו הוא y2 במשקל ארבע. אין רכיב HA מוסתר; זהו FA רגיל שמבוא אחד שלו מחובר לאפס. קוראים את הפלט y2y1y0.

### הוכחת שימור הערך
שלוש משוואות הרכיבים נותנות:

```text
x0+x1+x2 = s1+2c1
s1+x3+x4 = y0+2c2
c1+c2    = y1+2y2
```

לכן סכום חמש הכניסות הוא y0+2(c1+c2)=y0+2y1+4y2. כך מקבלים את מספר האחדות, ולא את ערך הקלט הבינארי או רק זוגיות. למשל 11111 נותן s1=1,c1=1; אחר כך y0=1,c2=1; ולבסוף y1=0,y2=1. הפלט 101 הוא חמש. קלט 10000 נותן 001, וקלט אפס נותן 000. שלושה ביטים דרושים כי הפלט יכול להיות חמש.

### עלות וחסם תחתון מוגדר
המימוש משתמש בשלושה FA ובשלוש שכבות תלות; אין טענה למדידת תזמון פיזי. אפשר גם להוכיח ששלושה הם מינימום רכיבי FA בספרייה שהוגדרה, באמצעות מנייה מלאה קטנה של כל רשת עם עד שני רכיבים. כל רשת חסרת מעגלים ניתנת לסדר טופולוגי. לרכיב הראשון זמינים חמישה קלטים ואפס: יש 56 שלשות פינים בלתי־מסודרות עם חזרות. אחריו זמינים גם שני מוצאיו, ולכן לרכיב השני יש 120 שלשות אפשריות. נבדקו כל 56 רשתות הרכיב היחיד וכל 56·120=6,720 רשתות שני הרכיבים, עם חזרות בפינים, פיצול ושימוש בכל חוט זמין כמוצא. אף רשת לא מכילה בו־זמנית את שלוש פונקציות ביטי הספירה בכל 32 הקלטים. בלי רכיבים גם הן אינן קלטים גולמיים. זו מנייה ממצה של המודל הסופי המוגדר, ולא ראיה ממדגם או מינימום שטח/שערים בספרייה אחרת.

המימוש נבדק בכל 32 הווקטורים וב־96 משוואות רכיבים משוקללות מול ספירת אחדות עצמאית. זהו Python בלבד, ללא HDL, סינתזה או מדידה. שלושת רמזי הווריאנט שמורים בחומר המשלים ובתוספת המסמך; שלושת הרמזים המקוריים נשארו בתור הקיים, שאינו בוחר רמזים אוטומטית לפי וריאנט.

### משקלי הנשאים חשובים יותר ממיקום הביט בקלט
נסמן HA(a,b)→(s,c1), ואז HA(s,c)→(y0,c2). משוואות הערך הן `a+b=s+2c1` ו־`s+c=y0+2c2`; לכן `a+b+c=y0+2(c1+c2)`.

כאשר c1=1, בהכרח a=b=1 ולכן s=0 ו־c2=s AND c=0. לכן c1 ו־c2 לעולם אינם 1 יחד. HA שלישי מקבל אותם: Sum שלו הוא y1=c1 XOR c2, והנשא שלו c1 AND c2=0 תמיד. אין צורך בשער OR שאינו מותר; עבור שני אותות זרים XOR שווה ל־OR. הפלט הוא y1y0.

ב־111: הראשון נותן s=0,c1=1; השני y0=1,c2=0; השלישי y1=1 ונשא 0, ולכן 11=3. ב־101 הפלט 10=2, וב־000 הפלט 00. כל שמונת הקלטים נבדקו, כולל הנשיאה שאינה מחוברת לפלט.

המימוש כולל שלושה HA, ללא FA או שער חיצוני. יש לכל היותר שלוש רמות תלות. זו עלות המבנה הנתון ולא טענת מינימום שערים/שטח/זמן.

### קוד SystemVerilog; תוצאות סימולציה בדוח נפרד

```systemverilog
`timescale 1ns/1ps
module prep001_ha(input wire a,b, output wire s,c);
  assign s=a^b;
  assign c=a&b;
endmodule
module prep001_ha3(input wire [2:0] x, output wire [1:0] y,
                   output wire unused_carry);
  wire s,c1,c2;
  prep001_ha first(x[0],x[1],s,c1);
  prep001_ha second(s,x[2],y[0],c2);
  prep001_ha carries(c1,c2,y[1],unused_carry);
endmodule
```


### שומרים סכום, לא רק זוגיות
FA מפיק Sum באותו משקל כמו שלושת קלטיו ו־Carry במשקל כפול. נשתמש בשבעה תאים:

```text
F0(x0,x1,x2) -> (s0,c0)
F1(x3,x4,x5) -> (s1,c1)
F2(s0,s1,x6) -> (s2,c2)
F3(s2,x7,0) -> (y0,c3)
F4(c0,c1,c2) -> (t0,u0)
F5(t0,c3,0) -> (y1,u1)
F6(u0,u1,0) -> (y2,y3)
```

ארבעת התאים הראשונים מקבלים משקל 1; c0..c3 במשקל 2. F4 ו־F5 מחברים במשקל 2 ומפיקים u0,u1 במשקל 4. F6 מחבר אותם ומפיק y2 במשקל 4 ו־y3 במשקל 8. סכימת הזהות של כל תא נותנת `sum(x)=y0+2y1+4y2+8y3`. זה מוכיח את הרשת לכל קלט בלי להסתמך על דוגמאות.

למשל 01001010 מכיל שלוש אחדות ולכן הפלט 0011; כל שמונת הביטים הדלוקים נותנים 1000. עץ XOR בלבד היה מחזיר זוגיות, לא את הסכום. בהשוואה למימוש בן שבעה קלטים, הקלט השמיני מחייב טיפול נוסף ואין להעתיק את מספר ארבעת המחברים שלו.

### עלות ומידת טענת המינימום
הבנייה משתמשת בשבעה FA, כולל שלושה תאים עם כניסת אפס המממשים פעולת HA אך נספרים FA. במודל מוגבל של דחיסת עמודות ללא שכפול סיביות, ושימוש ב־Sum באותו משקל וב־Carry במשקל כפול, דרושות ארבע פעולות בעמודת משקל 1 כדי להפוך שמונה סיביות לאחת; הן יוצרות ארבע סיביות משקל 2. בעמודה זו דרושות עוד שתי פעולות, היוצרות שתי סיביות משקל 4; עוד פעולה מחברת אותן. לכן שבע הוא מזערי במודל עמודות זה. אין מכאן הוכחה לכל מעגל FA עם פיצול ושימושים לא־רגילים בפלטים: זו טענת מינימום מצומצמת, והפתרון המקובל אינו תלוי בטענה כללית.

בדיקת המודל משווה את כל 256 הקלטים לספירת אחדות בלתי תלויה. קוד RTL שומר את שבעת המופעים במפורש, ובדיקת native נפרדת מאמתת את אותו תחום; לא בוצע מיפוי שטח או STA.

### קוד SystemVerilog; תוצאות סימולציה בדוח נפרד

```systemverilog
// Each instance is counted as a full adder, including pins tied to zero.
module prep001_fa(input wire a,b,c, output wire s,k);
  assign s = a ^ b ^ c;
  assign k = (a&b) | (a&c) | (b&c);
endmodule
module prep001_eight_fa_only(input wire [7:0] x, output wire [3:0] y);
  wire s0,s1,s2,c0,c1,c2,c3,t0,u0,u1;
  prep001_fa f0(x[0],x[1],x[2],s0,c0);
  prep001_fa f1(x[3],x[4],x[5],s1,c1);
  prep001_fa f2(s0,s1,x[6],s2,c2);
  prep001_fa f3(s2,x[7],1'b0,y[0],c3);
  prep001_fa f4(c0,c1,c2,t0,u0);
  prep001_fa f5(t0,c3,1'b0,y[1],u1);
  prep001_fa f6(u0,u1,1'b0,y[2],y[3]);
endmodule
```


### רכזו את היחידות ואז את הזוגות
FA0 מקבל x0,x1,x2 ומוציא sA,cA. FA1 מקבל x3,x4,x5 ומוציא sB,cB. ה־Sum בכל אחד נשאר במשקל 1 וה־Carry במשקל 2. FA2 מקבל sA,sB,x6 ומוציא y0,cC. FA3 מקבל cA,cB,cC, כולם במשקל 2, ומוציא y1 במשקל 2 ו־y2 במשקל 4.

לכן Σxi=sA+sB+x6+2(cA+cB)=y0+2(cA+cB+cC)=y0+2y1+4y2. זה מוכיח את הנכונות לכל הקלטים. שני הרכיבים הראשונים פועלים במקביל; המסלול הארוך עובר בשלושה FA. למשל 1111111 נותן 111, ו־0000000 נותן 000.

העלות היא ארבעה FA. במודל של צמצום סיביות שומר־משקל כל FA מפחית את מספר הסיביות הפנימיות באחת, ולכן מעבר משבע לשלוש דורש ארבעה צמצומים. זהו חסם של מודל הרכיבים המוגדר, ללא טענה על שטח או שיהוי פיזיים מינימליים. כל 128 הקלטים נבדקים גם במימוש SystemVerilog שהורץ בסימולטור.

## Count ones in an 8-bit input using full adders and half adders

Design a combinational circuit that accepts an 8-bit vector and outputs its number of set bits in binary. Use full adders (FAs) and half adders (HAs). State the output width and explain the weights of the sum and carry signals.

### Additional exercise: five-input population count using FAs only
Using only full-adder components, accept five bits and return their number of ones in binary.

Assumptions and definitions: all five inputs arrive together as vector x[4:0]; choose a combinational circuit, not a count of serially arriving bits. Unsigned y[2:0] ranges from zero to five. Each FA has three bit inputs and Sum/Carry outputs with a+b+c=Sum+2·Carry. Wiring, fanout and constant zero are allowed. No HAs, external gates, free complemented inputs, constant one or memory. An FA with one pin tied to zero is permitted and still counted as an FA. Show connections, weights, correctness and cost. Minimum components is not requested by the source; any minimum claim needs an explicit library and lower bound. Earlier variants remain separate.

### Extension: population count of three bits using HAs only
Accept three simultaneous bits and return their population count as a two-bit binary number. Use only half adders, wiring and fanout; no FA, external gates or storage. Each input contributes 0 or 1, not its original binary place value. Output ranges 0..3. A minimum-component proof is not required.

### Variant: eight bits using full adders only
Accept simultaneous x[7:0] and output their population count, zero through eight. Only FA cells, wiring, fanout and constant zero are allowed; no separate HAs, external gates or registers. An FA with a zero pin still counts as an FA. Show every cell connection, bit weights and cost. Chosen clarification: combinational operation; no unsupported global minimum claim is added. This differs from the earlier part that also allows HAs.

### Seven inputs using full adders only
Accept seven simultaneous bits and output their number of ones as three unsigned bits. Use only FA cells, wiring and fanout. Show all four cells, every signal weight and the number of dependency layers. No clock or storage is needed. A cell takes three equal-weight bits and satisfies a+b+c=Sum+2·Carry. This clause explicitly states the seven-bit variant already discussed in the proposed solution.

Assume inputs x0..x7 and a 4-bit output y3..y0 representing the population count. A minimum-adder implementation is: (1) FA1(x0,x1,x2)→s0,c1a; (2) FA2(x3,x4,x5)→s1,c1b; (3) FA3(s0,s1,x6)→s2,c1c; (4) HA1(s2,x7)→y0,c1d; (5) FA4(c1a,c1b,c1c)→t1,c2a; (6) HA2(t1,c1d)→y1,c2b; (7) HA3(c2a,c2b)→y2,c3; finally y3=c3. Every Sum stays at its current weight and every Carry moves to twice the weight, so the represented value is preserved. Four Full-Adders and three Half-Adders are minimal: there are 8 input wires and 4 output wires, and a Full-Adder is the only component here that reduces the total wire count, by one; therefore at least 4 Full-Adders are required. In weight-1 column, reducing 8 signals to one requires 2f0+h0=7, so with f0=3 at least one Half-Adder is needed. Balancing the next columns forces at least one Half-Adder in weight-2 and one in weight-4; this circuit uses exactly three. Exhaustive simulation covers all 256 inputs; output range is 0..8.

Proposed solution — 7-bit variant: output y2..y0 is the unsigned population count in 0..7. Each input contributes zero or one, not its original binary place value. Input 1001101 contains four ones, so output is binary 100.
Use four full adders with (sum,carry) output convention: FA1(x0,x1,x2)->(sA,cA); FA2(x3,x4,x5)->(sB,cB); FA3(sA,sB,x6)->(y0,cC); FA4(cA,cB,cC)->(y1,y2). All carries into FA4 have weight two. The invariant is sum(inputs)=sA+sB+x6+2(cA+cB)=y0+2(cA+cB+cC)=y0+2y1+4y2. FA1/FA2 are parallel; three adder dependency layers suffice. No flip-flops or subtractors are required for the combinational task. Registered or pipelined alternatives require explicit clock/latency and stage alignment.
Four is minimum only for a weight-preserving FA/HA bit-reduction network: reducing seven signals to three needs four one-signal reductions; each FA reduces by one and HA by zero. This is not a global area/gate/delay lower bound under arbitrary permitted components, nor is optimality explicitly requested. All 128 inputs, including zero, all ones, one-hot and the example, were checked against Python bit_count. Functional model verification only, not HDL or physical timing.

Intuition: a full adder splits up to three ones into a pair (carry) and a leftover unit (sum). FA1/FA2 keep pairs cA,cB and leftovers sA,sB. FA3 combines the leftovers and seventh input, yielding final unit y0 and another pair cC. FA4 counts the three pair indicators; its sum has original weight 2 and its carry original weight 4, giving y1,y2. Read output as y2y1y0. For input x6..x0=1001101: FA1 inputs (1,0,1) -> (sA,cA)=(0,1); FA2 (1,0,0)->(sB,cB)=(1,0); FA3 (0,1,1)->(y0,cC)=(0,1); FA4 (1,0,1)->(y1,y2)=(0,1). Output 100. Repeated net labels in the diagram denote the same physical connection. Cin has the same weight as A and B within a full adder and may receive an ordinary input bit.

### Count pairs and leftovers
An FA does not require a carry from an earlier adder: its three inputs have equal weight. It splits their number of ones into a Sum leftover and a Carry pair. For example, 1+1+1=3 gives Sum=1,Carry=1: one unit plus one pair.

### Three full adders, no HA
Every output pair is ordered Sum, then Carry:

```text
(s1, c1) = FA(x0, x1, x2)
(y0, c2) = FA(s1, x3, x4)
(y1, y2) = FA(c1, c2, 0)
```

The first two cells operate at unit weight. The second fixes final y0, leaving two possible pairs c1,c2, each of weight two. The third FA adds those equal-weight carries and zero: its Sum is y1 at weight two and Carry is y2 at weight four. No HA is hidden; this is an ordinary FA with one input tied to zero. Read output y2y1y0.

### Value-preservation proof
The three component equations give:

```text
x0+x1+x2 = s1+2c1
s1+x3+x4 = y0+2c2
c1+c2    = y1+2y2
```

Thus the five input bits sum to y0+2(c1+c2)=y0+2y1+4y2. This is population count, not the input’s binary value or just parity. For 11111, the first FA gives s1=1,c1=1; the second gives y0=1,c2=1; the last gives y1=0,y2=1. Output 101 means five. Input 10000 gives 001; zero gives 000. Three bits are necessary because the output may be five.

### Cost and a scoped lower bound
The construction has three FAs and three dependency layers, without a physical timing claim. Three is also a minimum FA-cell count in the declared library, proved by complete small-network enumeration. Every acyclic network has a topological order. The first cell can use five raw bits and zero: 56 unordered pin triples with repetition. Its two outputs expand the second cell’s pool to eight wires, giving 120 triples. All 56 one-cell and 56·120=6,720 two-cell networks were checked, allowing repeated pins, fanout and any available output tap. None simultaneously supplies all three population-count bit functions on all 32 inputs. Those functions are not raw wires in the zero-cell case either. This is complete finite-model enumeration, not sampled evidence or a physical area/gate minimum under another library.

The construction passed all 32 input vectors and 96 weighted component equations against an independent count. Python only; no HDL, synthesis or measurements. Three variant hints are stored in supporting material and the addendum.

### Carry weight matters more than input position
Let HA(a,b)→(s,c1), then HA(s,c)→(y0,c2). Value equations are `a+b=s+2c1` and `s+c=y0+2c2`, hence `a+b+c=y0+2(c1+c2)`.

If c1=1 then a=b=1, so s=0 and c2=s AND c=0. The carries are mutually exclusive. A third HA combines them: its sum y1=c1 XOR c2 is their sum, while its carry c1 AND c2 is always 0. No forbidden external OR is needed: XOR equals OR for mutually exclusive signals. Return y1y0.

For 111: HA1 gives s=0,c1=1; HA2 gives y0=1,c2=0; HA3 gives y1=1,carry=0, yielding 11=3. Input 101 yields 10=2 and 000 yields 00. All eight inputs and the disconnected carry were checked.

The construction uses three HAs, no FA or external gate, and at most three dependency levels. This is its cost, not a minimum-gate/area/delay claim. Earlier8/7/5-bit variants and their allowed libraries remain separate.

### SystemVerilog; simulation results are in a separate report

```systemverilog
`timescale 1ns/1ps
module prep001_ha(input wire a,b, output wire s,c);
  assign s=a^b;
  assign c=a&b;
endmodule
module prep001_ha3(input wire [2:0] x, output wire [1:0] y,
                   output wire unused_carry);
  wire s,c1,c2;
  prep001_ha first(x[0],x[1],s,c1);
  prep001_ha second(s,x[2],y[0],c2);
  prep001_ha carries(c1,c2,y[1],unused_carry);
endmodule
```


### Preserve value, not just parity
An FA produces Sum at its input weight and Carry at twice that weight. Use seven cells:

```text
F0(x0,x1,x2) -> (s0,c0)
F1(x3,x4,x5) -> (s1,c1)
F2(s0,s1,x6) -> (s2,c2)
F3(s2,x7,0) -> (y0,c3)
F4(c0,c1,c2) -> (t0,u0)
F5(t0,c3,0) -> (y1,u1)
F6(u0,u1,0) -> (y2,y3)
```

The first four cells take weight-one inputs; c0..c3 have weight two. F4 and F5 operate at weight two and produce weight-four u0,u1. F6 combines those into y2 at weight four and y3 at weight eight. Summing cell conservation equations gives `sum(x)=y0+2y1+4y2+8y3`, proving the entire network for every input.

For example, 01001010 contains three ones and yields 0011; eight asserted inputs yield 1000. An XOR tree alone would return parity rather than the count. The eighth input needs additional handling, so the four-FA cost of the separate seven-input exercise cannot be copied here.

### Cost and the scope of minimality
This construction has seven FAs, including three zero-tied cells that perform HA functions but still count as FAs. In the restricted nonduplicating weighted-column compression model, Sum stays at its input weight and Carry moves to twice that weight. Reducing eight weight-one bits to one requires four column operations, creating four weight-two carries. Reducing that column takes two more operations and creates two weight-four carries; one final operation combines those. Thus seven is minimal in this column-compression model. This is not a proof for every possible FA circuit with fanout or unconventional output reuse; the minimum claim is deliberately scoped, and accepting the construction does not require a global claim.

The Python model checks all 256 inputs against an independent popcount. RTL explicitly retains the seven cell instances, and a separate native run verifies the same input domain. No mapped-area or static-timing result is claimed.

### SystemVerilog; simulation results are in a separate report

```systemverilog
// Each instance is counted as a full adder, including pins tied to zero.
module prep001_fa(input wire a,b,c, output wire s,k);
  assign s = a ^ b ^ c;
  assign k = (a&b) | (a&c) | (b&c);
endmodule
module prep001_eight_fa_only(input wire [7:0] x, output wire [3:0] y);
  wire s0,s1,s2,c0,c1,c2,c3,t0,u0,u1;
  prep001_fa f0(x[0],x[1],x[2],s0,c0);
  prep001_fa f1(x[3],x[4],x[5],s1,c1);
  prep001_fa f2(s0,s1,x[6],s2,c2);
  prep001_fa f3(s2,x[7],1'b0,y[0],c3);
  prep001_fa f4(c0,c1,c2,t0,u0);
  prep001_fa f5(t0,c3,1'b0,y[1],u1);
  prep001_fa f6(u0,u1,1'b0,y[2],y[3]);
endmodule
```


### Collect units, then pairs
FA0 takes x0,x1,x2 and produces sA,cA. FA1 takes x3,x4,x5 and produces sB,cB. Each Sum has weight one and each Carry has weight two. FA2 takes sA,sB,x6 and produces y0,cC. FA3 takes cA,cB,cC, all of weight two, and produces y1 of weight two and y2 of weight four.

Thus Σxi=sA+sB+x6+2(cA+cB)=y0+2(cA+cB+cC)=y0+2y1+4y2. This proves correctness for every input. The first two cells operate in parallel; the longest dependency traverses three FAs. For example, 1111111 gives 111 and 0000000 gives 000.

The cost is four FAs. In a weight-preserving bit-compression model each FA reduces the number of represented bits by one, so reducing seven bits to three needs four reductions. This is a lower bound for that stated model without a minimum physical area or delay claim. All 128 inputs are also checked in compiled SystemVerilog simulation.

[he diagram](../diagrams/prep-001-popcount7-1115c-he.png)

[en diagram](../diagrams/prep-001-popcount7-1115c-en.png)

[Implementation](../solutions/prep_001_popcount7_faonly1115c.sv)

[Private source](../sources/2026-11-15-batch10c-02.png)
