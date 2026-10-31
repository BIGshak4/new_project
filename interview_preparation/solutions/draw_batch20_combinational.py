"""Original bilingual PNG schematics, never reproducing source screenshots."""
from pathlib import Path
from PIL import Image, ImageDraw
from draw_prep_016_064 import phrase, text, wire

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, BLUE, PURPLE, GREEN = "#23334b", "#2a62a0", "#7854a2", "#257b67"


def canvas(he, en, language, height=1300):
    image = Image.new("RGB", (2300, height), "white")
    draw = ImageDraw.Draw(image)
    phrase(draw, (1150, 90), he, en, language, 57, bold=True)
    return image, draw


def box(draw, xy, lines, color=BLUE):
    draw.rounded_rectangle(xy, 20, fill="#f5f8fd", outline=color, width=6)
    x0, y0, x1, y1 = xy
    for index, label in enumerate(lines, 1):
        text(draw, ((x0+x1)/2, y0+(y1-y0)*index/(len(lines)+1)), label, 42, bold=True, color=color)


def note(draw, y, he, en, language, size=40):
    phrase(draw, (1150, y), he, en, language, size)


def alert(language):
    image, draw = canvas("התראת תקלה משני חיישנים", "Two-sensor functional fault alert", language)
    box(draw, (900, 340, 1390, 760), ["OR", "E = H OR O"])
    for y, label in ((440, "H"), (650, "O")):
        text(draw, (380, y), label, 60, bold=True)
        wire(draw, [(450, y), (900, y)])
    wire(draw, [(1390, 550), (1900, 550)])
    text(draw, (1960, 550), "E", 60, bold=True)
    text(draw, (1150, 930), "H O | E     0 0 | 0     0 1 | 1     1 0 | 1     1 1 | 1", 42)
    note(draw, 1050, "אחד פירושו תקלה פעילה; שתיהן יחד עדיין מפיקות התראה", "One means an active fault; simultaneous faults still alert", language)
    note(draw, 1160, "תרגיל לוגי בלבד; אין כאן תכן בטיחות לרכב", "Boolean exercise only; this is not vehicle safety engineering", language)
    return image


def mux4(language):
    image, draw = canvas("מרבב מארבע כניסות בשלושה מרבבים", "Four inputs through three multiplexers", language, 1550)
    for y, zero, one in ((300, "Q3", "Q2"), (770, "Q1", "Q0")):
        box(draw, (650, y, 1050, y+340), ["MUX 2:1", "S = S0"])
        for yy, label, port in ((y+95, zero, "D0"), (y+240, one, "D1")):
            text(draw, (260, yy), label, 52, bold=True)
            wire(draw, [(330, yy), (650, yy)])
            text(draw, (555, yy-53), port, 36)
    box(draw, (1510, 530, 1920, 900), ["MUX 2:1", "S = S1"])
    wire(draw, [(1050, 470), (1260, 470), (1260, 625), (1510, 625)])
    wire(draw, [(1050, 940), (1320, 940), (1320, 805), (1510, 805)])
    text(draw, (1410, 575), "D0", 36)
    text(draw, (1410, 755), "D1", 36)
    wire(draw, [(1920, 715), (2150, 715)])
    text(draw, (2140, 635), "Out", 48, bold=True)
    text(draw, (1150, 1230), "S1S0: 00 -> Q3    01 -> Q2    10 -> Q1    11 -> Q0", 45, bold=True)
    note(draw, 1350, "סדר רגיל דורש החלפת חיווט הכניסות בלבד", "Standard ordering requires only rewiring the four data inputs", language)
    text(draw, (1150, 1450), "Standard: upper D0=Q0, D1=Q1; lower D0=Q2, D1=Q3", 40)
    return image


