# PREP-364 — אימות FIFO: מה אובד כשמסירים את המוניטור?

הצעה לפתרון. בדיקות מודל ממוחשבות. ממתין לביקורת מקצועית.

## אימות FIFO: מה אובד כשמסירים את המוניטור?

בסביבת אימות ל־FIFO קיימים generator,driver,interface,reference model ו־monitor. הסבירו מה תפקידו של כל רכיב ומה עלול לקרות אם מסירים את ה־monitor. הבחינו בין כיסוי של בקשות שנוצרו, כיסוי תעבורה שהתקבלה, בדיקות תקינות ו־code coverage.
השתמשו בדוגמה מוגדרת: FIFO סינכרוני בעומק2, ללא bypass בריק. כתיבה מתקבלת בחזית עם in_valid AND in_ready, קריאה עם out_valid AND out_ready. ראש התור מוצג לפני החזית ונשאר יציב תחת backpressure. מלא מאפשר כתיבת החלפה רק יחד עם קריאה שהתקבלה באותה חזית. איפוס סינכרוני מרוקן את התור וגובר על תעבורה. הראו מקרה שבו כוונת ה־driver שונה מהתעבורה, ותכננו איסוף וכיסוי שמסוגלים לגלות אובדן, שינוי סדר או נתון שגוי. אין צורך ב־UVM או בכלי מסוים.

### מפרידים בין יצירת כוונה לבין תצפית על הממשק
ה־generator בוחר פעולות ונתונים. ה־driver מתרגם אותן לאותות ומכבד את פרוטוקול ההעברה. ה־interface מרכז אותות ותזמון דגימה. המוניטור צופה באופן פסיבי באותות הממשק ומפיק אירועים שמשקפים מה ה־DUT קיבל או הוציא. מודל הייחוס מנבא התנהגות, ו־scoreboard משווה תחזית לתצפית. רכיבים יכולים להיות מאוחדים בקוד, אך תפקידיהם שונים.

בכל חזית ללא איפוס, דגמו את הערכים שהיו יציבים לפני העדכון: push=in_valid AND in_ready, pop=out_valid AND out_ready. out_data הוא הראש לפני החזית. על reset מרוקנים את המודל, ולא מתעדים העברה גם אם valid/ready גבוהים. תזמון הדגימה חייב להתאים לסביבת הסימולציה, למשל clocking block או דגימה מוגדרת שמונעת מרוץ עם עדכוני ה־driver וה־DUT.

דוגמה בעומק2: כתבו A ואזB וה־FIFO מלא. ה־driver מבקש לכתובC כשהצרכן אינו מוכן. יש שלוש בקשות שנוצרו אך רק שתי כתיבות שהתקבלו, כי in_ready=0 לבקשתC. כיסוי מבוסס־generator עשוי לטעון שביקרנו בכתיבתC; מודל שמוסיףC על סמך הכוונה משבש את מצב התור. אם ה־driver משאירC עד handshake מאוחר יותר, זו עדיין בקשה אחת וכתיבה אחת שהתקבלה, לא כתיבה בכל מחזור המתנה.

### מודל וכיסוי שמחוברים לתעבורה האמיתית
החזיקו deque של מילים שהתקבלו. בתחילת כל דגימה בדקו out_valid=(size>0) ו־in_ready=(size<2 OR (out_valid AND out_ready)) בחוזה שנבחר. אם out_valid, השוו out_data לראש המודל גם כשאין pop, כדי לבדוק נתון יציב ונכון בהמתנה. אם pop השוו ואז הסירו את הראש; אם push הוסיפו את in_data לסוף. ב־push ו־pop בו־זמנית, הקריאה היא מהראש הישן ורק אחר כך מוסיפים את הכתיבה. בריק שתי בקשות מקבלות רק כתיבה, ללא bypass; במלא קריאה וכתיבה יחד שומרות על size=2 ומחליפות את הזנב.

התור המנבא נותן סדר FIFO באינדוקציה: push מוסיף רק בסוף, pop מסיר ומשווה רק את הישן בראש, ואירועים חסומים אינם משנים תוכן. השוואת דגלים למצב המנובא נדרשת בנוסף; מודל שמאמין לכל ready/valid שגוי בלי לבדוק את החוזה יכול לפספס תקלה בפרוטוקול. פענוח occupancy רק מהפעולות שהתקבלו אינו תחליף למדידת הדגלים.

אספו bins ל־occupancy 0,1,2 לפני החזית, push, pop, שניהם, כתיבה חסומה וקריאה חסומה; הוסיפו רצף חיצוני שמחייב wrap, או bins של מצביעים אם הם נצפים, וכן reset כשהתור אינו ריק, ורצף backpressure ושחרורו. כיסוי פונקציונלי מראה שאירוע או שילוב נצפה, לא שהתוצאה נכונה. ה־scoreboard וה־assertions בודקים נכונות. code coverage מודד אילו שורות/ענפים/תנאים רצו, ויכול להישאר פעיל גם ללא מוניטור; הוא אינו הוכחת סדר או שלמות נתונים.

