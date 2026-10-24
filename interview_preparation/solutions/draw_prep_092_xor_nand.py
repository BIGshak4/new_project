"""Reproducible bilingual four-NAND schematic; no pasted source screenshot."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
BG, CARD, PURPLE, INK, GREEN = '#f8f4e9', '#fffdf8', '#5d4383', '#302344', '#33786d'


def label(d, xy, value, size=42, color=INK):
    text(d, xy, value, size, color=color, bold=True)


def gate(d, x, y, name):
    d.rectangle((x, y - 90, x + 90, y + 90), fill=CARD)
    d.pieslice((x, y - 90, x + 180, y + 90), -90, 90, fill=CARD)
    d.line((x, y - 90, x + 90, y - 90), fill=PURPLE, width=6)
    d.line((x, y - 90, x, y + 90), fill=PURPLE, width=6)
    d.line((x, y + 90, x + 90, y + 90), fill=PURPLE, width=6)
    d.arc((x, y - 90, x + 180, y + 90), -90, 90, fill=PURPLE, width=6)
    d.ellipse((x + 180, y - 14, x + 208, y + 14), fill=CARD, outline=PURPLE, width=5)
    label(d, (x + 78, y), 'NAND', 31)
    label(d, (x + 90, y - 140), name, 36, PURPLE)


def dot(d, x, y):
    d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=PURPLE)


def draw(lang):
    im = Image.new('RGB', (2200, 1500), BG)
    d = ImageDraw.Draw(im)
    phrase(d, (1100, 85), 'מימוש פעולת או־בלעדי', 'XOR from four NAND gates', lang, 61, bold=True)
    phrase(d, (1100, 170), 'ארבעה שערים עם שתי כניסות; מותר לפצל חוט', 'Two inputs per gate; wire fanout is allowed', lang, 39)
    # Independent input buses stay outside the shared T route.
    wire(d, [(130, 270), (900, 270), (900, 410), (1000, 410)], GREEN)
    wire(d, [(240, 270), (240, 610), (450, 610)], GREEN)
    label(d, (130, 220), 'A', 52, GREEN)
    d.ellipse((231, 261, 249, 279), fill=GREEN)
    wire(d, [(130, 1010), (900, 1010), (900, 890), (1000, 890)], GREEN)
    wire(d, [(330, 1010), (330, 690), (450, 690)], GREEN)
    label(d, (130, 1060), 'B', 52, GREEN)
    d.ellipse((321, 1001, 339, 1019), fill=GREEN)
    # Shared NAND output T drives one input on each middle gate.
    wire(d, [(658, 650), (810, 650)], PURPLE)
    wire(d, [(810, 490), (810, 810)], PURPLE)
    wire(d, [(810, 490), (1000, 490)], PURPLE)
    wire(d, [(810, 810), (1000, 810)], PURPLE)
    dot(d, 810, 650)
    label(d, (742, 605), 'T', 45, PURPLE)
    wire(d, [(1208, 450), (1430, 450), (1430, 610), (1550, 610)], PURPLE)
    wire(d, [(1208, 850), (1430, 850), (1430, 690), (1550, 690)], PURPLE)
    label(d, (1300, 395), 'P', 45, PURPLE)
    label(d, (1300, 905), 'Q', 45, PURPLE)
    wire(d, [(1758, 650), (2050, 650)], GREEN)
    label(d, (1950, 585), 'Y', 52, GREEN)
    for x, y, name in ((450, 650, 'G1'), (1000, 450, 'G2'), (1000, 850, 'G3'), (1550, 650, 'G4')):
        gate(d, x, y, name)
    label(d, (1100, 1165), 'T = NAND(A, B)', 43)
    label(d, (1100, 1240), 'P = NAND(A, T)     Q = NAND(B, T)', 43)
    label(d, (1100, 1315), 'Y = NAND(P, Q) = A XOR B', 46, PURPLE)
    phrase(d, (1100, 1415), 'כאשר הכניסות שונות המוצא אחד', 'The output is one exactly when the inputs differ', lang, 40)
    im.save(OUT / f'prep-092-xor-four-nand-{lang}.png')


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for language in ('he', 'en'):
        draw(language)
