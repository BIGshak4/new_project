# PREP-365: What determines a CMOS cell's propagation delay?

Proposed solution; educational equation checks only. Human review pending.

## מה קובע את השהיית המעבר של תא CMOS?

פרטו את הפרמטרים שמשפיעים על השהיית המעבר של שער CMOS והסבירו באילו תנאים כל שינוי מקצר או מאריך אותה ומדוע. הבדילו בין השהיית תא, זמן עלייה/ירידה, השהיית מסלול ואילוצי setup/hold.

חוזה התרגיל: נתחו מהפך CMOS עם עומס קיבולי. הגדירו tPHL כזמן בין חציית 50% בכניסה העולה לחציית 50% ביציאה היורדת, ו־tPLH עבור הקוטביות ההפוכה. אם משתמשים ב־tpd הממוצע, הגדירו (tPHL+tPLH)/2; בבדיקת חסם למסלול משתמשים בהשהיות מתאימות ולא בהכרח בממוצע.

דונו בחוזק ההנעה, רוחב ואורך, קיבול עומס, חיווט ו־fanout, סלו הכניסה, VDD,Vth, פינות תהליך וטמפרטורה. הציגו הסתייגויות מכיוונים שאינם אוניברסליים. לתרגיל מספרי בלבד החליפו את ה־NMOS המוליך ב־R=1 kΩ, בחרו C=20 fF, כניסת מדרגה אידאלית, מוצא התחלתי VDD=1 V וללא זמן תחילה נוסף. חשבו tPHL ואת זמן הירידה מ־90% ל־10%. לאחר מכן הכפילו רק את C, ואחר כך חצו רק את R ביחס לבסיס. לבסוף הסבירו מדוע הכפלת רוחב תא שלם אינה מבטיחה חציית השהיית מסלול שלם. המספרים הם השלמה לימודית ואינם נתוני ספריית תאים.

### קודם מגדירים איזה זמן מודדים
tPHL ו־tPLH הם זמני תגובה בין נקודות ייחוס בכניסה וביציאה; כאן שתיהן 50%. זמן ירידה נמדד בין שתי רמות ביציאה, כאן 90% ו־10%, ולכן אינו זהה להשהיה. בספרייה או בדף נתונים קוראים את רמות הייחוס ותנאי המדידה בפועל. השהיית מסלול כוללת תאים וחיווט לאורך המסלול הרלוונטי; setup/hold הם חלונות יציבות של רכיב הזיכרון, ונבדקים יחד עם הגעת נתונים ושעון. אין לזהות אותם עם השהיית שער יחיד.

### התחילו ממטען ומזרם
כדי לשנות יציאה במתח ΔV צריך להזיז מטען בקירוב CeffΔV. זרם גדול יותר מזיז אותו מהר יותר; קיבול גדול יותר דורש יותר מטען. אינטואיציות אלו מובילות ל־t≈CeffΔV/Ieff או, בקירוב נגד אפקטיבי, t50≈ln(2)ReffCeff. אלו מודלים מסבירים; תא אמיתי מתואר לכל קשת כניסה־יציאה וקוטביות בהתאם לסלו ולעומס.

| שינוי, כששאר התנאים קבועים | השפעה רגילה והסיבה |
|---|---|
| הגדלת עומס C או מספר כניסות שהיציאה מניעה | מאריכה זמן: יותר מטען. fanout חשמלי תלוי בסכום קיבולי הכניסות, לא רק במספרן. |
| הגדלת W של התקן מוליך | מפחיתה התנגדות ומגדילה זרם; יכולה לקצר השהיית תא תחת עומס חיצוני נתון, אך מוסיפה קיבולי שער ודיפוזיה. |
| הגדלת L | במודל תעלה ארוכה מחלישה זרם דרך W/L ובדרך כלל מאטה; בתכנון אמיתי נבדקים גם פרזיטים ושינויי סף. |
| הגדלת VDD בתחום פעולה חוקי | בדרך כלל מגדילה overdrive ומקצרת זמן, אף שגם משרעת הטעינה גדלה. אין לחרוג ממגבלות הטכנולוגיה. |
| הגדלת Vth באותו VDD | מקטינה overdrive וזרם ובדרך כלל מאריכה זמן; לא משנים סף בלי מודל תהליך. |
| כניסה איטית יותר | בדרך כלל מגדילה השהיית תא ומשך הולכה חופפת; הכיוון/הגודל המדויק תלויים בקשת ובשיטת המדידה. משתמשים בטבלת slew/load. |
| חיווט ארוך או צר יותר | התנגדות וקיבול חיווט גדלים בדרך כלל, ומוסיפים השהיה. נדרש מודל RC מבוזר למסלול ארוך. |

