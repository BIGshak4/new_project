// Reviewed openings for model paragraphs whose first line has no standard assumptions label.
// Match the actual words so reordering a prompt never moves an unrelated paragraph.
export const modelOpenings = [
  ["Auxiliary storage and one-time `O(N)`", "מותר להשתמש בזיכרון עזר ובאתחול"], // PREP-006
  ["`Z` means high impedance: the", "`Z` מציין עכבה גבוהה: היציאה"], // PREP-015
  ["Pass requirement: this is linear-time", "הבהרת דרישת המעבר: המטרה היא"], // PREP-019
  ["Delays: black box 3 ns;", "השהיות הרכיבים: קופסה שחורה —"], // PREP-020
  ["Here `O` denotes Big-O, not", "כאן `O` היא חסם עליון"], // PREP-027
  ["Ignore wiring and register timing", "הזניחו חיווט ורגיסטרים בניתוח הצירופי."], // PREP-034
  ["Equal values at different positions", "מותר שערכי שני האיברים יהיו"], // PREP-040
  ["Here n=100; also analyze the", "כאן n=100; נתחו את הסיבוכיות"], // PREP-041
  ["For this implementation, assume a", "למימוש זה הניחו קלט בינארי"], // PREP-042
  ["For a defined implementation, assume", "לצורך מימוש מוגדר, נניח שעון"], // PREP-044
  ["Explicit implementation assumptions: pulses are", "הנחות המימוש המפורשות: הפולסים כבר"], // PREP-045
  ["For this explicit version, free", "לצורך גרסה חד־משמעית זו מותר"], // PREP-047
  ["For precise timing, choose a", "כדי להגדיר במדויק את התזמון,"], // PREP-048
  ["The source does not state", "המקור אינו מפרט אילו קבועים"], // PREP-052
  ["Selection is random and fair:", "הבחירה אקראית והוגנת: כל אסיר"], // PREP-054
  ["For eventual termination assume fairness:", "לצורך הבטחת סיום מניחים הוגנות:"], // PREP-057
  ["Rules clarified: the total is", "הבהרת כללים: הסכום משותף וגלוי,"], // PREP-060
  ["**Explicit chosen timing model:** marker", "**מודל התזמון שנבחר במפורש:** המרחק"], // PREP-062
  ["Agents cannot read coordinates, separation,", "אין גישה לקואורדינטות, למרחק, לזהות"], // PREP-062
  ["Assume the unloaded plate is", "נניח שהצלחת ללא המשקולות כבר"], // PREP-084
  ["Duplicates, zeros and negative values", "מותרות חזרות, אפסים ומספרים שליליים."], // PREP-089
  ["The source does not define", "המקור אינו מגדיר כיצד לספור"], // PREP-089
  ["Explicit ideal model: Earth is", "מודל שהוגדר במפורש: כדור הארץ"], // PREP-090
  ["Explicitly added dimensions: the outer", "מודל מידות שהוספנו במפורש: הריבוע"], // PREP-093
  ["Width is fixed: leading zeros", "רוחב הקלט קבוע: אפסים מובילים"], // PREP-094
  ["Source examples: 0x00080000 returns true;", "דוגמאות מהמקור: 0x00080000 מחזיר true,"], // PREP-105
  ["The source calls it an", "המקור מכנה את הרכיב SR"], // PREP-106
  ["The source does not specify", "המקור אינו מציין סדר או"], // PREP-108
  ["Added cost model: each gate", "מודל העלות שהוספנו: כל שער"], // PREP-109
  ["Screen metadata is established beforehand:", "מטא־נתוני המסך ידועים מראש: width,height"], // PREP-111
  ["These are explicit assumptions: the", "אלו הנחות והגדרות: המקור לא"], // PREP-111
  ["Air shots are public signals", "היריות באוויר משמשות כאן אותות"], // PREP-113
  ["free requires an index currently", "free מקבלת רק אינדקס של"], // PREP-117
  ["Explicit added model: MUX(S,D0,D1) returns", "מודל שנוסף במפורש למקור: MUX(S,D0,D1)"], // PREP-120
  ["Added clarifications: the camel eats", "הבהרות שנוספו למקור: הגמל אוכל"], // PREP-121
  ["Explicit added model: ignite endpoints", "מודל התרגיל: מותר להדליק קצוות"], // PREP-124
  ["At the start of each", "בתחילת כל תוכנית A=a ו־B=b"], // PREP-125
  ["The edited contract requires the", "בחוזה הערוך נדרוש את החסם"], // PREP-142
  ["Define \"happiest\" lexicographically: first maximize", "הגדירו \"הכי מרוצים\" כך: ראשית"], // PREP-148
  ["For integer days choose start..end", "בגרסת ימים שלמים נבחר start..end"], // PREP-149
  ["A byte has fixed width,", "בית הוא רוחב קבוע, ולכן"], // PREP-151
  ["The two source screenshots share", "שני צילומי המקור עוסקים באותו"], // PREP-155
  ["The source specifies no size.", "המקור אינו מציין גודל. התחילו"], // PREP-157
  ["The source supplies no sheet", "המקור אינו מציין כמות דפים,"], // PREP-159
  ["The source switches from numbers", "המקור אומר מספרים ואז תווים"], // PREP-160
  ["Choose floors 1..8 and destination", "נבחר קומות 1..8 ובקשה היא"], // PREP-161
  ["Return(length, start, end) with zero-based", "הבהרות: החזירו (length, start, end)"], // PREP-163
  ["For the proposed analysis use", "לניתוח המוצע נבחר בריכה סגורה,"], // PREP-167
  ["The balance is exact, weights", "המאזניים מדויקים, המשקלים קבועים, אין"], // PREP-168
  ["The example defines completed-run checking:", "הדוגמה מבהירה שהבדיקה היא של"], // PREP-171
  ["Clocking and overlap were not", "המקור אינו מגדיר תזמון או"], // PREP-173
  ["The source omits signedness and", "המקור אינו מגדיר סימן או"], // PREP-174
  ["Choose a one-cycle path with", "נבחר נתיב חד־מחזורי בין אוגרים"], // PREP-176
  ["For illustration choose a victim", "להמחשה בלבד נבחר חוט victim"], // PREP-177
  ["A nonnegative integer address accesses", "הכתובת addr היא מספר שלם"], // PREP-178
  ["The source does not specify", "המקור אינו מציין סימן או"], // PREP-180
  ["Choose the origin and an", "לצורך המימוש נבחר ראשית צירים"], // PREP-182
  ["The screenshot says from one", "הצילום אומר מקצה אחד לקצה"], // PREP-183
  ["Explicitly assume independent uniform Random5", "נניח במפורש שכל קריאות Random5"], // PREP-184
  ["Emit one boom per matching", "נבחר פלט boom אחד לכל"], // PREP-185
  ["In this implementation a word", "בחוזה המימוש מילה היא רצף"], // PREP-187
  ["Right means increasing seat position", "ימין מוגדר לפי סדר המקומות"], // PREP-192
  ["Clarification: no circuit, thresholds or", "הבהרה: לא סופק מעגל, מתחי"], // PREP-193
  ["The source does not supply", "המקור אינו מגדיר בדיקת ריקות,"], // PREP-194
  ["Use summation 1..n for nonnegative", "הדוגמה היא סכום 1..n עבור"], // PREP-196
  ["The second draw is conditionally", "ההגרלה השנייה אחידה מותנה בערך"], // PREP-198
  ["The source gives neither width", "המקור אינו מגדיר רוחב או"], // PREP-199
  ["Choose Y=A for S=0 and", "נבחר Y=A כאשר S=0 ו־Y=B"], // PREP-200
  ["Choose a basic static complementary", "נבחר מהפך סטטי בסיסי עם"], // PREP-205
  ["The source supplies no internal", "במקור אין ספירת כניסות או"], // PREP-209
  ["Assume a first-order filter, unity", "הניחו מסנן מסדר ראשון, הגבר"], // PREP-221
  ["Assume the R-connected input is", "לניתוח הניחו שהכניסה שאליה מגיע"], // PREP-222
  ["A word is an already", "מילה כאן היא מחרוזת שכבר"], // PREP-225
  ["The main interface permits connecting", "במימוש הראשי מותר לחבר את"], // PREP-227
  ["For example [1,0,9,0,3,4,5,1] becomes [1,9,3,4,5,1,0,0].", "לדוגמה [1,0,9,0,3,4,5,1] יהפוך ל־[1,9,3,4,5,1,0,0]. האחד"], // PREP-229
  ["Explicit policy: WRITE THEN READ;", "מדיניות מפורשת: מטפלים קודם בכתיבה"], // PREP-230
  ["This is a queue even", "זהו תור, גם אם מכנים"], // PREP-230
  ["This is a sequential model:", "המודל הוא סדרתי: בכל פעולה"], // PREP-231
  ["Age means completed years and", "הגיל הוא מספר שנות החיים"], // PREP-232
  ["Inputs are binary, A is", "הקלטים בינאריים, A הוא ביט"], // PREP-234
  ["Comparison model: select signals and", "מודל ההשוואה: אותות הבחירה ותוצאת"], // PREP-235
  ["Let n≥1 be fixed at", "הגדירו n≥1 כפרמטר קבוע בבניית"], // PREP-236
  ["Input is finite and acyclic,", "הקלט סופי וללא מעגלים, כל"], // PREP-238
  ["Dialect: comma separator; double quotes", "חוזה הפורמט: פסיק הוא מפריד;"], // PREP-239
  ["Use an explicit model: all", "לצורך מודל מוגדר: כולם מתחילים"], // PREP-244
  ["Choose a 9×9 list of", "נבחר לוח 9×9 כרשימת תשע"], // PREP-245
  ["Reordering the input is allowed.", "מותר לשנות את סדר איברי"], // PREP-247
  ["Added spatial clarification: form a", "הבהרה מרחבית שנוספה: מסדרים שורה"], // PREP-250
  ["The source shows one trace,", "הצילום מציג עקבה אחת, עם"], // PREP-255
  ["Here “gates only” permits feedback", "״שערים בלבד״ מתיר כאן משוב"], // PREP-255
  ["For an exact implementation assume", "לצורך מימוש מדויק נגדיר שהחדר"], // PREP-256
  ["The screenshot supplies no topology,", "בצילום לא נמסרו טופולוגיה, אורכי"], // PREP-258
  ["Essential main-model assumptions: cavities are", "הבהרה מהותית לפתרון הראשי: החללים"], // PREP-259
  ["The short source says “NP", "הצילום הקצר כותב ״צומת NP״."], // PREP-260
  ["Implementation contract: vertices are cells;", "חוזה המימוש: כל vertex הוא"], // PREP-261
  ["The source specifies neither N", "המקור אינו מגדיר N או"], // PREP-263
  ["Explicit added contract: depth D=2^AW", "חוזה מפורש שנוסף למקור: עומק"], // PREP-264
  ["Reset both domains together to", "שני התחומים מאותחלים יחד לתור"], // PREP-264
  ["The source omits width and", "המקור אינו מגדיר רוחב או"], // PREP-265
  ["Use the documented endpoint `https://api.chucknorris.io/jokes/random`", "להמחשה נבחר endpoint מתועד `https://api.chucknorris.io/jokes/random`,"], // PREP-267
  ["Choose a one-room chat as", "כדוגמה עריכתית נבחר צ׳אט בחדר"], // PREP-268
  ["Explicit editorial assumption: the source", "הנחת עריכה מפורשת: המקור מגדיר"], // PREP-269
  ["Choose constant lookup tables. The", "נבחר מימוש באמצעות טבלאות קבועות."], // PREP-269
  ["The source does not specify", "המקור אינו מפרט שפה, סדר,"], // PREP-273
  ["For this exercise explicitly choose", "בחוזה התרגיל נבחר במפורש constructor"], // PREP-274
  ["The source chooses no device/output.", "המקור אינו בוחר התקן או"], // PREP-275
  ["Choose an explicit C++17 exercise:", "נבחר תרגיל מפורש ב־ C++17:"], // PREP-276
  ["The source describes 1024 bits", "המקור מתאר מערך בן 1024"], // PREP-278
  ["Teaching completion: use an ideal", "השלמה לימודית: בחרו מודל אידאלי"], // PREP-280
  ["Added assumptions: stable0/VDD inputs and", "השלמות: כניסות יציבות 0/VDD; בועה"], // PREP-282
  ["Choose a contract that also", "נבחר חוזה שמכסה גם נתונים"], // PREP-284
  ["Connected means repeatedly following parents", "״מחובר״ פירושו שהליכה חוזרת אל"], // PREP-284
  ["Complete the terse source by", "כדי להגדיר את המקור הקצר,"], // PREP-286
  ["Explicit completion: each rising edge", "השלמה מפורשת: כל עליית שעון"], // PREP-288
  ["Analysis assumptions: ideal resistors, ideal", "הנחות הניתוח: נגדים אידאליים, חיווט"], // PREP-290
  ["This explicitly defined atoi-style contract", "זהו חוזה מפורש בסגנון atoi,"], // PREP-295
  ["Explicit completion: zero starting phase,", "השלמה מפורשת: פאזה התחלתית אפס,"], // PREP-299
  ["Both source clauses say two", "בשני המשפטים בצילום כתוב שני"], // PREP-307
  ["Explicit completion: each channel is", "השלמה מפורשת: כל ערוץ הוא"], // PREP-310
  ["The chosen executable contract is", "חוזה המימוש שנבחר הוא JSON,"], // PREP-351
  ["Assume both runs complete successfully.", "הניחו שתי הרצות תקינות. אין"], // PREP-352
  ["Each next level first averages", "בכל רמה מחשבים תחילה לכל"], // PREP-354
  ["In this model, each equal-height", "במודל הזה כל רכיב קשיר"], // PREP-355
] as const;

