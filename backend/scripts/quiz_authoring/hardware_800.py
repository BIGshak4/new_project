"""Bilingual circuit exercises derived from the linked interview questions.

Each case has its own question, worked calculation and three explicit alternatives.
The first case doubles as the short card. Run this module to regenerate the shards.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTENT = ROOT / "apps/web/src/content"
SHARDS = ROOT / "backend/seeds/duel_quiz_batches"


def bilingual(line):
    he, en = (field.strip() for field in line.split("~"))
    return {"he": he, "en": en}


def build_bundle(lessons):
    cards, questions, checks = [], [], []
    for block in lessons.strip().split("\n\n"):
        header, title_line, scenario_line, principle_line, *cases = block.strip().splitlines()
        number, prep, topic, level = header.split()
        source = f"quick-hw-{number}"
        title, scenario, principle = map(bilingual, (title_line, scenario_line, principle_line))
        assert len(cases) == 5, source
        for variant, case in enumerate(cases, 1):
            he, en, working, options_line = (part.strip() for part in case.split("~"))
            options = options_line.split(";")
            assert len(set(options)) == 4, (source, variant)
            result = options[0]
            offset = (int(number) + variant) % 4
            options = options[offset:] + options[:offset]
            prompt = {lang: f"{scenario[lang]} {ask}" for lang, ask in (("he", he), ("en", en))}
            explanation = {lang: f"{result}. {principle[lang]} {working}." for lang in ("he", "en")}
            key = f"{source}-v{variant}"
            questions.append(
                dict(
                    key=key,
                    source_key=source,
                    variant=variant,
                    topic=topic,
                    status="draft",
                    prompt=prompt,
                    choices=[{"he": value, "en": value} for value in options],
                    correct=options.index(result),
                    explanation=explanation,
                )
            )
            checks.append(
                dict(
                    key=key,
                    task=int(number),
                    inputs={"scenario": scenario, "query": {"he": he, "en": en}},
                    options=options,
                    expected=result,
                    difficulty=int(level),
                    difficulty_rationale=f"Trace or calculate the quantity for {title['en'].lower()} under the stated assumptions.",
                    coverage=en,
                    interview_ids=[f"PREP-{prep}"],
                    working=working,
                    provenance="An original exercise derived from the linked interview question.",
                    method="Numerical reference results in test_fundamentals_hardware_800.py.",
                    scope="The stated discrete circuit trace or ideal electrical model.",
                )
            )
            if variant == 1:
                cards.append(
                    dict(
                        id=source,
                        topic=topic,
                        interviewIds=[f"PREP-{prep}"],
                        title=title,
                        prompt=prompt,
                        answer=explanation,
                        takeaway=principle,
                    )
                )
    return cards, questions, checks


LESSONS = """
351 366 electronics 3
הפרש דרך באורכי גל ~ Path difference in wavelengths
גל מישורי שאורך הגל שלו 12 ס״מ מגיע לשתי אנטנות. מגדירים הפרש פאזה חיובי כאשר הפרש הדרך חיובי. ~ A plane wave of wavelength 12 cm arrives at two antennas. Positive path difference gives positive phase difference.
כל אורך גל נוסף בדרך תורם סיבוב פאזה מלא. ~ Each extra wavelength of travel contributes one full turn of phase.
מהו הפרש הפאזה במעלות עבור הפרש דרך של 3 ס״מ? ~ What phase difference in degrees corresponds to 3 cm of extra travel? ~ 360 × 3 / 12 = 90 ~ 90;30;120;270
איזה הפרש דרך בס״מ מתאים לפאזה לא עטופה של 180 מעלות? ~ What path difference in cm gives an unwrapped phase of 180 degrees? ~ 12 × 180 / 360 = 6 ~ 6;3;12;24
מהו הפרש הפאזה הלא עטוף במעלות אם הפרש הדרך הוא מינוס 2 ס״מ? ~ What is the unwrapped phase in degrees for a path difference of −2 cm? ~ 360 × (−2) / 12 = −60 ~ −60;60;−30;300
הפרש הדרך גדל מ־1 ל־5 ס״מ. בכמה מעלות עלתה הפאזה הלא עטופה? ~ Path difference grows from 1 to 5 cm. By how many degrees does unwrapped phase rise? ~ 360 × (5 − 1) / 12 = 120 ~ 120;150;30;90
מהי הפאזה עבור 15 ס״מ לאחר עטיפה לטווח שבין 0 ל־360 מעלות, ללא הקצה העליון? ~ For 15 cm, what is the phase wrapped into the interval from 0 through just below 360 degrees? ~ 450 mod 360 = 90 ~ 90;450;270;45

352 366 electronics 4
כיוון הגעה ביחס לניצב ~ Arrival angle relative to broadside
שתי אנטנות מרוחקות 6 ס״מ. הזווית θ נמדדת מהניצב לקו המחבר ביניהן. בגל מישורי הפרש הדרך הוא 6sin(θ) ס״מ. ~ Two antennas are spaced 6 cm apart. Angle θ is measured from broadside. For a plane wave the path difference is 6sin(θ) cm.
היטל המרחק בין האנטנות על כיוון ההתקדמות קובע את הפרש הדרך. ~ The projection of the antenna spacing onto the propagation direction sets the path difference.
מה הפרש הדרך בס״מ עבור 30 מעלות? ~ What path difference in cm does an angle of 30 degrees produce? ~ 6 × sin(30°) = 3 ~ 3;6;0;12
איזו זווית במעלות בין מינוס 90 ל־90 מתאימה להפרש דרך של מינוס 3 ס״מ? ~ Which angle between −90 and 90 degrees gives −3 cm of path difference? ~ arcsin(−3/6) = −30° ~ −30;30;−60;60
מהו הערך המוחלט המרבי של הפרש הדרך בס״מ? ~ What is the largest absolute path difference in cm? ~ 6 × 1 = 6 ~ 6;3;12;36
איזה הפרש דרך בס״מ מתקבל בהגעה מכיוון הניצב? ~ What path difference in cm occurs at broadside? ~ 6 × sin(0°) = 0 ~ 0;3;6;12
מגדילים את המרחק בין האנטנות ל־8 ס״מ. מה הפרש הדרך החדש בס״מ בזווית 30 מעלות? ~ Increase the spacing to 8 cm. What is the new path difference in cm at 30 degrees? ~ 8 × sin(30°) = 4 ~ 4;3;8;16

353 366 electronics 4
כיול בין ערוצי קליטה ~ Calibrating receive-channel phase
מד הפאזה מוסיף היסט קבוע של 25 מעלות לפאזה הגאומטרית. התצוגה עוטפת תוצאות לטווח 0 עד 359 מעלות. ~ A phase meter adds a constant 25-degree offset to geometric phase. Its display wraps results to the range 0 through 359 degrees.
מחסרים את היסט הכיול מהמדידה ומפרשים את התוצאה מודולו סיבוב שלם. ~ Subtract the calibration offset from the reading and interpret the result modulo one turn.
מהי הפאזה הגאומטרית במעלות כאשר הצג מראה 85? ~ What is the geometric phase in degrees when the display reads 85? ~ 85 − 25 = 60 ~ 60;85;110;25
מה יראה הצג במעלות אם הפאזה הגאומטרית היא 350 מעלות? ~ What will the meter display in degrees for a geometric phase of 350 degrees? ~ (350 + 25) mod 360 = 15 ~ 15;375;325;35
מהי הפאזה המתוקנת בטווח התצוגה אם נמדדו 10 מעלות? ~ What corrected phase in the display range corresponds to a reading of 10 degrees? ~ (10 − 25) mod 360 = 345 ~ 345;15;35;335
בכיול עם אפס הפרש דרך, איזה ערך במעלות אמור להופיע? ~ What value in degrees should appear during calibration at zero path difference? ~ 0 + 25 = 25 ~ 25;0;335;50
שתי קריאות הן 75 ואז 95 מעלות. בכמה מעלות עלתה הפאזה הגאומטרית בהנחת שינוי קטן? ~ Two readings are 75 then 95 degrees. Assuming a small change, by how many degrees did geometric phase rise? ~ (95 − 25) − (75 − 25) = 20 ~ 20;45;70;5

354 367 electronics 3
יחס רוחבים במראת זרם ~ Width ratio in a current mirror
במראת NMOS אידאלית שני הטרנזיסטורים ברוויה, עם אותו אורך ערוץ. רוחב טרנזיסטור הייחוס 2 מיקרומטר ורוחב טרנזיסטור המוצא 6 מיקרומטר. ~ Both devices in an ideal NMOS mirror operate in saturation with equal channel lengths. Reference width is 2 micrometers and output width is 6 micrometers.
במתח שער משותף הזרמים ביחס ישר לרוחבי הערוצים, בהנחות המודל. ~ At a shared gate voltage, currents scale with channel width under the stated model.
מהו זרם המוצא במיקרואמפר עבור זרם ייחוס של 40 מיקרואמפר? ~ What is output current in microamps for a 40-microamp reference? ~ 40 × 6 / 2 = 120 ~ 120;40;80;240
מהו זרם הייחוס במיקרואמפר הנדרש למוצא של 75 מיקרואמפר? ~ What reference current in microamps gives 75 microamps at the output? ~ 75 × 2 / 6 = 25 ~ 25;75;225;50
זרם הייחוס גדל ב־7 מיקרואמפר. מהי התוספת לזרם המוצא במיקרואמפר? ~ Reference current rises by 7 microamps. What is the output increase in microamps? ~ 7 × 3 = 21 ~ 21;7;28;14
מחליפים את רוחב המוצא ב־4 מיקרומטר. מה יחס זרם המוצא לזרם הייחוס? ~ Change the output width to 4 micrometers. What is the output-to-reference current ratio? ~ 4 / 2 = 2 ~ 2;3;4;0.5
מה רוחב המוצא הנדרש במיקרומטר ליחס זרמים של 5? ~ What output width in micrometers gives a current ratio of 5? ~ 5 × 2 = 10 ~ 10;5;2.5;30

355 367 electronics 4
מרווח המתח במוצא מראת זרם ~ Current-mirror output headroom
מקור טרנזיסטור המוצא מחובר לאדמה. לפי מודל ארוך־ערוץ, הרוויה דורשת שמתח המוצא יהיה לפחות מתח היתר VGS−VT. נתונים VGS=720 mV ו־VT=480 mV. ~ The output source terminal is grounded. Long-channel saturation requires output voltage at least equal to overdrive VGS−VT. Here VGS=720 mV and VT=480 mV.
סף הרוויה תלוי במתח היתר. יתרת מתח המוצא מעל סף זה היא מרווח הפעולה. ~ Saturation begins at the overdrive voltage. The excess output voltage above this boundary is the headroom.
מהו מתח המוצא המזערי במיליוולט לרוויה? ~ What is the minimum output voltage in millivolts for saturation? ~ 720 − 480 = 240 ~ 240;480;720;1200
מהו מרווח הפעולה במיליוולט כאשר מתח המוצא 310 מיליוולט? ~ What is the headroom in millivolts at 310 millivolts output? ~ 310 − 240 = 70 ~ 70;240;170;550
בכמה מיליוולט צריך להעלות מוצא של 180 מיליוולט כדי להגיע לגבול הרוויה? ~ How many millivolts must be added to a 180-millivolt output to reach saturation? ~ 240 − 180 = 60 ~ 60;180;240;420
מהו סף הרוויה במיליוולט אם מתח השער עולה ל־800 מיליוולט? ~ What is the saturation boundary in millivolts if gate voltage rises to 800 millivolts? ~ 800 − 480 = 320 ~ 320;240;80;480
מהו מתח השער המרבי במיליוולט המאפשר רוויה במתח מוצא 200 מיליוולט? ~ What is the largest gate voltage in millivolts allowing saturation at 200 millivolts output? ~ 200 + 480 = 680 ~ 680;520;280;720

