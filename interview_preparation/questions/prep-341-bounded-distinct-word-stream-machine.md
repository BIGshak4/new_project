# PREP-341 — מכונת זרם שסופרת מילים שונות

פתרון מוצע.

## he

תכננו מכונת מצבים שקולטת מחרוזת המסתיימת בתו newline ומחזירה כמה מילים שונות הופיעו. רווח אחד או יותר מפריד מילים.

חוזה חומרה סופי שנבחר לתרגיל: האלפבית הוא a,b, אורך מילה לכל היותר 3, ולכן קיימות 14 מילים אפשריות. בכל חזית valid=1 מתקבל תו אחד. מותרות חזרות ורווחים בתחילה ובסוף. newline מסיים גם את המילה האחרונה. אות שאינה באלפבית או מילה ארוכה מדי מדליקה error דביק עד reset. אחרי newline מוציאים done=1 ושומרים את התוצאה עד reset; תווים מאוחרים אינם מתקבלים. הציגו מצב, זיכרון ועדכונים. הסבירו מה משתנה באלפבית רחב ובמילים באורך לא חסום.

1. הספירה של תחילת כל מילה אינה מזהה חזרות. מה צריך לזכור על מילים שכבר הסתיימו?
2. לכל מילה מותרת אפשר להקצות סיבית seen.
3. שמרו קידומת בעץ בינארי; בגבול מילה בדקו אם סיבית המילה כבר דולקת, והגדילו רק בפעם הראשונה.

### הגבול מסיים מילה, והזיכרון מזהה חזרה
ממפים a לסיבית 0 ו־b ל־1. שומרים prefix=p ואת האורך ℓ. באות חדשה מעדכנים p′=2p+bit ו־ℓ′=ℓ+1, בתנאי ℓ<3. למשל a,ab,bba מקבלות בהתאמה (ℓ,p)=(1,0),(2,1),(3,6).

למילה גמורה האינדקס הוא id=(2^ℓ−2)+p, בטווח 0..13. כך אורכים שונים אינם מתנגשים, גם כשהקידוד p כולל אפסים מובילים. שומרים seen[13:0] ומונה count בטווח 0..14. ברווח או newline, אם ℓ>0 ומצב error נקי, בודקים seen[id]. אם היא אפס מדליקים אותה ומגדילים count פעם אחת. אחר כך מאפסים p ו־ℓ. רווחים חוזרים אינם משנים את הספירה. newline מבצע קודם את אותה סגירת מילה, ורק אחר כך מעלה done, כך שהמילה האחרונה נכללת.

למשל `ab a ab bba\n` מחזיר 3. שתי ההופעות של ab פונות לאותה סיבית. רצף ריק או רווחים בלבד ואז newline מחזיר 0. valid=0 מחזיק את כל המצב. באות לא חוקית או באות רביעית מפעילים error; ממשיכים להמתין ל־newline אך התוצאה מסומנת לא תקפה. אחרי done כל הקלטים מוחזקים עד reset.

זהו מימוש סופי עם 14 סיביות seen, ארבע סיביות למונה, שלוש לקידומת, שתיים לאורך וסיביות error/done, ובקרת delimiter. אין צורך לשמור את המחרוזת כולה. ל־A אותיות ולאורך חסום L מספר המילים הוא M=Σ_{k=1..L} A^k, ולכן מפת הביטים גדלה במהירות. אם כל מילה יכולה להופיע, מכונה מדויקת חייבת להבחין בין 2^M קבוצות seen, כך שלפחות M סיביות מצב נדרשות לייצוג המידע הזה. גם hash סופי לבדו עלול להתנגש. ללא חסם מילים/אורכים וזיכרון גדל, FSM בעל מספר מצבים קבוע אינו יכול לספור בדיוק מספר לא חסום של מילים שונות.

