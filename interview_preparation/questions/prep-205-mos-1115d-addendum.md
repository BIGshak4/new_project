# PREP-205: CMOS inverter: connections, states and switching

Proposed solution; educational equation checks only. Human review pending.

## מהפך CMOS: חיבורים, מצבים ומעבר

ציירו מהפך CMOS והסבירו כיצד הוא פועל עבור כניסה נמוכה, גבוהה ובזמן מעבר. ציינו חיבורי שערים, מקורות, נקזים וגוף, ואת מסלולי טעינת ופריקת העומס.

נבחר מהפך סטטי בסיסי עם NMOS ו־PMOS משלימים, אספקת VDD חיובית וכניסה בין 0 ל־VDD. המקור אינו מספק תהליך, מידות, ספים או עומס; לכן אין לשרטט עקומת מעבר מספרית מדויקת או לטעון לתדר מרבי. התיאור הלוגי של רמות מסילה מופרד מהתנהגות אנלוגית ומזרמי דליפה.

### תגובת מוצא למדרגת כניסה
שרטטו את מוצא המהפך כאשר Vin עולה מ־0 ל־VDD בזמן t=0. הסבירו גם מדוע התגובה אינה מיידית. לצורך גרף מספרי נבחר מודל השהיה מסדר ראשון עם VDD=1 V, זמן תחילת תגובה td=0.20 ns וקבוע זמן פריקה τ=0.50 ns. מתח המוצא מתחיל ב־VDD. חשבו חציית 50% וזמן ירידה מ־90% ל־10%, והבחינו ביניהם.

### השפעת רוחב הטרנזיסטור על אופיין המעבר
במהפך CMOS הנתון הגדילו רק את רוחב ה־PMOS, כאשר רוחב ה־NMOS, אורכי התעלה, מתח האספקה, ספי ההתקנים והטמפרטורה קבועים. שרטטו את השינוי באופיין DC של Vout כתלות ב־Vin והסבירו את כיוון שינוי נקודת המיתוג Vm, המוגדרת באמצעות Vout=Vin. חזרו על הניתוח כאשר מגדילים רק את רוחב ה־NMOS. האם הגדלת שני הרוחבים באותו יחס מזיזה את Vm? הבדילו בין Vm לבין Vth של טרנזיסטור יחיד, ובין אופיין DC להשהיית מעבר.

לשם דוגמה מספרית בחרו מודל תעלה ארוכה עם VDD=1 V, Vtn=|Vtp|=0.25 V וחוזקים התחלתיים שווים βn=βp. β=μCoxW/L. השוו להכפלת βp בלבד ולהכפלת βn בלבד. השתמשו תחילה בקירוב רוויה אידאלי למציאת Vm. לשרטוט עקומה יחידה השתמשו בהרחבה הרציפה I=Icore·(1+λVDS), עם λ=0.15 V⁻¹ בשני ההתקנים ובשני אזורי ההולכה; עבור PMOS משתמשים ב־VSG,VSD ובגודל הזרם. זהו מודל לימודי ללא נתוני תהליך.

### שני טרנזיסטורים שמשלימים זה את זה
ה־PMOS העליון מחובר במקורו ל־VDD, בנקזו ל־Vout ובשערו ל־Vin. ה־NMOS התחתון מחובר במקורו ל־GND, בנקזו לאותה Vout ובשערו לאותה Vin. בגוף bulk רגיל, גוף ה־PMOS/ה־well מחובר ל־VDD וגוף ה־NMOS למתח האדמה בהתאם לתהליך. החיבורים הללו מוצגים במפורש בשרטוט; אין להחליף שער בנקז.

Vin=0 נותן ל־PMOS מתח שער־מקור שלילי בעוצמה מספקת, והוא מוליך; ה־NMOS כבוי. היציאה נטענת דרך ה־PMOS לכיוון VDD ולכן הלוגיקה היא אחד. Vin=VDD מכבה את ה־PMOS ומפעיל את ה־NMOS; העומס נפרק לאדמה ולכן היציאה אפס. במודל המתגים האידאלי אין בשני מצבי המסילה מסלול DC ישיר מ־VDD לאדמה. במציאות קיימים זרמי דליפה, ולכן „הספק סטטי אפס” הוא קירוב ולא מדידה.