356 367 electronics 3
ענפי מוצא על שער משותף ~ Output branches sharing a gate
מראת זרם אידאלית מוזנת ב־20 מיקרואמפר. שני ענפי מוצא ברוויה הם ברוחב פי 2 ופי 3 מענף הייחוס ובאותו אורך. ~ An ideal mirror has a 20-microamp reference. Two saturated output branches are 2 and 3 times as wide as the reference and have the same length.
כל ענף משכפל זרם לפי יחס הממדים שלו. זרם האספקה כולל גם את ענף הייחוס. ~ Each branch copies current in proportion to its geometry. Supply current also includes the reference branch.
כמה מיקרואמפר צורכים שני ענפי המוצא יחד? ~ How many microamps do the two outputs draw together? ~ 20 × (2 + 3) = 100 ~ 100;120;60;40
כמה מיקרואמפר מושכת המראה כולה מאספקה משותפת? ~ How many microamps does the entire mirror draw from a shared supply? ~ 20 × (1 + 2 + 3) = 120 ~ 120;100;80;60
מהו ההפרש במיקרואמפר בין שני זרמי המוצא? ~ What is the difference between the output currents in microamps? ~ 20 × (3 − 2) = 20 ~ 20;40;60;100
מוסיפים ענף מוצא ברוחב ענף הייחוס. מהו סך זרמי המוצא כעת במיקרואמפר? ~ Add an output as wide as the reference. What is total output current now in microamps? ~ 20 × (2 + 3 + 1) = 120 ~ 120;100;140;20
ללא הענף הנוסף, איזה זרם ייחוס במיקרואמפר ייתן זרם כולל של 150 מיקרואמפר בשני המוצאים? ~ Without the extra branch, what reference in microamps produces a combined output of 150 microamps? ~ 150 / (2 + 3) = 30 ~ 30;25;50;75

357 368 sequential 3
ספירת בית בזמן לחיצת יד ~ Counting a byte on handshake
בכל חזית מציינים שלשה בסדר valid, ready, data. הרצף הוא (1,0,7E), (1,1,7E), (1,1,00), (0,1,7E), (1,1,7E). הבתים כתובים בהקסדצימלי. ~ Each edge lists valid, ready, data. The trace is (1,0,7E), (1,1,7E), (1,1,00), (0,1,7E), (1,1,7E). Bytes are hexadecimal.
בית נספר רק בחזית שבה שני אותות לחיצת היד פעילים והבית תואם. ~ A byte counts only on an edge with both handshake signals asserted and matching data.
כמה מופעים של 7E התקבלו? ~ How many occurrences of 7E were accepted? ~ 1 + 1 = 2 ~ 2;4;3;1
כמה בתים התקבלו בסך הכול? ~ How many bytes were accepted in total? ~ 1 + 1 + 1 = 3 ~ 3;2;4;5
באיזו חזית, במספור מ־1, התקבל לראשונה בית שאינו 7E? ~ On which edge, numbered from 1, was the first non-7E byte accepted? ~ (1,1,00) → 3 ~ 3;1;2;4
כמה חזיתות הציגו 7E בלי שהתרחשה העברה? ~ On how many edges was 7E visible without a transfer? ~ (1,0) + (0,1) → 2 ~ 2;1;3;4
אם ready מופעל גם בחזית הראשונה וכל יתר הדגימות קבועות, כמה מופעי 7E מתקבלים? ~ If ready is asserted on the first edge too and all other samples stay fixed, how many 7E bytes are accepted? ~ 2 + 1 = 3 ~ 3;2;4;5

358 368 bits 3
מונה מופעים ברוחב מוגבל ~ Finite-width match counter
מונה ברוחב 3 ביטים מתחיל ב־6 ומתקדם מודולו 8 פעם לכל בית תואם שהתקבל. סדר האירועים הוא התאמה, התאמה, החטאה, התאמה. ~ A 3-bit counter starts at 6 and advances modulo 8 for each accepted matching byte. The events are match, match, miss, match.
התאמה מקדמת את המונה באחת. הגלישה משמיטה את ביט הנשיאה. ~ A match advances the counter by one. Wrapping drops the carry bit.
מהו ערך המונה הסופי? ~ What is the final counter value? ~ (6 + 3) mod 8 = 1 ~ 1;9;0;7
באיזה אירוע, במספור מ־1, מופיעה הגלישה הראשונה? ~ At which event, numbered from 1, does the first wrap occur? ~ 6 → 7 → 0 ~ 2;1;3;4
כמה התאמות נוספות דרושות מהערך הסופי עד לגלישה הבאה? ~ From the final value, how many further matches are needed for the next wrap? ~ 8 − 1 = 7 ~ 7;6;8;1
מה היה הערך הסופי אילו המונה היה נעצר ברוויה ב־7? ~ What would the final value be if the counter saturated at 7 instead? ~ min(7, 6 + 3) = 7 ~ 7;1;9;6
כמה ביטים דרושים כדי לייצג בדיוק את הספירה ההתחלתית בתוספת כל ההתאמות ברצף? ~ How many bits are needed to represent the starting count plus all matches in this trace exactly? ~ 8 ≤ 9 < 16 → 4 ~ 4;3;8;9

359 369 gates 3
זיהוי המחשב החריג ~ Identifying the dissenting computer
בסדר A,B,C התקבלו שלשות הפלט 110, 010, 000, 101. כל שלשה נדגמה באותה חזית. ~ In A,B,C order the output triples are 110, 010, 000, 101. Each triple is sampled on one edge.
רכיב חריג שונה משני חבריו באותה דגימה. הסכמה לבדה אינה מוכיחה תקינות. ~ A dissenter differs from both peers in one sample. Agreement alone does not establish correctness.
בכמה חזיתות יש אי־הסכמה? ~ How many edges show disagreement? ~ 110, 010, 101 → 3 ~ 3;4;2;1
כמה פעמים B הוא הרכיב החריג? ~ How often is B the dissenter? ~ 010, 101 → 2 ~ 2;1;3;0
כמה פעמים ייתן רוב השלשה את הערך 1? ~ How often does a majority vote give 1? ~ 110, 101 → 2 ~ 2;3;1;4
כמה שלשות ברצף מתאימות לאפשרות שכל שלושת המחשבים החזירו אותו ביט שגוי? ~ How many triples in this trace could represent all three computers returning the same wrong bit? ~ 000 → 1 ~ 1;0;2;3
כמה פעמים A הוא הרכיב החריג היחיד? ~ How often is A the sole dissenter? ~ 110 → C, 010 → B, 101 → B ~ 0;1;2;3

360 369 gates 4
חתימת השוואות בין זוגות ~ Pairwise disagreement signature
מחשבים שלושה ביטי השוואה בסדר A⊕B, B⊕C, C⊕A. כל מחשב מחזיר ביט אחד. ~ Three comparison bits are formed in the order A⊕B, B⊕C, C⊕A. Each computer returns one bit.
כל ביט מופיע פעמיים בהשוואות הזוגיות, ולכן מספר אי־ההתאמות תמיד זוגי. ~ Each bit participates in two comparisons, so the number of mismatches is always even.
מהי החתימה עבור A,B,C=1,1,0? ~ What is the signature for A,B,C=1,1,0? ~ (1⊕1,1⊕0,0⊕1) = 011 ~ 011;101;110;111
כמה חתימות שונות אפשר לקבל מכל שלשות הקלט? ~ How many distinct signatures can all input triples produce? ~ 000, 011, 101, 110 → 4 ~ 4;8;3;6
כמה שלשות קלט נותנות את החתימה 000? ~ How many input triples give signature 000? ~ 000, 111 → 2 ~ 2;1;3;0
אם החתימה מתחילה ב־10, מהו ביט החתימה השלישי? ~ If the signature begins with 10, what is its third bit? ~ 1⊕0 = 1 ~ 1;0;X;Z
מהי החתימה אם הופכים את כל ביטי הקלט 110? ~ What is the signature after complementing every bit of input 110? ~ 001 → 011 ~ 011;100;110;000

361 370 bits 3
כיסוי תאי זיכרון במכסת אחדות ~ Covering memory cells under a ones budget
בכל כתיבה למילה בת 64 ביטים מותר לבקש לכל היותר 7 אחדות. מחפשים תאים התקועים ב־0 באמצעות כתיבה וקריאה של אותה מילה. ~ Each write to a 64-bit word may request at most 7 ones. Test for cells stuck at 0 by writing and reading that word.
לבדיקת תא התקוע באפס צריך לבקש בו אחד. אפשר לכסות בכל כתיבה לכל היותר את המכסה. ~ Testing a stuck-at-zero cell requires requesting one there. A write can cover no more cells than its budget.
מהו מספר הכתיבות המזערי כדי לכסות את כל התאים? ~ What is the minimum number of writes to cover every cell? ~ ceil(64/7) = 10 ~ 10;9;7;64
כמה תאים יישארו אחרי 8 כתיבות ללא חפיפה, שכל אחת מהן מכסה 7 תאים? ~ How many cells remain after 8 disjoint writes that each cover 7 cells? ~ 64 − 8 × 7 = 8 ~ 8;7;9;56
כמה תאים נותרו לכתיבה האחרונה אם 9 הכתיבות הראשונות ניצלו את מלוא המכסה ללא חפיפה? ~ How many cells remain for the final write after 9 full nonoverlapping writes? ~ 64 − 9 × 7 = 1 ~ 1;7;0;6
אם המכסה יורדת ל־4 אחדות, כמה כתיבות נדרשות לכל הפחות? ~ If the budget drops to 4 ones, how many writes are necessary at minimum? ~ 64 / 4 = 16 ~ 16;4;10;15
מהי מכסת האחדות המזערית המאפשרת כיסוי ב־8 כתיבות? ~ What is the smallest ones budget permitting coverage in 8 writes? ~ ceil(64/8) = 8 ~ 8;7;9;16

