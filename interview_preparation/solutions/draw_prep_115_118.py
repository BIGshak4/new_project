"""Reproduce bilingual educational MOS/comparator figures (Pillow + matplotlib).

Curves come from the published equation model, not measured device data.
All figures are solution material; none is an original screenshot.
"""
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw
from prep_115_nmos_long_channel import nmos_current

OUT = Path(__file__).resolve().parents[1] / "diagrams"
INK, PURPLE, GREEN = "#302344", "#5d4383", "#33786d"
BG, PALE, BLUE, GOLD = "#fffdf8", "#e7def0", "#b4d5e6", "#d49d4b"


def canvas(he, en, lang, height=1500):
    image = Image.new("RGB", (2200, height), BG)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 82), he, en, lang, 52, bold=True)
    return image, draw


def label(draw, xy, value, size=40, color=INK):
    text(draw, xy, value, size, bold=True, color=color)


def arrow(draw, start, end, color=INK, width=5):
    draw.line((start, end), fill=color, width=width)
    dx, dy = end[0] - start[0], end[1] - start[1]
    norm = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / norm, dy / norm
    draw.polygon((end, (end[0] - 22 * ux + 10 * uy, end[1] - 22 * uy - 10 * ux),
                  (end[0] - 22 * ux - 10 * uy, end[1] - 22 * uy + 10 * ux)), fill=color)


def ground(draw, x, y):
    for delta, half in ((0, 32), (14, 22), (28, 10)):
        draw.line(((x - half, y + delta), (x + half, y + delta)), fill=INK, width=5)


def nmos_section(lang):
    image, d = canvas("חתך מושגי של טרנזיסטור תעלה מסוג אן", "Conceptual planar enhancement-NMOS cross-section", lang, 1500)
    phrase(d, (1100, 174), "החתך אינו בקנה מידה; תעלה מוליכה נוצרת רק בהטיה מתאימה", "Not to scale; the inversion channel exists only under suitable gate bias", lang, 35)
    d.rectangle((220, 680, 1980, 1120), fill="#f1dfcd", outline=INK, width=5)
    # Fabricated regions are colored blue; body contact is a separate p+ region.
    for rect, name in (((330, 680, 550, 835), "p+"), ((680, 680, 960, 835), "n+"), ((1480, 680, 1760, 835), "n+")):
        d.rectangle(rect, fill=BLUE if name == "n+" else "#e6b3bd", outline=INK, width=5)
        label(d, ((rect[0] + rect[2]) // 2, 770), name, 54)
    d.rectangle((900, 590, 1540, 680), fill=PALE, outline=PURPLE, width=4)
    d.rectangle((900, 450, 1540, 590), fill="#b0a5c4", outline=INK, width=5)
    # Insulator continues between gate and silicon; green is mobile inversion,
    # not another permanent dopant region.
    d.line(((955, 687), (1485, 687)), fill=GREEN, width=16)
    for x in range(1000, 1470, 75):
        label(d, (x, 730), "−", 31, GREEN)
    for x, name, y in ((440, "B", 310), (820, "S", 310), (1620, "D", 310)):
        wire(d, [(x, y + 75), (x, 680)], INK)
        label(d, (x, y), name, 53)
    wire(d, [(1220, 310), (1220, 450)], INK)
    label(d, (1220, 255), "G", 54)
    # Explicit external source-body connection; separate from the gate wire.
    wire(d, [(440, 405), (440, 355), (820, 355), (820, 405)], INK)
    for x in (440, 820):
        d.ellipse((x - 8, 397, x + 8, 413), fill=INK)
    label(d, (630, 260), "B = S", 37)
    phrase(d, (1100, 1010), "גוף סיליקון מסוג פי", "p-type silicon body", lang, 44, bold=True)
    label(d, (1880, 580), "SiO2", 39, PURPLE)
    arrow(d, (1830, 615), (1545, 615), PURPLE)
    phrase(d, (1850, 455), "מבודד שער", "Gate insulator", lang, 33)
    phrase(d, (1210, 510), "אלקטרודת שער", "Gate electrode", lang, 35)
    phrase(d, (1220, 855), "שכבת היפוך ניידת", "Mobile inversion sheet", lang, 35)
    arrow(d, (1220, 820), (1220, 700), GREEN)
    phrase(d, (1100, 1235), "אזורי המקור והשפך נוצרים באילוח תורמים ובהפעלתם בחום", "Source/drain: fabricated donor doping and thermal activation", lang, 39)
    phrase(d, (1100, 1340), "המתח בשער יוצר היפוך; הוא אינו יוצר אטומי אילוח", "Gate voltage induces inversion; it does not create dopant atoms", lang, 39)
    label(d, (1100, 1430), "VGS > VT      VDS >= 0      conventional ID: D → S", 34, PURPLE)
    image.save(OUT / f"prep-115-nmos-cross-section-{lang}.png")


def plot_image(fig, width, height):
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150, facecolor=BG)
    plt.close(fig)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB").resize((width, height), Image.Resampling.LANCZOS)


def style_axes(ax):
    ax.set_facecolor(BG)
    ax.grid(alpha=0.22, color=INK)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color(INK)
    ax.tick_params(colors=INK, labelsize=13)


def nmos_curves(lang):
    image, d = canvas("אופייני זרם במודל תעלה ארוכה", "Long-channel equation-model current characteristics", lang, 1550)
    phrase(d, (1100, 180), "נתוני הדוגמה אינם פרמטרים של תהליך מסחרי", "Illustrative parameters, not a calibrated commercial process", lang, 37)
    label(d, (1100, 270), "VT = 0.5 V       beta = 1 mA/V²       B = S       lambda = 0", 39)
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.8), facecolor=BG)
    fig.subplots_adjust(left=0.075, right=0.97, bottom=0.18, top=0.94, wspace=0.3)
    xvalues = [index / 200 for index in range(401)]
    for gate, color in ((1.0, GREEN), (1.5, PURPLE), (2.0, GOLD)):
        currents = [1000 * nmos_current(gate, drain, 0.001, 0.5)[1] for drain in xvalues]
        axes[0].plot(xvalues, currents, color=color, lw=3, label=f"VGS = {gate:g} V")
        boundary = gate - 0.5
        current = 1000 * nmos_current(gate, boundary, 0.001, 0.5)[1]
        axes[0].scatter([boundary], [current], color=color, s=55, zorder=4)
        axes[0].plot([boundary, boundary], [0, current], ls=":", color=color, alpha=0.65)
    axes[0].set_xlabel("VDS (V)", fontsize=17, color=INK)
    axes[0].set_ylabel("ID (mA)", fontsize=17, color=INK)
    axes[0].set_xlim(0, 2)
    axes[0].set_ylim(0, 1.3)
    axes[0].legend(fontsize=12, loc="upper left", frameon=False)
    currents = [1000 * nmos_current(gate, 2.0, 0.001, 0.5)[1] for gate in xvalues]
    axes[1].plot(xvalues, currents, color=PURPLE, lw=3, label="VDS = 2 V")
    axes[1].axvline(0.5, ls=":", color=GREEN)
    axes[1].set_xlabel("VGS (V)", fontsize=17, color=INK)
    axes[1].set_ylabel("ID (mA)", fontsize=17, color=INK)
    axes[1].set_xlim(0, 2)
    axes[1].set_ylim(0, 1.3)
    axes[1].legend(fontsize=12, loc="upper left", frameon=False)
    for ax in axes:
        style_axes(ax)
    image.paste(plot_image(fig, 2100, 950), (50, 330))
    phrase(d, (580, 1290), "נקודות: גבול טריודה ורוויה", "Dots: triode/saturation boundary", lang, 34)
    phrase(d, (1630, 1290), "רוויה בכל טווח הסריקה הפעיל", "Saturation throughout the active sweep", lang, 34)
    label(d, (580, 1370), "VDS = VGS - VT", 38, GREEN)
    label(d, (1630, 1370), "VGS > 0.5 V      VDS >= VGS - VT", 31, GREEN)
    phrase(d, (1100, 1470), "אין כאן נתוני מדידה, תת־סף או תופעות תעלה קצרה", "No measured data, subthreshold current or short-channel effects are shown", lang, 36)
    image.save(OUT / f"prep-115-nmos-current-characteristics-{lang}.png")


