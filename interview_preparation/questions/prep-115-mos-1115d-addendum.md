# PREP-115: MOSFET structure, doping, current characteristics and supply bias

Proposed solution; educational equation checks only. Human review pending.

## מבנה MOSFET, אילוח, אופייני זרם והשפעת מתח האספקה

א. שרטטו חתך MOSFET והסבירו את הגוף, המקור, השפך, השער והמבודד. כיצד מייצרים אזורי n+ ומה ההבדל בינם לבין תעלת היפוך?
ב. שרטטו אופייני ID מול VDS עבור כמה ערכי VGS, ו־ID מול VGS בתנאי רוויה. תנו משוואות זרם ותנאי תחומים, הגדירו פרמטרים ויחידות.
ג. כיצד שינוי VDD עשוי להשפיע? הגדירו חיבור מתח מסוים והסבירו מה משתנה בו.

הנחות והגדרות: המקור אינו בוחר NMOS או PMOS, טכנולוגיה או מעגל הטיה. נשתמש ב־NMOS מסוג enhancement, חתך מישורי בגוף p, מקור וגוף מחוברים, VDS≥0, טמפרטורה קבועה ומודל תעלה ארוכה עם ניידות קבועה. מודל הבסיס מזניח זרם תת־סף ומודולציית אורך תעלה. הפרידו הרחבות וקירובים מהמודל הזה, וציינו בקצרה את שינוי הקוטביות ב־PMOS. VDD הוא שם של אספקת המעגל ואינו מסוף חמישי של הטרנזיסטור. אין נתוני תהליך או מדידות שהופכים את המודל לתחזית כמותית של רכיב מודרני.

### הרחבה: תפקיד טרנזיסטור וכניסת מדרגה שלא זוהתה
מה תפקיד הטרנזיסטור, ומה קורה כשמכניסים פונקציית מדרגה? בצילום מופיע ממש הביטוי ״לגודל״. אין שרטוט ולא מוגדרת צומת קלט, ולכן אין לתקן בשקט ל־gate או לקבוע תגובת מוצא מסוימת. הסבירו קודם אילו נתונים חסרים. כהמחשה מסומנת בלבד, נתחו NMOS במבנה pull-down עם נגד pull-up ל־VDD וקיבול מוצא, כאשר מדרגת מתח 0→VDD נכפית על השער, והמוצא התחיל גבוה. הבדילו בין מדרגה אידאלית בשער לבין מקור מדרגה המחובר דרך התנגדות וקיבול שער.

### מקור Vth והפשרה בין הספק סטטי לדינמי
השתמשו בחתך ה־NMOS שבתרגיל, עם גוף ומקור מחוברים. הסבירו כיצד מתח השער יוצר תעלת היפוך ומדוע קיים מתח סף Vth. אילו תכונות של המבנה והתהליך משפיעות עליו? הבחינו בין סף התקן לבין נקודת מיתוג של מהפך.

לאחר מכן השוו שתי אפשרויות סף חיובי, 0.30 V ו־0.40 V, בטמפרטורה ובגאומטריה קבועות: איזו נעדיף כדי לצמצם דליפת תת־סף במצב כבוי, ומה המחיר בזמן מעבר? האם אפשר לבחור Vth שמקטין תמיד הספק דינמי? נתחו תחילה α,C,VDD,f קבועים. לשם חישוב נבחר Ioff∝exp[−Vth/(nUT)] עם n=1.5,UT=25.85 mV, וכן Psw=αCVDD²f עם α=0.1 אירועי טעינה 0→1 למחזור, C=20 fF,VDD=1 V,f=1 GHz. דונו בנפרד באפשרות לשנות VDD, גודל או תדר כדי לשמר יעד ביצועים. זהו מודל לימודי; אין הנחה שכל רכיבי הדליפה מתנהגים כמו תת־סף.

### שני תפקידים שונים: ליצור נתיב ולדחוף מטען לאורכו
חשבו על השער כבקר של כמות האלקטרונים בתעלה, ועל הפרש המתח בין השפך למקור כדוחף אותם לאורכה. אלו שני מתחים שונים: VGS=VG−VS ו־VDS=VD−VS. הגוף הוא המסוף הרביעי; כאן מחברים אותו למקור כדי שלא לשנות את מתח הסף בגלל הטיית גוף.

