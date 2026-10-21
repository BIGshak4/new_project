"""Build only the four owned archive records and bilingual Markdown files."""
import json
from pathlib import Path

BANK = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
questions, editorial, localization = [], {}, {}


def add(number, key, title, original, prompts, hints, solutions, material, topics, tags, companies,
        badge, code, diagrams, related, duplicate):
    ident = f'PREP-{number:03d}'
    q = {'id': ident, 'key': key, 'version': 1, 'created_on': '2026-10-21', 'category': 'hardware',
             'topic': topics[0], 'topics': ['hardware', *topics], 'source_topic_tags': ['hardware'] if 'hardware' in tags else [],
             'added_topic_tags': topics, 'source_tags': tags, 'reported_companies': companies,
             'source_company_badge': badge,
             'company_attribution_status': 'reported_by_supplied_source_not_independently_verified',
             'difficulty': None, 'estimated_minutes': None, 'format': 'circuit_design', 'status': 'in_review',
             'solution_status': 'proposed', 'solution_display_label': 'הצעה לפתרון',
             'origin': 'user_supplied_screenshot', 'reviewed_by': None, 'ai_assisted': True,
             'authorship': 'Founder-supplied screenshot; AI-assisted bilingual proposed solution, authored diagrams and Python model checks. Independent professional, translation-parity and reuse reviews pending.',
             'sources': [{'type': 'user_supplied_image', 'path': f'sources/prep-{number:03d}.png', 'received_on': '2026-10-21'}],
             'original_prompt': original, 'translations': {}, 'prepared_hints': []}
    for lang in ('he','en'):
        q['translations'][lang] = {'title': title[lang], 'prompt': prompts[lang], 'hint': hints[lang][0],
                                      'hints': hints[lang], 'reference_solution': solutions[lang]}
        q['prepared_hints'] += [{'id': f'{ident}-{lang}-H{i+1:02d}', 'language': lang, 'level': i+1, 'content': h}
                                for i,h in enumerate(hints[lang])]
    q.update({field: values['en'] for field,values in material.items()})
    q.update(follow_up_integration_status='prepared_in_archive_not_connected_to_interactive_queue',
             solution_code_path=code[0], solution_code_paths=code,
             verification_script_path=f'checks/check_prep_{number:03d}.py',
             verification_evidence_path=f'checks/prep-{number:03d}-verification.json',
             media_assets=[{'type': 'source_image', 'path': f'sources/prep-{number:03d}.png'}],
             related_question_ids=related, duplicate_check=duplicate,
             interview_relevance={'priority': 'high', 'basis': 'Foundational digital design and explicit behavioral contracts; company associations are reported only by the supplied screenshot.'},
             markdown_path=f'questions/prep-{number:03d}-{key}.md')
    for kind, stem, description in diagrams:
        for lang in ('he','en'):
            q['media_assets'].append({'type': kind,'path': f'diagrams/{stem}-{lang}.png','language': lang,'description': description[lang]})
    editorial[ident] = {'hints': hints, 'note': '2026-10-21: original screenshot archived; authored bilingual proposed solution and localized diagrams; Python checks passed, no HDL simulation or human professional approval claimed.'}
    localization[ident] = material
    questions.append(q)
    md=[f'# {ident} — {title["he"]}', '', '## מקור שנמסר', '', original, '',
        f'[צילום המקור הפנימי](../sources/prep-{number:03d}.png)', '',
        'סטטוס: פתרון מוצע בסיוע AI; בדיקה מקצועית אנושית ממתינה. השיוך לחברות הוא דיווח מהצילום בלבד.', '']
    for lang in ('he','en'):
        md += [f'## {title[lang]}', '', prompts[lang], '', '### רמזים' if lang=='he' else '### Hints', '']
        md += [f'{i+1}. {hint}' for i,hint in enumerate(hints[lang])]
        for asset in q['media_assets']:
            if asset['type']=='prompt_diagram' and asset.get('language')==lang:
                md += ['',f'![{asset["description"]}](../{asset["path"]})','']
        md += ['', '### הצעה לפתרון' if lang=='he' else '### Proposed solution','',solutions[lang],'']
        for asset in q['media_assets']:
            if asset['type']=='solution_diagram' and asset.get('language')==lang:
                md += [f'![{asset["description"]}](../{asset["path"]})','']
        for field, values in material.items():
            md += [f'### {field}', '', json.dumps(values[lang], ensure_ascii=False, indent=2), '']
    md += ['## Files', '', *[f'- [Code](../{p})' for p in code],
           f'- [Verification](../checks/check_prep_{number:03d}.py)',
           f'- [Evidence](../checks/prep-{number:03d}-verification.json)','']
    (BANK/q['markdown_path']).write_text('\n'.join(md),encoding='utf-8')


def pair(he,en): return {'he': he,'en': en}


