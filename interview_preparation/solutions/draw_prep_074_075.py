"""Authored deterministic localized circuit, timing and memory diagrams."""
from pathlib import Path

from draw_prep_016_064 import BLUE, GREEN, ORANGE, PURPLE, box, phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"


def canvas(he, en, lang, width=2800, height=1550):
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    phrase(draw, (width // 2, 100), he, en, lang, 62, bold=True)
    return image, draw


def label(draw, xy, value, size=46, color=BLUE):
    text(draw, xy, value, size, color=color, bold=True)


def feedback(lang):
    im, d = canvas("דלגלג עם משוב דרך שער איקסור", "D flip-flop with XOR feedback", lang)
    phrase(d, (1400, 205), "הכניסה נדגמת בחזית עולה בלבד", "Data is sampled only at rising clock edges", lang, 42)
    box(d, (850, 500, 1300, 900), BLUE)
    label(d, (1075, 700), "XOR", 62)
    box(d, (1690, 420, 2320, 1010), GREEN)
    label(d, (2005, 530), "D FF", 64, GREEN)
    label(d, (1755, 705), "D", 48, GREEN)
    label(d, (2245, 705), "Q", 48, GREEN)
    wire(d, [(230, 610), (850, 610)], BLUE)
    label(d, (290, 530), "A", 60)
    wire(d, [(1300, 705), (1690, 705)], BLUE)
    wire(d, [(2320, 705), (2640, 705)], GREEN)
    label(d, (2580, 625), "Q", 60, GREEN)
    d.ellipse((2439, 694, 2461, 716), fill=GREEN)
    wire(d, [(2450, 705), (2450, 1190), (565, 1190), (565, 810), (850, 810)], PURPLE)
    phrase(d, (1410, 1270), "משוב מאותו מוצא", "Feedback from the same Q output", lang, 45, color=PURPLE)
    wire(d, [(2005, 1340), (2005, 1010)], ORANGE)
    d.line([(1968, 1010), (2005, 966), (2042, 1010)], fill=ORANGE, width=6)
    label(d, (2005, 1410), "clk", 50, ORANGE)
    im.save(OUT / f"prep-074-feedback-prompt-{lang}.png")


def signal(d, y, values, boundaries, color, x0=540, end=2680):
    high, low = y - 65, y + 65
    points = [(x0, high if values[0] else low)]
    for x, previous, current in zip(boundaries, values, values[1:]):
        points.extend([(x, high if previous else low), (x, high if current else low)])
    points.append((end, high if values[-1] else low))
    d.line(points, fill=color, width=8)


def waveform(lang):
    im, d = canvas("דוגמת תזמון במצב קבוע", "Timing example for constant A", lang, 2800, 1700)
    label(d, (860, 205), "Q(initial)=0    T=10 ns    tCQ=1 ns", 39)
    phrase(d, (2170, 205), "אות השער יציב לפני כל חזית", "XOR settled before each edge", lang, 35)
    edges = [650 + i * 250 for i in range(8)]
    for i, x in enumerate(edges):
        d.line((x, 290, x, 1415), fill="#dde1ea", width=3)
        label(d, (x, 270), f"{10*(i+1)}", 32, PURPLE)
    clock_edges = [x for pair in ((x, x + 125) for x in edges) for x in pair]
    signal(d, 470, [0] + [v for _ in edges for v in (1, 0)], clock_edges, PURPLE)
    label(d, (240, 470), "clk", 46, PURPLE)
    signal(d, 790, [0] * 9, edges, GREEN)
    label(d, (265, 790), "Q, A=0", 44, GREEN)
    signal(d, 1130, [0] + [1 - i % 2 for i in range(8)], [x + 25 for x in edges], BLUE)
    label(d, (265, 1130), "Q, A=1", 44, BLUE)
    wire(d, [(edges[0], 1340), (edges[0] + 25, 1340)], ORANGE, width=5)
    phrase(d, (1100, 1350), "שינוי ביציאה לאחר חזית ועוד השהיה", "Q transition at edge + tCQ", lang, 37, color=ORANGE)
    phrase(d, (1400, 1490), "היציאה אינה מתהפכת שוב לפני החזית העולה הבאה", "Q cannot toggle again before the next rising edge", lang, 43)
    phrase(d, (1400, 1585), "דוגמה אידאלית אינה סימולציית תזמון פיזי", "This idealized example is not physical timing simulation", lang, 40)
    im.save(OUT / f"prep-074-waveform-{lang}.png")


def primitive(lang):
    im, d = canvas("רכיב הזיכרון הנתון", "The supplied single-port memory primitive", lang)
    box(d, (1100, 380, 2100, 1160), BLUE)
    label(d, (1600, 480), "SINGLE-PORT RAM", 55)
    label(d, (1600, 575), "N words x W bits", 46)
    for y, name in [(700, "read_en"), (825, "write_en"), (950, "address"), (1075, "write_data")]:
        wire(d, [(300, y), (1100, y)], BLUE)
        label(d, (650, y - 60), name, 42)
    wire(d, [(2100, 830), (2650, 830)], GREEN)
    label(d, (2390, 755), "read_data", 46, GREEN)
    wire(d, [(1600, 1340), (1600, 1160)], PURPLE)
    label(d, (1600, 1390), "clk", 46, PURPLE)
    phrase(d, (1400, 1470), "בכל חזית מותרת לכל היותר פעולת קריאה או כתיבה אחת", "At most one read OR one write is allowed at each edge", lang, 42)
    im.save(OUT / f"prep-075-primitive-prompt-{lang}.png")


def banking(lang):
    im, d = canvas("בנק נפרד לכל כתובת לוגית", "A separate bank for each logical address", lang, 3200, 2250)
    phrase(d, (1600, 210), "דוגמה עם שלוש מילים לוגיות ורק תא אפס בשימוש בכל רכיב", "Example: three logical words; only physical word zero is used in each macro", lang, 42)
    box(d, (120, 540, 820, 1450), PURPLE)
    label(d, (470, 640), "DECODE", 55, PURPLE)
    for y, name in [(790, "rd_en, rd_addr"), (930, "wr_en, wr_addr"), (1070, "write_data"), (1210, "clk")]:
        label(d, (470, y), name, 38, PURPLE)
    for i in range(3):
        top = 420 + i * 400
        box(d, (1070, top, 1880, top + 300), BLUE)
        label(d, (1475, top + 65), f"BANK {i} : single-port", 44)
        label(d, (1475, top + 150), f"logical M[{i}] = physical[0]", 35)
        label(d, (1475, top + 230), f"RE{i} / WE{i} / write_data", 34)
        wire(d, [(820, top + 150), (1070, top + 150)], PURPLE)
        wire(d, [(1880, top + 150), (2180, top + 150)], BLUE)
        label(d, (2010, top + 80), f"R{i}", 40)
    box(d, (2180, 420, 2650, 1520), GREEN)
    label(d, (2415, 850), "N:1 MUX", 51, GREEN)
    label(d, (2415, 955), "rd_addr_q", 37, GREEN)
    wire(d, [(2650, 920), (2830, 920)], GREEN)
    box(d, (2830, 650, 3120, 1210), ORANGE)
    label(d, (2975, 760), "BYPASS", 35, ORANGE)
    label(d, (2975, 865), "MUX", 41, ORANGE)
    wire(d, [(2975, 1210), (2975, 1370)], ORANGE)
    label(d, (2975, 1425), "read_data", 33, ORANGE)
    box(d, (160, 1670, 3060, 2110), PURPLE)
    label(d, (1610, 1740), "collision = rd_en AND wr_en AND (rd_addr == wr_addr)", 37, PURPLE)
    label(d, (1610, 1830), "WEi = wr_en AND (wr_addr == i)", 38, PURPLE)
    label(d, (1610, 1920), "REi = rd_en AND (rd_addr == i) AND NOT collision", 37, PURPLE)
    label(d, (1610, 2010), "Registers: rd_addr_q, collision_q, bypass_data_q, rd_valid", 37, PURPLE)
    wire(d, [(2415, 1670), (2415, 1520)], PURPLE)
    wire(d, [(2975, 1670), (2975, 1550), (2760, 1550), (2760, 1110), (2830, 1110)], ORANGE)
    phrase(d, (2790, 1600), "מעקף רשום", "registered bypass", lang, 32, color=ORANGE)
    phrase(d, (1600, 2190), "בכתובות זהות כותבים לרכיב ומחזירים את הנתון החדש דרך מעקף", "Same address: write the bank and return the new data through bypass", lang, 41)
    im.save(OUT / f"prep-075-word-banks-{lang}.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for language in ("he", "en"):
        feedback(language)
        waveform(language)
        primitive(language)
        banking(language)
