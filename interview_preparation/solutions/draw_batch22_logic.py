"""Original bilingual diagrams for eggs, clock motion, lions and calendar ages."""
from __future__ import annotations

import math
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BLUE, GREEN, PURPLE, ORANGE, INK = "#2a62a0", "#257b67", "#7854a2", "#b26522", "#23334b"


def canvas(he, en, language, height=1400, width=2400):
    image=Image.new("RGB",(width,height),"white")
    draw=ImageDraw.Draw(image)
    phrase(draw,(width/2,90),he,en,language,58,bold=True)
    return image,draw


def box(draw, rect, color=BLUE):
    draw.rounded_rectangle(rect,radius=24,fill="#f5f8fd",outline=color,width=6)


def eggs(language):
    image,draw=canvas("שתי ביצים ותקציב הולך וקטן", "Two eggs with a shrinking drop budget",language)
    box(draw,(550,225,1850,470),PURPLE)
    text(draw,(1200,305),"N <= k(k+1)/2",60,bold=True,color=PURPLE)
    phrase(draw,(1200,405),"הקומה הראשונה היא מינימום בין התקציב לגובה הבניין",
           "First test: min(k, N)",language,39)
    wire(draw,[(1200,470),(1200,570),(600,570),(600,680)],ORANGE)
    wire(draw,[(1200,470),(1200,570),(1800,570),(1800,680)],GREEN)
    phrase(draw,(620,615),"נשברה", "Breaks",language,48,color=ORANGE,bold=True)
    phrase(draw,(1780,615),"שרדה", "Survives",language,48,color=GREEN,bold=True)
    box(draw,(140,680,1060,1010),ORANGE)
    box(draw,(1340,680,2260,1010),GREEN)
    phrase(draw,(600,750),"נשארת ביצה אחת", "One egg remains",language,45,bold=True)
    phrase(draw,(600,845),"סורקים מלמטה למעלה", "Scan upward one floor at a time",language,40)
    text(draw,(600,940),"<= k-1",47,color=ORANGE)
    phrase(draw,(1800,750),"נשארות שתי ביצים", "Two eggs remain",language,45,bold=True)
    phrase(draw,(1800,845),"הקפיצה הבאה קטנה באחת", "Reduce the next gap by one",language,40)
    text(draw,(1800,940),"k-1, k-2, ...",44,color=GREEN)
    text(draw,(1200,1140),"N=10: 4 -> 7 -> 9 -> 10",45,bold=True)
    phrase(draw,(1200,1265),"הפלט הוא הקומה הבטוחה האחרונה גם אם אף ביצה לא נשברת",
           "Return the last safe floor, including N if nothing breaks",language,43)
    return image


def clock(language):
    image,draw=canvas("שני מחוגים נעים בקצבים שונים", "Two hands move at different rates",language)
    center=(710,730)
    draw.ellipse((290,310,1130,1150),outline=INK,width=7)
    for value in range(1,13):
        angle=math.radians(30*value-90)
        text(draw,(center[0]+350*math.cos(angle),center[1]+350*math.sin(angle)),str(value),47,bold=True)
    for angle,length,color,width in [(180,315,BLUE,15),(195,235,PURPLE,21)]:
        radians=math.radians(angle-90)
        endpoint=(center[0]+length*math.cos(radians),center[1]+length*math.sin(radians))
        wire(draw,[center,endpoint],color,width=width)
    draw.ellipse((697,717,723,743),fill=INK)
    draw.arc((585,605,835,855),start=90,end=105,fill=ORANGE,width=12)
    text(draw,(860,1010),"15°",43,bold=True,color=ORANGE)
    text(draw,(710,1235),"06:30",48,bold=True)
    box(draw,(1270,340,2290,1100),GREEN)
    phrase(draw,(1780,425),"מעלות בכיוון השעון", "Clockwise degrees from twelve",language,42,bold=True)
    text(draw,(1780,560),"M = 6m",56,color=BLUE,bold=True)
    text(draw,(1780,700),"H = 30(h mod 12) + m/2",43,color=PURPLE,bold=True)
    text(draw,(1780,845),"d = abs(H - M)",43)
    text(draw,(1780,970),"a = min(d, 360-d)",43,color=GREEN,bold=True)
    phrase(draw,(1200,1335),"מחוג השעות מתקדם גם בין שעות שלמות",
           "The hour hand moves between whole hours too",language,43)
    return image


