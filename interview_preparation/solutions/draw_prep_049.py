"""Draw the checked adaptive balance tree in Hebrew and English, from its model."""
import importlib.util
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('coins', ROOT/'solutions/prep_049_twelve_coins.py')
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)
S = 2
INK, BLUE, GREEN, AMBER, GRAY = '#24334b', '#2563b8', '#16806b', '#b36a17', '#708095'


def render(first, lang):
    im = Image.new('RGB', (2100*S, 1450*S), 'white')
    d = ImageDraw.Draw(im)
    def t(x,y,s,size=30,color=INK,bold=False,he=False):
        f=ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size*S)
        d.text((x*S,y*S),s[::-1] if he else s,font=f,fill=color,anchor='mm')
    def word(x,y,he,en,**kw):
        t(x,y,he if lang=='he' else en,he=lang=='he',**kw)
    def box(x,y,w,h,color=BLUE):
        d.rounded_rectangle((x*S,y*S,(x+w)*S,(y+h)*S),radius=18*S,fill='#f5f8fc',outline=color,width=3*S)
    def wire(points,color=BLUE):
        d.line([(x*S,y*S) for x,y in points],fill=color,width=4*S,joint='curve')
        (px,py),(x,y)=points[-2:]; a=math.atan2(y-py,x-px)
        pts=[(x,y)]+[(x-18*math.cos(a+b),y-18*math.sin(a+b)) for b in (-.43,.43)]
        d.polygon([(x*S,y*S) for x,y in pts],fill=color)
    def pans(pair):
        return ', '.join(map(str,pair[0]))+'    vs    '+', '.join(map(str,pair[1]))

    condition_he={'left':'שקילה ראשונה — כף שמאל כבדה יותר','balance':'שקילה ראשונה — הכפות מאוזנות','right':'שקילה ראשונה — כף ימין כבדה יותר'}[first]
    condition_en={'left':'First weighing: LEFT heavier','balance':'First weighing: BALANCED','right':'First weighing: RIGHT heavier'}[first]
    word(1050,65,condition_he,condition_en,size=43,bold=True)
    t(1050,135,'1, 2, 3, 4    vs    5, 6, 7, 8',36,BLUE,bold=True)
    word(1050,205,'המספרים משמאל הם בכף שמאל; המספרים מימין הם בכף ימין.','Numbers left of "vs" go on the LEFT pan; numbers right go on the RIGHT.',size=26,color=GRAY)
    word(1050,260,'סימני תוצאה: פלוס — שמאל כבדה; אפס — איזון; מינוס — ימין כבדה.','Outcome signs: + LEFT heavier; 0 BALANCED; - RIGHT heavier.',size=27,color=GRAY)
    box(600,330,900,220)
    word(1050,380,'שקילה שנייה','SECOND weighing',size=34,bold=True)
    t(1050,460,pans(MODEL.SECOND[first]),37,BLUE,bold=True)
    for i, second in enumerate(MODEL.OUTCOMES):
        cx=370+680*i
        pair,answers=MODEL.FINAL[(first,second)]
        color=(AMBER, GREEN, BLUE)[i]
        wire([(1050,550),(1050,590),(cx,590),(cx,700)],color)
        d.rounded_rectangle(((cx-28)*S,623*S,(cx+28)*S,677*S),radius=8*S,fill='white')
        t(cx,650,('+','0','-')[i],42,color,bold=True)
        box(cx-310,700,620,230,color)
        word(cx,750,'שקילה שלישית','THIRD weighing',size=32,bold=True)
        t(cx,820,pans(pair),40,color,bold=True)
        word(cx,890,'לאחריה קוראים את התוצאה למטה','Then use the result below',size=25,color=GRAY)
        box(cx-310,990,620,270,color)
        for j, answer in enumerate(answers):
            y=1045+80*j
            t(cx-235,y,('+','0','-')[j],36,color,bold=True)
            t(cx-155,y,'->',28,color)
            if answer:
                t(cx+55,y,f'{answer[0]} '+('H' if answer[1]=='heavy' else 'L'),37,bold=True)
            else:
                word(cx+55,y,'לא אפשרי במודל','IMPOSSIBLE',size=25,color=GRAY)
    word(1050,1330,'כל שורה מזהה גם את המטבע וגם אם הוא כבד או קל.','Each result identifies BOTH the coin and whether it is heavy or light.',size=28)
    if lang=='he':
        t(650,1390,'H',31,bold=True); t(745,1390,'כבד',31,he=True)
        t(1260,1390,'L',31,bold=True); t(1345,1390,'קל',31,he=True)
    else:
        t(1050,1390,'H = HEAVY       L = LIGHT',31,bold=True)
    path=ROOT/f'diagrams/prep-049-first-{first}-{lang}.png'
    im.save(path)
    return path


if __name__=='__main__':
    for lang in ('he','en'):
        for first in MODEL.OUTCOMES:
            print(render(first,lang))