### מה באמת קורה בלי המוניטור?
אם אין שום תצפית חלופית, המודל עלול להישאר בלי נתוני השוואה וכיסוי תעבורה עלול להיעלם או להציג רק כוונת גירוי. טסט יכול להסתיים ללא שגיאות אף שנתונים אבדו, משום שאיש לא בדק את המוצא. עם זאת, שם מחלקה monitor אינו תנאי לאימות: sampler פסיבי ב־interface, assertions או driver שדוגם באופן אמין את כל ההעברות והמוצאים יכולים למלא את תפקיד התצפית. שימוש ב־driver לבדו עלול לפספס תעבורה שלא הוא יזם או מוצא DUT; יש להוכיח מה בדיוק הוא דוגם.

תשובה קצרה: ה־driver אומר מה ניסינו; תצפית פסיבית אומרת מה קרה. רק העברות שהתקבלו מקדמות את המודל, ונתוני מוצא נבדקים נגדו. הסרת המחלקה אפשרית אם משמרים את מלוא תפקידה. המשך: הזריקו החלפה בין שתי מילים או ready שגוי ובדקו ש־scoreboard/בדיקת דגלים נכשלים, גם כאשר כל בקשות ה־generator הושלמו. עלות המודל היא O(depth) אחסון ו־O(1) פעולה לכל חזית; כיסוי עשוי לצבור עוד מצב בהתאם ל־bins.

```python
from collections import deque

class FifoObserver:
    """Passive reference state, driven by sampled accepted transfers only.

    No bypass; a full FIFO allows a replacement write with an accepted read.
    out_data is sampled pre-edge. Reset is not a traffic transaction.
    """
    def __init__(self,depth):
        if type(depth) is not int or depth<1:raise ValueError("positive depth")
        self.depth=depth;self.expected=deque();self.coverage=set();self.read_values=[]

    def sample(self,in_valid,in_ready,in_data,out_valid,out_ready,out_data,reset=False):
        if reset:
            self.expected.clear();self.coverage.add('reset');return False,False
        count=len(self.expected)
        # Flag contract is independent of requested transfers.
        want_out=(count>0)
        want_in=(count<self.depth) or (want_out and bool(out_ready))
        assert bool(out_valid)==want_out, "out_valid differs from reference occupancy"
        assert bool(in_ready)==want_in, "in_ready differs from specified full replacement rule"
        pop=bool(out_valid and out_ready);push=bool(in_valid and in_ready)
        self.coverage.add(('occupancy',count))
        if out_valid:
            assert out_data==self.expected[0], "FIFO data/order mismatch while valid"
        if pop:
            assert self.expected, "underflow"
            self.read_values.append(self.expected.popleft())
        if push:self.expected.append(in_data)
        if push:self.coverage.add('accepted_write')
        if pop:self.coverage.add('accepted_read')
        if in_valid and not in_ready:self.coverage.add('blocked_write')
        if out_ready and not out_valid:self.coverage.add('blocked_read')
        if push and pop:self.coverage.add('simultaneous')
        assert 0<=len(self.expected)<=self.depth
        return push,pop
```

### בדיקות שבוצעו
המוניטור נבדק מול FIFO מעגלי עצמאי בעומקים2 ו־3 על229,376 דגימות. נבדקו חסימות, העברות בו־זמניות ותפוסות0..3, וכן איפוס כשהתור אינו ריק. ארבע מוטציות מכוונות נדחו: ראש שגוי בהמתנה, out_valid שגוי, in_ready שגוי וסדר שגוי. דוגמת שלוש בקשות ושתי כתיבות שהתקבלו נבדקה בנפרד. איסוף כיסוי מצביעים פנימיים מוצע כהמשך ואינו ממומש ב־deque. אלה בדיקות Python של הדוגמה, ללא הרצת UVM או FIFO פיזי.

## FIFO verification: what is lost without a monitor?

A FIFO verification environment contains a generator, driver, interface, reference model and monitor. Explain each role and what can happen if the monitor is removed. Distinguish generated-request coverage, accepted-traffic coverage, correctness checking and code coverage.
Use this concrete example: a synchronous depth-two FIFO with no empty bypass. A write is accepted on in_valid AND in_ready and a read on out_valid AND out_ready at an edge. The head is visible before the edge and stable under backpressure. A full FIFO allows replacement only with an accepted read at that edge. Assume synchronous reset empties it and overrides traffic. Show driver intent differing from traffic, and design observation/coverage that detects loss, reordering or wrong data. No particular framework or UVM implementation is required.

### Separate intent generation from interface observation
The generator chooses operations/data. The driver converts them to pins and obeys the transfer protocol. The interface groups pins and sampling timing. A passive monitor observes interface signals and emits events describing what the DUT actually accepted or produced. A reference model predicts behavior and a scoreboard compares predictions to observations. Code may combine roles, but their responsibilities remain distinct.

