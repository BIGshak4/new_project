"""Exact state diagrams: serial remainder and positive-multiple variants."""
import json
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, INK, BLUE, GREEN, PURPLE
from register_prep_036 import STANDARD, POSITIVE

ROOT=Path(__file__).resolve().parents[1]

def arrow(d,points,label=None,at=None,color=BLUE):
    d.line(points,color,3)
    x,y=points[-1]; px,py=points[-2]
    if x>px: tri=[(x,y),(x-13,y-7),(x-13,y+7)]
    elif x<px: tri=[(x,y),(x+13,y-7),(x+13,y+7)]
    elif y>py: tri=[(x,y),(x-7,y-13),(x+7,y-13)]
    else: tri=[(x,y),(x-7,y+13),(x+7,y+13)]
    d.d.polygon([(a*2,b*2) for a,b in tri],fill=color)
    if label: d.text(*at,label,29,color,True)

def state(d,x,y,name,meaning,out):
    d.rect(x,y,300,180)
    d.text(x+150,y+16,name,36,INK,True,'mt')
    d.text(x+150,y+76,meaning,25,INK,False,'mt')
    d.text(x+150,y+122,f'Y = {out}',29,GREEN if out else INK,True,'mt')

def base(d,y):
    for x,name,meaning,out in [(200,'R0','remainder 0',1),(800,'R1','remainder 1',0),(1400,'R2','remainder 2',0)]:
        state(d,x,y,name,meaning,out)
    arrow(d,[(500,y+50),(800,y+50)],'x = 1',(590,y+9))
    arrow(d,[(800,y+130),(500,y+130)],'x = 1',(590,y+139))
    arrow(d,[(1100,y+50),(1400,y+50)],'x = 0',(1190,y+9))
    arrow(d,[(1400,y+130),(1100,y+130)],'x = 0',(1190,y+139))
    for x,label in [(200,'x = 0'),(1400,'x = 1')]:
        arrow(d,[(x+65,y),(x+65,y-110),(x+235,y-110),(x+235,y)],label,(x+95,y-155))

ordinary='diagrams/prep-036-remainder-fsm.png'
positive='diagrams/prep-036-positive-fsm.png'
d=Drawing('Divisible by 3 | Standard mathematical definition',
          'Moore FSM: each arrow consumes one input bit x. The new state determines Y after the clock edge.',900)
base(d,410)
arrow(d,[(350,730),(350,590)],'RESET',(240,745),PURPLE)
d.text(65,815,'Zero is divisible by 3: reset to R0, and Y = 1 for an all-zero prefix.',28)
d.save(Path(ordinary).name)

d=Drawing('Positive multiples of 3 | Matches the supplied example',
          'Z distinguishes value zero from positive values with remainder zero. All other transitions are unchanged.',1120)
base(d,650)
state(d,800,225,'Z','value is still 0',0)
arrow(d,[(950,405),(950,650)],'x = 1',(980,485))
arrow(d,[(1100,270),(1250,270),(1250,360),(1100,360)],'x = 0',(1270,290))
arrow(d,[(520,315),(800,315)],'RESET',(555,264),PURPLE)
d.text(65,940,'Input bits:       0       1       0       0       1',30)
d.text(65,990,'States:            Z      R1      R2      R1      R0',30)
d.text(65,1040,'Output Y:        0       0       0       0       1',30,GREEN,True)
d.save(Path(positive).name)

# Confirm labels used in the shared base and extra zero state.
assert STANDARD=={'R0':('R0','R1'),'R1':('R2','R0'),'R2':('R1','R2')}
assert POSITIVE=={'Z':('Z','R1'),**STANDARD}
p=ROOT/'questions.json'; raw=p.read_text(encoding='utf-8'); before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-036"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
for asset in (ordinary,positive):
    if not any(v.get('path')==asset for v in q['media_assets']):
        q['media_assets'].append(dict(type='solution_diagram',path=asset,description='Moore FSM with explicit input-labelled transitions, reset and state outputs.'))
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
assert json.loads(updated)['questions'][:-1]==before['questions'][:-1]
p.write_text(updated,encoding='utf-8')
md=ROOT/q['markdown_path']; body=md.read_text(encoding='utf-8')
if ordinary not in body:
    body+='\n\n## שרטוטי מכונת המצבים\n\nכל חץ מסומן בביט הכניסה, ובכל קופסה רשום המוצא של המצב.\n\n![התחלקות רגילה, כולל אפס](../'+ordinary+')\n\n![כפולות חיוביות, בהתאם לדוגמה](../'+positive+')\n'
    md.write_text(body,encoding='utf-8')
print('Both FSM diagrams saved and attached to PREP-036; earlier questions unchanged.')