### א. מה רואים בחתך
הגוף הוא סיליקון מסוג p. בתוכו שני אזורים מאולחים חזק מסוג n+, המקור S והשפך D. מגע גוף p+ מאפשר לחבר את הגוף B. מעל השטח שביניהם יש מבודד שער דק, ומעליו אלקטרודת שער G. בדוגמה לימודית המבודד הוא SiO2 והשער מתכת או פוליסיליקון; מבני high-k, FinFET ואחרים אינם אותו חתך פשוט.

n+ פירושו ריכוז גבוה של תורמים פעילים, למשל זרחן או ארסן. בתהליך מישורי טיפוסי מחדירים יוני תורמים לאזורים שנבחרו במסכה, ואז מבצעים טיפול חום להפעלת האילוח ולתיקון נזקי ההחדרה. אפשר גם תהליכי אילוח אחרים. סימן הפלוס מציין אילוח חזק, לא מתח חיובי על האזור. שינוי VG אינו יוצר אטומי אילוח: מתח שער חיובי מספיק יוצר ליד פני הגוף שכבת היפוך של אלקטרונים ניידים. השכבה הזו מחברת חשמלית את המקור לשפך כשהרכיב מוליך, ואינה אזור n+ שיוצר בתהליך.

### ב. שלושה תחומים במודל המוצהר
נסמן Vov=VGS−VT ו־β=μn·Cox·W/L. הניידות μn נמדדת ב־m²/(V·s), קיבול המבודד ליחידת שטח Cox ב־F/m², והיחס W/L חסר יחידות. לכן β נמדד ב־A/V² ו־ID באמפר.

| תנאי | תחום | זרם במודל הבסיס |
| --- | --- | --- |
| VGS≤VT | קיטעון | ID=0 |
| VGS>VT וגם 0≤VDS<Vov | לינארי / טריודה | ID=β·(Vov·VDS−VDS²/2) |
| VGS>VT וגם VDS≥Vov | רוויה | ID=β·Vov²/2 |

בטריודה כמות המטען המקומית פוחתת לכיוון השפך. אינטגרציה של β·(Vov−v) בין 0 ל־VDS נותנת את המשוואה. כאשר VDS=Vov, קצה התעלה סמוך לשפך מגיע לצביטה והמודל עובר לרוויה. צביטה אינה חסימת הזרם: אלקטרונים עדיין עוברים לאזור השפך. בהצבת הגבול בשתי הנוסחאות מקבלים אותו זרם, ולכן אין קפיצה באופיין האידיאלי. הזרם המקובל ID זורם משׂפך למקור; תנועת האלקטרונים הפוכה.

לדוגמה, β=1 mA/V², VT=0.5 V ו־VGS=1.5 V נותנים Vov=1 V. עבור VDS=0.25 V מתקבל ID=0.21875 mA; עבור VDS≥1 V מתקבל ID=0.5 mA במודל האידיאלי. באופיין ID מול VDS הזרם עולה ומתיישר, ועבור VGS גבוה יותר מתקבלת עקומה גבוהה יותר. אופיין ID מול VGS הוא ריבועי מעל VT רק כל עוד נשמר תנאי הרוויה עבור כל נקודה.

### ג. קודם מחברים את VDD, ורק אז מסיקים
אם S=B=0, השפך מוחזק ב־2 V והשער מחובר ל־VDD, שינוי VDD משנה VGS. בטווח VDD>VT ו־2≥VDD−VT, הזרם הוא β·(VDD−VT)²/2. לעומת זאת, אם VGS=1.5 V קבוע ורק השפך מחובר ל־VDD, הזרם עולה בטריודה עד VDD=1 V ואז נשאר קבוע במודל האידיאלי. לכן המשפט ״הגדלת VDD תמיד מגדילה את הזרם״ אינו תשובה בלי חיבור והנחות.