At every nonreset edge sample the values stable before the update: push=in_valid AND in_ready and pop=out_valid AND out_ready. out_data is the pre-edge head. Reset clears the reference state and is not a transfer even if valid/ready are high. Sampling must follow simulator scheduling, such as a clocking block or a defined sampling point avoiding races with driver/DUT updates.

Depth-two example: write A then B, filling the FIFO. Request writing C while the consumer is not ready. There are three generated requests but two accepted writes because in_ready=0 for C. Generator coverage can claim a C request occurred; appending C to the model from intent corrupts reference state. If the driver holds C until a later handshake, that is still one request and one accepted write, not a write on each wait cycle.

### Connect the model and coverage to real transfers
Keep a deque of accepted words. At each sample first check out_valid=(size>0) and in_ready=(size<2 OR (out_valid AND out_ready)) under this contract. Whenever out_valid, compare out_data with the reference head even without pop, checking correct/stable data while stalled. On pop compare then remove the head; on push append in_data. For simultaneous operations read the old head before appending. At empty, simultaneous requests accept only a write with no bypass; at full, an accepted read and write preserve size two while replacing the tail.

Inductively push appends only to the end, pop compares/removes only the old head, and blocked events do not alter content, preserving FIFO order. Also compare flags against predicted occupancy: blindly trusting faulty ready/valid can hide protocol bugs. Occupancy reconstructed from accepted operations does not substitute for observing flags.

Collect bins for pre-edge occupancy 0,1,2, push, pop, both, blocked write and blocked read; add externally observed wrap sequences (or pointer bins when internal pointer observation is available), reset while nonempty, and backpressure/release sequences. Functional coverage establishes that an event or combination was observed, not that it was correct. Scoreboards/assertions check correctness. Code coverage measures executed lines/branches/conditions and can remain available without a monitor; it does not prove order or losslessness.

### What does removing the monitor really change?
Without any replacement observation, the model may receive no comparison data and accepted-traffic coverage may disappear or reflect only stimulus intent. A test may end without errors despite lost data because nobody checked outputs. However, a class named monitor is not mandatory: a passive interface sampler, assertions, or a driver reliably sampling every accepted transaction and output can fulfill observation responsibilities. A driver alone may miss traffic it did not initiate or DUT output behavior; establish exactly what it samples.

Oral answer: the driver describes what was attempted; passive observation describes what happened. Only accepted transfers advance the model, and observed outputs are compared against it. The class can be removed if its complete role survives elsewhere. Follow-up: inject swapped words or incorrect ready and require scoreboard/flag assertions to fail even when every generated request completed. Model cost is O(depth) storage and O(1) work per edge; coverage state depends on the chosen bins.

```python
from collections import deque

class FifoObserver:
    """Passive reference state, driven by sampled accepted transfers only.

    No bypass; a full FIFO allows a replacement write with an accepted read.
    out_data is sampled pre-edge. Reset is not a traffic transaction.
    """
    def __init__(self,depth):
        if type(depth) is not int or depth<1:raise ValueError("positive depth")
        self.depth=depth;self.expected=deque();self.coverage=set();self.read_values=[]

    def sample(self,in_valid,in_ready,in_data,out_valid,out_ready,out_data,reset=False):
        if reset:
            self.expected.clear();self.coverage.add('reset');return False,False
        count=len(self.expected)
        # Flag contract is independent of requested transfers.
        want_out=(count>0)
        want_in=(count<self.depth) or (want_out and bool(out_ready))
        assert bool(out_valid)==want_out, "out_valid differs from reference occupancy"
        assert bool(in_ready)==want_in, "in_ready differs from specified full replacement rule"
        pop=bool(out_valid and out_ready);push=bool(in_valid and in_ready)
        self.coverage.add(('occupancy',count))
        if out_valid:
            assert out_data==self.expected[0], "FIFO data/order mismatch while valid"
        if pop:
            assert self.expected, "underflow"
            self.read_values.append(self.expected.popleft())
        if push:self.expected.append(in_data)
        if push:self.coverage.add('accepted_write')
        if pop:self.coverage.add('accepted_read')
        if in_valid and not in_ready:self.coverage.add('blocked_write')
        if out_ready and not out_valid:self.coverage.add('blocked_read')
        if push and pop:self.coverage.add('simultaneous')
        assert 0<=len(self.expected)<=self.depth
        return push,pop
```

### Executed checks
The observer passed 229,376 samples against an independent circular FIFO at depths 2 and 3, covering blocking, simultaneous transfers and occupancies 0..3, plus reset while nonempty. Four intentional mutations were rejected: wrong stalled head, wrong out_valid, wrong in_ready and reordered head. The three-requests/two-accepted-writes example was separately checked. Internal pointer-bin coverage is a follow-up, not implemented by the deque sampler. These are Python checks of the example, without a UVM run or physical FIFO test.

[he diagram](../diagrams/prep-364-fifo-monitor-1115d-he.png)

[en diagram](../diagrams/prep-364-fifo-monitor-1115d-en.png)

[Implementation](../solutions/digital1115d_models.py)

[Private source](../sources/2026-11-15-batch20d-17.png)
