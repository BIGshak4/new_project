"""Part 6: hierarchical box diagrams for two levels of conditional sum."""
import json
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, INK, BLUE, GREEN, PURPLE
from prep_034_recursive_carry_select import cost, delay, carry_select

root=Path(__file__).resolve().parents[1]
assert cost(32,2)==(72,44)
assert cost(16,1)==(24,9)
assert delay(32,2,1,1)==10
for a,b in [(0,0),(0xffff,1),(0xffffffff,1),(0x00ffffff,1),(0xffff0000,0xffff0000)]:
    s,c=carry_select(a,b,32,2)
    assert s+(c<<32)==a+b

def draw(path,title,subtitle,blocks,low_sum,carry,bundle,high_result,footers):
    d=Drawing(title,subtitle,1290)
    def route(points,color=INK,label=None,at=None):
        d.line(points,color,3)
        x,y=points[-1]
        if points[-2][0]==x:
            d.d.polygon([(x*2,y*2),((x-7)*2,(y-12)*2),((x+7)*2,(y-12)*2)],fill=color)
        else:
            d.arrow(x,y,color)
        if label:
            d.text(*at,label,27,color,bold=True)
    for y,title2,kind,description,abit,bbit,cin in blocks:
        d.rect(350,y,350,240)
        d.text(525,y+12,title2,26,BLUE,True,anchor='mt')
        d.text(525,y+90,kind,36,bold=True,anchor='mt')
        d.text(525,y+150,description,23,anchor='mt')
        for off,label,pin in [(50,abit,'A'),(120,bbit,'B'),(190,cin,'Cin')]:
            route([(75,y+off),(350,y+off)],label=label,at=(90,y+off-39))
            d.text(362,y+off,pin,21,anchor='lm')
    route([(700,245),(1790,245)],GREEN,low_sum,(1520,195))
    route([(700,355),(1420,355),(1420,595)],BLUE,carry,(790,308))
    pts=[(1280,570),(1560,620),(1560,960),(1280,1010),(1280,570)]
    d.d.polygon([(x*2,y*2) for x,y in pts],fill='#f6f9fc')
    d.line(pts,INK,3)
    d.text(1420,610,'SEL',25,BLUE,True,anchor='mt')
    d.text(1420,735,'MUX',34,bold=True,anchor='mt')
    d.text(1420,793,f'{bundle}-bit wide',25,bold=True,anchor='mt')
    d.text(1297,650,'I0',28,anchor='lm')
    d.text(1297,930,'I1',28,anchor='lm')
    route([(700,650),(1280,650)],PURPLE,f'R0  ({bundle} bits)',(825,601))
    route([(700,1000),(1090,1000),(1090,930),(1280,930)],PURPLE,f'R1  ({bundle} bits)',(800,1030))
    route([(1560,790),(1810,790)],GREEN,high_result,(1570,731))
    for y,text in zip([1160,1210,1260],footers):
        d.text(65,y,text,26)
    d.im.resize((1900,1290)).save(root/path)

outer='diagrams/prep-034-two-level-top.png'
inner='diagrams/prep-034-fast16-inside.png'
draw(outer,'Part 6 | Replace each RCA16 with a faster CS16',
     'Each CS16 contains three RCA8 blocks and a 9-bit MUX. See the second diagram.',
     [(180,'LOWER HALF','CS16','24 FAs + 9 MUXes','A[15:0]','B[15:0]','0'),
      (530,'UPPER: Cin = 0','CS16','24 FAs + 9 MUXes','A[31:16]','B[31:16]','0'),
      (880,'UPPER: Cin = 1','CS16','24 FAs + 9 MUXes','A[31:16]','B[31:16]','1')],
     'S[15:0]','C16',17,'C32, S[31:16]',
     ['Each CS16 is ready after 8t + d. The final MUX adds d: total delay = 8t + 2d.',
      'FA count: 3 x 24 = 72. One-bit MUX count: 3 x 9 + 17 = 44.',
      'All outputs include the final carry. d = one MUX delay; u = one-bit MUX area.'])
