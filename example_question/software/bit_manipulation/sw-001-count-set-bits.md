# SW-001 — Count asserted status bits

**כותרת בעברית:** ספירת ביטים פעילים

| Field | Value |
|---|---|
| Category | software / תוכנה |
| Topic | Bit manipulation / פעולות על ביטים |
| Difficulty | 3/10 (provisional) |
| Estimated time | 8 minutes |
| Format | code |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Given a nonnegative integer x with at most 32 bits, count its 1 bits without a built-in population-count function or converting it to a string. Give code or pseudocode, explain why it terminates, and analyze complexity. Test x=0, x=0b10110100, and x=0xFFFFFFFF.

## שאלה — עברית

נתון מספר שלם לא שלילי x המיוצג לכל היותר ב־32 ביטים. ספרו את ביטי ה־1 ללא פונקציית population count מובנית וללא המרה למחרוזת. כתבו קוד או פסאודו־קוד, הסבירו מדוע הוא מסתיים ונתחו סיבוכיות. בדקו x=0, x=0b10110100, x=0xFFFFFFFF.

## Hint — English

Inspect how subtracting one changes the lowest set bit.

## רמז — עברית

בדקו כיצד חיסור אחד משנה את ביט ה־1 הנמוך ביותר.

## Reference solution — English

Repeatedly apply x = x & (x-1) while x!=0 and increment a counter. Each step clears the lowest set bit. Counts: 0,4,32. For word width W and k set bits, time O(k)<=O(W), extra space O(1); at fixed W=32 the worst case is bounded.

## כיוון פתרון — עברית

כל עוד x שונה מאפס מבצעים x = x & (x-1) ומגדילים מונה. כל צעד מנקה את ביט ה־1 הנמוך ביותר. התוצאות: 0,4,32. עבור רוחב מילה W ו־k ביטים פעילים, הזמן O(k)<=O(W) והזיכרון הנוסף O(1); ברוחב קבוע 32 מספר הצעדים חסום.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [Python documentation: integer and bitwise operations](https://docs.python.org/3/library/stdtypes.html)
