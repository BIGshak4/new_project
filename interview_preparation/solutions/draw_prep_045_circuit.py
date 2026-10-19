"""Rebuild the approved bilingual NOR/enable/reset schematic as PNG and SVG."""

import html
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ENGLISH = {
    "שמירת הזוכה — שער לוגי ואיפוס מפורש": "First-finisher storage: explicit NOR and reset",
    "קו הנתונים מכיל שני ביטים. אות האפשור מכיל ביט אחד.": "Data has two bits. The enable signal has one bit.",
    "בחירת מסלול": "Select lane",
    "מקודד עדיפות": "Priority encoder",
    "קוד המסלול שנבחר": "Current candidate code",
    "שמירת הזוכה": "Store winner",
    "אוגר בן שני ביטים": "Two-bit register",
    "הזוכה השמור": "Stored winner",
    "פיצול לביטים": "Split into bits",
    "ביט אחד": "One bit",
    "טבלת האמת של האפשור": "Enable truth table",
    "האיפוס גובר על האפשור, גם כשהוא אפס. העדכון בחזית שעון עולה.": "Reset overrides enable, including EN=0. Update on a rising clock edge.",
}


def render_circuit(language):
    OUT = Path(__file__).resolve().parents[1] / "diagrams"
    S = 2
    W, H = 2050, 1280
    INK = "#24334b"
    BLUE = "#2563b8"
    GREEN = "#16806b"
    AMBER = "#be6b13"
    GRAY = "#708095"
    RED = "#b64b50"
    image = Image.new("RGB", (W * S, H * S), "#ffffff")
    d = ImageDraw.Draw(image)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>'
    ]

    def text(x, y, value, size=32, color=INK, he=False, bold=False):
        if he and language == "en":
            value = ENGLISH[value]
            he = False
        font = ImageFont.truetype(
            "C:/Windows/Fonts/" + ("arialbd.ttf" if bold else "arial.ttf"), size * S
        )
        d.text(
            (x * S, y * S),
            value[::-1] if he else value,
            font=font,
            fill=color,
            anchor="mm",
        )
        direction = ' direction="rtl"' if he else ""
        svg.append(
            f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{color}" text-anchor="middle" dominant-baseline="central" font-weight="{700 if bold else 400}"{direction}>{html.escape(value)}</text>'
        )

    def box(x, y, w, h, color, fill):
        d.rounded_rectangle(
            (x * S, y * S, (x + w) * S, (y + h) * S),
            radius=20 * S,
            fill=fill,
            outline=color,
            width=3 * S,
        )
        svg.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="{fill}" stroke="{color}" stroke-width="3"/>'
        )

    def wire(points, color, width=5, arrow=True):
        d.line(
            [(x * S, y * S) for x, y in points],
            fill=color,
            width=width * S,
            joint="curve",
        )
        svg.append(
            f'<polyline points="{" ".join(f"{x},{y}" for x, y in points)}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round"/>'
        )
        if arrow:
            (px, py), (x, y) = points[-2:]
            angle = math.atan2(y - py, x - px)
            tri = [(x, y)] + [
                (x - 19 * math.cos(angle + a), y - 19 * math.sin(angle + a))
                for a in (-0.43, 0.43)
            ]
            d.polygon([(a * S, b * S) for a, b in tri], fill=color)
            svg.append(
                f'<polygon points="{" ".join(f"{a},{b}" for a, b in tri)}" fill="{color}"/>'
            )

    text(1025, 60, "שמירת הזוכה — שער לוגי ואיפוס מפורש", 46, he=True, bold=True)
    text(
        1025,
        120,
        "קו הנתונים מכיל שני ביטים. אות האפשור מכיל ביט אחד.",
        29,
        color=GRAY,
        he=True,
    )
    box(300, 310, 385, 370, BLUE, "#f0f6ff")
    box(1190, 310, 380, 370, GREEN, "#eff9f4")
    text(492, 370, "בחירת מסלול", 36, BLUE, he=True, bold=True)
    text(492, 452, "מקודד עדיפות", 32, he=True)
    text(492, 520, "1 > 2 > 3", 33)
    text(492, 594, "1: 01     2: 10     3: 11", 26, color=GRAY)
    for i, y in enumerate((410, 500, 590), 1):
        text(124, y, f"p{i}", 35, BLUE, bold=True)
        wire([(183, y), (300, y)], BLUE)
    wire([(685, 410), (1190, 410)], BLUE)
    text(937, 365, "candidate[1:0]", 32, BLUE)
    text(937, 455, "קוד המסלול שנבחר", 29, GRAY, he=True)
    text(1380, 365, "שמירת הזוכה", 35, GREEN, he=True, bold=True)
    text(1220, 410, "D", 29, GREEN)
    text(1380, 470, "אוגר בן שני ביטים", 31, he=True)
    text(1380, 520, "REGISTER", 27, color=GRAY)
    text(1230, 590, "EN", 29, AMBER, bold=True)
    text(1537, 410, "Q", 29, GREEN)
    text(1380, 635, "REST=1: Q_next=00", 25, RED)
    wire([(1570, 410), (1910, 410)], GREEN)
    text(1760, 355, "winner[1:0]", 33, GREEN, bold=True)
    wire([(1290, 220), (1290, 310)], GRAY, width=3)
    text(1290, 186, "clk", 31, GRAY)
    wire([(1470, 220), (1470, 310)], RED, width=4)
    text(1470, 186, "REST", 33, RED, bold=True)

    # The green two-bit bus is separated into its two actual constituent wires.
    d.ellipse((1713 * S, 403 * S, 1727 * S, 417 * S), fill=GREEN)
    svg.append(f'<circle cx="1720" cy="410" r="7" fill="{GREEN}"/>')
    wire([(1720, 410), (1720, 830), (1490, 830)], GREEN)
    text(1855, 675, "הזוכה השמור", 29, GREEN, he=True)
    box(1400, 740, 90, 180, GRAY, "#fafbfd")
    text(1445, 705, "פיצול לביטים", 25, GRAY, he=True)
    text(1425, 780, "1", 23, GREEN)
    text(1425, 880, "0", 23, GREEN)
    text(1305, 745, "Q1", 29, GREEN, bold=True)
    text(1305, 920, "Q0", 29, GREEN, bold=True)

    # ANSI OR silhouette, mirrored to face left, with inversion bubble = NOR.
    def cubic(a, b, c, e):
        return [
            tuple(
                (1 - t) ** 3 * a[j]
                + 3 * (1 - t) ** 2 * t * b[j]
                + 3 * (1 - t) * t * t * c[j]
                + t**3 * e[j]
                for j in (0, 1)
            )
            for t in [i / 100 for i in range(101)]
        ]

    points = cubic((1220, 745), (1120, 745), (1025, 760), (980, 830))
    points += cubic((980, 830), (1025, 900), (1120, 915), (1220, 915))
    points += [
        (
            (1 - t) ** 2 * 1220 + 2 * (1 - t) * t * 1160 + t * t * 1220,
            (1 - t) ** 2 * 915 + 2 * (1 - t) * t * 830 + t * t * 745,
        )
        for t in [i / 100 for i in range(101)]
    ]
    d.polygon([(x * S, y * S) for x, y in points], fill="#fff8ec")
    d.line([(x * S, y * S) for x, y in points + [points[0]]], fill=AMBER, width=4 * S)
    svg.append(
        f'<path d="M1220 745 C1120 745 1025 760 980 830 C1025 900 1120 915 1220 915 Q1160 830 1220 745 Z" fill="#fff8ec" stroke="{AMBER}" stroke-width="4"/>'
    )
    d.ellipse(
        (956 * S, 818 * S, 980 * S, 842 * S), fill="white", outline=AMBER, width=4 * S
    )
    svg.append(
        f'<circle cx="968" cy="830" r="12" fill="white" stroke="{AMBER}" stroke-width="4"/>'
    )
    text(1103, 830, "NOR", 31, AMBER, bold=True)
    wire([(1400, 780), (1200.4, 780)], GREEN, width=4)
    wire([(1400, 880), (1200.4, 880)], GREEN, width=4)
    wire([(956, 830), (820, 830), (820, 590), (1190, 590)], AMBER)
    text(1050, 548, "EN", 31, AMBER, bold=True)
    text(922, 878, "ביט אחד", 24, AMBER, he=True)

    # Keep each digit in its own LTR cell; no bidi reversal of binary codes.
    box(280, 760, 410, 290, GRAY, "#fafbfd")
    text(485, 805, "טבלת האמת של האפשור", 27, he=True, bold=True)
    for x, label in ((365, "Q1"), (485, "Q0"), (605, "EN")):
        text(x, 855, label, 26, AMBER if label == "EN" else GREEN, bold=True)
    for y, values in zip(
        (900, 945, 990, 1035), ((0, 0, 1), (0, 1, 0), (1, 0, 0), (1, 1, 0))
    ):
        for x, value in zip((365, 485, 605), values):
            text(x, y, str(value), 28)
    text(1260, 1004, "EN = NOT(Q1 OR Q0)", 32, AMBER, bold=True)
    text(1260, 1054, "Q1 = winner[1]     Q0 = winner[0]", 27, GREEN)
    text(1025, 1142, "REST = 1  =>  Q_next = 00", 32, RED, bold=True)
    text(
        1025,
        1205,
        "האיפוס גובר על האפשור, גם כשהוא אפס. העדכון בחזית שעון עולה.",
        29,
        he=True,
    )
    svg.append("</svg>")
    image.save(
        OUT
        / (
            "prep-045-first-finisher-circuit.png"
            if language == "he"
            else "prep-045-first-finisher-circuit-en.png"
        )
    )
    (
        OUT
        / (
            "prep-045-first-finisher-circuit.svg"
            if language == "he"
            else "prep-045-first-finisher-circuit-en.svg"
        )
    ).write_text("\n".join(svg), encoding="utf-8")
    print(
        OUT
        / (
            "prep-045-first-finisher-circuit.png"
            if language == "he"
            else "prep-045-first-finisher-circuit-en.png"
        )
    )


def render_circuits():
    for language in ("he", "en"):
        render_circuit(language)


if __name__ == "__main__":
    render_circuits()
