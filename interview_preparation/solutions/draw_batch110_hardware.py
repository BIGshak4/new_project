"""Deterministic bilingual engineering diagrams for the owned batch110 content."""

from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE, PALE, GREEN, GRAY = (
    "#fffdf8", "#302344", "#624883", "#eee7f5", "#30766a", "#ddd6e4"
)


def canvas(he, en, language, height=1500):
    image = Image.new("RGB", (2400, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 95), he, en, language, 54, bold=True, color=INK)
    return image, draw


def label(draw, xy, value, size=40):
    text(draw, xy, value, size, bold=True, color=INK)


def box(draw, rect, lines):
    draw.rounded_rectangle(rect, 24, fill=PALE, outline=PURPLE, width=6)
    x1, y1, x2, y2 = rect
    for i, line in enumerate(lines, 1):
        label(draw, ((x1+x2)/2, y1+i*(y2-y1)/(len(lines)+1)), line)


def table(draw, rows, x, y, widths, height=82, size=34, language="en"):
    for r, row in enumerate(rows):
        left = x
        for value, width in zip(row, widths, strict=True):
            draw.rectangle((left, y+r*height, left+width, y+(r+1)*height),
                           fill=PALE if r == 0 else BG, outline=GRAY, width=3)
            if isinstance(value, tuple):
                phrase(draw, (left+width/2, y+(r+.5)*height), *value, language,
                       size, bold=True, color=INK)
            else:
                label(draw, (left+width/2, y+(r+.5)*height), str(value), size)
            left += width


def logarithm(language):
    image, draw = canvas("סופרים הזזות עד שנשאר אחד", "Count shifts until one remains", language, 1720)
    box(draw, (350, 290, 1050, 620), ["work[15:0]", "LD(x) / SHR"])
    box(draw, (1380, 290, 2060, 620), ["count[3:0]", "0 / count+1"])
    wire(draw, [(90, 440), (350, 440)], PURPLE)
    label(draw, (215, 355), "x[15:0]", 32)
    wire(draw, [(1050, 440), (1380, 440)], GREEN)
    label(draw, (1215, 330), "work > 1", 34)
    label(draw, (1215, 540), "SHR, EN_count", 31)
    box(draw, (1380, 755, 2060, 970), ["result <= count", "done=1, valid=1"])
    wire(draw, [(1720, 620), (1720, 755)], GREEN)
    label(draw, (1970, 690), "work = 1", 32)
    phrase(draw, (670, 810), "אפס: סיום מידי ללא תוצאה תקפה", "Zero: immediate completion, invalid", language, 34)
    phrase(draw, (670, 900), "הקלט נלכד רק בהתחלה כשהרכיב פנוי", "Input captured only on an idle start", language, 34)
    rows = [[("חזית אחרי הקליטה", "edge after capture"), "work", "count", "busy", "done / result"],
            ["0", "36", "0", "1", "0 / --"], ["1", "18", "1", "1", "0 / --"],
            ["2", "9", "2", "1", "0 / --"], ["3", "4", "3", "1", "0 / --"],
            ["4", "2", "4", "1", "0 / --"], ["5", "1", "5", "1", "0 / --"],
            ["6", "1", "5", "0", "1 / 5"]]
    table(draw, rows, 140, 1050, [650, 380, 380, 300, 400], 68, 32, language)
    phrase(draw, (1200, 1650), "חזית הסיום הנפרדת כלולה בהשהיה", "The separate completion edge is included in latency", language, 38)
    return image


