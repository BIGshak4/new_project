"""Part 4: three RCA16 boxes and a 17-bit selector; attach cost clarification."""
import json
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, INK, BLUE, GREEN, PURPLE

root=Path(__file__).resolve().parents[1]
asset='diagrams/prep-034-one-level-conditional-sum.png'
d=Drawing('Parts 4-5 | Compute both upper-half possibilities', 'Three 16-bit ripple adders work in parallel. C16 selects the correct upper result.', 1260)

def route(points,color=INK,label=None,at=None):
    d.line(points,color,3)
    x,y=points[-1]
    if len(points)>1 and points[-2][0]==x:
        # Current uses are downward signal arrows.
        d.d.polygon([(x*2,y*2),((x-7)*2,(y-12)*2),((x+7)*2,(y-12)*2)],fill=color)
    else:
        d.arrow(x,y,color)
    if label:
        d.text(*at,label,27,color,bold=True)

for y,title,abit,bbit,cin in [(180,'LOWER HALF','A[15:0]','B[15:0]','0'),(530,'UPPER: Cin = 0','A[31:16]','B[31:16]','0'),(880,'UPPER: Cin = 1','A[31:16]','B[31:16]','1')]:
    d.rect(350,y,350,240)
    d.text(525,y+12,title,27,BLUE,True,anchor='mt')
    d.text(525,y+92,'RCA 16',36,bold=True,anchor='mt')
    d.text(525,y+148,'16 full adders',25,anchor='mt')
    for off,label,pin in [(50,abit,'A'),(120,bbit,'B'),(190,cin,'Cin')]:
        route([(75,y+off),(350,y+off)],label=label,at=(90,y+off-39))
        d.text(362,y+off,pin,21,anchor='lm')

route([(700,245),(1790,245)],GREEN,'S[15:0]',(1570,195))
d.text(713,265,'16 bits',22,GREEN)
route([(700,355),(1420,355),(1420,595)],BLUE,'C16',(790,308))

# Data selector, with top select pin so the carry wire need not cross data.
pts=[(1280,570),(1560,620),(1560,960),(1280,1010),(1280,570)]
d.d.polygon([(x*2,y*2) for x,y in pts],fill='#f6f9fc')
d.line(pts,INK,3)
d.text(1420,610,'SEL',25,BLUE,True,anchor='mt')
d.text(1420,735,'MUX',34,bold=True,anchor='mt')
d.text(1420,793,'17-bit wide',25,bold=True,anchor='mt')
d.text(1297,650,'I0',28,anchor='lm')
d.text(1297,930,'I1',28,anchor='lm')
route([(700,650),(1280,650)],PURPLE,'R0  (17 bits)',(825,601))
route([(700,1000),(1090,1000),(1090,930),(1280,930)],PURPLE,'R1  (17 bits)',(800,1030))
route([(1560,790),(1810,790)],GREEN,'C32, S[31:16]',(1570,734))
d.text(1580,815,'17 output bits',23,GREEN)
d.text(65,1160,'R0 and R1 each contain 16 sum bits plus the carry-out of their upper-half adder.',27)
d.text(65,1210,'One 17-bit-wide MUX = 17 one-bit 2:1 MUXes, all controlled by C16.',27,BLUE,True)
d.im.resize((1900,1260)).save(root/asset)

p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-034"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
if not any(v.get('path')==asset for v in q['media_assets']):
    q['media_assets'].append({'type':'solution_diagram','path':asset,'description':'Three RCA16 blocks, speculative upper carries 0/1 and C16-controlled 17-bit selector; includes final carry-out.'})
q['part_5_cost_model']={'FA_count':48,'one_bit_mux_count':17,'delay':'16*t + d','area':'48*s + 17*u','symbols':{'t':'one-bit FA delay','s':'one-bit FA area','d':'one-bit 2:1 MUX delay','u':'one-bit 2:1 MUX area'},'assumptions':'Parallel upper speculation; one mux stage; 33-bit full unsigned output; ignore wire/fanout delay. MUX cost not provided by original source.'}
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
after=json.loads(updated);assert before['questions'][:-1]==after['questions'][:-1]
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];text=md.read_text(encoding='utf-8')
if asset not in text:
    text+='\n\n## סעיפים 4–5 — שרטוט מפורש ועלות המוקסים\n\n![שלושה מחברי 16 ביט ובחירת תוצאת החצי העליון](../'+asset+')\n\nבשרטוט המוקס הוא ברוחב 17 ביט: 16 ביטי סכום עליונים ועוד נשא יציאה. לכן השטחים נסכמים ל־48s+17u, אך המוקסים פועלים במקביל ולכן מוסיפים שלב השהיה אחד d בלבד. שלושת המחברים מסיימים במודל אחרי 16t; אחר כך מתבצעת הבחירה, והתוצאה המלאה מוכנה אחרי 16t+d. השיפור לעומת 32t מתקבל אם d<16t. ללא נתוני מוקס אין מספר מדויק לשטח ולהשהיה מתוך t,s בלבד. אין צורך במחזור שעון, ברגיסטרים או בשערי פיצול לשני עותקי החצי העליון; חיבור אותם ביטים לשתי כניסות הוא fanout שמודל העלות הפשוט אינו מתמחר.\n'
    md.write_text(text,encoding='utf-8')
print(root/asset)
