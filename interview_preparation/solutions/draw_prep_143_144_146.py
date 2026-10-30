"""Clean bilingual solution cards for conservation, sampling and trip timing."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
PAPER, INK, PURPLE, GREEN, PALE = "#fffdf8", "#302344", "#5d4383", "#33786d", "#e7def0"
RED, BLUE, ORANGE = "#b54e56", "#4678af", "#b76530"


def panel(draw, rectangle, color=PURPLE):
    draw.rounded_rectangle(rectangle, 24, fill=PALE if color == PURPLE else "#e8f1eb", outline=color, width=5)


def cups(language):
    image = Image.new("RGB", (2200, 1350), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 90), "כמות זרה שווה אינה תמיד שיעור זר שווה", "Equal foreign volumes need not mean equal foreign fractions", language, 48, bold=True)
    phrase(draw, (1100, 180), "אותו נפח יוצא וחוזר לכל כוס", "The same spoon volume leaves and returns", language, 40)
    for x, color, foreign, name in ((620, RED, BLUE, "A"), (1580, BLUE, RED, "B")):
        draw.rounded_rectangle((x-260, 380, x+260, 870), 18, fill="white", outline=INK, width=7)
        draw.rectangle((x-250, 465, x+250, 855), fill=color)
        draw.rectangle((x-250, 465, x+250, 505), fill=foreign)
        text(draw, (x, 325), name, 62, bold=True)
        text(draw, (x, 665), "V = 100", 54, color="white", bold=True)
        text(draw, (x, 940), "foreign volume = 100/11", 40, bold=True, color=PURPLE)
        text(draw, (x, 1010), "foreign fraction = 1/11", 40)
    wire(draw, [(930, 390), (1270, 390)], PURPLE, 7)
    text(draw, (1100, 330), "s = 10", 40, color=PURPLE)
    wire(draw, [(1270, 820), (930, 820)], GREEN, 7)
    text(draw, (1100, 880), "s = 10", 40, color=GREEN)
    phrase(draw, (1100, 1110), "הדוגמה מניחה ערבוב ונפחים התחלתיים שווים", "Illustration assumes mixing and equal initial volumes", language, 38)
    phrase(draw, (1100, 1190), "בנפחים שונים הכמויות נשארות שוות אך האחוזים שונים", "With unequal cup volumes, equal amounts give different fractions", language, 37, bold=True)
    phrase(draw, (1100, 1270), "קרבת צבע נראית לעין דורשת מודל אופטי נוסף", "Perceived color closeness needs an additional optical model", language, 36)
    image.save(OUT / f"prep-143-cup-conservation-{language}.png")


def sampling(language):
    image = Image.new("RGB", (2400, 1450), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 90), "מסננים לפני שהרעש מתקפל לתחום הרצוי", "Filter before unwanted energy aliases into the useful band", language, 51, bold=True)
    for rect, he, en in (((80, 310, 660, 570), "אות ורעש", "Signal + noise"), ((900, 310, 1500, 570), "מסנן אנלוגי", "Analog low-pass"), ((1740, 310, 2320, 570), "דוגם וממיר", "Sampler / ADC")):
        panel(draw, rect)
        phrase(draw, ((rect[0]+rect[2])/2, 400), he, en, language, 43, bold=True)
    text(draw, (370, 485), "useful: 0..10 kHz", 34)
    text(draw, (1200, 485), "pass: 0..10 kHz", 34)
    text(draw, (2030, 485), "example: 48 ksample/s", 32)
    wire(draw, [(660, 440), (900, 440)], GREEN, 7)
    wire(draw, [(1500, 440), (1740, 440)], GREEN, 7)
    phrase(draw, (1200, 660), "תחום מעבר למסנן במימוש לדוגמה", "Transition space in the illustrative design", language, 40, bold=True)
    text(draw, (1200, 730), "10 kHz < transition band < 24 kHz", 43, color=GREEN)
    panel(draw, (150, 830, 2250, 1100), GREEN)
    text(draw, (1200, 900), "38 kHz  -- sample at 48 ksample/s -->  10 kHz", 45, bold=True, color=GREEN)
    phrase(draw, (1200, 1000), "אחרי הדגימה אי אפשר להבחין בין שני טוני קוסינוס אלה", "These two cosine tones are indistinguishable after sampling", language, 37)
    phrase(draw, (1200, 1200), "הגבול האידאלי אינו תכנון מסנן או קצב מעשי יחיד", "The ideal bound is not a complete filter or a unique practical rate", language, 38, bold=True)
    text(draw, (1200, 1280), "fs > 2B    |    B = 10 kHz    |    fs > 20 ksample/s", 42)
    phrase(draw, (1200, 1365), "סדר המסנן תלוי בהנחתה וברעש המותרים", "Filter order depends on attenuation and allowed residual noise", language, 37)
    image.save(OUT / f"prep-144-antialias-sampling-chain-{language}.png")


def speed(language):
    image = Image.new("RGB", (2200, 1270), PAPER)
    draw = ImageDraw.Draw(image)
    phrase(draw, (1100, 90), "בודקים קודם את תקציב הזמן", "Start with the total time budget", language, 56, bold=True)
    text(draw, (1100, 195), "target average = 2*v1     total distance = 2*d", 44)
    phrase(draw, (1100, 320), "כל הזמן המותר כבר נוצל בדרך הלוך", "The outbound leg consumes the entire allowed time", language, 44, bold=True)
    draw.rounded_rectangle((180, 430, 1730, 600), 20, fill=PALE, outline=PURPLE, width=5)
    text(draw, (955, 515), "allowed time = (2*d)/(2*v1) = d/v1", 42, color=PURPLE, bold=True)
    draw.rounded_rectangle((180, 720, 1730, 890), 20, fill="#e8f1eb", outline=GREEN, width=5)
    text(draw, (955, 805), "outbound time = d/v1", 48, color=GREEN, bold=True)
    draw.rounded_rectangle((1760, 720, 2130, 890), 20, fill="#f7e9de", outline=ORANGE, width=5)
    text(draw, (1945, 775), "return", 34, color=ORANGE, bold=True)
    text(draw, (1945, 840), "d/v2 > 0", 37, color=ORANGE, bold=True)
    text(draw, (1100, 1010), "v_avg = 2*v1*v2/(v1+v2) < 2*v1", 49, color=PURPLE, bold=True)
    phrase(draw, (1100, 1110), "אין מהירות חזרה חיובית וסופית שמשיגה את היעד", "No finite positive return speed reaches the target", language, 40, bold=True)
    phrase(draw, (1100, 1190), "אפשר להתקרב ליעד ככל שמהירות החזרה גדלה", "The average approaches the target as return speed grows", language, 38)
    image.save(OUT / f"prep-146-round-trip-time-budget-{language}.png")


if __name__ == "__main__":
    for language in ("he", "en"):
        cups(language)
        sampling(language)
        speed(language)
