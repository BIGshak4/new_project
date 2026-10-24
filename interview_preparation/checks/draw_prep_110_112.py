"""Draw original bilingual comparator and inverted-pin gate teaching figures."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, BLUE, GREEN, GREY = "#17213a", "#345b9f", "#276858", "#657186"
FONT = "C:/Windows/Fonts/arial.ttf"


def figure(title, subtitle, he):
    image = Image.new("RGB", (1800, 1120), "white")
    draw = ImageDraw.Draw(image)
    text(draw, (900, 65), title, 45, he, "mm")
    text(draw, (900, 135), subtitle, 27, he, "mm", GREY)
    return image, draw


def text(draw, xy, value, size=29, rtl=False, anchor="lm", color=INK):
    # These RTL labels contain only Hebrew and punctuation; technical expressions
    # are drawn as separate LTR labels. This Pillow runtime has no libraqm.
    draw.text(xy, value[::-1] if rtl else value,
              font=ImageFont.truetype(FONT, size), fill=color, anchor=anchor)


def box(draw, bounds, label):
    draw.rounded_rectangle(bounds, radius=15, outline=BLUE, width=4, fill="#f5f8fd")
    x1, y1, x2, y2 = bounds
    text(draw, ((x1+x2)/2, (y1+y2)/2), label, 31,
         rtl=any("\u05d0" <= ch <= "\u05ea" for ch in label), anchor="mm")


def arrow(draw, points, color=BLUE):
    draw.line(points, fill=color, width=4)
    (a, b), (x, y) = points[-2:]
    if x > a:
        head = [(x, y), (x-15, y-8), (x-15, y+8)]
    elif x < a:
        head = [(x, y), (x+15, y-8), (x+15, y+8)]
    elif y > b:
        head = [(x, y), (x-8, y-15), (x+8, y-15)]
    else:
        head = [(x, y), (x-8, y+15), (x+8, y+15)]
    draw.polygon(head, fill=color)


def inverted_pin(draw, x, y):
    draw.ellipse((x-10, y-10, x+10, y+10), fill="white", outline=BLUE, width=4)


for lang in ("he", "en"):
    he = lang == "he"
    img, d = figure("משווה ביט אחד ומשווה ארבעה ביטים" if he else "One-bit and four-bit comparators",
                    "הסימון השלישי תוקן במפורש; זהו ממשק השאלה בלבד" if he else
                    "The third label is explicitly corrected to a<b; this is the question interface", he)
    box(d, (650, 270, 1130, 650), "compare_bit")
    for y, value in ((365, "a"), (550, "b")):
        text(d, (345, y), value, 37)
        arrow(d, [(410, y), (650, y)])
    for y, value in ((340, "G = (a > b)"), (460, "E = (a == b)"), (580, "L = (a < b)")):
        arrow(d, [(1130, y), (1330, y)])
        text(d, (1370, y), value, 32)
    text(d, (900, 785), "סעיף א: שתי כניסות של ביט אחד ושלוש יציאות השוואה" if he else
         "Part A: a,b are single bits; G,E,L are output bits.", 31, he, "mm")
    text(d, (900, 850), "סעיף ב: השוו שתי מילים של ארבעה ביטים ללא סימן בעזרת רכיבים אלו" if he else
         "Part B: A[3:0], B[3:0] are unsigned; build G,E,L from these cells.", 29, he, "mm")
    text(d, (900, 1000), "ממשק שאלה נקי; פלט גדול ופלט קטן הם מוצאים שונים" if he else "Clean question interface; L is distinct from G", 28, he, "mm", GREEN)
    img.save(OUT/f"prep-110-prompt-comparator-{lang}.png")

    img, d = figure("משווה מדורג: הביט המשמעותי קובע קודם" if he else "Comparator cascade: higher bits decide first",
                    "פתרון מוצע — השוואה ללא סימן, לא ניתוח תזמון פיזי" if he else
                    "Proposed solution — unsigned comparison, not physical timing analysis", he)
    for i, bit in enumerate((3, 2, 1, 0)):
        x = 150 + i*420
        text(d, (x+150, 265), f"A{bit}, B{bit}", 34, anchor="mm")
        arrow(d, [(x+150, 300), (x+150, 350)])
        box(d, (x, 350, x+300, 530), f"g{bit}, e{bit}, l{bit}")
        box(d, (x, 620, x+300, 755), "צירוף" if he else "combine")
        arrow(d, [(x+150, 530), (x+150, 620)])
        if i < 3:
            arrow(d, [(x+300, 690), (x+420, 690)])
    text(d, (900, 855), "G' = G OR (E AND gi)     L' = L OR (E AND li)     E' = E AND ei", 30, anchor="mm")
    text(d, (900, 920), "(G,E,L) = (0,1,0);  i: 3 → 2 → 1 → 0", 31, anchor="mm")
    text(d, (900, 1015), "לוגיקה מצטברת משמאל לימין, ללא שעון או רגיסטרים" if he else
         "Accumulated combinational logic from left to right; no clock or registers", 29, he, "mm", GREEN)
    img.save(OUT/f"prep-110-comparator-cascade-{lang}.png")

    img, d = figure("שערים עם כניסה מהופכת אחת" if he else "Gates with one inverted input",
                    "העיגול מציין היפוך בכניסה, לא ביציאה" if he else
                    "A bubble denotes an inverted input, not an inverted output", he)
    for x, name, expression in ((300, "ANDN", "F(p,q) = p AND NOT q"), (1050, "ORN", "G(p,q) = p OR NOT q")):
        box(d, (x, 340, x+380, 650), name)
        arrow(d, [(x-150, 410), (x, 410)])
        arrow(d, [(x-150, 565), (x-10, 565)])
        inverted_pin(d, x, 565)
        text(d, (x-190, 410), "p", 34)
        text(d, (x-190, 565), "q", 34)
        arrow(d, [(x+380, 495), (x+525, 495)])
        text(d, (x+190, 760), expression, 31, anchor="mm")
    text(d, (900, 940), "נדרש שער וגם רגיל; תנאי שימוש בקבועים ובעותקי שערים מפורטים בשאלה" if he else
         "Required: Y=A AND B; constant-wire and gate-copy rules are explicit in the prompt", 28, he, "mm", GREEN)
    img.save(OUT/f"prep-112-prompt-inverted-pins-{lang}.png")

    img, d = figure("יצירת שער וגם משני סוגי השערים הנתונים" if he else "AND from one ORN and one ANDN",
                    "פתרון מוצע — כאן מותר חיבור לקבוע 0" if he else
                    "Proposed solution — a constant-zero wire is explicitly allowed here", he)
    box(d, (380, 390, 740, 700), "ORN")
    text(d, (135, 460), "0", 39)
    arrow(d, [(195, 460), (380, 460)])
    text(d, (135, 620), "B", 39)
    arrow(d, [(195, 620), (370, 620)])
    inverted_pin(d, 380, 620)
    box(d, (1100, 285, 1460, 595), "ANDN")
    text(d, (850, 355), "A", 39)
    arrow(d, [(910, 355), (1100, 355)])
    arrow(d, [(740, 540), (920, 540), (920, 515), (1090, 515)])
    inverted_pin(d, 1100, 515)
    text(d, (905, 620), "t = NOT B", 31, anchor="mm")
    arrow(d, [(1460, 440), (1610, 440)])
    text(d, (1650, 440), "Y", 39)
    text(d, (900, 840), "t = G(0,B) = NOT B", 36, anchor="mm")
    text(d, (900, 920), "Y = F(A,t) = A AND NOT(NOT B) = A AND B", 34, anchor="mm")
    text(d, (900, 1030), "אין מהפך חינמי; שני ההיפוכים הם בכניסות השערים הנתונים" if he else
         "No free inverter: both inversions are the given gates' input bubbles", 29, he, "mm", GREEN)
    img.save(OUT/f"prep-112-and-with-zero-{lang}.png")
print("Wrote eight original bilingual PNG files.")
