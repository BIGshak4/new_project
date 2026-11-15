# PREP-356 — מונה חניון עם חמישים מקומות

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## מונה חניון עם חמישים מקומות

תכננו מכונת מצבים לחניון בן 50 מקומות. הסבירו כמה ערוצי חישה דרושים, איך מעדכנים את מספר המכוניות ואיך מזהים בדיוק תפוסה 50.

השלמת ממשק לצורך התרגיל: יש נתיב כניסה חד־כיווני ונתיב יציאה חד־כיווני. כל אחד מספק בקשה מסונכרנת ונטולת ריצוד, באורך מחזור אחד. לכל היותר מכונית אחת בכל נתיב בכל מחזור. אישור בקשה מייצג חצייה אטומית שהושלמה במחזור זה; הבקר החיצוני מקיים את האישור בפועל. מצב התחלתי ריק ואיפוס סינכרוני פעיל־גבוה. בזמן איפוס אין אישורי חצייה. מותרת כניסה במקביל ליציאה גם בחניון מלא. יציאה מריק נדחית; בחניון ריק, כניסה ויציאה יחד מאשרות רק את הכניסה. כניסה למלא ללא יציאה נדחית. הוציאו full, אישורי כניסה/יציאה וסימוני דחייה, והראו את מניין התפוסה לצורך בדיקה. הסבירו מה משתנה בנתיב דו־כיווני יחיד.

### תרגמו את החיישנים לאירועים מוגדרים
במודל שתי התנועות החד־כיווניות מספיקים שני ערוצי חישה, אחד לכל נתיב. מניחים שעיצוב החיישן והבקר מספקים פעימה אחת לכל מכונית. בחיישן גולמי יש לטפל בריצוד, סינכרון, זמן מעבר ומכוניות צמודות. בנתיב משותף צריך מידע כיוון; למשל שני חיישנים לאורך הנתיב ובקר שמבחין בסדר A→B לעומת B→A, ומטפל בנסיגה ובחסימה. חיישן נוכחות יחיד בנתיב דו־כיווני אינו מבחין לבדו בין הכיוונים.

### שמרו תפוסה חוקית
מצב n מייצג תפוסה בין 0 ל־50. נסמן E בקשת כניסה ו־X בקשת יציאה. כאשר האיפוס אינו פעיל, חשבו accepted_exit=X AND(n>0), ואז accepted_entry=E AND(n<50 OR accepted_exit). העדכון הוא n'=n+accepted_entry−accepted_exit. בקשה שאינה מאושרת מסומנת בדחייה. ב־n=50 עם שתי הבקשות, שני האירועים מאושרים והמצב נשאר 50. ב־n=0 עם שתיהן, היציאה נדחית והתפוסה עולה ל־1. החלטות אלה משתמשות במצב שלפני חזית השעון.

| מצב | E,X=00 | 10 | 01 | 11 |
|---|---|---|---|---|
|0|0|1|0, יציאה נדחית|1, יציאה נדחית|
|1..49|n|n+1|n−1|n|
|50|50|50, כניסה נדחית|49|50|

אינדוקציה מוכיחה שהמצב נשאר בין 0 ל־50, וכל אישור משנה אותו לפי מספר החציות שאושרו. צריך 51 מצבים, ולכן שישה ביטי מצב מספיקים. גם רק פלט full מבחין בין כל שני מצבים i<j: הוסיפו 50−j כניסות חוקיות, ואז j מגיע למלא ו־i עדיין אינו מלא. לכן 51 מצבים ושישה ביטים נדרשים במודל של זיכרון מדויק.

### פענחו חמישים
50=110010. לכן full=q5 AND q4 AND NOT q3 AND NOT q2 AND q1 AND NOT q0. זהו פענוח שוויון, ולא רק בדיקה ששני הביטים הגבוהים הם 1. קודי המצב 51..63 מסומנים כשגיאה ומתאוששים לאפס בחזית הבאה. פלט full הוא פענוח קומבינטורי לצרכן סינכרוני; דרישה לפלט פיזי נטול גליצ׳ים עשויה להצדיק רישום פלט נפרד ובדיקות תזמון. אין להסיק חסינות פיזית מסימולציה לוגית בלבד.

```systemverilog
// Entry/exit requests are synchronous, debounced, single-cycle events.
// An acknowledged event represents an atomic completed crossing in this model.
module prep356_parking(
  input wire clk,rst,entry_req,exit_req,
  output reg [5:0] occupancy,
  output wire full,accept_entry,accept_exit,reject_entry,reject_exit,state_error
);
  assign state_error = occupancy > 6'd50;
  assign full = occupancy[5] & occupancy[4] & ~occupancy[3]
                & ~occupancy[2] & occupancy[1] & ~occupancy[0];
  assign accept_exit = ~rst & ~state_error & exit_req & (occupancy != 0);
  assign accept_entry = ~rst & ~state_error & entry_req
                        & ((occupancy < 6'd50) | accept_exit);
  assign reject_entry = entry_req & ~accept_entry;
  assign reject_exit = exit_req & ~accept_exit;
  always @(posedge clk) begin
    if (rst || state_error) occupancy <= 6'd0;
    else if (accept_entry && !accept_exit) occupancy <= occupancy + 6'd1;
    else if (accept_exit && !accept_entry) occupancy <= occupancy - 6'd1;
  end
endmodule
```