def adder(language):
    image, draw = canvas("חיבור שתי סיביות לארבע סיביות", "Adding two bits to four bits", language, 1550)
    for bit in range(4):
        x = 220 + 540*bit
        box(draw, (x, 420, x+350, 900), [f"FA{bit}", "1 ns"])
        a = f"A{bit}" if bit < 2 else "0"
        text(draw, (x+80, 265), a, 48, bold=True)
        text(draw, (x+270, 265), f"B{bit}", 48, bold=True)
        wire(draw, [(x+80, 310), (x+80, 420)])
        wire(draw, [(x+270, 310), (x+270, 420)])
        wire(draw, [(x+175, 900), (x+175, 1080)])
        text(draw, (x+175, 1140), f"S{bit}", 49, bold=True)
        text(draw, (x+175, 1220), f"t <= {bit+1} ns", 37)
        if bit == 0:
            wire(draw, [(55, 650), (x, 650)])
            text(draw, (75, 580), "C0=0", 37)
        else:
            wire(draw, [(x-190, 650), (x, 650)])
            text(draw, (x-100, 580), f"C{bit}", 37)
    wire(draw, [(2190, 650), (2260, 650), (2260, 1080)])
    text(draw, (2190, 1140), "S4=C4", 37, bold=True)
    note(draw, 1360, "הסכום המרבי שמונה עשרה ולכן דרושות חמש סיביות", "Maximum sum is eighteen, so five result bits are necessary", language)
    text(draw, (1150, 1460), "A in [0,3], B in [0,15]     |     ripple: 4 FA, 4 ns", 43, bold=True)
    return image


