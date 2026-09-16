# HW-002 — Enable logic using only NAND gates

**כותרת בעברית:** לוגיקת הפעלה באמצעות שערי NAND בלבד

| Field | Value |
|---|---|
| Category | hardware / חומרה |
| Topic | Boolean logic / אלגברה בוליאנית |
| Difficulty | 3/10 (provisional) |
| Estimated time | 8 minutes |
| Format | construct |
| Modes | deep, simulation |
| Status | In review; not published or independently expert-reviewed |
| Company attribution | None; not claimed to be asked by a particular employer |

## Question — English

A device runs when enable E is 1 and at least one request A or B is 1: Y = E & (A | B). Implement Y using only two-input NAND gates, with no free inverted inputs. Provide a gate-by-gate description and verify the cases E=0 and A=B=0. Minimum gate count is not required.

## שאלה — עברית

התקן פועל כאשר אות ההפעלה E הוא 1 ולפחות אחת מהבקשות A או B היא 1: Y = E & (A | B). ממשו את Y באמצעות שערי NAND בעלי שני קלטים בלבד, ללא קלטים מהופכים זמינים מראש. תארו את השערים ובדקו את המצבים E=0 וכן A=B=0. אין צורך להוכיח מספר שערים מינימלי.

## Hint — English

A NAND gate with both inputs tied together acts as an inverter.

## רמז — עברית

שער NAND ששני קלטיו מחוברים לאותו אות פועל כמהפך.

## Reference solution — English

One five-gate implementation is nA=NAND(A,A), nB=NAND(B,B), R=NAND(nA,nB), nY=NAND(E,R), Y=NAND(nY,nY). R implements A OR B by De Morgan. Either disabled E or no requests forces Y=0.

## כיוון פתרון — עברית

מימוש אפשרי בחמישה שערים: nA=NAND(A,A), nB=NAND(B,B), R=NAND(nA,nB), nY=NAND(E,R), Y=NAND(nY,nY). לפי דה־מורגן R מממש OR. אם E אינו פעיל או שאין בקשות, מתקבל Y=0.

## Sources and provenance / מקורות

Independently authored interview-style exercise using standard concepts. Sources provide technical background; this is not a copied or translated source question. Human technical and translation review is pending.

- [HDLBits: digital logic topic catalog](https://hdlbits.01xz.net/wiki/Problem_sets)
