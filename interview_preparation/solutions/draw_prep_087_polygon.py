"""Author clean bilingual point/polygon learning figures for PREP-087."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, MUTED = "#35234f", "#73558d", "#766783"
POLY = [(0, 0), (12, 0), (12, 7), (8, 7), (8, 3), (4, 3), (4, 7), (0, 7)]


def diagram(language, solution=False):
    im = Image.new("RGB", (1600, 1400 if solution else 1030), "#fffdf8")
    draw = ImageDraw.Draw(im)

    def text(point, value, size=38, he=False, color=INK, bold=False):
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf", size)
        draw.text(point, value[::-1] if he else value, font=font, fill=color, anchor="mm")

    def localized(point, he, en, size=38, color=INK, bold=False):
        text(point, he if language == "he" else en, size, language == "he", color, bold)

    localized((800, 60), "נקודה בתוך מצולע או מחוצה לו", "Point inside or outside a polygon", 51, bold=True)
    localized((800, 125), "מצולע פשוט יכול להיות קעור", "A simple polygon can be concave", 36, MUTED)

    def shape(origin, scale, query, crossings=False, labels=False):
        def xy(p):
            return origin[0] + scale * p[0], origin[1] - scale * p[1]
        pts = [xy(p) for p in POLY]
        draw.polygon(pts, fill="#eee8f3")
        draw.line(pts + pts[:1], fill=INK, width=6, joint="curve")
        for i, (x, y) in enumerate(pts):
            draw.ellipse((x - 7, y - 7, x + 7, y + 7), fill=INK)
            if labels:
                offsets = [(-26, 30), (28, 30), (30, -27), (-28, -27), (28, 29), (-28, 29), (28, -27), (-27, -27)]
                dx, dy = offsets[i]
                text((x + dx, y + dy), str(i + 1), 32, color=MUTED)
        px, py = xy(query)
        if crossings:
            for x in range(int(px + 15), 1480, 22):
                draw.line((x, py, x + 11, py), fill=PURPLE, width=4)
            draw.polygon([(1490, py), (1468, py - 11), (1468, py + 11)], fill=PURPLE)
            for x_value in ([4, 8, 12] if query[0] == 2 else [8, 12]):
                x, y = xy((x_value, query[1]))
                draw.ellipse((x - 11, y - 11, x + 11, y + 11), fill="#fffdf8", outline=PURPLE, width=5)
        draw.ellipse((px - 12, py - 12, px + 12, py + 12), fill=PURPLE, outline="#fffdf8", width=3)
        text((px - 20, py - 35), "P", 39, color=PURPLE, bold=True)

    if solution:
        shape((300, 655), 65, (2, 5), crossings=True)
        localized((800, 705), "שלושה חיתוכים: מספר אי זוגי — בפנים", "3 crossings: odd means inside", 40, PURPLE, bold=True)
        shape((300, 1230), 65, (6, 5), crossings=True)
        localized((800, 1280), "שני חיתוכים: מספר זוגי — בחוץ", "2 crossings: even means outside", 40, PURPLE, bold=True)
        localized((800, 1350), "החיתוכים המסומנים אינם קודקודים", "Marked crossings are not vertices", 31, MUTED)
    else:
        shape((250, 840), 85, (2, 5), labels=True)
        localized((800, 935), "הקודקודים מחוברים לפי הסדר והצלע האחרונה סוגרת את המצולע", "Connect ordered vertices; the last edge closes the polygon", 34, MUTED)
        localized((800, 987), "שרטוט דוגמה בלבד — אין הנחת קמירות", "Example only; convexity is not assumed", 33, MUTED)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"prep-087-{'ray-parity' if solution else 'polygon'}-{language}.png"
    im.save(path)
    print(path.name)


if __name__ == "__main__":
    for lang in ("he", "en"):
        diagram(lang)
        diagram(lang, solution=True)