362 370 bits 4
אבחנה בין תא תקין לשתי תקלות קבועות ~ Distinguishing a good cell from stuck faults
בכל בדיקה כותבים מילה בת 8 ביטים וקוראים בחזרה. מגבלת הכתיבה היא 2 אחדות. מניחים שתא תקול תמיד נקרא כ־0 או תמיד כ־1. ~ Each test writes and reads an 8-bit word. At most 2 ones may be requested. A faulty cell always reads as 0 or always as 1.
כדי להבחין בין תקינות לשתי התקלות צריך לבדוק כל תא בשני ערכי הקלט. ~ Testing both requested values at every cell distinguishes correct behavior from either stuck value.
כמה כתיבות נדרשות לכל הפחות כדי לבדוק את שתי התקלות בכל התאים? ~ What is the minimum number of writes that test both faults at every cell? ~ ceil(8/2) = 4 ~ 4;5;8;2
בארבע כתיבות של זוגות ביטים ללא חפיפה, כמה פעמים נדרש אפס בכל תא? ~ Across four writes with disjoint pairs of ones, how often is zero requested in each cell? ~ 4 − 1 = 3 ~ 3;4;1;2
עם ארבע הכתיבות הללו, כמה זוגות של מיקום וסוג תקלה מכוסים? ~ With those four writes, how many combinations of cell location and stuck-fault type are covered? ~ 8 × 2 = 16 ~ 16;8;4;32
לאחר כתיבה יחידה של אפסים, בכמה מיקומים אפשר לגלות תקיעה ב־1? ~ After a single all-zero write, at how many locations can a cell stuck at 1 be detected? ~ 8 × 1 = 8 ~ 8;0;2;16
מבצעים רק כתיבות של אפסים. כמה מתקלות התקיעה ב־0 הבודדות ניתנות לגילוי? ~ If all writes request only zeros, how many single cells stuck at 0 can be detected? ~ 0 × 8 = 0 ~ 0;1;2;8

363 364 sequential 3
מה המוניטור רואה בכתיבה ל־FIFO ~ What a FIFO write monitor observes
רצף דגימות של write, full, data הוא (1,0,9), (1,1,4), (0,0,8), (1,0,6). כתיבה מתקבלת רק אם write=1 ו־full=0. ~ Samples of write, full, data are (1,0,9), (1,1,4), (0,0,8), (1,0,6). A write is accepted only with write=1 and full=0.
מודל הייחוס מוסיף לתור פריט לכל כתיבה שהתקבלה בפועל בממשק. ~ The reference model enqueues one item for each write actually accepted at the interface.
כמה מילים יוסיף המוניטור לתור הצפוי? ~ How many words should the monitor add to the expected queue? ~ [9,6] → 2 ~ 2;3;4;1
איזה ערך התקבל אחרון? ~ Which data value was accepted last? ~ [9,6] → 6 ~ 6;8;4;9
איזה ערך הוצע אך נדחה בגלל full? ~ Which offered value was rejected because of full? ~ (1,1,4) → 4 ~ 4;9;6;8
אם נספור כל write בלי לבדוק full, בכמה תהיה הספירה גדולה מדי? ~ If every write is counted regardless of full, by how much is the count too large? ~ 3 − 2 = 1 ~ 1;0;2;3
איזה ערך אמורה להחזיר הקריאה הראשונה אחר כך, אם התור התחיל ריק? ~ What should a subsequent first read return if the FIFO started empty? ~ [9,6] → 9 ~ 9;6;8;4

364 364 states 3
תור צפוי בזמן איפוס ~ Expected queue across reset
תור צפוי מתחיל ריק. W(x) מוסיפה מילה שהתקבלה, R מוציאה את הראש ו־Z מרוקנת את התור. העקבות הן W(4), W(7), R, Z, W(2), W(8), R. ~ An expected queue starts empty. W(x) appends an accepted word, R removes the head, and Z clears the queue. Events are W(4), W(7), R, Z, W(2), W(8), R.
איפוס מסיים את התוקף של כל המילים הממתינות להשוואה. ~ Reset invalidates every outstanding word in the comparison queue.
איזה ערך צפוי בקריאה השנייה? ~ What value is expected on the second read? ~ [2,8] → 2 ~ 2;4;7;8
איזו מילה נמחקה באיפוס? ~ Which word was discarded by reset? ~ [4,7] → [7] → [] ~ 7;4;2;8
מה עומק התור מיד אחרי האיפוס? ~ What is the queue depth immediately after reset? ~ [7] → [] → 0 ~ 0;1;2;3
איזו מילה נשארה בתור בסוף? ~ Which word remains at the end? ~ [2,8] → [8] ~ 8;7;4;2
מה העומק המרבי של התור במהלך הרצף? ~ What is the maximum queue depth during the trace? ~ max(1,2,1,0,1,2,1) = 2 ~ 2;3;4;1

365 363 states 3
היסטרזיס בין שני ספי טמפרטורה ~ Hysteresis between temperature thresholds
מאוורר מתחיל כבוי. דגימה של 80 מעלות ומעלה מפעילה אותו, ודגימה של 65 מעלות ומטה מכבה אותו. בין הספים מצבו נשמר. הדגימות הן 72,80,77,65,70. ~ A fan starts off. A sample at or above 80 degrees turns it on. A sample at or below 65 turns it off. Between thresholds it holds. Samples are 72,80,77,65,70.
בתחום שבין הספים הפלט תלוי בהיסטוריה. גם הדגימות השוות לספים מקבלות פעולה מוגדרת. ~ Between thresholds the output depends on history. Equality at each threshold has a defined action.
אחרי כמה מהדגימות המאוורר פועל? ~ After how many samples is the fan on? ~ 0,1,1,0,0 → 2 ~ 2;1;3;4
מה רוחב התחום בין הספים במעלות? ~ What is the threshold separation in degrees? ~ 80 − 65 = 15 ~ 15;14;16;145
באיזו דגימה, במספור מ־1, המאוורר נכבה לראשונה לאחר שהופעל? ~ At which sample, numbered from 1, does it first switch off after turning on? ~ 80 → 77 → 65 → 4 ~ 4;3;5;2
כמה פעמים השתנה מצב המאוורר במהלך הרצף? ~ How many times does the fan change state in the trace? ~ 0 → 1 → 0 ~ 2;1;3;4
אם המאוורר מתחיל פועל במקום כבוי, אחרי כמה דגימות יהיה פועל באותו הרצף? ~ If the fan starts on instead, after how many samples is it on in this trace? ~ 1,1,1,0,0 → 3 ~ 3;2;4;5

366 363 sequential 3
התנגשות פולסי סף ~ Simultaneous threshold pulses
בקר מתחיל כבוי. פולס H מפעיל אותו, פולס L מכבה אותו, ובהיעדר פולס המצב נשמר. בהתנגשות L גובר. סדר הדגימות הוא H, שקט, H+L, שקט, H. ~ A controller starts off. H turns it on, L turns it off, and silence holds state. L wins on collision. Samples are H, silence, H+L, silence, H.
קביעת עדיפות מפורשת מעניקה ערך חד־משמעי גם לדגימה שבה שני אירועי הסף מופיעים יחד. ~ An explicit priority assigns an unambiguous state when the two threshold events coincide.
כמה דגימות מסתיימות במצב פעיל? ~ How many samples end in the on state? ~ 1,1,0,0,1 → 3 ~ 3;4;2;5
מה המצב מיד אחרי ההתנגשות, כאשר 1 מציין פעיל? ~ What is the state immediately after the collision, with 1 denoting on? ~ L → 0 ~ 0;1;X;Z
כמה פעמים יש מעבר מכבוי לפעיל? ~ How many off-to-on transitions occur? ~ 0 → 1, 0 → 1 ~ 2;1;3;0
אם H יקבל עדיפות בהתנגשות, כמה דגימות יסתיימו במצב פעיל? ~ If H wins on collision instead, how many samples end in the on state? ~ 1,1,1,1,1 → 5 ~ 5;4;3;2
בכמה דגימות שונה הפלט בין שתי מדיניות העדיפות? ~ On how many samples do the outputs of the two priority policies differ? ~ 3,4 → 2 ~ 2;1;3;0

367 357 electronics 4
פשרת העומס בהגדלת מהפך ~ Loading tradeoff when sizing an inverter
במודל פשוט, השהיית שלוש דרגות בפיקו־שניות היא D(s)=2s+18/s+4, כאשר s הוא גודל המהפך האמצעי. הגדלים המותרים הם 1,2,3,6. ~ In a simple model, three-stage delay in picoseconds is D(s)=2s+18/s+4, where s is middle-inverter size. Allowed sizes are 1,2,3,6.
הגדלת המהפך מקלה על הנעת המוצא ומכבידה על הדרגה הקודמת. ~ A larger inverter drives its output more strongly and adds load to the preceding stage.
איזה גודל מותר ממזער את ההשהיה? ~ Which allowed size minimizes delay? ~ D(1,2,3,6) → 24,17,16,19 ~ 3;1;2;6
מה ההשהיה בפיקו־שניות בגודל 2? ~ What is the delay in picoseconds at size 2? ~ 2 × 2 + 18/2 + 4 = 17 ~ 17;16;13;24
בכמה פיקו־שניות פוחתת ההשהיה במעבר מגודל 1 ל־3? ~ By how many picoseconds does delay fall from size 1 to 3? ~ 24 − 16 = 8 ~ 8;6;3;16
באיזה גודל מותר ההשהיות התלויות בגודל שוות זו לזו? ~ At which allowed size do the two size-dependent delay terms match? ~ 2 × 3 = 18/3 ~ 3;1;2;6
בכמה פיקו־שניות מתארכת ההשהיה במעבר מגודל 3 ל־6? ~ How many picoseconds of delay are added by increasing size from 3 to 6? ~ 19 − 16 = 3 ~ 3;6;9;0

368 365 electronics 3
אינטרפולציה בטבלת עומס ~ Interpolating a load table
בקצב מעבר קבוע בכניסה, ספריית התא נותנת השהיה של 18 פיקו־שניות בעומס 2 fF ושל 42 פיקו־שניות בעומס 8 fF. מניחים אינטרפולציה ליניארית בין הנקודות. ~ At fixed input slew, a cell table gives 18 picoseconds at 2 fF and 42 picoseconds at 8 fF. Interpolate linearly between the points.
באינטרפולציה ליניארית תוספת ההשהיה יחסית לשינוי העומס בתוך הקטע הנתון. ~ Under linear interpolation, delay changes in proportion to load within the given interval.
מה ההשהיה בפיקו־שניות בעומס 5 fF? ~ What is delay in picoseconds at a load of 5 fF? ~ 18 + (5 − 2) × 4 = 30 ~ 30;24;36;21
מה שיפוע ההשהיה בפיקו־שניות ל־fF? ~ What is the delay slope in picoseconds per fF? ~ (42 − 18) / (8 − 2) = 4 ~ 4;3;6;8
איזה עומס ב־fF נותן השהיה של 34 פיקו־שניות? ~ Which load in fF gives a delay of 34 picoseconds? ~ 2 + (34 − 18)/4 = 6 ~ 6;4;8;5
כמה פיקו־שניות מוסיפה הגדלת עומס מ־4 ל־7 fF? ~ How many picoseconds are added when load grows from 4 to 7 fF? ~ (7 − 4) × 4 = 12 ~ 12;3;16;28
מהו העומס המרבי ב־fF העומד בתקציב של 26 פיקו־שניות? ~ What is the maximum load in fF meeting a 26-picosecond budget? ~ 2 + (26 − 18)/4 = 4 ~ 4;2;6;8