```python
"""Finite exact character-stream controller; fourteen possible words."""


class DistinctWords:
    def __init__(self):
        self.reset()

    def reset(self):
        self.prefix = self.length = self.seen = self.count = 0
        self.error = self.done = False

    def accept(self, char, valid=True):
        if not valid or self.done:
            return
        if char in (" ", "\n"):
            if not self.error and self.length:
                index = (1 << self.length) - 2 + self.prefix
                mask = 1 << index
                if not self.seen & mask:
                    self.seen |= mask
                    self.count += 1
            self.prefix = self.length = 0
            if char == "\n":
                self.done = True
            return
        if self.error:
            return
        if char not in ("a", "b") or self.length == 3:
            self.error = True
            return
        self.prefix = 2*self.prefix + (char == "b")
        self.length += 1


def count_distinct(text):
    if not isinstance(text, str) or not text.endswith("\n") or text.count("\n") != 1:
        raise ValueError("one newline is required at the end of the input")
    unit = DistinctWords()
    for char in text:
        unit.accept(char)
    if not unit.done or unit.error:
        raise ValueError("valid newline-terminated bounded text required")
    return unit.count
```

## en

Design a state machine receiving a string terminated by newline and returning the number of distinct words. One or more spaces separate words.

Chosen finite hardware contract: alphabet a,b and maximum word length three, giving fourteen possible words. Each valid rising edge accepts one character. Repetitions and leading/trailing spaces are allowed. Newline also terminates the final word. An invalid character or overlong word sets sticky error until reset. Newline produces done=1 and holds the result until reset; later characters are ignored. Describe state, memory and updates, and explain the change for a wider alphabet or unbounded word length.

1. Counting word starts cannot detect repeated words. What must survive after a word ends?
2. Allocate one seen bit to each allowed word.
3. Track a binary-trie prefix and commit its word at a delimiter, incrementing only when its seen bit was clear.

### Delimiters close words; retained memory recognizes repetition
Map a to zero and b to one. Retain prefix p and length ℓ. Each letter updates p′=2p+bit and ℓ′=ℓ+1, provided ℓ<3. For example a, ab and bba have (ℓ,p) equal to (1,0),(2,1),(3,6).

A completed word uses id=(2^ℓ−2)+p, covering 0..13. Including length prevents collisions between prefixes containing leading zeroes. Retain seen[13:0] and count in 0..14. On space or newline, when ℓ>0 and error is clear, test seen[id]. Only a previously clear bit is set and increments count. Then clear p and ℓ. Consecutive spaces do nothing. Newline commits the last word before setting done, including a final word without trailing space.

For example, ab a ab bba followed by newline returns three. Empty input or only spaces then newline gives zero. valid=0 retains state. An invalid symbol or fourth letter sets sticky error. The machine waits for newline but marks its result invalid. After done, all input is ignored until reset.

The design uses fourteen seen bits, four count bits, three prefix bits, two length bits and error/done flags plus delimiter control. It never stores the entire text. With alphabet size A and maximum length L there are M=Σ_{k=1..L} A^k possible words. Exact arbitrary membership requires distinguishing 2^M seen sets, hence at least M information bits: different sets have different counts immediately or are distinguishable by appending a word in their symmetric difference. A fixed-width hash alone can collide. With unbounded words and a fixed finite state space, exact unbounded distinct-word counting is impossible.

```python
"""Finite exact character-stream controller; fourteen possible words."""


class DistinctWords:
    def __init__(self):
        self.reset()

    def reset(self):
        self.prefix = self.length = self.seen = self.count = 0
        self.error = self.done = False

    def accept(self, char, valid=True):
        if not valid or self.done:
            return
        if char in (" ", "\n"):
            if not self.error and self.length:
                index = (1 << self.length) - 2 + self.prefix
                mask = 1 << index
                if not self.seen & mask:
                    self.seen |= mask
                    self.count += 1
            self.prefix = self.length = 0
            if char == "\n":
                self.done = True
            return
        if self.error:
            return
        if char not in ("a", "b") or self.length == 3:
            self.error = True
            return
        self.prefix = 2*self.prefix + (char == "b")
        self.length += 1


def count_distinct(text):
    if not isinstance(text, str) or not text.endswith("\n") or text.count("\n") != 1:
        raise ValueError("one newline is required at the end of the input")
    unit = DistinctWords()
    for char in text:
        unit.accept(char)
    if not unit.done or unit.error:
        raise ValueError("valid newline-terminated bounded text required")
    return unit.count
```

[Executable model](../solutions/prep_341_hardware1115.py)
[Checks](../checks/check_hardware1115.py)
[Results](../checks/hardware1115-verification.json)

[Private source](../sources/2026-11-15-batch20-18.png)
[he diagram](../diagrams/prep-341-solution-nov15-he.png)
[en diagram](../diagrams/prep-341-solution-nov15-en.png)
