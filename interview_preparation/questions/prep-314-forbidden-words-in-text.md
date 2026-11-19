# PREP-314 — האם הטקסט נקי ממילים אסורות?

פתרון מוצע בסיוע AI. ממתין לביקורת מקצועית אנושית.

[צילום המקור](../sources/2026-11-14-batch30-15.png)

נתון לך מחסן מילים ואתה צריך באמצעות פונקציות של STRING לוודא שבמחרוזת שנתונה לך לא מופיעה אף אחת מהמילים הנ״ל.

## האם הטקסט נקי ממילים אסורות?

כתבו contains_no_forbidden_words(text, forbidden). הטקסט מכיל מילים המופרדות ברווח לבן, והמילון מכיל מילים שלמות ולא ריקות ללא רווחים. החזירו true אם אף מילה במילון אינה מופיעה כמילה שלמה בטקסט. ההשוואה רגישה לרישיות, וסימני פיסוק שייכים למילה שבה הם מופיעים. מותר להשתמש בפעולות מחרוזת ובקבוצת גיבוב.

### רמזים

1. מה צריכה להיות התוצאה עבור cat בטקסט scatter?
2. כיצד תפרידו את הטקסט למילים כאשר יש שני רווחים רצופים או טאב?
3. הכינו קבוצת חיפוש מהמילון. די בהתאמה אחת כדי להחזיר false.

### פתרון מוצע

בונים קבוצה מהמילים האסורות ומפצלים את הטקסט בנקודות שבהן מופיע רווח לבן. ב־Python הקריאה split() ללא פרמטר מסירה רווח לבן מהקצוות ומטפלת ברצפי מפרידים. משווים כל מילה שלמה לקבוצה. התאמה אחת מספיקה להחזרת false; אם עברנו על כל המילים, מחזירים true.

למשל, עם {"cat"}, הטקסט "scatter Cat" עובר ואילו "scatter cat" נכשל. לפני כל בדיקה כל המילים הקודמות עברו, ולכן סיום הלולאה בלי התאמה מוכיח את התנאי לכל הטקסט. אם הדרישה היא חלק ממילה, התוצאה עבור "scatter" משתנה ודרוש חוזה אחר.

```python
def contains_no_forbidden_words(text, forbidden):
    """Compare complete, case-sensitive tokens separated by whitespace."""
    vocabulary = set(forbidden)
    return all(word not in vocabulary for word in text.split())
```

### הנחות

התאמה מדויקת בין אסימונים, עם מפרידי רווח לבן וללא נרמול אותיות או פיסוק.

### מקרה קצה

טקסט ריק, טקסט של רווחים בלבד או מילון ריק עוברים. cat, עם פסיק היא מילה שונה מ־cat לפי החוזה.

### טעות נפוצה

חיפוש תת־מחרוזת יסמן גם scatter, ושימוש בפיצול רק לפי רווח רגיל יחמיץ טאבים.

### סיבוכיות או עלות

בתוחלת O(T+D) זמן, כאשר T ו־D הם מספרי התווים בטקסט ובמילון במודל גיבוב מקובל. הקבוצה והמילים שמחזירה split תופסות O(T+D) זיכרון.

### בדיקות

דוגמאות הכוללות טאבים, פיסוק, רישיות וקלט ריק, והשוואה מול חיפוש לינארי נפרד במילון.

### תשובה קצרה

אחפש כל אסימון שלם בקבוצת המילים האסורות ואפסיק ברגע שיש התאמה.

### שאלת המשך

איך חוסכים את רשימת המילים המפוצלת בטקסט גדול? קוראים תו אחר תו, צוברים רק את המילה הנוכחית ומשווים כשהיא מסתיימת, כולל המילה האחרונה.

## Does the text contain any forbidden word?

Write contains_no_forbidden_words(text, forbidden). Whitespace separates words in the text. The dictionary contains nonempty, whitespace-free words. Return true if no complete token in the text equals a dictionary word. Comparisons are case-sensitive and punctuation stays attached to a token. String operations and a hash set are allowed.

### Hints

1. Should cat match the text scatter?
2. How will you recognize words across consecutive spaces or a tab?
3. Build a lookup set from the dictionary. One match suffices to return false.

### Proposed solution

Build a set of forbidden words and split the text at whitespace. In Python, split() without an argument handles runs of whitespace and ignores leading and trailing whitespace. Test each complete token for set membership. Return false on the first match and true after all tokens have passed.

With {"cat"}, "scatter Cat" passes and "scatter cat" fails. Before each check all preceding tokens were allowed. Reaching the end therefore proves that every token is allowed. A substring interpretation would change the outcome for "scatter" and is a different contract.

```python
def contains_no_forbidden_words(text, forbidden):
    """Compare complete, case-sensitive tokens separated by whitespace."""
    vocabulary = set(forbidden)
    return all(word not in vocabulary for word in text.split())
```

### Assumptions

Exact token matching, whitespace separators, and no case or punctuation normalization.

### Edge case

Empty text, whitespace-only text and an empty dictionary pass. The comma makes cat, different from cat.

### Common mistake

Substring search also matches scatter. Splitting on literal spaces alone misses tabs.

### Cost

Expected O(T+D) time for T text and D dictionary characters under ordinary hashing assumptions. The set and the list returned by split use O(T+D) space.

### Verification

Checks include tabs, punctuation, case and empty input; a separate linear dictionary scan supplies expected decisions.

### Interview answer

I check each complete token against a hash set and stop on the first match.

### Follow-up

How can a large text be processed without a token list? Read one character at a time. Buffer and test each current token at a boundary, including the last token.

[checks/check_nov14_reasoning_software.py](../checks/check_nov14_reasoning_software.py)

[checks/prep-314-1114-verification.json](../checks/prep-314-1114-verification.json)

[solutions/prep_314_forbidden_words.py](../solutions/prep_314_forbidden_words.py)
