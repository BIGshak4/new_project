# PREP-131 — מקסימום במחסנית בזמן קבוע

[צילום המקור](../sources/2026-11-14-batch30-10.png)

נתונה מחסנית עם push, pop ו־top בזמן O(1). יש לאפשר max(s) בזמן O(1), גם אחרי הוצאות, ללא הגבלה על מקום וללא מיון מראש.

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

## מקסימום במחסנית בזמן קבוע

הוסיפו גם max(s) שמחזירה את האיבר הגדול במחסנית. על push, pop, top ו־max לפעול בזמן O(1) במקרה הגרוע במודל צמתים עם הקצאה והשוואת מילה בעלות קבועה. אין מגבלת מקום ואיברים עשויים לחזור. פעולת קריאה או הוצאה ממחסנית ריקה מעלה IndexError במימוש Python. במחלקה MaxStack קוראים למקסימום באמצעות s.max(). דחיפת ערך שאינו int מעלה ValueError.

1. בגרסת המקסימום, חשבו מה צריך לשחזר אחרי שמוציאים את הגדול ביותר.
2. גם מקסימום הוא תכונה של קידומת המחסנית.
3. שמרו בכל צומת את הגדול מבין הערך החדש ומקסימום הצומת הקודם.

בכל צומת שומרים את הערך שלו, את המקסימום מעומק זה ומטה ואת הקישור לצומת הקודם. בדחיפה מחשבים max של הערך ושל המקסימום הישן; במחסנית ריקה הערך הוא המקסימום. max קוראת את השדה בראש. pop מחזירה את הערך ומקדמת את הראש, וכך משחזרת את המקסימום הקודם ללא חיפוש. לדוגמה, אחרי דחיפות 3,7,7,2, הוצאת 2 ו־7 עדיין משאירה מקסימום 7; הוצאת ה־7 הבא מחזירה מקסימום 3. באינדוקציה, המידע בצומת נראה כמו ברגע דחיפתו כיוון שהצמתים שמתחתיו לא השתנו. כל פעולה מבצעת מספר קבוע של גישות והאחסון הנוסף O(n). כדי לתמוך במינימום ובמקסימום יחד שומרים שני שדות בכל צומת.

```python
class MaxStack:
    def __init__(self):
        self.head = None

    def push(self, value):
        if type(value) is not int:
            raise ValueError("stack values must be integers")
        previous = self.head
        maximum = value if previous is None else max(value, previous[1])
        self.head = (value, maximum, previous)

    def top(self):
        if self.head is None:
            raise IndexError("empty stack")
        return self.head[0]

    def max(self):
        if self.head is None:
            raise IndexError("empty stack")
        return self.head[1]

    def pop(self):
        value = self.top()
        self.head = self.head[2]
        return value
```

## Constant-time maximum of a stack

Also support max(s), returning the largest element. Push, pop, top and max must each take worst-case O(1) in a node model with constant-cost allocation and word comparison. Extra storage is allowed and values can repeat. Reading or popping an empty stack raises IndexError in the Python implementation. Call s.max() on the MaxStack instance. Pushing a non-int raises ValueError.

1. For the maximum variant, consider what must be restored when the largest item is removed.
2. The maximum is also a property of a stack prefix.
3. Store the larger of the new value and the previous node’s maximum in each node.

Store the value, the maximum from that depth downward, and the previous-node link in each node. On push, take the greater of the new value and the previous maximum, or the new value for an empty stack. Max reads the head field. Pop returns the value and advances the head, immediately restoring the previous maximum. For example, after pushes 3,7,7,2, popping 2 and one 7 still leaves maximum 7. Popping the other 7 restores 3. By induction each head retains the correct extremum from the moment it was pushed since the nodes below it have not changed. Each operation uses a constant number of accesses and total extra storage is O(n). Store both extrema per node to support minimum and maximum together.

```python
class MaxStack:
    def __init__(self):
        self.head = None

    def push(self, value):
        if type(value) is not int:
            raise ValueError("stack values must be integers")
        previous = self.head
        maximum = value if previous is None else max(value, previous[1])
        self.head = (value, maximum, previous)

    def top(self):
        if self.head is None:
            raise IndexError("empty stack")
        return self.head[0]

    def max(self):
        if self.head is None:
            raise IndexError("empty stack")
        return self.head[1]

    def pop(self):
        value = self.top()
        self.head = self.head[2]
        return value
```

[solutions/prep_131_max_stack.py](../solutions/prep_131_max_stack.py)

[checks/check_nov14_reasoning_software.py](../checks/check_nov14_reasoning_software.py)

[checks/prep-131-1114-verification.json](../checks/prep-131-1114-verification.json)
