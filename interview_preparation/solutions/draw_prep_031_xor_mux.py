"""Pin-labelled two-MUX XOR using constant zero only; link saved diagram."""
import json
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN, INK

root=Path(__file__).resolve().parents[1]
asset='diagrams/prep-031-xor-two-mux.png'
d=Drawing('XOR | Two 2:1 MUXes, constant 0 only', 'S=0 selects I0. S=1 selects I1. Repeated a / b labels denote the same input signal.', 770)

def mux(x,y,name,select):
    points=[(x,y),(x+280,y+50),(x+280,y+290),(x,y+340),(x,y)]
    d.d.polygon([(a*2,b*2) for a,b in points],fill='#f6f9fc')
    d.line(points,INK,3)
    d.text(x+140,y-65,name,34,bold=True,anchor='mt')
    d.text(x+20,y+85,'I0',28,anchor='lm')
    d.text(x+20,y+255,'I1',28,anchor='lm')
    d.text(x+245,y+170,'Q',28,anchor='rm')
    d.text(x+140,y+285,'S',30,BLUE,True,anchor='mt')
    d.line([(x+140,y+435),(x+140,y+315)],BLUE)
    d.text(x+140,y+447,select,35,BLUE,True,anchor='mt')

mux(330,220,'MUX 1','b')
mux(1180,220,'MUX 2','a')
for x,y,label in [(330,305,'a'),(330,475,'0'),(1180,305,'b')]:
    d.line([(x-180,y),(x,y)])
    d.arrow(x,y)
    d.text(x-170,y-48,label,36,GREEN,True)
d.line([(610,390),(900,390),(900,475),(1180,475)],GREEN)
d.arrow(1180,475,GREEN)
d.text(745,340,'t',34,GREEN,True)
d.line([(1460,390),(1790,390)],GREEN)
d.arrow(1790,390,GREEN)
d.text(1500,338,'Y = a XOR b',32,GREEN,True)
d.im.resize((1900,770)).save(root/asset)

p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-031"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
if not any(v['path']==asset for v in q['media_assets']):
    q['media_assets'].append({'type':'solution_diagram','path':asset,'description':'Pin-labelled two-MUX XOR, with selects b and a and constant zero only.'})
    updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
    after=json.loads(updated)
    assert before['questions'][:-1]==after['questions'][:-1]
    p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];text=md.read_text(encoding='utf-8')
if asset not in text:
    text += '\n\n## שרטוט המימוש בשני מוקסים\n\n![XOR עם שני מוקסים וקבוע 0](../'+asset+')\n\nכניסות בעלות אותו שם הן אותו אות; I0 נבחרת כשהסלקטור 0 ו־I1 כשהוא 1.\n'
    md.write_text(text,encoding='utf-8')
print(root/asset)
