"""Explicit pin-labelled RCA boxes; an ellipsis stands for FA2 through FA30."""
import json
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN

root=Path(__file__).resolve().parents[1]
asset='diagrams/prep-034-32-bit-rca-boxes.png'
d=Drawing('32-bit Ripple Carry Adder | 32 full adders', 'Start at bit 0 (LSB). Each carry-out feeds the carry-in of the next full adder.', 820)

def down_arrow(x,y,color):
    d.d.polygon([(x*2,y*2),((x-7)*2,(y-12)*2),((x+7)*2,(y-12)*2)],fill=color)

for x,i in [(220,0),(680,1),(1400,31)]:
    d.rect(x,300,280,250)
    d.text(x+140,365,f'FA{i}',36,bold=True,anchor='mt')
    d.text(x+15,435,'Cin',24,BLUE,True,anchor='lm')
    d.text(x+265,435,'Cout',24,BLUE,True,anchor='rm')
    for off,name in [(70,'A'),(210,'B')]:
        d.text(x+off,155,f'{name}{i}',32,bold=True,anchor='mt')
        d.line([(x+off,205),(x+off,300)])
        down_arrow(x+off,300,'#26374a')
        d.text(x+off,315,name,25,anchor='mt')
    d.text(x+140,510,'S',28,GREEN,True,anchor='mt')
    d.line([(x+140,550),(x+140,660)],GREEN)
    down_arrow(x+140,660,GREEN)
    d.text(x+140,674,f'S{i}',32,GREEN,True,anchor='mt')

for a,b,label in [(65,220,'C0 = 0'),(500,680,'C1'),(960,1070,'C2'),(1240,1400,'C31'),(1680,1830,'C32')]:
    d.line([(a,435),(b,435)],BLUE)
    if b!=1070:
        d.arrow(b,435,BLUE)
    d.text((a+b)/2,384,label,27,BLUE,True,anchor='mt')
for x in range(1070,1240,28):
    d.line([(x,435),(min(x+14,1240),435)],BLUE)
d.text(1150,480,'FA2 ... FA30',25,anchor='mt')
d.text(1150,520,'29 more full adders',22,anchor='mt')
d.text(65,753,'Full unsigned result: C32 S31 S30 ... S1 S0  (33 bits)',30,GREEN,True)
d.im.resize((1900,820)).save(root/asset)

p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-034"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
if not any(v.get('path')==asset for v in q['media_assets']):
    q['media_assets'].append({'type':'solution_diagram','path':asset,'description':'Part 2: RCA32, labelled A/B/S/Cin/Cout pins, initial carry zero, and explicit omission of FA2..FA30.'})
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
after=json.loads(updated);assert before['questions'][:-1]==after['questions'][:-1]
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];text=md.read_text(encoding='utf-8')
if asset not in text:
    text+='\n\n## סעיף 2 — שרטוט RCA בקופסאות\n\n![מחבר 32 ביט עם נשא מתפשט](../'+asset+')\n\nFA0 מטפל בביטים הפחות משמעותיים ו־FA31 בביטים המשמעותיים ביותר. הקו המקווקו מחליף בציור 29 מחברים נוספים, FA2 עד FA30, ולא מייצג חוט שמדלג עליהם. בחיבור A+B מחברים C0 ל־0. אם יש נשא חיצוני מחברים אותו במקום 0. המוצא המלא ללא סימן כולל 33 ביט: C32 ואחריו S31 עד S0. השמות A0 וכו׳ מציינים חוט ביט יחיד, לא ערך קבוע.\n'
    md.write_text(text,encoding='utf-8')
print(root/asset)