// Headings without an explicit “variant” label that introduce a different exercise.
export const alternateHeadings = [
  "Seven inputs using full adders only",
  "שבע כניסות ורק מחברים מלאים",
  "General hour and minute inputs",
  "שעה ודקות כלליות",
  "Test the power and return its exponent",
  "בדיקת חזקה והחזרת המעריך",
  "Two eggs and N floors: return the highest safe floor",
  "שתי ביצים ו־N קומות: מחזירים את הקומה הבטוחה האחרונה",
  "An unpaired integer among equal pairs",
  "מספר בודד בין זוגות של מספרים שלמים",
  "D. Repetitions, zero sentinels and every missing value",
  "ד. חזרות, אפסים וכל הערכים החסרים",
  "Analyze source code with enable and simulation delay",
  "ניתוח קוד מקור עם enable והשהיית סימולציה",
  "Preserve the full carry when a+2 exceeds the word width",
  "סכום מלא כאשר a+2 עובר את רוחב המילה",
  "ד. מקור נוסף — דגלים והמתנה, ללא חיישן מפגש",
  "Reverse conversion: SR from one DFF, with two priority choices",
  "Compare two-bit words using multiplexers",
  "השוואת שתי מילים בנות שני ביטים באמצעות מוקסים",
  "מאגר גדול ללא מטא־דאטה חיצוני נוסף",
  "Constant-time maximum of a stack",
  "מקסימום במחסנית בזמן קבוע",
  "Fully specified exercise: one hundred doors and an explicit rule",
  "תרגיל מוגדר: מאה דלתות וכלל מפורש",
  "Printing a signed int with one parameter",
  "הדפסת int חתום בפונקציה עם פרמטר יחיד",
  "Count a massive bit array",
  "ספירת מערך ביטים גדול",
  "Three data paths reconverging at OR",
  "שלושה מסלולי נתונים המתכנסים ל־OR",
  "Output response to an input step",
  "תגובת מוצא למדרגת כניסה",
  "Divide by two, four and eight with safe selection",
  "חלוקה בשתיים, ארבע ושמונה ובחירה ללא פעימה קצרה",
  "Complete numerical exercise: an explicitly selected coin inventory",
  "תרגיל מספרי מלא: מלאי מטבעות שנבחר לצורך הלימוד",
] as const;
