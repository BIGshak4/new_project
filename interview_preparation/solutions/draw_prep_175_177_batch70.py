"""Clean bilingual conceptual diagrams; no reconstruction of missing circuits."""

from draw_prep_016_064 import phrase, wire
from draw_prep_170_174_batch70 import GREEN, OUT, PURPLE, canvas, label, panel, table


def buffer(lang):
    im, d = canvas(
        "באפר מפריד עומס — דוגמה שנבחרה במפורש",
        "Buffer load isolation: an explicitly chosen example",
        lang,
        1400,
    )
    phrase(
        d,
        (1200, 210),
        "השרטוט המקורי לא צורף; זו אינה שחזור שלו",
        "The original circuit is absent; this is not its reconstruction",
        lang,
        35,
    )
    panel(d, (160, 330, 2250, 610))
    label(d, (1200, 400), "source Rs  →  CL", 46)
    label(d, (1200, 520), "t50 = ln(2) Rs CL", 42, GREEN)
    panel(d, (160, 730, 2250, 1070))
    label(d, (1200, 820), "source Rs  →  Cin | BUFFER tb, Rb |  →  CL", 42)
    label(d, (1200, 970), "t50 ≈ ln(2) Rs Cin + tb + ln(2) Rb CL", 40, GREEN)
    phrase(
        d,
        (1200, 1210),
        "יתרון אפשרי בעומס גדול; השהיה וצריכת הספק נוספות",
        "Large loads may benefit; intrinsic delay and power are added",
        lang,
        37,
    )
    im.save(OUT / f"prep-175-buffer-load-isolation-{lang}.png")


def timing(lang):
    im, d = canvas("חלון יציבות סביב חזית הלכידה", "A stability window around capture", lang, 1500)
    panel(d, (170, 250, 600, 430))
    panel(d, (950, 250, 1430, 430))
    panel(d, (1780, 250, 2220, 430))
    label(d, (385, 340), "LAUNCH FF", 36)
    label(d, (1190, 340), "LOGIC / WIRE", 36)
    label(d, (2000, 340), "CAPTURE FF", 36)
    wire(d, [(600, 340), (950, 340)], PURPLE, arrow=True)
    wire(d, [(1430, 340), (1780, 340)], PURPLE, arrow=True)
    label(d, (1200, 530), "s > 0: capture clock arrives later", 39)
    wire(d, [(260, 800), (2160, 800)], PURPLE, arrow=True)
    d.line((1200, 660, 1200, 950), fill=GREEN, width=7)
    d.rectangle((760, 760, 1510, 840), outline=PURPLE, width=5)
    label(d, (1200, 630), "CAPTURE", 37, GREEN)
    label(d, (950, 910), "SETUP", 37)
    label(d, (1380, 910), "HOLD", 37)
    phrase(
        d,
        (1200, 1010),
        "הנתון חייב להישאר יציב לאורך שני חלקי החלון",
        "D must stay stable across both parts of the window",
        lang,
        36,
    )
    label(d, (1200, 1150), "setup slack = T + s - Us - setup - CQmax - Dmax", 37)
    label(d, (1200, 1260), "hold slack = CQmin + Dmin - s - Uh - hold", 37)
    phrase(
        d,
        (1200, 1390),
        "מחזור ארוך יותר עוזר ל־setup; אינו מתקן hold במודל הזה",
        "A longer period helps setup; it does not fix hold in this model",
        lang,
        34,
    )
    im.save(OUT / f"prep-176-setup-hold-windows-{lang}.png")


def crosstalk(lang):
    im, d = canvas(
        "השכן משנה את המטען בקבל הצימוד", "A neighbor changes the coupling-capacitor charge", lang, 1450
    )
    label(d, (430, 330), "aggressor a(t)", 39, GREEN)
    wire(d, [(750, 330), (2140, 330)], GREEN)
    label(d, (440, 600), "R → victim v(t)", 39)
    wire(d, [(750, 600), (2140, 600)], PURPLE)
    d.line((1430, 330, 1430, 430), fill=PURPLE, width=6)
    d.line((1380, 430, 1480, 430), fill=PURPLE, width=6)
    d.line((1380, 465, 1480, 465), fill=PURPLE, width=6)
    d.line((1430, 465, 1430, 600), fill=PURPLE, width=6)
    label(d, (1570, 445), "Cc", 36)
    d.line((1960, 600, 1960, 690), fill=PURPLE, width=6)
    d.line((1900, 690, 2020, 690), fill=PURPLE, width=6)
    d.line((1900, 725, 2020, 725), fill=PURPLE, width=6)
    d.line((1960, 725, 1960, 790), fill=PURPLE, width=6)
    label(d, (1780, 710), "Cg", 36)
    label(d, (1960, 830), "GND", 31)
    table(
        d,
        [
            ["aligned slopes", "k = a'/v'", "Ceff"],
            ["same direction", "+1", "Cg"],
            ["quiet neighbor", "0", "Cg + Cc"],
            ["opposite", "-1", "Cg + 2Cc"],
        ],
        260,
        910,
        [740, 520, 620],
        92,
        34,
    )
    phrase(
        d,
        (1200, 1350),
        "גורמי ההמחשה אינם קבועים לכל חוט אמיתי או חלון מיתוג",
        "These illustrative factors are not universal wire or timing-window constants",
        lang,
        34,
    )
    im.save(OUT / f"prep-177-coupled-wire-delay-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        buffer(language)
        timing(language)
        crosstalk(language)
    print("Six clean bilingual diagrams saved.")
