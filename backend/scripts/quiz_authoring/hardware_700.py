"""100 bilingual hardware fundamentals and 500 draft interview-derived cases.

The equations below are explicit teaching contracts, not HDL execution, SPICE,
CDC signoff or human review. Tests independently enumerate/replay their inputs.
Difficulty and provenance are internal evidence, never learner-facing fields.
"""
from __future__ import annotations

import json
import math
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / 'apps/web/src/content'
OUT = ROOT / 'backend/seeds/duel_quiz_batches'
CARDS, SPECS = [], []


def loc(he, en):
    return dict(he=he, en=en)


def rows(names, values):
    return [dict(zip(names.split(), values_row, strict=True)) for values_row in values]


def add(n, prep, topic, titles, prompts, reasons, takeaways, names, values, coverage, difficulty=3):
    assert len(values) == len(coverage.split('|')) == 5
    SPECS.append(dict(n=n, prep=prep, topic=topic, title=loc(*titles),
                      prompt=loc(*prompts), reason=loc(*reasons), takeaway=loc(*takeaways),
                      cases=rows(names, values), coverage=coverage.split('|'), difficulty=difficulty))


def model(n, p):
    if '_query' in p: return alternative(n, p)
    if n == 251:
        if p['reset']: return [0,0]
        accept = not p['busy'] or p['done'] and p['bypass']
        operand = p['product'] if p['done'] and p['bypass'] else p['p']
        return [p['s'] + operand if accept else p['s'], p['product'] if p['done'] else p['p']]
    if n == 252:
        total, overflow = p['initial'], p['overflow']
        for reset, term in p['events']:
            if reset: total, overflow = 0, 0
            else:
                full = total + term
                overflow |= int(full >= 1 << p['w'])
                total = full % (1 << p['w'])
        return [total, overflow]
    if n == 253:
        result, valid = 0, 0
        for reset, equal, computed in p['events']:
            if reset: result, valid = 0, 0
            elif equal: result, valid = computed, 1
            else: valid = 0
        return [result, valid]
    if n == 254: return math.prod(p['factors']) % (1 << p['w'])
    if n == 255: return sum(v and r for v, r in p['vr'])
    if n == 256: return p['i'] * p['r']
    if n == 257: return p['vs'] - p['i'] * (p['rs'] + p['rg'])
    if n == 258: return p['common'] + F(p['branch'], p['paths'])
    if n == 259: return p['factor'] ** 2
    if n == 260: return F(p['i'] * p['us'], p['uf']) * 1000
    if n == 261:
        c = p['x'].bit_count()
        return [int(c < 4), int(c >= 3), c % 2, 1 - c % 2]
    if n == 262: return p['x'] ^ (2 if p['x'] in (5, 7) else 0)
    if n == 263: return (p['a'] & ~p['b'] & ((1 << p['w']) - 1)).bit_count()
    if n == 264:
        a, b = p['a'], p['b']
        return [1 - (a & b), a & b, (1 - a) & (1 - b)]
    if n == 265:
        a, b, c = p['abc']
        return [int(not a or b), int(not b or c), int(not a or c)]
    if n == 266: return p['inputs'] - 1
    if n == 267: return 1 if p['selected'] == 0 else p['other_depth'] + 1
    if n == 268: return 1 << p['select'] if p['enable'] else 0
    if n == 269:
        healthy = p['data'][p['select']]
        return [healthy, p['stuck'] if p['select'] == p['fault'] else healthy]
    if n == 270: return sum(p['data'])
    if n == 271: return 5 * p['x'] % 10
    if n == 272: return 5 * p['x'] // 10
    if n == 273: return [p['x'] >> 4, p['x'] & 15]
    if n == 274: return (p['x'] // 10) * 16 + p['x'] % 10
    if n == 275: return sum(x // 10 == p['tens'] for x in range(p['limit'] + 1))
    if n == 276:
        b, g = 0, p['g']
        while g: b, g = b ^ g, g >> 1
        return b
    if n == 277: return (p['write'] - p['read']) % (2 * p['depth'])
    if n == 278: return p['capture'] + p['stages'] + p['flag']
    if n == 279:
        a, b = p['a'], p['b']
        return ((a ^ (a >> 1)) ^ (b ^ (b >> 1))).bit_count()
    if n == 280: return p['depth'] - (p['write'] - p['seen_read'])
    if n == 281: return sorted(p['samples'][-3:], reverse=True)
    if n == 282: return sorted(p['samples'])[1]
    if n == 283:
        fill = 0
        for reset, valid in p['rv']: fill = 0 if reset else min(3, fill + valid)
        return fill
    if n == 284:
        a, b, c = p['samples']
        return [min(a, b), min(max(a, b), c), max(a, b, c)]
    if n == 285:
        pairs = list(zip(p['values'],p['tags'],strict=True))
        for a,b in [(0,2),(0,1),(1,2)]:
            if pairs[a][0] > pairs[b][0]: pairs[a],pairs[b] = pairs[b],pairs[a]
        return [tag for _,tag in pairs]
    if n == 286: return max(p['delays']) + p['overhead']
    if n == 287: return 0 if p['count'] == 0 else p['latency'] + (p['count'] - 1) * p['ii']
    if n == 288: return F(p['count'] * sum(p['delays']), (len(p['delays']) + p['count'] - 1) * max(p['delays']))
    if n == 289:
        progress = 0
        for edge in range(1, 100):
            progress += edge not in p['stalls']
            if progress == p['stages']: return edge
    if n == 290: return max(p['ii'])
    if n == 291: return [2 if direction == 'up' else 0 for direction in p['directions']]
    if n == 292: return [0, 1, 2, 1][(p['phase'] + p['edges']) % 4]
    if n == 293: return sum(k % 2 == 1 for k in range(1, p['edges'] + 1))
    if n == 294:
        q, rejected = p['initial'], 0
        for event in p['events']:
            nxt = q + event
            if event == 2 or not 0 <= nxt <= p['capacity']: rejected += 1
            else: q = nxt
        return [q, rejected]
    if n == 295: return p['lower']
    if n == 296: return (3 * ((1 << p['w']) - 1)).bit_length()
    if n == 297: return ((3 * p['x']) % (1 << p['w'])) * 16 + p['x']
    if n == 298: return (p['target'] - 1) // 16
    if n == 299: return (49 * p['x']) % 16
    if n == 300: return 49 * p['x'] // (1 << p['w'])
    if n == 301: return F(p['r'], 3)
    if n == 302: return math.comb(p['dimension'], p['layer']) * (p['dimension'] - p['layer'])
    if n == 303: return F(5 * p['r'], 6)
    if n == 304: return F(p['r2'] * p['r3'], p['r1'])
    if n == 305:
        r1, r2, r3, r4 = (p[k] for k in ['r1', 'r2', 'r3', 'r4'])
        return F(r1 * r2, r1 + r2) + F(r3 * r4, r3 + r4)
    if n == 306: return 1 + F(p['rf'], p['rg'])
    if n == 307: return F(p['a'] * p['den'], p['den'] + p['a'])
    if n == 308: return p['ib'] * p['r']
    if n == 309: return max(p['low'], min(p['high'], p['gain'] * p['vin']))
    if n == 310: return F(-p['vin'], p['rc'])
    if n == 311: return p['start'] - F(sum(v * t for v, t in p['segments']), p['rc'])
    if n == 312: return F(p['initial_error'], 2 ** p['halvings'])
    if n == 313: return F(p['vs'] * p['bottom'], p['top'] + p['bottom'])
    if n == 314: return (2 ** p['k']) - 1 if p['k'] >= 0 else F(1, 2 ** (-p['k'])) - 1
    if n == 315: return F(p['nd'], p['na'])
    if n == 316: return F(p['aggregate'], p['channels'])
    if n == 317: return (p['last'] - p['first']) * p['slot']
    if n == 318: return p['samples'] * p['channels'] * p['bits'] // 8
    if n == 319: return p['bits'] + 1
    if n == 320: return max(0, min((1 << p['bits']) - 1, p['mv'] * (1 << p['bits']) // p['fs']))
    if n == 321: return p['fs'] // p['fout']
    if n == 322:
        q = p['phase'] % (p['period'] // 2)
        return min(q, p['period'] // 2 - q)
    if n == 323: return p['first'][p['phase'] % len(p['first'])] * (-1 if p['phase'] >= len(p['first']) else 1)
    if n == 324: return F(p['clock'] * sum(p['en']), p['period'] * len(p['en']))
    if n == 325: return p['period'] // 4 + 1
    if n == 326: return F(p['r'], p['gates'].count(0))
    if n == 327: return p['r'] * p['series']
    if n == 328: return F(p['activity_num'], p['activity_den']) * p['freq'] * F(p['voltage_num'], p['voltage_den']) ** 2
    if n == 329:
        corner = p['corner']
        device = 1 if p['edge'] == 'rise' else 0
        return 2 if corner[device] == 'F' else 5
    if n == 330: return p['cq'] + p['data'] + p['setup'] + p['uncertainty'] - p['skew']
    if n == 331: return max(0, p['skew'] + p['hold'] + p['uncertainty'] - p['cq'] - p['data'])
    if n == 332: return p['capture'] - p['launch'] - p['cq'] - p['data'] - p['setup']
    if n == 333:
        lower = p['cqmax'] + p['dmax'] + p['setup'] - p['period']
        upper = p['cqmin'] + p['dmin'] - p['hold']
        return max(0, upper - lower)
    if n == 334: return max(0, -min(p['slacks']))
    if n == 335: return min(p['slacks'])
    if n == 336: return F(p['load'] - p['z0'], p['load'] + p['z0'])
    if n == 337: return F(p['vs'] * p['z0'], p['rs'] + p['z0'])
    if n == 338: return 2 * p['flight']
    if n == 339: return F(2 * p['incident'] * p['load'], p['load'] + p['z0'])
    if n == 340: return p['z0']
    if n == 341:
        longest = [1] * p['nodes']
        for v in range(p['nodes']):
            for a, b in p['edges']:
                if b == v: longest[v] = max(longest[v], longest[a] + 1)
        return max(longest)
    if n == 342: return max(map(len, p['kinds'].split('L')))
    if n == 343: return sum(length > p['limit'] for length in p['endpoint_lengths'])
    if n == 344: return sum(bool(roles) and set(roles) <= {'reset', 'clock'} for roles in p['roles'])
    if n == 345:
        remaining = set(range(p['nodes']))
        while True:
            roots = {v for v in remaining if not any(b == v and a in remaining for a, b in p['edges'])}
            if not roots: return len(remaining)
            remaining -= roots
    if n == 346: return min(3, sum(p['bits']))
    if n == 347: return max(0, 3 - sum(p['bits']))
    if n == 348: return max(0, math.isqrt(p['n']) - 1)
    if n == 349: return sum(x >= 2 and all(x % d for d in range(2, math.isqrt(x) + 1)) for x in p['numbers'])
    if n == 350: return next((d for d in range(2, math.isqrt(p['n']) + 1) if p['n'] % d == 0), 0)
    raise AssertionError(n)


add(251,219,'sequential',('פלוס ממתין למכפלה או לעקיפה מפורשת','Plus waits for a product or explicit bypass'),
    ('S={s},P={p},busy={busy}; מוצע PLUS. done={done}; רק done=1 טוען product={product} ל־P. bypass={bypass}. PLUS מתקבל אם !busy OR(done AND bypass), ומוסיף product רק ב־done AND bypass; אחרת P הישן. reset={reset}; רק reset=1 מאפס וגובר. מה [S,P] הבא?',
     'S={s},P={p},busy={busy}; PLUS is offered. done={done}; only done=1 loads product={product} into P. bypass={bypass}. PLUS accepts iff !busy OR(done AND bypass), adding product only for done AND bypass; otherwise old P. reset={reset}; only reset=1 clears both with priority. What is next [S,P]?'),
    ('קבלה משתמשת במצב busy הישן. תוצאה שחוזרת בחזית אינה זמינה לאותו פלוס בלי עקיפה מפורשת; איפוס מבטל את שני העדכונים.','Acceptance uses old busy. A product returning on the edge cannot feed that plus without explicit bypass; reset cancels both updates.'),
    ('תלות נתונים מחייבת המתנה או נתיב עקיפה מוגדר.','A data dependency requires waiting or a defined bypass path.'),
    's p busy done product bypass reset',[(3,5,1,1,12,0,0),(3,5,1,0,12,0,0),(3,5,1,1,12,1,0),(3,5,0,0,12,0,0),(3,5,1,1,12,1,1)],
    'result arrival without bypass|multiplier still busy|same-edge bypass|already idle|reset overrides completion',4)
add(252,219,'sequential',('דגל גלישה נשמר עד הביטוי הבא','Overflow stays latched until the next expression'),
    ('S ברוחב {w} ביט מתחיל ב־{initial}, ודגל גלישה ב־{overflow}. אירועים [reset,term] הם {events}. reset מאפס ושולל חיבור; אחרת מחברים term מודולו 2^{w}, ונשא מציב דגל שאינו מתאפס מעצמו. מה [S,דגל] הסופי?',
     '{w}-bit S starts at {initial}, overflow flag at {overflow}. Events [reset,term] are {events}. Reset clears both and skips addition; otherwise add term modulo 2^{w}, with carry setting a sticky flag. What is final [S,flag]?'),
    ('נשא מכל חיבור נצבר ב־OR לדגל. חיבור מאוחר שאינו גולש אינו מוחק גלישה קודמת; רק איפוס פותח מדידה חדשה.','OR each addition’s carry into the flag. A later nonoverflowing addition cannot erase earlier overflow; reset starts a new measurement.'),
    ('תוצאת חשבון מודולרית ודיווח גלישה הם מצבים נפרדים.','A modular arithmetic result and overflow reporting are separate states.'),
    'w initial overflow events',[(4,14,0,[[0,3],[0,2]]),(4,14,0,[[0,3],[1,7]]),(4,1,1,[[0,0],[0,1]]),(3,7,0,[[0,1]]),(4,0,0,[[0,3],[0,2]])],
    'sticky after later safe sum|reset clears overflow|zero does not clear|exact wrap carry|all additions fit')
add(253,219,'sequential',('תוצאה שמורה אינה בהכרח תוצאה חדשה','A held result is not necessarily new'),
    ('[result,valid] מתחילים ב־[0,0]. חזיתות [reset,accepted_equals,computed] הן {events}. reset מאפס וגובר; שוויון שהתקבל טוען computed ומרים valid; אחרת result נשמר ו־valid מתאפס. מה הזוג הסופי?',
     '[result,valid] starts at [0,0]. Edges [reset,accepted_equals,computed] are {events}. Reset clears both with priority; accepted equals loads computed and asserts valid; otherwise result holds and valid clears. What is the final pair?'),
    ('valid מתאר השלמה בחזית האחרונה, ואינו מציין אם אוגר התוצאה מכיל מספר ישן. איפוס גובר גם על השלמה בו־זמנית.','Valid denotes completion on the last edge, not whether the result register contains an old number. Reset overrides simultaneous completion.'),
    ('תוקף עסקה חדשה נפרד משימור נתוני העסקה הקודמת.','A new transaction’s validity is separate from retaining the previous transaction’s data.'),
    'events',[([[0,1,14],[0,0,7]],),([[0,1,3],[0,1,9]],),([[0,1,6],[1,1,4]],),([[0,0,8],[0,0,2]],),([[0,1,0]],)],
    'result held without valid|back-to-back results|reset overrides completion|no completed expression|valid zero result')
add(254,219,'bits',('גלישת מכפלה נשמרת בחשבון מודולרי','Product overflow obeys modular arithmetic'),
    ('אוגר מכפלה ללא סימן ברוחב {w} ביט מתחיל ב־1 ומכפיל בסדר את {factors}. אחרי כל כפל נשמרים {w} ביטים. מה הערך הסופי?',
     'An unsigned {w}-bit product register starts at 1 and multiplies by {factors} in order. Each multiplication retains {w} bits. What is the final value?'),
    ('מכפלת הגורמים מודולו 2 בחזקת הרוחב נותנת אותה תוצאה כמו חיתוך בכל שלב.','The product modulo two to the word width equals truncation after every stage.'),
    ('הרחבה לאחר חיתוך אינה משחזרת ביטים שאבדו.','Widening after truncation cannot recover lost bits.'),
    'w factors',[(4,[3,7]),(4,[4,4,3]),(3,[7,7]),(5,[31,1]),(4,[9,3,0])],
    'overflow residue|intermediate zero wrap|two overflows|identity at maximum|late zero')
add(255,219,'sequential',('אסימון ממתין אינו מתקבל שוב','A waiting token is not accepted again'),
    ('זוגות [valid,ready] במחזורי מעריך ביטויים הם {vr}. קבלה היא valid AND ready בחזית. כמה אסימונים התקבלו? valid גבוה בזמן ready נמוך מציין אסימון ממתין.',
     'Expression-evaluator cycles have [valid,ready] pairs {vr}. Acceptance is valid AND ready at the edge. How many tokens were accepted? High valid while ready is low denotes a waiting token.'),
    ('סופרים רק חזיתות שבהן שני האותות גבוהים. המתנה למכפיל אינה קבלת אסימון נוסף.','Count only edges where both signals are high. Waiting for the multiplier does not accept another token.'),
    ('קצב הצגת נתונים וקצב קבלתם הם כמויות שונות.','Presentation rate and acceptance rate are different quantities.'),
    'vr',[([[1,0],[1,0],[1,1]],),([[0,1],[0,1]],),([[1,1],[1,1],[1,1]],),([[1,1],[1,0],[0,0],[1,1]],),([[0,0],[1,0],[0,1]],)],
    'held valid|ready without valid|back to back|busy gap|no coincident assertion')
add(256,233,'electronics',('מיליאוהם הופך למיליוולט','Milliohms become millivolts'),
    ('במודל DC, זרם {i} אמפר עובר במוליך בעל התנגדות {r} מיליאוהם. מה מפל המתח במיליוולט?',
     'In a DC model, {i} amperes flow through a conductor of resistance {r} milliohms. What is its voltage drop in millivolts?'),
    ('חוק אוהם נותן I·R. אמפר כפול מיליאוהם הוא מיליוולט; אין להכפיל שוב באלף.','Ohm’s law gives I·R. Amperes times milliohms gives millivolts; do not multiply by one thousand again.'),
    ('יחידות הן חלק מחישוב תקציב המתח.','Units belong in the voltage budget.'),
    'i r',[(2,15),(0,20),(5,0),(1,100),(10,3)],'loaded wire|zero current|ideal wire|large resistance|high current')
add(257,233,'electronics',('האדמה המקומית עולה גם היא','Local ground also rises'),
    ('מקור הוא {vs}mV. זרם {i}A עובר בנתיב אספקה {rs}mΩ ובחזרה {rg}mΩ. מה המתח בין שני פיני העומס, במיליוולט?',
     'The source is {vs}mV. Current {i}A flows through supply resistance {rs}mΩ and return resistance {rg}mΩ. What voltage appears between the load pins, in millivolts?'),
    ('מחסרים מהמקור את שני מפלי I·R. המדידה היא יחסית לאדמת העומס, ולא לאדמת המקור.','Subtract both I·R drops from the source. The reference is load ground, not source ground.'),
    ('תקציב אספקה כולל את מסלול ההלוך ואת מסלול החזרה.','A supply budget includes both outgoing and return paths.'),
    'vs i rs rg',[(1000,2,10,5),(1000,0,10,5),(1200,3,0,10),(1000,4,20,0),(900,5,5,25)],
    'both paths|no load|return only|supply only|dominant ground loss')
add(258,233,'electronics',('קטע משותף אינו מוכפל במקביל','The shared segment is not paralleled'),
    ('נתיב כולל {common}mΩ משותפים, ואחריהם {paths} ענפים זהים במקביל, כל אחד {branch}mΩ. מה ההתנגדות הכוללת במיליאוהם?',
     'A path has a shared {common}mΩ segment followed by {paths} identical parallel branches of {branch}mΩ each. What is total resistance in milliohms?'),
    ('רק התנגדות הענף מתחלקת במספר הענפים. מוסיפים את התנגדות הקטע המשותף פעם אחת.','Only branch resistance divides by the branch count. Add the shared resistance once.'),
    ('שכפול חלק מהנתיב אינו מבטל צוואר בקבוק משותף.','Duplicating part of a path leaves its shared bottleneck.'),
    'common paths branch',[(4,2,12),(0,3,9),(7,1,5),(10,4,4),(1,2,3)],
    'shared segment|pure parallel|single branch|common dominates|fractional resistance')
add(259,233,'electronics',('חימום גדל כריבוע הזרם','Heating grows with current squared'),
    ('באותו מוליך, ההתנגדות קבועה וזרם ההתחלה חיובי. מכפילים את הזרם פי {factor}. פי כמה משתנה הספק החימום I²R?',
     'A conductor has fixed resistance and initially positive current. Current is multiplied by {factor}. By what factor does its I²R heating power change?'),
    ('ההתנגדות מצטמצמת ביחס ההספקים, ונשאר ריבוע יחס הזרמים. גם כיוון זרם הפוך יוצר חימום.','Resistance cancels from the power ratio, leaving the squared current ratio. Reversed current still produces heating.'),
    ('מפל מתח ליניארי בזרם; הפסד הספק ריבועי בו.','Voltage drop is linear in current; power loss is quadratic.'),
    'factor',[(2,),(0,),(1,),(-1,),(-3,)],'double current|off|unchanged|reverse direction|larger reversed current',2)
add(260,233,'electronics',('קבל מקומי מספק מטען זמני','A local capacitor supplies temporary charge'),
    ('קבל אידאלי של {uf}µF מספק לבדו חוסר זרם קבוע של {i}A במשך {us}µs. מתעלמים מ־ESR והשראות. מה ירידת המתח במיליוולט?',
     'An ideal {uf}µF capacitor alone supplies a constant {i}A current deficit for {us}µs. Ignore ESR and inductance. What is its voltage decrease in millivolts?'),
    ('המטען שנגרע הוא I·t, וירידת המתח Q/C. התוצאה בוולטים מוכפלת באלף למיליוולט.','Removed charge is I·t and voltage decrease is Q/C. Convert volts to millivolts by multiplying by one thousand.'),
    ('קיבול תומך במעבר קצר; הוא אינו מקור DC קבוע.','Capacitance supports a transient, not a permanent DC deficit.'),
    'uf i us',[(50,1,1),(10,0,5),(20,2,0),(100,2,3),(8,1,1)],
    'ordinary transient|no deficit|zero duration|longer pulse|small capacitor')
add(261,234,'gates',('ארבע משמעויות לאותה מילה','Four predicates for the same word'),
    ('המילה x={x} היא בת ארבעה ביטים. מה וקטור התוצאות [יש אפס,לפחות שלושה אחדים,זוגיות אי־זוגית,זוגיות זוגית]? כל רכיב הוא 0 או 1.',
     'x={x} is a four-bit word. What is [contains zero,at least three ones,odd parity,even parity]? Each component is 0 or 1.'),
    ('סופרים אחדים. יש אפס כשהספירה קטנה מארבע; רוב מחמיר דורש לפחות שלושה; הזוגיות תלויה בשארית בחלוקה לשתיים.','Count ones. A zero exists below four; strict majority needs at least three; parity depends on the count modulo two.'),
    ('בחירת מצב משנה את התנאי, לא את פירוש ביטי הנתון.','Mode selection changes the predicate, not data-bit interpretation.'),
    'x',[(7,),(0,),(15,),(5,),(8,)],'three ones|all zero|all one|even split|single one')
add(262,254,'gates',('מסכה מותנית שומרת את יתר הערכים','A conditional mask preserves other values'),
    ('מעגל בן שלושה ביטים מחליף רק 5 ו־7 ומשאיר כל ערך אחר ללא שינוי. הקלט הוא {x}. מה הפלט העשרוני?',
     'A three-bit circuit swaps only 5 and 7, preserving every other value. Input is {x}. What is the decimal output?'),
    ('רק כאשר הביט הגבוה והביט הנמוך הם אחד, הופכים את הביט האמצעי. מסכת XOR קבועה הייתה משנה גם קלטים אחרים.','Invert the middle bit only when the high and low bits are both one. An unconditional XOR mask would also change other inputs.'),
    ('הבטחת שימור של קלטים אחרים מחייבת תנאי הפעלה.','Preserving other inputs requires an activation condition.'),
    'x',[(5,),(7,),(4,),(3,),(0,)],'forward swap|reverse swap|missing low control|missing high control|neither control')
add(263,283,'gates',('אילו ערוצים מפרים גרירה','Which channels violate implication'),
    ('בווקטורים ללא סימן ברוחב {w}, A={a}, B={b}. בכל מיקום נדרש A גורר B. כמה מיקומים מפרים את הדרישה?',
     'Unsigned {w}-bit vectors are A={a}, B={b}. Each position must satisfy A implies B. How many positions violate the requirement?'),
    ('הפרה קיימת רק במקום שבו A=1 וגם B=0. סופרים את האחדים ב־A AND NOT B בתחום הרוחב.','Only A=1 with B=0 violates implication. Count the ones of A AND NOT B within the word width.'),
    ('תנאי שלא הופעל אינו הפרה של גרירה.','An inactive premise does not violate an implication.'),
    'w a b',[(4,13,9),(4,0,0),(4,15,0),(4,5,15),(6,63,21)],
    'single missing consequence|vacuous truth|all violations|stronger consequence|alternating coverage')
add(264,286,'gates',('יציאות ביניים במימוש משערים אוניברסליים','Intermediate outputs in universal-gate constructions'),
    ('A={a}, B={b}. מחשבים t=NAND(A,B), y=NAND(t,t), z=NOR(A,B). מה [t,y,z] אחרי התייצבות?',
     'A={a}, B={b}. Compute t=NAND(A,B), y=NAND(t,t), z=NOR(A,B). What is [t,y,z] after settling?'),
    ('NAND עם כניסות מחוברות הופך את t ולכן y=A AND B. NOR ישיר מחזיר אחד רק כששניהם אפס.','A tied-input NAND inverts t, so y=A AND B. Direct NOR returns one only when both inputs are zero.'),
    ('חיבור הכניסות קובע אם שער אוניברסלי משמש כהיפוך.','Input wiring determines whether a universal gate acts as an inverter.'),
    'a b',[(1,1),(0,0),(1,0),(0,1),(1,1)],'both high|both low|A only|B only|settled return to high',2)
add(265,283,'gates',('גרירה בשרשרת נבדקת בכל חוליה','Implication is checked on each link'),
    ('שלושת הביטים [A,B,C] הם {abc}. מה וקטור ערכי האמת [A גורר B,B גורר C,A גורר C]?',
     'Bits [A,B,C] are {abc}. What is the truth vector [A implies B,B implies C,A implies C]?'),
    ('לכל זוג, רק 1 גורר 0 הוא שקר. אם שתי חוליות השרשרת אמת, גם הגרירה הישירה אמת.','For each pair, only one implying zero is false. If both chain links are true, the direct implication is also true.'),
    ('שתי גרירות אמת בשרשרת מצדיקות גרירה טרנזיטיבית.','Two true implications in a chain justify a transitive implication.'),
    'abc',[([1,1,0],),([1,0,1],),([0,1,0],),([1,1,1],),([0,0,0],)],
    'second link fails|first link fails|inactive premise|all active|all inactive')
add(266,235,'gates',('מספר הצמתים בעץ בוררים','Count nodes in a selector tree'),
    ('עץ מלא ללא שיתוף מכיל {inputs} עלי נתונים עצמאיים; לכל צומת פנימי MUX עם שתי כניסות. אין שערי נתונים אחרים. כמה MUXים בעץ?',
     'A full tree without sharing has {inputs} independent data leaves; each internal node is a two-input MUX. There are no other data gates. How many MUXes does it contain?'),
    ('כל MUX מחבר שתי תוצאות לאחת ומפחית את מספר הקבוצות באחת. כדי להגיע לקבוצה אחת נדרשים מספר העלים פחות אחד.','Each MUX joins two results, reducing the number of groups by one. Reaching one group needs one fewer join than leaves.'),
    ('ספירת רכיבים אינה זהה לעומק מסלול הנתונים.','Component count differs from data-path depth.'),
    'inputs',[(8,),(1,),(2,),(7,),(16,)],'balanced eight leaves|wire only|one selector|nonpower of two|larger tree')
add(267,235,'gates',('קיצור הנתיב של הקלט המאחר','Shorten the late input path'),
    ('MUX אחרון בוחר D0 ישירות כשהאינדקס 0, ואחרת תוצאה מעץ בעומק {other_depth}. נבחר אינדקס {selected}. כמה רמות MUX עובר הנתון הנבחר?',
     'A final MUX selects D0 directly for index 0, otherwise a result from a tree of depth {other_depth}. Selected index is {selected}. How many MUX levels does the selected datum traverse?'),
    ('הקלט הישיר עובר רק את הבורר האחרון. כל קלט מהעץ עובר גם את עומק העץ וגם את הבורר האחרון.','The direct input crosses only the final selector. A tree input crosses the tree depth plus the final selector.'),
    ('אופטימיזציה לקלט מאחר יכולה להאריך נתיבי קלט אחרים.','Optimizing a late input can lengthen other input paths.'),
    'other_depth selected',[(3,0),(3,1),(2,0),(1,1),(4,7)],
    'late direct input|ordinary input|shallower alternate tree|single alternate stage|deep alternate path')
add(268,236,'gates',('מפענח פעיל מספק בחירה חד־חמה','An enabled decoder supplies one-hot selection'),
    ('מפענח כולל שמונה יציאות, ביט 0 הוא D0. כתובת הבחירה {select}, enable={enable}. יציאה נבחרת היא 1; בכיבוי כולן 0. מה מסכת היציאות העשרונית?',
     'A decoder has eight outputs, with bit 0 naming D0. Select address is {select}, enable={enable}. The selected output is 1; disabled outputs are all 0. What is the decimal output mask?'),
    ('כאשר enable פעיל מציבים אחד רק בביט הכתובת. כיבוי מונע בחירה גם כשהכתובת חוקית.','When enabled, set only the addressed bit. Disable suppresses selection even for a legal address.'),
    ('אות הפעלה הוא חלק מהגדרת המפענח.','Enable belongs to the decoder contract.'),
    'select enable',[(3,1),(0,1),(7,1),(3,0),(7,0)],
    'interior select|lowest select|highest select|disabled interior|disabled high address')
add(269,235,'gates',('תקלה בנתון שאינו נבחר','A fault on unselected data'),
    ('MUX מקבל נתונים {data}. אינדקס {fault} תקוע ב־{stuck}; נבחר {select}. מה [פלט תקין,פלט תקול] אחרי התייצבות?',
     'A MUX has data {data}. Input index {fault} is stuck at {stuck}; selection is {select}. What is [healthy output,faulty output] after settling?'),
    ('רק הנתון הנבחר מגיע לפלט. תקלה נראית רק כשהנתיב שלה נבחר והערך התקוע שונה מערכו התקין.','Only selected data reaches the output. A fault is observable only when selected and different from the healthy value.'),
    ('בדיקת תקלה דורשת גם הפעלה וגם נתיב תצפית.','Testing a fault needs both activation and an observation path.'),
    'data fault stuck select',[([0,1,0,1],1,0,1),([0,1,0,1],1,0,3),([0,1,0,1],2,0,2),([0,0,1,1],0,1,0),([1,0,0,1],3,1,3)],
    'visible stuck low|masked by selection|unactivated stuck low|visible stuck high|unactivated stuck high')
add(270,236,'gates',('אילו מינטרמים יכולים להרים את הפלט','Which minterms can raise the output'),
    ('MUX עם נתונים קבועים {data} ממומש כמפענח ו־OR של מינטרמים. לכל כתובת קוד יחיד. כמה קודי בחירה מפיקים פלט 1?',
     'A MUX with constant data {data} uses a decoder and OR of minterms. Each address has one code. How many select codes produce output 1?'),
    ('כל כניסת נתון שהיא אחד תורמת בדיוק קוד בחירה אחד. כתובות שונות נשארות מינטרמים נפרדים.','Each data input equal to one contributes exactly one select code. Different addresses remain distinct minterms.'),
    ('נתוני MUX קבועים הם טבלת אמת לפי כתובת.','Constant MUX data forms a truth table indexed by address.'),
    'data',[([0,1,0,1],),([0,0,0,0],),([1,1,1,1],),([0,0,0,1],),([1,0,1,1,0,0,1,0],)],
    'alternating|constant zero|constant one|single minterm|larger table')
add(271,257,'bits',('ספרת יחידות באמצעות ביט אחד ושני חוטים','Build the units digit with one bit and two wires'),
    ('במכפיל 5x עם x בן ארבעה ביטים, מחברים את x[0] לביטים 0 ו־2 של ספרת היחידות BCD, ואת האחרים לאפס. עבור x={x}, מה ערך הספרה שהחיווט מפיק?',
     'For four-bit 5x, wire x[0] to bits 0 and 2 of the BCD units digit and tie its other bits low. For x={x}, what digit value does this wiring produce?'),
    ('החיווט יוצר 0000 לקלט זוגי ו־0101 לקלט אי־זוגי. אלו בדיוק ספרות היחידות של 5x; אין צורך בחילוק או ממיר כללי.','The wiring produces 0000 for even input and 0101 for odd input. These are exactly 5x’s units digits, requiring no divider or general converter.'),
    ('מאפיין של קבוע הכפל יכול להחליף המרה כללית בחיווט.','A multiplier constant’s property can replace general conversion with wiring.'),
    'x',[(7,),(0,),(2,),(15,),(14,)],'ordinary odd|zero|even ten boundary|maximum input|largest even input')
add(272,257,'bits',('ספרת העשרות יוצאת מפרוסת קלט','The tens digit comes from an input slice'),
    ('מכפיל 5x עבור קלט בן ארבעה ביטים מזין את ספרת העשרות ישירות מ־x[3:1], עם ביט BCD עליון אפס. עבור x={x}, מה הערך העשרוני על קווי העשרות?',
     'A four-bit 5x converter drives its tens digit directly from x[3:1], with the high BCD bit zero. For x={x}, what decimal value appears on the tens wires?'),
    ('הפרוסה היא floor(x/2), ששווה floor(5x/10). היא תמיד בטווח 0..7 ולכן קידוד BCD חוקי, גם בלי לבנות את המכפלה.','The slice is floor(x/2), equal to floor(5x/10). It always lies in 0..7, so it is valid BCD without constructing the product.'),
    ('פישוט אלגברי יכול להחליף ממיר כללי במעגל קטן.','Algebraic simplification can replace a general converter with a small circuit.'),
    'x',[(6,),(1,),(2,),(15,),(0,)],'even interior|below ten|first tens carry|maximum input|zero')
add(273,262,'bits',('חיתוך לניבלים אינו המרה לעשרוני','Nibble splitting is not decimal conversion'),
    ('מישהו מחלק בטעות x={x} בינארי לניבל גבוה ונמוך כדי להזין תצוגה עשרונית. מה הערכים [ניבל גבוה,ניבל נמוך] שיקבל בפועל?',
     'Someone incorrectly splits binary x={x} into high and low nibbles for a decimal display. What [high nibble,low nibble] values actually result?'),
    ('חלוקה לניבלים היא מנה ושארית בבסיס 16. היא עשויה להפיק ספרה מעל תשע או ערך עשרוני שגוי.','Nibble splitting gives quotient and remainder in base sixteen. It may produce a digit above nine or the wrong decimal value.'),
    ('תקינות רוחב אינה מוכיחה תקינות קידוד ספרות.','A valid width does not prove valid digit encoding.'),
    'x',[(13,),(9,),(16,),(31,),(32,)],'illegal low digit|coincidentally correct|hex carry|both misleading|maximum promised input')
add(274,262,'bits',('שתי ספרות BCD במילה אחת','Pack two BCD digits into one word'),
    ('ממירים x={x}, בטווח 0..32, ל־BCD: העשרות בניבל הגבוה והיחידות בנמוך. מה הערך העשרוני של מילת שמונת הביטים המקודדת?',
     'Convert x={x}, in 0..32, to BCD: tens in the high nibble and units in the low nibble. What is the decimal value of the encoded eight-bit word?'),
    ('מחשבים עשרות ויחידות בבסיס עשר, ואז מקודדים 16·עשרות+יחידות. ערך המילה הבינארית אינו בהכרח x.','Compute decimal tens and units, then encode 16·tens+units. The binary word value need not equal x.'),
    ('מפרידים בין הערך המוצג לבין הקידוד שנשלח לתצוגה.','Separate the displayed value from its transport encoding.'),
    'x',[(13,),(0,),(9,),(10,),(32,)],'mixed digits|zero|last single digit|first tens carry|upper bound')
add(275,262,'gates',('תחום הקלט מגביל שורות תצוגה','Input range limits display rows'),
    ('ממיר מקבל את כל השלמים 0..{limit} בלבד. בכמה קלטים ספרת העשרות העשרונית שווה {tens}?',
     'A converter accepts exactly the integers 0..{limit}. For how many inputs is the decimal tens digit {tens}?'),
    ('סופרים את החיתוך בין תחום הקלט לבין קבוצת המספרים בעלי ספרת העשרות המבוקשת. אין להוסיף שורות מחוץ לחוזה.','Count the intersection of the input range with the requested tens-digit group. Do not add rows outside the contract.'),
    ('טבלת אמת מחויבת לכל התחום המותר ורק להבטחותיו.','A truth table must cover the entire promised domain.'),
    'limit tens',[(32,3),(32,0),(32,4),(20,2),(9,1)],'partial final decade|full first decade|unreachable digit|single endpoint|no tens')
add(276,264,'bits',('משחזרים מונה מקוד גריי','Recover a count from Gray code'),
    ('מצביע FIFO בן ארבעה ביטים נשלח כ־g=b XOR (b>>1). הקוד שהתקבל הוא g={g} בעשרוני. מה המצביע הבינארי b בעשרוני?',
     'A four-bit FIFO pointer is sent as g=b XOR (b>>1). Received Gray code is g={g} in decimal. What is binary pointer b in decimal?'),
    ('ביט ה־MSB נשמר. כל ביט בינארי הבא הוא XOR בין הביט הבינארי שמעליו לבין ביט הגריי הנוכחי.','The MSB is unchanged. Each next binary bit is the XOR of the preceding binary bit and the current Gray bit.'),
    ('קוד גריי מייצג מספר אך אינו משקל בינארי רגיל.','Gray code represents a number without ordinary binary place weights.'),
    'g',[(7,),(0,),(1,),(12,),(8,)],'interior prefix xor|zero|first increment|high half|last binary code')
add(277,264,'sequential',('ביט ההקפה מבחין בין מלא לריק','The wrap bit distinguishes full from empty'),
    ('FIFO בעומק {depth} משתמש במצביעים בינאריים מודולו {modulus}. write={write}, read={read}; הפרש חוקי מובטח בין 0 לעומק. כמה מילים מאוחסנות?',
     'A depth-{depth} FIFO uses binary pointers modulo {modulus}. write={write}, read={read}; occupancy is guaranteed between zero and depth. How many words are stored?'),
    ('מחסרים את מצביע הקריאה ממצביע הכתיבה במודולו שתי הקפות. כתובות נמוכות זהות יכולות לציין אפס או עומק מלא.','Subtract read from write modulo two wraps. Equal low addresses can mean either zero occupancy or a full buffer.'),
    ('מצביע מורחב שומר מידע שהכתובת לבדה מאבדת.','An extended pointer preserves information the address alone loses.'),
    'depth modulus write read',[(8,16,8,0),(8,16,0,0),(8,16,1,14),(4,8,0,4),(4,8,6,5)],
    'full equal addresses|empty equal pointers|pointer wrap|full across wrap|one item')
add(278,264,'sequential',('קבלה ראשונה אחרי סנכרון הדגל','First acceptance after flag synchronization'),
    ('בתחילה FIFO ריק, והמסנכרן והדגל תואמים לכך. מצביע הכתיבה הראשונה נלכד בחזית {capture}. יש {stages} אוגרי סנכרון. flag={flag}: דגל empty רשום אם 1, צירופי אם 0. בקשת קריאה קבועה; אין מטא־יציבות. באיזו חזית תתקבל קריאה ראשונה?',
     'Initially FIFO, synchronizer and flag indicate empty. The first write pointer captures at edge {capture}, through {stages} synchronizer registers. flag={flag}: empty is registered if 1, combinational if 0. Read request stays high; no metastability. At which edge is the first read accepted?'),
    ('הביט מגיע לשלב האחרון אחרי stages−1 חזיתות נוספות. דגל רשום מוסיף חזית, והקבלה משתמשת בדגל שכבר היה בתוקף לפני החזית.','The pointer reaches the last stage after stages−1 further edges. A registered flag adds an edge; acceptance uses the flag established before its edge.'),
    ('מספר שלבי סנכרון אינו לבדו השהיית פעולת הממשק.','Synchronizer depth alone is not the interface-operation latency.'),
    'capture stages flag',[(1,2,1),(1,2,0),(3,2,1),(2,3,1),(4,3,0)],
    'registered empty|combinational empty|late successful capture|three stages|late three-stage combinational',4)
add(279,264,'bits',('דגימות גריי מדלגות אינן שכנות','Skipped Gray samples need not be neighbors'),
    ('מונה בינארי התקדם מ־{a} ל־{b}. המקלט ראה רק את קודי הגריי בשני הקצוות, g=binary XOR (binary>>1). כמה ביטים שונים בין הדגימות?',
     'A binary counter advanced from {a} to {b}. A receiver saw only the endpoint Gray codes, g=binary XOR (binary>>1). How many bits differ between the samples?'),
    ('ממירים כל קצה לגריי ואז סופרים הבדלים. ההבטחה לשינוי ביט יחיד חלה על צעדים סמוכים, ולא על כל זוג דגימות מדלגות.','Convert both endpoints to Gray, then count differences. The one-bit guarantee applies to adjacent advances, not every pair of skipped samples.'),
    ('תקינות כל מעבר אינה מגבילה מרחק בין תצפיות רחוקות.','Valid individual transitions do not bound the distance between separated observations.'),
    'a b',[(0,2),(3,4),(0,7),(5,5),(1,6)],
    'skip one count|binary carry boundary|long skip|no advancement|three changed bits')
add(280,264,'sequential',('מצביע ישן מקטין מקום זמין לכאורה','A stale pointer understates free space'),
    ('FIFO בעומק {depth}: מונה כתיבות {write}, קריאות בפועל {actual_read}, וקריאות שנצפו בסנכרון {seen_read}. אין הקפה בדוגמה. כמה מקומות פנויים הצד הכותב מחשב מהמצביע שנצפה?',
     'A depth-{depth} FIFO has write count {write}, actual read count {actual_read}, and synchronized observed read count {seen_read}. No counter wrap occurs. How many free slots does the writer calculate from the observed pointer?'),
    ('התפוסה הנצפית היא write−seen_read; מחסרים אותה מהעומק. קריאות שטרם נצפו אינן מפנות מקום מבחינת הכותב.','Observed occupancy is write−seen_read; subtract it from depth. Unobserved reads do not yet free space for the writer.'),
    ('דגל שמרני עשוי לדחות פעולה חוקית בלי לפגוע בנתונים.','A conservative flag may delay a legal operation while preserving data.'),
    'depth write actual_read seen_read',[(8,8,2,0),(8,8,2,2),(8,5,5,3),(4,4,4,0),(4,3,0,0)],
    'stale full|caught up|actual empty observed occupied|full versus actual empty|no stale reads')
add(281,279,'sequential',('חלון עדכני מפנה גם מקסימום ישן','A recent window evicts an old maximum'),
    ('ערכים התקבלו לפי הסדר {samples}. מחזיקים רק את שלושת האחרונים ומציגים בסדר יורד. מה הפלט [מקסימום,אמצעי,מינימום]?',
     'Values were accepted in order {samples}. Keep only the latest three and display them descending. What is [maximum,middle,minimum]?'),
    ('מוחקים כל ערך שקדם לשלושת האחרונים, ואז ממיינים עותק של החלון. אין לשמור שיא היסטורי במקום היסטוריית קבלה.','Discard values before the latest three, then sort a copy of that window. A historical record cannot replace arrival history.'),
    ('שמירת היסטוריה ומיון הפלט הן שתי פעולות נפרדות.','History retention and output sorting are separate operations.'),
    'samples',[([3,1,2,0],),([0,1,2],),([2,2,1,2],),([3,3,3,0,0,0],),([0,3,1,3,2],)],
    'evict old maximum|first full window|retain duplicates|complete replacement|repeated maximum')
add(282,279,'gates',('אמצע אינו הערך השני השונה','The middle is not the second distinct value'),
    ('שלושה נתונים הם {samples}. ממיינים אותם בלי למחוק כפילויות. מה הערך האמצעי?',
     'Three data values are {samples}. Sort them without removing duplicates. What is the middle value?'),
    ('החציון הוא האיבר במיקום השני אחרי מיון של כל שלוש ההופעות. כפילויות הן נתונים אמיתיים.','The median is the second position after sorting all three occurrences. Duplicates remain real data.'),
    ('מיון שומר ריבוי הופעות ואינו יוצר קבוצת ערכים ייחודיים.','Sorting preserves multiplicity instead of forming a set of distinct values.'),
    'samples',[([2,2,0],),([3,0,1],),([1,1,1],),([0,3,3],),([2,1,0],)],
    'duplicated maximum|unordered distinct|all equal|duplicated maximum with zero|descending distinct')
add(283,279,'sequential',('אפסי איפוס אינם דגימות','Reset zeros are not received samples'),
    ('מונה מילוי לחלון שלושה מתחיל ב־0. זוגות [reset,valid] הם {rv}; reset גובר, valid מגדיל עד רוויה ב־3. מה המונה הסופי?',
     'A three-sample fill counter starts at 0. [reset,valid] pairs are {rv}; reset overrides valid, otherwise valid increments up to 3. What is the final count?'),
    ('סופרים רק קבלות מאז האיפוס האחרון. איפוס פוסל היסטוריה, ומחזור ללא valid אינו ממלא תא חדש.','Count only acceptances since the most recent reset. Reset invalidates history; a cycle without valid fills no new entry.'),
    ('תוקף היסטוריה אינו נובע מערכי הנתונים באוגרים.','History validity cannot be inferred from register data values.'),
    'rv',[([[0,1],[0,0],[0,1]],),([[0,1],[0,1],[0,1],[0,1]],),([[0,1],[1,1]],),([[1,0],[0,1],[0,1],[0,1]],),([[0,0],[0,0]],)],
    'bubble|saturation|reset priority|refill after reset|no acceptance')
add(284,279,'gates',('שני משווים כבר קובעים את המקסימום','Two comparators already place the maximum'),
    ('מתחילים ב־[a,b,c]={samples}. מחליפים a,b אם a>b, ואז b,c אם b>c. לפני ההשוואה השלישית, מה [a,b,c]?',
     'Start with [a,b,c]={samples}. Swap a,b if a>b, then b,c if b>c. Before the third comparison, what is [a,b,c]?'),
    ('ההשוואה הראשונה מעלה את הגדול מהזוג למרכז; השנייה מעלה את הגדול מהשלושה לסוף. שני הראשונים עדיין עשויים להיות הפוכים.','The first comparison moves the pair maximum to the middle; the second moves the overall maximum to the end. The first two may remain reversed.'),
    ('אינווריאנט ביניים מסביר למה דרוש שלב מיון נוסף.','An intermediate invariant explains why another sorting stage is needed.'),
    'samples',[([3,2,1],),([0,1,2],),([2,0,3],),([1,3,0],),([2,2,1],)],
    'third comparator needed|already sorted|first swap only|second swap only|equal pair')
add(285,279,'gates',('השוואה מחמירה אינה מבטיחה מיון יציב','Strict comparison does not guarantee stable sorting'),
    ('ערכים {values} נושאים תגיות {tags}. רשת ממיינת משווה (0,2), אחר כך (0,1), ואז (1,2), ומחליפה רק כשהערך השמאלי גדול. מה סדר התגיות הסופי?',
     'Values {values} carry tags {tags}. A sorting network compares (0,2), then (0,1), then (1,2), swapping only when the left value is greater. What is the final tag order?'),
    ('מחליפים נתון ותגית יחד לפי שלושת הזוגות. החלפה לא סמוכה יכולה להעביר פריט שווה מעבר לחברו בלי להשוות ביניהם בשוויון.','Swap values with their tags through all three pairs. A nonadjacent swap can move equal items past one another without directly swapping an equal pair.'),
    ('יציבות תלויה גם במבנה הרשת ולא רק בתנאי ההחלפה.','Stability depends on network structure as well as the swap condition.'),
    'values tags',[([2,2,1],[0,1,2]),([1,1,1],[0,1,2]),([3,2,1],[0,1,2]),([1,2,1],[0,1,2]),([1,2,2],[0,1,2])],
    'nonadjacent equal-order reversal|all equal hold|reverse distinct|equal minima preserved|sorted equal maxima')
add(286,280,'sequential',('השלב האיטי קובע את תקופת הצינור','The slowest stage sets the pipeline period'),
    ('השהיות השלבים הן {delays}ns. לכל מסלול מוסיפים overhead={overhead}ns הכולל תקורת אוגרים ואי־ודאות; אין skew. מה תקופת השעון המזערית במודל?',
     'Stage delays are {delays}ns. Every path adds overhead={overhead}ns for registers and uncertainty; there is no skew. What is the minimum clock period in this model?'),
    ('כל שלב חייב להסתיים בתקופה אחת. לכן בוחרים את ההשהיה המרבית ומוסיפים תקורה פעם אחת.','Every stage must finish within one period. Choose the maximum stage delay and add overhead once.'),
    ('חלוקת עבודה אינה מבטיחה שלבים מאוזנים.','Partitioning work does not guarantee balanced stages.'),
    'delays overhead',[([2,1,3,2],1),([2,2,2],0),([0,0,0],1),([7],2),([1,1,9,1,1],1)],
    'unequal stages|balanced zero overhead|register-limited|single stage|dominant bottleneck')
add(287,280,'sequential',('מרווח התנעה קובע זמן אצווה','Initiation interval determines batch time'),
    ('צינור ריק מעבד {count} פריטים. הראשון מסתיים אחרי {latency} מחזורים; קבלות נוספות מופרדות ב־II={ii} מחזורים, ללא תקיעות. כמה מחזורים נדרשים עד סוף האצווה? אצווה ריקה דורשת אפס.',
     'An empty pipeline processes {count} items. The first finishes after {latency} cycles; later acceptances are spaced by II={ii} cycles, without stalls. How many cycles finish the batch? An empty batch needs zero.'),
    ('לפריט הראשון משלמים את כל ההשהיה, ולכל אחד מהבאים רק את מרווח ההתנעה. בריק אין מילוי צינור.','Pay full latency for the first item and one initiation interval for each later item. An empty batch does not fill the pipeline.'),
    ('השהיה וקצב קבלה תורמים בנפרד לזמן אצווה.','Latency and acceptance rate contribute separately to batch time.'),
    'count latency ii',[(4,5,1),(0,5,1),(1,5,2),(4,6,2),(3,3,3)],
    'overlapped batch|empty|single item|slower initiation|no overlap')
add(288,280,'sequential',('האצה תלויה גם בגודל האצווה','Speedup also depends on batch size'),
    ('השהיות פעולות הן {delays}ns. ללא צינור כל פריט עולה סכומן. בצינור: שלב לכל פעולה, תקופה=max, ללא תקורה, II=1. עבור {count} פריטים, מה יחס זמן ללא צינור לזמן עם צינור?',
     'Operation delays are {delays}ns. Unpipelined time per item is their sum. The pipeline has one stage per operation, period=max, zero overhead, II=1. For {count} items, what is unpipelined time divided by pipelined time?'),
    ('זמן רגיל הוא מספר פריטים כפול סכום השהיות. זמן הצינור כולל מילוי: (מספר שלבים+פריטים−1) כפול ההשהיה המרבית.','Ordinary time is count times summed delays. Pipeline time includes filling: (stages+count−1) times the maximum delay.'),
    ('צינור יכול לשפר תפוקה בלי לשפר זמן של פריט יחיד.','A pipeline can improve throughput without improving single-item latency.'),
    'delays count',[([2,2,2],4),([2,2,2],1),([1,5,1],2),([3],5),([1,1,1,1],9)],
    'balanced batch|single item|imbalance slowdown|one stage|longer batch',4)
add(289,280,'sequential',('הקפאה עוצרת התקדמות של פריט','A freeze stops an item advancing'),
    ('פריט מוצע לפני מחזור 1 לצינור בן {stages} שלבים. במחזורים {stalls} יש הקפאה מלאה; באחרים הוא מתקדם שלב אחד, כולל קבלה לשלב הראשון. באיזו חזית הוא מסיים?',
     'An item is offered before cycle 1 to a {stages}-stage pipeline. Cycles {stalls} globally freeze it; other cycles advance one stage, including acceptance into stage one. At which edge does it complete?'),
    ('סופרים רק מחזורים ללא הקפאה עד שמצטבר מספר השלבים. תקיעה אחרי ההשלמה אינה משנה אותה.','Count only unfrozen cycles until the stage count is reached. A stall after completion has no effect.'),
    ('מספר חזיתות שחלפו אינו תמיד מספר שלבי העיבוד שהושלמו.','Elapsed edges need not equal completed processing stages.'),
    'stages stalls',[(3,[2]),(3,[]),(3,[1,2]),(2,[5]),(4,[2,4,5])],
    'middle stall|no stall|acceptance delayed|stall after completion|separated freezes')
add(290,280,'sequential',('שלב איטי מגביל קצב יציב','A slow stage bounds steady throughput'),
    ('שלבים בצינור מסוגלים להתחיל פריט חדש כל {ii} מחזורים בהתאמה. יש אגירה מספקת, תזמון תואם ואין תלות נתונים. מה מרווח ההתנעה המזערי בקצב יציב?',
     'Pipeline stages can start a new item every {ii} cycles respectively. Buffering is sufficient, scheduling is compatible, and there are no data dependencies. What is the minimum steady-state initiation interval?'),
    ('כל פריט עובר בכל שלב. לכן הקצב אינו יכול לעבור את קצב השלב בעל מרווח ההתנעה הגדול ביותר.','Every item visits every stage. The rate cannot exceed the stage with the largest initiation interval.'),
    ('אוגרים אינם מבטלים מגבלת קצב של יחידת חישוב.','Registers cannot eliminate a computation unit’s rate limit.'),
    'ii',[([1,3,1],),([1,1,1],),([2,2],),([5],),([1,2,4,3],)],
    'one bottleneck|fully pipelined|equal bottlenecks|single unit|several rates')
add(291,292,'states',('אותו פלט יכול להסתיר שני מצבים','The same output can hide two states'),
    ('מחזור הפלט הוא 0,1,2,1. בשני מצבי 1, up פירושו שהקודם היה 0; down פירושו שהקודם היה 2. למקרים {directions}, מה רשימת הפלטים הבאים?',
     'The output cycle is 0,1,2,1. In output-one states, up means the preceding output was 0; down means it was 2. For cases {directions}, what is the list of next outputs?'),
    ('מצב 1 בעלייה ממשיך ל־2; מצב 1 בירידה ממשיך ל־0. איחודם היה מאבד את המידע הנדרש לצעד הבא.','The ascending one continues to two; the descending one continues to zero. Merging them loses information needed for the next step.'),
    ('ממזגים מצבים לפי התנהגות עתידית ולא לפי פלט יחיד.','Merge states by future behavior, not one current output.'),
    'directions',[(['up','down'],),(['down'],),(['up'],),(['up','up','down'],),(['down','up','down'],)],
    'distinguishable pair|descending phase|ascending phase|repeated ascending state|alternating contexts')
add(292,292,'states',('פאזה פנימית קובעת את ההמשך','Internal phase determines what follows'),
    ('ארבע פאזות 0,1,2,3 מפיקות בהתאמה 0,1,2,1, ומתקדמות במחזור. מתחילים בפאזה {phase}. מה הפלט אחרי {edges} חזיתות?',
     'Phases 0,1,2,3 output 0,1,2,1 respectively and advance cyclically. Start at phase {phase}. What is the output after {edges} edges?'),
    ('מקדמים את הפאזה מודולו ארבע ורק אז ממפים לפלט. הפלט 1 לבדו אינו מספר מצב חד־משמעי.','Advance phase modulo four, then map to output. Output one alone is not an unambiguous state number.'),
    ('תקופת המצב עשויה להיות גדולה ממספר ערכי הפלט.','State period can exceed the number of output values.'),
    'phase edges',[(1,1),(3,1),(0,4),(2,0),(3,6)],
    'ascending one|descending one|whole period|no edge|multiple wraps')
add(293,292,'sequential',('סופרים ביקורים בפלט משותף','Count visits to a shared output'),
    ('המחזור 0,1,2,1 מתחיל בפלט 0 לפני הספירה. מתוך {edges} החזיתות הבאות, אחרי כמה חזיתות הפלט הוא 1?',
     'The cycle 0,1,2,1 starts at output 0 before counting. Across the next {edges} edges, after how many is the output 1?'),
    ('הפלט 1 מופיע אחרי החזיתות האי־זוגיות. שני מצבים שונים תורמים לאותו ערך פלט.','Output one occurs after odd-numbered edges. Two distinct states contribute to that output value.'),
    ('תדירות ערך פלט תלויה במספר ביקוריו במחזור.','An output value’s frequency depends on its visits per cycle.'),
    'edges',[(7,),(0,),(1,),(4,),(10,)],'partial period|zero observations|first edge|one period|multiple periods')
add(294,301,'states',('אירוע נדחה אינו משנה תפוסה','A rejected event leaves occupancy unchanged'),
    ('קיבולת {capacity}, תפוסה התחלתית {initial}. אירועים {events}: 1 כניסה, ‎-1 יציאה, 0 המתנה, 2 לא חוקי. כניסה במלא ויציאה בריק נדחות. מה [תפוסה סופית,מספר דחיות]?',
     'Capacity is {capacity}, initial occupancy {initial}. Events {events}: 1 entry, -1 exit, 0 idle, 2 invalid. Entry at full and exit at empty are rejected. What is [final occupancy,rejection count]?'),
    ('מעדכנים רק באירוע חוקי שמשאיר תפוסה בתחום. אירוע שנדחה נספר פעם אחת ואינו משנה את המצב.','Update only for legal events that keep occupancy in range. Each rejection counts once and leaves state unchanged.'),
    ('זיהוי אירוע פסול ועדכון מצב צריכים להשתמש באותו מצב ישן.','Rejection detection and state update must use the same old state.'),
    'capacity initial events',[(3,0,[-1,1,1]),(3,3,[1,-1,1]),(2,1,[2,0,-1]),(1,0,[1,1,-1,-1]),(3,2,[-1,-1,1])],
    'empty rejection|full rejection|invalid code and idle|both bounds|all accepted')
add(295,301,'states',('רצף יציאות מבחין בין שתי תפוסות','An exit sequence distinguishes occupancies'),
    ('מנורה דולקת בדיוק כשיש אנשים. השוו תפוסות {lower} ו־{upper}, כאשר {lower} קטנה יותר. מה מספר היציאות החוקיות המזערי שיכבה רק את התפוסה הקטנה? אפשר גם אפס יציאות.',
     'A lamp is on exactly when occupancy is positive. Compare occupancies {lower} and {upper}, with the former smaller. What minimum number of legal exits turns off only the lower occupancy? Zero exits are allowed.'),
    ('אחרי lower יציאות התפוסה הקטנה אפס והגדולה עדיין חיובית. קודם לכן שתיהן חיוביות, אלא אם lower התחילה באפס.','After lower exits the smaller occupancy is zero and the larger remains positive. Earlier both are positive unless lower started at zero.'),
    ('רצף המשך שמבדיל פלטים מוכיח שמצבים אינם שקולים.','A continuation that distinguishes outputs proves states inequivalent.'),
    'lower upper',[(1,3),(0,2),(2,3),(3,8),(1,2)],
    'two hidden positive counts|already distinguishable|adjacent high counts|larger capacity|adjacent low counts')
add(296,293,'bits',('גם תוצאת הביניים צריכה רוחב','The intermediate result also needs width'),
    ('x הוא ללא סימן ברוחב {w} ביט. במכפיל 49 שומרים קודם t=3x. מה רוחב t המזערי שמונע גלישה לכל x?',
     'x is an unsigned {w}-bit input. A multiply-by-49 circuit first stores t=3x. What minimum t width prevents overflow for every x?'),
    ('המקסימום הוא שלוש פעמים ערך הקלט המרבי. בוחרים את הרוחב הקטן שהמקסימום נכנס בו.','The maximum is three times the largest input. Choose the smallest width capable of representing it.'),
    ('תוצאה סופית רחבה אינה מתקנת אוגר ביניים צר מדי.','A wide final result cannot repair an undersized intermediate register.'),
    'w',[(10,),(1,),(2,),(4,),(8,)],'ten-bit source|one-bit exception|two-bit carry growth|nibble input|byte input')
add(297,293,'bits',('מאתרים גלישה לפני ההזזה','Locate overflow before the shift'),
    ('מימוש שגוי שומר t=3x רק ב־{w} ביטים, ואז מחשב y=16t+x ברוחב בלתי מוגבל. עבור x={x}, מה y שהמימוש מפיק בפועל?',
     'A faulty implementation stores t=3x in only {w} bits, then computes y=16t+x at unlimited width. For x={x}, what y does it actually produce?'),
    ('חותכים את 3x ברוחב אוגר t לפני ההכפלה ב־16. הביטים שאבדו אינם חוזרים בהרחבת הפלט.','Truncate 3x to t’s register width before multiplying by sixteen. Widening the output does not restore discarded bits.'),
    ('מיקום חיתוך הרוחב משנה את הפונקציה הממומשת.','The location of width truncation changes the implemented function.'),
    'w x',[(4,6),(4,5),(4,0),(4,15),(3,3)],
    'first overflowing product|last fitting product|zero|multiple lost carries|different width')
add(298,293,'gates',('עובדים לאחור מפירוק כפל קבוע','Work backward from a constant multiplier'),
    ('מבנה נתון מחשב y=16t+x ורוצה y={target}x בדיוק. מגדירים t=kx עם k שלם. מה k הדרוש?',
     'A fixed structure computes y=16t+x and requires exact y={target}x. Define t=kx with integer k. What k is needed?'),
    ('משווים מקדמים: 16k+1 חייב להיות מקדם הכפל הרצוי. מחסרים אחד ומחלקים ב־16.','Match coefficients: 16k+1 must equal the desired multiplier. Subtract one, then divide by sixteen.'),
    ('זהות אלגברית מספקת חוזה לכל קלט ולא רק לדוגמה.','An algebraic identity specifies every input, not just an example.'),
    'target',[(49,),(17,),(1,),(33,),(65,)],
    'triple intermediate|wire intermediate|zero intermediate|double intermediate|quadruple intermediate')
add(299,293,'bits',('ארבעת הביטים הנמוכים של פי ארבעים ותשע','The low nibble of forty-nine times input'),
    ('מחשבים y=49x בדיוק עבור x={x}. מה הערך העשרוני של ארבעת הביטים הנמוכים של y?',
     'Compute exact y=49x for x={x}. What is the decimal value of y’s low four bits?'),
    ('49=3·16+1, לכן המכפלה שקולה ל־x מודולו 16. החלק המוזז אינו משנה את הניבל הנמוך.','Since 49=3·16+1, the product equals x modulo sixteen. The shifted term cannot change the low nibble.'),
    ('שארית של קבוע כפל יכולה לחשוף חיווט ישיר.','A multiplier constant’s residue can reveal direct wiring.'),
    'x',[(13,),(0,),(16,),(31,),(1023,)],
    'ordinary nibble|zero|nibble wrap|higher bits ignored|maximum ten-bit input')
add(300,293,'bits',('החלק העליון הוא מנה ולא ביט נשא יחיד','The upper part is a quotient, not one carry'),
    ('מחשבים y=49x בדיוק, כאשר x={x} הוא קלט ללא סימן ברוחב {w}. זורקים את {w} הביטים הנמוכים של y. מה ערך החלק שנותר?',
     'Compute exact y=49x with unsigned {w}-bit input x={x}. Discard y’s lowest {w} bits. What is the remaining upper part’s value?'),
    ('הסרת הביטים הנמוכים היא חלוקה שלמה ב־2 בחזקת הרוחב. החלק העליון עשוי להיות גדול מאחד.','Removing low bits is integer division by two to the width. The upper part may be larger than one.'),
    ('כפל בקבוע עשוי לייצר כמה ביטי הרחבה.','Constant multiplication may produce multiple extension bits.'),
    'w x',[(4,15),(4,0),(4,1),(10,1023),(10,20)],
    'many upper bits|zero|small input carry|full-scale input|below first carry')
add(301,290,'electronics',('שלושה חיבורים לצמתים שווי־פוטנציאל','Three connections to equipotential nodes'),
    ('בצמצום קוביית נגדים, שלושת השכנים של הקודקוד המוזן שווי־פוטנציאל. שלושת הנגדים אליו הם {r}Ω כל אחד. מה התנגדות קבוצת הקצה השקולה באוהם?',
     'In a resistor-cube reduction, the three neighbors of the driven vertex are equipotential. Its three connecting resistors are {r}Ω each. What is this endpoint group’s equivalent resistance in ohms?'),
    ('שלושת הנגדים רואים אותו הפרש מתח ולכן הם במקביל. המוליכויות מסתכמות, וההתנגדות היא R/3.','All three resistors see the same voltage difference, so they are parallel. Conductances add, giving resistance R/3.'),
    ('מיזוג צמתים דורש שוויון פוטנציאלים מוכח.','Merging nodes requires justified equal potentials.'),
    'r',[(3,),(1,),(6,),(9,),(12,)],
    'integral equivalent|unit edge|scaled cube|larger edge|inverse current interpretation')
add(302,290,'electronics',('סופרים צלעות בין שכבות קובייה','Count cube edges between vertex layers'),
    ('קודקודי קובייה מממד {dimension} מסומנים במילים בינאריות ברוחב זה. צלע מחברת מילים שנבדלות בביט אחד. כמה צלעות מחברות שכבה עם {layer} אחדים לשכבה עם אחד נוסף?',
     'Vertices of a {dimension}-dimensional cube are labeled by binary words of that width. An edge joins words differing in one bit. How many edges join the layer with {layer} ones to the layer with one more?'),
    ('בוחרים את מיקומי האחדים בקודקוד התחתון; מכל קודקוד אפשר להעלות כל ביט אפס. כל צלע כזו נספרת פעם אחת.','Choose the one positions of a lower vertex; each zero bit can be raised. Every such edge is counted once.'),
    ('סופרים צלעות בין שכבות, לא צמתים בכל שכבה.','Count edges between layers, not vertices in each layer.'),
    'dimension layer',[(3,1),(3,0),(3,2),(4,1),(2,1)],
    'cube middle edges|source layer|destination layer|four-dimensional extension|square boundary')
add(303,290,'electronics',('הקבוצות המצומצמות מתחברות בטור','The reduced groups connect in series'),
    ('במודל הקובייה בין קודקודים נגדיים, שלוש קבוצות בטור הן R/3, R/6, R/3. כל צלע מקורית R={r}Ω. מה ההתנגדות הכוללת באוהם?',
     'A cube between opposite vertices reduces to three series groups R/3, R/6, R/3. Each original edge has R={r}Ω. What is the total resistance in ohms?'),
    ('בכל קבוצה עובר הזרם הכולל, ולכן סכום ההתנגדויות הוא 5R/6. אין לחבר את שלוש הקבוצות במקביל.','The same total current crosses each group, so their resistances sum to 5R/6. The three groups are not parallel.'),
    ('לאחר צמצום סימטריה עדיין צריך לזהות נכון טור ומקביל.','After symmetry reduction, series and parallel connections still matter.'),
    'r',[(6,),(1,),(12,),(3,),(18,)],
    'integral total|unit-resistor cube|double edge resistance|fractional total|larger scale')
add(304,294,'electronics',('משלימים יחס בגשר מאוזן','Complete a balanced bridge ratio'),
    ('גשר DC עם מקור לא אפס: R1 מעל R2 משמאל, R3 מעל R4 מימין. R1={r1}, R2={r2}, R3={r3} בקילו־אוהם. איזה R4 יבטיח אפס זרם בין האמצעים?',
     'A DC bridge has nonzero supply: R1 above R2 on the left, R3 above R4 on the right. R1={r1}, R2={r2}, R3={r3} kiloohms. What R4 makes midpoint current zero?'),
    ('משווים יחסי מחלקים: R1/R2=R3/R4. לכן R4=R2·R3/R1; נגד הגישור אינו משנה את תנאי האיזון.','Equate divider ratios: R1/R2=R3/R4. Thus R4=R2·R3/R1; bridge-link resistance does not change the balance condition.'),
    ('איזון הוא שוויון יחסים ולא בהכרח שוויון ארבעת הנגדים.','Balance requires equal ratios, not necessarily four equal resistors.'),
    'r1 r2 r3',[(1,2,3),(2,2,5),(4,1,2),(3,6,1),(5,1,5)],
    'scaled branches|equal midpoint halves|fractional resistor|inverted size ordering|matching top resistors')
add(305,294,'electronics',('ההתנגדות שהנגד המגשר רואה','The resistance seen by the bridge link'),
    ('מסירים את נגד הגישור ומקצרים מקור מתח אידאלי. זרועות הגשר הן R1={r1}, R2={r2}, R3={r3}, R4={r4}Ω. מה התנגדות תבנין בין שני האמצעים?',
     'Remove the bridge-link resistor and short the ideal voltage source. Bridge arms are R1={r1}, R2={r2}, R3={r3}, R4={r4}Ω. What is the Thevenin resistance between the midpoints?'),
    ('בכל צד שני הנגדים במקביל אל הצומת המשותף; בין האמצעים שתי השקולות בטור. התוצאה R1||R2 + R3||R4.','Each side has two resistors in parallel to the common node; those equivalents are series between midpoints. The result is R1||R2 + R3||R4.'),
    ('איפוס מקור משנה את החיבורים לצורך התנגדות תבנין.','Deactivating a source changes connections for Thevenin-resistance calculation.'),
    'r1 r2 r3 r4',[(2,2,4,4),(1,1,1,1),(2,6,3,3),(3,6,6,3),(1,3,2,6)],
    'different symmetric sides|fully equal bridge|unbalanced arms|mirrored arms|fractional parallels',4)
add(306,297,'electronics',('יחס המשוב קובע הגבר לא מהפך','Feedback ratio sets non-inverting gain'),
    ('מגבר שרת אידאלי בתחום הליניארי: Vin בכניסת הפלוס, Rf={rf}kΩ מהפלט למינוס ו־Rg={rg}kΩ מהמינוס לאדמה. מה Vout/Vin?',
     'An ideal op-amp operates linearly: Vin drives plus, Rf={rf}kΩ connects output to minus, and Rg={rg}kΩ connects minus to ground. What is Vout/Vin?'),
    ('אין זרם כניסה, ולכן Vminus=Vout·Rg/(Rf+Rg). משוב שלילי מציב Vminus=Vin ומתקבל 1+Rf/Rg.','With zero input current, Vminus=Vout·Rg/(Rf+Rg). Negative feedback gives Vminus=Vin, hence gain 1+Rf/Rg.'),
    ('שוויון מתחי הכניסה דורש משוב שלילי ופעולה ליניארית.','Equal input voltages require negative feedback and linear operation.'),
    'rf rg',[(10,10),(0,10),(30,10),(5,20),(20,5)],
    'equal resistors|ideal follower wire|gain four|fractional gain|large feedback ratio')
add(307,297,'electronics',('הגבר פתוח סופי מקטין הגבר סגור','Finite open-loop gain reduces closed-loop gain'),
    ('במודל מגבר: Vout=A(Vin−Vout/{den}), A={a}, ללא רוויה. מה ההגבר הסגור Vout/Vin?',
     'An amplifier model obeys Vout=A(Vin−Vout/{den}), with A={a}, without saturation. What is closed-loop gain Vout/Vin?'),
    ('מעבירים את איבר המשוב לאגף שמאל. מתקבל A/(1+A/den), קטן מהגבול האידאלי den עבור A חיובי.','Move the feedback term to the left. Gain is A/(1+A/den), below ideal limit den for positive A.'),
    ('הקירוב האידאלי הוא גבול של משוואת משוב סופית.','The ideal approximation is a limit of a finite-feedback equation.'),
    'a den',[(18,2),(2,2),(0,2),(99,1),(12,4)],
    'near ideal|weak open-loop gain|zero amplifier gain|follower error|different feedback fraction')
add(308,297,'electronics',('זרם הטיה יוצר מפל בנגד הכניסה','Bias current creates an input-resistor drop'),
    ('זרם הטיה {ib}µA זורם מהמקור דרך נגד {r}kΩ אל כניסת הפלוס. מה Vsource−Vplus במיליוולט? סימן שלילי מציין זרם בכיוון ההפוך.',
     'Bias current {ib}µA flows from the source through {r}kΩ into the plus input. What is Vsource−Vplus in millivolts? A negative current denotes the reverse direction.'),
    ('חוק אוהם נותן I·R, ביחידות µA כפול kΩ שהן mV. סימן הזרם קובע את סימן המפל.','Ohm’s law gives I·R; µA times kΩ is mV. Current direction determines the voltage-drop sign.'),
    ('נגד כניסה חסר מפל רק במודל זרם כניסה אפס.','An input resistor has no drop only under a zero-input-current model.'),
    'ib r',[(2,10),(0,100),(1,0),(-3,4),(5,2)],
    'finite bias|ideal input|direct connection|reversed bias|same drop different pair')
add(309,297,'electronics',('המסילה קוטמת את הבקשה הליניארית','The rail clips the linear request'),
    ('מודל הוראה: פלט מגבר הוא gain·Vin, נקטם לתחום [{low},{high}]V. gain={gain}, Vin={vin}V. מה הפלט? זהו מודל קיטום מפורש, לא מפרט רכיב.',
     'Teaching model: amplifier output is gain·Vin, clipped to [{low},{high}]V. gain={gain}, Vin={vin}V. What is the output? This explicit clipping model is not a device specification.'),
    ('מחשבים את הבקשה הליניארית ואז מגבילים למסילה הנמוכה או הגבוהה אם צריך. בתוך התחום אין קיטום.','Compute the linear request, then limit it to the low or high rail if necessary. Inside the range no clipping occurs.'),
    ('נוסחת הגבר ליניארי לבדה אינה מתירה פלט מעבר למסילות.','A linear-gain formula alone cannot justify output beyond the rails.'),
    'gain vin low high',[(2,3,-5,5),(2,-3,-5,5),(2,1,-5,5),(3,0,1,8),(2,2,-4,4)],
    'upper saturation|lower saturation|linear interior|asymmetric rails|exact rail')
add(310,222,'electronics',('כניסת DC לאינטגרטור יוצרת שיפוע','A DC integrator input creates a slope'),
    ('אינטגרטור מהפך אידאלי וליניארי מקבל Vin={vin}V, עם RC={rc}ms. מה dVout/dt בוולט למילישנייה?',
     'An ideal linear inverting integrator has Vin={vin}V and RC={rc}ms. What is dVout/dt in volts per millisecond?'),
    ('זרם הנגד טוען את קבל המשוב כך ש־dVout/dt=−Vin/(RC). סימן הכניסה מתהפך בשיפוע.','Resistor current charges the feedback capacitor, giving dVout/dt=−Vin/(RC). Input sign is inverted in the slope.'),
    ('קלט קבוע לאינטגרטור אינו יוצר בהכרח פלט קבוע.','A constant integrator input need not produce a constant output.'),
    'vin rc',[(2,4),(-3,2),(0,5),(1,1),(-4,8)],
    'negative ramp|positive ramp|hold ideal charge|unit slope|fractional positive slope')
add(311,222,'electronics',('שטח הכניסה מעדכן את מתח האינטגרטור','Input area updates the integrator voltage'),
    ('Vout התחלתי {start}V, RC={rc}ms. מקטעי כניסה [מתח בוולט,משך במילישניות] הם {segments}. אינטגרטור מהפך אידאלי ללא רוויה: מה הפלט הסופי?',
     'Initial Vout is {start}V, RC={rc}ms. Input segments [volts,milliseconds] are {segments}. For an ideal inverting integrator without saturation, what is final output?'),
    ('מחסרים מהמתח ההתחלתי את סכום שטחי מתח־זמן חלקי RC. מקטעים בעלי סימנים מנוגדים יכולים לבטל זה את זה.','Subtract summed voltage-time areas divided by RC from the initial voltage. Opposite-sign segments can cancel.'),
    ('האינטגרטור שומר גם תנאי התחלה, לא רק שטח חדש.','An integrator retains its initial condition as well as new area.'),
    'start rc segments',[(1,2,[[2,1],[0,3]]),(0,1,[[2,1],[-1,2]]),(3,2,[[0,5]]),(-1,4,[[-2,3]]),(2,3,[[1,2],[2,2]])],
    'input then hold|cancelling area|nonzero initial charge|negative input|fractional final state')
add(312,307,'electronics',('שגיאת RC דועכת ולא המתח כולו','RC error decays, not the whole voltage'),
    ('פער מתח מהערך הסופי מתחיל ב־{initial_error}mV. חלפו {halvings} פרקי זמן, כל אחד RC·ln(2). מה פער המתח שנותר במודל RC מסדר ראשון?',
     'Voltage error relative to the final value starts at {initial_error}mV. After {halvings} intervals of RC·ln(2) each, what error remains in the first-order RC model?'),
    ('כל פרק זמן מחלק את הפער בשתיים. מפעילים את הדעיכה על ההפרש מהערך הסופי ולא בהכרח על המתח עצמו.','Each interval halves the error. Decay applies to the difference from the final value, not necessarily the voltage itself.'),
    ('פתרון מעבר נבנה מערך סופי ועוד שגיאה דועכת.','A transient solution combines a final value with a decaying error.'),
    'initial_error halvings',[(800,3),(0,4),(100,0),(-80,2),(1,3)],
    'three half-lives|already settled|initial instant|approach from above|fractional error')
add(313,307,'electronics',('ייחוס משווה מתוך מחלק מתח','Comparator reference from a divider'),
    ('מקור {vs}V מזין נגד עליון {top}kΩ ונגד תחתון {bottom}kΩ לאדמה. כניסת המשווה אינה צורכת זרם. מה מתח נקודת האמצע?',
     'A {vs}V source feeds a {top}kΩ top resistor and a {bottom}kΩ bottom resistor to ground. The comparator input draws no current. What is midpoint voltage?'),
    ('זרם המחלק הוא Vs/(Rtop+Rbottom); כופלים בנגד התחתון. החלפת שני הנגדים משנה את הסף.','Divider current is Vs/(Rtop+Rbottom); multiply by the bottom resistor. Swapping resistors changes the threshold.'),
    ('סף יחיד אינו יוצר היסטרזיס בלי מנגנון זיכרון נוסף.','One threshold does not create hysteresis without an additional memory mechanism.'),
    'vs top bottom',[(3,10,20),(3,20,10),(5,10,10),(0,1,2),(2,3,1)],
    'two-thirds threshold|reversed ratio|half supply|zero source|quarter supply')
add(314,260,'electronics',('משוואת דיודה כוללת גם מינוס אחד','The diode equation includes minus one'),
    ('מודל דיודה אידאלי: I/Is=exp(V/(ηVT))−1. נבחר V={k}·ηVT·ln(2). מה I/Is? אין פריצה או התנגדות טורית במודל.',
     'Ideal diode model: I/Is=exp(V/(ηVT))−1. Set V={k}·ηVT·ln(2). What is I/Is? The model excludes breakdown and series resistance.'),
    ('האקספוננט נותן 2 בחזקת k, ואז מחסרים אחד. באפס מתח הזרם נטו אפס; במתח שלילי הוא שלילי.','The exponential becomes two to power k, then subtract one. At zero voltage net current is zero; negative voltage gives negative current.'),
    ('מודל אקספוננציאלי אינו מתג בעל מתח הפעלה קשיח.','An exponential model is not a switch with a hard turn-on voltage.'),
    'k',[(2,),(0,),(1,),(-1,),(-3,)],
    'forward exponential|equilibrium|small forward bias|reverse bias|approaching reverse limit')
add(315,260,'electronics',('מחסור נשאים מתפשט יותר בצד המדולל','Depletion extends farther into the lighter-doped side'),
    ('בצומת חד מתקיים NA·xp=ND·xn. ריכוזים באותן יחידות הם NA={na}, ND={nd}. מה היחס xp/xn?',
     'An abrupt junction satisfies NA·xp=ND·xn. Concentrations in the same units are NA={na}, ND={nd}. What is xp/xn?'),
    ('מחלוקת שוויון המטענים מתקבל xp/xn=ND/NA. הצד בעל הריכוז הנמוך צריך רוחב גדול יותר לאותו מטען.','Charge neutrality gives xp/xn=ND/NA. The lower-doped side needs greater width to balance the same charge.'),
    ('שוויון מטען אינו אומר שוויון רוחב בשני הצדדים.','Equal charge does not imply equal widths on both sides.'),
    'na nd',[(1,4),(3,3),(4,1),(2,6),(8,2)],
    'P side wider|symmetric doping|N side wider|nonunit concentrations|fractional ratio')
add(316,310,'electronics',('קצב הממיר מתחלק בין הערוצים','Converter rate is shared among channels'),
    ('ממיר יחיד מבצע {aggregate}kS/s בסריקה אחידה של {channels} ערוצים, ללא המרות מבוזבזות. מה קצב הדגימה לכל ערוץ ב־kS/s?',
     'One converter performs {aggregate}kS/s while uniformly scanning {channels} channels with no wasted conversions. What is each channel’s sampling rate in kS/s?'),
    ('כל ערוץ מקבל המרה אחת בכל סבב. לכן מחלקים את קצב ההמרות הכולל במספר הערוצים.','Each channel gets one conversion per scan, so divide aggregate conversion rate by channel count.'),
    ('בדיקת נייקוויסט נעשית לפי קצב הערוץ ולא קצב הממיר הכולל.','Apply Nyquist to the per-channel rate, not the aggregate converter rate.'),
    'aggregate channels',[(1000,4),(1000,1),(800,4),(1200,3),(1000,8)],
    'four-channel example|single channel|exact twice-bandwidth boundary|different scan length|oversubscribed converter')
add(317,310,'electronics',('סריקה אינה דגימה סימולטנית','Scanning is not simultaneous sampling'),
    ('בסריקה עוקבת, מועד הדגימה של מיקום k הוא k·{slot}ns מתחילת הסבב. מה ההפרש בעל הסימן t({last})−t({first}), בננו־שניות?',
     'In sequential scanning, position k samples at k·{slot}ns from scan start. What is signed t({last})−t({first}), in nanoseconds?'),
    ('מחסרים את מיקומי הדגימה ומכפילים במשך חלון ההמרה. אותו סבב אינו מבטיח אותו רגע.','Subtract scan positions and multiply by the conversion-slot duration. The same scan does not imply the same instant.'),
    ('מדידות הפרש פאזה צריכות להתחשב בהיסט הזמן בין ערוצים.','Phase-difference measurements must account for interchannel sample skew.'),
    'slot first last',[(1000,0,3),(1000,1,1),(500,1,2),(200,0,7),(1000,2,0)],
    'first to last|same position|adjacent channels|long scan|signed reverse comparison')
add(318,310,'bits',('זיכרון רכישה כולל את כל הערוצים','Acquisition storage includes every channel'),
    ('שומרים {samples} דגימות לכל אחד מ־{channels} ערוצים, {bits} ביט לכל דגימה. אריזה צפופה ללא מטא־נתונים; המכפלה מתחלקת בשמונה. כמה בתים נדרשים?',
     'Store {samples} samples per channel for {channels} channels, using {bits} bits per sample. Packing is dense, without metadata; the total is divisible by eight. How many bytes are required?'),
    ('כופלים דגימות, ערוצים ורוחב ביטים, ואז מחלקים בשמונה. אין להחליף ביטים בבתים לפני החשבון.','Multiply samples, channels and bit width, then divide by eight. Do not confuse bits with bytes.'),
    ('חוזה האריזה משנה את עלות הזיכרון של דגימות.','The packing contract changes sample-storage cost.'),
    'samples channels bits',[(100,4,12),(0,4,16),(8,1,1),(5,2,8),(3,4,10)],
    'packed twelve-bit|empty capture|bit packing|byte samples|nonbyte sample width')
add(319,310,'electronics',('דיוק בביטים קובע מספר זמני דעיכה','Bit precision determines settling intervals'),
    ('שגיאת התייצבות מתחילה ב־full-scale ודועכת בחצי כל τ·ln(2). בממיר {bits} ביטים נדרש פער לכל היותר חצי LSB, עם LSB=FS/2^{bits}. מה מספר פרקי הזמן המזערי שנדרש?',
     'Settling error starts at full scale and halves every τ·ln(2). A {bits}-bit converter requires at most half an LSB, with LSB=FS/2^{bits}. What minimum number of these intervals is required?'),
    ('חצי LSB הוא FS/2^(bits+1), ולכן דרושות bits+1 חלוקות בשתיים. זהו מודל דעיכה מסדר ראשון בלבד.','Half an LSB is FS/2^(bits+1), requiring bits+1 halvings. This is only a first-order settling model.'),
    ('הגדלת רזולוציה מחמירה גם את דרישת ההתייצבות.','Increasing resolution also tightens settling requirements.'),
    'bits',[(12,),(1,),(8,),(10,),(16,)],
    'twelve-bit accuracy|one-bit endpoint|byte converter|intermediate precision|high precision')
add(320,310,'bits',('קוד ADC בגבול ובקיטום','ADC codes at boundaries and saturation'),
    ('ממיר אידאלי {bits} ביט: code=floor(V·2^{bits}/FS), נקטם ל־0..2^{bits}−1. V={mv}mV, FS={fs}mV. מה הקוד?',
     'Ideal {bits}-bit converter: code=floor(V·2^{bits}/FS), clipped to 0..2^{bits}−1. V={mv}mV, FS={fs}mV. What is the code?'),
    ('מחשבים את מספר מדרגות ה־LSB השלמות ואז מגבילים לקודים הקיימים. בדיוק ב־FS אין קוד נוסף מעבר למקסימום.','Count complete LSB steps, then clip to available codes. At exactly FS there is no extra code above the maximum.'),
    ('יש להגדיר במפורש כלל כימות, תחום וקיטום.','Specify the quantization rule, range and clipping explicitly.'),
    'bits mv fs',[(3,375,1000),(3,1000,1000),(3,-10,1000),(3,124,1000),(4,500,1000)],
    'exact code threshold|full-scale clamp|negative clamp|below first step|midscale')
add(321,299,'sequential',('תקופה של טבלת גל נמדדת בדגימות','A waveform-table period is measured in samples'),
    ('מחולל קורא מילה אחת בכל דגימה, בקצב {fs}kS/s, וחוזר על הטבלה עבור תדר {fout}kHz. היחס שלם. כמה מילים בטבלת מחזור מלאה?',
     'A generator reads one word per sample at {fs}kS/s and repeats the table for {fout}kHz output. The ratio is integral. How many words form one full-period table?'),
    ('מחזור אחד נמשך 1/fout ובו fs/fout דגימות. זהו מספר מילים; מספר הביטים דורש גם רוחב דגימה.','One period lasts 1/fout and contains fs/fout samples. This counts words; bit storage additionally needs sample width.'),
    ('מפרידים בין תדר דגימה, תדר גל וגודל מילה.','Separate sample rate, waveform frequency and word size.'),
    'fs fout',[(1000,100),(1000,250),(960,30),(1000,1),(800,100)],
    'ten-sample period|four-phase period|power-of-two period|long period|eight-sample period')
add(322,299,'bits',('קיפול כתובות לפי סימטריית רבע גל','Fold addresses using quarter-wave symmetry'),
    ('תקופת סינוס כוללת {period} דגימות. למגניטודה משתמשים ב־q=phase mod (period/2), address=min(q,period/2−q). עבור phase={phase}, מה כתובת המגניטודה?',
     'A sine period contains {period} samples. Magnitude uses q=phase mod (period/2), address=min(q,period/2−q). For phase={phase}, what magnitude address is used?'),
    ('מצמצמים תחילה לחצי המחזור ואז משקפים את החצי היורד. הסימן נקבע בנפרד ואינו כתובת נוספת.','Reduce to the half-period, then reflect its descending half. Sign is handled separately rather than as another magnitude address.'),
    ('סימטריה חוסכת אחסון במחיר לוגיקת כתובת וסימן.','Symmetry saves storage at the cost of address and sign logic.'),
    'period phase',[(10,3),(10,0),(10,5),(10,9),(16,4)],
    'peak between samples|zero phase|half-wave zero|negative-half reflection|integer peak sample')
add(323,299,'bits',('מחזור שלילי מתוך חצי טבלה','Construct the negative half from half a table'),
    ('חצי טבלת גל הוא {first}; התקופה כפולה מאורכו. בחצי השני קוראים אותה כתובת יחסית והופכים סימן, ללא גלישה. עבור phase={phase}, מה הדגימה?',
     'The first half of a waveform table is {first}; period is twice its length. The second half reads the relative address and negates it without overflow. For phase={phase}, what is the sample?'),
    ('הכתובת היא phase מודולו אורך החצי. רק בחצי השני הופכים את הערך, ולכן גם אפס נשאר אפס.','Address is phase modulo half-length. Negate only in the second half, leaving zero unchanged.'),
    ('סימטריית חצי גל דורשת ייצוג שמאפשר גם ערך נגדי.','Half-wave symmetry requires representing each sample’s negative.'),
    'first phase',[([0,3,5,5,3],6),([0,3,5,5,3],0),([0,3,5,5,3],5),([0,3,5,5,3],4),([0,7,0,-7],7)],
    'negative nonzero|initial zero|second-half zero|positive falling sample|negating negative stored value')
add(324,299,'sequential',('הפעלה חלקית מאטה את קצב הפאזה','Partial enable slows phase advancement'),
    ('שעון {clock}kHz, טבלה בת {period} דגימות, ודפוס enable מחזורי {en}. הפאזה מתקדמת רק באחד. מה תדר מחזורי הפאזה הממוצע ב־kHz? ייתכנו רכיבי ספקטרום נוספים בגלל ההחזקה.',
     'Clock is {clock}kHz, table length {period}, and repeated enable pattern is {en}. Phase advances only on one. What is the average phase-cycle rate in kHz? Holding may add spectral components.'),
    ('כופלים את קצב השעון בשיעור החזיתות המופעלות ומחלקים באורך הטבלה. אפס הפעלות מקפיא את הפאזה.','Multiply clock rate by the enabled-edge fraction, then divide by table length. Zero enables freeze phase.'),
    ('תדר שעון לבדו אינו קובע תדר כאשר קיימת הפעלה מותנית.','Clock frequency alone does not set output rate with conditional enables.'),
    'clock period en',[(1000,10,[1,0]),(1000,10,[1,1]),(1000,10,[0,0]),(1200,8,[1,0,0]),(1000,10,[1,1,0,0,0])],
    'half-rate enable|always enabled|frozen phase|one-third enable|uneven burst enables')
add(325,299,'bits',('שומרים גם את קצות רבע המחזור','Store both quarter-wave endpoints'),
    ('סינוס בדגימות כולל N={period} דגימות למחזור, N מתחלק בארבע. מאחסנים במפורש את מגניטודות הפאזות 0 עד N/4 כולל, בלי יצירת אפס בחיווט. כמה מילים בטבלה?',
     'A sampled sine has N={period} samples per period, divisible by four. Explicitly store magnitude phases 0 through N/4 inclusive, without generating zero by wiring. How many table words are needed?'),
    ('הטווח כולל גם אפס וגם את נקודת השיא, ולכן מספר הכתובות הוא N/4+1. ספירת רווחים בלבד מפספסת קצה.','Both zero and the peak are included, so the address count is N/4+1. Counting intervals alone misses an endpoint.'),
    ('חיסכון סימטרי אינו מבטל את ספירת נקודות הקצה.','Symmetry compression still requires endpoint accounting.'),
    'period',[(32,),(4,),(8,),(16,),(64,)],
    'thirty-two phases|smallest quarter grid|three stored magnitudes|five stored magnitudes|larger lookup table')
add(326,302,'electronics',('כמה נתיבי משיכה למעלה מוליכים','Count conducting pull-up paths'),
    ('רשת PMOS במקביל מקבלת מתחי שער בינאריים {gates}. PMOS מוליך רק בשער 0, ובמודל התנגדותו אז {r}kΩ; אחרת מנותק. מה התנגדות המשיכה השקולה בקילו־אוהם?',
     'Parallel PMOS devices have binary gate levels {gates}. Each conducts only for gate 0, with model resistance {r}kΩ; otherwise it is disconnected. What is equivalent pull-up resistance in kiloohms?'),
    ('מזהים שערים באפס ורק אז מסכמים את מוליכויות הנתיבים הפעילים. שער באחד אינו תורם נתיב במודל.','Identify low gates first, then add conductances of active paths. A high gate contributes no conducting path in this model.'),
    ('טבלת אמת לבדה אינה מתארת התנגדות נתיב פעיל.','A truth table alone does not describe active-path resistance.'),
    'gates r',[([0,0],6),([1,0],6),([0,1,0],6),([0,0,0,0],2),([1,1,0],3)],
    'both NAND pullups|one disabled pullup|mixed three-input network|four active devices|only final branch active')
add(327,302,'electronics',('ערימת NMOS מוסיפה התנגדויות','An NMOS stack adds resistances'),
    ('במודל נגדים אידאלי, {series} NMOS מוליכים בטור, כל אחד {r}kΩ. מה התנגדות נתיב המשיכה לאדמה בקילו־אוהם? אין ענף עוקף.',
     'In an ideal resistor model, {series} conducting NMOS devices are in series, each {r}kΩ. What is pull-down path resistance in kiloohms? There is no bypass branch.'),
    ('אותו זרם עובר בכל התקני הטור, ולכן מפלי המתח וההתנגדויות מצטרפים. המודל אינו חישוב זרם MOS פיזיקלי.','The same current crosses every series device, so drops and resistances add. This is not a physical MOS current calculation.'),
    ('מימוש לוגי נכון עדיין דורש בדיקת נתיבים חשמליים.','A correct logic implementation still needs electrical-path analysis.'),
    'series r',[(2,3),(1,3),(3,2),(4,1),(2,0)],
    'two-device stack|single device|longer stack|four devices|ideal-switch limit')
add(328,302,'electronics',('השפעת מתח על הספק דינמי','Voltage affects dynamic power quadratically'),
    ('במודל P=αCV²f, C קבוע. יחס הפעילות הוא {activity_num}/{activity_den}, יחס התדר {freq}, ויחס המתח {voltage_num}/{voltage_den}. מה יחס ההספק החדש לישן?',
     'Use P=αCV²f with constant C. Activity ratio is {activity_num}/{activity_den}, frequency ratio {freq}, and voltage ratio {voltage_num}/{voltage_den}. What is new power divided by old power?'),
    ('מכפילים יחס פעילות, יחס תדר וריבוע יחס מתח. היחסים מתייחסים למודל הספק דינמי בלבד.','Multiply activity ratio, frequency ratio and squared voltage ratio. These ratios describe dynamic power only.'),
    ('הורדת מתח משנה הספק באופן שונה מהורדת תדר.','Voltage reduction affects power differently from frequency reduction.'),
    'activity_num activity_den freq voltage_num voltage_den',[(1,1,2,1,1),(1,1,1,1,2),(1,2,2,1,1),(0,1,2,2,1),(1,2,2,3,2)],
    'double frequency|half voltage|activity offsets frequency|no switching|combined scaling')
add(329,306,'electronics',('פינה מעורבת משפיעה אחרת על עלייה וירידה','Mixed corners affect rise and fall differently'),
    ('מודל מהפך: בפינה {corner} האות הראשונה מתארת NMOS והשנייה PMOS. F נותן השהיה 2ps ו־S נותן 5ps. למעבר פלט {edge}, מה ההשהיה? עלייה דרך PMOS, ירידה דרך NMOS.',
     'In an inverter model, corner {corner} names NMOS first and PMOS second. F gives 2ps delay and S gives 5ps. What delay applies to output {edge}? Rising uses PMOS; falling uses NMOS.'),
    ('בוחרים את סוג הטרנזיסטור שמניע את המעבר ואת האות המתאימה בפינה. אין להחליף בין קצב עלייה לקצב ירידה.','Select the device driving the transition, then its corner letter. Rising and falling speeds need not match.'),
    ('פינת תהליך אינה מספר מהירות יחיד לכל קשת תזמון.','A process corner is not one speed number for every timing arc.'),
    'corner edge',[('FS','rise'),('FS','fall'),('SF','rise'),('SF','fall'),('SS','rise')],
    'slow PMOS mixed corner|fast NMOS mixed corner|fast PMOS mixed corner|slow NMOS mixed corner|both slow')
add(330,306,'sequential',('בונים תקופת שעון מדרישת setup','Build a clock period from setup timing'),
    ('ב־ps: CQmax={cq}, Dmax={data}, setup={setup}, uncertainty={uncertainty}, skew={skew}. skew חיובי פירושו לכידה מאוחרת. מה T המזערי לפי דרישת setup בלבד?',
     'In ps: CQmax={cq}, Dmax={data}, setup={setup}, uncertainty={uncertainty}, skew={skew}. Positive skew means later capture. What is minimum T from setup alone?'),
    ('נדרש CQmax+Dmax ≤ T+skew−setup−uncertainty. מבודדים את T, תוך שמירת סימן ה־skew.','Require CQmax+Dmax ≤ T+skew−setup−uncertainty. Isolate T while retaining the skew sign.'),
    ('תקופת שעון מתקבלת ממסלול ומחוזה לכידה מוגדרים.','Clock period follows a defined path and capture contract.'),
    'cq data setup uncertainty skew',[(100,500,80,20,0),(100,500,80,20,50),(100,500,80,20,-50),(0,0,80,20,0),(120,700,50,0,20)],
    'zero skew|later capture|earlier capture|overhead-only path|different path bound')
add(331,306,'sequential',('כמה השהיה חסרה לתיקון hold','How much delay is missing for hold'),
    ('ב־ps: CQmin={cq}, Dmin={data}, hold={hold}, uncertainty={uncertainty}, skew={skew}. מוסיפים השהיה אידאלית רק לנתון. מה התוספת הלא־שלילית המזערית שמספקת hold?',
     'In ps: CQmin={cq}, Dmin={data}, hold={hold}, uncertainty={uncertainty}, skew={skew}. Add ideal delay only to data. What minimum nonnegative addition satisfies hold?'),
    ('הגעה מוקדמת חייבת להיות לפחות skew+hold+uncertainty. מחסרים ממנה את CQmin+Dmin הקיימים, ומגבילים באפס.','Earliest arrival must be at least skew+hold+uncertainty. Subtract existing CQmin+Dmin and clamp the required addition at zero.'),
    ('לתיקון hold משתמשים בהשהיה מינימלית ולא מקסימלית.','Hold repair uses minimum rather than maximum delay.'),
    'cq data hold uncertainty skew',[(20,10,50,10,0),(40,30,50,10,0),(20,40,50,10,0),(20,10,50,10,40),(20,10,50,10,-40)],
    'violation|already safe|exact boundary|positive skew worsens|negative skew helps')
add(332,306,'sequential',('ציר זמן משותף אינו משנה מרווח','A common time shift does not change slack'),
    ('חזית שיגור בזמן {launch}ps וחזית הלכידה הנדרשת בזמן {capture}ps. CQ={cq}, נתיב={data}, setup={setup}ps; אין אי־ודאות. מה מרווח ה־setup?',
     'Launch edge is at {launch}ps and required capture edge at {capture}ps. CQ={cq}, path={data}, setup={setup}ps; there is no uncertainty. What is setup slack?'),
    ('זמן ההגעה הוא launch+CQ+path; המועד האחרון capture−setup. ההפרש ביניהם אינו תלוי בהזזה משותפת של ציר הזמן.','Arrival is launch+CQ+path; the deadline is capture−setup. Their difference is invariant to a common time-axis shift.'),
    ('משווים זמני הגעה ודרישה באותה מערכת ייחוס.','Compare arrival and required times in the same reference frame.'),
    'launch capture cq data setup',[(0,100,10,50,10),(1000,1100,10,50,10),(0,60,10,50,10),(-20,80,10,50,10),(10,80,10,50,10)],
    'base timeline|common positive shift|violation|negative origin|exact zero slack')
add(333,306,'sequential',('חלון skew צריך לספק שתי דרישות','The skew window must satisfy two constraints'),
    ('ב־ps: T={period}, CQmax={cqmax}, Dmax={dmax}, setup={setup}, CQmin={cqmin}, Dmin={dmin}, hold={hold}. ללא אי־ודאות, מה רוחב תחום ה־skew שמספק setup ו־hold? אם ריק, החזירו 0.',
     'In ps: T={period}, CQmax={cqmax}, Dmax={dmax}, setup={setup}, CQmin={cqmin}, Dmin={dmin}, hold={hold}. With zero uncertainty, what is the width of the skew interval satisfying setup and hold? Return 0 if empty.'),
    ('setup נותן גבול תחתון CQmax+Dmax+setup−T; hold נותן עליון CQmin+Dmin−hold. רוחב הוא העליון פחות התחתון, מוגבל באפס.','Setup gives lower bound CQmax+Dmax+setup−T; hold gives upper bound CQmin+Dmin−hold. Width is upper minus lower, clamped at zero.'),
    ('שינוי skew מועיל רק בתוך התחום שמותר לשתי הדרישות.','Changing skew helps only within both constraints’ permitted interval.'),
    'period cqmax dmax setup cqmin dmin hold',[(100,10,70,10,5,20,5),(80,10,70,10,5,20,5),(60,10,70,10,5,20,5),(90,10,70,10,5,0,5),(120,10,70,10,5,10,5)],
    'wide feasible interval|narrow interval|infeasible|single boundary point|negative skew allowed',4)
add(334,306,'sequential',('תקופת שעון שמתקנת את כל מסלולי ההכנה','A period change that repairs every setup path'),
    ('מרווחי setup נוכחיים הם {slacks}ps. hold כבר תקין, וכל נתוני המסלולים ו־skew נשארים קבועים. מה התוספת הלא־שלילית המזערית ל־T שתביא את כל מרווחי ה־setup לאפס לפחות?',
     'Current setup slacks are {slacks}ps. Hold already passes, and all path parameters and skew stay fixed. What minimum nonnegative increase in T makes every setup slack at least zero?'),
    ('כל מרווח setup גדל בתוספת התקופה. צריך לכסות את החסר הגדול ביותר, ולא את סכום החסרים במסלולים.','Each setup slack grows by the period increase. Cover the largest deficit, rather than summing deficits across paths.'),
    ('תיקון משותף נקבע לפי הדרישה המחמירה ביותר.','A shared repair is governed by the strongest constraint.'),
    'slacks',[([-20,5,-7],),([0,5,10],),([-1,-1,-1],),([-50,-20,3],),([10,20],)],
    'different deficits|zero boundary passes|tied deficits|dominant failing path|all positive')
add(335,306,'sequential',('הפינה הקריטית נקבעת מהמרווחים','Measured slack determines the critical corner'),
    ('לאותו מסלול נמדדו מרווחי setup בפינות שונות: {slacks}ps. כדי לעבור בכולן, מה מרווח ה־setup הקובע?',
     'The same path has setup slacks {slacks}ps across characterized corners. To pass all corners, what is the governing setup slack?'),
    ('צריך לעמוד בכל הפינות, ולכן המרווח הקטן ביותר קובע. שם פינה לבדו אינו מחליף נתוני אפיון.','Every corner must pass, so the smallest slack governs. A corner label cannot replace characterized timing data.'),
    ('בודקים תוצאות אפיון ולא מניחים מראש איזו פינה תנצח.','Inspect characterized results instead of assuming the critical corner.'),
    'slacks',[([20,-5,10],),([0,15,8],),([5,5,5],),([-2,-8,-1],),([40,3,19,12],)],
    'one failing corner|exact boundary|tied corners|all failing|nonfirst critical corner')
add(336,258,'electronics',('התאמת קצה קובעת מקדם החזרה','Load matching sets the reflection coefficient'),
    ('קו אידאלי בעל Z0={z0}Ω מסתיים בנגד ZL={load}Ω. מה מקדם החזרת המתח Γ=(ZL−Z0)/(ZL+Z0)? זהו עומס התנגדותי.',
     'An ideal line has Z0={z0}Ω and resistive termination ZL={load}Ω. What is voltage reflection coefficient Γ=(ZL−Z0)/(ZL+Z0)?'),
    ('עומס תואם נותן אפס; קצר נותן מינוס אחד; עומס גדול מ־Z0 נותן החזרה חיובית. מחלקים הפרש בסכום.','A matched load gives zero; a short gives minus one; a load above Z0 gives positive reflection. Divide difference by sum.'),
    ('קו ללא הפסדים עדיין יכול להחזיר גל בקצה לא תואם.','A lossless line can still reflect a wave at a mismatched end.'),
    'z0 load',[(50,150),(50,50),(50,0),(75,25),(40,80)],
    'positive reflection|matched|short circuit|negative reflection|different characteristic impedance')
add(337,258,'electronics',('המדרגה המשוגרת קטנה ממתח המקור','The launched step can be below source voltage'),
    ('מקור מדרגה {vs}V בעל התנגדות טורית Rs={rs}Ω מזין קו Z0={z0}Ω. לפני חזרת החזרות, מה אמפליטודת הגל המשוגר?',
     'A {vs}V step source with series Rs={rs}Ω drives a line of Z0={z0}Ω. Before reflections return, what is the launched-wave amplitude?'),
    ('בתחילת השיגור הקו מציג Z0, ולכן חלוקת המתח נותנת Vs·Z0/(Rs+Z0). אין להניח שהגל תמיד שווה Vs.','At launch the line presents Z0, so voltage division gives Vs·Z0/(Rs+Z0). The launched wave need not equal Vs.'),
    ('מבחינים בין מתח המחולל לבין אמפליטודת הגל בקו.','Distinguish generator voltage from the traveling-wave amplitude.'),
    'vs rs z0',[(4,50,50),(4,0,50),(3,100,50),(0,50,50),(-2,50,50)],
    'matched source|ideal zero-resistance source|source resistance dominates|no excitation|negative step')
add(338,258,'electronics',('המקור רואה את העומס רק אחרי הלוך וחזור','The source sees the load after a round trip'),
    ('זמן התפשטות חד־כיווני בקו הוא {flight}ns. שינוי משוגר בזמן 0. מה הזמן המוקדם ביותר שבו החזרה מהעומס יכולה לחזור למקור?',
     'One-way line flight time is {flight}ns. A change launches at time zero. What is the earliest time a load reflection can return to the source?'),
    ('הגל חייב להגיע לעומס ואז לעבור שוב את הקו בכיוון ההפוך. זמן הסבב הוא פעמיים הזמן החד־כיווני.','The wave must reach the load and traverse the line back. Round-trip time is twice the one-way flight time.'),
    ('מידע על סיום הקו אינו מגיע למקור באופן מיידי.','Information about the termination does not reach the source instantly.'),
    'flight',[(5,),(1,),(0,),(12,),(3,)],
    'ordinary line|short flight|zero-delay ideal limit|long flight|odd one-way duration')
add(339,258,'electronics',('מתח בקצה הוא סכום גל נכנס ומוחזר','Load voltage sums incident and reflected waves'),
    ('גל מדרגה נכנס בעוצמה {incident}V מגיע לקו Z0={z0}Ω עם עומס התנגדותי {load}Ω. לפני החזרות נוספות, מה מדרגת המתח בעומס?',
     'An incident {incident}V step reaches the end of a Z0={z0}Ω line terminated by {load}Ω. Before further reflections, what is the load-voltage step?'),
    ('בעומס מחברים גל נכנס וגל מוחזר: A(1+Γ)=2A·ZL/(ZL+Z0). בקצר המתח אפס למרות זרם.','Sum incident and reflected waves: A(1+Γ)=2A·ZL/(ZL+Z0). A short has zero voltage despite current.'),
    ('מתח בצומת הוא סכום הגלים המקומיים.','Node voltage is the sum of the local traveling waves.'),
    'incident z0 load',[(2,50,150),(2,50,50),(2,50,0),(3,60,20),(-2,50,150)],
    'positive reflection gain|matched amplitude|short load|negative reflection attenuation|negative incident wave')
add(340,258,'electronics',('מקור מותאם סופג את הגל החוזר','A matched source absorbs the returning wave'),
    ('קו Z0={z0}Ω מחובר למקור תבנין. כדי שהגל החוזר יראה Γsource=0, איזה Rs באוהם נדרש? מאפסים את מקור המתח לצורך מקדם ההחזרה.',
     'A Z0={z0}Ω line connects to a Thevenin source. What Rs in ohms gives Γsource=0 for the returning wave? Deactivate the voltage source when computing this reflection coefficient.'),
    ('מקדם ההחזרה במקור הוא (Rs−Z0)/(Rs+Z0). הוא אפס כאשר התנגדות המקור שווה לעכבה האופיינית.','Source reflection is (Rs−Z0)/(Rs+Z0). It vanishes when source resistance equals characteristic impedance.'),
    ('התאמה בקצה המקור שונה מבחירת מתח המדרגה.','Matching the source end is separate from choosing step voltage.'),
    'z0',[(50,),(75,),(25,),(100,),(60,)],
    'fifty-ohm line|seventy-five-ohm line|lower impedance|higher impedance|nonstandard teaching line')
add(341,261,'gates',('אורך שרשרת נמדד במספר תאים','Chain length counts cells'),
    ('גרף DAG של buffers ממוספר 0..{last}. כל קשת {edges} מכוונת ממספר קטן לגדול. מה מספר התאים בשרשרת הארוכה ביותר? גם תא מבודד הוא שרשרת באורך 1.',
     'A buffer DAG has nodes 0..{last}. Directed edges {edges} go from lower to higher indices. How many cells are in its longest chain? An isolated cell is a chain of length one.'),
    ('מתחילים באורך אחד לכל תא. לאורך קשת מוסיפים אחד לאורך הקודם, ובמפגש מסלולים שומרים את המקסימום.','Initialize each cell length to one. Across an edge add one to its predecessor length; at reconvergence retain the maximum.'),
    ('אורך שרשרת תאים אינו מספר הקשתות ואינו השהיה חשמלית.','Cell-chain length is neither edge count nor electrical delay.'),
    'nodes last edges',[(4,3,[[0,1],[1,2],[2,3]]),(3,2,[]),(4,3,[[0,1],[0,2],[2,3]]),(5,4,[[0,2],[1,2],[2,4]]),(5,4,[[0,1],[3,4]])],
    'simple chain|isolated cells|branch|reconvergence|disconnected chains')
add(342,261,'gates',('שער רגיל שובר רצף buffers','An ordinary gate breaks a buffer run'),
    ('מסלול תאים מסומן {kinds}, כאשר B הוא buffer ו־L הוא תא לוגי אחר. חוטים אינם מופיעים. מה אורך רצף ה־buffers הארוך ביותר?',
     'A cell path is {kinds}, where B is a buffer and L is another logic cell. Wires are omitted. What is the longest consecutive buffer run?'),
    ('סופרים רצפי B נפרדים ומאפסים את הספירה בכל L. אין לצרף buffers משני צדי שער אחר.','Count separate B runs and reset the count at each L. Do not join buffers across another gate.'),
    ('רצף מסוג תא מסוים שונה ממסלול לוגי שלם.','A run of one cell type differs from an entire logic path.'),
    'kinds',[('BBLBBB',),('LLLL',),('BBBB',),('LBBL',),('BLBLB',)],
    'two runs|no buffers|unbroken chain|bounded run|alternating cells')
add(343,261,'gates',('יותר מהסף אינו כולל שוויון','Strictly above the limit excludes equality'),
    ('לכל נקודת קצה של buffers נמצאו אורכי שרשרת מרביים {endpoint_lengths}. מדווחים עדות אחת לנקודת קצה רק אם האורך גדול מ־{limit}. כמה דיווחים יופקו?',
     'Buffer endpoints have longest-chain lengths {endpoint_lengths}. Emit one witness per endpoint only if its length is greater than {limit}. How many reports are produced?'),
    ('בודקים כל נקודת קצה פעם אחת עם אי־שוויון מחמיר. אין לספור את כל המסלולים שמגיעים אליה.','Check each endpoint once with strict inequality. Do not count every path reaching it.'),
    ('חוזה הדיווח קובע גם את גודל הפלט.','The reporting contract also determines output size.'),
    'endpoint_lengths limit',[([9,10,11,12],10),([10,10],10),([1,2,3],0),([],10),([12,12,5],10)],
    'around threshold|all equal boundary|zero threshold|no endpoints|equal lengths distinct endpoints')
add(344,261,'gates',('שימוש בנתונים מונע סינון כעץ בקרה בלבד','Data use prevents control-only filtering'),
    ('קבוצות תפקידי הקצוות של ענפי buffer הן {roles}. מסננים רק קבוצה לא ריקה המכילה reset או clock בלבד. data,unknown או קבוצה ריקה נשמרים. כמה ענפים מסוננים?',
     'Buffer cones have terminal-role sets {roles}. Exclude only nonempty sets containing solely reset or clock. Preserve data, unknown and empty sets. How many cones are excluded?'),
    ('תפקיד פין מתועד קובע סינון. ענף מעורב המכיל נתונים נשמר גם אם יש בו שימוש reset.','Documented pin roles govern filtering. A mixed cone containing data remains even when it also serves reset.'),
    ('שם אות או fanout אינם ראיה מספקת לתפקידו.','A signal name or fanout alone does not establish its role.'),
    'roles',[([['reset'],['reset','data'],[]],),([['clock'],['reset','clock']],),([['unknown'],['data']],),([[],[]],),([['reset'],['unknown','reset'],['clock','data']],)],
    'mixed-use retention|control-only cones|unknown roles|empty cones|control plus uncertainty')
add(345,261,'gates',('מיון טופולוגי נתקע גם אחרי מעגל','Topological removal can leave a cycle’s descendants'),
    ('בגרף buffer יש {nodes} צמתים 0..{last}, וקשתות {edges}. מסירים שוב ושוב צמתים ללא קשת נכנסת מצומת שנותר. כמה צמתים לא יוסרו?',
     'A buffer graph has {nodes} nodes 0..{last} and edges {edges}. Repeatedly remove nodes having no incoming edge from a remaining node. How many nodes remain?'),
    ('מסירים מקורות ומעדכנים דרגות כניסה. צמתים במעגל, וגם צאצאים התלויים בו, עשויים להישאר; זה אינו בהכרח מספר צמתי המעגל בלבד.','Remove sources and update indegrees. Cycle nodes and descendants depending on them may remain; the count need not equal only the cycle size.'),
    ('כישלון מיון טופולוגי מעיד על מעגל בלי להמציא אורך סופי.','Failed topological sorting detects a cycle without inventing a finite longest path.'),
    'nodes last edges',[(3,2,[[0,1],[1,0],[1,2]]),(3,2,[[0,1],[1,2]]),(1,0,[[0,0]]),(4,3,[[0,1],[2,3],[3,2]]),(3,2,[])],
    'cycle with descendant|acyclic chain|self-loop|mixed components|isolated nodes',4)
add(346,263,'gates',('מונה רווי מספיק לסף סטטי','A saturated count suffices for a static threshold'),
    ('סורקים את ביטי המילה {bits} פעם אחת. מונה מתחיל ב־0 ומוסיף כל ביט, עם רוויה ב־3. אין חיסורים או חלון נע. מה ערכו בסיום?',
     'Scan word bits {bits} once. A counter starts at zero, adds each bit and saturates at three. There are no subtractions or sliding windows. What is its final value?'),
    ('הסכום נשמר במדויק עד שלוש, ואז נשאר שלוש. זה מספיק להחלטה אם הספירה גדולה משתיים, בחוזה ללא חיסור.','The count is exact through three and remains three afterward. This suffices to decide whether count exceeds two when no subtraction is required.'),
    ('מידע שניתן להשמיט תלוי בפעולות העתידיות ובפלט הדרוש.','Discardable information depends on future operations and required output.'),
    'bits',[([1,0,1,1,1],),([0,0,0],),([1,1,0],),([1,1,1],),([1,0,0,0],)],
    'above threshold saturation|zero|just below threshold|exact threshold|single active input')
add(347,263,'gates',('כמה הפעלות חסרות כדי לעבור את הסף','How many activations are missing to cross the threshold'),
    ('נתונים ביטים {bits}, ויש מספיק אפסים להפעלה נוספת. נדרש יותר משני אחדים. מה מספר האפסים המזערי שצריך להפוך לאחד? אם התנאי כבר מתקיים, החזירו 0.',
     'Bits are {bits}, with enough zeros available for further activation. More than two ones are required. What minimum number of zeros must become one? Return zero if already satisfied.'),
    ('היעד המזערי הוא שלושה אחדים, לא שניים. מחסרים את הספירה הקיימת משלוש ומגבילים באפס.','The minimum target is three ones, not two. Subtract the current count from three and clamp at zero.'),
    ('ניסוח מחמיר של סף משנה את מקרה הגבול.','A strict threshold changes the boundary case.'),
    'bits',[([1,1,0,0],),([0,0,0,0],),([1,0,0,0],),([1,1,1,0],),([1,1,1,1,0],)],
    'one missing|all inactive|two missing|already exactly enough|already above minimum')
add(348,265,'sequential',('גבול השורש כולל ריבוע מושלם','The square-root bound includes perfect squares'),
    ('לצורך תקציב בדיקות, סופרים את כל המחלקים המועמדים השלמים d מ־2 עם d²≤{n}, גם אם בדיקה מוקדמת הייתה מוצאת גורם. כמה מועמדים יש?',
     'For a checking budget, count all integer trial divisors d from 2 with d²≤{n}, even if an earlier test would find a factor. How many candidates are there?'),
    ('המועמד האחרון הוא floor(sqrt(n)); סופרים החל משתיים. בריבוע מושלם יש לכלול את השורש עצמו.','The final candidate is floor(sqrt(n)); count from two. A perfect square must include its square root.'),
    ('בדיקת גבול נכונה חיונית כדי לא לפספס ריבועים מורכבים.','A correct boundary test prevents missing composite squares.'),
    'n',[(49,),(47,),(4,),(3,),(0,)],
    'perfect square|below square|smallest composite|empty candidate range|zero input')
add(349,265,'gates',('ראשוניות דורשת טיפול גם באפס ואחד','Primality must handle zero and one'),
    ('בלוק ראשוניות נבדק על הערכים {numbers}. כמה מהם צריכים להפיק 1? ראשוני הוא מספר גדול מאחד עם שני מחלקים חיוביים בלבד.',
     'A primality block is tested on values {numbers}. How many should output 1? A prime is greater than one and has exactly two positive divisors.'),
    ('אפס ואחד אינם ראשוניים; שתיים כן. יתר המספרים נבדקים למציאת גורם עד השורש כולל.','Zero and one are not prime; two is. Check other numbers for a factor through the square root inclusive.'),
    ('לולאת בדיקה ריקה אינה לבדה הוכחה לראשוניות.','An empty trial loop alone does not prove primality.'),
    'numbers',[([0,1,2,3],),([4,9,25,49],),([2,4,6,8],),([11,13,17,19],),([1,7,15,23,27],)],
    'zero one and small primes|odd and even squares|two is special|all prime|mixed batch')
add(350,265,'sequential',('הגורם הראשון מסיים חיפוש מורכבות','The first factor ends a compositeness search'),
    ('בקר מנסה מחלקים 2,3,4,... עד השורש כולל עבור n={n}. מה המחלק הראשון עם שארית אפס? החזירו 0 אם לא נמצא בתחום.',
     'A controller tries divisors 2,3,4,... through the square root inclusive for n={n}. What is the first divisor with zero remainder? Return zero if none exists in that range.'),
    ('עוברים בסדר עולה ועוצרים בגורם הראשון. גורם בשורש תקף; מספר ראשוני מגיע לסוף בלי גורם בתחום.','Try ascending divisors and stop at the first factor. A square-root factor counts; a prime exhausts the range without a factor.'),
    ('מציאת גורם היא עדות קצרה; היעדר גורם דורש כיסוי הטווח.','A factor is a short witness; no factor requires covering the candidate range.'),
    'n',[(49,),(21,),(16,),(47,),(2,)],
    'factor at square root|small odd factor|earliest even factor|prime full search|empty range')


def replace_case(n, variant, query, prompt, reason, **inputs):
    """Some objectives vary the inference, not merely numeric constants."""
    spec = SPECS[n - 251]
    spec['cases'][variant - 1] = dict(_query=query, _prompt=loc(*prompt), _reason=loc(*reason), **inputs)
    spec['coverage'][variant - 1] = query


replace_case(264,5,'miswired_inverter',('A=0,B=1. מחשבים t=NAND(A,B), אבל בטעות y=NAND(t,A) במקום NAND(t,t); z=NOR(A,B). מה [t,y,z] אחרי התייצבות?', 'A=0,B=1. Compute t=NAND(A,B), but mistakenly y=NAND(t,A) instead of NAND(t,t); z=NOR(A,B). What is [t,y,z] after settling?'), ('הכניסה A=0 כופה y=1, ולכן השער השני כבר אינו הופך את t.','Input A=0 forces y=1, so the second gate no longer inverts t.'), a=0,b=1)
replace_case(301,2,'recover_branch',('שלושה נגדים זהים במקביל נותנים 1Ω. מה התנגדות כל נגד באוהם?', 'Three identical parallel resistors give 1Ω. What is each resistor in ohms?'), ('כל נגד הוא פי שלושה מהשקול.','Each branch resistance is three times the equivalent.'), equivalent=1)
replace_case(301,3,'total_current',('שלושה נגדי 6Ω במקביל בין צמתים שהפרש המתח ביניהם 6V. מה הזרם הכולל באמפר?', 'Three 6Ω resistors connect in parallel across 6V. What is total current in amperes?'), ('בכל ענף 1A; שלושת הזרמים מצטרפים.','Each branch carries 1A; the three currents add.'), r=6, v=6)
replace_case(301,4,'branch_current',('שלושה נגדים זהים במקביל מוליכים יחד 9A. מה הזרם בכל ענף באמפר?', 'Three identical parallel resistors carry 9A in total. What is current in each branch in amperes?'), ('בסימטריה כל ענף נושא שליש מהזרם הכולל.','Symmetry assigns one third of total current to each branch.'), total=9)
replace_case(301,5,'one_open',('שלושה נגדי 12Ω במקביל; אחד נותק. מה ההתנגדות השקולה החדשה באוהם?', 'Three 12Ω resistors are parallel; one is disconnected. What is the new equivalent resistance in ohms?'), ('נותרו שני נתיבים זהים במקביל.','Two identical parallel paths remain.'), r=12)
replace_case(303,2,'voltage',('קובייה סימטרית נותנת Req=5R/6. כל צלע 1Ω, וזרם הכניסה 6A. מה הפרש המתח בין הפינות?', 'A symmetric cube gives Req=5R/6. Every edge is 1Ω and input current is 6A. What is the corner-to-corner voltage?'), ('מכפילים את התנגדות הקובייה השקולה בזרם הכולל.','Multiply the cube equivalent resistance by total current.'), r=1, current=6)
replace_case(303,3,'current',('קובייה סימטרית: Req=5R/6, R=12Ω. מפעילים 10V בין הפינות. מה הזרם הכולל?', 'Symmetric cube: Req=5R/6 with R=12Ω. Apply 10V between corners. What is total current?'), ('מחלקים את מתח ההזנה בהתנגדות השקולה.','Divide applied voltage by equivalent resistance.'), r=12, voltage=10)
replace_case(303,4,'power',('קובייה סימטרית: Req=5R/6, R=3Ω, זרם כולל 2A. מה הספק החימום הכולל בוואט?', 'Symmetric cube: Req=5R/6, R=3Ω, total current 2A. What is total heating power in watts?'), ('ההספק הכולל הוא ריבוע הזרם כפול ההתנגדות השקולה.','Total power is current squared times equivalent resistance.'), r=3, current=2)
replace_case(303,5,'scale',('כל צלע בקובייה משתנה מ־6Ω ל־18Ω, בלי שינוי חיבורים. פי כמה משתנה ההתנגדות בין פינות נגדיות?', 'Every cube edge changes from 6Ω to 18Ω without changing connections. By what factor does opposite-corner resistance change?'), ('כפל כל ההתנגדויות באותו גורם מכפיל גם את השקול בו.','Scaling every resistance by one factor scales the equivalent by that factor.'), old=6, new=18)
replace_case(319,2,'initial_quarter',('ממיר 1 ביט דורש שגיאת התייצבות לכל היותר חצי LSB. השגיאה ההתחלתית היא FS/4. כמה חלוקות בשתיים עוד נדרשות?', 'A 1-bit ADC requires at most half-LSB settling error. Initial error is FS/4. How many further halvings are needed?'), ('חצי LSB כבר שווה FS/4, ולכן הדרישה מתקיימת.','Half an LSB already equals FS/4, so the requirement is met.'), bits=1, initial_power=2, margin=1)
replace_case(319,3,'quarter_lsb',('שגיאה מתחילה ב־FS. עבור ADC של 8 ביט, דורשים לכל היותר רבע LSB. כמה חלוקות בשתיים נדרשות?', 'Error starts at FS. An 8-bit ADC requires at most a quarter LSB. How many halvings are needed?'), ('רבע LSB הוא FS/2^(8+2).','A quarter LSB is FS/2^(8+2).'), bits=8, initial_power=0, margin=2)
replace_case(319,4,'two_lsb',('שגיאה מתחילה ב־FS. בממיר 10 ביט מותר פער של עד 2LSB. כמה חלוקות בשתיים נדרשות?', 'Error starts at FS. A 10-bit converter permits up to 2LSB error. How many halvings are needed?'), ('שני LSB הם FS/2^9.','Two LSBs equal FS/2^9.'), bits=10, initial_power=0, margin=-1)
replace_case(319,5,'time_coefficient',('לממיר 16 ביט דרושה התייצבות מ־FS לחצי LSB. τ=2ns. הזמן המזערי הוא t=k·ln(2)ns; מה k?', 'A 16-bit converter must settle from FS to half an LSB. τ=2ns. Minimum settling time is t=k·ln(2)ns; what is k?'), ('נדרשות 17 חלוקות בשתיים, כל אחת במשך 2ln(2)ns.','Seventeen halvings each take 2ln(2)ns.'), bits=16, tau=2)
replace_case(321,2,'frequency',('טבלה בת 4 דגימות נקראת בקצב 1000kS/s וחוזרת במחזור. מה תדר המחזור ב־kHz?', 'A four-sample table repeats while read at 1000kS/s. What is its cycle frequency in kHz?'), ('מחלקים קצב דגימה במספר הדגימות למחזור.','Divide sample rate by samples per cycle.'), samples=4, fs=1000)
replace_case(321,3,'sample_rate',('מחולל צריך 30kHz עם 32 דגימות למחזור. מה קצב הדגימה הדרוש ב־kS/s?', 'A generator needs 30kHz with 32 samples per cycle. What sampling rate in kS/s is required?'), ('כל מחזור צורך 32 דגימות.','Each cycle consumes 32 samples.'), samples=32, fout=30)
replace_case(321,4,'bits',('טבלת מחזור מלאה כוללת 1000 מילים של 12 ביט. כמה ביטי נתונים נשמרים, ללא לוגיקת בקרה?', 'A full-period table has 1000 twelve-bit words. How many data bits are stored, excluding control logic?'), ('מכפילים מספר מילים ברוחב המילה.','Multiply word count by word width.'), samples=1000, width=12)
replace_case(321,5,'last_address',('טבלת מחזור מכילה 8 מילים, בכתובות רציפות החל מאפס. מה הכתובת האחרונה לפני החזרה לאפס?', 'A period table has eight words, addressed consecutively from zero. What is the last address before wrapping to zero?'), ('מספר כתובות שמונה פירושו טווח 0..7.','Eight addresses span 0..7.'), samples=8)
replace_case(325,2,'wired_zero',('למחזור 4 דגימות שומרים רבע גל כולל השיא, אבל יוצרים את דגימת האפס בחיווט. כמה מילים צריך לאחסן?', 'For a four-sample period, retain quarter-wave samples including the peak, but generate zero by wiring. How many words must be stored?'), ('מסירים את מילת האפס מטווח הקצוות הכלולים.','Remove the zero word from the inclusive endpoint range.'), period=4)
replace_case(325,3,'intervals',('למחזור 8 דגימות שומרים כתובות מגניטודה 0..N/4 כולל. כמה רווחי כתובת יש בין המילה הראשונה לאחרונה?', 'For an eight-sample period, store magnitude addresses 0..N/4 inclusive. How many address intervals separate the first and last words?'), ('מספר הרווחים קטן באחד ממספר הנקודות.','There is one fewer interval than points.'), period=8)
replace_case(325,4,'storage',('N=16 דגימות למחזור. שומרים פאזות 0..N/4 כולל, ברוחב 10 ביט למילה. כמה ביטים בטבלה?', 'N=16 samples per cycle. Store phases 0..N/4 inclusive, ten bits per word. How many bits are in the table?'), ('חמש נקודות כפול עשרה ביטים.','Five points times ten bits.'), period=16, width=10)
replace_case(325,5,'peak_address',('N=64 דגימות למחזור. רבע הטבלה ממוספר מאפס וכולל את השיא. מה כתובת דגימת השיא?', 'N=64 samples per cycle. The quarter table starts at address zero and includes the peak. What is the peak sample address?'), ('השיא נמצא בפאזה N/4.','The peak lies at phase N/4.'), period=64)
replace_case(338,2,'load_arrival',('זמן חד־כיווני בקו הוא 1ns. מדרגה משוגרת בזמן 0. מתי יכול העומס להגיב לראשונה, בננו־שניות?', 'One-way line delay is 1ns. A step launches at zero. When can the load first respond, in nanoseconds?'), ('לעומס דרוש מעבר אחד בלבד.','Reaching the load takes one traversal.'), flight=1)
replace_case(338,3,'infer_flight',('החזרה מהעומס מגיעה לראשונה למקור 8ns אחרי השיגור. מה זמן ההתפשטות החד־כיווני בקו סימטרי?', 'A load reflection first reaches the source 8ns after launch. What is the symmetric line’s one-way flight time?'), ('זמן הלוך וחזור כולל שני מעברים שווים.','Round-trip time contains two equal traversals.'), roundtrip=8)
replace_case(338,4,'second_load',('זמן חד־כיווני 12ns. גל שוגר ב־0, הוחזר מהעומס ואז הוחזר שוב מהמקור. מתי ההחזרה השנייה מגיעה לעומס?', 'One-way flight time is 12ns. A wave launches at zero, reflects from the load, then reflects again at the source. When does that second wave reach the load?'), ('השיגור לעומס, חזרה למקור ושוב לעומס הם שלושה מעברים.','Source to load, back to source, then to load takes three traversals.'), flight=12)
replace_case(338,5,'absolute_return',('מדרגה משוגרת בזמן 7ns בקו שזמן המעבר בו 3ns לכל כיוון. מתי יכולה ההחזרה להגיע למקור בזמן מוחלט?', 'A step launches at time 7ns on a line taking 3ns each way. What absolute time can its reflection reach the source?'), ('מוסיפים זמן הלוך וחזור למועד השיגור.','Add the round-trip duration to launch time.'), flight=3, launch=7)
replace_case(340,2,'ideal_source',('גל חוזר למקור מתח אידאלי עם Rs=0 בקו Z0=75Ω. מה מקדם החזרת המתח במקור?', 'A wave returns to an ideal voltage source with Rs=0 on a Z0=75Ω line. What is the source voltage-reflection coefficient?'), ('מקור מתח מאופס הוא קצר: מקדם ההחזרה מינוס אחד.','A deactivated ideal voltage source is a short: reflection coefficient minus one.'), z0=75, rs=0)
replace_case(340,3,'reflected_amplitude',('גל חוזר של 3V מגיע למקור מותאם Rs=Z0=25Ω. מה אמפליטודת הגל המוחזר שוב לקו?', 'A returning 3V wave reaches a matched source Rs=Z0=25Ω. What amplitude is reflected back into the line?'), ('מקדם החזרה אפס מכפיל את הגל החוזר לאפס.','Zero reflection coefficient gives zero re-reflected amplitude.'), incident=3, z0=25, rs=25)
replace_case(340,4,'source_step',('גל חוזר של ‎-2V מגיע למקור מותאם Rs=Z0=100Ω. מה שינוי המתח בצומת המקור עקב הגל הזה בלבד?', 'A returning -2V wave reaches a matched source Rs=Z0=100Ω. What source-node voltage change is due to this wave alone?'), ('אין גל מוחזר נוסף, ולכן שינוי הצומת שווה לגל הנכנס.','There is no additional reflected wave, so the node change equals the incoming wave.'), incident=-2, z0=100, rs=100)
replace_case(340,5,'positive_source_reflection',('בקו Z0=60Ω רוצים מקדם החזרה במקור Γ=1/2. איזה Rs נותן (Rs−Z0)/(Rs+Z0)=1/2?', 'On a Z0=60Ω line, source reflection Γ=1/2 is required. Which Rs gives (Rs−Z0)/(Rs+Z0)=1/2?'), ('פתרון המשוואה נותן Rs=3Z0; זו בכוונה אינה התאמה.','Solving gives Rs=3Z0; this is intentionally a mismatch.'), z0=60)


def alternative(n, p):
    q = p['_query']
    if n == 264:
        t = 1 - (p['a'] & p['b'])
        return [t, 1 - (t & p['a']), 1 - (p['a'] | p['b'])]
    if n == 301:
        if q == 'recover_branch': return 3 * p['equivalent']
        if q == 'total_current': return F(3 * p['v'], p['r'])
        if q == 'branch_current': return F(p['total'], 3)
        return F(p['r'], 2)
    if n == 302:
        if q == 'six_currents': return 6 * p['current']
        if q == 'recover_six': return 6 * p['equivalent']
        if q == 'current_split': return F(p['total'], 6)
        return F(6, p['r'])
    if n == 303:
        if q == 'scale': return F(p['new'], p['old'])
        r = F(5 * p['r'], 6)
        if q == 'voltage': return p['current'] * r
        if q == 'current': return p['voltage'] / r
        return p['current'] ** 2 * r
    if n == 319:
        if q == 'time_coefficient': return (p['bits'] + 1) * p['tau']
        return max(0, p['bits'] + p['margin'] - p['initial_power'])
    if n == 321:
        if q == 'frequency': return F(p['fs'], p['samples'])
        if q == 'sample_rate': return p['samples'] * p['fout']
        if q == 'bits': return p['samples'] * p['width']
        return p['samples'] - 1
    if n == 325: return (p['period'] // 4 + 1) * p['width'] if q == 'storage' else p['period'] // 4
    if n == 338:
        if q == 'infer_flight': return F(p['roundtrip'], 2)
        return dict(load_arrival=1, second_load=3, absolute_return=2)[q] * p['flight'] + p.get('launch', 0)
    if n == 340:
        if q == 'positive_source_reflection': return 3 * p['z0']
        reflection = F(p['rs'] - p['z0'], p['rs'] + p['z0'])
        if q == 'ideal_source': return reflection
        return p['incident'] * (reflection + (q == 'source_step'))
    raise AssertionError((n, q))


def normalize(value):
    if isinstance(value, F):
        return value.numerator if value.denominator == 1 else str(value)
    return value


def render(value):
    return json.dumps(value, separators=(',', ':')) if isinstance(value, list) else str(value)


def choices_for(value, task):
    if isinstance(value, list):
        if task in {261,264,265,269}:
            candidates = [value] + [list(bits) for bits in __import__('itertools').product((0,1), repeat=len(value))]
        else:
            candidates = [value, list(reversed(value)), [0] * len(value),
                      [x + 1 for x in value], [max(0, x - 1) for x in value],
                      [1 - x if x in (0, 1) else x + 2 for x in value], [x + 2 for x in value], [x + 3 for x in value]]
    else:
        v = F(value)
        candidates = [normalize(v), normalize(v + 1), normalize(v - 1),
                      normalize(v * 2), normalize(-v), normalize(v + 2)]
    result = []
    for x in candidates:
        if x not in result: result.append(x)
        if len(result) == 4: return result
    raise AssertionError(value)


def build():
    CARDS.clear()
    questions, checks = [], []
    assert [s['n'] for s in SPECS] == list(range(251, 351))
    for spec in SPECS:
        source = f"quick-hw-{spec['n']}"
        for variant, (p, coverage) in enumerate(zip(spec['cases'], spec['coverage'], strict=True), 1):
            value = normalize(model(spec['n'], p))
            candidates = choices_for(value, spec['n'])
            shift = ((spec['n'] - 251) * 5 + variant - 1) % 4
            options = candidates[shift:] + candidates[:shift]
            prompt = {lang: p.get('_prefix', {}).get(lang, '') + p.get('_prompt', spec['prompt'])[lang].format_map(p)
                      for lang in ('he', 'en')}
            explanation = {lang: f"{render(value)}. {p.get('_reason', spec['reason'])[lang]}" for lang in ('he', 'en')}
            key = f'{source}-v{variant}'
            questions.append(dict(key=key, source_key=source, variant=variant, topic=spec['topic'],
                                  status='draft', prompt=prompt,
                                  choices=[loc(render(x), render(x)) for x in options],
                                  correct=options.index(value), explanation=explanation))
            checks.append(dict(key=key, task=spec['n'], inputs=p, options=options, expected=value,
                               difficulty=spec['difficulty'],
                               difficulty_rationale=f"Requires applying this bounded objective: {spec['title']['en']}. Includes the stated boundary cases; editorial estimate, not learner calibration.",
                               coverage=coverage,
                               interview_ids=[f"PREP-{spec['prep']:03}"],
                               provenance='Original short exercise derived from the linked interview editorial and bilingual bank; not a reported company question.',
                               method='Input-derived independent enumeration, circuit equation or event replay in test_fundamentals_hardware_700.py',
                               scope='Bounded Python teaching models only; no HDL compilation, SPICE, physical hardware, CDC closure or human expert review.'))
            if variant == 1:
                CARDS.append(dict(id=source, topic=spec['topic'], interviewIds=[f"PREP-{spec['prep']:03}"],
                                  title=spec['title'], prompt=prompt, answer=explanation, takeaway=spec['takeaway']))
    return questions, checks


def write():
    questions, checks = build()
    for path, values in [(CONTENT / 'fundamentals-hardware-700.json', CARDS),
                         (OUT / 'hardware_700.json', questions), (OUT / 'hardware_700.checks.json', checks)]:
        path.write_text(json.dumps(values, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'{len(CARDS)} hardware cards; {len(questions)} draft variants; {len(checks)} evidence records')


if __name__ == '__main__':
    write()