369 351 sequential 4
שינוי במרווח תזמון בין ריצות ~ Slack changes between timing runs
אותם מסלולים A,B,C נמדדו בשתי ריצות. מרווחי התזמון בפיקו־שניות היו (20,−5,8) וכעת הם (11,3,−2). מרווח שלילי הוא הפרה. ~ The same paths A,B,C are measured in two runs. Slacks in picoseconds were (20,−5,8) and are now (11,3,−2). A negative slack is a violation.
משווים מרווחים לאותו מסלול ובאותם אילוצים כדי לזהות שינוי שחומק מסיכום כללי. ~ Match the same path and constraints to detect changes that a single summary can hide.
מהו השינוי במרווח של B בפיקו־שניות, חדש פחות ישן? ~ What is B's slack change in picoseconds, new minus old? ~ 3 − (−5) = 8 ~ 8;−8;2;−2
מהו המרווח הגרוע ביותר בריצה החדשה בפיקו־שניות? ~ What is the worst slack in the new run in picoseconds? ~ min(11,3,−2) = −2 ~ −2;−5;3;11
כמה מסלולים עברו מעמידה באילוץ להפרה? ~ How many paths changed from meeting the constraint to violating it? ~ C: 8 → −2 ~ 1;0;2;3
בכמה פיקו־שניות הורע המסלול שמרווחו ירד הכי הרבה? ~ How many picoseconds did the most degraded path lose? ~ max(20 − 11, 8 − (−2)) = 10 ~ 10;9;8;3
בכמה פיקו־שניות השתפר המרווח הגרוע ביותר בין שתי הריצות? ~ By how many picoseconds did the worst slack improve between runs? ~ −2 − (−5) = 3 ~ 3;8;7;−3

370 352 sequential 3
מסלול חסר בדוח מקוצר ~ A missing path in a truncated report
כל הדוחות מציגים רק את שני מרווחי התזמון הקטנים ביותר. בריצה אחת הערכים של A,B,C,D הם 1,4,7,9 פיקו־שניות. בריצה הבאה הם 1,6,3,9. ~ Each report shows only the two smallest slacks. In one run A,B,C,D have 1,4,7,9 picoseconds. In the next run they have 1,6,3,9.
הגבלת מספר השורות בדוח יכולה להסתיר מסלול קיים כאשר דירוגו משתנה. ~ A row limit can hide an existing path when its rank changes.
מה דירוג B בריצה השנייה, כאשר הגרוע ביותר מדורג 1? ~ What is B's rank in the second run if worst is ranked 1? ~ A,C,B,D → 3 ~ 3;2;1;4
כמה מסלולים משותפים לשני הדוחות המקוצרים? ~ How many paths appear in both truncated reports? ~ {A,B} ∩ {A,C} = {A} ~ 1;0;2;3
מה מספר השורות המזערי שיציג גם את B בריצה השנייה? ~ What minimum row limit includes B in the second run? ~ A,C,B → 3 ~ 3;1;2;4
איזה מרווח בפיקו־שניות קובע את סף ההופעה בריצה השנייה עם שתי שורות? ~ Which slack in picoseconds sets the inclusion cutoff in the second two-row report? ~ (1,3) → 3 ~ 3;1;6;9
בכמה פיקו־שניות השתפר בפועל מרווחו של המסלול שנעלם מהדוח? ~ By how many picoseconds did the path that disappeared from the report actually improve? ~ B: 6 − 4 = 2 ~ 2;3;6;−2

371 356 states 3
תפוסה בחניון מלא עם יציאה באותו מחזור ~ Admission when a full lot has a departure
חניון בן 50 מקומות מתחיל בתפוסה 49. בכל מחזור מוציאים רכב אם אפשר, ואז מכניסים רכב אם התפנה מקום. הבקשות בסדר כניסה,יציאה הן 10,10,11,01,01. ~ A 50-space lot starts at 49. Each cycle first honors a possible departure, then admits an arrival if space is available. Requests in arrival,departure order are 10,10,11,01,01.
מדיניות סדר האירועים קובעת אם יציאה מאפשרת כניסה באותו מחזור גם כשהחניון התחיל מלא. ~ Event ordering determines whether a departure allows admission in the same cycle when the lot starts full.
מהי התפוסה הסופית? ~ What is the final occupancy? ~ 49 → 50 → 50 → 50 → 49 → 48 ~ 48;49;50;47
כמה בקשות כניסה נדחו? ~ How many arrival requests were rejected? ~ 3 − 2 = 1 ~ 1;0;2;3
בכמה מחזורים התקבלו גם כניסה וגם יציאה? ~ In how many cycles were both an arrival and a departure accepted? ~ 11 → 1 ~ 1;0;2;3
כמה מחזורים הסתיימו בחניון מלא? ~ How many cycles ended with the lot full? ~ 50,50,50,49,48 → 3 ~ 3;1;2;4
כמה מקומות פנויים נותרו בסוף? ~ How many spaces are free at the end? ~ 50 − 48 = 2 ~ 2;0;1;3

372 350 sequential 3
מספר הזזות שנשמר בזמן טעינה ~ Shift count latched on load
במחזור הטעינה נטענים למילה בת 8 ביטים הערך 180 והמונה 3. בכל חזית עוקבת עם enable פעיל ומונה חיובי מזיזים ימינה לוגית ומקטינים את המונה. דגימות enable הן 1,0,1,1,1. ~ A load sets an 8-bit register to 180 and its count to 3. At each subsequent enabled edge with positive count, shift logically right and decrement. Enable samples are 1,0,1,1,1.
מונה ההזזות מתעד עבודה שנותרה. חזית מושבתת שומרת את המונה ואת המילה. ~ The shift counter tracks remaining work. A disabled edge preserves both count and word.
מה הערך העשרוני הסופי במילה? ~ What is the final decimal register value? ~ 180 → 90 → 45 → 22 ~ 22;11;45;90
מהו המונה אחרי שתי החזיתות הראשונות? ~ What is the count after the first two edges? ~ 3 − 1 = 2 ~ 2;1;3;0
באיזו חזית לאחר הטעינה, במספור מ־1, המונה מגיע לראשונה לאפס? ~ At which edge after loading, numbered from 1, does the count first reach zero? ~ 1,3,4 → 4 ~ 4;3;5;2
באיזה ערך עשרוני מחזיקה המילה מיד לפני ההזזה האחרונה? ~ Which decimal value does the register hold immediately before the last shift? ~ 180 >> 2 = 45 ~ 45;22;90;11
אם נטען מונה 4 במקום 3, מה הערך הסופי אחרי אותן חזיתות? ~ If the loaded count is 4 instead of 3, what is the final value after the same edges? ~ 180 >> 4 = 11 ~ 11;22;45;5

373 349 gates 3
בחירת קבוצה במקודד עדיפויות ~ Selecting a group in a priority encoder
מקודד בן 16 כניסות מעניק עדיפות לאינדקס הגבוה ביותר. ארבע קבוצות רצופות מכילות ארבע כניסות כל אחת. הבקשות הפעילות הן באינדקסים 2,6,9,11. ~ A 16-input encoder prioritizes the highest index. Four consecutive groups contain four inputs each. Requests are active at indices 2,6,9,11.
האינדקס הגלובלי הוא ארבע פעמים מספר הקבוצה בתוספת המיקום המקומי, במספור מאפס. ~ The global index is four times the zero-based group number plus the local index.
מהו האינדקס המקומי בקבוצה הזוכה? ~ What is the local index within the winning group? ~ 11 mod 4 = 3 ~ 3;2;1;0
מהו מספר הקבוצה הזוכה? ~ What is the winning group number? ~ 11 div 4 = 2 ~ 2;3;1;0
איזה אינדקס גלובלי ייבחר אם בקשה 11 תתבטל? ~ Which global index wins if request 11 is cleared? ~ max(2,6,9) = 9 ~ 9;6;2;11
כמה מקודדים מקומיים מסמנים שיש בקשה בקבוצתם? ~ How many local encoders assert that their group has a request? ~ {0,1,2} → 3 ~ 3;4;2;1
איזה אינדקס גלובלי מתקבל עבור בחירת קבוצה 3 ומיקום מקומי 1? ~ What global index is represented by group 3 and local index 1? ~ 4 × 3 + 1 = 13 ~ 13;12;7;4

374 340 gates 3
מציאת המרב בנתונים בני שני ביטים ~ Maximum of two-bit values
יש 16 מילים לא מסומנות בנות 2 ביטים. ערכי 00,01,10,11 מופיעים בהתאמה 4,5,7,0 פעמים. המוצא הוא הערך המרבי המופיע. ~ There are 16 unsigned 2-bit words. Values 00,01,10,11 occur 4,5,7,0 times respectively. The output is the largest value present.
רק קיום של ערך גבוה יותר יכול להחליף את המרב. תדירות נמוכה מספיקה אם היא חיובית. ~ Only the presence of a larger value can replace the maximum. A single occurrence suffices.
מהו ערך המוצא בבינארי? ~ What is the binary output? ~ max(00,01,10) = 10 ~ 10;11;01;00
כמה מילים חייבות להשתנות לכל הפחות כדי להוריד את המרב ל־01? ~ At least how many words must change to lower the maximum to 01? ~ count(10) = 7 ~ 7;1;5;12
כמה מילים חייבות להשתנות לכל הפחות כדי להעלות את המרב ל־11? ~ At least how many words must change to raise the maximum to 11? ~ 00 → 11 ~ 1;7;2;0
מה יתקבל בבינארי אם פשוט נבצע OR ביטי על כל המילים? ~ What binary value would a bitwise OR of all words produce? ~ 01 OR 10 = 11 ~ 11;10;01;00
כמה מילים שוות למרב לאחר החלפת כל מופעי 10 ב־01? ~ How many words equal the maximum after changing every 10 to 01? ~ 5 + 7 = 12 ~ 12;7;5;16

375 339 sequential 4
מעקב אחרי משוב XOR ~ Following an XOR feedback register
מצב האוגר כתוב abc בסדר משמאל לימין. בכל חזית המצב הבא הוא (b⊕c,a,b). מתחילים ב־001 ודוגמים לאחר כל חזית. ~ A register state is written abc from left to right. Each edge updates it to (b⊕c,a,b). Start at 001 and sample after each edge.
כל הביטים מתעדכנים במקביל לפי המצב הישן. מצב האפס חוזר לעצמו במשוב XOR. ~ All bits update simultaneously from the old state. The all-zero state feeds back to itself under XOR.
מהו המצב לאחר שתי חזיתות? ~ What is the state after two edges? ~ 001 → 100 → 010 ~ 010;100;001;101
כמה חזיתות דרושות לחזרה הראשונה למצב ההתחלתי? ~ How many edges elapse before the first return to the starting state? ~ 001→100→010→101→110→111→011→001 ~ 7;8;6;3
לכמה מצבים שונים מגיעים אם מאתחלים ל־000? ~ How many different states are visited when initialized to 000? ~ 000 → 000 ~ 1;7;8;0
בכמה מצבים במחזור הלא־אפס הביט c הוא 1? ~ In how many states of the nonzero cycle is bit c equal to 1? ~ 001,101,111,011 → 4 ~ 4;3;7;2
מהו המצב מיד לפני החזרה ל־001? ~ Which state immediately precedes the return to 001? ~ 011 → 001 ~ 011;111;010;100