add(65, 'dff-from-edge-triggered-srff',
    pair('מימוש דלגלג D בעזרת דלגלג SR','Implementing a D flip-flop using an SR flip-flop'),
    'ממש DFF בעזרת SRFF',
    pair('ממשו דלגלג D באמצעות דלגלג SR ושערים לוגיים. הציגו חיבורים וטבלת פעולת הרכיב.\n\nהנחה מפורשת שנוספה למקור: הרכיב הנתון הוא דלגלג SR בחזית עולה, עם כניסות S,R סינכרוניות פעילות בגבוה: 00 שומר, 01 מאפס, 10 קובע 1, ו־11 אסור. אין זו הנחה על נועל שקוף או על כניסות preset/clear אסינכרוניות. הקלט D יציב סביב חזית השעון בהתאם לזמני ההכנה וההחזקה, לרבות המסלול דרך המהפך. אין דרישת איפוס נוספת. הסבירו מה משתנה אם הרכיב הנתון הוא דווקא נועל SR.',
         'Implement a D flip-flop using an SR flip-flop and logic gates. Give the connections and operation table.\n\nExplicit editorial assumption: the supplied SR primitive is rising-edge triggered, with synchronous active-high S,R: 00 holds, 01 resets, 10 sets, and 11 is forbidden. It is not a transparent latch or asynchronous preset/clear input pair. D meets setup and hold on both paths, including the inverter path. No additional reset is required. Explain why a transparent SR latch would change the answer.'),
    pair(['מה צריכה להיות היציאה מיד אחרי חזית כאשר D=0, ומה כאשר D=1?',
          'כניסת Set יכולה לבקש לשמור 1, וכניסת Reset יכולה לבקש לשמור 0. צריך שהבקשות לא יהיו פעילות יחד בזמן הדגימה.',
          'בחרו S כך שיעלה בדיוק כאשר D=1 ואת R כהיפוכו. בדקו את שני ערכי D ואת המצב האסור 11.'],
         ['What should Q become after an edge for D=0, and for D=1?',
          'Set requests a stored one; reset requests zero. The requests must not both be active when sampled.',
          'Let S be high exactly when D=1, and make R its complement. Check both D values and the forbidden 11 input.']),
    pair('''### הרעיון: לתרגם נתון לפקודת קביעה או איפוס

דלגלג D צריך לשמור אחרי כל חזית את הערך שהיה על D בזמן הדגימה. אין צורך לחשב משוב מ־Q: אם D=1 נבקש Set, ואם D=0 נבקש Reset. לכן נחבר:

```text
S = D
R = NOT D
clk של דלגלג SR = clk של המערכת
Q של דלגלג SR = Q של דלגלג D
```

בשרטוט יש נקודת פיצול על D: הענף הישיר מגיע ל־S, והענף השני עובר במהפך ומגיע ל־R. חץ clk נכנס לכניסת השעון, ולא לאחת מכניסות הנתונים.

### בדיקה בטבלה

| D | S | R | Q אחרי חזית עולה |
| --- | --- | --- | --- |
| 0 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 |

לשם השוואה, טבלת דלגלג SR היא 00: שמירת Q הישן, 01: 0, 10: 1, 11: מצב אסור. החיבורים שלנו משתמשים רק ב־01 וב־10. לכן Q(next)=D לכל ערך קודם של Q. בהיעדר חזית, Q נשמר גם אם D משתנה. במעגל אמיתי השינוי ביציאה מגיע אחרי השהיית clock-to-Q.

### מדוע סוג הרכיב חשוב?

אם SR הוא נועל שקוף או רכיב עם S,R אסינכרוניים, אותו חיבור יכול לגרום ל־Q לעקוב אחרי D בין חזיתות. זה אינו דלגלג D בחזית. נועל SR עם אפשור ובקשות S=EN AND D, R=EN AND NOT D נותן נועל D; כדי לקבל פעולה בחזית אפשר להשתמש במבנה master–slave תקין עם שלבי שעון משלימים ומגבלות תזמון. זה פתרון אחר, עם רכיבים והנחות נוספות, ולא מה שהשרטוט הזה טוען לממש.

### עלות והנחות תזמון

במודל הנבחר מספיקים דלגלג SR אחד ומהפך אחד. מבחינת ביטי מצב נדרש ביט אחד ואנו משתמשים בביט אחד; אין כאן הוכחת מינימום לשטח או להשהיה. במציאות המסלול הישיר והמסלול המהופך אינם באותה השהיה: מעבר D עלול ליצור לזמן קצר S=R=1. במודל סינכרוני אידאלי אין לכך השפעה אם לא דוגמים את החפיפה, אבל יש לבחור primitive מתאים ולעמוד בזמני setup/hold ולמנוע הפרת המצב האסור סמוך לחזית. הניסוח S=~R אינו הבטחה לאפס גליצ'ים פיזיים.

בדיקות פייתון עברו על כל ארבעת שילובי Q,D, שמונת שילובי Q,S,R, ועל 4,094 רצפי נתונים באורכים 0–10 משני מצבים התחלתיים, עם 36,868 חזיתות. הן בדקו גם שמירה בלי חזית ודחיית 11 בחזית. מצורף קוד SystemVerilog תיאורי, שלא קומפל או הורץ בסימולטור HDL. ההצעה ממתינה לביקורת מקצועית.''',
         '''### Translate data into a set or reset request

A D flip-flop stores the value sampled on D at each edge. No Q feedback is needed: request set when D=1 and reset when D=0. Connect:

```text
S = D
R = NOT D
SR clock = system clock
SR Q = D-flip-flop Q
```

The diagram branches D: one wire goes directly to S and the other passes through an inverter to R. The clock arrow enters the clock port, never a data port.

### Operation table

| D | S | R | Q after the rising edge |
| --- | --- | --- | --- |
| 0 | 0 | 1 | 0 |
| 1 | 1 | 0 | 1 |

For comparison, the SR primitive holds old Q on 00, resets on 01, sets on 10, and forbids 11. This wiring uses only 01 and 10, proving Q(next)=D for either previous Q. Without a rising edge Q holds even if D changes. Physical Q changes after clock-to-Q propagation delay.

### Why the primitive type matters

If SR is a transparent latch or the named S,R ports are asynchronous controls, this wiring can make Q follow D between edges. That is not an edge-triggered DFF. Gating an SR latch with S=EN AND D and R=EN AND NOT D produces a D latch; a valid master–slave design with complementary phases and timing constraints can create edge behavior. That is a different construction with additional primitives and assumptions, not what this schematic claims.

### Cost and timing assumptions

One SR state bit plus one inverter suffices in the declared model. One state bit is necessary and used; no minimum area or propagation-delay claim is made. Physical direct and inverted paths differ in delay, so a D transition can briefly produce S=R=1. An ideal synchronous primitive ignores an overlap away from its sampling aperture, but real primitive behavior, setup/hold and forbidden-state timing must be checked. Complementary Boolean equations do not guarantee glitch-free physical signals.

Python checks covered all four Q,D combinations, eight Q,S,R rows, and 4,094 data streams of lengths zero through ten from both starting states, totaling 36,868 rising edges. They also verified holding without an edge and rejecting 11 at an edge. Behavioral SystemVerilog is supplied but was not compiled or HDL-simulated. Independent professional review is pending.'''),
    {'assumptions': pair(['דלגלג SR בחזית עולה עם S,R סינכרוניים פעילים בגבוה; 11 אסור.', 'D עומד בתזמון בשני הנתיבים, כולל המהפך; אין איפוס נוסף.', 'הקשר בין DFF לנועל מוסבר בנפרד ואינו משנה בשקט את הרכיב הנתון.'],
                          ['Rising-edge synchronous active-high SR primitive; 11 forbidden.', 'D meets timing on both paths, including inversion; no additional reset.', 'Transparent-latch interpretation is distinguished explicitly.']),
         'optimality': pair({'criterion': 'מספר ביטי מצב.','result': 'ביט מצב אחד ומהפך אחד מספיקים במודל.','proof': 'יש לשמר שני מצבים, ולכן נדרש לפחות ביט אחד.','scope': 'אין הוכחת מינימום שערים, שטח או השהיה; סוג ה־primitive מהותי.'},{'criterion': 'State-bit count.','result': 'One state bit plus one inverter suffices.','proof': 'Two stored values require at least one state bit.','scope': 'No minimum gate/area/delay claim; primitive semantics matter.'}),
         'verification': pair('עברו 4 שילובי Q,D, שמונת שילובי SR, 4,094 רצפים ו־36,868 חזיתות במודל פייתון. קוד HDL לא קומפל ולא סומלץ; תזמון וגליצ׳ים פיזיים לא נבדקו.', 'Passed four Q,D combinations, eight SR rows, 4,094 streams and 36,868 edges in Python. HDL uncompiled/unsimulated; physical timing and glitches untested.'),
         'edge_cases': pair(['Q ראשוני אינו חייב להיות ידוע; החזית החוקית הראשונה קובעת D.', 'אין חזית: Q נשמר.', 'שינוי D סמוך לחזית עלול להפר תזמון.', 'S,R אסינכרוניים או נועל שקוף אינם מממשים את אותו חוזה.'],['Initial Q may be unknown; the first valid edge establishes D.', 'No edge means hold.', 'D changes near the edge may violate timing.', 'Asynchronous S,R or transparent latches have a different contract.']),
         'common_mistakes': pair(['לחבר S=D וגם R=D, וכך להגיע ל־11.', 'להשתמש בנועל שקוף ולקרוא לו DFF.', 'להניח שהמהפך מוחק כל חפיפה רגעית.', 'להציג איפוס אסינכרוני כקלט נתונים סינכרוני.'],['Driving both S and R from D, reaching 11.', 'Calling a transparent latch a DFF.', 'Assuming inversion removes every transient overlap.', 'Treating asynchronous clear as a synchronous data input.']),
         'interview_answer': pair('בהנחה שזה דלגלג SR סינכרוני בחזית, אחבר S=D ו־R=NOT D ואשתמש באותו clk. D=0 בוחר איפוס ו־D=1 בוחר קביעה, לכן אחרי החזית Q=D. אם נתון נועל או S,R אסינכרוניים, זה אינו אותו מימוש וצריך לדון במבנה שעון מתאים.', 'For an edge-triggered synchronous SR primitive, wire S=D and R=NOT D on the same clock. D=0 resets and D=1 sets, so Q after the edge equals D. A transparent latch or asynchronous controls need a different clocked construction.'),
         'solution_extensions': pair({'question': 'כיצד תוסיפו אפשור EN כך שב־EN=0 נשמור Q?','direction': 'ל־SR סינכרוני אפשר לבחור S=EN AND D ו־R=EN AND NOT D. ב־EN=0 מתקבל 00 ושמירה. בדקו גם תזמון של EN.','status': 'מוכן בתוכן; לא מחובר לתור המשך חי.'},{'question': 'How would you add an enable EN that holds Q when zero?','direction': 'For synchronous SR use S=EN AND D and R=EN AND NOT D. Disabled gives 00 and hold; EN also has timing constraints.','status': 'Prepared in content, not connected to the live follow-up queue.'})},
    ['latches_flip_flops','synchronous_design','truth_tables'], ['nvidia','hardware','mellanox'], ['NVIDIA','Mellanox'], 'מלאנוקס',
    ['solutions/prep_065_dff_from_sr.py','solutions/prep_065_dff_from_sr.sv'],
    [('solution_diagram','prep-065-sr-dff',pair('חיבורי D, מהפך, SR ושעון','D, inverter, SR and clock wiring'))], ['PREP-055','PREP-010'],
    'Related flip-flop/enable exercises do not ask conversion from a synchronous active-high SR primitive; retained as a distinct primitive-conversion question.')


