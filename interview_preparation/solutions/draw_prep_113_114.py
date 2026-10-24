"""Localized solution-only public-round and complementary-degree diagrams."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, PALE = "#fffdf8", "#302344", "#5d4383", "#33786d", "#e7def0"


def signal_rounds(language):
    image = Image.new("RGB", (1800, 1180), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (900, 80), "סופרים הזדמנויות לאותת מאז ההכרזה",
           "Count signal opportunities after the announcement", language, 49, bold=True)
    phrase(draw, (900, 165), "ההסקה תקפה רק תחת ההנחות המפורשות של הנוסח הערוך",
           "Inference uses the edited contract's explicit assumptions", language, 34)
    hours = ("23:00", "00:00", "01:00", "02:00", "03:00", "04:00")
    for index, hour in enumerate(hours):
        x = 160 + 290 * index
        color = PURPLE if index in (0, 5) else GREEN
        draw.rounded_rectangle((x - 110, 355, x + 110, 485), 22,
                               fill=PALE if index in (0, 5) else PAPER, outline=color, width=5)
        text(draw, (x, 420), hour, 47, bold=True, color=color)
        if index < 5:
            wire(draw, [(x + 115, 420), (x + 170, 420)], INK, 4)
        if index == 0:
            phrase(draw, (x, 560), "הכרזה", "Announcement", language, 31, bold=True)
            text(draw, (x, 630), "—", 42)
        else:
            if language == "he":
                phrase(draw, (x + 28, 560), "סבב", "Round", language, 35,
                       color=color, bold=True)
                text(draw, (x - 43, 560), str(index), 35, color=color, bold=True)
            else:
                text(draw, (x, 560), f"round {index}", 35, color=color, bold=True)
            phrase(draw, (x, 640), "אות ראשון" if index == 5 else "אין אות",
                   "First signal" if index == 5 else "Silence", language, 31, color=color)
    text(draw, (750, 790), "23 → 00 → 01 → 02 → 03 → 04", 44,
         bold=True, color=PURPLE)
    if language == "he":
        phrase(draw, (1460, 750), "מספר סבבים", "Rounds", language, 31, color=PURPLE)
        text(draw, (1460, 810), "5", 45, bold=True, color=PURPLE)
    else:
        text(draw, (1460, 790), "5 rounds", 40, bold=True, color=PURPLE)
    phrase(draw, (900, 900), "השתיקה בכל סבב שוללת את אפשרות המספר הקטן הבא",
           "Each silent round rules out the next smaller liar count", language, 36)
    phrase(draw, (900, 1000), "במודל הערוך חמישה שקרנים גורמים לאות ראשון בסבב החמישי",
           "In the edited model five liars first signal in round five", language, 36, bold=True)
    phrase(draw, (900, 1100), "שמיעת אות בשעה זו בלבד אינה מספיקה בנוסח המקורי החסר",
           "Hearing a signal at that time alone is insufficient in the incomplete source", language, 32)
    image.save(OUT / f"prep-113-public-signal-rounds-{language}.png")


def handshake_pairs(language):
    image = Image.new("RGB", (1800, 1320), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (900, 80), "מספרי לחיצות משלימים שייכים לבני זוג",
           "Complementary handshake counts belong to partners", language, 48, bold=True)
    phrase(draw, (900, 165), "תשעת המשיבים שאינם הנסיך מדווחים מספרים שונים מאפס עד שמונה",
           "The nine respondents other than the prince have degrees zero through eight", language, 33)
    for index in range(4):
        y = 300 + 160 * index
        color = PURPLE if index % 2 == 0 else GREEN
        for x, number in ((440, index), (1360, 8 - index)):
            draw.rounded_rectangle((x - 140, y - 50, x + 140, y + 55), 18,
                                   fill=PALE if color == PURPLE else "#e6f0eb", outline=color, width=5)
            text(draw, (x, y), str(number), 49, bold=True, color=color)
        draw.line((580, y, 1220, y), fill=color, width=5)
        phrase(draw, (900, y - 43), "בני זוג", "Partners", language, 30, color=color)
    phrase(draw, (900, 900), "הקווים מציינים זוגיות ואינם לחיצות ידיים",
           "Lines indicate partnerships, not handshakes", language, 34, bold=True)
    for x, he, en in ((440, "הנסיכה", "Princess"), (1360, "הנסיך", "Prince")):
        draw.rounded_rectangle((x - 180, 995, x + 180, 1115), 22,
                               fill="#eee7f4", outline=PURPLE, width=6)
        text(draw, (x, 1055), "4", 58, color=PURPLE, bold=True)
        phrase(draw, (x, 950), he, en, language, 36, bold=True)
    draw.line((620, 1055, 1180, 1055), fill=PURPLE, width=5)
    phrase(draw, (900, 1190), "הנסיכה נשארת עם המספר האמצעי וגם הנסיך לחץ ארבע ידיים",
           "The princess retains the middle count; the prince also shook four hands", language, 34)
    phrase(draw, (900, 1270), "ארבעה זוגות אורחים בדיוק ועוד זוג המארחים",
           "Exactly four guest couples plus the host couple", language, 32)
    image.save(OUT / f"prep-114-complementary-handshake-counts-{language}.png")


if __name__ == "__main__":
    for lang in ("he", "en"):
        signal_rounds(lang)
        handshake_pairs(lang)
