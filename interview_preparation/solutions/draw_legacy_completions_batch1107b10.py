"""Clean bilingual diagrams for explicitly chosen teaching contracts."""
from pathlib import Path

from draw_prep_016_064 import phrase, text
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, BLUE, GREEN, RED = "#23334b", "#2a62a0", "#257b67", "#b24747"


def painters(lang):
    im = Image.new("RGB", (2400, 1500), "white")
    d = ImageDraw.Draw(im)
    phrase(d, (1200, 90), "חוזה נבחר: ימי צביעה לעומת תנועה ביניהם",
           "Selected contract: painting days versus motion between them", lang, 52, bold=True)
    phrase(d, (1200, 180), "כללי הדוגמה הם השלמה לימודית מפורשת",
           "The example rules are explicitly authored teaching assumptions", lang, 37, color=GREEN)
    text(d, (650, 260), "A(n) = 1 + 2n", 42, color=BLUE)
    text(d, (1680, 260), "B(n) = 100 - n(n+3)/2", 40, color=RED)
    d.rounded_rectangle((120, 320, 2280, 1150), radius=24, fill="#f5f8fd", outline=BLUE, width=4)
    x0, y0, xs, ys = 300, 1040, 900, 25
    d.line((x0, 1040, 2200, 1040), fill=INK, width=4)
    d.line((x0, 1040, x0, 330), fill=INK, width=4)
    for day in (10, 11, 12):
        x = x0 + (day - 10) * xs
        d.line((x, 1030, x, 1050), fill=INK, width=3)
        text(d, (x, 1100), str(day), 39)
    # A close view of the two valid painting intervals surrounding the crossing.
    scale = lambda value: y0 - (value - 10) * ys
    d.line([(x0 + (n - 10) * xs, scale(1 + 2 * n)) for n in (10, 11, 12)], fill=BLUE, width=7)
    d.line([(x0 + (n - 10) * xs, scale(100 - n * (n + 3) // 2)) for n in (10, 11, 12)], fill=RED, width=7)
    for n in (10, 12):
        for value, color in [(1 + 2 * n, BLUE), (100 - n * (n + 3) // 2, RED)]:
            x, y = x0 + (n - 10) * xs, scale(value)
            d.ellipse((x - 11, y - 11, x + 11, y + 11), fill=color)
            text(d, (x + 65, y - 18), str(value), 36, color=color)
    crossing_x = x0 + xs
    crossing_y = scale(23)
    d.ellipse((crossing_x - 14, crossing_y - 14, crossing_x + 14, crossing_y + 14), fill=GREEN)
    text(d, (1760, 450), "day = 11", 44, bold=True, color=GREEN)
    text(d, (1760, 520), "door = 23", 44, bold=True, color=GREEN)
    text(d, (1260, crossing_y - 35), "23", 40, bold=True, color=GREEN)
    phrase(d, (1200, 1240), "בכלל שנבחר נפגשים ביום שלם ובדלת שלמה",
           "The selected rule meets on an integer day at a numbered door", lang, 43, bold=True)
    phrase(d, (1200, 1330), "גם התנועה הישרה בין האירועים נפגשת לראשונה באותו רגע",
           "Linear inter-event travel first meets at that same instant", lang, 38)
    text(d, (1200, 1420), "n = 0,...,12; 100 doors labeled 1,...,100", 36)
    return im


def coins(lang):
    im = Image.new("RGB", (2400, 1500), "white")
    d = ImageDraw.Draw(im)
    phrase(d, (1200, 90), "מלאי נבחר: תשלום מדויק בלי למחזר מטבע",
           "Selected inventory: exact payment without reusing a coin", lang, 52, bold=True)
    phrase(d, (1200, 180), "המלאי בדוגמה הוא השלמה לימודית מפורשת",
           "This inventory is an explicitly authored teaching assumption", lang, 37, color=GREEN)
    for i, value in enumerate((100, 60, 35, 25, 15, 10)):
        x = 260 + i * 375
        selected = i in (1, 2, 3)
        color = GREEN if selected else INK
        d.ellipse((x - 115, 320, x + 115, 550), fill="#e5f2ed" if selected else "#f3f5f8", outline=color, width=6)
        text(d, (x, 435), str(value), 60, bold=True, color=color)
        text(d, (x, 620), f"index {i}", 35, color=color)
    d.rounded_rectangle((210, 760, 2190, 1040), radius=20, outline=GREEN, fill="#eaf6f0", width=5)
    text(d, (1200, 850), "60 + 35 + 25 = 120", 72, bold=True, color=GREEN)
    text(d, (1200, 955), "indices [1, 2, 3]  |  minimum = 3", 46, bold=True, color=GREEN)
    phrase(d, (1200, 1140), "אין מטבע יחיד או זוג שמשלימים את היעד",
           "No one-coin or two-coin subset reaches the target", lang, 42, bold=True)
    text(d, (1200, 1235), "greedy: 100 + 15 = 115; missing 5", 44, color=RED)
    phrase(d, (1200, 1355), "לכל אינדקס מטבע פיזי אחד בלבד",
           "Each index denotes exactly one physical coin", lang, 39)
    return im


if __name__ == "__main__":
    for lang in ("he", "en"):
        painters(lang).save(OUT / f"prep-133-completed-contract-batch1107b10-{lang}.png")
        coins(lang).save(OUT / f"prep-271-concrete-inventory-batch1107b10-{lang}.png")