add(67, 'eight-cell-synchronous-hardware-fifo',
    pair('FIFO סינכרוני בחומרה עם שמונה תאים','Eight-cell synchronous hardware FIFO'),
    'יש לממש FIFO בחומרה בגודל של 8 "תאי זיכרון".',
    pair('ממשו FIFO בחומרה בעומק שמונה תאים. הציגו זיכרון, מצביעי קריאה וכתיבה, דגלי full/empty ומימוש התנהגותי.\n\nהבהרות שנוספו למקור: בכל תא W ביטים, כאשר W מספר שלם חיובי. שעון עולה משותף לקריאה ולכתיבה ואיפוס סינכרוני פעיל בגבוה. קריאה מריק נדחית, ללא העברה מיידית של כתיבה ליציאה. כתיבה למלא נדחית אלא אם מתקבלת באותה חזית קריאה, ואז שניהם מתקבלים והפריט הישן נקרא לפני דריסתו. בכל מצב ביניים שתי בקשות מתקבלות יחד. dout הוא פלט רשום: אחרי קריאה שהתקבלה הוא מכיל את הפריט שנקרא ו־rd_valid=1 למחזור הבא; בלי קריאה הוא שומר ערך ו־rd_valid=0. איפוס גובר על הבקשות, מרוקן ומאפס את פלט הקריאה. אין דרישה לשני תחומי שעון.',
         'Implement a hardware FIFO of depth eight. Show memory, read/write pointers, full/empty flags and behavioral code.\n\nEditorial clarifications: each cell has W bits for positive integer W. Read and write share one rising-edge clock; reset is synchronous active high. Empty reads are rejected with no write-to-read bypass. Full writes are rejected unless a read is accepted at that same edge; then both are accepted and the old item is read before overwrite. Both requests are accepted at intermediate occupancy. dout is registered: after an accepted read it holds that item and rd_valid=1 for the following cycle; otherwise it holds its old value with rd_valid=0. Reset overrides requests, empties the FIFO and clears read outputs. This is not a dual-clock FIFO.'),
    pair(['איזה מידע צריך לשמור כדי לדעת מאיזה תא לקרוא, לאיזה תא לכתוב וכמה תאים תפוסים?', 'המצביעים חוזרים אחרי תא 7 לתא 0. מדוע שוויון בין המצביעים לבדו אינו מבדיל בין מלא לריק?', 'הוסיפו מונה תפוסה 0–8. קבעו קודם pop לפי המצב הישן, ואז push שיכול להתקבל במלא רק אם pop התקבל. עדכנו count בתוספת push פחות pop.'],
         ['What state tells us where to read, where to write and how many cells are occupied?', 'Pointers wrap from cell seven to zero. Why can pointer equality mean either full or empty?', 'Add occupancy 0..8. Determine pop from old state, then allow push at full only if pop is accepted. Update count by push minus pop.']),
    pair('''### מפרידים נתונים מסדר התור

לא מזיזים את כל הפריטים. נשמור מערך mem עם שמונה מילים ברוחב W, מצביע קריאה rp ומצביע כתיבה wp בני שלושה ביטים, ומונה count בן ארבעה ביטים כדי לייצג גם 8. rp מצביע לפריט הוותיק ביותר כאשר התור אינו ריק; wp הוא התא הבא שאליו תבוצע כתיבה שהתקבלה. המצביעים מתקדמים מעגלית, ולכן אחרי 7 מגיע 0.

```text
empty = (count == 0)
full  = (count == 8)
pop   = rd_en AND NOT empty
push  = wr_en AND (NOT full OR pop)
```

את כל התנאים מחשבים מהמצב שלפני החזית. אותות wr_accepted ו־rd_accepted בקוד הם אותות קבלה צירופיים המתארים מה יתקבל בחזית הבאה, ונחסמים בזמן rst. הם שונים מ־rd_valid, שמתאר את נתוני הקריאה הרשומים לאחר החזית.

### מה עושים בחזית?

אם rst=1: מאפסים rp,wp,count,dout,rd_valid. אין צורך לאפס את כל תאי mem: count=0 מונע קריאת ערך ישן. בלי איפוס: rd_valid מקבל pop. אם pop=1, שומרים ב־dout את mem[rp] הישן ומקדמים rp. אם push=1, כותבים din ל־mem[wp] ומקדמים wp. לבסוף count מקבל count+push−pop.

| תפוסה לפני החזית | wr_en | rd_en | push | pop | תפוסה אחרי החזית |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 1 | 0 | 0 | 0 |
| 0 | 1 | 1 | 1 | 0 | 1 |
| 1–7 | 1 | 1 | 1 | 1 | ללא שינוי |
| 8 | 1 | 0 | 0 | 0 | 8 |
| 8 | 1 | 1 | 1 | 1 | 8 |

יתר המקרים נובעים מהמשוואות: רק כתיבה חוקית מגדילה את count, רק קריאה חוקית מקטינה, וללא בקשות נשמר המצב. ב־count=1 וקריאה וכתיבה יחד נקרא הפריט היחיד הישן, והפריט החדש נשאר בתור. בריק שתי בקשות אינן קוראות את din מיד: רק הכתיבה מתקבלת, כפי שהוגדר.

### המקרה העדין: תור מלא ושתי בקשות

במלא rp=wp. נניח שהתור מכיל A עד H ושניהם מצביעים לתא A. קריאה וכתיבת X יחד מחזירות A ומחליפות את התא ב־X, מקדמות את שני המצביעים ושומרות count=8. הסדר הלוגי החדש הוא B,C,D,E,F,G,H,X. בקוד SystemVerilog עם מערך אוגרים והשמות לא חוסמות, צד ימין של dout <= mem[rp] נקרא מהערך הישן, לפני עדכון mem. אם מחליפים את המערך בבלוק RAM, חייבים לבחור התנהגות read-first מתאימה או להוסיף טיפול מפורש; אין להניח שכל RAM יתנהג כך.

### למה זה נכון וכמה זה עולה?

האינווריאנט: 0≤count≤8 והפריטים החיים נמצאים במיקומים rp עד rp+count−1 מודולו 8, לפי סדר הכניסה. הוספה כותבת בקצה הזה, וקריאה מוציאה מראשו. התנאים חוסמים גלישה וחסר, ושתי פעולות חוקיות מקיימות את שני הקצוות יחד. מכאן נשמר סדר FIFO.

הנתונים דורשים 8W ביטים. במימוש הזה יש עוד 6 ביטי מצביעים, 4 ביטי מונה, W ביטי פלט וביט rd_valid: סך לוגי 9W+11 ביטים, לפני תקורות המימוש הפיזי. הבקרה דורשת מספר קבוע של פעולות למחזור, ועד פריט אחד נקרא ואחד נכתב בכל חזית. אין כאן טענת שטח מינימלי; למשל אפשר להבדיל בין מלא וריק גם בעזרת ביטי גלישה במקום count. עיכוב ושעון מרבי תלויים במימוש הזיכרון ובספריית התאים.

בדיקת מודל בפייתון מול deque עצמאי עברה על 65,408 מעברים ממצבים בעלי נתונים בני ביט אחד: כל תוכני התור באורכים 0–8, כל סיבובי rp, הבקרות, din והפלט הקודם. עוד 16,352 מקרי איפוס ו־100,000 חזיתות מדגמיות עם נתונים בני 16 ביט נבדקו. קוד SystemVerilog צורף אך לא קומפל ולא סומלץ. אין בכך בדיקת RAM פיזית, CDC או תזמון. הפתרון מוצע וממתין לביקורת מקצועית.''',
         '''### Separate stored data from queue order

Do not shift every item. Use mem[0:7] of W-bit words, three-bit read/write pointers rp,wp, and a four-bit occupancy count that can represent eight. rp identifies the oldest item when nonempty; wp is the next accepted-write location. Both pointers wrap from seven to zero.

```text
empty = (count == 0)
full  = (count == 8)
pop   = rd_en AND NOT empty
push  = wr_en AND (NOT full OR pop)
```

All decisions use the pre-edge state. The combinational wr_accepted and rd_accepted outputs describe what will be accepted at the next edge and are blocked during reset. They differ from rd_valid, which describes the registered read result after the edge.

### Edge updates

With rst=1 clear rp,wp,count,dout,rd_valid. Memory cells need not be reset because zero occupancy blocks stale-data reads. Otherwise assign rd_valid=pop. If pop, capture old mem[rp] in dout and advance rp. If push, write din to mem[wp] and advance wp. Set count to count+push−pop.

| Pre-edge occupancy | wr_en | rd_en | push | pop | Post-edge occupancy |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 1 | 0 | 0 | 0 |
| 0 | 1 | 1 | 1 | 0 | 1 |
| 1–7 | 1 | 1 | 1 | 1 | unchanged |
| 8 | 1 | 0 | 0 | 0 | 8 |
| 8 | 1 | 1 | 1 | 1 | 8 |

Other cases follow directly: a legal write alone increments occupancy, a legal read alone decrements it, and no requests hold it. At occupancy one, simultaneous operations return the old sole item and retain the new one. At empty, simultaneous requests accept only the write; there is no immediate din bypass by contract.

### The subtle full case

At full, rp=wp. Suppose items A through H fill the FIFO and both pointers address A. Reading while writing X returns A, replaces that cell with X, advances both pointers and keeps occupancy eight. Logical order becomes B,C,D,E,F,G,H,X. In the supplied register-array SystemVerilog, nonblocking assignments read old mem[rp] before updating memory. A replacement RAM block needs documented read-first behavior or explicit collision handling; not every RAM has this behavior.

### Correctness and cost

Invariant: occupancy stays in zero through eight, and live items occupy rp through rp+count−1 modulo eight in insertion order. Push appends at the end, pop removes the front, boundary guards prevent overflow/underflow, and legal simultaneous operations update both ends. Thus FIFO order is preserved.

Storage uses 8W data bits. This construction also has six pointer bits, four count bits, W output bits and one valid bit, totaling 9W+11 logical state bits before physical implementation overhead. Control uses a constant number of operations per cycle and supports up to one read and one write per edge. No minimum-area claim is made; wrap bits can replace the occupancy scheme. Delay and maximum clock rate depend on memory/cell technology.

Python comparison against an independent deque passed 65,408 transitions over every one-bit live queue content of lengths zero through eight, all rp rotations, controls, din and previous dout. A further 16,352 reset cases and 100,000 sampled sixteen-bit edges passed. Supplied SystemVerilog was not compiled or HDL-simulated. These are not physical RAM, CDC or timing checks. Independent professional review is pending.'''),
    {'assumptions': pair(['עומק 8, רוחב W≥1; שעון יחיד ואיפוס סינכרוני פעיל בגבוה.', 'אין bypass בריק; במלא אפשר לקרוא ולכתוב יחד ולהחזיר את הפריט הישן.', 'dout רשום; rd_valid תקף אחרי חזית קריאה שהתקבלה. בלי קריאה dout נשמר.', 'איפוס מנקה את מצב הבקרה והפלט, אך לא את הזיכרון; נדרשת חזית איפוס לפני שימוש.', 'מערך אוגרים תומך בקריאת ערך ישן וכתיבה יחד; מימוש RAM חלופי מחייב חוזה תואם.'],['Depth eight, W≥1; one rising-edge clock and synchronous active-high reset.', 'No bypass at empty; full permits simultaneous read/write with old-data return.', 'Registered dout; rd_valid marks the cycle after an accepted read. No read holds dout.', 'Reset clears control/output state, not memory; reset edge required before use.', 'Register array provides old-data simultaneous read/write; replacement RAM requires a matching contract.']),
         'optimality': pair({'criterion': 'קצב וסיבוכיות למימוש שנבחר.','result': 'עד קריאה וכתיבה אחת בחזית; O(1) פעולות בקרה למחזור. מצב לוגי 9W+11 ביטים.','proof': 'אין הזזת התור; רק גישה ממוספרת, קידום שני מצביעים ועדכון תפוסה.','scope': 'אין מינימום שטח/מספר FF/השהיה; העלות הפיזית תלויה במיפוי זיכרון.'},{'criterion': 'Throughput and operation count for this construction.','result': 'Up to one read and one write per edge; O(1) control operations/cycle; 9W+11 logical state bits.','proof': 'No shifting: indexed access, at most two pointer advances and occupancy update.','scope': 'No minimum area/FF/delay claim; physical cost depends on storage mapping.'}),
         'verification': pair('עברו 65,408 מעברים ממצבי תור בני ביט אחד, 16,352 מקרי עדיפות איפוס ו־100,000 חזיתות מדגמיות עם נתוני 16 ביט מול deque עצמאי. קוד SystemVerilog לא קומפל ולא סומלץ.', 'Passed 65,408 one-bit-state transitions, 16,352 reset-priority cases and 100,000 sampled sixteen-bit edges against independent deque. SystemVerilog uncompiled/unsimulated.'),
         'edge_cases': pair(['שוויון rp=wp יכול להיות ריק או מלא; count מכריע.', 'בריק שתי בקשות מקבלות רק כתיבה, ללא rd_valid.', 'במלא שתי בקשות מתקבלות יחד; יש להחזיר את הערך הישן.', 'ב־count=1 שתי בקשות מחליפות את הפריט בלי שינוי תפוסה.', 'איפוס בעת שתי בקשות דוחה אותן ומאפס פלט.', 'כמה סיבובים אינם משנים סדר; אין לאפס את הזיכרון כדי למנוע קריאת זבל.'],['Equal pointers mean empty or full; count distinguishes them.', 'Empty with both requests accepts only push and no read-valid.', 'Full with both requests accepts both and must return old data.', 'At count one both requests replace the item without changing occupancy.', 'Reset with both requests rejects both and clears read outputs.', 'Wrap preserves order; occupancy prevents stale reads without resetting memory.']),
         'common_mistakes': pair(['מונה בן שלושה ביטים שאינו מסוגל לייצג 8.', 'שוויון המצביעים משמש גם כמלא וגם כריק בלי ביט נוסף.', 'הגדלת count על בקשה שנדחתה.', 'שינוי מדיניות גבול בלי לתעד אותה.', 'לקרוא mem לאחר שדרסנו את התא במודל תוכנה.', 'להציג FIFO חד־שעוני כפתרון בטוח לשני שעונים בלתי תלויים.'],['Using a three-bit count that cannot represent eight.', 'Pointer equality alone for both full and empty.', 'Changing occupancy on rejected requests.', 'Silently changing boundary policy.', 'Overwriting before reading in a software model.', 'Claiming single-clock control safely handles unrelated clocks.']),
         'interview_answer': pair('אשתמש במערך 8×W, שני מצביעים בני שלושה ביטים ומונה תפוסה בן ארבעה. pop חוקי רק כשהתור אינו ריק; push חוקי כשאינו מלא או כשיש pop באותה חזית. אקרא את הפריט הישן, אכתוב בקצה, אקדם רק מצביעים של פעולות שהתקבלו ואעדכן count ב־push פחות pop. הפלט רשום עם rd_valid.', 'Use eight W-bit cells, two three-bit pointers and four-bit occupancy. Pop only when nonempty; push when not full or with a same-edge valid pop. Read old front, write at tail, advance only accepted-operation pointers and update count by push minus pop. Read output is registered with rd_valid.'),
         'solution_extensions': pair({'question': 'מה נדרש אם צד הקריאה והכתיבה פועלים בשעונים שונים?','direction': 'זה FIFO אסינכרוני: נדרשים מצביעים וביטי גלישה, קידוד Gray וסנכרון לכל תחום שעון, חישוב דגלים מקומי וניתוח CDC. אין להעביר count בינארי רב־ביטי ישירות.','status': 'מוכן בתוכן; לא מחובר לתור המשך חי.'},{'question': 'What changes when readers and writers use unrelated clocks?','direction': 'An asynchronous FIFO needs wrap-aware pointers, Gray encoding, cross-domain synchronizers, local flags and CDC analysis. Do not pass a multi-bit binary occupancy count directly between clocks.','status': 'Prepared in content, not connected to the live follow-up queue.'})},
    ['fifo','registers_shifters','synchronous_design'], ['nvidia','amazon','hardware','apple'], ['NVIDIA','Amazon','Apple'], 'אפל',
    ['solutions/prep_067_fifo8.py','solutions/prep_067_fifo8.sv'],
    [('solution_diagram','prep-067-fifo8',pair('זיכרון מעגלי, פלט רשום ובקרת FIFO','Circular memory, registered output and FIFO control'))], ['PREP-006','PREP-044'],
    'Existing queue/data-structure or register questions do not specify eight physical cells, acceptance at full/empty, registered read outputs and one-clock hardware control; distinct hardware construction.')


