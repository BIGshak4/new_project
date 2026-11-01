"""Clean, bilingual explanatory assets; no copied source screenshot content."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
INK, BLUE, GREEN, PURPLE, ORANGE = '#23334b', '#2a62a0', '#257b67', '#7854a2', '#b26522'


def canvas(he, en, language):
    image = Image.new('RGB', (2400, 1400), 'white')
    draw = ImageDraw.Draw(image)
    phrase(draw, (1200, 95), he, en, language, 57, bold=True, color=INK)
    return image, draw


def panel(draw, rect, color=BLUE):
    draw.rounded_rectangle(rect, radius=22, fill='#f5f8fd', outline=color, width=6)


def networking(language):
    image, draw = canvas('פרוטוקולים והיקף רשת הן שתי שאלות שונות', 'Protocol roles and network scope answer different questions', language)
    for i, (name, he, en) in enumerate([
        ('FTP', 'העברת קבצים', 'File transfer'), ('TCP', 'תעבורה בין תהליכים', 'Transport between processes'),
        ('IP', 'כתובות וניתוב חבילות', 'Addressing and packet routing')]):
        x = 100 + 790 * i
        panel(draw, (x, 270, x + 620, 650))
        text(draw, (x + 310, 375), name, 73, bold=True, color=BLUE)
        phrase(draw, (x + 310, 525), he, en, language, 33)
        if i < 2:
            wire(draw, [(x + 620, 455), (x + 790, 455)], INK, width=6)
    for x, name, he, en in [(170, 'LAN', 'תחום מקומי', 'Local area'), (1280, 'WAN', 'חיבור בין אתרים', 'Wider-area connectivity')]:
        panel(draw, (x, 820, x + 940, 1150), GREEN)
        text(draw, (x + 470, 900), name, 62, bold=True, color=GREEN)
        phrase(draw, (x + 470, 1040), he, en, language, 43)
    phrase(draw, (1200, 1290), 'אין להסיק הצפנה משם פרוטוקול או אבטחה מהיקף רשת',
           'Protocol names and geographical scope do not establish encryption or security', language, 37)
    return image


def static(language):
    image, draw = canvas('מפרידים משך חיים וקישוריות ושייכות למחלקה', 'Separate duration, linkage and class membership', language)
    cards = [
        ('משך חיים', 'Storage duration', 'static int calls;', '1 -> 2 -> 3', 'נשמר בין קריאות', 'Retained across calls'),
        ('קישוריות', 'Linkage', 'static int file_state;', 'translation unit', 'שם פנימי ליחידת תרגום', 'Name internal to a translation unit'),
        ('חבר מחלקה', 'Class member', 'inline static int total;', 'Counter::total', 'נתון משותף ולא עותק לכל מופע', 'Shared data, not a copy per instance'),
    ]
    for i, (he, en, code, result, explain_he, explain_en) in enumerate(cards):
        x = 75 + 790 * i
        panel(draw, (x, 300, x + 670, 1030), [BLUE, PURPLE, GREEN][i])
        phrase(draw, (x + 335, 410), he, en, language, 45, bold=True)
        text(draw, (x + 335, 585), code, 30, bold=True, color=BLUE)
        text(draw, (x + 335, 735), result, 37, color=PURPLE)
        phrase(draw, (x + 335, 905), explain_he, explain_en, language, 29)
    phrase(draw, (1200, 1210), 'שם מקומי יכול להתייחס לאובייקט שחי לאורך התוכנית',
           'A local name may denote an object lasting throughout the program', language, 44, bold=True)
    phrase(draw, (1200, 1310), 'אתחול משותף בטוח אינו הופך כל שינוי מאוחר לאטומי',
           'Safe shared initialization does not make every later mutation atomic', language, 38)
    return image


def python(language):
    image, draw = canvas('מנגנון קיים ואופן אכיפה אינם אותו דבר', 'A supported mechanism and its enforcement are different', language)
    cells = [
        ('טיפוסים דינמיים', 'Dynamic types', '1 + "1" -> TypeError', 'פעולה שגויה עדיין נכשלת', 'Invalid operations still fail'),
        ('רמזי טיפוסים', 'Type annotations', 'value: int', 'אינם בדיקת זמן ריצה אוטומטית', 'Not automatic runtime validation'),
        ('גישה לחברים', 'Member access', '__value -> _Class__value', 'שינוי שם אינו מחסום אבטחה', 'Mangling is not a security boundary'),
        ('הגדרת מתודה מחדש', 'Method redefinition', 'def f ...; def f ...', 'ההגדרה האחרונה קושרת את השם', 'The last definition binds the name'),
    ]
    for i, (he, en, code, bottom_he, bottom_en) in enumerate(cells):
        x, y = 120 + (i % 2) * 1180, 265 + (i // 2) * 510
        panel(draw, (x, y, x + 990, y + 425), GREEN if i % 2 else BLUE)
        phrase(draw, (x + 495, y + 85), he, en, language, 42, bold=True)
        text(draw, (x + 495, y + 210), code, 37, color=PURPLE, bold=True)
        phrase(draw, (x + 495, y + 335), bottom_he, bottom_en, language, 33)
    phrase(draw, (1200, 1330), 'מחלקות וירושה ופולימורפיזם קיימים גם בלי תחביר זהה לשפה אחרת',
           'Classes, inheritance and polymorphism do not require identical syntax across languages', language, 33)
    return image


def abstract(language):
    image, draw = canvas('מחלקה אבסטרקטית ודרישת מתודה הן רמות שונות', 'An abstract class and a method requirement are different levels', language)
    for x, name, code, he, en, color in [
        (100, 'C++17', 'virtual double area() const = 0;', 'פונקציה וירטואלית טהורה', 'Pure virtual function', BLUE),
        (1280, 'C#', 'public abstract double Area();', 'מתודה אבסטרקטית במחלקה אבסטרקטית', 'Abstract method in an abstract class', GREEN)]:
        panel(draw, (x, 300, x + 1020, 810), color)
        text(draw, (x + 510, 405), name, 60, color=color, bold=True)
        text(draw, (x + 510, 565), code, 35, bold=True)
        phrase(draw, (x + 510, 710), he, en, language, 33)
    phrase(draw, (1200, 950), 'הבסיס אינו מופע עצמאי והנגזרת מממשת את הדרישה',
           'The base is not a standalone instance; a concrete derived class implements the requirement', language, 37, bold=True)
    text(draw, (1200, 1090), 'Shape -> Rectangle: area = width * height', 48, color=PURPLE, bold=True)
    phrase(draw, (1200, 1260), 'במחלקת בסיס יכולות להיות גם מתודות ממומשות ונתונים',
           'A base class may also contain implemented methods and state', language, 42)
    return image


def motorcycles(language):
    image, draw = canvas('פחות מובילים ומכלים מלאים בכל שלב', 'Fewer carriers, with full tanks at each stage', language)
    for i, (active, distance) in enumerate([(100, '50 / 100'), (99, '50 / 99'), (2, '50 / 2'), (1, '50')]):
        x = 60 + i * 595
        panel(draw, (x, 310, x + 500, 930), GREEN if active == 1 else BLUE)
        text(draw, (x + 250, 420), f'k = {active}', 57, bold=True, color=BLUE)
        phrase(draw, (x + 250, 540), 'מרחק השלב', 'Stage distance', language, 35)
        text(draw, (x + 250, 645), distance, 50, bold=True, color=PURPLE)
        phrase(draw, (x + 250, 795), 'מטרים', 'metres', language, 40)
        if i < 3:
            wire(draw, [(x + 500, 615), (x + 595, 615)], INK, width=5)
    text(draw, (1200, 1050), 'D = 50 * (1/100 + 1/99 + ... + 1)', 51, color=PURPLE, bold=True)
    text(draw, (1200, 1175), 'D = 259.368875881981 m', 56, color=GREEN, bold=True)
    phrase(draw, (1200, 1320), 'הצריכה היא ליטר למטר והעברת הדלק מתבצעת במפגש',
           'Consumption is one litre per metre; fuel transfer requires a meeting', language, 38)
    return image


if __name__ == '__main__':
    for number, producer in [(240, networking), (241, static), (242, python), (243, abstract), (244, motorcycles)]:
        for language in ('he', 'en'):
            producer(language).save(OUT / f'prep-{number}-concepts-{language}.png')
    print('Ten original bilingual concept diagrams written')
