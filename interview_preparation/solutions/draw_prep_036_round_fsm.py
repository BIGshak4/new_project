"""Redraw the verified FSM as circular states and curved transitions."""
import json
import math
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from register_prep_036 import STANDARD, POSITIVE

ROOT=Path(__file__).resolve().parents[1]
SCALE=2
INK='#23354d'; BLUE='#326caa'; GREEN='#12836f'; GRAY='#64748b'; PURPLE='#8a63b8'

class Canvas:
    def __init__(self,height,title,subtitle):
        self.height=height
        self.im=Image.new('RGB',(1900*SCALE,height*SCALE),'#ffffff')
        self.d=ImageDraw.Draw(self.im)
        self.text(90,45,title,42,INK,True)
        self.text(90,106,subtitle,25,GRAY)

    def font(self,size,bold=False):
        return ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),size*SCALE)

    def text(self,x,y,text,size=28,color=INK,bold=False,anchor=None):
        self.d.text((x*SCALE,y*SCALE),text,font=self.font(size,bold),fill=color,anchor=anchor)

    def line(self,points,color=BLUE,width=3):
        self.d.line([(x*SCALE,y*SCALE) for x,y in points],fill=color,width=width*SCALE,joint='curve')

    def head(self,end,previous,color=BLUE):
        x,y=end; px,py=previous
        length=math.hypot(x-px,y-py); ux=(x-px)/length; uy=(y-py)/length
        pts=[(x,y),(x-17*ux-7*uy,y-17*uy+7*ux),(x-17*ux+7*uy,y-17*uy-7*ux)]
        self.d.polygon([(a*SCALE,b*SCALE) for a,b in pts],fill=color)

    def curve(self,p0,p1,p2,p3,label=None,label_at=None,color=BLUE):
        pts=[]
        for i in range(161):
            t=i/160
            pts.append(tuple((1-t)**3*p0[k]+3*(1-t)**2*t*p1[k]+3*(1-t)*t*t*p2[k]+t**3*p3[k] for k in (0,1)))
        self.line(pts,color)
        self.head(pts[-1],pts[-4],color)
        if label:
            self.pill(*label_at,label,color)

    def pill(self,x,y,label,color=BLUE):
        font=self.font(26,True)
        width=self.d.textlength(label,font=font)/SCALE+30
        self.d.rounded_rectangle(((x-width/2)*SCALE,(y-23)*SCALE,(x+width/2)*SCALE,(y+23)*SCALE),radius=15*SCALE,fill='white')
        self.text(x,y,label,26,color,True,'mm')

    def state(self,x,y,name,out,desc):
        color=GREEN if out else BLUE
        radius=105
        self.d.ellipse(((x-radius)*SCALE,(y-radius)*SCALE,(x+radius)*SCALE,(y+radius)*SCALE),fill='#eff9f5' if out else '#f3f7fc',outline=color,width=3*SCALE)
        self.text(x,y-47,name,42,color,True,'mm')
        self.line([(x-70,y-13),(x+70,y-13)],'#cde4db' if out else '#d4e1f0',2)
        self.text(x,y+20,f'Y = {out}',30,color,True,'mm')
        self.text(x,y+60,desc,20,GRAY,False,'mm')

    def save(self,path):
        self.im.resize((1900,self.height),Image.Resampling.LANCZOS).save(ROOT/path)

def shared(c,y):
    for x,name,out in [(400,'R0',1),(950,'R1',0),(1500,'R2',0)]:
        c.state(x,y,name,out,'remainder '+name[-1])
    # Points are on the circle at +/-30 degrees, to within <0.05 pixels.
    dx=105*math.cos(math.pi/6); dy=52.5
    for left,right,label in [(400,950,'x = 1'),(950,1500,'x = 0')]:
        c.curve((left+dx,y-dy),(left+195,y-205),(right-195,y-205),(right-dx,y-dy),label,((left+right)/2,y-176))
        c.curve((right-dx,y+dy),(right-195,y+205),(left+195,y+205),(left+dx,y+dy),label,((left+right)/2,y+176))
    side=105/math.sqrt(2)
    for x,label in [(400,'x = 0'),(1500,'x = 1')]:
        c.curve((x+side,y-side),(x+215,y-355),(x-215,y-355),(x-side,y-side),label,(x,y-293))