376 338 states 4
מעבר ישיר מחמש לאחת ~ Jumping directly from five to one
מונה בן 3 ביטים מתחיל ב־1. בכל חזית הוא גדל ב־1, פרט למצב 5 שבו נטען 1. נתעלם מאתחול נוסף. ~ A 3-bit counter starts at 1. Each edge increments it by 1, except at state 5 where it loads 1. There are no further resets.
בחירת ערך הטעינה מתוך המצב הנוכחי מונעת הצגה של מצב נוסף בין מחזורים. ~ Selecting the load from the current state avoids displaying an extra state between cycles.
מה הערך מיד אחרי החזית השמינית? ~ What is the value immediately after edge eight? ~ 1 + (8 mod 5) = 4 ~ 4;3;5;1
באיזו חזית, במספור מ־1, מופיע 5 לראשונה אחרי ההתחלה? ~ On which edge, numbered from 1, does 5 first appear after initialization? ~ 1 → 2 → 3 → 4 → 5 ~ 4;5;3;1
כמה טעינות של 1 מתרחשות ב־12 חזיתות? ~ How many loads of 1 occur in 12 edges? ~ floor(12/5) = 2 ~ 2;3;12;1
כמה קודים בני 3 ביטים אינם מופיעים במחזור התקין? ~ How many 3-bit codes do not appear in the normal cycle? ~ 8 − 5 = 3 ~ 3;2;5;0
אם בודקים 6 במקום 5 כדי להפעיל טעינה, מה יהיה אורך המחזור בחזיתות? ~ If load is triggered from 6 instead of 5, what is the cycle length in edges? ~ 1,2,3,4,5,6 → 6 ~ 6;5;7;8

377 341 states 4
מפת נוכחות למילים במילון קטן ~ A presence map for a bounded dictionary
מילון החומרה מכיר את המילים A,B,C,D. ביט i במפה מציין שהמילה כבר התקבלה, לפי הסדר A=0 עד D=3. המפה מתחילה ריקה. מתקבלות B,D,B,A. ~ A hardware dictionary recognizes A,B,C,D. Map bit i records whether its word was seen, with A=0 through D=3. The map starts empty. The stream is B,D,B,A.
הופעה ראשונה מדליקה ביט במפת הנוכחות. הופעה חוזרת משאירה אותו דולק. ~ A first occurrence sets its presence bit. A repeated word leaves that bit set.
מה ערכה העשרוני של המפה בסוף? ~ What is the decimal map value at the end? ~ 2 + 8 + 1 = 11 ~ 11;13;4;15
כמה מילים שונות התקבלו? ~ How many distinct words arrived? ~ {A,B,D} → 3 ~ 3;4;2;11
באיזה אירוע, במספור מ־1, מתקבלת לראשונה מילה שכבר נראתה? ~ At which event, numbered from 1, is an already seen word first observed? ~ B,D,B → 3 ~ 3;2;4;1
איזו מסכה עשרונית חסרה כדי שכל ארבעת הביטים יהיו פעילים? ~ What decimal mask is missing to make all four bits active? ~ 15 XOR 11 = 4 ~ 4;3;8;2
כמה מפות נוכחות שונות יכולות להיווצר בקליטת רצפים כלשהם במילון הזה? ~ How many different presence maps can arbitrary streams produce for this dictionary? ~ 2⁴ = 16 ~ 16;4;8;24

378 325 sequential 4
כמה חזיתות נמצאות בתוך פולס ~ Sampling edges inside a pulse
השעון דוגם בזמנים 0,10,20,… ננו־שניות. הפולס גבוה החל מ־13 ננו־שניות ועד לפני 46 ננו־שניות. המונה סופר חזיתות שבהן הכניסה גבוהה. ~ Sampling edges occur at times 0,10,20,… nanoseconds. A pulse is high from 13 nanoseconds up to but excluding 46 nanoseconds. A counter counts edges sampling high.
מונה מדוגם מודד כמה נקודות של רשת השעון נפלו בתוך הפולס. ~ A sampled counter measures how many points of the clock grid fall inside the pulse.
כמה חזיתות נספרו? ~ How many edges were counted? ~ 20,30,40 → 3 ~ 3;4;2;5
מהו רוחב הפולס בפועל בננו־שניות? ~ What is the actual pulse width in nanoseconds? ~ 46 − 13 = 33 ~ 33;30;40;46
מהי שגיאת האומדן בננו־שניות אם מחשבים ספירה כפול זמן מחזור פחות הרוחב האמיתי? ~ What is estimated minus actual width in nanoseconds if the estimate is count times period? ~ 3 × 10 − 33 = −3 ~ −3;3;7;−13
מזיזים את אותו פולס 5 ננו־שניות ימינה. כמה חזיתות ייספרו כעת? ~ Shift the entire pulse 5 nanoseconds later. How many edges are now counted? ~ 20,30,40,50 → 4 ~ 4;3;5;2
באיזה זמן בננו־שניות מתקבלת הדגימה הנמוכה הראשונה לאחר סיום הפולס המקורי? ~ At what time in nanoseconds does the first low sample after the original pulse end occur? ~ 10 × ceil(46/10) = 50 ~ 50;46;40;60

379 328 bits 3
רוחב ביניים בעץ מחברים ~ Intermediate widths in an adder tree
ארבעה קלטים לא מסומנים בני 3 ביטים מחוברים בזוגות. מחברים את שני סכומי הביניים ומכפילים את הסכום בשתיים. רוצים ייצוג מדויק ללא גלישה. ~ Four unsigned 3-bit inputs are added in pairs. The two partial sums are added, then doubled. Exact results without overflow are required.
רוחב כל צומת נקבע לפי הערך המרבי שיכול להגיע אליו, כולל ביטים שנוספו בחיבורים קודמים. ~ Each node's width follows its maximum possible value, including growth at earlier additions.
כמה ביטים דרושים לכל סכום של זוג? ~ How many bits does each pair sum require? ~ 7 + 7 = 14 < 16 → 4 ~ 4;3;5;6
מהו הסכום המרבי של כל ארבעת הקלטים לפני ההכפלה? ~ What is the largest four-input sum before doubling? ~ 4 × 7 = 28 ~ 28;31;56;14
כמה ביטים דרושים לפלט הסופי? ~ How many bits does the final output need? ~ 32 ≤ 56 < 64 → 6 ~ 6;5;4;7
איזה ביט במוצא קבוע תמיד באפס, במספור מ־0 בביט הימני? ~ Which output bit is always zero, numbering the rightmost bit 0? ~ 2 × n → bit 0 ~ 0;1;4;5
אם שומרים רק 5 ביטים בפלט, איזה ערך עשרוני מתקבל עבור ארבעה קלטים שכל אחד מהם 7? ~ If only 5 output bits are retained, what decimal value appears with all four inputs equal to 7? ~ 56 mod 32 = 24 ~ 24;28;31;56

380 328 sequential 4
תגיות בזמן מילוי צינור ~ Tracking tags while a pipeline fills
צינור מקבל מילה בכל חזית עם valid פעיל, ומוציא אותה בדיוק 3 חזיתות אחר כך. אין השהיות. מתקבלות מילים בחזיתות 2,3,6,7. ~ A pipeline accepts a word on each valid edge and outputs it exactly 3 edges later. There are no stalls. Words are accepted at edges 2,3,6,7.
ההשהיה מזיזה את כל חזיתות התקפות באותו מספר מחזורים, כך שהרווחים ביניהן נשמרים. ~ Fixed latency translates every valid edge by the same number of cycles and preserves the gaps.
באיזו חזית יוצאת המילה השלישית? ~ At which edge does the third word emerge? ~ 6 + 3 = 9 ~ 9;6;8;10
כמה מילים כבר יצאו עד סוף חזית 8? ~ How many words have emerged by the end of edge 8? ~ 5,6 → 2 ~ 2;3;4;1
כמה מילים שהתקבלו עדיין ממתינות לפלט מיד אחרי חזית 7? ~ How many accepted words still await output immediately after edge 7? ~ 4 − 2 = 2 ~ 2;4;1;3
כמה חזיתות ריקות מופיעות בין הפלט השני לשלישי? ~ How many empty output edges separate the second and third outputs? ~ 9 − 6 − 1 = 2 ~ 2;3;1;0
מוסיפים דרגה אחת שמוסיפה מחזור להשהיה. באיזו חזית תצא המילה האחרונה? ~ Add one stage that increases latency by a cycle. At which edge will the final word emerge? ~ 7 + 4 = 11 ~ 11;10;8;12

381 322 sequential 3
פירוק בתים ליחידות שידור ~ Breaking bytes into transfer units
מקור מוסר בית בן 8 ביטים כל 5 מחזורי יעד. המקלט מקבל יחידת שידור אחת במחזור. בוחרים רוחב יחידה קבוע ומרפדים באפסים את היחידה האחרונה בכל בית לפי הצורך. ~ A source provides an 8-bit byte every 5 destination cycles. The receiver accepts one fixed-width transfer per cycle. Each byte's last transfer is zero-padded if needed.
מספר ההעברות לבית מעוגל כלפי מעלה. התכנון עומד בקצב כאשר ניתן לסיים בית לפני הבא. ~ Round the transfers per byte upward. The rate is sustainable when each byte can finish before the next arrives.
מהו רוחב היחידה המזערי בביטים לעמידה בקצב? ~ What is the minimum transfer width in bits that sustains the rate? ~ ceil(8/5) = 2 ~ 2;1;3;5
כמה מחזורי יעד פנויים נשארים בין בתים ברוחב יחידה של 2 ביטים? ~ How many unused destination cycles remain per byte at a transfer width of 2 bits? ~ 5 − 8/2 = 1 ~ 1;0;2;4
כמה ביטי ריפוד מתווספים לכל בית ברוחב יחידה של 3 ביטים? ~ How many padding bits does each byte need with 3-bit transfers? ~ 3 × ceil(8/3) − 8 = 1 ~ 1;0;2;3
כמה מחזורים דרושים לשידור בית יחיד ברוחב יחידה של ביט אחד? ~ How many cycles does a single byte require with a one-bit transfer width? ~ 8 / 1 = 8 ~ 8;5;4;1
אם בית מגיע כל 3 מחזורים במקום כל 5, מה רוחב היחידה המזערי בביטים? ~ If a byte arrives every 3 cycles instead of every 5, what is the minimum transfer width in bits? ~ ceil(8/3) = 3 ~ 3;2;4;8