def one_shot(language):
    image, draw = canvas("אותה כניסה, תגובה התלויה בהיסטוריה", "The response depends on trigger history", language, 1440)
    traces = [([0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], "Vin"),
              ([0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 0], "Vout_NR"),
              ([0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0], "Vout_R")]
    left, step = 500, 105
    for row, (values, name) in enumerate(traces):
        base = 400+row*320
        label(draw, (460, base-190), name, 32)
        draw.line((left, base+30, 2240, base+30), fill=GRAY, width=3)
        points = [(left, base-110*values[0])]
        for t, value in enumerate(values):
            xx = left+t*step
            if t:
                points.extend([(xx, base-110*values[t-1]), (xx, base-110*value)])
            points.append((xx+step, base-110*value))
        draw.line(points, fill=PURPLE if row == 0 else GREEN, width=7)
        for t in (2, 4, 7, 9, 10, 15):
            xx = left+t*step
            draw.line((xx, base-155, xx, base+20), fill=GRAY, width=2)
            label(draw, (xx, base+70), str(t), 28)
    label(draw, (1190, 1240), "tau = 5; t_trigger = {2, 4, 10}", 43)
    phrase(draw, (1200, 1350), "טריגר בזמן הפולס: מתעלמים או מאריכים לפי סוג הרכיב", "A trigger during the pulse is ignored or extends it, according to type", language, 37)
    return image


def link(language):
    image, draw = canvas("יותר סמלים בעזרת זמן ומסגור מוסכם", "More symbols using time and agreed framing", language, 1530)
    box(draw, (180, 320, 760, 720), ["TX", "s[4:0] : 0..17"])
    box(draw, (1640, 320, 2220, 720), ["RX", "s = first+16*second"])
    for i in range(4):
        y = 390+80*i
        wire(draw, [(760, y), (1640, y)], PURPLE)
        label(draw, (1200, y-30), f"DATA[{3-i}]", 31)
    phrase(draw, (1200, 840), "כל מסגרת כוללת שתי דגימות של אותם ארבעה קווים", "Each frame samples the same four wires twice", language, 40)
    table(draw, [["s", ("קוד בינארי", "binary code"), ("דגימה ראשונה", "first sample"), ("דגימה שנייה", "second sample")],
                 ["0", "00000", "0000", "0000"], ["15", "01111", "1111", "0000"],
                 ["16", "10000", "0000", "0001"], ["17", "10001", "0001", "0001"]],
          200, 930, [350, 550, 550, 550], 82, 37, language)
    label(draw, (1200, 1400), "16^1 = 16 < 18; 16^2 = 256 >= 18", 43)
    phrase(draw, (1200, 1480), "שעון ומופע מסגרת הם הנחה מפורשת; אין קו נתונים חמישי", "Shared timing and frame phase are explicit; no fifth DATA wire", language, 34)
    return image


def bottles(language):
    image, draw = canvas("עשר תערובות במקביל ומסכת תוצאות", "Ten parallel pools and an outcome mask", language, 1460)
    label(draw, (1200, 240), "j - 1 = b9 ... b1 b0", 44)
    table(draw, [["j", ("תווית בעשר סיביות", "label (10 bits)"), ("בודקים המקבלים דגימה", "testers receiving its sample")],
                 ["1", "0000000000", "--"], ["2", "0000000001", "T0"],
                 ["6", "0000000101", "T0, T2"], ["1000", "1111100111", "T0,T1,T2,T5,T6,T7,T8,T9"]],
          180, 350, [320, 700, 1020], 100, 35, language)
    y = 1050
    wire(draw, [(220, y), (2200, y)], PURPLE)
    for xx, value in [(300, "0"), (1500, "60"), (2100, "90 min")]:
        draw.line((xx, y-30, xx, y+30), fill=GREEN, width=7)
        label(draw, (xx, y+85), value)
    phrase(draw, (420, 920), "כל הבדיקות מתחילות יחד", "All pools sampled together", language, 34)
    phrase(draw, (1460, 920), "פענוח התוצאות עד כאן", "Decode by this point", language, 34)
    phrase(draw, (1200, 1250), "תגובה בתוך לכל היותר שעה; לא נדרש זמן מדויק", "A hard one-hour upper bound; exact delay is unnecessary", language, 39)
    label(draw, (1200, 1360), "2^9 = 512 < 1000 <= 1024 = 2^10", 45)
    return image


if __name__ == "__main__":
    for number, stem, draw in [(191, "shift-log2", logarithm), (193, "one-shot-waveforms", one_shot),
                               (197, "four-wire-frames", link), (73, "ninety-minute-code", bottles)]:
        for language in ("he", "en"):
            draw(language).save(OUT/f"prep-{number:03d}-{stem}-batch110-{language}.png")