def comparator_interface(lang):
    image, d = canvas("משווה מתח וגבולות הממשק הספרתי", "Voltage comparator and digital-interface boundaries", lang, 1900)
    phrase(d, (1100, 180), "סף ההחלטה הוא פרמטר במפרט, ולא בהכרח חצי האספקה", "The specified decision threshold is not necessarily half-supply", lang, 37)
    d.polygon(((750, 400), (750, 950), (1350, 675)), fill="#f4eef8", outline=PURPLE, width=6)
    wire(d, [(150, 530), (750, 530)], INK)
    wire(d, [(150, 825), (750, 825)], INK)
    label(d, (300, 450), "Vin", 50)
    label(d, (300, 745), "Vref", 50)
    label(d, (810, 530), "+", 56, GREEN)
    label(d, (810, 825), "−", 56, GREEN)
    wire(d, [(1050, 300), (1050, 537)], INK)
    wire(d, [(1050, 812), (1050, 1000)], INK)
    label(d, (1050, 260), "VCC", 42)
    label(d, (1050, 1065), "VEE", 42)
    wire(d, [(1350, 675), (1650, 675)], PURPLE)
    label(d, (1490, 595), "Y", 52, PURPLE)
    d.rounded_rectangle((1650, 500, 2090, 850), radius=20, fill="#edf5ef", outline=GREEN, width=5)
    phrase(d, (1870, 590), "צרכן ספרתי", "Digital receiver", lang, 35, bold=True)
    label(d, (1870, 680), "VIH / VIL", 35)
    label(d, (1870, 775), "0 / 1", 43, GREEN)
    label(d, (1100, 1150), "IDEAL:  Vin > Vref : HIGH       Vin < Vref : LOW", 40, PURPLE)
    phrase(d, (1100, 1240), "בשוויון אין רמת יציאה מובטחת; יש היסט, רעש והשהיה", "Equality has no guaranteed logic result; offset, noise and delay matter", lang, 36)
    # Separate output-stage option, not an extra wire on every comparator.
    d.rounded_rectangle((200, 1370, 740, 1610), radius=18, fill=PALE, outline=PURPLE, width=4)
    label(d, (470, 1455), "OPEN-DRAIN", 38, PURPLE)
    phrase(d, (470, 1540), "אפשרות יציאה", "Output option", lang, 30)
    wire(d, [(740, 1490), (1890, 1490)], INK)
    wire(d, [(470, 1610), (470, 1660)], INK)
    ground(d, 470, 1660)
    wire(d, [(1190, 1335), (1190, 1380)], INK)
    d.line(((1190, 1380), (1170, 1392), (1210, 1410), (1170, 1428), (1210, 1446), (1190, 1460)), fill=INK, width=5)
    wire(d, [(1190, 1460), (1190, 1490)], INK)
    d.ellipse((1182, 1482, 1198, 1498), fill=INK)
    label(d, (1190, 1300), "Vpullup", 35)
    label(d, (1370, 1410), "Rpullup", 34)
    label(d, (1850, 1420), "Y", 45, PURPLE)
    phrase(d, (1440, 1595), "מסילת המשיכה נבחרת רק בגבולות שהרכיב מתיר", "Pull-up rail must be permitted by the selected device", lang, 31)
    phrase(d, (1100, 1765), "בדקו בנפרד את תחומי הכניסה ואת רמות היציאה בעומס", "Check input operating limits and loaded output logic levels separately", lang, 37)
    phrase(d, (1100, 1850), "שרטוט עקרוני; לא בוצעה בחירת חלק או סימולציה אנלוגית", "Conceptual diagram; no part selection or analog simulation was performed", lang, 32)
    image.save(OUT / f"prep-118-voltage-comparator-interface-{lang}.png")