382 324 bits 3
מנה ושארית בחלוקה לשש ~ Quotient and remainder for division by six
מחלק מקבל מספר שלם לא מסומן N בתחום 0 עד 63 ומחזיר מנה q ושארית r בחלוקה ב־6. ~ A divider accepts an unsigned integer N from 0 through 63 and returns quotient q and remainder r on division by 6.
המנה והשארית מקיימות יחד את משוואת החלוקה. השארית תמיד קטנה מהמחלק. ~ Quotient and remainder satisfy the division identity, with remainder strictly below the divisor.
כמה ביטים דרושים לייצוג המנה המרבית? ~ How many bits are needed to represent the largest quotient? ~ floor(63/6) = 10 → 4 ~ 4;3;6;10
מהי השארית עבור הקלט המרבי? ~ What is the remainder at maximum input? ~ 63 − 6 × 10 = 3 ~ 3;5;0;10
מהו הקלט הקטן ביותר שעבורו המנה היא 8? ~ What is the smallest input whose quotient is 8? ~ 8 × 6 = 48 ~ 48;47;54;8
כמה קלטים בתחום נותנים מנה 10? ~ How many allowed inputs give quotient 10? ~ 60,61,62,63 → 4 ~ 4;6;3;10
מהו הקלט שעבורו מתקבלים q=5 ו־r=4? ~ What input produces q=5 and r=4? ~ 6 × 5 + 4 = 34 ~ 34;30;29;54

383 323 sequential 3
קשר בין מספר העליות לירידות ~ Relating rising and falling edge counts
גלאי מתחיל עם דגימה קודמת 0 ומקבל לפי הסדר 1,1,0,1,0,0,1. בכל חזית הוא משווה את הדגימה הנוכחית לקודמת. ~ A detector starts with previous sample 0 and receives 1,1,0,1,0,0,1. Each edge compares the current sample with the previous one.
כל שינוי הוא עלייה אחת או ירידה אחת. ההפרש בין הספירות שווה לערך הסופי פחות ההתחלתי. ~ Each change is one rise or one fall. Their count difference equals the final level minus the initial level.
כמה פולסי עלייה מופיעים? ~ How many rise pulses occur? ~ 1,4,7 → 3 ~ 3;4;2;5
כמה פולסי ירידה מופיעים? ~ How many fall pulses occur? ~ 3,5 → 2 ~ 2;3;4;1
כמה חזיתות מפעילות את אות השינוי toggle? ~ How many edges assert the toggle signal? ~ 3 + 2 = 5 ~ 5;7;4;3
מה ההפרש בין מספר העליות למספר הירידות אחרי הרצף? ~ What is the number of rises minus the number of falls after the trace? ~ 1 − 0 = 1 ~ 1;0;2;−1
אם הדגימה הקודמת בתחילת הרצף הייתה 1, כמה שינויים היו נרשמים? ~ If the initial previous sample were 1 instead, how many changes would be recorded? ~ 5 − 1 = 4 ~ 4;5;6;3

384 320 gates 4
מרחקי הזזה בדרגות של מזיז חבית ~ Shift distances in barrel-shifter stages
מזיז ימינה לוגית למילים בנות 8 ביטים בנוי משלוש דרגות: הזזה ב־1, ב־2 וב־4 ביטים. כל דרגה פעילה מוסיפה את מרחקה. ~ An 8-bit logical right barrel shifter has stages shifting by 1, 2 and 4 bits. Each enabled stage adds its distance.
ביטי הבקרה מייצגים את מרחק ההזזה במשקל בינארי. ביטים שנדחקו מעבר לימין אובדים. ~ Control bits encode the shift distance in binary. Bits shifted past the right edge are discarded.
אם הדרגות של 1 ושל 4 פעילות, מה מרחק ההזזה הכולל? ~ If stages 1 and 4 are enabled, what is the total shift distance? ~ 1 + 4 = 5 ~ 5;4;3;8
מה הפלט העשרוני עבור קלט 224 והזזה ב־5? ~ What is the decimal output for input 224 shifted by 5? ~ 224 div 32 = 7 ~ 7;14;28;3
כמה קווי בחירה יש במזיז, כשכל דרגה נשלטת בנפרד? ~ How many select lines does the shifter need if each stage is independently controlled? ~ log₂(8) = 3 ~ 3;8;7;2
כמה דרגות פעילות בהזזה ב־6? ~ How many stages are enabled for a shift by 6? ~ 6 = 4 + 2 → 2 ~ 2;1;3;6
כמה ביטים מובילים מובטח שיהיו אפס לאחר הזזה ימינה ב־7, לכל קלט? ~ How many leading bits are guaranteed zero after a logical right shift by 7, for every input? ~ 8 − 1 = 7 ~ 7;8;1;0

385 329 electronics 3
מרכז תא הכימות ~ Midpoint reconstruction in a quantizer
מכמת אחיד מחלק את הטווח 0 עד 1 וולט ל־8 תאים שווים, ממוספרים מ־0. כל תא כולל את גבולו התחתון ומיוצג על ידי נקודת האמצע שלו. ~ A uniform quantizer partitions 0 to 1 volt into 8 equal bins numbered from 0. Each bin includes its lower edge and is represented by its midpoint.
קוד הכימות מציין תא. בשחזור לפי אמצע התא שגיאת הקירוב מוגבלת לחצי מרוחבו בתחום הכניסה. ~ A code identifies a bin. Midpoint reconstruction bounds the in-range approximation error by half the bin width.
מה רוחב תא במיליוולט? ~ What is the bin width in millivolts? ~ 1000/8 = 125 ~ 125;250;62.5;8
מהו קוד הכימות העשרוני עבור כניסה של 500 מיליוולט? ~ What is the decimal quantization code for an input of 500 millivolts? ~ 500/125 = 4 ~ 4;3;5;7
מהו מתח השחזור במיליוולט עבור קוד 2? ~ What reconstruction voltage in millivolts corresponds to code 2? ~ (2 + 0.5) × 125 = 312.5 ~ 312.5;250;375;125
מהו הערך המוחלט המרבי של שגיאת השחזור במיליוולט בתוך התחום? ~ What is the maximum absolute in-range reconstruction error in millivolts? ~ 125/2 = 62.5 ~ 62.5;125;31.25;250
אם מגדילים את הרזולוציה ל־4 ביטים באותו תחום, מהו רוחב התא החדש במיליוולט? ~ If resolution rises to 4 bits over the same range, what is the new bin width in millivolts? ~ 1000/16 = 62.5 ~ 62.5;125;31.25;250

386 327 electronics 4
תגובת RC בחצאי מחזור ~ RC response over half-cycles
מסנן RC מעביר נמוכים מקבל גל ריבועי מחזורי בין 0 ל־3 וולט. בכל חצי מחזור הפער בין מתח הקבל לרמת הכניסה מצטמצם למחצית. מניחים מצב מחזורי יציב. ~ An RC low-pass filter receives a periodic square wave between 0 and 3 volts. In each half-cycle the gap between capacitor voltage and input level halves. Assume periodic steady state.
במצב מחזורי המתח בסוף כל מחזור שווה למתח בתחילתו. כל חצי מחזור מקרב אותו לכניסה. ~ Periodic steady state repeats the starting voltage after each cycle. Each half-cycle moves it toward the input.
מהו מתח הקבל המזערי בוולט? ~ What is the minimum capacitor voltage in volts? ~ H=(3+L)/2, L=H/2 → L=1 ~ 1;0;1.5;2
מהו מתח הקבל המרבי בוולט? ~ What is the maximum capacitor voltage in volts? ~ H=(3+1)/2=2 ~ 2;1;3;1.5
מהו המתח שיא־לשיא בקבל בוולט? ~ What is the capacitor peak-to-peak voltage in volts? ~ 2 − 1 = 1 ~ 1;2;3;0.5
מחוץ למצב היציב, מתחילים בקבל פרוק. מה מתחו בוולט אחרי חצי המחזור הגבוה הראשון? ~ Starting outside steady state with a discharged capacitor, what is its voltage after the first high half-cycle? ~ (3 + 0)/2 = 1.5 ~ 1.5;1;2;3
מתחילים בקבל פרוק. מה מתחו בוולט אחרי חצי מחזור גבוה ואחריו חצי מחזור נמוך? ~ Starting discharged, what is the voltage after one high half-cycle followed by a low half-cycle? ~ 1.5/2 = 0.75 ~ 0.75;1;1.5;0.5

387 310 electronics 3
חלונות המרה בממיר משותף ~ Conversion slots in a shared ADC
ממיר ADC יחיד מבצע 2 מיליון המרות בשנייה. הוא עובר במחזור קבוע של 5 חלונות: חלון אחד לכל אחד מארבעה ערוצים וחלון סרק. ~ One ADC provides 2 million conversion slots per second. A repeating frame has 5 slots, one for each of four channels plus one idle slot.
קצב הדגימה של ערוץ נקבע לפי תדירות החלון המוקצה לו. גם חלון סרק מאריך את הזמן בין דגימות. ~ A channel's rate follows its allocated slots. An idle slot also extends the time between samples.
מה קצב הדגימה של כל ערוץ בקילו־דגימות לשנייה? ~ What is each channel's rate in kilosamples per second? ~ 2000/5 = 400 ~ 400;500;2000;320
מה אורך מסגרת מלאה במיקרו־שניות? ~ What is one full frame duration in microseconds? ~ 5 × 0.5 = 2.5 ~ 2.5;0.5;2;5
כמה אחוזים מחלונות ההמרה משמשים לדגימות? ~ What percentage of conversion slots actually carry samples? ~ 100 × 4/5 = 80 ~ 80;20;75;100
לאיזו תדירות נייקוויסט בקילו־הרץ מתאים קצב הדגימה של ערוץ אחד? ~ What Nyquist frequency in kHz corresponds to one channel's sample rate? ~ 400/2 = 200 ~ 200;400;1000;250
מסירים את החלון הריק. מה קצב הדגימה החדש לכל ערוץ בקילו־דגימות לשנייה? ~ Remove the idle slot. What is the new per-channel rate in kilosamples per second? ~ 2000/4 = 500 ~ 500;400;800;250

388 345 electronics 4
העומס שרואה מקור תבנין ~ Loading a Thévenin source
לרשת יש שקול תבנין של 6 וולט בטור ל־3 קילואוהם. מחברים נגד עומס משתנה ומחפשים העברת הספק מרבית לעומס. ~ A network has a Thévenin equivalent of 6 volts in series with 3 kiloohms. Connect a variable resistive load and seek maximum load power.
בעומס מותאם המתח מתחלק שווה בשווה בין ההתנגדות הפנימית לעומס. ~ At resistance matching, the internal resistance and load share the source voltage equally.
באיזה עומס בקילואוהם יתקבל הספק מרבי? ~ Which load in kiloohms receives maximum power? ~ RL = Rth = 3 ~ 3;6;1.5;9
מה מתח העומס המותאם בוולט? ~ What is the matched-load voltage in volts? ~ 6/2 = 3 ~ 3;6;2;1
מה זרם העומס המותאם במיליאמפר? ~ What is the matched-load current in milliamps? ~ 6/(3 + 3) = 1 ~ 1;2;3;0.5
מה הספק העומס המרבי במיליוואט? ~ What is the maximum load power in milliwatts? ~ 3 × 1 = 3 ~ 3;6;12;1.5
איזה אחוז מהספק מקור המתח האידאלי מתבזבז בהתנגדות הפנימית בעומס המותאם? ~ What percentage of the ideal voltage source's power is dissipated in the internal resistance at matching? ~ 100 × 3/(3 + 3) = 50 ~ 50;25;75;100