קיבול אפקטיבי כולל גם קיבולי יציאה, כניסות המשך, חיווט וקיבולי צימוד. שכן שמתחלף בכיוון מנוגד עשוי להגדיל את העומס האפקטיבי של צימוד לעומת שכן שקט; מעבר באותו כיוון עשוי להקטינו. הכיוון והעיתוי של האגרסור חשובים. גם טופולוגיית שער, טרנזיסטורים בטור, זהות הקלט המתחלף, מצב כניסות אחרות ומצב פנימי משפיעים. זמן הירידה נקבע בעיקר מהפריקה דרך NMOS, וזמן העלייה מהטעינה דרך PMOS; הם אינם חייבים להיות שווים.

### תהליך, מתח וטמפרטורה
פינת תהליך מהירה עשויה לתת זרמי הנעה גבוהים יותר מפינה איטית, אבל יש להבחין בין n ו־p, קשתות וקוטביות. העלאת טמפרטורה מורידה בדרך כלל ניידות ומחלישה הנעה; בו־זמנית Vth עשוי לרדת, מה שמגדיל overdrive. במתח נמוך תיתכן temperature inversion, ולכן אין לקבוע שטמפרטורה גבוהה תמיד איטית יותר. משתמשים בספרייה מאופיינת בפינת ה־PVT הרלוונטית, ובודקים גם ירידות אספקה מקומיות, שונות וחוסר ודאות. הסבר זה נועד לניתוח מגמות ולא לבחירת פינת signoff בלי נתונים.

### החישוב המספרי וגבולותיו
במודל הנבחר Vout(t)=VDD·exp(−t/RC), כאשר חציית הכניסה היא t=0. מתקבל RC=20 ps. לכן:

```text
tPHL = RC ln 2 = 13.8629 ps
t90 = −RC ln 0.9 = 2.1072 ps
t10 = −RC ln 0.1 = 46.0517 ps
tfall = t10−t90 = RC ln 9 = 43.9445 ps
```

הכפלת C בלבד נותנת tPHL=27.7259 ps וזמן ירידה 87.8890 ps. חציית R בלבד נותנת tPHL=6.9315 ps וזמן ירידה 21.9722 ps. מודל עלייה דרך Rp נותן tPLH=ln(2)RpC; אין נתון Rp בתרגיל ולכן לא נחשב ממוצע מספרי ללא הנחה נוספת.

בכניסת מדרגה אידאלית חציית 50% מוגדרת ברגע המדרגה. אם מוסיפים זמן תחילה td, אז tPHL=td+RC ln 2 ואילו זמן הירידה נשאר RC ln 9. במעגל אמיתי יש סלו כניסה, התנגדות תלוית מתח וקיבולים לא ליניאריים. אינטגרציית KCL עצמאית ב־18 תרחישי RC וב־144,000 צעדים אימתה את העקומות והחציות של המודל, ללא סימולציית טרנזיסטורים.

### מדוע הגדלת תא אינה מאיצה הכול באותו יחס
אם מכפילים את רוחבי שני ההתקנים, התנגדות ההנעה עשויה לרדת בערך פי שניים, אבל גם קיבולים עצמיים וקיבול הכניסה גדלים. השלב הקודם רואה עומס כבד יותר. אפילו אם רכיב העומס החיצוני של התא מואץ, רכיב ההשהיה הפרזיטי אינו בהכרח נחצה, והשהיית המסלול עשויה להשתפר או להחמיר. מתאימים גודל, buffering וטופולוגיה למסלול ולמטרות שטח/הספק, ואז בודקים מחדש את הקשתות והפינות הרלוונטיות. אין כלל אוניברסלי „הכפלת W חוצה tpd”.

## What determines a CMOS cell's propagation delay?

List parameters affecting CMOS-gate propagation delay and explain when each change makes it shorter or longer and why. Distinguish cell delay, output rise/fall time, path delay and setup/hold requirements.

Exercise contract: analyze a CMOS inverter driving a capacitive load. Define tPHL from the rising input's 50% crossing to the falling output's 50% crossing, and tPLH for the opposite polarity. If using an average tpd, define it as (tPHL+tPLH)/2; a path bound uses appropriate delays rather than necessarily this average.

Discuss drive strength, width/length, load capacitance, wires/fanout, input slew, VDD,Vth, process corners and temperature. Qualify effects whose direction is not universal. For a numerical exercise only, replace the conducting NMOS by R=1 kΩ, choose C=20 fF, an ideal input step, initial output VDD=1 V and no additional response-start delay. Compute tPHL and the 90%-to-10% fall time. Next double only C, then halve only R relative to baseline. Finally explain why doubling an entire cell's width does not guarantee halving a complete path's delay. These values are an educational completion, not cell-library data.

