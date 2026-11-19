# PREP-205 — מהפך CMOS: חיבורים, מצבים ומעבר

פתרון מוצע.

[מקור פנימי](../sources/2026-11-15-batch20b-08.png)

## he

ציירו מהפך CMOS והסבירו כיצד הוא פועל עבור כניסה נמוכה, גבוהה ובזמן מעבר. ציינו חיבורי שערים, מקורות, נקזים וגוף, ואת מסלולי טעינת ופריקת העומס.

נבחר מהפך סטטי בסיסי עם NMOS ו־PMOS משלימים, אספקת VDD חיובית וכניסה בין 0 ל־VDD. המקור אינו מספק תהליך, מידות, ספים או עומס; לכן אין לשרטט עקומת מעבר מספרית מדויקת או לטעון לתדר מרבי. התיאור הלוגי של רמות מסילה מופרד מהתנהגות אנלוגית ומזרמי דליפה.

### תגובת מוצא למדרגת כניסה
שרטטו את מוצא המהפך כאשר Vin עולה מ־0 ל־VDD בזמן t=0. הסבירו גם מדוע התגובה אינה מיידית. לצורך גרף מספרי נבחר מודל השהיה מסדר ראשון עם VDD=1 V, זמן תחילת תגובה td=0.20 ns וקבוע זמן פריקה τ=0.50 ns. מתח המוצא מתחיל ב־VDD. חשבו חציית 50% וזמן ירידה מ־90% ל־10%, והבחינו ביניהם.

1. אחד הטרנזיסטורים צריך לחבר את היציאה למתח הגבוה והשני לאדמה. מי צריך להוליך עבור כניסה נמוכה? מדרגה עולה בכניסה צריכה לגרום לירידה במוצא, אחרי השהיה.
2. חברו את שני השערים ל־Vin ואת שני הנקזים ל־Vout; המקורות הולכים למסילות המתאימות. הקבל במוצא צריך לפרוק מטען דרך מסלול ההולכה. השתמשו במודל מעריכי שנבחר במפורש.
3. ב־Vin=0 ה־PMOS טוען את היציאה וה־NMOS כבוי. ב־Vin=VDD התפקידים מתחלפים. בזמן מעבר ייתכן ששניהם מוליכים. ל־t>td חשבו Vout=VDD exp(−(t−td)/τ). השהיית 50% כוללת את td; זמן 90%–10% הוא הפרש חציות.

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

## en

Draw a CMOS inverter and explain operation for low input, high input and switching. Identify gate, source, drain and body connections and the load charging/discharging paths.

Choose a basic static complementary NMOS/PMOS inverter, positive VDD, and inputs within the supply rails. No process, sizing, thresholds or load are supplied, so no exact numerical transfer curve or maximum frequency is implied. Separate the rail-level logic model from analog behavior and leakage.

### Output response to an input step
Draw the inverter output when Vin rises from 0 to VDD at t=0 and explain why it is not instantaneous. For a numerical plot choose a first-order delayed response with VDD=1 V, response-start delay td=0.20 ns and discharge time constant τ=0.50 ns. The output initially equals VDD. Find the 50% crossing and 90%-to-10% fall time, distinguishing the two.

1. One device pulls the output high and the other pulls it low. Which must conduct for a low input? A rising input step causes a falling output after a delay.
2. Connect both gates to Vin and both drains to Vout, with sources at the appropriate rails. Output capacitance must discharge through a conducting path. Use the explicitly chosen exponential model.
3. At Vin=0 the PMOS charges the output and NMOS is off. At Vin=VDD the roles reverse. Both can conduct during a transition. For t>td use Vout=VDD exp(−(t−td)/τ). The 50% delay includes td; 90%-to-10% time is a difference of crossings.

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

[Executable reference](../solutions/inverter_step_rc1115b.py)
[Checks](../checks/check_sta1115b.py)
[Verification](../checks/sta1115b-verification.json)
[he diagram](../diagrams/prep-205-sta-given-1115b-he.png)
[en diagram](../diagrams/prep-205-sta-given-1115b-en.png)
[he diagram](../diagrams/prep-205-sta-solution-1115b-he.png)
[en diagram](../diagrams/prep-205-sta-solution-1115b-en.png)