ברכיב אמיתי יש זרם תת־סף, תלות בטמפרטורה, שינוי ניידות ומגבלות מתח. מודולציית אורך תעלה מוסיפה שיפוע גם ברוויה; הרחבה מקומית אפשרית כאן היא ID≈(β·Vov²/2)·[1+λ·(VDS−Vov)] לרוויה בלבד, עם λ ביחידות 1/V. זו בחירת קירוב רציפה בגבול, לא התאמה שנמדדה. הטיית גוף משנה VT, ותופעות תעלה קצרה ומהירות נשאים עלולות לפסול את חוק הריבוע. ל־PMOS מחליפים את סוגי האילוח והקוטביות: גוף n, מקור/שפך p+, ומשתמשים ב־VSG,VSD,|VTp| ובגודל הזרם. הקוד והגרפים הם מודל משוואות לימודי; אינם SPICE, BSIM או מדידת חומרה.

```python
"""Educational DC equation model, not a process/BSIM or measured-device model.

Enhancement NMOS, source tied to body, VDS >= 0, constant mobility and VT.
All voltages are volts, beta = mu_n * Cox * W/L is A/V**2; ID is amperes.
The ideal core omits subthreshold conduction and channel-length modulation.
"""
from math import isfinite


def nmos_current(vgs, vds, beta, vth):
    """Return (region, ID) for the declared long-channel model."""
    values = (vgs, vds, beta, vth)
    if any(isinstance(value, bool) or not isfinite(value) for value in values):
        raise ValueError("finite real parameters required")
    if beta <= 0 or vth <= 0 or vds < 0:
        raise ValueError("require beta > 0, VT > 0, VDS >= 0")
    overdrive = vgs - vth
    if overdrive <= 0:
        return "cutoff", 0.0
    if vds < overdrive:
        return "triode", beta * (overdrive * vds - vds * vds / 2)
    return "saturation", beta * overdrive * overdrive / 2


def saturation_with_clm(vgs, vds, beta, vth, channel_lambda):
    """Optional local CLM approximation, continuous at VDS = VGS - VT.

    Uses 1 + lambda*(VDS - VDSsat), lambda in 1/V. Valid only in
    saturation; lambda is not a universal device constant or a fit here.
    """
    region, current = nmos_current(vgs, vds, beta, vth)
    if not isfinite(channel_lambda) or channel_lambda < 0:
        raise ValueError("lambda must be finite and nonnegative")
    if region != "saturation":
        raise ValueError("optional CLM extension requires saturation")
    return current * (1 + channel_lambda * (vds - (vgs - vth)))
```


### אין תגובת מדרגה בלי להגדיר את המערכת
טרנזיסטור שולט בזרם בין שני מסופים באמצעות מתח או זרם במסוף בקרה, לפי סוג ההתקן. ניתן להשתמש בו כמתג, כמגבר או כרכיב העברה; ״התפקיד״ אינו קבוע לכל חיבור. במודל ה־NMOS המקורי כאן VGS משפיע על זרם הנקז. תיאור BJT או PMOS היה מחייב סימנים וממשק אחרים.

המילה ״לגודל״ אינה שם צומת מזוהה. חסרים סוג ההתקן, חיבורי מסופים, מתחי הטיה, מקום המדרגה, עומס ומה נמדד. למשל מדרגה בשער NMOS יכולה לגרום למוצא נקז לרדת במבנה common-source, בעוד מדרגה באספקה או מקור עוקב נותנת התנהגות אחרת. אי אפשר לבחור אחת מהן כעובדת מקור.

### המחשה שנבחרה בגלוי
נניח NMOS שמקורו לאדמה, נקזו במוצא, נגד Rpullup למתח VDD וקבל Cout לאדמה. המוצא היה גבוה לפני t=0. מדרגה חיובית נכפית ישירות על השער. בקירוב מתג פשוט, ה־NMOS נהיה Ron, ומתקבל:

```text
Vfinal = VDD*Ron/(Rpullup+Ron)
tau = (Rpullup || Ron)*Cout
Vout(t) = Vfinal + (VDD-Vfinal)*exp(-t/tau)
```

המוצא אינו קופץ בקבל ואינו בהכרח מגיע לאפס. זהו מודל RC עם Ron קבוע, לא משוואת MOS מלאה ולא נתון שסופק בצילום. בלי Cout או התנגדויות לא נקבע זמן מעבר מספרי.

