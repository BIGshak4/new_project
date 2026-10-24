"""Clean bilingual convexity and byte-mask diagrams for PREP-108/111."""
from pathlib import Path

from draw_prep_016_064 import phrase, text
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN, RED = "#35234f", "#73558d", "#327568", "#a25d4b"
PALE, BG, LINE = "#eee7f3", "#fffdf8", "#d9cfe3"


def canvas(he, en, lang):
    image = Image.new("RGB", (2000, 1300), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1000, 75), he, en, lang, 49, bold=True, color=INK)
    return image, draw


def convex(lang):
    image, draw = canvas("קמירות ופשטות הן שתי שאלות שונות", "Convexity and simplicity are separate questions", lang)
    phrase(draw, (1000, 155), "הקודקודים מחוברים לפי הסדר הנתון", "Connect vertices in the given order", lang, 37)
    examples = [
        (340, [(0, 0), (4, 0), (4, 4), (0, 4)], GREEN, "קמור", "Convex"),
        (1000, [(0, 0), (4, 0), (4, 4), (2, 2), (0, 4)], RED, "קעור", "Concave"),
    ]
    for center, vertices, color, he, en in examples:
        phrase(draw, (center, 265), he, en, lang, 44, bold=True, color=color)
        points = [(center - 160 + 80 * x, 715 - 80 * y) for x, y in vertices]
        draw.polygon(points, fill="#e6eee9" if color == GREEN else "#f2e7e2")
        draw.line(points + points[:1], fill=color, width=7, joint="curve")
        for x, y in points:
            draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color)
    center = 1660
    outer = [(0, 3), (3, 1), (2, -3), (-2, -3), (-3, 1)]
    points = [(center + 55 * outer[i][0], 550 - 55 * outer[i][1]) for i in (0, 2, 4, 1, 3)]
    phrase(draw, (center, 265), "חותך את עצמו", "Self-intersecting", lang, 42, bold=True, color=RED)
    draw.line(points + points[:1], fill=RED, width=7, joint="curve")
    for x, y in points:
        draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=RED)
    phrase(draw, (340, 815), "פניות לאותו צד", "Same-side turns", lang, 34, color=GREEN)
    phrase(draw, (1000, 815), "פינה אחת פונה פנימה", "An inward corner", lang, 34, color=RED)
    phrase(draw, (1660, 815), "גם כאן סימני הפניות אחידים", "Turn signs are consistent here too", lang, 31, color=RED)
    draw.line((180, 900, 1820, 900), fill=LINE, width=3)
    phrase(draw, (1000, 970), "בדיקת פניות לינארית מניחה מראש גבול פשוט", "The linear turn test assumes a simple boundary", lang, 41, bold=True)
    phrase(draw, (1000, 1050), "בלי ההבטחה הזאת צריך לבדוק גם חיתוכי צלעות", "Without that promise, validate edge intersections too", lang, 38)
    phrase(draw, (1000, 1160), "קודקוד נוסף על צלע ישרה מותר רק בגרסה הלא ממשית", "An extra straight-edge vertex is allowed only in weak mode", lang, 37)
    image.save(OUT / f"prep-108-convex_polygon-{lang}.png")


def bitmap(lang):
    image, draw = canvas("קו אופקי שומר את כל הביטים שסביבו", "A horizontal line preserves every surrounding bit", lang)
    text(draw, (1000, 165), "width=19   height=2   pitch=4   x=5   y=1   length=10", 40, color=INK)
    phrase(draw, (1000, 240), "הפיקסל השמאלי בכל בית משתמש בביט הגבוה", "The leftmost pixel in each byte uses its highest bit", lang, 36)
    before, after = (0xAA,) * 4, (0xAF, 0xFE, 0xAA, 0xAA)
    for row, values, he, en in [(350, before, "לפני", "Before"), (640, after, "אחרי", "After")]:
        phrase(draw, (110, row + 45), he, en, lang, 35, bold=True)
        for byte, value in enumerate(values):
            start = 300 + 350 * byte
            for position in range(8):
                x = start + position * 36
                pixel = 8 * byte + position
                selected = row == 640 and 5 <= pixel < 15
                padding = pixel >= 19
                color = "#dcece7" if selected else ("#e7e4df" if padding else PALE)
                draw.rectangle((x, row, x + 36, row + 90), fill=color, outline=LINE, width=2)
                text(draw, (x + 18, row + 45), str((value >> (7 - position)) & 1), 34,
                     color=GREEN if selected else INK, bold=True)
            text(draw, (start + 144, row + 130), f"byte {byte}: 0x{value:02X}", 29, color=PURPLE)
            if row == 350:
                if byte < 3:
                    text(draw, (start + 144, row - 40), f"{8 * byte}..{min(8 * byte + 7, 18)}", 28)
                else:
                    phrase(draw, (start + 144, row - 40), "ריפוד", "padding", lang, 28)
    phrase(draw, (1000, 885), "רק עשרת הפיקסלים המבוקשים נדלקים; כל הריפוד נשמר", "Only the ten requested pixels are set; all padding survives", lang, 38, bold=True)
    draw.line((180, 950, 1820, 950), fill=LINE, width=3)
    phrase(draw, (1000, 1015), "בבית אחד לוקחים חיתוך של שתי מסכות הקצוות", "For one byte, intersect the two endpoint masks", lang, 38)
    text(draw, (1000, 1100), "x=2, length=3:     00111111  AND  11111000  =  00111000", 38, color=GREEN, bold=True)
    phrase(draw, (1000, 1195), "את המסכה הסופית מחברים לבית הקיים בלי למחוק ביטים אחרים", "OR the resulting mask into the existing byte without erasing other bits", lang, 35)
    image.save(OUT / f"prep-111-horizontal_bitmap_line-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        convex(language)
        bitmap(language)
