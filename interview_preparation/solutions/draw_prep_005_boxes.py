"""Box-and-wire sorting schematics, with explicit pins and orthogonal routes."""
import json
import shutil
from itertools import permutations, product
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, INK, BLUE, GREEN, PURPLE

root=Path(__file__).resolve().parents[1]
assets=[]

def pair(a,b):
    return max(a,b),min(a,b)

def boxed4(a,b,c,d):
    M1,m1=pair(a,b); M2,m2=pair(c,d)
    y1,p=pair(M1,M2); q,y4=pair(m1,m2)
    y2,y3=pair(p,q)
    return y1,y2,y3,y4

def boxed6(a,b,c,d,e,f):
    u1,u2,u3,u4=boxed4(a,b,c,d)
    M,m=pair(e,f)
    v1,p=pair(u3,M); q,y6=pair(u4,m)
    v2,y5=pair(p,q)
    y1,p=pair(u1,v1); q,y4=pair(u2,v2)
    y2,y3=pair(p,q)
    return y1,y2,y3,y4,y5,y6

for values in list(permutations(range(4)))+list(product((0,1),repeat=4)):
    assert boxed4(*values)==tuple(sorted(values,reverse=True))
for values in list(permutations(range(6)))+list(product((0,1),repeat=6)):
    assert boxed6(*values)==tuple(sorted(values,reverse=True))

def wire(d,pts,label=None,at=None,color=INK):
    d.line(pts,color,3)
    d.arrow(*pts[-1],color)
    if label:
        d.text(*at,label,29,color,bold=True)

def cell(d,x,y,name):
    d.rect(x,y,220,180)
    d.text(x+110,y+15,name,27,BLUE,True,anchor='mt')
    d.text(x+110,y+72,'2 x 2',29,bold=True,anchor='mt')
    for off,label in [(50,'MAX'),(130,'MIN')]:
        d.text(x+207,y+off,label,21,GREEN,True,anchor='rm')
    for off in [50,130]:
        d.text(x+12,y+off,'in',20,anchor='lm')

def save(d,name,height):
    path='diagrams/'+name
    d.im.resize((1900,height)).save(root/path)
    assets.append(path)

# A: the conventional five-comparator drawing, similar to the supplied reference.
d=Drawing('A. Sort four values | Five 2 x 2 boxes', 'Each box outputs MAX above MIN. Arrows show signal direction.', 1160)
for args in [(250,260,'C1'),(250,700,'C2'),(850,180,'C3'),(850,780,'C4'),(1370,470,'C5')]:
    cell(d,*args)
for x,y,label in [(250,310,'a'),(250,390,'b'),(250,750,'c'),(250,830,'d')]:
    wire(d,[(80,y),(x,y)],label,(100,y-43))
wire(d,[(470,310),(670,310),(670,230),(850,230)],'M1',(500,263))
wire(d,[(470,390),(740,390),(740,830),(850,830)],'m1',(500,417))
wire(d,[(470,750),(700,750),(700,310),(850,310)],'M2',(500,701))
wire(d,[(470,830),(620,830),(620,910),(850,910)],'m2',(500,860))
# Bridge on the horizontal m1 wire: it does not join vertical M2.
d.line([(682,390),(718,390)],'white',8)
d.d.arc((682*2,372*2,718*2,408*2),180,360,fill=INK,width=6)
wire(d,[(1070,230),(1790,230)],'Y1 = MAX(M1, M2)',(1310,180),GREEN)
wire(d,[(1070,310),(1220,310),(1220,520),(1370,520)],'p',(1100,266))
wire(d,[(1070,830),(1260,830),(1260,600),(1370,600)],'q',(1100,785))
wire(d,[(1070,910),(1790,910)],'Y4 = MIN(m1, m2)',(1310,940),GREEN)
wire(d,[(1590,520),(1790,520)],'Y2',(1690,472),GREEN)
wire(d,[(1590,600),(1790,600)],'Y3',(1690,626),GREEN)
d.text(65,1010,'M1 = MAX(a,b)     m1 = MIN(a,b)     M2 = MAX(c,d)     m2 = MIN(c,d)',27)
d.text(65,1060,'p = MIN(M1,M2)     q = MAX(m1,m2)     Y2 = MAX(p,q)     Y3 = MIN(p,q)',27)
d.text(65,1110,'The small wire bridge marks a crossing WITHOUT a connection.',25,BLUE)
save(d,'prep-005-boxes-four.png',1160)

