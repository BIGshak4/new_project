# PREP-357 — שינוי גודל המהפך האמצעי בשרשרת

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## שינוי גודל המהפך האמצעי בשרשרת

שלושה מהפכי CMOS מחוברים בטור. מגדילים רק את רוחב שני הטרנזיסטורים במהפך האמצעי באותו יחס s, בלי לשנות אורך תעלה. גדלי הראשון והשלישי, עומס היציאה והמתח נשארים קבועים. כיצד משתנה זמן המעבר מהכניסה ליציאה?

השלמת מודל: בקירוב מסדר ראשון, התנגדות ההנעה של התא האמצעי יורדת פי s וקיבולי הכניסה והפרזיטיים שלו גדלים פי s. דונו בנפרד בהשהיית השלב הראשון, האמצעי ובסכום. נתחו D(s)=A·s+B/s+C עבור s>0 ו־A,B>0, C≥0. הסבירו את המקרה הסימטרי A=B, והציגו גם דוגמה A=1 ps, B=4 ps, C=1 ps. המספרים הם מודל לימודי שהוסף, ללא נתוני תא מאופיינים.

### עקבו אחרי שני העומסים
נסמן את התנגדות הראשון ב־R1, קיבול הכניסה ליחידת גודל של האמצעי ב־Cg2, ואת ההתנגדות שלו בגודל יחידה ב־R2. הגדלת האמצעי גורמת לאיבר R1·s·Cg2 בשלב הראשון. בשלב האמצעי מקבלים (R2/s)·(C3+s·Cp2)=R2·C3/s+R2·Cp2. לכן רכיב העומס הפרזיטי העצמי בקירוב הזה קבוע. כל האיברים הקבועים, כולל השלב השלישי, נאספים ב־C, והסכום הוא D(s)=A·s+B/s+C.

ההגדלה מזרזת את רכיב ההנעה של האמצעי אך מאטה את הראשון. D'(s)=A−B/s² ו־D''(s)=2B/s³>0, ולכן s*=√(B/A) הוא המינימום במודל. עבור s<s* הגדלה מקטינה את D, ועבור s>s* היא מגדילה אותו. אם מותר רק להגדיל מהמצב s=1, יש תועלת בתחילה רק כאשר B>A; optimum מורשה הוא max(1,s*).

### שני מקרים ברורים
כאשר A=B, המינימום הוא s=1. הגדלה של האמצעי בלבד מעלה את הסכום, כי s+1/s≥2. לדוגמה, בלי האיבר הקבוע, s=1 נותן 2A ו־s=2 נותן 2.5A.

במודל הדוגמה A=1, B=4, C=1 פיקו־שניות, s*=2. מתקבלים D(1)=6 ps, D(2)=5 ps ו־D(4)=6 ps. זו המחשה של מאזן עומס והנעה בתנאים לא סימטריים, ולא נתון הנגזר מהצילום. עבור s גדול מאוד איבר A·s שולט.

### מה חסר לתזמון פיזי
הקירוב מתעלם מצורת גל הכניסה, קיבול Miller, חיווט, תלות התנגדות במתח והבדלי עלייה/ירידה. הגדלת שני הרוחבים שומרת בקירוב על יחס החוזקים, אך אינה קובעת זמן מספרי או מבטיחה קיצור כולל. בתא אמיתי משתמשים במודל הטכנולוגיה, slew ועומס נתונים ומריצים ניתוח מתאים לכל קוטביות. זוהי מסקנת מודל RC, ללא הרצת SPICE או signoff פיזי.

```python
"""Finite occupancy controller and explicit first-order inverter delay model."""
from math import isfinite, sqrt


def parking_step(occupancy, entry, exit_event, reset=False):
    if type(occupancy) is not int or not 0 <= occupancy < 64:
        raise ValueError("six-bit state required")
    if any(type(v) is not bool for v in (entry, exit_event, reset)):
        raise ValueError("Boolean events required")
    state_error = occupancy > 50
    exit_ok = not reset and not state_error and exit_event and occupancy > 0
    entry_ok = not reset and not state_error and entry and (occupancy < 50 or exit_ok)
    result = 0 if reset or state_error else occupancy + entry_ok - exit_ok
    return result, entry_ok, exit_ok


def delay(scale, first_load, middle_drive, fixed):
    values = scale, first_load, middle_drive, fixed
    if not all(isfinite(v) for v in values):
        raise ValueError("finite parameters required")
    if min(scale, first_load, middle_drive) <= 0 or fixed < 0:
        raise ValueError("positive scale/A/B and nonnegative C required")
    return first_load*scale + middle_drive/scale + fixed


def optimum(first_load, middle_drive):
    if not all(isfinite(v) and v > 0 for v in (first_load, middle_drive)):
        raise ValueError("positive finite A and B required")
    return sqrt(middle_drive/first_load)
```

