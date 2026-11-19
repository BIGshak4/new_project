# PREP-340 — המקסימום של שש־עשרה מילים בנות שתי סיביות

פתרון מוצע.

## he

לקלט בן 32 סיביות יש פירוק ל־16 מילים unsigned ‏x_i=(h_i,l_i) בנות שתי סיביות. תכננו לוגיקה משערי AND,OR,NOT שמוציאה את הערך הגדול ביותר, בשתי סיביות. אין צורך להוציא אינדקס. כל המילים נוכחות במקביל. תנו משוואות, הוכחת נכונות והשוואת עומק לעץ משווים זוגיים.

1. בכל מילה יש רק ארבע אפשרויות. אפשר לבדוק אם אחת הקטגוריות מופיעה.
2. הסיבית הגבוהה של המקסימום אומרת אם קיימת מילה ששווה לפחות 2.
3. אם קיימת מילה גבוהה, הסיבית הנמוכה נקבעת על פי קיום 3. אחרת היא נקבעת על פי קיום 1.

### תחילה מזהים את הקבוצה הגבוהה
נגדיר H=OR_i h_i, ‏L=OR_i l_i, ‏T=OR_i(h_i AND l_i). אז y1=H ו־y0=T OR ((NOT H) AND L).

אם H=0, כל הערכים הם 0 או 1 והמקסימום הוא L. אם H=1 ויש T=1, מופיע 3 והוא הגדול ביותר. אם H=1 ו־T=0, מופיע לפחות 2 ואף 3, ולכן התוצאה 2. שלושת המקרים ממצים את כל האפשרויות. לדוגמה 01 ו־10 מפיקים 10; OR פשוט של כל המילים היה נותן בטעות 11. כפילויות ושוויון אינם דורשים טיפול נפרד.

בפריסה ישירה עם שערי OR דו־כניסתיים מאוזנים, כל הפחתה על 16 אותות דורשת 15 שערי OR בארבע רמות. שלוש ההפחתות דורשות 45 OR; זיהוי T מוסיף 16 AND. הסיום מוסיף NOT, ‏AND ו־OR. הספירה הכוללת היא 45 OR להפחתות ועוד OR מסיים, 17 AND ו־NOT אחד. עומק מרבי הוא שבע רמות שער במסלול H דרך NOT/AND/OR, לפי ספריית שערים אידאלית זו. ספריית תאים עם fan-in אחר או סינתזה עשויה לשנות זאת.

עץ של 15 תאי max זוגיים נותן ארבע רמות של תאים, אך כל תא כולל כמה רמות שער. לכן אין להשוות ארבע רמות תאים ישירות לשבע רמות שער. הנוסחה מנצלת את רוחב שתי הסיביות ומחזירה ערך בלבד, בלי מידע על מיקומו. לא נטען מינימום שטח פיזי.

```python
"""Parallel presence equations; no pairwise arithmetic comparison."""


def maximum16(words):
    if len(words) != 16 or any(type(x) is not int or not 0 <= x <= 3 for x in words):
        raise ValueError("sixteen unsigned two-bit words required")
    high = low = three = 0
    for word in words:
        h, l = (word >> 1) & 1, word & 1
        high |= h
        low |= l
        three |= h & l
    return (high << 1) | (three | ((1-high) & low))
```

## en

A 32-bit input consists of sixteen unsigned two-bit words x_i=(h_i,l_i). Use AND, OR and NOT gates to return the maximum value as two bits. No index is required. All words arrive in parallel. Give equations, a correctness argument and compare logical depth with a tree of pairwise comparators.

1. Only four word values exist, so detect the presence of each relevant category.
2. The high output bit says whether any word is at least two.
3. If any high word exists, the low bit depends on whether three exists. Otherwise it depends on whether one exists.

### Detect the highest present category
Define H=OR_i h_i, L=OR_i l_i and T=OR_i(h_i AND l_i). Then y1=H and y0=T OR ((NOT H) AND L).

If H=0, every word is zero or one, so L is the maximum. If H=1 and T=1, three occurs and is maximal. If H=1 and T=0, at least one two occurs and no three occurs, giving two. These cases exhaust all inputs. For words 01 and 10 the answer is 10; bitwise OR alone would incorrectly return 11. Repeated values need no special handling.

A direct realization with balanced two-input OR gates uses fifteen OR gates and four levels per sixteen-input reduction. Three reductions use forty-five OR gates; local T terms add sixteen AND gates. The final expression adds NOT, AND and OR, totaling forty-six OR, seventeen AND and one NOT in this explicit layout. The longest H path has seven gate levels through the final NOT/AND/OR. Different fan-in libraries and synthesis can change these numbers.

A tournament of fifteen pairwise-max cells has four cell layers, but each cell has several gate layers. Cell depth and gate depth must use the same metric before comparison. This specialization returns a two-bit value without its position. No physical area minimum is asserted.

```python
"""Parallel presence equations; no pairwise arithmetic comparison."""


def maximum16(words):
    if len(words) != 16 or any(type(x) is not int or not 0 <= x <= 3 for x in words):
        raise ValueError("sixteen unsigned two-bit words required")
    high = low = three = 0
    for word in words:
        h, l = (word >> 1) & 1, word & 1
        high |= h
        low |= l
        three |= h & l
    return (high << 1) | (three | ((1-high) & low))
```

[Executable model](../solutions/prep_340_hardware1115.py)
[Checks](../checks/check_hardware1115.py)
[Results](../checks/hardware1115-verification.json)

[Private source](../sources/2026-11-15-batch20-07.png)
[he diagram](../diagrams/prep-340-given-nov15-he.png)
[en diagram](../diagrams/prep-340-given-nov15-en.png)
[he diagram](../diagrams/prep-340-solution-nov15-he.png)
[en diagram](../diagrams/prep-340-solution-nov15-en.png)