# B: three explicitly ported four-input boxes; bypass wires route around boxes.
d=Drawing('B. Sort six values | Three copies of the four-input box', 'Every S4 box contains the complete five-comparator circuit from part A.', 1030)
for x,y,name in [(300,220,'S4-A'),(840,480,'S4-B'),(1380,220,'S4-C')]:
    d.rect(x,y,240,400)
    d.text(x+120,y+145,name,35,BLUE,True,anchor='mt')
    d.text(x+120,y+205,'4 x 4',32,bold=True,anchor='mt')
    for k,off in enumerate([80,160,240,320],1):
        d.text(x+12,y+off,str(k),22,anchor='lm')
        d.text(x+227,y+off,str(k),22,anchor='rm')
for k,y in enumerate([300,380,460,540],1):
    wire(d,[(70,y),(300,y)],f'x{k}',(100,y-43))
wire(d,[(540,300),(1380,300)],'u1',(630,253))
wire(d,[(540,380),(1380,380)],'u2',(630,407))
wire(d,[(540,460),(700,460),(700,560),(840,560)],'u3',(570,485))
wire(d,[(540,540),(660,540),(660,640),(840,640)],'u4',(565,565))
wire(d,[(70,760),(740,760),(740,720),(840,720)],'x5',(100,717))
wire(d,[(70,840),(780,840),(780,800),(840,800)],'x6',(100,797))
wire(d,[(1080,560),(1180,560),(1180,460),(1380,460)],'v1',(1110,586))
wire(d,[(1080,640),(1230,640),(1230,540),(1380,540)],'v2',(1110,667))
for k,y in enumerate([300,380,460,540],1):
    wire(d,[(1620,y),(1790,y)],f'Y{k}',(1670,y-43),GREEN)
wire(d,[(1080,720),(1790,720)],'Y5  (second smallest)',(1370,669),GREEN)
wire(d,[(1080,800),(1790,800)],'Y6  (smallest)',(1370,828),GREEN)
d.text(65,937,'S4-A sorts wires 1-4; S4-B sorts wires 3-6; S4-C sorts wires 1-4 again.',27)
d.text(65,983,'Three physical boxes: 5 + 5 + 5 = 15 comparators. Output is largest to smallest.',27,GREEN)
save(d,'prep-005-boxes-six.png',1030)

# C1: open second block after removing its already-ordered first pair.
d=Drawing('C. Improved second block | Four comparators', 'u3 and u4 are already ordered: u3 >= u4. Their comparison is replaced by wires.', 1020)
for args in [(250,540,'C6'),(850,210,'C7'),(850,700,'C8'),(1370,470,'C9')]:
    cell(d,*args)
wire(d,[(700,260),(850,260)],'u3',(705,213))
wire(d,[(700,750),(850,750)],'u4',(705,700))
wire(d,[(80,590),(250,590)],'x5',(100,543))
wire(d,[(80,670),(250,670)],'x6',(100,697))
wire(d,[(470,590),(640,590),(640,340),(850,340)],'MAX(x5,x6)',(500,610))
wire(d,[(470,670),(690,670),(690,830),(850,830)],'MIN(x5,x6)',(500,856))
wire(d,[(1070,260),(1790,260)],'v1 -> last S4',(1440,211),GREEN)
wire(d,[(1070,340),(1220,340),(1220,520),(1370,520)])
wire(d,[(1070,750),(1260,750),(1260,600),(1370,600)])
wire(d,[(1070,830),(1790,830)],'Y6  (smallest)',(1440,861),GREEN)
wire(d,[(1590,520),(1790,520)],'v2',(1690,472),GREEN)
wire(d,[(1590,600),(1790,600)],'Y5',(1690,626),GREEN)
d.text(65,945,'v1 and v2 feed the last block. Y5 and Y6 are already in their final positions.',27)
d.text(65,988,'Removed: the comparator on u3,u4. Each remaining box still outputs MAX above MIN.',25,BLUE)
save(d,'prep-005-boxes-pruned-second.png',1020)

