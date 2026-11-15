# PREP-363 — בקר מאוורר עם שני ספי טמפרטורה וזיכרון

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## בקר מאוורר עם שני ספי טמפרטורה וזיכרון

תכננו בקר סינכרוני למנוע של מאוורר קירור. Th=1 מציין טמפרטורה גבוהה מדי ו־Tl=1 טמפרטורה נמוכה מדי; שני האותות כבר מסונכרנים ונידגמים בחזית עולה. hot בלבד מפעיל את המאוורר, cold בלבד מכבה אותו, וכאשר שניהם0 שומרים את המצב הקודם. אם שניהם1, כבו את המנוע והפיקו sensor_fault=1 במשך הסתירה; לאחריה ממשיכים מהמצב כבוי עד דרישה חדשה. איפוס סינכרוני פעיל־גבוה כופה OFF. הגדירו טבלת מעברים, משוואה, רכיבים ומימוש. הסבירו מדוע לוגיקה קומבינטורית לבדה אינה מספיקה.

### הספים מייצרים היסטרזיס באמצעות מצב אחד
בחירת התרגיל היא מאוורר קירור: בחום מדליקים, בקור מכבים. נסמן q את fan_on. הטבלה קובעת את המצב הבא אחרי החזית:

|Th|Tl|qnext|sensor_fault|
|---|---|---|---|
|0|0|q|0|
|0|1|0|0|
|1|0|1|0|
|1|1|0|1|

אם reset=1 נקבע qnext=0 ללא תלות בשורה. sensor_fault הוא האבחון הקומבינטורי Th AND Tl; הוא אינו נשמר ואינו מוסתר בזמן איפוס. ביט הפלט fan_on נשמר בפליפ־פלופ. הפלטים מתייחסים לאותות המנורמלים Th,Tl, לא לחיישן אנלוגי גולמי.

בלי איפוס: qnext=(Th AND NOT Tl) OR (q AND NOT Th AND NOT Tl). אפשר לממש בשערים ופליפ־פלופ יחיד, או במוקסים הבוחרים ON,OFF או feedback לפי הטבלה. בשתי היסטוריות שונות אפשר להגיע לאותן כניסות00 אך לדרוש ON אחרי חום ו־OFF אחרי קור; זו הוכחה שמימוש ללא זיכרון אינו מספיק. ביט מצב אחד מספיק ומתבקש בחוזה הזה.

לדוגמה, מאתחלים OFF. הרצף (Th,Tl)=00,10,00,00,01,00 נותן q=0,1,1,1,0,0. הסתירה11 אחרי ON מעבירה ל־OFF ומדווחת fault; אם אחריה00, נשאריםOFF. לכן רטט קטן בתוך תחום הספים אינו מחליף מצב בכל דגימה. זו היסטרזיס לוגית, בלי טענה לסינון רעש מעבר לחוזה או לבטיחות מנוע במערכת ממשית.

הוכחת נכונות היא ניתוח ארבע שורות הטבלה, עם אינווריאנט שבאזור00 נשמרת הדרישה התקינה האחרונה מאז האיפוס או הסתירה. העלות הלוגית היא פליפ־פלופ אחד ולוגיקת next-state קבועה; הרכבת המנוע, דרייבר זרם, הגנות וניתוח חיישנים מחוץ למודל. בדיקות כוללות את שני המצבים, כל זוג כניסות ואיפוס, וכן רצפים עם סתירות.

תשובה קצרה לראיון: המצב הוא האם המאוורר פועל; חם קובע1, קר קובע0 ובאזור הביניים שומרים. צריך להחליט גם על אתחול וסתירת חיישנים. טעויות נפוצות הן y=Th שאינו שומר היסטרזיס, או חיבור S=Th,R=Tl לרכיב SR בלי הגדרת11. המשך: אם המנוע הוא גוף חימום, החליפו את משמעות ON/OFF בחם/קר והשאירו את שימור האזור; אם חיישנים אסינכרוניים יש להוסיף חוזה סנכרון וטיפול בסתירות זמניות.