draw(inner,'Inside ONE CS16 | Three RCA8 blocks',
     'Local inputs: U[15:0], V[15:0], K. Outputs: Z[15:0], Cout. K is this block\'s carry-in.',
     [(180,'LOWER 8 BITS','RCA 8','8 full adders','U[7:0]','V[7:0]','K'),
      (530,'UPPER: Cin = 0','RCA 8','8 full adders','U[15:8]','V[15:8]','0'),
      (880,'UPPER: Cin = 1','RCA 8','8 full adders','U[15:8]','V[15:8]','1')],
     'Z[7:0]','c8',9,'Cout, Z[15:8]',
     ['All three RCA8 blocks compute in parallel; the lower carry c8 selects the upper result.',
      'Each candidate upper result has 8 sum bits + 1 carry bit, so selection is 9 bits wide.',
      'One CS16: delay = 8t + d; area = 24s + 9u. The full circuit uses THREE copies.'])

he='''סעיף 6 — שתי רמות של Conditional Sum: מחליפים כל אחד משלושת ה־RCA16 מסעיף 4 בבלוק CS16 מהיר. בתוך כל בלוק כזה שלושה RCA8: אחד לחצי התחתון עם נשא הכניסה K של הבלוק, ושניים לחצי העליון עם נשאי כניסה 0 ו־1. הנשא c8 מהתחתון בוחר את תוצאת החצי העליון במוקס ברוחב 9 ביט. שמונת ביטי הסכום התחתונים יוצאים ישירות. בקופסה הכללית U,V הם 16 ביטי הקלט המקומיים; הם אינם בהכרח 16 הביטים התחתונים של המילה המקורית.

במעגל הגדול משתמשים בשלושה CS16: לתחתון K=0; לעליון הראשון K=0 ולעליון השני K=1. המוקס האחרון ברוחב 17 ביט נשאר ובוחר לפי C16. כל CS16 מכיל 24 FA ו־9 מוקסים חד־ביטיים, ופועל בזמן 8t+d. לכן המעגל הגדול מכיל 72 FA ו־44 מוקסים חד־ביטיים, שטחו 72s+44u והשהייתו 8t+2d. שלושת מוקסי ה־9 ביט נמצאים בשלושה ענפים מקבילים, ולכן במסלול קריטי עוברים מוקס פנימי אחד ואז המוקס הסופי — לא את כל 44 המוקסים בטור. תשעת מחברי RCA8 מחשבים במקביל עבור הנחות הנשיאה שלהם.

השיפור לעומת 16t+d מותנה ב־d<8t. זו התקדמות טבעית לניתוח n רמות שבסעיף 7. אין צורך לעבור ל־Compound כדי לבצע את הצעד הזה; בתמונת הקורס Compound משפר את סדר הגודל של השטח ביחס ל־Conditional Sum, וההשוואה המדויקת דורשת חיווט ועלויות משלה. נוסחאות העלות כאן מתייחסות למבנה המשוכפל שצויר, ללא פישוטים או שיתוף לוגיקה נוספים.'''
en='''Part 6 replaces each of the three RCA16 instances with a CS16 made of three RCA8 blocks and a 9-bit selector. The local lower RCA8 gets the block carry-in K; upper candidates use zero and one. Its lower carry c8 selects 8 upper sum bits plus carry. The top-level three blocks receive K=0,0,1 respectively and feed the unchanged 17-bit selector controlled by C16. Each CS16 costs 24 FAs and 9 one-bit MUXes, delay 8t+d. Total is 72 FAs and 44 one-bit MUXes, area 72s+44u, delay 8t+2d. Each critical path traverses one local selector and the final selector, not every selector in series. Faster than one level only for d<8t. This is the course's Conditional Sum progression; no claim of globally minimal area or physical timing is made.'''
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-034"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
for asset in [outer,inner]:
    if not any(v.get('path')==asset for v in q['media_assets']):
        q['media_assets'].append({'type':'solution_diagram','path':asset,'description':'Part 6: two-level Conditional Sum with explicit CS16 hierarchy and 8-bit ripple leaves.'})
q['part_6_two_level_explanation']={'he':he,'en':en,'assets':[outer,inner],'FA_count':72,'one_bit_mux_count':44,'delay':'8*t+2*d','area':'72*s+44*u'}
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
after=json.loads(updated);assert before['questions'][:-1]==after['questions'][:-1]
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];text=md.read_text(encoding='utf-8')
if inner not in text:
    text+='\n\n## סעיף 6 — שתי רמות, עם קופסה פנימית מפורטת\n\n'+he+'\n\n![המעגל הגדול](../'+outer+')\n\n![פירוט קופסת CS16](../'+inner+')\n\n'+en+'\n'
    md.write_text(text,encoding='utf-8')
print('Part 6 diagrams saved, hierarchical costs checked, explanation attached.')