# C2: final merge of two already ordered pairs.
d=Drawing('C. Improved last block | Three comparators', 'Known on entry: u1 >= u2 and v1 >= v2. Both initial pair comparisons are removed.', 980)
for args in [(400,240,'C10'),(400,660,'C11'),(1170,450,'C12')]:
    cell(d,*args)
for y,label in [(290,'u1'),(370,'v1'),(710,'u2'),(790,'v2')]:
    wire(d,[(120,y),(400,y)],label,(160,y-43))
wire(d,[(620,290),(1790,290)],'Y1',(1690,243),GREEN)
wire(d,[(620,370),(920,370),(920,500),(1170,500)],'MIN(u1,v1)',(650,397))
wire(d,[(620,710),(970,710),(970,580),(1170,580)],'MAX(u2,v2)',(650,661))
wire(d,[(620,790),(1790,790)],'Y4',(1690,821),GREEN)
wire(d,[(1390,500),(1790,500)],'Y2',(1690,453),GREEN)
wire(d,[(1390,580),(1790,580)],'Y3',(1690,609),GREEN)
d.text(65,915,'Total optimized circuit: first block (5) + second block (4) + last block (3) = 12 comparators.',27,GREEN,True)
save(d,'prep-005-boxes-pruned-last.png',980)

# Preserve the user's style reference and attach the replacement diagram set.
source='sources/prep-005-box-diagram-style-reference.png'
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-2c5d9af7-20d5-47c8-9c54-bd42061f5d1d.png',root/source)
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-005"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
for asset in assets:
    if not any(x.get('path')==asset for x in q.setdefault('media_assets',[])):
        q['media_assets'].append({'type':'solution_diagram','path':asset,'description':'Preferred box-and-wire schematic with labelled pins, elbow routing and MAX/MIN outputs.'})
if not any(x.get('path')==source for x in q['media_assets']):
    q['media_assets'].append({'type':'user_supplied_diagram_reference','path':source,'description':'User-supplied reference for preferred box-and-wire drawing style; not a new question.'})
q['preferred_solution_diagrams']=assets
q['diagram_style']='Explicit rectangular component boxes, labelled input/output pins, orthogonal wires, bridge on unconnected crossings; avoid comparator-dot rail notation.'
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
after=json.loads(updated)
assert all(a==b for a,b in zip(before['questions'],after['questions']) if a['id']!='PREP-005')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];text=md.read_text(encoding='utf-8')
if assets[-1] not in text:
    text+='\n\n## שרטוטים מועדפים — קופסאות וחיבורים מפורשים\n\nאותו מעגל ופתרון, עם קופסאות Max/Min, חיבורים בזוויות וקשת בחצייה ללא חיבור. שרטוטי סעיף ג׳ מציגים בנפרד את הממיין השני והשלישי לאחר הסרת משווים; הממיין הראשון נשאר הממיין בן חמשת הרכיבים שבסעיף א׳. הכניסות u1,u2 הן שני מוצאי הממיין הראשון העליונים; v1,v2 הם שני מוצאי הממיין השני העליונים.\n\n'
    text+='\n\n'.join('![שרטוט קופסאות '+str(i)+'](../'+asset+')' for i,asset in enumerate(assets,1))
    text+='\n\n[תמונת סגנון שסיפק המשתמש](../'+source+')\n'
    md.write_text(text,encoding='utf-8')
r=root/'README.md';text=r.read_text(encoding='utf-8')
pref='העדפת שרטוט: להציג רכיבים כקופסאות עם כניסות ומוצאים מסומנים, חיבורים בזוויות ושמות אותות; לסמן בבירור חציות ללא חיבור. להימנע מסימון רשת מיון באמצעות קווים אנכיים ושתי נקודות בלבד.'
if pref not in text:
    r.write_text(text+'\n'+pref+'\n',encoding='utf-8')
print('Saved four preferred box-and-wire schematics and user style reference; bank linked.')