גם לשער MOS אין ״אפס זרם״ בכל מצב: במודל DC אידאלי זרם השער זניח, אבל טעינת קיבולי שער דורשת זרם מעבר. אם מקור מדרגה מזין את השער דרך Rs ובקירוב קיבול Cg, אז Vg(t)=Vstep(1−exp(−t/(RsCg))); זו אינה אותה הנחה כמו מדרגה אידאלית שכבר נכפית על Vg. במדרגה אידאלית ממש על קבל יש זרם אימפולס במודל המתמטי, לא זרם פיזי סופי שנחזה מכאן.

16 תצורות המחשת RC הושוו לאינטגרציה עצמאית של משוואת הזרם ב־16,016 דגימות. הבדיקה מאמתת רק את ההמחשה שהגדרנו ואינה פותרת את חוסר הצומת בצילום. המקור והניסוח הקודם נשמרים, והרמזים הנוספים מופיעים בנפרד.

```python
"""Explicit added resistor-switch example, not the ambiguous source's circuit."""

from math import exp


def drain_after_gate_turn_on(time, *, supply=3.3, pullup=1000.0, on_resistance=100.0, load_capacitance=1e-9):
    """Gate is an externally forced step; output starts at supply and relaxes.

    Model NMOS as Ron after turn-on. Rpullup remains attached. No gate slew,
    threshold transition, channel-charge effect or physical device fit is implied.
    """
    if min(supply, pullup, on_resistance, load_capacitance) <= 0 or time < 0:
        raise ValueError("positive parameters and nonnegative time required")
    final_voltage = supply * on_resistance / (pullup + on_resistance)
    equivalent = pullup * on_resistance / (pullup + on_resistance)
    tau = equivalent * load_capacitance
    return final_voltage + (supply - final_voltage) * exp(-time / tau)
```


### הסף נובע מהאלקטרוסטטיקה של מבנה MOS
השער מבודד מן הסיליקון. ב־NMOS עם גוף מסוג p, מתח שער חיובי דוחה חורים מהמשטח ויוצר תחילה אזור מחסור במטען נייד. הגדלת המתח מושכת מספיק אלקטרונים לממשק כדי ליצור היפוך: תעלה עשירה באלקטרונים המחברת בין אזורי המקור והנקז מסוג n+. השדה משנה את אוכלוסיית הנשאים; הוא אינו מוסיף אטומי אילוח ואינו מחייב זרם DC דרך תחמוצת אידאלית. VDS גורם לזרם לאורך התעלה; VGS שולט במטענה.

Vth הוא הגדרה שימושית של תחילת היפוך חזק, ולא גבול שבו הזרם האמיתי קופץ מאפס. במודל פלנרי ארוך־תעלה, עם VSB=0 ו־φF=(kT/q)ln(NA/ni)>0 בגוף p, קירוב המחסור נותן:

```text
Vth0 = VFB + 2φF + sqrt(4qεSiNAφF)/Cox
Cox = εox/tox
Vth(VSB) = Vth0 + γ[sqrt(2φF+VSB)−sqrt(2φF)]
```

כאן Cox הוא קיבול ליחידת שטח, VFB כולל הבדל פונקציות עבודה ומטען תחמוצת, ו־γ הוא מקדם אפקט גוף. לכן חומר השער, אילוח, עובי/חומר המבודד ומטענים משפיעים על הסף. בנוסחת הגוף מניחים הטיה חוקית של הצמתים ו־VSB≥0; בגוף הקשור למקור VSB=0. התקן קצר־תעלה דורש גם השפעות כגון DIBL, ואי אפשר להפוך את הנוסחה לקבוע אוניברסלי לכל טכנולוגיה. PMOS מתואר בסימנים הפוכים וב־|Vtp|.

### Vth גבוה: פחות תת־סף, פחות זרם הנעה באותו מתח
במודל הדליפה שנבחר, העלאת הסף ב־0.10 V נותנת יחס Ioff חדש/ישן = exp[−0.10/(1.5·0.02585)]≈0.07585, כלומר ירידה פי כ־13.18. ב־VDD קבוע אותו יחס חל על רכיב ההספק VDD·Ioff. זה אינו מבטיח אותו יחס בדליפת שער, דליפת צמתים או בסך הדליפה של מעגל שלם.

