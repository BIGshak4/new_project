"""Own bilingual probability and information-flow diagrams; no source-image reuse."""
from pathlib import Path

from draw_prep_016_064 import phrase, text, wire
from PIL import Image, ImageDraw

OUT=Path(__file__).resolve().parents[1]/'diagrams'
INK,BLUE,GREEN,RED='#23334b','#2a62a0','#257b67','#b24747'


def card(d,rect,label,color=BLUE,size=43):
    d.rounded_rectangle(rect,radius=22,fill='#f5f8fd',outline=color,width=5)
    text(d,((rect[0]+rect[2])//2,(rect[1]+rect[3])//2),label,size,bold=True,color=color)


def bayes(lang):
    im=Image.new('RGB',(2400,1700),'white');d=ImageDraw.Draw(im)
    phrase(d,(1200,90),'צ׳יפ תקין משנה את ההסתברות למפעל',
           'A good chip changes the posterior factory probability',lang,53,bold=True)
    phrase(d,(1200,195),'שני הצ׳יפים באותו ארגז שייכים לאותו מפעל',
           'Both chips in one box come from the same selected factory',lang,40)
    card(d,(800,290,1600,440),'P(A) = P(B) = 1/2')
    card(d,(400,575,900,720),'A',BLUE,60)
    card(d,(1500,575,2000,720),'B',BLUE,60)
    wire(d,[(970,440),(650,575)],width=6);wire(d,[(1430,440),(1750,575)],width=6)
    text(d,(720,465),'1/2',40);text(d,(1680,465),'1/2',40)
    leaves=[(300,'G1',GREEN),(950,'NOT G1',RED),(1450,'G1',GREEN),(2100,'NOT G1',RED)]
    for x,label,color in leaves:card(d,(x-190,930,x+190,1060),label,color,42)
    for start,end,label in [((550,720),(300,930),'PA'),((750,720),(950,930),'1 - PA'),
                            ((1650,720),(1450,930),'PB'),((1850,720),(2100,930),'1 - PB')]:
        wire(d,[start,end],color=GREEN if label in ('PA','PB') else RED,width=6)
        offset=-80 if label in ('PA','PB') else 80
        text(d,((start[0]+end[0])//2+offset,(start[1]+end[1])//2-25),label,38,bold=True)
    for x in (950,2100):
        d.line((x-130,955,x+130,1035),fill=RED,width=5)
        d.line((x-130,1035,x+130,955),fill=RED,width=5)
    phrase(d,(1200,1160),'מתנים באירוע שבו הצ׳יפ הראשון תקין',
           'Condition on the first chip being good',lang,40,bold=True,color=GREEN)
    text(d,(1200,1260),'P(A | G1) = PA/(PA+PB)      P(B | G1) = PB/(PA+PB)',42,bold=True)
    card(d,(220,1355,2180,1510),'P(G2 | G1) = (PA^2 + PB^2) / (PA + PB)',GREEN,49)
    phrase(d,(1200,1600),'אי תלות מותנית במפעל ולא לאחר ערבוב מפעלים',
           'Independence is conditional on factory, not on the mixed population',lang,38)
    return im


def hats(lang):
    im=Image.new('RGB',(2400,1700),'white');d=ImageDraw.Draw(im)
    phrase(d,(1200,90),'מאה כובעים והודעת זוגיות אחת',
           'One hundred hats and one parity message',lang,54,bold=True)
    phrase(d,(1200,190),'הדובר האחורי מתחיל וכולם שומעים את התשובות',
           'The rear speaker starts; everyone hears earlier replies',lang,41)
    positions=[300,750,1200,1650,2100]
    for x,label in zip(positions,['100','99','98','...','1']):
        card(d,(x-160,560,x+160,770),label,GREEN if label!='100' else BLUE,60)
    phrase(d,(300,835),'ראשון לדבר','first to speak',lang,35,bold=True,color=BLUE)
    phrase(d,(2100,835),'קדמת הטור','front of line',lang,35,bold=True)
    wire(d,[(300,530),(300,355),(2100,355),(2100,530)],color=BLUE,width=6)
    phrase(d,(1200,295),'האחורי רואה את כל הכובעים שלפניו',
           'The rear person sees all ninety-nine hats ahead',lang,38,color=BLUE)
    for x in positions[:-1]:wire(d,[(x+160,670),(x+290,670)],color=GREEN,width=6)
    phrase(d,(1200,955),'התשובה הראשונה היא הודעה ולא צבע כובע ידוע',
           'The first reply is a message, not a known true hat color',lang,41,bold=True)
    text(d,(1200,1060),'S = h1 XOR h2 XOR ... XOR h99',48,bold=True,color=BLUE)
    text(d,(1200,1170),'hi = S XOR heard_true_hats XOR visible_hats',44,bold=True,color=GREEN)
    phrase(d,(1200,1300),'כל דובר נוסף מבטל את הצבעים הידועים ומגלה את צבעו',
           'Each later speaker cancels known hats and recovers their own',lang,40)
    card(d,(380,1400,2020,1530),'',GREEN,45)
    phrase(d,(1200,1465),'תשעים ותשע מובטחות ולא ניתן להבטיח מאה',
           '99 guaranteed correct; 100 cannot be guaranteed',lang,43,bold=True,color=GREEN)
    phrase(d,(1200,1610),'לבן מקודד כאפס ואדום כאחד',
           'Agreed codes: white zero, red one',lang,39)
    return im


if __name__=='__main__':
    for language in ('he','en'):
        bayes(language).save(OUT/f'prep-308-bayes-factory-1108b20-{language}.png')
        hats(language).save(OUT/f'prep-096-hundred-parity-1108b20-{language}.png')