add(69, 'nor-branch-stuck-at-fault-observability',
    pair('תקלה תקועה בענף NOR — מה אפשר לזהות?','Stuck-at fault on a NOR branch — what is observable?'),
    'נתון המעגל שבתמונה אשר בנקודה המסומנת X בכחול תיתכן תקלה. התקלות האפשריות הן שהנקודה תהיה מקוצרת ל־0 לוגי (stuck@0) או שהנקודה תהיה מקוצרת ל־1 לוגי (stuck@1). אילו קלטים נכניס למעגל בכדי לבדוק מה התקלה שקיימת בנקודה?',
    pair('במעגל הנתון A מגיע ישירות לשער AND בעל שלוש כניסות. B וענף של C נכנסים ל־NOR שמוצאו מגיע לכניסה השנייה של ה־AND. ענף נפרד של C עובר במהפך, ומוצא המהפך מגיע לכניסה השלישית של ה־AND. נקודת X נמצאת רק על ענף C שנכנס ל־NOR, אחרי הפיצול; ענף המהפך נשאר תקין.\n\nידוע שב־X קיימת אחת משתי תקלות: stuck-at-0 או stuck-at-1. אפשר לשלוט ב־A,B,C ולמדוד רק את Y במוצא. איזה וקטור בדיקה יאפשר להבחין בין שתי התקלות? הרחבה להבהרת מגבלת האבחון: אם גם מעגל תקין הוא אפשרות, האם ניתן להפריד בין כל שלושת המצבים? עבדו במודל בינארי צירופי ללא תזמון או תקלות נוספות.',
         'A feeds a three-input AND directly. B and one branch of C feed a NOR whose output is the second AND input. A separate C branch passes through an inverter into the third AND input. X lies only on the C-to-NOR branch after fanout; the inverter branch remains healthy.\n\nExactly one fault is known to exist at X: stuck-at-0 or stuck-at-1. You may control A,B,C and observe Y only. Which test vector distinguishes the two faults? Diagnostic-limit extension: if a healthy circuit is also possible, can all three states be distinguished? Use an ideal combinational binary model with no delays or other faults.'),
    pair(['כדי שהבדל בנקודה פנימית יגיע ליציאה, צריך גם ליצור את ההבדל וגם לא לחסום אותו בשער הבא.', 'לצורך הפצת שינוי דרך AND, שאר כניסותיו צריכות להיות 1. מה זה מחייב לגבי A ו־C?', 'אם C=0 ו־B=0, מוצא ה־NOR התקין הוא 1. בדקו מה קורה כאשר X=1. נסו גם ליצור הבדל לתקלה X=0 באמצעות C=1, ובדקו את ענף המהפך.'],
         ['An internal fault must first create a difference and then propagate it through the remaining gates.', 'To propagate through AND, its other inputs must be one. What does that require for A and C?', 'With C=0 and B=0 the healthy NOR outputs one. Check X=1. To activate X stuck at zero, try C=1 and examine the inverter branch.']),
    pair('''### כותבים קודם את מיקום התקלה במדויק

נסמן x כערך שבאמת נכנס לכניסה התחתונה של ה־NOR. תקין: x=C; תקלה תקועה באפס: x=0; תקלה תקועה באחת: x=1. ענף המהפך עדיין מקבל את C המקורי. לכן:

```text
Y = A AND NOT(B OR x) AND NOT C
Y(clean) = A AND NOT B AND NOT C
Y(sa0)   = A AND NOT B AND NOT C
Y(sa1)   = 0
```

שימו לב לתוצאה: תקלה תקועה באפס אינה משנה את פונקציית המוצא כלל. זו אינה טעות בחישוב; במעגל קיימת יתירות מבחינת התקלה המסוימת הזאת.

### מזהים stuck-at-1

נרצה שבמעגל תקין x יהיה 0 כדי שתהיה הבחנה מ־x התקוע ב־1. לכן בוחרים C=0. כדי שה־NOR יגיב ל־x בוחרים B=0. כדי ש־AND לא יחסום בוחרים A=1; המהפך ממילא נותן 1 כי C=0. נקבל וקטור בדיקה יחיד:

```text
A=1, B=0, C=0
Y(clean)=1, Y(sa0)=1, Y(sa1)=0
```

אם יודעים בוודאות שיש אחת משתי התקלות, Y=0 מזהה sa1 ו־Y=1 מזהה sa0 בתהליך אלימינציה. אם גם מצב תקין אפשרי, Y=1 אינו מוכיח שיש תקלה באפס: הוא תואם גם מעגל תקין. זה ההבדל בין זיהוי תקלה לבין אבחון תחת הנחה שקיימת תקלה.

### מדוע אי אפשר לזהות stuck-at-0 מול תקין?

כדי שהערך התקוע x=0 יהיה שונה מהערך התקין צריך C=1. אבל אז ענף המהפך נותן NOT C=0, ו־AND מוציא 0 ללא תלות ב־NOR. אם C=0, x=0 זהה לערך התקין מלכתחילה. אלה כל האפשרויות ל־C, ולכן אין אף וקטור ב־A,B,C שמבדיל sa0 מתקין. מספר בלתי מוגבל של בדיקות באותה נקודת מדידה לא יעזור.

### כל טבלת האמת

| A | B | C | Y תקין | Y תקוע באפס | Y תקוע באחת |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 0 |
| 0 | 0 | 1 | 0 | 0 | 0 |
| 0 | 1 | 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 | 0 | 0 |
| 1 | 0 | 0 | 1 | 1 | 0 |
| 1 | 0 | 1 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 1 | 1 | 0 | 0 | 0 |

הטבלה מוכיחה גם ש־100 הוא הווקטור היחיד שמזהה sa1 מול תקין במודל הזה. בדיקה אחת מספיקה להפריד בין שני סוגי התקלה כאשר ידוע שאחת קיימת; אפס בדיקות לא יכולות להפריד ביניהם. אין כאן פתרון לזיהוי כל שלושת המצבים, משום שתקין ו־sa0 שקולים ביציאה.

השרטוט שבשאלה הוא שרטוט נקי של הנתון בלבד. השרטוט בפתרון מוסיף משוואה ותוצאת בדיקה, וה־X נמצא אחרי נקודת הפיצול בענף NOR. אילו התקלה הייתה על הגזע לפני הפיצול, גם המהפך היה מקבל את הערך התקוע והבעיה הייתה אחרת. האימות עבר על כל 8 קלטי A,B,C ושלוש גרסאות המעגל, 24 חישובים. זו בדיקה בינארית מלאה; לא בוצעה הזרקת תקלות לחומרה או בדיקת תזמון. ביקורת מקצועית ממתינה.''',
         '''### Model the fault location exactly

Let x be the actual NOR branch input. Healthy x=C; stuck-at-0 x=0; stuck-at-1 x=1. The inverter still receives original C. Therefore:

```text
Y = A AND NOT(B OR x) AND NOT C
Y(clean) = A AND NOT B AND NOT C
Y(sa0)   = A AND NOT B AND NOT C
Y(sa1)   = 0
```

Stuck-at-0 does not alter the output function. This is real redundancy for this fault, not a calculation error.

### Detect stuck-at-1

To differ from x stuck at one, choose healthy x=0, hence C=0. Set B=0 so the NOR responds to x. Set A=1 so AND does not block propagation; the inverter also outputs one because C=0. The test is:

```text
A=1, B=0, C=0
Y(clean)=1, Y(sa0)=1, Y(sa1)=0
```

If exactly one of the two faults is known to exist, Y=0 identifies sa1 and Y=1 identifies sa0 by elimination. If healthy operation is possible, Y=1 cannot prove a stuck-at-zero fault because a healthy circuit gives the same result. This separates detection from diagnosis under a prior fault guarantee.

### Why no test distinguishes sa0 from healthy

Activating a difference between x stuck at zero and healthy x requires C=1. Then the healthy inverter produces NOT C=0, forcing the final AND to zero regardless of the NOR result. At C=0, x=0 already equals the healthy value. These exhaust C, so no A,B,C vector distinguishes sa0 from healthy. Unlimited repetitions at the same output cannot help.

### Complete truth table

| A | B | C | Healthy Y | Stuck-at-0 Y | Stuck-at-1 Y |
| --- | --- | --- | --- | --- | --- |
| 0 | 0 | 0 | 0 | 0 | 0 |
| 0 | 0 | 1 | 0 | 0 | 0 |
| 0 | 1 | 0 | 0 | 0 | 0 |
| 0 | 1 | 1 | 0 | 0 | 0 |
| 1 | 0 | 0 | 1 | 1 | 0 |
| 1 | 0 | 1 | 0 | 0 | 0 |
| 1 | 1 | 0 | 0 | 0 | 0 |
| 1 | 1 | 1 | 0 | 0 | 0 |

The table also proves that 100 is the only vector detecting sa1 versus healthy in this model. One test suffices to distinguish the two fault types if exactly one is guaranteed present; zero observations cannot separate them. Distinguishing all three states is impossible because healthy and sa0 are output-equivalent.

The question uses a clean data-only schematic; the solution schematic adds equations and a test result. X remains after fanout on the NOR branch. A stem fault before fanout would also alter the inverter and create a different problem. All eight input combinations and three circuit versions were checked, totaling twenty-four evaluations. This is exhaustive binary-model verification, not hardware fault injection or timing testing. Independent professional review is pending.'''),
    {'assumptions': pair(['תקלה יחידה בענף C אל NOR אחרי הפיצול; ענף המהפך תקין.', 'שליטה רק ב־A,B,C ותצפית רק ב־Y; לוגיקה צירופית בינארית.', 'מפרידים בין הנחת תקלה ודאית לבין אפשרות שהמעגל תקין.'],['Single C-to-NOR branch fault after fanout; inverter branch healthy.', 'Control A,B,C, observe Y only; ideal binary combinational logic.', 'Guaranteed-fault diagnosis is distinguished from a possible healthy circuit.']),
         'optimality': pair({'criterion': 'מספר בדיקות להפרדה בין שתי תקלות ודאיות.','result': 'בדיקת 100 אחת מספיקה; אין בדיקה שמפרידה תקין מ־sa0.','proof': '100 נותן 1 ב־sa0 ו־0 ב־sa1. שתי פונקציות תקין ו־sa0 זהות בכל התחום.','scope': 'בלי הנחת תקלה ודאית לא ניתן לאבחן את שלושת המצבים במוצא Y בלבד.'},{'criterion': 'Tests separating the two guaranteed fault hypotheses.','result': 'One test, 100, suffices; no test separates healthy from sa0.','proof': '100 gives one for sa0 and zero for sa1. Healthy and sa0 functions are identical over the full domain.','scope': 'Without the guaranteed-fault assumption, three-way diagnosis from Y alone is impossible.'}),
         'verification': pair('כל שמונת הקלטים בשלוש גרסאות המעגל עברו, 24 חישובים. זוהה 100 כווקטור היחיד ל־sa1; לא נמצא הבדל יחיד בין sa0 לתקין, בהתאמה להוכחה האלגברית. אין בדיקת חומרה פיזית.', 'All eight inputs across three circuit versions passed, twenty-four evaluations. 100 is the only sa1-detecting vector; healthy and sa0 agree everywhere, matching the algebraic proof. No physical hardware checks.'),
         'edge_cases': pair(['A=0 או B=1 חוסמים כל תצפית שימושית.', 'C=1 מפעיל את תקלה באפס אך גם חוסם את AND.', 'Y=1 ב־100 אינו מפריד תקין מתקלה באפס.', 'תקלה על C לפני הפיצול היא בעיה שונה.'],['A=0 or B=1 blocks useful propagation.', 'C=1 activates sa0 but also blocks the AND.', 'Y=1 at 100 cannot distinguish healthy from sa0.', 'A C-stem fault before fanout is a different problem.']),
         'common_mistakes': pair(['להחליף את C גם בכניסת המהפך כשמזריקים תקלה לענף בלבד.', 'להפעיל תקלה פנימית בלי לבדוק שהיא מגיעה למוצא.', 'להבטיח זיהוי sa0 מתקין למרות יתירות לוגית.', 'לבלבל אבחון בהנחת תקלה ודאית עם זיהוי עצם התקלה.'],['Changing the inverter input when injecting only a branch fault.', 'Activating a fault without checking output propagation.', 'Promising sa0 detection despite functional redundancy.', 'Confusing guaranteed-fault diagnosis with detecting whether a fault exists.']),
         'interview_answer': pair('אכתוב Y=A·NOT(B OR x)·NOT C. ב־100 תקין ו־sa0 נותנים 1 ו־sa1 נותן 0. sa0 אינו ניתן לזיהוי מול תקין: כדי ליצור הבדל צריך C=1, ואז המהפך מאפס את AND. אם ידוע מראש שיש אחת משתי התקלות, אותה בדיקה יחידה מבדילה ביניהן.', 'Write Y=A·NOT(B OR x)·NOT C. At 100, healthy and sa0 give one, while sa1 gives zero. sa0 cannot be detected versus healthy: activating it requires C=1, whose inverter output blocks AND. If one of the two faults is guaranteed, that one test distinguishes them.'),
         'solution_extensions': pair({'question': 'איך נוכל להפוך גם את sa0 לנצפית?','direction': 'אפשר להוסיף נקודת תצפית למוצא ה־NOR. שם C=1,B=0 ייתן 0 בתקין ו־1 ב־sa0, בלי חסימת ענף המהפך. זה משנה את נגישות הבדיקה, לא את תשובת המעגל המקורי.','status': 'מוכן בתוכן; לא מחובר לתור המשך חי.'},{'question': 'How could sa0 become observable too?','direction': 'Add an observation point at the NOR output. With C=1,B=0 it is zero when healthy and one under sa0, without inverter-path masking. This changes test access, not the original circuit answer.','status': 'Prepared in content, not connected to the live follow-up queue.'})},
    ['fault_detection','boolean_algebra','truth_tables'], ['hardware','nvidia','amazon','intel','apple'], ['NVIDIA','Amazon','Intel','Apple'], 'אינטל',
    ['solutions/prep_069_branch_fault.py'],
    [('prompt_diagram','prep-069-prompt',pair('המעגל הנתון ומיקום תקלת הענף','Given circuit and branch fault location')),
     ('solution_diagram','prep-069-solution',pair('הפצת התקלה והבדיקה המבחינה','Fault propagation and distinguishing test')),
     ('solution_diagram','prep-069-truth-table',pair('טבלת אמת מלאה לשלוש גרסאות המעגל','Full truth table for three circuit versions'))], ['PREP-013','PREP-030'],
    'No existing catalog exercise has this branch-specific NOR/inverter reconvergence and redundant sa0 fault; related gate/debugging questions are retained separately.')