מצד שני, במודל רוויה ארוך־תעלה Ion∝(VDD−Vth)². עבור VDD=1 V מעבר מ־Vth=0.30 ל־0.40 V מקטין את הזרם פי (0.60/0.70)²≈0.7347. בקירוב t∝CVDD/Ion, זמן המעבר גדל פי 1.3611, כאשר C ושאר הפרמטרים קבועים. אלו יחסים של המודל; השהיית תא מאופיין תלויה גם בסלו, עומס, מסלול ומצב ההתקנים. קרבה של VDD ל־Vth מחריפה מאוד את מגבלת הביצועים.

### הספק דינמי: יש להגדיר מה נשאר קבוע
אירוע טעינה מלא 0→1 שואב מהאספקה אנרגיה CVDD²; מחציתה נאגרת בקבל ומחציתה מתבזבזת במסלול הטעינה. במחזור טעינה־פריקה מלא כל האנרגיה מתפזרת. לכן עבור α המוגדר כאירועי 0→1 למחזור, Psw=αCVDD²f. בדוגמה Psw=2 μW בשתי אפשרויות Vth כל עוד α,C,VDD,f קבועים. Vth כלל אינו מופיע באיבר זה. אם משתמשים בפעילות שסופרת את שתי החזיתות יש להתאים את גורם החצי.

להקטנת האיבר הקיבולי פועלים ישירות על פעילות, קיבול, מתח או תדר. הקטנת VDD מ־1 ל־0.8 V באותם C,α,f נותנת 1.28 μW, אך בדרך כלל מאטה את המעגל. סף נמוך יותר עשוי לאפשר את הורדת האספקה תוך עמידה ביעד זמן, במחיר דליפה; לחלופין פיצוי על סף גבוה באמצעות טרנזיסטורים רחבים יותר מגדיל קיבולים. ההשפעה הכוללת תלויה באילוצים. גם זרם קצר־דרך בזמן מעבר וגליצ'ים יכולים להוסיף להספק הדינמי. לכן אין תשובה גורפת „Vth גבוה/נמוך מקטין דינמי” בלי חוזה ביצועים ושאר הנתונים.

Vth שייך להתקן יחיד; Vm של מהפך הוא Vin שבו Vout=Vin ונקבע מאיזון זרמי PMOS/NMOS. שאלת המשך טבעית היא בחירת תאי high-Vth במסלולים בעלי מרווח זמן ותאי low-Vth במסלולים קריטיים, ולא שינוי אחיד לכל השבב.

## MOSFET structure, doping, current characteristics and supply bias

A. Draw a MOSFET cross-section and explain body, source, drain, gate and insulator. How are n+ regions fabricated, and how do they differ from an inversion channel?
B. Plot ID against VDS for several VGS values and ID against VGS under saturation conditions. Give current equations, region conditions, parameter definitions and units.
C. How can changing VDD affect operation? Specify a bias connection and identify what changes.

Assumptions and definitions: the source specifies neither NMOS/PMOS, technology nor bias circuit. Use an enhancement NMOS, planar p-type body, source tied to body, VDS≥0, fixed temperature and a long-channel constant-mobility model. The core neglects subthreshold current and channel-length modulation. Separate extensions/approximations from this model and briefly explain the PMOS polarity changes. VDD names a circuit supply, not a fifth transistor terminal. No process data or measurements make this a quantitative model of a modern device.

### Extension: transistor role and an unidentified step-input node
What does a transistor do, and what happens when a step is applied? The screenshot literally uses the unidentified word legodel; no circuit or input node is specified. Do not silently replace it withgate or assert one output waveform. First identify missing information. As a separately labeled illustration only, analyze an NMOS pull-down with resistor pull-up to VDD and output capacitance, whose gate is forced from 0 to VDD and output starts high. Distinguish an ideal gate step from a step source connected through resistance and gate capacitance.