normal='diagrams/prep-036-remainder-fsm-round.png'
positive='diagrams/prep-036-positive-fsm-round.png'
c=Canvas(900,'Binary divisibility by 3','Moore machine  /  input on arrows  /  output inside each state')
shared(c,510)
c.text(950,820,'Includes zero: start in R0. Read Y after each input bit is clocked in.',27,GRAY,False,'mm')
c.save(normal)

c=Canvas(1100,'Positive multiples of 3','Matches the supplied example  /  Z separates zero from positive multiples')
shared(c,745)
c.state(950,290,'Z',0,'value is zero')
c.curve((950,395),(950,465),(950,560),(950,640),'x = 1',(950,520))
dx=105*math.cos(math.pi/6)
c.curve((950+dx,237.5),(1330,100),(1330,480),(950+dx,342.5),'x = 0',(1260,290))
c.text(950,1010,'Input:  0  1  0  0  1     |     Output:  0  0  0  0  1',29,INK,False,'mm')
c.text(950,1060,'Only R0 has Y = 1. The remainder transitions are unchanged.',24,GRAY,False,'mm')
c.save(positive)

assert STANDARD=={'R0':('R0','R1'),'R1':('R2','R0'),'R2':('R1','R2')}
assert POSITIVE=={'Z':('Z','R1'),**STANDARD}
reference='sources/prep-036-round-state-style-reference.png'
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-a2c154c5-d813-425d-be10-fd976c526feb.png',ROOT/reference)
p=ROOT/'questions.json'; raw=p.read_text(encoding='utf-8'); before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-036"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
for asset,kind in [(normal,'solution_diagram'),(positive,'solution_diagram'),(reference,'style_reference_image')]:
    if not any(v.get('path')==asset for v in q['media_assets']):
        q['media_assets'].append(dict(type=kind,path=asset,description='Circular states and curved arrows. Solution diagrams retain Moore outputs inside states; supplied reference uses Mealy edge notation.'))
if not any(v.get('path')==reference for v in q['sources']):
    q['sources'].append(dict(type='user_supplied_style_reference',path=reference,received_on='2026-09-29',description='Visual style reference only; not a request to replace the Moore model with Mealy.'))
q['preferred_solution_diagrams']=[normal,positive]
q['diagram_style_note']='For FSM diagrams use circular states and curved transitions; keep component schematics as labeled boxes. Preserve output semantics independently from visual reference style. Omit RESET arrows from these diagrams at user request; the defined initial states remain R0 and Z respectively.'
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
assert json.loads(updated)['questions'][:-1]==before['questions'][:-1]
p.write_text(updated,encoding='utf-8')
md=ROOT/q['markdown_path']; body=md.read_text(encoding='utf-8')
if normal not in body:
    body+='\n\n## השרטוטים המועדפים — מצבים עגולים וחצים מעוגלים\n\nלפי בקשת המשתמש, מכונות מצבים מוצגות בעיגולים ובחצים מעוגלים. שרטוטי רכיבים יישארו בקופסאות. תמונת הסגנון משתמשת בסימון Mealy על החצים; הפתרונות שלנו נשארים Moore והמוצא בתוך המצב.\n\n![התחלקות רגילה](../'+normal+')\n\n![כפולות חיוביות בלבד](../'+positive+')\n\n![תמונת סגנון מקורית](../'+reference+')\n'
    md.write_text(body,encoding='utf-8')
readme=ROOT/'README.md'; text=readme.read_text(encoding='utf-8')
note='העדפת שרטוט FSM: מצבים בעיגולים וחצי מעברים מעוגלים, עם תוויות קריאות ומרווחים. ההעדפה לקופסאות נשארת עבור רכיבי חומרה. אין לשנות בין Moore ל־Mealy רק כדי לחקות סגנון של תמונת ייחוס.'
if note not in text: readme.write_text(text+'\n'+note+'\n',encoding='utf-8')
print('Round FSM diagrams generated, reference preserved, preference saved. Other 35 records unchanged.')