def gate_bundle(language):
    image, draw = canvas("ארבעה שערים בעזרת מרבבים", "Four Boolean gates with multiplexers", language, 1500)
    text(draw, (1150, 220), "MUX(S,D0,D1): S=0 -> D0; S=1 -> D1", 46)
    for index, (name, d0, d1) in enumerate((("AND", "0", "B"), ("OR", "B", "1"), ("XOR", "B", "nB"), ("NAND", "1", "nB"))):
        x = 120 + (index % 2)*1150
        y = 370 + (index // 2)*480
        box(draw, (x+310, y, x+720, y+300), ["MUX", "S = A"])
        for yy, label, port in ((y+70, d0, "D0"), (y+230, d1, "D1")):
            text(draw, (x+120, yy), label, 47, bold=True)
            wire(draw, [(x+185, yy), (x+310, yy)])
            text(draw, (x+245, yy-45), port, 31)
        wire(draw, [(x+720, y+150), (x+940, y+150)])
        text(draw, (x+925, y+75), name, 47, bold=True)
    text(draw, (1150, 1310), "nB = MUX(B,1,0)       |       4 function MUX + 1 shared inverter MUX", 41)
    note(draw, 1425, "אם המשלים זמין בחינם לא סופרים את מרבב ההיפוך", "If the complement is already available, its inverter MUX is not counted", language)
    return image


def storage(language):
    image, draw = canvas("משוב ומבנה אב עבד באמצעות מרבבים", "MUX feedback and master-slave storage", language, 1500)
    for x, label, select, incoming, outgoing in ((420, "Master", "nCLK", "D", "M"), (1390, "Slave", "CLK", "M", "Q")):
        box(draw, (x, 440, x+440, 880), [label, "MUX 2:1", f"S={select}"])
        wire(draw, [(x-210, 540), (x, 540)])
        text(draw, (x-155, 465), incoming, 45, bold=True)
        text(draw, (x+40, 495), "D1", 33)
        wire(draw, [(x+440, 650), (x+670, 650)])
        text(draw, (x+630, 575), outgoing, 48, bold=True)
        # Explicit output-to-D0 feedback, with a connection dot at the takeoff.
        draw.ellipse((x+528,638,x+552,662),fill=GREEN)
        wire(draw, [(x+540, 650), (x+540, 1000), (x-90, 1000), (x-90, 770), (x, 770)], GREEN)
        text(draw, (x+40, 820), "D0", 33, color=GREEN)
    # Explicitly join the master output to the slave's new-data port.
    wire(draw, [(1090, 650), (1135, 650), (1135, 540), (1180, 540)], BLUE)
    text(draw, (1150, 250), "nCLK = MUX(CLK,1,0)       D -> Master -> M -> Slave -> Q", 45)
    note(draw, 1140, "האב שקוף בשעון נמוך; העבד שקוף בשעון גבוה", "Master is transparent at low clock; slave at high clock", language)
    note(draw, 1260, "המשוב שומר ערך; ללא משוב אין אחסון", "Feedback holds state; an acyclic MUX network has no storage", language)
    note(draw, 1380, "מודל אידאלי בלבד; היפוך שעון אינו מבטיח העדר חפיפה פיזית", "Ideal model only; clock inversion does not guarantee physical nonoverlap", language, 37)
    return image


def lsb(language):
    image, draw = canvas("בידוד האחד הקרוב לסיבית הנמוכה", "Isolate the least-significant one", language, 1500)
    box(draw, (220, 450, 850, 830), ["OR tree", "P_i = OR(x[i-1:0])"])
    wire(draw, [(50, 635), (220, 635)])
    text(draw, (230, 370), "x0 ... x(i-1)", 44)
    box(draw, (1100, 500, 1390, 770), ["NOT"])
    wire(draw, [(850, 635), (1100, 635)])
    box(draw, (1650, 500, 1970, 900), ["AND", "y_i"])
    wire(draw, [(1390, 635), (1650, 635)])
    wire(draw, [(1810, 350), (1810, 500)])
    text(draw, (1810, 280), "x_i", 52, bold=True)
    wire(draw, [(1970, 700), (2200, 700)])
    text(draw, (1150, 1050), "y0 = x0      |      y_i = x_i AND NOT P_i", 48, bold=True)
    text(draw, (1150, 1180), "20 bits: serial = 18 OR + NOT + AND = 20 ns", 45)
    text(draw, (1150, 1280), "Balanced: ceil(log2 19) + 1 + 1 = 7 ns <= 10 ns", 45)
    note(draw, 1410, "שערי צירוף בעלי שתי כניסות; היפוך יחיד; חוטים ופיצול חופשיים", "Two-input AND/OR, unary NOT; zero wire/fanout delay", language, 38)
    return image


def compare(language):
    image, draw = canvas("השוואה קשיחה מאזור נמוך לגבוה", "Strict comparison from low bits to high bits", language, 1500)
    for index, x in enumerate((260, 940, 1620)):
        bit = ("0", "1", "N-1")[index]
        box(draw, (x, 430, x+420, 930), [f"bit {bit}", "XOR -> S", "MUX", f"D1=A[{bit}]"])
        text(draw, (x+210, 300), f"A[{bit}], B[{bit}]", 43, bold=True)
        wire(draw, [(x+210, 350), (x+210, 430)])
        wire(draw, [(x-150, 680), (x, 680)])
        text(draw, (x-100, 600), "0" if index == 0 else "g_prev", 36)
        if index == 2:
            wire(draw, [(x+420, 680), (2220, 680)])
            text(draw, (2130, 600), "A>B", 43, bold=True)
    wire(draw, [(680, 680), (940, 680)])
    wire(draw, [(1360, 680), (1620, 680)])
    draw.rectangle((1450, 640, 1530, 720), fill="white")
    text(draw, (1490, 680), "...", 60, bold=True)
    text(draw, (1150, 1090), "g[-1]=0; g[i]=MUX(A_i XOR B_i, g[i-1], A_i)", 43, bold=True)
    text(draw, (1150, 1210), "Equal bit -> keep lower result; differing bit -> higher bit decides", 39)
    note(draw, 1350, "השוואת שני ביטים", "One-bit comparison", language, 38)
    text(draw, (1150, 1440), "X=A AND NOT B; Y=NOT A AND B; equal -> X=Y=0", 42)
    return image


if __name__ == "__main__":
    for ident, factory in ((213, alert), (214, mux4), (215, adder), (70, gate_bundle),
                           (83, storage), (107, lsb), (110, compare)):
        for language in ("he", "en"):
            path = OUT / f"prep-{ident:03d}-combinational-batch20-{language}.png"
            factory(language).save(path)
            print(path.name)