add(70, 'and-gate-with-one-two-to-one-mux',
    pair('מימוש שער AND באמצעות MUX 2:1 יחיד','Implement AND with one 2:1 MUX'),
    'ממש שער AND מ MUX2:1',
    pair('ממשו Y=A AND B בעזרת מרבב MUX 2:1 יחיד. ציינו את חיבורי D0,D1,S ושרטטו את המעגל.\n\nהבהרות: הכניסות בינאריות, המרבב בוחר D0 כאשר S=0 ו־D1 כאשר S=1. מותר לחבר קבוע לוגי 0 וחוטים, אך אין להשתמש בשער לוגי נוסף. זהו מעגל צירופי ללא שעון.',
         'Implement Y=A AND B with one 2:1 multiplexer. Specify D0,D1,S and draw the circuit.\n\nClarifications: binary signals; the MUX chooses D0 for S=0 and D1 for S=1. Constant logic zero and wires are allowed, but no additional logic gate. This is combinational, with no clock.'),
    pair(['בחרו אחת הכניסות כבוררת ובדקו מה הפלט צריך להיות בכל אחד משני ערכיה.', 'כאשר A=0 הפלט תמיד 0; כאשר A=1 הפלט שווה ל־B.', 'חברו A לבחירה S. קבעו איזה אות צריך להופיע ב־D0 ואיזה ב־D1 לפי שתי השורות האלה.'],
         ['Choose one input as select and ask what the output must be for each select value.', 'When A=0 the output is always zero; when A=1 it equals B.', 'Wire A to S. Choose D0 and D1 from those two cases.']),
    pair('''### חושבים לפי הבחירה של המרבב

מרבב אינו דורש ששתי כניסות הנתונים יהיו קבועות. אפשר לחבר אחת מהן לאות B. נבחר את A כבורר:

```text
S  = A
D0 = 0
D1 = B
Y  = MUX(S,D0,D1)
```

בשרטוט החץ של A נכנס ל־S בתחתית. הקבוע 0 נכנס ל־D0 העליון, ו־B נכנס ל־D1 התחתון. המספרים 0 ו־1 הם מספרי פורטי הנתונים הנבחרים לפי S; אין הכוונה לחבר קבוע 1 ל־D1.

### למה החיבור הזה עובד?

כאשר A=0 המרבב בוחר D0=0, בדיוק כמו AND עם אחת הכניסות אפס. כאשר A=1 הוא בוחר D1=B, בדיוק כמו AND עם כניסה אחת 1. בנוסחת המרבב:

```text
Y = (NOT S AND D0) OR (S AND D1)
  = (NOT A AND 0) OR (A AND B)
  = A AND B
```

| A | B | פורט נבחר | Y |
| --- | --- | --- | --- |
| 0 | 0 | D0 | 0 |
| 0 | 1 | D0 | 0 |
| 1 | 0 | D1 | 0 |
| 1 | 1 | D1 | 1 |

גם החיבור הסימטרי S=B,D0=0,D1=A תקף. אין צורך במהפך, דלגלג או שעון. מספר הרכיבים הוא MUX אחד וקבוע אפס. תחת מודל שמותר בו רק חוטים וקבועים בלי שום רכיב פונקציונלי, אי אפשר להפיק AND באמצעות אפס מרבבים: חוט יחיד נותן A,B או קבוע, ואף אחד מהם אינו פונקציית AND לכל הקלטים. לכן אחד הוא המינימום במודל הזה; אין בכך הוכחה לשטח מינימלי בספריית תאים אחרת.

נבדקו כל 8 שורות פונקציית המרבב, 4 שורות AND ו־4 שורות החיבור הסימטרי. אלה בדיקות לוגיות מלאות של המודל, ללא סינתזה או מדידת השהיה. הפתרון מוצע וממתין לביקורת מקצועית.''',
         '''### Reason by the select cases

MUX data inputs need not both be constants: one can carry B. Choose A as select:

```text
S  = A
D0 = 0
D1 = B
Y  = MUX(S,D0,D1)
```

In the diagram A enters the bottom S port. Constant zero enters upper D0 and B enters lower D1. The digits in D0/D1 identify selected data ports; D1 is not tied to constant one.

### Why it works

At A=0 the MUX selects constant zero, matching AND with one zero input. At A=1 it selects B, matching AND with one input held high. Algebraically:

```text
Y = (NOT S AND D0) OR (S AND D1)
  = (NOT A AND 0) OR (A AND B)
  = A AND B
```

| A | B | Selected port | Y |
| --- | --- | --- | --- |
| 0 | 0 | D0 | 0 |
| 0 | 1 | D0 | 0 |
| 1 | 0 | D1 | 0 |
| 1 | 1 | D1 | 1 |

The symmetric S=B,D0=0,D1=A also works. No inverter, storage or clock is needed: one MUX and a zero constant suffice. With only wires and constants and no functional component, zero MUXes can output only A,B or a constant, none equal to AND on every input. Therefore one is minimal in this restricted component model, not a minimum physical-area result for other cell libraries.

Checks covered all eight MUX rows, four AND rows and four symmetric-wiring rows. These are exhaustive logical-model checks, not synthesis or propagation-delay measurements. Independent professional review is pending.'''),
    {'assumptions': pair(['מרבב אידאלי בוחר D0 ב־S=0 ו־D1 ב־S=1.', 'קבוע אפס וחוטים מותרים; אין שער נוסף או שעון.'],['Ideal MUX chooses D0 at S=0 and D1 at S=1.', 'Zero constant and wires allowed; no additional gate or clock.']),
         'optimality': pair({'criterion': 'מספר מרבבים כשמותר רק חיווט וקבועים לצדם.','result': 'מרבב אחד נחוץ ומספיק.','proof': 'בלי רכיב פונקציונלי אפשר לקבל רק כניסה או קבוע, ולא AND; המימוש משתמש באחד.','scope': 'אין טענת שטח או השהיה מינימליים בספריית שערים כללית.'},{'criterion': 'MUX count with only wires and constants otherwise.','result': 'One MUX is necessary and sufficient.','proof': 'With no functional component only a primary input or constant is possible, not AND; construction uses one.','scope': 'No minimum physical area/delay claim for a general cell library.'}),
         'verification': pair('עברו כל 8 שורות המרבב, כל 4 שורות AND ו־4 שורות המימוש הסימטרי בפייתון. לא בוצעה סינתזה או בדיקת חומרה.', 'Passed all eight MUX rows, four AND rows and four symmetric-implementation rows in Python. No synthesis or hardware tests.'),
         'edge_cases': pair(['A=0 קובע אפס בלי תלות ב־B.', 'A=1 מעביר B, כולל B=0.', 'אם ספריית הרכיבים משתמשת במוסכמת בחירה הפוכה יש להתאים את שמות הפורטים.', 'החלפת D0,D1 בלי להחליף תנאי בחירה נותנת פונקציה אחרת.'],['A=0 forces zero independently of B.', 'A=1 forwards B, including B=0.', 'A library with reversed select convention needs corresponding port mapping.', 'Swapping D0 and D1 without changing selection gives a different function.']),
         'common_mistakes': pair(['לחבר D1 לקבוע 1 במקום ל־B, וכך להחזיר רק A.', 'להחליף בין פורט הבחירה לפורט נתונים.', 'להוסיף שער AND וכך לעקוף את השאלה.', 'לצייר חוטים ללא מספרי הפורטים ולכן לא להגדיר מה נבחר.'],['Tying D1 high instead of B, which outputs only A.', 'Confusing select and data ports.', 'Adding an AND gate and bypassing the constraint.', 'Omitting port numbers so select behavior remains ambiguous.']),
         'interview_answer': pair('אבחר A כ־S, אחבר D0=0 ו־D1=B. כאשר A=0 נקבל 0 וכאשר A=1 נקבל B, ולכן בדיוק A AND B. מספיק מרבב אחד, ללא שעון או שער נוסף.', 'Use S=A,D0=0,D1=B. Select zero returns zero; select one returns B, exactly A AND B. One MUX suffices with no clock or extra gate.'),
         'solution_extensions': pair({'question': 'כיצד תממשו OR בעזרת אותו סוג מרבב יחיד?','direction': 'בחרו S=A,D0=B,D1=1: כאשר A=0 צריך B וכאשר A=1 צריך תמיד 1. נדרש קבוע 1 מותר בגרסת ההמשך.','status': 'מוכן בתוכן; לא מחובר לתור המשך חי.'},{'question': 'How would you implement OR with one such MUX?','direction': 'Use S=A,D0=B,D1=1: when A=0 return B; when A=1 return one. This follow-up explicitly permits a high constant.','status': 'Prepared in content, not connected to the live follow-up queue.'})},
    ['combinational_blocks','multiplexers','boolean_algebra'], ['apple','hardware','nvidia'], ['Apple','NVIDIA'], 'Nvidia',
    ['solutions/prep_070_and_mux.py'],
    [('solution_diagram','prep-070-and-mux',pair('מרבב יחיד עם שמות פורטים וכיוון אותות','One MUX with numbered ports and signal arrows'))], ['PREP-011','PREP-031'],
    'Existing MUX implementations cover other Boolean/arithmetic functions; this is the elementary one-MUX AND construction, retained as a linked constraint-specific question.')


if __name__=='__main__':
    (OUT/'hardware.json').write_text(json.dumps({'questions': questions,'editorial': editorial,'localization': localization},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {len(questions)} hardware questions and paired material localizations')