def lions(language):
    image,draw=canvas("החלטה לפי ההישרדות במשחק הקטן", "Decide from survival in the smaller game",language)
    for i,n in enumerate(range(4)):
        x=100+i*590
        color=GREEN if n%2 else BLUE
        box(draw,(x,300,x+490,805),color)
        text(draw,(x+245,395),f"n={n}",65,bold=True,color=color)
        phrase(draw,(x+245,530),"הפרה נאכלת" if n%2 else "הפרה נשארת",
               "Cow is eaten" if n%2 else "Cow survives",language,39,bold=True)
        phrase(draw,(x+245,675),"האוכל שורד" if n%2 else "אין אריה שאוכל",
               "The eater survives" if n%2 else "No lion chooses to eat",language,34)
        if i<3:
            wire(draw,[(x+490,550),(x+590,550)],PURPLE,width=6)
    text(draw,(1200,935),"E(n) = NOT E(n-1)     |     E(0) = false",47,bold=True,color=PURPLE)
    phrase(draw,(1200,1060),"הישרדות קודמת לבשר וכל אכילה הופכת אריה אחד לפרה",
           "Survival outranks meat; one eater becomes the new cow",language,43)
    box(draw,(400,1160,2000,1330),GREEN)
    phrase(draw,(1200,1240),"במאה הפרה נשארת ובמאה ואחד הפרה נאכלת",
           "With one hundred the cow survives; with one hundred and one it is eaten",language,42,bold=True,color=GREEN)
    return image


def calendar(language):
    image,draw=canvas("שתי יממות שחוצות יום הולדת ושנה", "Two days cross a birthday and a year",language)
    points=[("30/12", "Y-1", "8", "לפני יומיים", "Two days ago"),
            ("31/12", "Y-1", "9", "יום הולדת אתמול", "Birthday yesterday"),
            ("01/01", "Y", "9", "היום", "Today"),
            ("31/12", "Y", "10", "יום הולדת השנה", "Birthday this year"),
            ("31/12", "Y+1", "11", "יום הולדת בשנה הבאה", "Birthday next year")]
    for i,(day,year,age,he,en) in enumerate(points):
        x=65+i*475
        color=GREEN if i==2 else PURPLE
        box(draw,(x,360,x+400,1000),color)
        text(draw,(x+200,460),day,57,bold=True,color=color)
        text(draw,(x+200,565),year,48,color=color)
        phrase(draw,(x+200,690),he,en,language,29,bold=True)
        phrase(draw,(x+200,805),"גיל", "Age",language,36)
        text(draw,(x+200,905),age,72,bold=True,color=color)
        if i<4:
            wire(draw,[(x+400,680),(x+475,680)],BLUE,width=6)
    phrase(draw,(1200,1145),"היום הראשון בינואר ויום ההולדת האחרון בדצמבר",
           "Today is January first; the birthday is December thirty-first",language,45,bold=True)
    phrase(draw,(1200,1280),"בשנה הבאה פירושו בשנה הקלנדרית הבאה ולא בעוד שתים עשרה חודשים",
           "Next year means the next calendar year, not twelve months from today",language,40)
    return image


if __name__ == "__main__":
    for stem,producer in [("prep-025-highest-safe-batch22",eggs),("prep-017-general-clock-batch22",clock),
                          ("prep-231-lion-survival-parity",lions),("prep-232-calendar-age-timeline",calendar)]:
        for language in ("he","en"):
            producer(language).save(OUT/f"{stem}-{language}.png")
    print("Eight original bilingual logic diagrams written")
