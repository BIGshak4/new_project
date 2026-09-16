# HW-016 — Request and acknowledgement controller

**כותרת בעברית:** בקר בקשה ואישור

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Finite state machines / מכונות מצבים |
| Difficulty | 4/10 (provisional) |
| Estimated time | 12 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

Design a Moore FSM with states IDLE, WAIT_ACK, DONE. In IDLE, a sampled start=1 enters WAIT_ACK. In WAIT_ACK, req=1 until a sampled ack=1 enters DONE. DONE asserts done=1 for one full cycle then returns to IDLE unconditionally. start outside IDLE and ack outside WAIT_ACK are ignored. Reset enters IDLE. Give outputs, transitions, and behavior if start remains high continuously.

## שאלה — עברית

תכננו Moore FSM עם המצבים IDLE, WAIT_ACK, DONE. ב־IDLE דגימת start=1 מעבירה ל־WAIT_ACK. ב־WAIT_ACK הפלט req=1 עד שדגימת ack=1 מעבירה ל־DONE. במצב DONE הפלט done=1 במשך מחזור שלם ואז חוזרים ל־IDLE ללא תנאי. מתעלמים מ־start מחוץ ל־IDLE ומ־ack מחוץ ל־WAIT_ACK. איפוס מעביר ל־IDLE. תנו פלטים, מעברים והתנהגות כאשר start נשאר גבוה ברציפות.

## Hint — English

Do not add an undocumented wait-for-start-to-fall state.

## רמז — עברית

אל תוסיפו מצב המתנה לירידת start שלא נדרש במפרט.

## Reference solution — English

Outputs (req,done): IDLE=(0,0), WAIT_ACK=(1,0), DONE=(0,1). Transitions follow the specified guards. A continuously high start launches another request at the next sampling edge in IDLE after DONE. This is a level-sensitive request interface, not a once-per-rising-edge interface.

## כיוון פתרון — עברית

הפלטים (req,done): במצב IDLE הם (0,0), ב־WAIT_ACK הם (1,0), וב־DONE הם (0,1). המעברים לפי התנאים שניתנו. start שנשאר גבוה מפעיל בקשה נוספת בחזית הדגימה הבאה ב־IDLE לאחר DONE. הממשק רגיש לרמה ואינו מבטיח בקשה יחידה לכל עלייה.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [MIT 6.111: sequential assignments and FSMs](https://classes.csail.mit.edu/6.111/f2006/handouts/L06.pdf)
