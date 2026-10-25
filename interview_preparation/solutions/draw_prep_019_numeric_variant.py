"""Clean bilingual invariant figure for the numeric source specialization."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
FONT = "C:/Windows/Fonts/arial.ttf"
INK = "#17213a"


def text(draw, xy, value, size=32, he=False, color=INK):
    draw.text(xy, value[::-1] if he else value, font=ImageFont.truetype(FONT, size),
              fill=color, anchor="mm")


for language in ("he", "en"):
    he = language == "he"
    image = Image.new("RGB", (2000, 1200), "white")
    d = ImageDraw.Draw(image)
    text(d, (1000, 70), "חלוקה לאזורים ידועים ולאזור שטרם סווג" if he else
         "Known regions and one shrinking unclassified interval", 46, he)
    text(d, (1000, 145), "פתרון מוצע — מעבר לינארי אינו איסור לקרוא שוב תא שהוחלף" if he else
         "Proposed solution — linear partitioning does not forbid revisiting a swapped position", 30, he)
    regions = [(100, 430, "0", "[0, low)", "#e8f2fc"),
               (430, 860, "1", "[low, mid)", "#e6f3eb"),
               (860, 1510, "טרם סווג" if he else "unclassified", "[mid, high + 1)", "#fff0c2"),
               (1510, 1900, "2", "[high + 1, n)", "#f0e9fa")]
    for left, right, label, interval, fill in regions:
        d.rectangle((left, 330, right, 540), fill=fill, outline="#345b9f", width=4)
        text(d, ((left+right)/2, 435), label, 42, he and label == "טרם סווג")
        text(d, ((left+right)/2, 595), interval, 30)
    text(d, (1000, 740), "[2,0,1]   →   [1,0,2]", 55)
    text(d, (1000, 825), "low=0, mid=0, high=2   →   low=0, mid=0, high=1", 31)
    text(d, (1000, 940), "לא מקדמים את אמצע הבדיקה אחרי העברת שתיים לקצה" if he else
         "After moving a two to the right, do not advance mid", 34, he, "#276858")
    text(d, (1000, 1020), "הערך שהגיע מהקצה עדיין אינו ידוע — בודקים אותו באותו מקום" if he else
         "The incoming value from high is still unknown: classify it at the same position", 30, he)
    text(d, (1000, 1080), "high - mid + 1", 32)
    text(d, (1000, 1140), "קטן באחד בכל איטרציה" if he else "decreases by one each iteration", 30, he)
    image.save(OUT / f"prep-019-numeric-partition-{language}.png")
print("Wrote two bilingual numeric partition figures.")