### מה קורה בין אפס לאחד?
אם Vtn<Vin<VDD−|Vtp| בתחום שבו התנאים חופפים, שני ההתקנים יכולים להוליך ונוצר זרם קצר־דרך בזמן המעבר. גם טעינה ופריקה של קיבול העומס צורכות אנרגיה; ההספק הדינמי תלוי בפעילות, בקיבול, במתח ובתדר. היציאה אינה משתנה מיד, ו־rise/fall delays תלויים בחוזק ההתקנים ובעומס. כניסה צפה או איטית מדי אינה מצב לוגי תקין מובטח.

צורת Vout(Vin) יורדת באופן טיפוסי, אבל נקודת המיתוג אינה בהכרח VDD/2: היא תלויה בספים וביחס חוזק NMOS/PMOS. בלי נתוני תהליך אין מספר יחיד לקביעתה, למרווחי רעש או להשהיה. ההסבר על רמות מסילה וזרמי מעבר נסמך על [TI — צריכת הספק ב־CMOS](https://www.ti.com/lit/an/scaa035b/scaa035b.pdf) ועל [Toshiba — פעולת CMOS בסיסית](https://toshiba.semicon-storage.com/ap-en/semiconductor/knowledge/e-learning/cmos-logic-basics/chap2/chap2-3.html). המודל המצורף בודק רק מצבי הולכה אידאליים, ולא מחליף ניתוח אנלוגי.

### מודל לוגי בפייתון שהורץ

```python
"""Ideal rail-input switch model, separate from any analog transfer curve."""


def rail_inverter(vin_bit):
    if vin_bit not in (0, 1):
        raise ValueError("rail model accepts only zero or one")
    pmos_on = vin_bit == 0
    nmos_on = vin_bit == 1
    return {"pmos_on": pmos_on, "nmos_on": nmos_on,
            "vout_bit": 1 - vin_bit, "ideal_dc_rail_path": pmos_on and nmos_on}


def gate_overdrive_flags(vin, vdd=1.0, vtn=0.3, vtp_abs=0.3):
    if not 0 <= vin <= vdd or min(vtn, vtp_abs) <= 0:
        raise ValueError("positive thresholds and legal input voltage required")
    # Only indicates possible channel conduction, not output voltage/current.
    return vin > vtn, (vdd - vin) > vtp_abs
```


במהפך CMOS אמיתי מדרגה גבוהה מדליקה את NMOS ומכבה את PMOS, והקיבול במוצא נפרק. במודל שנבחר Vout=VDD עד td, ולאחר מכן Vout=VDD exp(−(t−td)/τ). לכן t50=td+τ ln 2≈0.5466 ns. חציית 90% בזמן 0.2527 ns וחציית 10% בזמן 1.3513 ns, ולכן זמן הירידה הוא τ ln 9≈1.0986 ns.

במהפך לוגי אידאלי עם השהיה ניתן לצייר פשוט מעבר מ־1 ל־0 אחרי tp. העקומה המעריכית היא השלמה לימודית עם קיבול והתנגדות אפקטיביים. td,τ והסף אינם נובעים מהצילום, והערכים אינם מאפייני תא ייצור. ללא מודל עומס/תהליך אין תשובה מספרית יחידה. במדרגה יורדת בכניסה המוצא עולה; במודל טעינה מקביל Vout=VDD(1−exp(−(t−td)/τp)), והשהיות העלייה והירידה עשויות להיות שונות.

```python
"""First-order capacitive-load illustration, not a characterized transistor model."""
from math import exp, isfinite, log


def falling_output(time, delay=0.2, tau=0.5, vdd=1.0):
    if (not all(isfinite(v) for v in (time, delay, tau, vdd))
            or delay < 0 or tau <= 0 or vdd <= 0):
        raise ValueError("finite time and positive physical constants required")
    return vdd if time <= delay else vdd * exp(-(time - delay) / tau)


def threshold_crossing(fraction, delay=0.2, tau=0.5):
    if not 0 < fraction < 1 or delay < 0 or tau <= 0:
        raise ValueError("fraction in (0,1) and legal timing constants required")
    return delay - tau * log(fraction)
```

### זרם המשיכה למעלה מול זרם המשיכה למטה
במצב DC ללא עומס מוליך מתקיים Ip=In. כאשר מגדילים Wp בלבד, βp גדל וה־PMOS מושך למעלה חזק יותר באותם מתחי הדקים. כדי להגיע לאותה יציאה דרושה Vin גדולה יותר: היא מחזקת את ה־NMOS ומחלישה את ה־PMOS. לכן אזור המעבר נע ימינה ו־Vm עולה. הגדלת Wn בלבד מחזקת את הפריקה; המעבר נע שמאלה ו־Vm יורד. זו אינה הזזה קשיחה של כל העקומה: השיפוע, הרוחב ומרווחי הרעש עשויים להשתנות, ובמודל התקין רמות הקצה נשארות קרובות למסילות.

### גזירת נקודת המיתוג בקירוב אידאלי
ב־Vout=Vin=Vm שני ההתקנים ברוויה תחת תנאי הדוגמה. הזנחת מודולציית אורך תעלה נותנת:

```text
βn(Vm−Vtn)² = βp(VDD−Vm−|Vtp|)²
r = sqrt(βp/βn)
Vm = [Vtn + r(VDD−|Vtp|)]/(1+r)
```

כאשר VDD>Vtn+|Vtp|, הנגזרת לפי r חיובית: (VDD−|Vtp|−Vtn)/(1+r)². לכן כיוון השינוי נובע מהמשוואה, ולא רק מהציור. בדוגמה: חוזקים שווים נותנים 0.500 V; הכפלת βp נותנת בקירוב 0.5429 V; הכפלת βn נותנת 0.4571 V. רוחבים גאומטריים שווים אינם מבטיחים β שווים, כי גם הניידויות שונות.

הגרפים משתמשים ב־λ חיובי ובפתרון KCL בכל Vin. בהם מתקבלים בהתאמה Vm=0.5000,0.54218,0.45782 V; זהו הבדל צפוי מן הקירוב λ=0. ל־Icore משתמשים במשוואת הטריודה β[(VGS−Vth)VDS−VDS²/2] לפני הרוויה וב־β(VGS−Vth)²/2 אחריה, כאשר VGS>Vth. הכפלה ב־1+λVDS בשני האזורים שומרת על רציפות בגבול. במודל הרוויה האידאלי לחלוטין, ברגע ששני זרמי הרוויה שווים עשוי להיות תחום יציאות אפשרי באותה Vin; לכן אין לייחס למודל הזה לבדו עקומת מעבר חלקה ויחידה.

### יחס חוזקים לעומת גודל כולל
הכפלת שני β באותו גורם מכפילה את שני צדי KCL, ולכן אופיין ה־DC ו־Vm אינם משתנים במודל שנבחר. לעומת זאת, התנגדויות, קיבולי שער ודיפוזיה, טעינת השלב הקודם והשהיות כן משתנים. הגדלת PMOS עשויה לקצר עליית יציאה תחת עומס חיצוני נתון, אך גם להגדיל קיבול ולהעמיס על הקלט; לא נובע מכך שכל מסלול יואץ.

Vm הוא נקודת איזון של שני טרנזיסטורים במעגל. Vth מתאר הופעת היפוך/הגדרת סף בהתקן יחיד. שינוי רוחב אינו נחשב שינוי Vth במודל זה. בהתקן פיזי ייתכנו השפעות גאומטריה ותהליך המחייבות מודל מאופיין. גם מרווחי רעש דורשים הגדרת VIL,VIH וניתוח שיפוע; אין להסיק שכולם משתפרים יחד. בדיקות המודל השוו 1,005 נקודות DC לפתרון עצמאי בחשבון Decimal ואינטגרל מטען תעלה. זו בדיקת משוואות, ללא SPICE או מדידה.

## CMOS inverter: connections, states and switching

Draw a CMOS inverter and explain operation for low input, high input and switching. Identify gate, source, drain and body connections and the load charging/discharging paths.

Choose a basic static complementary NMOS/PMOS inverter, positive VDD, and inputs within the supply rails. No process, sizing, thresholds or load are supplied, so no exact numerical transfer curve or maximum frequency is implied. Separate the rail-level logic model from analog behavior and leakage.

### Output response to an input step
Draw the inverter output when Vin rises from 0 to VDD at t=0 and explain why it is not instantaneous. For a numerical plot choose a first-order delayed response with VDD=1 V, response-start delay td=0.20 ns and discharge time constant τ=0.50 ns. The output initially equals VDD. Find the 50% crossing and 90%-to-10% fall time, distinguishing the two.

### Transistor width and the voltage-transfer curve
For the given CMOS inverter, increase only PMOS width while keeping NMOS width, channel lengths, supply, device thresholds and temperature fixed. Sketch the change in the DC Vout-versus-Vin curve and explain the direction of the switching-point change. Define Vm by Vout=Vin. Repeat when only NMOS width increases. Does scaling both widths by the same factor move Vm? Distinguish Vm from one device's Vth, and the DC curve from transition delay.

For a numerical illustration use a long-channel model with VDD=1 V, Vtn=|Vtp|=0.25 V and initially equal strengths βn=βp, where β=μCoxW/L. Compare doubling βp alone and doubling βn alone. First find Vm using ideal saturation. To draw a single-valued curve, use the continuous extension I=Icore·(1+λVDS), with λ=0.15 V⁻¹ on both devices in both conducting regions; use VSG,VSD and current magnitude for PMOS. This is a teaching model without process data.

### Two complementary devices
The upper PMOS has source at VDD, drain at Vout and gate at Vin. The lower NMOS has source at ground, drain at the same Vout and gate at the same Vin. In a conventional bulk implementation, connect the PMOS body/well to VDD and NMOS body to ground as required by the process. The diagram identifies these terminals; do not confuse a gate with a drain.

Vin=0 supplies sufficient negative gate-source voltage to turn on the PMOS while NMOS is off. The load charges through PMOS toward VDD, giving logic one. Vin=VDD turns PMOS off and NMOS on; the load discharges toward ground, giving zero. In the ideal switch model neither rail-input state has a direct DC path from VDD to ground. Real devices leak, so “zero static power” is an approximation rather than a measured guarantee.

### Between the rails
When Vtn<Vin<VDD−|Vtp| and the intervals overlap, both devices can conduct, producing transition short-circuit current. Charging and discharging load capacitance also consumes energy; dynamic power depends on activity, capacitance, voltage and frequency. Output does not change instantaneously, and rise/fall delays depend on sizing and load. Floating or excessively slow inputs do not provide a guaranteed valid logic state.

The typical transfer characteristic decreases with Vin, but its switching point is not universally VDD/2: thresholds and relative NMOS/PMOS strengths matter. Without process data there is no unique numerical switching point, noise margin or delay. Rail and transient behavior are described by [TI's CMOS power note](https://www.ti.com/lit/an/scaa035b/scaa035b.pdf) and [Toshiba's CMOS operation guide](https://toshiba.semicon-storage.com/ap-en/semiconductor/knowledge/e-learning/cmos-logic-basics/chap2/chap2-3.html). The attached model checks only ideal conduction states; it is not an analog analysis.

### Executed Python logical model

```python
"""Ideal rail-input switch model, separate from any analog transfer curve."""


def rail_inverter(vin_bit):
    if vin_bit not in (0, 1):
        raise ValueError("rail model accepts only zero or one")
    pmos_on = vin_bit == 0
    nmos_on = vin_bit == 1
    return {"pmos_on": pmos_on, "nmos_on": nmos_on,
            "vout_bit": 1 - vin_bit, "ideal_dc_rail_path": pmos_on and nmos_on}


def gate_overdrive_flags(vin, vdd=1.0, vtn=0.3, vtp_abs=0.3):
    if not 0 <= vin <= vdd or min(vtn, vtp_abs) <= 0:
        raise ValueError("positive thresholds and legal input voltage required")
    # Only indicates possible channel conduction, not output voltage/current.
    return vin > vtn, (vdd - vin) > vtp_abs
```


In a CMOS inverter a high input turns NMOS on and PMOS off, discharging output capacitance. In the chosen model Vout=VDD until td and Vout=VDD exp(−(t−td)/τ) afterward. Thus t50=td+τ ln 2≈0.5466 ns. The 90% and 10% crossings are 0.2527 ns and 1.3513 ns, giving fall time τ ln 9≈1.0986 ns.

An ideal delayed logic model simply changes from one to zero after tp. The exponential is an explicit educational completion using effective resistance/capacitance. The source supplies no td,τ or threshold, and these numbers are not characterized production-cell parameters. Without load/process data there is no unique numeric result. A falling input instead produces a rising output, illustrated by Vout=VDD(1−exp(−(t−td)/τp)) after td, with potentially different rise/fall parameters.

```python
"""First-order capacitive-load illustration, not a characterized transistor model."""
from math import exp, isfinite, log


def falling_output(time, delay=0.2, tau=0.5, vdd=1.0):
    if (not all(isfinite(v) for v in (time, delay, tau, vdd))
            or delay < 0 or tau <= 0 or vdd <= 0):
        raise ValueError("finite time and positive physical constants required")
    return vdd if time <= delay else vdd * exp(-(time - delay) / tau)


def threshold_crossing(fraction, delay=0.2, tau=0.5):
    if not 0 < fraction < 1 or delay < 0 or tau <= 0:
        raise ValueError("fraction in (0,1) and legal timing constants required")
    return delay - tau * log(fraction)
```

### Pull-up current versus pull-down current
For a DC output without a conducting external load, Ip=In. Increasing Wp alone increases βp and strengthens pull-up at the same terminal voltages. Reaching the same output then requires a larger Vin, which strengthens NMOS and weakens PMOS. The transition region moves right and Vm rises. Increasing Wn alone strengthens discharge, so the transition moves left and Vm falls. This is not a rigid translation of the entire curve: slope, transition width and noise margins may change, while the proper rail levels remain close to the supply rails.

### Derive the ideal switching-point approximation
At Vout=Vin=Vm both devices are saturated under the example's assumptions. Neglecting channel-length modulation gives:

```text
βn(Vm−Vtn)² = βp(VDD−Vm−|Vtp|)²
r = sqrt(βp/βn)
Vm = [Vtn + r(VDD−|Vtp|)]/(1+r)
```

For VDD>Vtn+|Vtp| its derivative with respect to r is positive: (VDD−|Vtp|−Vtn)/(1+r)². This establishes the direction algebraically. Equal strengths give 0.500 V; doubling βp gives about 0.5429 V; doubling βn gives 0.4571 V. Equal geometric widths need not give equal β because carrier mobilities differ.

The plots instead use positive λ and solve KCL at each Vin. Their switching points are respectively 0.5000,0.54218,0.45782 V, an expected difference from the λ=0 approximation. Icore is β[(VGS−Vth)VDS−VDS²/2] in triode and β(VGS−Vth)²/2 in saturation, for VGS>Vth. Multiplying by 1+λVDS in both regions preserves continuity at their boundary. With perfectly ideal saturation, equal saturation currents can permit an interval of output voltages at a single Vin; that model alone does not determine a smooth unique transition curve.

### Strength ratio versus overall size
Multiplying both β values by the same factor multiplies both sides of KCL, leaving the chosen model's DC curve and Vm unchanged. Resistance, gate/diffusion capacitance, predecessor loading and transient delays do change. A wider PMOS may speed the rising output for a specified external load, while also adding capacitance and input loading; it does not guarantee a faster entire path.

Vm is a balance point of two devices in a circuit. Vth describes inversion onset/a threshold definition for one device. Width scaling does not change Vth in this model. Real geometry/process effects need a characterized model. Noise margins also require definitions of VIL,VIH and slope analysis; they do not all necessarily improve together. Model checks compared 1,005 DC points against an independent Decimal channel-charge integration and root solve. This verifies equations, without SPICE or measurements.

[he diagram](../diagrams/prep-205-width-given-1115d-he.png)

[en diagram](../diagrams/prep-205-width-given-1115d-en.png)

[he diagram](../diagrams/prep-205-width-vtc-1115d-he.png)

[en diagram](../diagrams/prep-205-width-vtc-1115d-en.png)

[Educational models](../solutions/mos1115d_models.py)
[Checks](../checks/check_mos1115d.py)
[Results](../checks/mos1115d-verification.json)
[Private source](../sources/2026-11-15-batch20d-07.png)