### Where Vth comes from: static and dynamic power tradeoffs
Use the exercise's NMOS cross-section with body tied to source. Explain how gate voltage forms an inversion channel and why a threshold Vth exists. Which structural/process properties affect it? Distinguish device threshold from an inverter's switching point.

Then compare positive threshold choices of 0.30 V and 0.40 V at fixed geometry and temperature: which reduces off-state subthreshold leakage, and what timing cost follows? Can one Vth choice always reduce dynamic power? First hold α,C,VDD,f fixed. For calculation choose Ioff∝exp[−Vth/(nUT)] with n=1.5,UT=25.85 mV, and Psw=αCVDD²f with α=0.1 charging events 0→1 per cycle, C=20 fF,VDD=1 V,f=1 GHz. Separately discuss changing VDD, size or frequency to maintain a performance target. These are educational models; not every leakage component is assumed to follow the subthreshold relation.

### Two separate jobs: create a path and drive charge along it
Think of the gate as controlling the electron charge available in the channel, while the drain-to-source voltage drives motion along that channel. These are distinct voltages: VGS=VG−VS and VDS=VD−VS. Body is the fourth terminal; tying it to source removes body-bias variation from our threshold model.

### A. Reading the cross-section
The body is p-type silicon containing heavily doped n+ source S and drain D. A p+ body contact connects B. A thin gate insulator separates the intervening surface from gate electrode G. In the teaching example the insulator is SiO2 and the gate is metal or polysilicon; high-k structures, FinFETs and other technologies are not this simple cross-section.

n+ denotes a high concentration of electrically active donors, such as phosphorus or arsenic. A typical planar process implants donor ions into selected masked regions, then anneals to activate dopants and repair implantation damage. Other doping processes exist. The plus denotes heavy doping, not a positive terminal voltage. Gate bias does not create dopant atoms: sufficiently positive gate bias induces a mobile electron inversion sheet near the body surface. That sheet electrically connects source and drain during conduction; it is distinct from fabricated n+ regions.

### B. Three regions in the declared model
Let Vov=VGS−VT and β=μn·Cox·W/L. Mobility μn has units m²/(V·s), oxide capacitance per area Cox has units F/m², and W/L is dimensionless. Thus β has units A/V² and ID is amperes.

| Condition | Region | Core-model current |
| --- | --- | --- |
| VGS≤VT | Cutoff | ID=0 |
| VGS>VT and 0≤VDS<Vov | Linear / triode | ID=β·(Vov·VDS−VDS²/2) |
| VGS>VT and VDS≥Vov | Saturation | ID=β·Vov²/2 |

In triode, local inversion charge decreases toward the drain. Integrating β·(Vov−v) from 0 to VDS produces the equation. At VDS=Vov the channel reaches pinch-off near the drain and enters saturation. Pinch-off does not block current: electrons still reach the drain region. Substitution at the boundary gives the same current from both equations, so the ideal characteristic is continuous. Conventional ID flows drain to source; electron motion is opposite.

For example, β=1 mA/V², VT=0.5 V and VGS=1.5 V give Vov=1 V. At VDS=0.25 V, ID=0.21875 mA; for VDS≥1 V the ideal current is 0.5 mA. The ID–VDS curve rises then levels off; higher VGS yields a higher curve. The ID–VGS curve is quadratic above VT only while the saturation condition remains true at every plotted point.

### C. Connect VDD before drawing a conclusion
If S=B=0, drain is held at 2 V and gate connects to VDD, changing VDD changes VGS. For VDD>VT and 2≥VDD−VT, current is β·(VDD−VT)²/2. Conversely, with VGS fixed at 1.5 V and only drain connected to VDD, current rises through triode until VDD=1 V and then stays constant in the ideal model. Therefore, “raising VDD always raises current” is incomplete without wiring and assumptions.

Real devices have subthreshold current, temperature dependence, mobility changes and voltage limits. Channel-length modulation gives saturation a slope; an optional local extension here is ID≈(β·Vov²/2)·[1+λ·(VDS−Vov)] in saturation only, with λ in 1/V. This is a boundary-continuous approximation choice, not a measured fit. Body bias changes VT, while short-channel and carrier-velocity effects can invalidate the square law. For PMOS reverse doping and voltage polarity: n-type body, p+ source/drain, and use VSG,VSD,|VTp| and current magnitude. Code and plots are educational equation models, not SPICE, BSIM or hardware measurements.

