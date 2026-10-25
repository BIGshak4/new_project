"""Bilingual diagrams for five independently verified software contracts."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "diagrams"
BG, INK, PURPLE = "#fffdf8", "#35234f", "#73558d"
GREEN, ORANGE, PALE = "#327568", "#ae592e", "#eee7f3"


def panel(draw, rect, color=PURPLE, fill=PALE):
    draw.rounded_rectangle(rect, radius=25, fill=fill, outline=color, width=5)


def canvas(he,en,lang):
    image=Image.new("RGB",(2600,1750),BG)
    draw=ImageDraw.Draw(image)
    phrase(draw,(1300,105),he,en,lang,63,bold=True,color=INK)
    return image,draw


def row(draw,values,centers,y,colors=None,size=56,halfwidth=105):
    for index,(value,cx) in enumerate(zip(values,centers,strict=True)):
        color=colors[index] if colors else PURPLE
        panel(draw,(cx-halfwidth,y-80,cx+halfwidth,y+80),color=color,fill="#edf5ef" if color==GREEN else "#f6f0fa")
        text(draw,(cx,y),str(value),size,bold=True,color=color)


def minimum(lang):
    image,draw=canvas("כל עומק זוכר את המינימום שלו","Each depth remembers its own minimum",lang)
    text(draw,(1300,230),"Push: 5, 2, 2, 7",51,bold=True)
    phrase(draw,(800,350),"ערך ומינימום שמור","Value and saved minimum",lang,46,bold=True)
    for y,value,minimum_value in [(530,7,2),(750,2,2),(970,2,2),(1190,5,5)]:
        panel(draw,(350,y-80,1300,y+80),fill="#f6f0fa")
        text(draw,(825,y),f"value = {value}       min = {minimum_value}",49,bold=True)
        if y<1190:
            wire(draw,[(825,y+80),(825,y+140)],PURPLE,width=6)
    text(draw,(170,530),"Top",43,bold=True,color=PURPLE)
    for y,label,values,minimum_value in [(540,"Pop 7","[5, 2, 2]",2),(880,"Pop 2","[5, 2]",2),(1220,"Pop 2","[5]",5)]:
        panel(draw,(1570,y-130,2380,y+130),color=GREEN,fill="#edf5ef")
        text(draw,(1975,y-50),label,49,bold=True)
        text(draw,(1975,y+55),f"{values}   min = {minimum_value}",47,bold=True,color=GREEN)
    phrase(draw,(1300,1490),"מינימום כפול נשאר גם אחרי הוצאה אחת","A duplicated minimum survives one removal",lang,48,bold=True)
    phrase(draw,(1300,1620),"בריקה אין מינימום; הפעולה נכשלת במפורש","An empty stack has no minimum; query fails explicitly",lang,43)
    image.save(OUT/f"prep-131-prefix-minimum-depths-{lang}.png")


def deletion(lang):
    image,draw=canvas("מחיקה לאחור אינה מדלגת על ערכים","Backward deletion does not skip entries",lang)
    phrase(draw,(1300,240),"האינדקסים הנמוכים עדיין לא השתנו","Lower unprocessed indices have not changed",lang,46)
    centers=[450+index*400 for index in range(5)]
    row(draw,[1,2,20,3,19],centers,480,[ORANGE,ORANGE,GREEN,ORANGE,GREEN])
    for index,cx in enumerate(centers):
        text(draw,(cx,620),str(index),38)
    wire(draw,[(2050,735),(450,735)],PURPLE,width=7)
    text(draw,(1300,820),"Del(3)",53,bold=True,color=ORANGE)
    row(draw,[1,2,20,19],centers[:4],1030,[ORANGE,ORANGE,GREEN,GREEN])
    phrase(draw,(1300,1190),"כעת ממשיכים לאינדקס שתיים","Continue next at index two",lang,45)
    row(draw,[20,19],[1100,1500],1370,[GREEN,GREEN])
    phrase(draw,(1300,1540),"בדיקות לינאריות אינן מבטיחות עלות הזזה לינארית","Linear tests do not imply linear shifting work",lang,43,bold=True)
    text(draw,(1300,1625),"[1] * 50 + [19] * 50",43,color=ORANGE)
    phrase(draw,(1300,1700),"המחיקות לאחור מזיזות אלפיים וחמש מאות איברים","Backward deletions move 2500 entries",lang,37)
    image.save(OUT/f"prep-135-deletion-shifts-and-compaction-{lang}.png")


def mirror(lang):
    image,draw=canvas("היפוך בית בשלוש החלפות קבוצות","Reverse a byte in three group exchanges",lang)
    phrase(draw,(1300,240),"בכל שלב מחליפים קבוצות גדולות יותר","Each stage exchanges larger groups",lang,46)
    values=["01101011","10010111","01101101","11010110"]
    labels=[("קלט","Input",""),("שכנים","Neighbours","0x55"),("קבוצות זוגיות","Two-bit groups","0x33"),("חצאי בית","Nibbles","0x0F")]
    for index,(bits,(he,en,mask)) in enumerate(zip(values,labels,strict=True)):
        y=440+index*300
        phrase(draw,(460,y-30),he,en,lang,44,bold=True)
        if mask:
            text(draw,(460,y+55),mask,48,bold=True,color=PURPLE)
        row(draw,list(bits),[900+i*190 for i in range(8)],y,size=54,halfwidth=78)
        if index<3:
            wire(draw,[(1565,y+95),(1565,y+195)],GREEN,width=6)
    phrase(draw,(1300,1550),"שלושה שלבים אינם שלוש הוראות מכונה","Three stages do not mean three machine instructions",lang,46,bold=True)
    text(draw,(1300,1660),"1 -> 128       15 -> 240       240 -> 15",49,color=GREEN,bold=True)
    image.save(OUT/f"prep-094-c-binary-mirror-optimization-{lang}.png")


def missing(lang):
    image,draw=canvas("חזרות אינן משנות נוכחות; אפס אינו תשובה","Repetition preserves presence; zero is not an answer",lang)
    text(draw,(1300,230),"N = 5     input = [3, 3, 0, 5]",51,bold=True)
    phrase(draw,(1300,350),"תחום התשובות מתחיל באחת","The answer domain starts at one",lang,46)
    centers=[500+i*400 for i in range(5)]
    for value,cx in enumerate(centers,1):
        text(draw,(cx,460),str(value),45,bold=True)
    row(draw,["F","F","T","F","T"],centers,610,[ORANGE,ORANGE,GREEN,ORANGE,GREEN])
    phrase(draw,(1300,820),"חלופת שינוי קלט: הצבה במקום הייעודי","Mutating alternative: place each value at its home",lang,46,bold=True)
    text(draw,(1300,945),"[3, 3, 0, 5]   ->   [0, 3, 3, 5]",54,bold=True)
    text(draw,(1300,1060),"home(v) = v - 1       1 <= v < N",49)
    text(draw,(1300,1180),"present_N = True",51,bold=True,color=GREEN)
    phrase(draw,(1300,1280),"לערך האחרון אין תא ייעודי; שומרים דגל נפרד","The final domain value has no slot; keep a separate flag",lang,42)
    panel(draw,(450,1400,2150,1550),color=GREEN,fill="#edf5ef")
    text(draw,(1300,1475),"missing = [1, 2, 4]",60,bold=True,color=GREEN)
    phrase(draw,(1300,1650),"כתיבת כל החסרים דורשת זמן לפי גודל הפלט","Writing every missing value takes time proportional to output",lang,43)
    image.save(OUT/f"prep-041-all-missing-repeated-zero-sentinel-{lang}.png")


def merging(lang):
    image,draw=canvas("ממזגים מהסוף אל הקיבולת השמורה","Merge backward into reserved capacity",lang)
    text(draw,(250,370),"a",56,bold=True)
    row(draw,[1,4,4],[650,1000,1350],370)
    text(draw,(1350,230),"i = 2",43,bold=True,color=PURPLE)
    text(draw,(250,740),"b",56,bold=True)
    centers=[550+index*330 for index in range(6)]
    row(draw,[2,4,7,0,0,0],centers,740,[GREEN,GREEN,GREEN,PURPLE,PURPLE,PURPLE])
    text(draw,(centers[2],590),"j = 2",43,bold=True,color=GREEN)
    text(draw,(centers[5],590),"k = 5",43,bold=True,color=PURPLE)
    wire(draw,[(centers[2],835),(centers[2],960),(centers[5],960),(centers[5],835)],ORANGE,width=7)
    phrase(draw,(1300,1080),"רק שלושת התאים הראשונים הם נתוני קלט","Only the first three b slots are input data",lang,45)
    row(draw,[1,2,4,4,4,7],centers,1310,[GREEN]*6)
    text(draw,(1300,1510),"k - j = i + 1 > 0",55,bold=True,color=PURPLE)
    phrase(draw,(1300,1640),"הכתיבה מימין לקלט שלא נקרא; המערך הראשון נשמר","Write beyond unread b; preserve a",lang,44)
    image.save(OUT/f"prep-098-inplace-backward-capacity-merge-{lang}.png")


if __name__=="__main__":
    for language in ("he","en"):
        minimum(language)
        deletion(language)
        mirror(language)
        missing(language)
        merging(language)