## Resizing the middle inverter in a three-stage chain

Three CMOS inverters form a chain. Scale only both transistor widths in the middle cell by the same factor s, keeping channel length fixed. Keep the first and third sizes, output load and supply unchanged. How does input-to-output propagation delay change?

Chosen first-order model: the middle cell's effective drive resistance scales as 1/s, while its input and parasitic capacitances scale as s. Discuss the first-stage delay, middle-stage delay and total separately. Analyze D(s)=A·s+B/s+C for s>0 with A,B>0 and C≥0. Explain the symmetric case A=B and also use illustrative A=1 ps, B=4 ps, C=1 ps. These are added educational parameters without characterized-cell data.

### Follow both loads
Let the first drive resistance be R1, the middle input capacitance per unit size Cg2 and its unit drive resistance R2. Increasing the middle size introduces R1·s·Cg2 in the first-stage delay. For the middle stage, (R2/s)·(C3+s·Cp2)=R2·C3/s+R2·Cp2. Its self-parasitic term is constant in this approximation. Collect all fixed contributions, including the third stage, in C, yielding D(s)=A·s+B/s+C.

Upsizing improves the middle drive term while slowing its predecessor. D'(s)=A−B/s² and D''(s)=2B/s³>0, so s*=√(B/A) is the model minimum. Increasing size reduces D below s* and increases D above s*. If only upsizing from s=1 is allowed, initial benefit requires B>A; the constrained optimum is max(1,s*).

### Two concrete cases
With A=B the optimum is s=1. Upsizing only the middle raises total delay because s+1/s≥2. Ignoring the fixed term, s=1 gives 2A and s=2 gives 2.5A.

For illustrative A=1, B=4, C=1 ps, s*=2. Then D(1)=6 ps, D(2)=5 ps and D(4)=6 ps. This demonstrates unequal loading/drive balance and is an added example, not a parameter inferred from the photograph. At large s, A·s dominates.

### Physical timing needs further data
The approximation omits input waveform, Miller capacitance, wire loading, voltage-dependent resistance and rise/fall differences. Scaling both widths approximately preserves their strength ratio, but does not determine numeric timing or guarantee lower total delay. A real-cell evaluation needs technology models, input slew and output load for each transition polarity. This is RC-model reasoning without SPICE execution or physical signoff.

```python
"""Finite occupancy controller and explicit first-order inverter delay model."""
from math import isfinite, sqrt


def parking_step(occupancy, entry, exit_event, reset=False):
    if type(occupancy) is not int or not 0 <= occupancy < 64:
        raise ValueError("six-bit state required")
    if any(type(v) is not bool for v in (entry, exit_event, reset)):
        raise ValueError("Boolean events required")
    state_error = occupancy > 50
    exit_ok = not reset and not state_error and exit_event and occupancy > 0
    entry_ok = not reset and not state_error and entry and (occupancy < 50 or exit_ok)
    result = 0 if reset or state_error else occupancy + entry_ok - exit_ok
    return result, entry_ok, exit_ok


def delay(scale, first_load, middle_drive, fixed):
    values = scale, first_load, middle_drive, fixed
    if not all(isfinite(v) for v in values):
        raise ValueError("finite parameters required")
    if min(scale, first_load, middle_drive) <= 0 or fixed < 0:
        raise ValueError("positive scale/A/B and nonnegative C required")
    return first_load*scale + middle_drive/scale + fixed


def optimum(first_load, middle_drive):
    if not all(isfinite(v) and v > 0 for v in (first_load, middle_drive)):
        raise ValueError("positive finite A and B required")
    return sqrt(middle_drive/first_load)
```

[he diagram](../diagrams/prep-357-inverter-sizing-given-1115c-he.png)

[en diagram](../diagrams/prep-357-inverter-sizing-given-1115c-en.png)

[he diagram](../diagrams/prep-357-inverter-sizing-delay-1115c-he.png)

[en diagram](../diagrams/prep-357-inverter-sizing-delay-1115c-en.png)

[Implementation](../solutions/hardware1115c_models.py)

[Private source](../sources/2026-11-15-batch10c-09.png)