```python
"""Educational DC equation model, not a process/BSIM or measured-device model.

Enhancement NMOS, source tied to body, VDS >= 0, constant mobility and VT.
All voltages are volts, beta = mu_n * Cox * W/L is A/V**2; ID is amperes.
The ideal core omits subthreshold conduction and channel-length modulation.
"""
from math import isfinite


def nmos_current(vgs, vds, beta, vth):
    """Return (region, ID) for the declared long-channel model."""
    values = (vgs, vds, beta, vth)
    if any(isinstance(value, bool) or not isfinite(value) for value in values):
        raise ValueError("finite real parameters required")
    if beta <= 0 or vth <= 0 or vds < 0:
        raise ValueError("require beta > 0, VT > 0, VDS >= 0")
    overdrive = vgs - vth
    if overdrive <= 0:
        return "cutoff", 0.0
    if vds < overdrive:
        return "triode", beta * (overdrive * vds - vds * vds / 2)
    return "saturation", beta * overdrive * overdrive / 2


def saturation_with_clm(vgs, vds, beta, vth, channel_lambda):
    """Optional local CLM approximation, continuous at VDS = VGS - VT.

    Uses 1 + lambda*(VDS - VDSsat), lambda in 1/V. Valid only in
    saturation; lambda is not a universal device constant or a fit here.
    """
    region, current = nmos_current(vgs, vds, beta, vth)
    if not isfinite(channel_lambda) or channel_lambda < 0:
        raise ValueError("lambda must be finite and nonnegative")
    if region != "saturation":
        raise ValueError("optional CLM extension requires saturation")
    return current * (1 + channel_lambda * (vds - (vgs - vth)))
```


### A step response needs a defined system
A transistor controls current between terminals through a control voltage or current, depending on device type. It may be used as a switch, amplifier or pass device; its role is circuit-dependent. In this record'sNMOS model, VGS affects drain current. BJT or PMOS would require a different interface and polarity.

The quoted source word does not identify a node. Missing information includes device type, connections, bias, step location, load and observed output. A gate step on a common-source NMOS may drive its drain downward; a supply step or source-follower topology behaves differently. None can be asserted as the original circuit.

### Explicit added illustration
Choose an NMOS from output to ground, a pull-up resistor to VDD and output capacitance Cout, initially charged high. Force a positive gate step at t=0. Approximating the on transistor by Ron gives:

```text
Vfinal = VDD*Ron/(Rpullup+Ron)
tau = (Rpullup || Ron)*Cout
Vout(t) = Vfinal + (VDD-Vfinal)*exp(-t/tau)
```

Capacitor voltage remains continuous and need not reach zero. This is a constant-Ron RC approximation, not a full MOS equation or source-supplied circuit. Without resistance and capacitance values, no numeric switching time follows.

AnMOS gate also does not imply zero current during every transition: ideal DC gate current is negligible, but capacitance charging needs transient current. A step source behind Rs driving lumped Cg gives Vg(t)=Vstep(1−exp(−t/(RsCg))), unlike directly imposing a step at Vg. An ideal voltage step directly across a capacitor implies a mathematical current impulse, not a finite physical current predicted by this illustration.

Sixteen explicit RC scenarios matched independent current-equation integration at 16,016 samples. This checks only the stated illustration and does not resolve the missing node. Original copy/hints remain intact; new hints are supplemental.

```python
"""Explicit added resistor-switch example, not the ambiguous source's circuit."""

from math import exp


def drain_after_gate_turn_on(time, *, supply=3.3, pullup=1000.0, on_resistance=100.0, load_capacitance=1e-9):
    """Gate is an externally forced step; output starts at supply and relaxes.

    Model NMOS as Ron after turn-on. Rpullup remains attached. No gate slew,
    threshold transition, channel-charge effect or physical device fit is implied.
    """
    if min(supply, pullup, on_resistance, load_capacitance) <= 0 or time < 0:
        raise ValueError("positive parameters and nonnegative time required")
    final_voltage = supply * on_resistance / (pullup + on_resistance)
    equivalent = pullup * on_resistance / (pullup + on_resistance)
    tau = equivalent * load_capacitance
    return final_voltage + (supply - final_voltage) * exp(-time / tau)
```