389 326 sequential 4
זמן הגעה מול חזית קליטה מאוחרת ~ Data arrival versus a delayed capture edge
חזית השיגור בזמן 0. זמן המחזור 15 פיקו־שניות, חזית הקליטה מאחרת ב־5, השהיית השעון־למוצא המרבית היא 3, השהיית הלוגיקה המרבית 12 וזמן setup הוא 2 פיקו־שניות. ~ Launch is at time 0. Period is 15 picoseconds, capture skew is +5, maximum clock-to-Q is 3, maximum logic delay is 12 and setup time is 2 picoseconds.
מרווח setup שווה למועד ההגעה המאוחר המותר פחות זמן הגעת הנתון במסלול האיטי. ~ Setup slack equals the latest allowed data arrival minus arrival along the slow path.
מהו מרווח ה־setup בפיקו־שניות? ~ What is setup slack in picoseconds? ~ (15 + 5 − 2) − (3 + 12) = 3 ~ 3;−2;5;0
באיזה זמן בפיקו־שניות מגיע הנתון במקרה האיטי? ~ At what time in picoseconds does the slow data arrive? ~ 3 + 12 = 15 ~ 15;12;18;20
באיזה זמן בפיקו־שניות נסגר חלון ההגעה המותר לצורך setup? ~ At what time in picoseconds does the allowed setup arrival window close? ~ 15 + 5 − 2 = 18 ~ 18;20;13;15
מה זמן המחזור המזערי בפיקו־שניות תחת אותו skew? ~ What is the minimum period in picoseconds with the same skew? ~ 3 + 12 + 2 − 5 = 12 ~ 12;17;15;10
מה יהיה מרווח ה־setup בפיקו־שניות אם מבטלים את ה־skew? ~ What would setup slack be in picoseconds if skew were removed? ~ (15 − 2) − 15 = −2 ~ −2;3;2;0

390 354 sequential 4
מאגר שורות לטשטוש בזרימה ~ Line storage for streaming blur
תמונה ברוחב 64 פיקסלים מגיעה שורה אחרי שורה, משמאל לימין. מסנן 3×3 מחשב רק חלונות שלמים. שתי שורות קודמות נשמרות, והפיקסל הנוכחי נכנס מחיישן התמונה. ~ A 64-pixel-wide image arrives row by row, left to right. A 3×3 filter computes only complete windows. Two preceding rows are stored and the current pixel arrives from the sensor.
חלון מקומי בזרימה דורש היסטוריה של שורות קודמות ושל פיקסלים סמוכים באותה שורה. ~ A local streaming window needs prior rows and neighboring pixels from the same row.
כמה פיקסלים מכילים שני מאגרי השורות יחד? ~ How many pixels do the two line buffers hold in total? ~ 2 × 64 = 128 ~ 128;64;192;9
כמה בתים נדרשים לשני מאגרי השורות בפיקסלים בני 16 ביטים? ~ How many bytes do the two line buffers require with 16-bit pixels? ~ 128 × 2 = 256 ~ 256;128;512;2048
מה אינדקס השורה הראשונה שמאפשרת פלט, במספור מ־0 של שורת הקלט הנוכחית? ~ What is the first current input row index that permits an output, counting from 0? ~ 3 − 1 = 2 ~ 2;0;1;3
כמה חלונות מלאים מתקבלים לאורך שורת פלט אחת? ~ How many complete windows fit across one output row? ~ 64 − 3 + 1 = 62 ~ 62;64;63;61
אחרי כמה פיקסלים שנקלטו, כולל הנוכחי, ניתן לחשב את החלון הראשון? ~ After how many received pixels, including the current one, can the first window be computed? ~ 2 × 64 + 3 = 131 ~ 131;128;130;192

391 015 gates 3
נהיגה ושחרור בצומת משותפת ~ Driving and releasing a shared node
רכיב P נוהג 1 רק עבור קלט 00. רכיב N נוהג 0 רק עבור 11. בכל צירוף אחר כל רכיב משחרר את מוצאו ל־Z. מחברים את המוצאים לאותו צומת. ~ P drives 1 only for input 00. N drives 0 only for 11. Each releases its output to Z otherwise. Connect both outputs to one node.
צומת ללא נהג נשאר בעכבה גבוהה במודל הלוגי. נהג פעיל אחד קובע את הערך. ~ An undriven node is high impedance in the logic model. One active driver sets the value.
מה ערך הצומת עבור 01, ללא נגד משיכה? ~ What is the node value for 01, without a pull resistor? ~ Z + Z → Z ~ Z;0;1;X
עבור כמה מצירופי הקלט הצומת נהוג לערך ידוע ללא נגד משיכה? ~ For how many input combinations is the node driven to a known value without a pull resistor? ~ 00,11 → 2 ~ 2;1;3;4
מה ערך הצומת עבור 11 כאשר מוסיפים נגד משיכה לאספקה? ~ What is the node value for 11 if a weak pull-up is added? ~ N(11) → 0 ~ 0;1;Z;X
אם שני קווי הקלט מחוברים לאותו ביט, כמה מצירופי הקלט האפשריים כעת משאירים את הצומת ב־Z? ~ If both input wires are tied to one bit, how many now-possible input patterns leave the node at Z? ~ {00,11} → 0 ~ 0;1;2;4
עם נגד משיכה לאדמה, בכמה צירופי קלט שונים יתקבל 1? ~ With a weak pull-down, for how many distinct input patterns is the node 1? ~ 00 → 1 ~ 1;0;2;3

392 140 sequential 3
צבירת מספרים אי־זוגיים ליצירת ריבועים ~ Accumulating odd numbers to generate squares
שני אוגרים מתחילים ב־S=0 ו־D=1. בכל חזית שני האוגרים מתעדכנים יחד: S מקבל את S+D ו־D גדל ב־2. הרוחב מספיק לכל הערכים. ~ Registers start at S=0 and D=1. On each edge they update together: S takes S+D and D increases by 2. Width is sufficient for all values.
ההפרש בין ריבועים עוקבים הוא מספר אי־זוגי. סכום האוגרים משתמש בערכיהם מלפני החזית. ~ Consecutive squares differ by an odd number. The sum uses both register values from before the edge.
מה ערכו של D מיד אחרי החזית הרביעית? ~ What is D immediately after the fourth edge? ~ 1 + 4 × 2 = 9 ~ 9;7;16;8
איזה ערך יקבל S בחזית החמישית? ~ What value does S take on the fifth edge? ~ 16 + 9 = 25 ~ 25;23;16;36
כאשר S=36 ברצף הזה, מהו D באותו זמן? ~ When S=36 in this sequence, what is D at the same time? ~ 1 + 2 × 6 = 13 ~ 13;11;12;7
כמה חזיתות דרושות למעבר מ־S=9 ל־S=49? ~ How many edges take S from 9 to 49? ~ 7 − 3 = 4 ~ 4;7;5;40
מהו סכום הערכים שנוספו ל־S בחזיתות הרביעית והחמישית יחד? ~ What is the sum of the addends applied to S on edges four and five? ~ 7 + 9 = 16 ~ 16;14;18;25

393 140 bits 4
שמירת נשיאה בבדיקת פיתגורס ~ Preserving carry in a Pythagorean test
בודקים אם a²+b²=c² עבור שלושה קלטים לא מסומנים בני 4 ביטים. כל ריבוע מחושב במלואו. יש לבחור רוחב מספיק למחבר לפני ההשוואה. ~ Test whether a²+b²=c² for three unsigned 4-bit inputs. Each square is computed exactly. Choose a sufficiently wide adder before comparing.
בחיבור שני ריבועים מדויקים עלול להיווצר ביט נוסף. יש להרחיב את האופרנדים לפני החיבור. ~ Adding two exact squares can require one extra bit. Widen the operands before adding.
מהו הסכום המרבי של שני הריבועים? ~ What is the largest possible sum of the two squares? ~ 15² + 15² = 450 ~ 450;225;510;256
כמה ביטים דרושים לשמירת הסכום לכל האפשרויות? ~ How many bits store the sum for all possible inputs? ~ 256 ≤ 450 < 512 → 9 ~ 9;8;10;7
כמה ביטים דרושים לשמירת ריבוע אחד בלבד? ~ How many bits are needed for a single square? ~ 128 ≤ 225 < 256 → 8 ~ 8;4;9;7
מה יתקבל מהסכום המרבי אם נשמור רק את 8 הביטים התחתונים? ~ If only the low 8 bits of the maximum sum are kept, what value remains? ~ 450 mod 256 = 194 ~ 194;225;450;255
עבור a=9 ו־b=12, איזה ערך c בן 4 ביטים יגרום להשוואה להצליח? ~ For a=9 and b=12, what 4-bit c makes the comparison succeed? ~ 81 + 144 = 225 = 15² ~ 15;13;14;12

394 307 electronics 3
בדיקת סף על דגימות של טעינת קבל ~ Detecting a threshold in sampled capacitor charge
קבל פרוק נטען לעבר 900 מיליוולט. בין דגימות עוקבות הפרש המתח מהיעד מצטמצם למחצית. המשווה מציין מתח הגדול או שווה לשני שלישים מהיעד. ~ A discharged capacitor charges toward 900 millivolts. Between samples its gap to the target halves. A comparator asserts at or above two thirds of the target.
בכל דגימה נשאר חצי מהפער הקודם ליעד. המשווה בודק את המתח שהצטבר. ~ Each sample leaves half the previous gap to the target. The comparator tests the accumulated voltage.
באיזו דגימה אחרי תחילת הטעינה, במספור מ־1, המשווה מופעל לראשונה? ~ At which sample after charging starts, numbered from 1, does the comparator first assert? ~ 450 < 600 ≤ 675 → 2 ~ 2;1;3;4
מהו מתח הסף במיליוולט? ~ What is the threshold voltage in millivolts? ~ 900 × 2/3 = 600 ~ 600;300;450;675
מה מתח הקבל אחרי שתי דגימות במיליוולט? ~ What is capacitor voltage after two samples in millivolts? ~ 900 − 900/4 = 675 ~ 675;600;450;750
מה הפער ליעד אחרי שלוש דגימות במיליוולט? ~ What is the remaining gap to the target after three samples in millivolts? ~ 900/8 = 112.5 ~ 112.5;225;787.5;300
מעלים את סף המשווה ל־800 מיליוולט. באיזו דגימה יופעל לראשונה? ~ Raise the threshold to 800 millivolts. At which sample does it first assert? ~ 787.5 < 800 ≤ 843.75 → 4 ~ 4;3;2;5