def hysteresis_transfer(lang):
    image, d = canvas("היסטרזיס: שני ספים עם זיכרון ביניהם", "Hysteresis: two thresholds with memory between them", lang, 1400)
    phrase(d, (1100, 180), "אותו מתח ברצועה יכול לתת אפס או אחד לפי ההיסטוריה", "Inside the band, the same voltage can produce zero or one depending on history", lang, 35)
    fig, ax = plt.subplots(figsize=(12.6, 5.1), facecolor=BG)
    fig.subplots_adjust(left=0.08, right=0.96, bottom=0.18, top=0.92)
    ax.axvspan(1.2, 1.3, color=PALE, alpha=0.8)
    ax.plot([0.95, 1.3, 1.3, 1.55], [0, 0, 1, 1], color=PURPLE, lw=4, label="Vin ↑")
    ax.plot([1.55, 1.2, 1.2, 0.95], [1, 1, 0, 0], color=GREEN, lw=3, ls="--", label="Vin ↓")
    for y, start, end, color in ((0, 1.07, 1.17, PURPLE), (1, 1.48, 1.38, GREEN)):
        ax.annotate("", xy=(end, y), xytext=(start, y), arrowprops={"arrowstyle": "->", "lw": 3, "color": color})
    ax.annotate("", xy=(1.3, 0.78), xytext=(1.3, 0.25), arrowprops={"arrowstyle": "->", "lw": 3, "color": PURPLE})
    ax.annotate("", xy=(1.2, 0.22), xytext=(1.2, 0.75), arrowprops={"arrowstyle": "->", "lw": 3, "color": GREEN})
    ax.set_xticks([1.0, 1.2, 1.3, 1.5])
    ax.set_yticks([0, 1])
    ax.set_xlim(0.95, 1.55)
    ax.set_ylim(-0.16, 1.2)
    ax.set_xlabel("Vin (V)", fontsize=18, color=INK)
    ax.set_ylabel("Y", fontsize=20, rotation=0, color=INK)
    ax.legend(fontsize=16, frameon=False, loc="upper left")
    style_axes(ax)
    image.paste(plot_image(fig, 2050, 900), (75, 260))
    label(d, (1100, 1170), "Vlow = 1.2 V       Vhigh = 1.3 V", 40, PURPLE)
    phrase(d, (1100, 1270), "זהו תרשים מצבים יציבים; נקודות הסף וההשהיה תלויות ברכיב", "Settled-state illustration; exact trip points and delay depend on the device", lang, 35)
    phrase(d, (1100, 1350), "בהפעלה בתוך הרצועה אין מצב מובטח ללא מפרט אתחול", "Startup inside the band has no guaranteed state without a startup specification", lang, 34)
    image.save(OUT / f"prep-118-hysteresis-transfer-{lang}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        nmos_section(language)
        nmos_curves(language)
        comparator_interface(language)
        hysteresis_transfer(language)
    print("Wrote 8 bilingual solution figures for PREP-115/PREP-118")
