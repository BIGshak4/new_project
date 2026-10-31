"""50 short hardware objectives and 250 draft, source-linked quiz cases.

This bounded author model is replayed independently by
test_fundamentals_hardware_500.py. It is not HDL, SPICE or timing signoff.
No existing card, quiz approval or learner history is edited here.
"""
from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "apps/web/src/content"
OUT = ROOT / "backend/seeds/duel_quiz_batches"
CARDS, QUESTIONS, CHECKS = [], [], []


def loc(he, en):
    return {"he": he, "en": en}


def params(names, rows):
    return [dict(zip(names.split(), row, strict=True)) for row in rows]


def model(n, p):
    match n:
        case 201:
            return ((p['x'] >> p['k']) | (p['x'] << (p['w'] - p['k']))) & ((1 << p['w']) - 1)
        case 202:
            return (p['a'] + p['b']) % p['w']
        case 203:
            return p['w'] * (p['w'].bit_length() - 1)
        case 204:
            return p['x'].bit_count()
        case 205:
            return (p['j'] + p['k']) % p['w']
        case 206:
            return p['d'][2 * p['s1'] + p['s0']]
        case 207:
            return abs(p['s0_time'] - p['s1_time'])
        case 208:
            return [int(p['vdd'] - p['gate'] > p['vtp']), int(p['gate'] > p['vtn'])]
        case 209:
            n_on, p_on = bool(p['ng']), not p['pg']
            if not (n_on or p_on):
                return 'Z'
            if p['data']:
                return 1 if p_on else 0.7
            return 0 if n_on else 0.3
        case 210:
            return p['c'] * p['v'] ** 2
        case 211:
            return len(p['en']) * 6 // math.gcd(sum(p['en']), 6)
        case 212:
            return 0 if p['q'] >= 6 else (p['q'] + p['en']) % 6
        case 213:
            return (p['start'] + sum(p['en'])) // 6
        case 214:
            return sum(a and not b for a, b in zip(p['clk'], [0, *p['clk'][:-1]], strict=True))
        case 215:
            return 2 * p['period']
        case 216:
            return p['ripple'] * p['tcq']
        case 217:
            return p['detect'] + 1
        case 218:
            return next(''.join(bits) for length in range(1, 5)
                        for bits in itertools.product('01', repeat=length)
                        if (p['a'] + ''.join(bits)).endswith('1101') != (p['b'] + ''.join(bits)).endswith('1101'))
        case 219:
            pattern = p['pattern']
            return next(shift for shift in range(1, len(pattern) + 1) if pattern[shift:] == pattern[:len(pattern) - shift])
        case 220:
            history, pulses = '', []
            for cycle, (valid, bit) in enumerate(p['samples'], 1):
                if valid:
                    history += str(bit)
                    if history.endswith('0101'):
                        pulses.append(cycle)
            return pulses
        case 221:
            return sum(p['valid'])
        case 222:
            streak = 0
            for v, word in p['samples']:
                if v:
                    streak = streak + 1 if word == p['ref'] else 0
            return streak
        case 223:
            return sum(v and word in p['refs'] for v, word in p['samples'])
        case 224:
            return sorted(set(p['accepted'][:p['cut']]) - set(p['done']))
        case 225:
            return max(p['times'][tag] for tag in p['snapshot'])
        case 226:
            return sum(tag in p['snapshot'] for tag in p['done'])
        case 227:
            return sum(p['end'] - start for start in p['arrivals'])
        case 228:
            return sum(end - start for start, end in p['pairs']) // len(p['pairs'])
        case 229:
            return sum(p['sums']) // sum(p['counts'])
        case 230:
            return p['memory'][p['sampled_addr']]
        case 231:
            return [p['old'] if not p['en'] else p['read'], p['en']]
        case 232:
            return p['old'] if p['policy'] == 'read-first' else p['new']
        case 233:
            return 4 * p['w'] + p['w'] * p['registered']
        case 234:
            return (1 << p['addr']) if p['en'] else 0
        case 235:
            return ((p['release'] + p['recovery'] + p['period'] - 1) // p['period']) * p['period']
        case 236:
            upper = (p['a'] >> 2) + (p['b'] >> 2) + int((p['a'] & 3) + (p['b'] & 3) >= 4)
            return [upper & 3, upper >> 2]
        case 237:
            return [int((p['a'] ^ p['b']) == (1 << p['w']) - 1), (p['a'] + p['b']) >> p['w']]
        case 238:
            return ((1 << p['a']) + (1 << p['b']) - 2).bit_length()
        case 239:
            return (p['a'] + p['b'] + 1) // 2
        case 240:
            s = p['a'] + p['b']
            return s // 2 + int(s % 2 and (s // 2) % 2)
        case 241:
            return (3 * p['digit']) % 10
        case 242:
            return (3 * p['digit']) // 10
        case 243:
            return {'excluded': 6, 'lowest_invalid': 10, 'highest_valid': 9, 'defined_rows': 10, 'output_max': 27}[p['query']]
        case 244:
            return p['x'].bit_length() - 1
        case 245:
            return (p['w'] - 1).bit_length()
        case 246:
            return (2 * p['r'] + p['bit']) // 5
        case 247:
            return p['bits_value'] // 5
        case 248:
            return (p['divisor'] - 1).bit_length()
        case 249:
            end = -1
            pulses = 0
            for trigger in p['triggers']:
                if trigger >= end:
                    pulses += 1
                    end = trigger + p['width']
            return pulses
        case 250:
            return p['triggers'][-1] + p['width']
    raise ValueError(n)


def question(n, p):
    match n:
        case 201:
            return loc(f"מסובבים את המילה הבלתי מסומנת {p['x']:0{p['w']}b} ברוחב {p['w']} ימינה ב־{p['k']} מקומות, באופן מעגלי. מה ערך הפלט העשרוני?",
                       f"Rotate unsigned {p['x']:0{p['w']}b}, width {p['w']}, right by {p['k']} positions cyclically. What is the decimal output?")
        case 202:
            return loc(f"על מילה ברוחב {p['w']} מבצעים סיבוב מעגלי ימינה ב־{p['a']} ואז ב־{p['b']}. לאיזה סיבוב יחיד ימינה זה שקול, בתחום 0 עד {p['w'] - 1}?",
                       f"A width-{p['w']} word is rotated cyclically right by {p['a']}, then {p['b']}. What single right-rotation amount in 0 through {p['w'] - 1} is equivalent?")
        case 203:
            return loc(f"מסובב מעגלי ברוחב {p['w']}, חזקה של 2, בנוי בשלבי סיבוב מותנה 1,2 וכן הלאה עד {p['w'] // 2}. בכל שלב MUX של ביט אחד לכל ביט. כמה רכיבי MUX 2:1 יש בסך הכול?",
                       f"A width-{p['w']} cyclic rotator, a power of 2, uses conditional rotation stages 1,2 and so on through {p['w'] // 2}. Each stage has one single-bit MUX per bit. How many 2:1 MUXes are used in total?")
        case 204:
            return loc(f"מילה בת {p['w']} ביטים היא {p['x']:0{p['w']}b}. מסובבים אותה מעגלית בכל כמות חוקית. כמה ביטי 1 יהיו בפלט, בלי לדעת את כמות הסיבוב?",
                       f"A {p['w']}-bit word is {p['x']:0{p['w']}b}. It is cyclically rotated by any legal amount. How many output bits are 1, regardless of the rotation amount?")
        case 205:
            return loc(f"במסובב מעגלי ימינה ברוחב {p['w']} ובכמות {p['k']}, איזה אינדקס קלט מזין את ביט הפלט {p['j']}? ביט 0 הוא LSB.",
                       f"For width-{p['w']} cyclic right rotation by {p['k']}, which input index feeds output bit {p['j']}? Bit 0 is the LSB.")
        case 206:
            return loc(f"MUX 4:1 משתמש ב־S1 כסיבית הבחירה הגבוהה וב־S0 כנמוכה. הנתונים D0..D3 הם {p['d']}; S1={p['s1']}, S0={p['s0']}. מה הפלט?",
                       f"A 4:1 MUX uses S1 as the high select bit and S0 as the low bit. D0..D3 are {p['d']}; S1={p['s1']}, S0={p['s0']}. What is its output?")
        case 207:
            return loc(f"MUX 4:1 אידאלי ללא השהיה מחזיק D0..D3=[0,1,1,0]. הבחירה משתנה מ־00 ל־11: S0 עולה בזמן {p['s0_time']} ns ו־S1 בזמן {p['s1_time']} ns. לכמה ns הפלט יהיה 1 בין שני מצבי הקצה?",
                       f"An ideal zero-delay 4:1 MUX holds D0..D3=[0,1,1,0]. Selection changes from 00 to 11: S0 rises at {p['s0_time']} ns and S1 at {p['s1_time']} ns. For how many ns is output 1 between the endpoint states?")
        case 208:
            return loc(f"במודל סף למהפך CMOS, VDD={p['vdd']} V ומתח שני השערים {p['gate']} V. ספי ההולכה הם Vtn={p['vtn']} V ו־|Vtp|={p['vtp']} V. הולכה דורשת מתח שער־מקור שעובר ממש את הסף המתאים. מה [PMOS מוליך,NMOS מוליך], בביטי 0/1?",
                       f"In a CMOS inverter threshold model, VDD={p['vdd']} V and both gates are at {p['gate']} V. Thresholds are Vtn={p['vtn']} V and |Vtp|={p['vtp']} V. Conduction requires gate-source magnitude strictly beyond the relevant threshold. What is [PMOS on,NMOS on] as 0/1 bits?")
        case 209:
            return loc(f"NMOS ו־PMOS במקביל מעבירים נתון {p['data']} V. מתחי הבקרה הם NG={p['ng']} V, PG={p['pg']} V; המסילה 1 V וסף כל רכיב 0.3 V. במודל מעבר סטטי ללא גוף או עומס, NMOS מעביר גבוה עד 0.7 ו־PMOS נמוך עד 0.3. מה הפלט, או Z כששניהם מנותקים?",
                       f"Parallel NMOS and PMOS pass {p['data']} V. Controls: NG={p['ng']} V, PG={p['pg']} V; rail 1 V, thresholds 0.3 V. In a static model without body effect or load, NMOS passes high to 0.7 and PMOS low to 0.3. What is output, or Z if both disconnect?")
        case 210:
            return loc(f"מהפך אידאלי טוען עומס {p['c']} pF מ־0 ל־VDD={p['v']} V פעם אחת. כמה pJ מספק מקור המתח? אין זרם קצר או דליפה.",
                       f"An ideal inverter charges a {p['c']} pF load from 0 to VDD={p['v']} V once. How many pJ does the supply deliver? Ignore short-circuit and leakage currents.")
        case 211:
            return loc(f"מונה מודולו 6 מתחיל ב־0. תבנית EN={p['en']} חוזרת לנצח, ומתקדמים רק עם EN=1. אחרי כמה מחזורי שעון לראשונה גם המונה חוזר ל־0 וגם מסתיימת תבנית EN שלמה?",
                       f"A modulo-6 counter starts at 0. EN pattern {p['en']} repeats forever; advance only with EN=1. After how many clock cycles do both counter=0 and the end of a whole EN pattern first recur together?")
        case 212:
            return loc(f"מונה 3 ביטים מודולו 6 מוגדר כך: מצב לא חוקי 6 או 7 חוזר ל־0 בחזית הבאה, בלי קשר ל־EN. מצב חוקי מתקדם רק עם EN. כעת Q={p['q']}, EN={p['en']}. מה Q הבא?",
                       f"A 3-bit modulo-6 counter recovers from invalid state 6 or 7 to 0 at the next edge regardless of EN. Legal states advance only with EN. Now Q={p['q']}, EN={p['en']}. What is next Q?")
        case 213:
            return loc(f"מונה מודולו 6 מתחיל ב־{p['start']}; פולס wrap מופק רק בחזית מתקבלת המעבירה 5 ל־0. עבור EN={p['en']}, כמה פולסי wrap יופקו?",
                       f"A modulo-6 counter starts at {p['start']}; a wrap pulse occurs only on an enabled edge taking 5 to 0. For EN={p['en']}, how many wrap pulses occur?")
        case 214:
            return loc(f"בבדיקת שעון מגודר, רמות clk AND EN שנמדדו בזמנים עוקבים הן {p['clk']}, והרמה לפני המדגם הראשון היא 0. כמה חזיתות עלייה רואה הרכיב? שינוי EN בזמן clk גבוה עשוי ליצור חזית נוספת.",
                       f"In a gated-clock check, successive measured levels of clk AND EN are {p['clk']}, with initial level 0. How many rising edges does the component see? Changing EN while clk is high can create an extra edge.")
        case 215:
            return loc(f"שני TFF בטור מחלקים שעון בעל מחזור {p['period']} ns ב־4. במצב מחזורי יציב, כמה ns נמשכת הרמה הגבוהה של היציאה הסופית, בהנחת רכיבים אידאליים?",
                       f"Two cascaded TFFs divide a clock of period {p['period']} ns by 4. In steady periodic operation, how many ns is the final output high, assuming ideal devices?")
        case 216:
            return loc(f"במונה ripple נתיב המעבר האחרון עובר דרך {p['ripple']} רכיבי FF בזה אחר זה, עם clk-to-Q של {p['tcq']} ns לכל אחד וללא השהיות אחרות. מה השהיית הנתיב ב־ns?",
                       f"A ripple-counter transition reaches the last output through {p['ripple']} consecutive FFs, each with clk-to-Q {p['tcq']} ns and no other delays. What is the path delay in ns?")
        case 217:
            return loc(f"ביט אחרון של רצף נקלט בחזית שמספרה {p['detect']}. פלט Mealy המחושב אחריה נדגם ב־FF נוסף בחזית הבאה. באיזו חזית מתחיל הפולס הרשום? אין מסלול עוקף.",
                       f"A pattern's last bit is captured at edge {p['detect']}. Its post-edge Mealy output is captured by an extra FF at the next edge. At which edge does the registered pulse begin? No bypass exists.")
        case 218:
            return loc(f"בשני מצבי גלאי 1101, ההיסטוריות הן {p['a'] or 'ריקה'} ו־{p['b'] or 'ריקה'}. איזה המשך לא ריק וקצר ביותר ייתן זיהוי בסופו בדיוק באחד המצבים? אם יש תיקו, בוחרים לקסיקוגרפית עם 0 לפני 1.",
                       f"Two 1101-detector states have histories {p['a'] or 'empty'} and {p['b'] or 'empty'}. Which shortest nonempty continuation gives a detection at its final bit from exactly one state? Break ties lexicographically, with 0 before 1.")
        case 219:
            return loc(f"גלאי חופף מזהה את הרצף {p['pattern']}. מה מספר מחזורי השעון המזערי האפשרי בין סיומי שתי הופעות שונות? כל מחזור מקבלים ביט אחד ואין הפסקות קבלה.",
                       f"An overlapping detector recognizes {p['pattern']}. What is the minimum possible clock-cycle gap between the ends of two distinct occurrences? Accept one bit per cycle without pauses.")
        case 220:
            return loc(f"גלאי חופף 0101 מקבל מדגמי [Valid,ביט]: {p['samples']}. במחזור לא תקף המצב מוחזק והפלט 0. באילו מחזורי שעון פיזיים, ממוספרים מ־1, יופק פולס? המצב בתחילה ריק.",
                       f"An overlapping 0101 detector receives [Valid,bit] samples: {p['samples']}. On invalid cycles state holds and output is 0. At which physical clock cycles, numbered from 1, does a pulse occur? Start with empty history.")
        case 221:
            return loc(f"קורא טביעות אצבע מקבל אותו ערך שוב ושוב. Valid לאורך {len(p['valid'])} מחזורים הוא {p['valid']}. בכל Valid=1 מתקבלת דגימה חדשה, גם ללא שינוי בנתון. כמה דגימות התקבלו?",
                       f"A fingerprint reader presents the same value repeatedly. Valid over {len(p['valid'])} cycles is {p['valid']}. Each Valid=1 accepts a new sample even without a data change. How many samples are accepted?")
        case 222:
            return loc(f"מונה רצף התאמות מתחיל ב־0, מול ערך שמור {p['ref']}. מדגמים [Valid,נתון] הם {p['samples']}. אי־התאמה תקפה מאפסת; Valid=0 מקפיא. מה המונה בסוף?",
                       f"A matching-streak counter starts at 0 with reference {p['ref']}. Samples [Valid,data] are {p['samples']}. A valid mismatch resets; Valid=0 holds. What is the final count?")
        case 223:
            return loc(f"שני ערכים שמורים הם {p['refs']}. מדגמים [Valid,נתון] הם {p['samples']}. משווים לשניהם במקביל, ומקבלים הצלחה אם לפחות השוואה אחת שווה. כמה הצלחות תקפות יש?",
                       f"Two stored references are {p['refs']}. Samples [Valid,data] are {p['samples']}. Compare both in parallel and accept a match if either equals the sample. How many valid matches occur?")
        case 224:
            return loc(f"משימות התקבלו לפי הסדר {p['accepted']}. לחיצת snapshot הייתה אחרי {p['cut']} הקבלות. המשימות שהושלמו הן {p['done']}. אילו תגיות מה־snapshot עדיין חסרות, בסדר עולה? התגיות ייחודיות.",
                       f"Tasks were accepted in order {p['accepted']}. A snapshot was taken after {p['cut']} acceptances. Completed tasks are {p['done']}. Which snapshot tags are still missing, sorted ascending? Tags are unique.")
        case 225:
            return loc(f"צילום משימות מכיל תגיות {p['snapshot']}; זמני השלמה מוחלטים הם {p['times']}. ניתן להשלים שלא לפי סדר. מה הזמן המוקדם ביותר שבו כל הצילום הושלם?",
                       f"A task snapshot contains tags {p['snapshot']}; absolute completion times are {p['times']}. Completion may be out of order. What is the earliest time when the entire snapshot is complete?")
        case 226:
            return loc(f"ממתינים לצילום תגיות {p['snapshot']}. התקבלו ACK להשלמה עבור תגיות שונות {p['done']}. כל ACK מציין משימה שהושלמה, אבל חלקן מאוחרות מהצילום. כמה ACK רלוונטיים לצילום?",
                       f"A barrier waits for snapshot tags {p['snapshot']}. Completion ACKs arrived for distinct tags {p['done']}. Some tasks were accepted after the snapshot. How many ACKs are relevant to this barrier?")
        case 227:
            return loc(f"חבילות נכנסו בזמנים {p['arrivals']} וכולן עדיין בפנים בזמן {p['end']}. בכמה יחידות חבילה־זמן הן תרמו עד עכשיו לאינטגרל התפוסה?",
                       f"Packets arrived at times {p['arrivals']} and all remain inside at time {p['end']}. How many packet-time units have they contributed so far to the occupancy integral?")
        case 228:
            return loc(f"רק החבילות שהושלמו נכללות בממוצע. זוגות [כניסה,יציאה] שלהן הם {p['pairs']}. מה זמן השהייה הממוצע? חבילות פעילות אינן כלולות. התוצאה שלמה.",
                       f"Only completed packets enter this mean. Their [arrival,departure] pairs are {p['pairs']}. What is mean residence time? Active packets are excluded. The result is an integer.")
        case 229:
            return loc(f"בשני פורטים סכומי זמני השהייה הם {p['sums']} ומספרי החבילות שהושלמו הם {p['counts']}. מה הממוצע הכולל לכל חבילה? התוצאה שלמה.",
                       f"Two ports have residence-time sums {p['sums']} and completed-packet counts {p['counts']}. What is the overall mean per packet? The result is an integer.")
        case 230:
            return loc(f"זיכרון סינכרוני מכיל בכתובות 0..3 את {p['memory']}. בחזית קריאה נדגמה כתובת {p['sampled_addr']}, ומיד אחריה הכתובת השתנתה ל־{p['later_addr']}. מה הנתון שנלכד ביציאה באותה חזית? אין כתיבה.",
                       f"A synchronous memory holds {p['memory']} at addresses 0..3. A read edge samples address {p['sampled_addr']}; just afterward the address changes to {p['later_addr']}. Which value was captured at that edge? No write occurs.")
        case 231:
            return loc(f"בזיכרון סינכרוני read_data הישן הוא {p['old']}. כש־re_en=0 היציאה מחזיקה ערך ו־Valid=0; כש־re_en=1 נלכד {p['read']} ו־Valid=1. כעת re_en={p['en']}. מה [read_data,Valid] אחרי החזית?",
                       f"A synchronous memory's old read_data is {p['old']}. With re_en=0 it holds data and sets Valid=0; with re_en=1 it captures {p['read']} and sets Valid=1. Now re_en={p['en']}. What is [read_data,Valid] after the edge?")
        case 232:
            return loc(f"אותה כתובת נקראת ונכתבת באותה חזית. ערכה הישן {p['old']}, והכתיבה מכניסה {p['new']}. המדיניות המפורשת היא {p['policy']}. מה נתון הקריאה? read-first מחזיר ישן, write-first מחזיר חדש.",
                       f"The same address is read and written at one edge. Its old value is {p['old']} and the new write is {p['new']}. The explicit policy is {p['policy']}. What is read? Read-first returns old; write-first returns new.")
        case 233:
            return loc(f"בונים ארבע מילות זיכרון ברוחב {p['w']} ביטים. בנוסף, מספר רגיסטרי היציאה ברוחב מילה הוא {p['registered']}. מתעלמים מ־Valid ובקרה. כמה FF לאחסון נתונים דרושים?",
                       f"Build four memory words, each {p['w']} bits wide, plus {p['registered']} word-wide output registers. Ignore Valid and control. How many data-storage FFs are required?")
        case 234:
            return loc(f"בזיכרון בן ארבע כתובות, wr_addr={p['addr']} ו־wr_en={p['en']}. מה ערכה העשרוני של מסכת ה־enable בת 4 ביטים, כשביט i מפעיל כתובת i?",
                       f"In a four-address memory, wr_addr={p['addr']} and wr_en={p['en']}. What is the decimal 4-bit enable mask, where bit i enables address i?")
        case 235:
            return loc(f"FF דורש ששחרור איפוס יקדים חזית פעילה בלפחות {p['recovery']} ns, כולל שוויון. חזיתות באות בכפולות של {p['period']} ns, והאיפוס משתחרר בזמן {p['release']} ns. מה החזית הראשונה שמקיימת את חוזה ה־recovery? מתעלמים מ־removal.",
                       f"An FF requires reset release at least {p['recovery']} ns before an active edge, equality allowed. Edges occur at multiples of {p['period']} ns; reset releases at {p['release']} ns. What is the first edge satisfying recovery? Ignore removal.")
        case 236:
            return loc(f"מחבר carry-select מחבר A={p['a']} ו־B={p['b']}, כל אחד 4 ביטים. מחלקים לשתי קבוצות של 2 ביטים, עם carry-in כללי אפס. הקבוצה הגבוהה מחשבת מראש עם נשא 0 ועם 1. מה [שני ביטי סכום גבוהים כערך עשרוני,נשא סופי] אחרי בחירה לפי הקבוצה הנמוכה?",
                       f"A carry-select adder adds 4-bit A={p['a']} and B={p['b']} in two 2-bit groups, with initial carry-in zero. The high group precomputes carry-in 0 and 1. What is [high two sum bits as decimal,final carry] after selection by the low group?")
        case 237:
            return loc(f"מחברים מילים ברוחב {p['w']}: A={p['a']}, B={p['b']}. מגדירים G כנשא החוצה עם carry-in=0, ו־P=1 רק אם הנשיאה החוצה שווה ל־carry-in עבור שתי אפשרויותיו. מה [P,G] של כל הקבוצה?",
                       f"Add width-{p['w']} words A={p['a']} and B={p['b']}. G is carry-out with carry-in=0; P=1 only if carry-out equals carry-in for both possible inputs. What is the whole group's [P,G]?")
        case 238:
            return loc(f"מחברים מספר בלתי מסומן בן {p['a']} ביטים למספר בלתי מסומן בן {p['b']} ביטים. מה רוחב הפלט המזערי ששומר כל סכום אפשרי ללא גלישה?",
                       f"Add an unsigned {p['a']}-bit number to an unsigned {p['b']}-bit number. What minimum output width preserves every possible sum without overflow?")
        case 239:
            return loc(f"מחשבים ממוצע של מספרים בלתי מסומנים A={p['a']}, B={p['b']}, עם חיבור ברוחב מספיק. נדרש עיגול כלפי מעלה. מה הפלט השלם?",
                       f"Average unsigned A={p['a']} and B={p['b']} using a sufficiently wide sum. Round upward. What integer is output?")
        case 240:
            return loc(f"ממוצע A={p['a']}, B={p['b']} מעוגל לשלם הקרוב; בדיוק בחצי בוחרים שלם זוגי. החיבור אינו גולש. מה הפלט?",
                       f"Average A={p['a']} and B={p['b']}, rounding to nearest integer and breaking exact-half ties toward even. Addition does not overflow. What is the output?")
        case 241:
            return loc(f"קלט BCD חוקי מייצג ספרה {p['digit']}. מחזירים 3 פעמים הספרה בשתי ספרות BCD. מה ספרת היחידות העשרונית?",
                       f"A valid BCD input represents digit {p['digit']}. Return 3 times it as two BCD digits. What is the decimal units digit?")
        case 242:
            return loc(f"קלט BCD חוקי מייצג ספרה {p['digit']}. מחזירים 3 פעמים הספרה בשתי ספרות BCD. מה ספרת העשרות העשרונית?",
                       f"A valid BCD input represents digit {p['digit']}. Return 3 times it as two BCD digits. What is the decimal tens digit?")
        case 243:
            queries = {
                'excluded': ('כמה מילות קלט מתוך 16 אינן מכוסות בהבטחה?', 'How many of the 16 input words lie outside the promise?'),
                'lowest_invalid': ('מה הערך העשרוני הקטן ביותר שאינו קלט חוקי?', 'What is the smallest decimal value that is not a legal input?'),
                'highest_valid': ('מה הערך העשרוני הגדול ביותר של קלט חוקי?', 'What is the largest decimal value of a legal input?'),
                'defined_rows': ('בכמה שורות של טבלת 16 השורות הפלט נדרש לפי החוזה?', 'In how many rows of the 16-row truth table is output required by the contract?'),
                'output_max': ('מה ערך הפלט העשרוני המרבי עבור קלט חוקי?', 'What is the largest decimal output for a legal input?'),
            }[p['query']]
            return loc('למכפיל BCD ב־3 מובטח שקלט בן 4 ביטים הוא רק 0..9. ' + queries[0],
                       'A BCD times-3 circuit is promised a 4-bit input in 0..9. ' + queries[1])
        case 244:
            return loc(f"למציאת floor(log2(x)) עבור x={p['x']}>0, מזיזים ימינה עד 1 וסופרים הזזות בלבד. מה המונה בסוף?",
                       f"To find floor(log2(x)) for x={p['x']}>0, shift right until reaching 1 and count shifts only. What is the final count?")
        case 245:
            return loc(f"למילה בלתי מסומנת ברוחב {p['w']} ו־x>0, מחזירים floor(log2(x)). כמה ביטי פלט מספיקים לכל התוצאות? אינדיקציית x=0 נשמרת בנפרד.",
                       f"For a width-{p['w']} unsigned word with x>0, return floor(log2(x)). How many output bits cover every result? Validity for x=0 is handled separately.")
        case 246:
            return loc(f"בחלוקה סדרתית ב־5, השארית הקודמת היא {p['r']}, וביט חדש {p['bit']} נצמד מימין. הספרה החדשה במנה היא floor((2r+b)/5). מה ערכה?",
                       f"In serial division by 5, the old remainder is {p['r']} and new bit {p['bit']} is appended on the right. The next quotient bit is floor((2r+b)/5). What is it?")
        case 247:
            return loc(f"ביטים {p['bits_value']:0{p['width']}b} נקלטים MSB תחילה, כולל אפסים מובילים, ומחלקים ב־5 תוך שמירת מנה ושארית. מה המנה העשרונית לאחר כל הביטים?",
                       f"Bits {p['bits_value']:0{p['width']}b} arrive MSB first, including leading zeros. A divider by 5 stores quotient and remainder. What is the decimal quotient after all bits?")
        case 248:
            return loc(f"מחלק סדרתי ב־{p['divisor']} שומר רק את השארית הלא שלילית. כמה FF לפחות דרושים לקודד את כל השאריות האפשריות בינארית? המנה מועברת בנפרד.",
                       f"A serial divider by {p['divisor']} stores only its nonnegative remainder. How many FFs are needed for binary encoding of every possible remainder? Quotient data travels separately.")
        case 249:
            return loc(f"חד־יציב שאינו ניתן לאתחול מחדש מפיק פולס ברוחב {p['width']}. טריגרים בזמנים {p['triggers']}; טריגר בזמן פולס נזנח, ובדיוק בסיומו מתקבל. כמה פולסים מתחילים? המצב בתחילה נמוך.",
                       f"A non-retriggerable monostable emits width-{p['width']} pulses. Triggers occur at {p['triggers']}; triggers during a pulse are ignored, while one exactly at its end is accepted. How many pulses start? Initially low.")
        case 250:
            return loc(f"חד־יציב ניתן לאתחול מחדש מפיק רוחב {p['width']}. הטריגרים הם {p['triggers']}, וכל מרווח קטן מהרוחב, כך שהפלט אינו נופל ביניהם. מתי הפולס מסתיים?",
                       f"A retriggerable monostable has width {p['width']}. Triggers are {p['triggers']}, with every gap smaller than the width, so output never falls between them. When does the pulse end?")
    raise ValueError(n)


def rationale(n, p, value):
    if n == 207 and p['s0_time'] == p['s1_time']:
        return loc("שני ביטי הבחירה משתנים יחד מ־00 ל־11. במודל ללא השהיה אין שהייה בקוד ביניים והפלט נשאר 0, ולכן רוחב הפולס אפס.",
                   "Both select bits change together from 00 to 11. In the zero-delay model no intermediate code persists and output stays 0, so pulse width is zero.")
    reasons = {
        201: ("הביטים היוצאים מצד ימין חוזרים לשמאל; מסכת הרוחב מסירה ביטים עודפים.", "Bits leaving the right return at the left; the width mask removes excess bits."),
        202: ("סיבובים באותו כיוון מצטברים; סיבוב ברוחב מלא מחזיר את אותה מילה.", "Same-direction rotations add; a full-width rotation returns the same word."),
        203: ("יש log2 של הרוחב שלבים, וכל שלב משתמש במספר MUX השווה לרוחב.", "There are log2(width) stages, with width MUXes per stage."),
        204: ("סיבוב מעגלי הוא תמורה של מיקומי הביטים ואינו משנה את מספר האחדים.", "Cyclic rotation permutes bit positions without changing the number of ones."),
        205: ("בסיבוב ימינה, פלט j מקבל קלט j+k, מודולו רוחב המילה.", "For right rotation, output j receives input j+k modulo the word width."),
        206: ("מספר הנתון הנבחר הוא 2*S1+S0; אין להפוך בין הבחירה הגבוהה לנמוכה.", "The selected data index is 2*S1+S0; the high and low select bits are not interchangeable."),
        207: ("בין שני שינויי הבחירה נבחר D1 או D2. גם MUX ללא השהיות מגיב לקוד הביניים; איזון השהיות פנימיות לבדו אינו מונע זאת.", "Between the select changes, D1 or D2 is selected. Even a zero-delay MUX responds to that intermediate code; balancing internal delays alone cannot prevent it."),
        208: ("עבור NMOS בודקים VG>Vtn; עבור PMOS בודקים VDD-VG>|Vtp|. באזור המעבר ייתכנו שני רכיבים מוליכים או שניהם כבויים.", "For NMOS test VG>Vtn; for PMOS test VDD-VG>|Vtp|. The transition region can have both devices on or both off."),
        209: ("NMOS חזק בהעברת נמוך ו־PMOS חזק בהעברת גבוה; יחד הם מעבירים את שתי המסילות במודל הנתון.", "NMOS passes low strongly and PMOS passes high strongly; together they pass both rails in this model."),
        210: ("המקור מספק מטען C*V במתח V, ולכן האנרגיה C*V²; בקבל נשמר רק חצי ממנה.", "The supply delivers charge C*V at voltage V, hence energy C*V²; only half is stored in the capacitor."),
        211: ("בכל תבנית מתקדמים כמספר האחדים שבה. חוזרים יחד כשהמספר המצטבר מתחלק ב־6 ומסתיימת תבנית שלמה.", "Each pattern advances by its number of ones. Joint recurrence requires a multiple of 6 increments and a whole number of EN patterns."),
        212: ("תנאי התאוששות ממצב לא חוקי קודם לתנאי enable, לפי החוזה המפורש.", "Invalid-state recovery takes precedence over enable under the explicit contract."),
        213: ("רק מעבר מתקבל מ־5 ל־0 הוא wrap; שהייה ב־5 עם EN=0 אינה פולס נוסף.", "Only an accepted 5-to-0 transition is a wrap; holding at 5 with EN=0 adds no pulse."),
        214: ("חזית עלייה היא מעבר 0 ל־1 של השעון המגודר עצמו, ולא של שעון המקור בהכרח.", "A rising edge is a 0-to-1 transition of the gated clock itself, not necessarily of the source clock."),
        215: ("המחזור הסופי הוא ארבעה מחזורי קלט, והרמה הגבוהה נמשכת מחצית ממנו.", "The final period is four input periods, and its high phase occupies half of it."),
        216: ("ב־ripple החזית עוברת רכיב אחר רכיב, ולכן מצטברות השהיות clk-to-Q.", "In a ripple structure, the edge travels through successive devices, accumulating clk-to-Q delays."),
        217: ("רגיסטר יציאה נוסף דוגם בחזית הבאה; הוא מוסיף מחזור השהיה ואינו משנה את הרצף המזוהה.", "An extra output register samples at the next edge, adding a cycle without changing the recognized pattern."),
        218: ("מצבים שנותנים פלט שונה לאותו המשך אינם ניתנים למיזוג. בודקים המשכים לפי אורך ואז סדר לקסיקוגרפי.", "States producing different output for the same continuation cannot be merged. Check continuations by length and then lexicographic order."),
        219: ("מרחק חפיפה חוקי דורש שהסיומת של ההופעה הראשונה תתאים לקידומת השנייה; בלי חפיפה המרחק הוא אורך הרצף.", "A legal overlap requires the first occurrence's suffix to equal the second's prefix; without overlap the gap equals pattern length."),
        220: ("רק דגימות תקפות מצטרפות לרצף, אבל הפולס ממוקם על ציר מחזורי השעון המקורי.", "Only valid samples extend the pattern, but pulses are placed on the original clock-cycle timeline."),
        221: ("Valid מתאר קבלה; נתון זהה יכול לייצג כמה דגימות נפרדות.", "Valid defines acceptance; identical data may represent several distinct samples."),
        222: ("דגימה לא תקפה אינה שוברת רצף של דגימות תקפות; רק אי־התאמה תקפה מאפסת.", "An invalid cycle does not break a streak of accepted samples; only an accepted mismatch resets it."),
        223: ("מחברים ב־OR את שתי תוצאות השוויון, ומסננים באמצעות Valid; לא סופרים אותה דגימה פעמיים.", "OR the equality results and qualify with Valid; never count one sample twice."),
        224: ("צילום קובע קבוצת תגיות קבועה; השלמת משימה מאוחרת אינה משלימה תגית חסרה מהצילום.", "A snapshot fixes the tag set; finishing a later task cannot replace a missing snapshot tag."),
        225: ("ממתינים לזמן ההשלמה המרבי בקבוצת הצילום, בלי להניח שסדר הקבלה הוא סדר ההשלמה.", "Wait for the latest completion within the snapshot, without assuming acceptance order equals completion order."),
        226: ("סופרים חיתוך קבוצות התגיות; ACK של משימה מחוץ לצילום אינו מקדם את המחסום הזה.", "Count the intersection of tag sets; an ACK outside the snapshot does not advance this barrier."),
        227: ("כל חבילה תורמת את הזמן שעבר מאז כניסתה; האינטגרל כולל גם חבילות שטרם יצאו.", "Each packet contributes elapsed time since entry; the integral includes packets that have not yet departed."),
        228: ("מסכמים יציאה פחות כניסה לכל חבילה שהושלמה ומחלקים במספר החבילות האלה.", "Sum departure minus arrival for each completed packet and divide by their count."),
        229: ("מחלקים את סכום הזמנים הכולל במספר החבילות הכולל; ממוצע פשוט בין פורטים אינו משוקלל.", "Divide total residence time by total packet count; a simple mean of port means ignores weighting."),
        230: ("הכתובת נדגמת בחזית; שינוי אחריה אינו מחליף בדיעבד את הדגימה שכבר נלכדה.", "The address is sampled at the edge; changing it afterward cannot replace the captured sample."),
        231: ("הנתון המוחזק אינו בהכרח תשובה חדשה; Valid מבדיל בין קבלה חדשה לבין ערך ישן.", "Held data need not be a new response; Valid distinguishes a new capture from an old value."),
        232: ("הכרעת התנגשות אינה נגזרת מעצם המילה סינכרוני; משתמשים במדיניות שהוגדרה במפורש.", "Collision behavior is not implied by the word synchronous; use the explicitly specified policy."),
        233: ("יש ארבע מילות אחסון ועוד כל רגיסטר יציאה שנדרש בנפרד; כל ביט דורש FF במימוש זה.", "Count four stored words plus each separately required output register; each bit requires an FF in this implementation."),
        234: ("מפענח מפעיל ביט יחיד בכתובת הנבחרת רק כאשר כתיבה מאופשרת.", "The decoder activates exactly the selected address bit only when writing is enabled."),
        235: ("שחרור האיפוס אינו נתון רגיל, אך גם לו תנאי תזמון: מחפשים חזית שאינה קודמת לזמן השחרור ועוד recovery.", "Reset release is not ordinary data, but it has timing constraints too: find an edge no earlier than release plus recovery."),
        236: ("מחשבים נשא משני הביטים הנמוכים ובוחרים בעזרתו את זוג תוצאת הסכום והנשא הגבוהים; אסור לבחור אותם מנתיבי קדם־חישוב שונים.", "Compute carry from the low two bits and use it to select both high sum and high carry; never mix results from different precomputed branches."),
        237: ("G נבדק עם נשא כניסה אפס. הקבוצה מעבירה נשא רק כשסכומה ללא נשא הוא בדיוק 2^W-1.", "Evaluate G with carry-in zero. The group propagates only when its sum without carry-in is exactly 2^W-1."),
        238: ("מוצאים את סכום שני הערכים המרביים ואת מספר הביטים הדרוש לייצוגו.", "Find the sum of the two maximum inputs and the bits needed to represent it."),
        239: ("לסכום אי־זוגי מוסיפים אחד לפני חלוקה ב־2; עיגול כלפי מטה נותן תוצאה שונה.", "For an odd sum, add one before dividing by 2; rounding downward produces a different result."),
        240: ("בסכום אי־זוגי שתי האפשרויות במרחק חצי; בוחרים את הזוגית מביניהן.", "For an odd sum, both neighboring integers are half a unit away; select the even one."),
        241: ("ספרת היחידות היא שארית 3*d בחלוקה ב־10; היא אינה ארבעת הביטים הנמוכים של המכפלה.", "The units digit is the remainder of 3*d modulo 10, not the product's low four bits."),
        242: ("ספרת העשרות היא החלק השלם של 3*d חלקי 10; היא יכולה להיות גם 2.", "The tens digit is the integer part of 3*d divided by 10; it may equal 2."),
        243: ("מבין 16 צירופי ארבעה ביטים רק עשרה הם ספרות BCD; הגדרת התנהגות לשישה הנותרים היא חוזה נוסף.", "Of 16 four-bit patterns, only ten are BCD digits; defining the other six requires an additional contract."),
        244: ("מספר ההזזות עד 1 שווה לאינדקס האחד הגבוה ביותר; אין לספור את ההזזה שהייתה מוחקת גם אותו.", "The shifts needed to reach 1 equal the highest-one index; do not count a shift that would erase it."),
        245: ("הערכים האפשריים הם 0 עד W-1; רוחב הפלט מקודד אינדקס ולא את המילה כולה.", "Possible results range from 0 to W-1; output width encodes an index, not the entire word."),
        246: ("השארית הקודמת קטנה מ־5, ולכן 2r+b לכל היותר 9 והספרה החדשה היא רק 0 או 1.", "The old remainder is below 5, so 2r+b is at most 9 and the next quotient digit is only 0 or 1."),
        247: ("בכל צעד נשמרת הזהות קידומת=5*מנה+שארית; אפסים מובילים אינם משנים את הערך.", "Each step preserves prefix=5*quotient+remainder; leading zeros do not change the value."),
        248: ("מחלק d דורש d שאריות שונות, 0 עד d-1; מספר הביטים הוא ceil(log2(d)).", "A divisor d requires d distinct remainder states, 0 through d-1; binary width is ceil(log2(d))."),
        249: ("לא כל טריגר יוצר פולס: טריגרים בתוך חלון פעיל אינם מזיזים את סיומו בחד־יציב זה.", "Not every trigger starts a pulse: triggers within an active window do not move its end in this monostable."),
        250: ("כל טריגר דוחה את הסיום לרוחב מלא אחריו; בשרשרת ללא הפסקה קובע הטריגר האחרון.", "Each trigger postpones the end by a full width; in a continuous chain the last trigger determines the end."),
    }
    return loc(*reasons[n])


# Each row is a distinct learning objective, not a new interview attribution.
# Cases vary data, boundary, enable, event timing or inference within that objective.
SPECS = [
    (201, 199, 'bits', 'הסיבוב מחזיר את הביטים לקצה השני', 'Rotation returns bits at the opposite end', 'סיבוב שומר את כל הביטים, בניגוד להזזה שממלאת באפסים.', 'Rotation preserves every bit, unlike a zero-filling shift.', params('w x k', [(4,9,1),(4,6,2),(8,129,3),(8,165,7),(4,11,0)])),
    (202, 199, 'bits', 'שני סיבובים הם כמות מודולרית אחת', 'Two rotations form one modular amount', 'מפשטים שרשרת סיבובים באמצעות חיבור מודולו הרוחב.', 'Simplify rotation chains by addition modulo width.', params('w a b', [(8,3,6),(4,3,1),(8,0,7),(16,12,9),(4,2,3)])),
    (203, 199, 'gates', 'עלות השלבים במסובב נשלט', 'Count stages in a controlled rotator', 'מסובב בשלבים מחליף בחירה גדולה בכמה שכבות MUX.', 'A staged rotator replaces a large selection with several MUX layers.', params('w', [(4,),(8,),(16,),(32,),(64,)])),
    (204, 199, 'bits', 'כמות האחדים אינה מסתובבת החוצה', 'The ones count cannot rotate away', 'חיווט מחדש משנה מיקומים, לא את משקל המילה.', 'Rewiring changes positions, not word Hamming weight.', params('w x', [(4,11),(8,129),(8,255),(4,0),(8,90)])),
    (205, 199, 'gates', 'למצוא את מקורו של ביט פלט', 'Find the source of an output bit', 'כותבים מיפוי אינדקסים לפני שמחברים חוטים.', 'Write the index mapping before connecting wires.', params('w k j', [(8,3,7),(8,2,1),(4,1,3),(16,7,12),(4,0,2)])),
    (206, 214, 'gates', 'מי סיבית הבחירה הגבוהה', 'Which select bit is high-order', 'סדר סיביות הבחירה הוא חלק מהגדרת ה־MUX.', 'Select-bit ordering is part of the MUX contract.', [dict(d=d,s1=s1,s0=s0) for d,s1,s0 in [([7,2,9,4],1,0),([1,5,8,3],0,1),([6,4,2,9],1,1),([8,3,5,1],0,0),([2,7,1,8],1,0)]]),
    (207, 214, 'gates', 'קוד ביניים בבחירה יוצר פולס גם בלי השהיות', 'An intermediate select code creates a pulse even without delays', 'שינוי כמה ביטי בקרה דורש חוזה לדגימה או לקידוד הביניים.', 'Changing several control bits needs a sampling or intermediate-code contract.', params('s0_time s1_time', [(1,4),(5,2),(3,3),(0,2),(2,7)])),
    (208, 205, 'electronics', 'אזורי הולכה חופפים במהפך CMOS', 'Overlapping conduction regions in a CMOS inverter', 'עוברים ממודל ביטים למודל סף כדי להבין מצב מעבר.', 'Use a threshold model to reason about the transition region.', params('vdd gate vtn vtp', [(4,0,1,1),(4,4,1,1),(4,2,1,1),(2,1,1.2,1.2),(4,1.5,1,3)])),
    (209, 200, 'electronics', 'שני רכיבי מעבר משלימים זה את זה', 'Two pass devices complement one another', 'חיבור NMOS ו־PMOS במקביל יכול להעביר את שתי המסילות.', 'Parallel NMOS and PMOS devices can pass both rails.', params('ng pg data', [(1,1,1),(0,0,0),(1,0,1),(1,0,0),(0,1,1)])),
    (210, 205, 'electronics', 'אנרגיה מהמקור לעומת אנרגיה שנשמרת', 'Supply energy differs from stored energy', 'טעינה מלאה שואבת C*V² מהמקור; חצי נשמר בקבל.', 'A full charge draws C*V² from the supply; half stays in the capacitor.', params('c v', [(2,3),(4,2),(1,5),(3,2),(5,1)])),
    (211, 202, 'sequential', 'מחזור החזרה תלוי גם בתבנית enable', 'Recurrence depends on the enable pattern too', 'מפרידים בין מחזור המונה לבין הזמן בשעון המקור.', 'Distinguish the counter cycle from time in source-clock cycles.', [dict(en=en) for en in [[1,0],[1,1,0],[1,0,1,0,0],[1,1,1,0],[1,1,1,1,0]]]),
    (212, 202, 'states', 'התאוששות גם כאשר enable כבוי', 'Recovery even when enable is low', 'סדר קדימויות בין התאוששות והקפאה חייב להיות מוגדר.', 'Recovery-versus-hold priority must be specified.', params('q en', [(6,0),(7,1),(5,0),(5,1),(2,1)])),
    (213, 202, 'sequential', 'wrap הוא מעבר ולא מצב מוחזק', 'Wrap is a transition, not a held state', 'פולס על אירוע דורש את תנאי הקבלה לצד פענוח המצב.', 'An event pulse needs acceptance as well as state decoding.', [dict(start=q,en=en) for q,en in [(5,[0,0,1]),(4,[1,1,0]),(0,[1]*6),(5,[1]*7),(5,[0]*4)]]),
    (214, 216, 'sequential', 'ספירת חזיתות אחרי גידור נאיבי', 'Count edges after naive clock gating', 'enable סינכרוני אינו זהה ל־AND שרירותי על השעון.', 'A synchronous enable is not an arbitrary AND on the clock.', [dict(clk=c) for c in [[0,1,0,1,0],[1,0,1,0,1],[0,0,1,1,0],[1,1,1,0,0],[0,1,0,1,0,1,0]]]),
    (215, 216, 'sequential', 'רוחב הרמה הגבוהה אחרי חלוקה', 'High-phase width after division', 'מחזור ומשך רמה גבוהה הם גדלים שונים.', 'Period and high-phase duration are different quantities.', params('period', [(2,),(3,),(5,),(7,),(10,)])),
    (216, 216, 'sequential', 'חזית ripple אינה מגיעה לכולם יחד', 'Ripple edges do not arrive together', 'חלוקה פונקציונלית נכונה עדיין יכולה ליצור סטייה בתזמון החזיתות.', 'Correct frequency division can still produce edge-timing skew.', params('ripple tcq', [(2,1),(3,2),(4,1),(2,3),(5,2)])),
    (217, 204, 'states', 'רגיסטר יציאה מזיז את מחזור הזיהוי', 'An output register shifts detection time', 'מציינים אם הפולס משויך לחזית האחרונה או לחזית שאחריה.', 'Specify whether the pulse belongs to the final-bit edge or the next edge.', params('detect', [(4,),(6,),(9,),(12,),(20,)])),
    (218, 204, 'states', 'המשך קלט שמוכיח ששני מצבים שונים', 'A continuation proving two states differ', 'מוכיחים שמצבים נפרדים נחוצים באמצעות המשך שמבדיל ביניהם.', 'Prove separate states are necessary with a distinguishing continuation.', [dict(a=a,b=b) for a,b in [('', '1'),('1','11'),('11','110'),('','110'),('1','110')]]),
    (219, 217, 'states', 'מרחק מזערי בין שתי הופעות', 'Minimum separation between two occurrences', 'סיומות וקידומות מגבילות את קצב הזיהויים האפשרי.', 'Suffixes and prefixes constrain the maximum possible detection rate.', [dict(pattern=s) for s in ['101101','0101','1101','1111','10110']]),
    (220, 207, 'states', 'בועת קבלה אינה ביט אפס ברצף', 'An acceptance bubble is not a zero bit', 'רצף סיביות מתקבלות וציר מחזורי השעון אינם אותו ציר.', 'The accepted-bit sequence and physical clock timeline are different axes.', [dict(samples=s) for s in [[[1,0],[0,1],[1,1],[1,0],[1,1]],[[1,0],[1,1],[1,0],[0,0],[1,1]],[[1,0],[1,1],[1,0],[1,1],[0,1],[1,0],[1,1]],[[0,0],[1,0],[1,1],[0,0]],[[1,0],[1,0],[1,1],[1,0],[1,1]]]]),
    (221, 218, 'sequential', 'ערך זהה אינו אותה עסקה', 'The same value is not the same transaction', 'מספר דגימות נקבע לפי Valid ולא לפי שינוי בנתון.', 'Valid, not data transitions, determines the sample count.', [dict(valid=v) for v in [[1,1,1],[1,0,1],[0,0,0],[1,0,0,1,1],[0,1,0,1]]]),
    (222, 218, 'states', 'בועת Valid אינה אי־התאמה', 'A Valid bubble is not a mismatch', 'רצף דגימות תקפות שונה מרצף מחזורי שעון.', 'A streak of accepted samples differs from a streak of clock cycles.', [dict(ref=5,samples=s) for s in [[[1,5],[0,2],[1,5]],[[1,5],[1,2],[1,5]],[[0,5],[0,5]],[[1,5],[1,5],[1,5]],[[1,5],[0,9],[1,2]]]]),
    (223, 218, 'gates', 'התאמה כפולה אינה ספירה כפולה', 'Two equal references do not double-count', 'OR בין התאמות נותן הצלחה אחת לכל דגימה.', 'OR of equality checks yields one success per sample.', [dict(refs=r,samples=s) for r,s in [([5,5],[[1,5],[1,2]]),([2,8],[[1,2],[1,8],[0,8]]),([1,3],[[1,2],[1,2]]),([0,9],[[1,0],[1,9],[1,9]]),([4,7],[[0,4],[1,7]])]]),
    (224, 208, 'states', 'משימה מאוחרת אינה חלק מהצילום', 'Later tasks are outside the snapshot', 'מחסום צילום עוקב אחר הקבוצה שנקבעה ברגע הלחיצה.', 'A snapshot barrier tracks the set fixed at button time.', [dict(accepted=a,cut=c,done=d) for a,c,d in [([1,2,3],2,[1,3]),([2,4,6],1,[4,6]),([1,2],2,[2,1]),([3,5,7,9],3,[3]),([1,2,3,4],0,[1,4])]]),
    (225, 208, 'states', 'האחרונה שהתקבלה אינה בהכרח האחרונה שסיימה', 'Last accepted need not finish last', 'תגיות מאפשרות לזהות חורים בסדר ההשלמה.', 'Tags expose holes in completion order.', [dict(snapshot=s,times=t) for s,t in [(['A','B'],dict(A=9,B=4)),(['A','C'],dict(A=2,B=20,C=7)),(['B'],dict(A=10,B=3)),(['A','B','C'],dict(A=8,B=6,C=4)),(['A','D'],dict(A=1,D=12))]]),
    (226, 208, 'states', 'ACK רלוונטי לקבוצת המתנה מסוימת', 'An ACK belongs to a particular waiting set', 'מונה כולל אינו תחליף לחברות בקבוצת הצילום.', 'A total completion count does not replace snapshot membership.', [dict(snapshot=s,done=d) for s,d in [([1,2],[2,3]),([2,4],[1,3]),([1,2,3],[3,1]),([5],[5,6,7]),([1,4],[1,4])]]),
    (227, 209, 'sequential', 'הזמן של חבילה שעדיין לא יצאה', 'Time accumulated by an unfinished packet', 'שטח מתחת לתפוסה כולל גם גיל של חבילות פעילות.', 'Occupancy area includes the age of active packets.', [dict(arrivals=a,end=t) for a,t in [([1,3],5),([0,2,4],6),([5],5),([1,1],4),([0,1,2,3],4)]]),
    (228, 209, 'sequential', 'ממוצע של קבוצת חבילות שהושלמה', 'Mean over a completed-packet cohort', 'מגדירים את קבוצת החבילות לפני שמחלקים במונה.', 'Define the packet cohort before dividing by a count.', [dict(pairs=p) for p in [[[0,4],[1,7]],[[2,5]],[[0,2],[1,5],[3,9]],[[1,4],[2,7]],[[0,10],[8,10]]]]),
    (229, 209, 'sequential', 'לשקלל את מספר החבילות בכל פורט', 'Weight each port by packet count', 'ממוצעים מקומיים דורשים משקלי מדגם כדי להתאחד נכון.', 'Local means need sample weights to combine correctly.', [dict(sums=s,counts=c) for s,c in [([2,18],[1,3]),([4,20],[2,2]),([6,6],[3,1]),([0,12],[1,3]),([12,18],[2,3])]]),
    (230, 220, 'sequential', 'כתובת חדשה אינה משנה קריאה שכבר נדגמה', 'A new address cannot alter a captured read', 'בקריאה סינכרונית הכתובת רלוונטית בחזית הקבלה.', 'For synchronous reads, address matters at the accepting edge.', [dict(memory=[3,7,2,9],sampled_addr=a,later_addr=b) for a,b in [(0,1),(1,3),(2,0),(3,2),(0,3)]]),
    (231, 220, 'sequential', 'הנתון מוחזק אבל Valid יורד', 'Data holds while Valid falls', 'ערך ישן ביציאה אינו מעיד שהייתה קריאה חדשה.', 'Old output data does not prove a new read occurred.', params('old read en', [(3,7,0),(3,7,1),(8,2,0),(0,9,1),(5,5,0)])),
    (232, 220, 'sequential', 'שם המדיניות קובע מה נקרא בהתנגשות', 'Collision policy determines the read value', 'מגדירים במפורש התנהגות קריאה וכתיבה לאותה כתובת.', 'Define same-address read/write behavior explicitly.', [dict(old=a,new=b,policy=c) for a,b,c in [(2,9,'read-first'),(2,9,'write-first'),(0,7,'read-first'),(8,1,'write-first'),(5,6,'read-first')]]),
    (233, 220, 'sequential', 'רגיסטר הקריאה אינו אחת ממילות הזיכרון', 'The read register is not a stored memory word', 'סופרים בנפרד את מערך הנתונים ואת אוגרי היציאה.', 'Count the data array and output registers separately.', params('w registered', [(8,1),(4,0),(16,1),(1,1),(3,0)])),
    (234, 220, 'gates', 'כתיבה מפעילה רק מילה אחת', 'A write enables only one word', 'פענוח כתובת חייב להיות מגודר גם ב־write enable.', 'Address decoding must also be qualified by write enable.', params('addr en', [(0,1),(3,1),(2,0),(1,1),(2,1)])),
    (235, 176, 'sequential', 'גם שחרור איפוס כפוף לתזמון', 'Reset release has timing constraints too', 'תזמון בקרה אסינכרונית דורש חוזה נפרד מתזמון הנתונים.', 'Asynchronous control timing needs its own contract, separate from data timing.', params('release recovery period', [(8,3,10),(7,3,10),(0,2,5),(15,2,8),(4,1,5)])),
    (236, 34, 'gates', 'בוחרים יחד את הסכום והנשא', 'Select sum and carry together', 'ב־carry-select בחירת נתיב שגוי יכולה לפגוע בסכום או בנשא בנפרד.', 'In carry-select, the wrong branch can corrupt sum and carry independently.', params('a b', [(3,1),(7,9),(5,6),(15,15),(8,4)])),
    (237, 34, 'gates', 'העברת נשא בכל קבוצת הטורים', 'Carry propagation across a whole group', 'העברת נשא של קבוצה דורשת מעבר דרך כל הטורים שלה.', 'Group propagation requires propagation through every column.', params('w a b', [(4,6,9),(4,7,9),(4,2,3),(3,3,4),(3,5,5)])),
    (238, 215, 'bits', 'רוחב סכום של כניסות שאינן באותו רוחב', 'Width of a sum with unequal input widths', 'גוזרים רוחב מהערך המרבי, בלי לקטום נשא.', 'Derive width from the maximum value without truncating carry.', params('a b', [(2,4),(1,4),(3,5),(2,2),(1,1)])),
    (239, 180, 'bits', 'ממוצע בעיגול כלפי מעלה', 'A mean rounded upward', 'רוחב מספיק ועיגול מוגדר הם שני תנאים נפרדים.', 'Sufficient width and defined rounding are separate requirements.', params('a b', [(2,5),(8,9),(0,0),(15,14),(4,6)])),
    (240, 180, 'bits', 'בחצי בוחרים את הזוגי', 'At a half choose the even result', 'אותו סכום דורש תוספת שונה בהתאם לכלל העיגול.', 'The rounding rule determines whether the truncated result needs incrementing.', params('a b', [(2,3),(3,4),(0,1),(5,6),(6,8)])),
    (241, 181, 'bits', 'ספרת יחידות אינה חיתוך בינארי', 'A units digit is not binary truncation', 'BCD דורש חישוב ספרות עשרוניות ולא רק חיתוך לביטים.', 'BCD requires decimal-digit arithmetic, not just bit truncation.', params('digit', [(4,),(7,),(9,),(0,),(6,)])),
    (242, 181, 'bits', 'גם עשרות יכולות להגיע לשתיים', 'The tens digit can reach two', 'טווח הקלט קובע כמה ספרות BCD דרושות בפלט.', 'Input range determines how many BCD output digits are needed.', params('digit', [(3,),(4,),(6,),(7,),(9,)])),
    (243, 181, 'gates', 'תחום BCD קובע אילו שורות מחייבות', 'The BCD domain determines required rows', 'קלט מחוץ לתחום אינו דוגמה נגדית לחוזה המובטח.', 'An input outside the domain does not refute a promised-domain contract.', [dict(query=q) for q in ['excluded','lowest_invalid','highest_valid','defined_rows','output_max']]),
    (244, 191, 'sequential', 'עוצרים באחד ולא באפס', 'Stop at one instead of zero', 'תנאי העצירה קובע אם סופרים אורך מילה או אינדקס ביט.', 'The stopping condition distinguishes bit length from a bit index.', params('x', [(1,),(2,),(7,),(16,),(65535,)])),
    (245, 191, 'bits', 'רוחב אינדקס האחד הגבוה', 'Width of the highest-one index', 'קידוד מיקום דורש פחות ביטים מהמילה שאותה הוא מתאר.', 'Encoding a position needs fewer bits than the word it describes.', params('w', [(4,),(8,),(16,),(32,),(64,)])),
    (246, 179, 'states', 'ביט המנה נובע מהשארית הקודמת', 'The quotient bit comes from the old remainder', 'בחילוק ארוך מעדכנים מנה ושארית מאותה קידומת.', 'Long division updates quotient and remainder from the same prefix.', params('r bit', [(0,1),(2,0),(2,1),(3,0),(4,1)])),
    (247, 179, 'states', 'מנה מצטברת אחרי כמה ביטים', 'The accumulated quotient after several bits', 'האינווריאנט של חילוק נשמר בכל קידומת ולא רק בסוף.', 'The division invariant holds for every prefix, not only the final word.', params('bits_value width', [(13,4),(31,5),(5,8),(0,4),(18,5)])),
    (248, 179, 'states', 'גודל מצב השארית אינו גודל המנה', 'Remainder state width is not quotient width', 'מספר השאריות קבוע גם כשאורך זרם הקלט גדל.', 'The number of remainder states stays fixed as the input stream grows.', params('divisor', [(5,),(3,),(8,),(9,),(16,)])),
    (249, 193, 'electronics', 'טריגר בזמן פולס יכול להיעלם', 'A trigger during a pulse may disappear', 'תגובה לטריגר תלויה בהגדרת retrigger, לא רק במתח הקלט.', 'Trigger response depends on retrigger semantics, not just input voltage.', [dict(width=w,triggers=t) for w,t in [(5,[0,2,5]),(4,[1,2,3]),(3,[0,3,6]),(5,[0,4,8]),(2,[0,1,2,3,4])]]),
    (250, 193, 'electronics', 'הטריגר האחרון דוחה את סיום הפולס', 'The final trigger postpones pulse end', 'בחד־יציב ניתן לאתחול מחדש שומרים את מועד הטריגר האחרון.', 'A retriggerable monostable retains the latest trigger time.', [dict(width=w,triggers=t) for w,t in [(5,[0,2,4]),(4,[1,3,5]),(3,[0,1,2]),(6,[2,5,8]),(2,[0,1,2,3])]]),
]


def distractors(n, value, p):
    if n in {208, 237}:
        return [[0, 0], [0, 1], [1, 0], [1, 1]]
    if n == 236:
        return [value, [value[0], 1 - value[1]], [(value[0] + 1) % 4, value[1]], [(value[0] + 3) % 4, value[1]]]
    if n == 209:
        return [value] + [x for x in [0, 1, 0.3, 0.7, 'Z'] if x != value][:3]
    if n == 218:
        return [value] + [x for x in ['0', '1', '01', '101', '1101'] if x != value][:3]
    if n == 231:
        return [[p['old'], 0], [p['read'], 1], [p['old'], 1], [p['read'], 0]] if p['old'] != p['read'] else [[p['old'], 0], [p['old'], 1], [0, 0], [0, 1]]
    if n == 224:
        candidates = [value, [], sorted(p['accepted'][:p['cut']]), sorted(p['done']), sorted(p['accepted'])]
    elif n == 220:
        candidates = [value, [], [1], [3], [2,4], [1,3,5], [4,6]]
    else:
        candidates = [value, max(0, value - 1), value + 1, value + 2, value + 3]
    out = []
    for item in candidates:
        if item not in out:
            out.append(item)
        if len(out) == 4:
            return out
    for filler in [[0], [99], [0,99], [99,100]]:
        if filler not in out:
            out.append(filler)
        if len(out) == 4:
            return out
    raise ValueError((n, value, p))


def render(value):
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    return str(value)


def build():
    CARDS.clear()
    QUESTIONS.clear()
    CHECKS.clear()
    for n, prep, topic, th, te, kh, ke, cases in SPECS:
        assert len(cases) == 5
        source = f'quick-hw-{n}'
        for v, p in enumerate(cases, 1):
            value = model(n, p)
            options = distractors(n, value, p)
            assert len(options) == 4 and sum(x == value for x in options) == 1
            options = [value] + [x for x in options if x != value]
            # A sequence counter balances the 250 answer positions to within one.
            shift = (5 * (n - 201) + v - 1) % 4
            options = options[shift:] + options[:shift]
            prompt = question(n, p)
            # Repeated binary physical states are explored with an explicit
            # changed preceding state rather than pretending five binary inputs exist.
            if 'context' in p:
                context = {
                    'low': ('הקלט נשאר נמוך.', 'The input remains low.'),
                    'high': ('הקלט נשאר גבוה.', 'The input remains high.'),
                    'after-fall': ('המעבר כלפי מטה כבר הסתיים.', 'A falling transition has finished.'),
                    'after-rise': ('המעבר כלפי מעלה כבר הסתיים.', 'A rising transition has finished.'),
                    'stable-zero': ('לאחר המתנה ארוכה נמדד אפס.', 'After a long wait, zero is measured.'),
                    'pass': ('הנתיב צריך להעביר נתון.', 'The path must pass data.'),
                    'isolate': ('הנתיב צריך לבודד נתון.', 'The path must isolate data.'),
                    'stable-one': ('ה־enable נשאר באחד.', 'Enable remains at one.'),
                    'zero': ('נבחן טור מחבר ללא אחדים בקלט.', 'Examine an adder column with no input ones.'),
                    'left': ('האחד מגיע מ־B.', 'The one comes from B.'),
                    'right': ('האחד מגיע מ־A.', 'The one comes from A.'),
                    'generate': ('שני הקלטים גבוהים.', 'Both inputs are high.'),
                    'second': ('בודקים גם carry-in גבוה ונמוך.', 'Check both high and low carry-in.'),
                }[p['context']]
                prompt = {lang: prompt[lang] + ' ' + context[i] for i, lang in enumerate(('he', 'en'))}
            explanation = rationale(n, p, value)
            explanation = {lang: f'{render(value)}. {text}' for lang, text in explanation.items()}
            key = f'{source}-v{v}'
            QUESTIONS.append(dict(key=key, source_key=source, variant=v, topic=topic, status='draft',
                                  prompt=prompt, choices=[loc(render(x), render(x)) for x in options],
                                  correct=options.index(value), explanation=explanation))
            CHECKS.append(dict(key=key, task=n, inputs=p, options=options, expected=value,
                               method='Independent enumeration or event replay in test_fundamentals_hardware_500.py',
                               scope='Bounded teaching model; no HDL/SPICE, physical timing or human-review claim.'))
            if v == 1:
                CARDS.append(dict(id=source, topic=topic, interviewIds=[f'PREP-{prep:03}'],
                                  title=loc(th,te), prompt=prompt, answer=explanation, takeaway=loc(kh,ke)))
    return QUESTIONS, CHECKS


def write():
    build()
    (CONTENT / 'fundamentals-hardware-500.json').write_text(json.dumps(CARDS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for name, values in [('hardware_500.json', QUESTIONS), ('hardware_500.checks.json', CHECKS)]:
        (OUT / name).write_text(json.dumps(values, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(CARDS)} hardware cards; {len(QUESTIONS)} draft variants; {len(CHECKS)} evidence records')


if __name__ == '__main__':
    write()