395 321 states 3
שמירת בקשות למעלית במסכת ביטים ~ Latching elevator requests in a bit mask
שלוש קומות ממוספרות 0,1,2. בקשה מדליקה את הביט המתאים, והגעה לקומה מוחקת רק אותו. מתחילים במסכה ריקה. הרצף הוא בקשה ל־2, בקשה ל־0, בקשה ל־2, הגעה ל־0. ~ Floors are numbered 0,1,2. A request sets its floor bit and arrival clears only that bit. Start empty. Events are request 2, request 0, request 2, arrive at 0.
מסכת בקשות שומרת אם כל קומה ממתינה. בקשות חוזרות לאותה קומה אינן מייצרות רשומות נפרדות. ~ A request mask tracks whether each floor is waiting. Repeated requests for one floor share one bit.
מהו הערך העשרוני של המסכה בסוף? ~ What is the final decimal mask? ~ 0 → 4 → 5 → 5 → 4 ~ 4;5;2;1
כמה בקשות לקומות שונות ממתינות לפני ההגעה ל־0? ~ How many distinct floors are waiting before arrival at 0? ~ {0,2} → 2 ~ 2;3;1;0
מהו הביט שנמחק בהגעה, כערך מסכה עשרוני? ~ What is the decimal value of the bit mask cleared on arrival? ~ 2⁰ = 1 ~ 1;0;2;4
מה יהיה ערך המסכה אם לאחר הרצף תתקבל גם בקשה לקומה 1? ~ What will the mask be if a request for floor 1 follows the trace? ~ 4 OR 2 = 6 ~ 6;5;7;2
כמה מצבי מסכה אפשריים עבור שלוש קומות, כולל מצב ריק? ~ How many mask states exist for three floors, including empty? ~ 2³ = 8 ~ 8;3;7;9

396 359 electronics 3
נקודת הכשל הראשונה בסריקת מתח ~ First failing point on a voltage sweep
ציוד בדיקה סורק מתחים החל מ־800 מיליוולט בקפיצות מדויקות של 25 מיליוולט ועד 1000 כולל. הבדיקה עוברת מתחת ל־910 מיליוולט ונכשלת ממנו ומעלה. ~ A tester sweeps from 800 through 1000 millivolts inclusive in exact 25-millivolt increments. It passes below 910 millivolts and fails at or above it.
נקודת הכשל הראשונה בסריקה היא המתח הראשון ברשת שנמצא בצד הכושל של הסף. ~ The first measured failure is the earliest grid voltage on the failing side of the threshold.
באיזה מתח במיליוולט נמדד הכשל הראשון? ~ At what voltage in millivolts is the first failure measured? ~ 800 + 5 × 25 = 925 ~ 925;910;900;950
מהו המתח האחרון במיליוולט שעבר בהצלחה? ~ What is the last passing voltage in millivolts? ~ 925 − 25 = 900 ~ 900;910;875;925
כמה נקודות נבדקות אם מפסיקים מיד לאחר הכשל הראשון? ~ How many points are tested when stopping immediately after the first failure? ~ 800,825,850,875,900,925 → 6 ~ 6;5;4;9
כמה נקודות יש בסריקה המלאה, כולל שני הקצוות? ~ How many points are in the full sweep, including both endpoints? ~ (1000 − 800)/25 + 1 = 9 ~ 9;8;10;7
אם מקטינים את גודל הקפיצה ל־10 מיליוולט, מה הכשל הראשון הנמדד במיליוולט? ~ If the increment falls to 10 millivolts, what is the first measured failing voltage in millivolts? ~ 800 + 11 × 10 = 910 ~ 910;900;920;925

397 044 sequential 4
עצירת סדרת פיבונאצ׳י בעזרת enable ~ Pausing a Fibonacci register pair
זוג אוגרים מתחיל ב־X=0,Y=1. בכל חזית מאופשרת הזוג מתעדכן במקביל ל־(Y,X+Y), ובחזית מושבתת נשמר. דגימות enable הן 1,1,0,1,1. המוצא הוא X+Y. ~ Registers start at X=0,Y=1. An enabled edge updates the pair simultaneously to (Y,X+Y). A disabled edge holds both. Enable samples are 1,1,0,1,1. Output is X+Y.
עדכון שני האוגרים משתמש בערכי החזית הקודמת. עצירה של שניהם שומרת את המקום בסדרה. ~ Both registers update from the previous values. Holding them together preserves the position in the sequence.
מהו המוצא אחרי כל הדגימות? ~ What is the output after all samples? ~ (3,5) → 8 ~ 8;5;13;3
מה ערך X מיד אחרי החזית המושבתת? ~ What is X immediately after the disabled edge? ~ (0,1) → (1,1) → (1,2) → (1,2) ~ 1;2;3;0
מהו המוצא מיד אחרי האתחול ולפני חזית מופעלת כלשהי? ~ What is the output immediately after initialization before any enabled edge? ~ 0 + 1 = 1 ~ 1;0;2;3
אם גם החזית השלישית תופעל, מה יהיה המוצא הסופי? ~ If the third edge is enabled as well, what is the final output? ~ (5,8) → 13 ~ 13;8;5;21
כמה מהחזיתות ברצף המקורי שינו את ערך המוצא? ~ How many edges in the original trace changed the output value? ~ 1 → 2 → 3 → 3 → 5 → 8 ~ 4;5;3;2

398 199 bits 3
סיבוב ימינה שמשמר ביטים ~ Rotating right without losing bits
מילת 8 ביטים היא 10010101. מסובבים אותה ימינה באופן מחזורי. ביט שיוצא מהקצה הימני חוזר לקצה השמאלי. ~ An 8-bit word is 10010101. Rotate it cyclically to the right. A bit leaving the right edge reenters at the left edge.
סיבוב מעביר ביטים בין מיקומים מודולו רוחב המילה ושומר את מספר האחדות. ~ Rotation moves bits between positions modulo word width and preserves the number of ones.
מהי המילה אחרי סיבוב אחד ימינה? ~ What is the word after one right rotation? ~ 10010101 → 11001010 ~ 11001010;01001010;00101011;10101001
כמה אחדות יהיו במילה אחרי 5 סיבובים? ~ How many ones are in the word after 5 rotations? ~ 1 + 1 + 1 + 1 = 4 ~ 4;3;5;8
לאיזה מיקום יעבור ביט 1 המקורי אחרי 3 סיבובים ימינה, במספור מ־0 מימין? ~ Where does original bit position 1 move after 3 right rotations, numbering from 0 on the right? ~ (1 − 3) mod 8 = 6 ~ 6;4;5;7
כמה סיבובים ימינה לכל הפחות יש להוסיף ל־3 סיבובים כדי שהמילה תחזור למצבה המקורי? ~ How many more right rotations must follow 3 rotations to first restore this word? ~ 8 − 3 = 5 ~ 5;3;8;1
מהי המילה אחרי 4 סיבובים ימינה? ~ What is the word after 4 right rotations? ~ 1001 0101 → 0101 1001 ~ 01011001;01010110;00001001;10010101

399 001 bits 3
שמירת משקל ביטי הנשיאה בספירת אחדות ~ Preserving carry weight in a population count
סופרים אחדות ב־7 ביטים. שני מחברים מלאים ראשונים מקבלים שלשות עם 3 ו־2 אחדות. הביט השביעי הוא 1. כל מחבר מוציא ביט סכום וביט נשיאה. ~ Count ones in 7 bits. The first two full adders receive triples containing 3 and 2 ones. The seventh bit is 1. Each adder produces a sum bit and a carry bit.
ביט נשיאה שוקל פי שניים מביט הסכום של אותה דרגה. מחברים יחד ביטים מאותו משקל. ~ A carry has twice the weight of its stage's sum bit. Add bits of the same weight together.
כמה ביטי נשיאה פעילים יוצאים משני המחברים הראשונים יחד? ~ How many carry bits are active across the two initial adders? ~ floor(3/2) + floor(2/2) = 2 ~ 2;1;3;0
כמה אחדות נכנסות למחבר הבא של ביטי המשקל הנמוך, כולל הביט השביעי? ~ How many ones enter the next low-weight adder, including the seventh bit? ~ (3 mod 2) + (2 mod 2) + 1 = 2 ~ 2;3;1;0
מהו ביט הפלט הפחות משמעותי של הספירה המלאה? ~ What is the least significant bit of the complete count? ~ 6 mod 2 = 0 ~ 0;1;X;Z
מה הספירה הסופית בבינארי, ב־3 ביטים? ~ What is the final count in 3-bit binary? ~ 3 + 2 + 1 = 6 → 110 ~ 110;101;111;011
אם הביט השביעי היה 0, מה היה הערך העשרוני של הספירה? ~ If the seventh bit were 0, what would the decimal count be? ~ 3 + 2 + 0 = 5 ~ 5;6;4;3

400 176 sequential 4
תקציב השהיה נוסף למסלול אחד ~ Added-delay budget for one path
למסלול יש מרווח setup של 18 פיקו־שניות ומרווח hold של מינוס 4 פיקו־שניות. במודל זה רכיב השהיה מוסיף אותה השהיה d למסלול המהיר והאיטי, ללא שינוי בשעון. ~ A path has setup slack of 18 picoseconds and hold slack of −4 picoseconds. In this model a delay element adds the same d to fast and slow data paths, with unchanged clock timing.
השהיית נתונים נוספת מגדילה את מרווח ה־hold ומקטינה את מרווח ה־setup באותה כמות במודל הזה. ~ Added data delay increases hold slack and decreases setup slack by the same amount in this model.
מהי התוספת המזערית בפיקו־שניות שמתקנת את הפרת ה־hold? ~ What minimum added delay in picoseconds fixes the hold violation? ~ −4 + d = 0 → d = 4 ~ 4;0;14;18
מהי התוספת המרבית בפיקו־שניות שעדיין מאפשרת לעמוד ב־setup? ~ What maximum delay in picoseconds still meets setup? ~ 18 − d = 0 → d = 18 ~ 18;14;22;4
מה יהיה מרווח ה־setup בפיקו־שניות לאחר הוספת 7 פיקו־שניות? ~ What is setup slack in picoseconds after adding 7 picoseconds? ~ 18 − 7 = 11 ~ 11;25;3;7
מה יהיה מרווח ה־hold בפיקו־שניות לאחר אותה תוספת של 7 פיקו־שניות? ~ What is hold slack in picoseconds after adding 7 picoseconds? ~ −4 + 7 = 3 ~ 3;11;−11;7
איזו תוספת בפיקו־שניות משווה בין מרווחי ה־setup וה־hold? ~ What added delay in picoseconds makes setup and hold slacks equal? ~ 18 − d = −4 + d → d = 11 ~ 11;7;14;9
"""


def build():
    _, questions, checks = build_bundle(LESSONS)
    return questions, checks


def write():
    cards, questions, checks = build_bundle(LESSONS)
    for path, records in (
        (CONTENT / "fundamentals-hardware-800.json", cards),
        (SHARDS / "hardware_800.json", questions),
        (SHARDS / "hardware_800.checks.json", checks),
    ):
        path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write()