### Define the measured interval first
tPHL and tPLH are delays between input/output reference crossings, chosen here as 50%. Fall time is measured between two output levels, here 90% and 10%, so it is not the same interval. A library or datasheet specifies its actual reference levels and conditions. Path delay includes relevant cell and interconnect delays. Setup/hold are storage-element stability windows checked together with data/clock arrivals, not single-gate propagation delay.

### Start with charge and current
An output swing ΔV requires moving approximately CeffΔV charge. More current moves it faster; more capacitance requires more charge. This motivates t≈CeffΔV/Ieff or, with an effective resistance, t50≈ln(2)ReffCeff. These are explanatory models. A real cell is characterized for each input/output arc and transition polarity versus input slew and output load.

| Change with other conditions fixed | Usual effect and reason |
|---|---|
| More load C or downstream inputs | Longer delay because more charge is required. Electrical fanout depends on summed pin capacitances, not just pin count. |
| Larger conducting-device W | Lower resistance/higher drive can shorten cell delay at a specified external load, while adding gate and diffusion capacitance. |
| Longer L | In a long-channel model W/L decreases and drive weakens, usually slowing switching; real design also checks parasitics and threshold changes. |
| Higher VDD within the valid range | Usually increases overdrive and reduces delay even though the required swing also grows. Technology voltage limits still apply. |
| Higher Vth at fixed VDD | Reduces overdrive/current and usually lengthens delay; threshold changes require a process model. |
| Slower input transition | Usually increases cell delay and overlapping conduction; exact direction/amount depends on the arc and measurement convention. Use slew/load tables. |
| Longer or narrower wire | Usually increases wire resistance/capacitance and delay; a long path needs distributed RC analysis. |

Effective capacitance includes output parasitics, downstream pins, wiring and coupling. An opposite-switching neighbor can increase coupling load relative to a quiet neighbor; same-direction switching can reduce it. Aggressor direction and timing matter. Gate topology, series stacks, the changing pin, other input values and internal state also matter. NMOS discharge primarily determines a falling output, while PMOS charging determines a rising output; these delays need not be equal.

### Process, voltage and temperature
A fast process corner may provide stronger drive than a slow corner, but distinguish n/p devices, arcs and polarities. Higher temperature usually reduces mobility and weakens drive, while threshold can decrease and increase overdrive. At low voltage temperature inversion can occur, so hot is not universally slow. Use the relevant characterized PVT library, also accounting for local supply droop, variation and uncertainty. These are trend explanations, not sufficient data for choosing a signoff corner.

### Numerical calculation and its limits
In the chosen model Vout(t)=VDD·exp(−t/RC), with the input crossing at t=0. RC=20 ps. Hence:

```text
tPHL = RC ln 2 = 13.8629 ps
t90 = −RC ln 0.9 = 2.1072 ps
t10 = −RC ln 0.1 = 46.0517 ps
tfall = t10−t90 = RC ln 9 = 43.9445 ps
```

Doubling C alone gives tPHL=27.7259 ps and fall time 87.8890 ps. Halving R alone gives tPHL=6.9315 ps and fall time 21.9722 ps. A rising model through Rp gives tPLH=ln(2)RpC; Rp is unspecified, so there is no numeric average delay without an extra assumption.

For an ideal input step the 50% input crossing is defined at the step instant. Adding a response-start delay td instead gives tPHL=td+RC ln 2, while fall time stays RC ln 9. Real circuits have input slew, voltage-dependent resistance and nonlinear capacitance. Independent KCL integration in 18 RC scenarios and 144,000 steps verified this model's waveforms/crossings, without transistor simulation.

### Why cell upsizing does not scale the whole path
Doubling both device widths may roughly halve drive resistance, while increasing self capacitance and input capacitance. The predecessor sees a heavier load. Even if the external-load component speeds up, the parasitic delay need not halve, and total path delay can improve or worsen. Choose sizing, buffering and topology for the path's area/power/performance goals, then recheck relevant arcs and corners. There is no universal rule that doubling W halves tpd.

[he diagram](../diagrams/prep-365-delay-given-1115d-he.png)

[en diagram](../diagrams/prep-365-delay-given-1115d-en.png)

[he diagram](../diagrams/prep-365-delay-rc-1115d-he.png)

[en diagram](../diagrams/prep-365-delay-rc-1115d-en.png)

[Educational models](../solutions/mos1115d_models.py)
[Checks](../checks/check_mos1115d.py)
[Results](../checks/mos1115d-verification.json)
[Private source](../sources/2026-11-15-batch20d-09.png)
