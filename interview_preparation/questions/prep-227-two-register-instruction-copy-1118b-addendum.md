# PREP-227 — העתקה בין שני רגיסטרים ללא רגיסטר נתונים נוסף

הצעה לפתרון. ביקורת מקצועית אנושית ממתינה.

## עברית

### הרחבה: העתקת ערך עם קבוצת פקודות מצומצמת
הציבו ב־R2 את הערך המקורי של R1 ושמרו את R1. תנו פתרון עם MOV, פתרון בלי MOV כאשר מותרות פעולות לוגיות, ולבסוף פתרון עם INC, DEC ו־JMPZ בלבד. להשלמת המפרט נשתמש בשני אוגרים בלבד ברוחב קבוע וידוע w≥1, שמכילים בתחילה ערכים כלשהם. הפקודה JMPZ R,label בודקת ישירות אם R שווה לאפס. אפשר לפרוס קוד לפי הרוחב הידוע. ציינו אם דרך חלופית דורשת אוגר עזר או פירוש אחר לקפיצה.

1. החליטו קודם אם צריך לשמר את המקור ומה בדיוק בודקת פקודת הקפיצה.
2. ל־w סיביות יש רק 2 בחזקת w ערכים. אפשר להקטין עד אפס ברצף פקודות שגודלו ידוע מראש.
3. כשהמקור מגיע לאפס, מיקום הפקודה יכול לזכור כמה פעמים הוקטן. קפצו לסיומת המגדילה את שני האוגרים בדיוק מספר זה של פעמים.

### שימור המקור באמצעות תוויות התוכנית

#### כיווני חשיבה להרחבה
1. החליטו קודם אם צריך לשמר את המקור ומה בדיוק בודקת פקודת הקפיצה.
2. ל־w סיביות יש רק 2 בחזקת w ערכים. אפשר להקטין עד אפס ברצף פקודות שגודלו ידוע מראש.
3. כשהמקור מגיע לאפס, מיקום הפקודה יכול לזכור כמה פעמים הוקטן. קפצו לסיומת המגדילה את שני האוגרים בדיוק מספר זה של פעמים.

נשתמש במוסכמת יעד תחילה. הפקודה הרגילה היא `MOV R2,R1`. ללא MOV אפשר לבצע `XOR R2,R2` ואחריה `OR R2,R1`. הראשונה מאפסת את היעד והשנייה מעתיקה אליו את סיביות המקור.

בגרסה המצומצמת נסמן `K=2^w−1`. פרסו K זוגות של בדיקת אפס ב־R2 ואחריה הקטנת R2. כל בדיקה קופצת לשלב הספירה אם היעד כבר אפס. אחרי הזוג האחרון גם הערך המרבי התאפס. כעת בודקים את R1. אם הוא אפס מסיימים. אחרת מקטינים, ובכל עותק של הבדיקה קופצים לתווית אחרת כאשר מגיעים לאפס. בתווית המתאימה ל־a הקטנות מתחילה סיומת עם a זוגות של `INC R1` ו־`INC R2`. במקרה המרבי מספיק ליפול ישירות לתוך הסיומת הארוכה. לדוגמה, זו התוכנית המלאה לשני ביטים.

```text
JMPZ R2, count
DEC R2
JMPZ R2, count
DEC R2
JMPZ R2, count
DEC R2
count:
JMPZ R1, end
DEC R1
JMPZ R1, one
DEC R1
JMPZ R1, two
DEC R1
three:
INC R1
INC R2
two:
INC R1
INC R2
one:
INC R1
INC R2
end:
```

אם בתחילה R1=2,R2=3, היעד מתאפס לאחר שלוש הקטנות. המקור מגיע לאפס לאחר שתיים. הקפיצה ל־two מפעילה שני זוגות הגדלות ומסיימת עם 2 בשני האוגרים. אין איפוס מתחת לאפס או גלישה, כולל בקלט אפס ובקלט מרבי. מונה התוכנית מובנה במעבד ומיקום התווית נושא את המידע הזמני. המחיר הוא סדר גודל של 2 בחזקת w בגודל הקוד ובזמן המקרה הגרוע. זהו מימוש אפשרי במפרט שנבחר, ללא טענת אופטימליות. במעבד עם דגל אפס של הפקודה האחרונה וחשבון מודולרי ברוחב w, החליפו כל בדיקת אוגר ב־INC R, אחריה DEC R ואחריה JMPZ label. שתי הפעולות משחזרות את הערך והדגל האחרון מעיד אם ערכו המקורי אפס. לולאה שמקטינה את המקור ומגדילה את היעד בלבד צורכת את המקור.


## English

### Follow-up: Copying a value under an instruction constraint
Assign the original R1 value to R2 while preserving R1. Give a solution with MOV, one without MOV when logic instructions are available, and one using only INC, DEC and JMPZ. For a precise contract use just two registers of known fixed width w≥1, initially arbitrary. JMPZ R,label directly tests whether R is zero. The code may be expanded at assembly time for that fixed width. State any scratch-register or branch-semantics assumptions in an alternative.

1. Decide whether the source survives and what the branch actually tests.
2. A w-bit register has only 2 to the power w possible values. An unrolled sequence can decrement it until zero.
3. When the source reaches zero, the instruction address can encode how many decrements occurred. Branch into a suffix with that many increments of both registers.

### Preserving the source using instruction labels

#### Hints for the follow-up
1. Decide whether the source survives and what the branch actually tests.
2. A w-bit register has only 2 to the power w possible values. An unrolled sequence can decrement it until zero.
3. When the source reaches zero, the instruction address can encode how many decrements occurred. Branch into a suffix with that many increments of both registers.

Using destination-first notation the usual instruction is `MOV R2,R1`. With logic instructions use `XOR R2,R2` followed by `OR R2,R1`. The first clears the destination and the second copies the source bits into it.

For the restricted machine put `K=2^w−1`. Emit K pairs testing R2 for zero then decrementing it. Each test branches to the counting stage if R2 is already zero. Even the maximum destination reaches zero after the last pair. Now test R1. Finish immediately if it is zero. Otherwise decrement it, and at each unrolled zero test branch to a different label when it reaches zero. The label for a decrements starts a suffix containing a pairs of `INC R1` and `INC R2`. The maximum case falls straight into the longest suffix. Here is the full program for two bits.

```text
JMPZ R2, count
DEC R2
JMPZ R2, count
DEC R2
JMPZ R2, count
DEC R2
count:
JMPZ R1, end
DEC R1
JMPZ R1, one
DEC R1
JMPZ R1, two
DEC R1
three:
INC R1
INC R2
two:
INC R1
INC R2
one:
INC R1
INC R2
end:
```

Starting with R1=2,R2=3, three decrements clear the destination. Two decrements clear the source and the branch to two executes precisely two increment pairs, leaving both registers equal to 2. Neither underflow nor overflow occurs, even for zero and maximum initial values. The existing program counter temporarily records the count in the instruction address. Code size and worst-case execution time are both on the order of 2 to the power w. This is one valid implementation for the stated instruction model. If JMPZ reads only the last arithmetic zero flag and arithmetic wraps modulo 2^w, replace every register test by INC R, DEC R, JMPZ label. The pair restores R, and the final flag indicates whether the original value was zero. A loop that only decrements the source and increments the destination consumes the source.


[צילום מקור פנימי 20](../sources/2026-11-18-batch21-20.png)
[קובץ המימוש](../solutions/digital1118b_models.py)
[תוצאות בדיקות](../checks/digital1118b-verification.json)