### Threshold follows MOS electrostatics
The gate is insulated from silicon. For an NMOS in a p-type body, a positive gate voltage repels holes from the surface, initially creating a depletion region. Further voltage attracts enough electrons to the interface for inversion: an electron-rich channel connecting the n+ source and drain regions. The electric field changes carrier populations; it does not add dopant atoms or require DC current through an ideal oxide. VDS drives channel current, while VGS controls channel charge.

Vth is a useful definition of strong-inversion onset, not a boundary where real current jumps from zero. For a planar long-channel device with VSB=0 and φF=(kT/q)ln(NA/ni)>0 in the p body, the depletion approximation gives:

```text
Vth0 = VFB + 2φF + sqrt(4qεSiNAφF)/Cox
Cox = εox/tox
Vth(VSB) = Vth0 + γ[sqrt(2φF+VSB)−sqrt(2φF)]
```

Cox is capacitance per unit area; VFB includes the work-function difference and oxide charge; γ is the body-effect coefficient. Gate material, doping, insulator thickness/material and charges therefore affect threshold. The body relation assumes valid junction bias and VSB≥0; a source-tied body gives VSB=0. Short-channel devices also require effects such as DIBL, so this is not a universal formula for every technology. PMOS reverses polarities and uses |Vtp|.

### Higher Vth: less subthreshold current, less drive at the same supply
In the chosen leakage model, increasing threshold by 0.10 V gives new/old Ioff = exp[−0.10/(1.5·0.02585)]≈0.07585, about a 13.18-fold reduction. At fixed VDD the VDD·Ioff power component has the same ratio. This does not imply the same change in gate leakage, junction leakage or a complete circuit's total leakage.

Conversely, the long-channel saturation model gives Ion∝(VDD−Vth)². At VDD=1 V, changing Vth from 0.30 to 0.40 V reduces drive by (0.60/0.70)²≈0.7347. With t∝CVDD/Ion and fixed C/other parameters, the transition-time proxy increases by 1.3611. These are model ratios; characterized cell delay also depends on input slew, load, path and device state. Bringing VDD close to Vth makes performance much more difficult.

### Dynamic power: state what remains fixed
One complete 0→1 charging event draws CVDD² energy from the supply: half is stored on the capacitor and half is dissipated during charging. Across a full charge/discharge cycle all of it dissipates. Thus, with α counting 0→1 events per cycle, Psw=αCVDD²f. The example gives 2 μW for both thresholds when α,C,VDD,f stay fixed. Vth does not appear in this capacitive term. An activity definition counting both edge types needs the corresponding factor of one half.

To reduce this term, directly reduce activity, capacitance, voltage or frequency. Dropping VDD from 1 to 0.8 V at the same C,α,f gives 1.28 μW but generally slows operation. Lower Vth may enable lower supply while meeting a timing target, at a leakage cost. Conversely, compensating for higher Vth with wider devices increases capacitance. The net effect depends on the constraints. Transition short-circuit current and glitches can also add dynamic power. There is consequently no universal high/low-Vth answer for dynamic power without a performance contract and the other conditions.

Vth belongs to one device. An inverter's Vm is the Vin where Vout=Vin, established by PMOS/NMOS current balance. A natural extension uses high-Vth cells where timing slack permits and low-Vth cells on critical paths, instead of changing every device uniformly.

[he diagram](../diagrams/prep-115-threshold-structure-1115d-he.png)

[en diagram](../diagrams/prep-115-threshold-structure-1115d-en.png)

[he diagram](../diagrams/prep-115-threshold-power-1115d-he.png)

[en diagram](../diagrams/prep-115-threshold-power-1115d-en.png)

[Educational models](../solutions/mos1115d_models.py)
[Checks](../checks/check_mos1115d.py)
[Results](../checks/mos1115d-verification.json)
[Private source](../sources/2026-11-15-batch20d-08.png)