## A parking occupancy controller for fifty spaces

Design a state machine for a fifty-space car park. Explain the sensing channels, occupancy updates and an exact full indication at occupancy 50.

Chosen interface: separate one-way entrance and exit lanes provide synchronized, debounced one-cycle requests, with at most one car per lane per cycle. An acknowledged request represents an atomic crossing completed in that cycle; the external controller enforces acknowledgements. Start empty and use synchronous active-high reset. No crossings are acknowledged during reset. An entry may accompany an exit when full. Reject exit from empty; at empty, simultaneous requests accept only entry. Reject entry to full without exit. Output full, entry/exit acknowledgements and rejection flags, with occupancy exposed for checking. Explain the change for one shared bidirectional lane.

### Give the sensors a precise event contract
For the two one-way lanes, two sensing channels suffice in the ideal model, one per lane. Their front ends must deliver exactly one event per car. Real raw sensors need synchronization, debouncing, transit-time and tailgating handling. A shared bidirectional lane needs direction information, such as two spaced sensors and a controller distinguishing A→B from B→A, including reversal and obstruction handling. One presence sensor alone does not distinguish direction.

### Maintain legal occupancy
State n is occupancy in 0..50. Let E be entry request and X exit request. When reset is inactive, compute accepted_exit=X AND(n>0), then accepted_entry=E AND(n<50 OR accepted_exit). Update n'=n+accepted_entry−accepted_exit. Flag each unacknowledged request as rejected. At n=50 with both requests, both are accepted and occupancy remains 50. At n=0 with both, exit is rejected and occupancy becomes one. Decisions use the pre-edge state.

| State | E,X=00 | 10 | 01 | 11 |
|---|---|---|---|---|
|0|0|1|0, reject exit|1, reject exit|
|1..49|n|n+1|n−1|n|
|50|50|50, reject entry|49|50|

Induction proves occupancy stays in 0..50 and changes by precisely the accepted crossings. There are 51 states, so six state bits suffice. Even full alone distinguishes every pair i<j: append 50−j valid entry events, making state j full while i remains below capacity. Thus 51 states and six bits are required for exact occupancy memory under this interface.

### Decode fifty
50=110010. Hence full=q5 AND q4 AND NOT q3 AND NOT q2 AND q1 AND NOT q0. This is equality decoding; just checking the highest two bits is insufficient. Codes 51..63 raise a state-error indication and recover to zero on the next edge. full is combinational for a synchronous consumer. A physically glitch-free output may require a separately registered flag and timing checks. Logical simulation alone cannot establish physical glitch immunity.

```systemverilog
// Entry/exit requests are synchronous, debounced, single-cycle events.
// An acknowledged event represents an atomic completed crossing in this model.
module prep356_parking(
  input wire clk,rst,entry_req,exit_req,
  output reg [5:0] occupancy,
  output wire full,accept_entry,accept_exit,reject_entry,reject_exit,state_error
);
  assign state_error = occupancy > 6'd50;
  assign full = occupancy[5] & occupancy[4] & ~occupancy[3]
                & ~occupancy[2] & occupancy[1] & ~occupancy[0];
  assign accept_exit = ~rst & ~state_error & exit_req & (occupancy != 0);
  assign accept_entry = ~rst & ~state_error & entry_req
                        & ((occupancy < 6'd50) | accept_exit);
  assign reject_entry = entry_req & ~accept_entry;
  assign reject_exit = exit_req & ~accept_exit;
  always @(posedge clk) begin
    if (rst || state_error) occupancy <= 6'd0;
    else if (accept_entry && !accept_exit) occupancy <= occupancy + 6'd1;
    else if (accept_exit && !accept_entry) occupancy <= occupancy - 6'd1;
  end
endmodule
```

[he diagram](../diagrams/prep-356-parking-interface-1115c-he.png)

[en diagram](../diagrams/prep-356-parking-interface-1115c-en.png)

[he diagram](../diagrams/prep-356-parking-states-1115c-he.png)

[en diagram](../diagrams/prep-356-parking-states-1115c-en.png)

[Implementation](../solutions/prep_356_parking_capacity50_1115c.sv)

[Implementation](../solutions/hardware1115c_models.py)

[Private source](../sources/2026-11-15-batch10c-07.png)