```systemverilog
module prep_thermal1115d(input wire clk,rst,hot,cold,
                        output reg fan_on,output wire sensor_fault);
  assign sensor_fault=hot & cold;
  always @(posedge clk) begin
    if(rst || sensor_fault) fan_on<=0;
    else if(hot) fan_on<=1;
    else if(cold) fan_on<=0;
  end
endmodule
```

### בדיקות שבוצעו
כל16 שורות מצב/קלט/איפוס נבדקו במודל עצמאי. המודול prep_thermal1115d קוּמפל והורץ ב־Icarus על10,240 דגימות של זוגות חיישנים, כולל סתירות ואיפוס באמצע רצף. הטבלאות והקוד מיישמים את אותה מדיניותOFF בסתירה. לא נבדק מנוע פיזי או תזמון אנלוגי.

## A cooling-fan controller with two thresholds and memory

Design a synchronous controller for a cooling-fan motor. Th=1 means too hot and Tl=1 means too cold; both inputs are already synchronized and sampled on the rising edge. Hot alone turns the fan on, cold alone turns it off, and two zeroes retain its previous state. If both are one, turn the motor off and assert sensor_fault for the contradictory interval; after it clears, remain off until a new request. Assume synchronous active-high reset forces OFF. Give transitions, an equation, components and implementation. Explain why memoryless combinational logic is insufficient.

### Thresholds create hysteresis through one stored state
This exercise chooses a cooling fan: hot turns it on and cold turns it off. Let q be fan_on. The table gives the state after an edge:

|Th|Tl|qnext|sensor_fault|
|---|---|---|---|
|0|0|q|0|
|0|1|0|0|
|1|0|1|0|
|1|1|0|1|

Reset forces qnext=0 regardless of the row. sensor_fault is combinational Th AND Tl; it is neither latched nor hidden during reset. A flip-flop stores fan_on. These signals are the normalized synchronous Th,Tl inputs, not a raw analog sensor.

Without reset, qnext=(Th AND NOT Tl) OR (q AND NOT Th AND NOT Tl). Use gates and one flip-flop, or MUXes selecting ON, OFF or feedback according to the table. Two histories can reach inputs 00 while requiring ON after hot and OFF after cold, proving that memoryless logic cannot satisfy the specification. One state bit suffices under this contract.

Starting OFF, pairs 00,10,00,00,01,00 give q=0,1,1,1,0,0. A contradictory 11 after ON turns it OFF and flags a fault; a subsequent 00 retains OFF. Thus small variation within the deadband does not change output every sample. This is logical hysteresis, without an extra noise-filtering or real-motor safety claim.

Correctness follows from the four rows and the invariant that 00 retains the most recent valid command since reset or contradiction. Logical cost is one flip-flop plus constant next-state logic. Power drive, protections and physical sensor analysis lie outside this model. Checks cover both old states, every control pair, reset and contradictory sequences.

Oral answer: remember whether the fan is on; hot sets, cold clears and deadband holds. Define initialization and contradictory sensors too. Common errors are y=Th, which loses hysteresis, or using S=Th,R=Tl without defining 11. Follow-up: for a heater reverse the hot/cold ON commands while retaining deadband memory; asynchronous sensors need an additional synchronization and transient-contradiction contract.

```systemverilog
module prep_thermal1115d(input wire clk,rst,hot,cold,
                        output reg fan_on,output wire sensor_fault);
  assign sensor_fault=hot & cold;
  always @(posedge clk) begin
    if(rst || sensor_fault) fan_on<=0;
    else if(hot) fan_on<=1;
    else if(cold) fan_on<=0;
  end
endmodule
```

### Executed checks
An independent model checked all 16 state/input/reset combinations. The prep_thermal1115d module compiled and ran in Icarus on 10,240 sensor-pair samples, including conflicts and midstream reset. The table and code share the same conflict-OFF policy. No physical motor or analog timing was tested.

[he diagram](../diagrams/prep-363-thermal-1115d-he.png)

[en diagram](../diagrams/prep-363-thermal-1115d-en.png)

[Implementation](../solutions/digital1115d.sv)

[Implementation](../solutions/digital1115d_models.py)

[Private source](../sources/2026-11-15-batch20d-15.png)
