"""Draw and verify all three sorting parts, consistently MAX above MIN."""
import json
import shutil
from itertools import permutations, product
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, INK, BLUE, GREEN, PURPLE

root=Path(__file__).resolve().parents[1]
out=root/'diagrams'
sort4=[(1,2),(3,4),(1,3),(2,4),(2,3)]
full=sort4+[(3,4),(5,6),(3,5),(4,6),(4,5)]+sort4
removed={5,10,11}
opt=[v for i,v in enumerate(full) if i not in removed]
def run(values, net, check_removed=False):
    v=list(values)
    for k,(i,j) in enumerate(net):
        if check_removed and k in removed:
            assert v[i-1]>=v[j-1]
        v[i-1],v[j-1]=max(v[i-1],v[j-1]),min(v[i-1],v[j-1])
    return v
for values in list(product((0,1),repeat=4))+list(permutations(range(4))):
    assert run(values,sort4)==sorted(values,reverse=True)
cases=list(product((0,1),repeat=6))+list(permutations(range(6)))+list(product((-1,0,1),repeat=6))
for values in cases:
    v=list(values)
    for start in (0,2,0):
        v[start:start+4]=sorted(v[start:start+4],reverse=True)
    assert v==run(values,full,True)==run(values,opt)==sorted(values,reverse=True)

asset_a='diagrams/prep-005-four-descending.png'
asset_b='diagrams/prep-005-six-three-blocks.png'
asset_c='diagrams/prep-005-six-pruned.png'
shutil.copy2(out/'prep-030-sorting-network.png',root/asset_a)

d=Drawing('B. Six inputs | Three complete 4-input sorters', 'Every S4 sorts its four incoming values from largest (top) to smallest (bottom).', 960)
ys=[260+i*95 for i in range(6)]
for i,y in enumerate(ys):
    d.line([(130,y),(1730,y)])
    d.arrow(1730,y)
    d.text(65,y,f'x{i+1}',30,bold=True,anchor='lm')
    d.text(1770,y,f'Y{i+1}',30,GREEN,True,anchor='lm')
for x,start,label in [(350,0,'S4-A'),(850,2,'S4-B'),(1350,0,'S4-C')]:
    y=ys[start]-38
    d.rect(x,y,230,3*95+76)
    d.text(x+115,y+130,label,34,BLUE,True,anchor='mt')
    d.text(x+115,y+184,'4 inputs',26,anchor='mt')
    d.text(x+115,y+223,'MAX to MIN',24,anchor='mt')
    for k in range(4):
        d.text(x+12,ys[start+k],str(k+1),20,anchor='lm')
        d.text(x+218,ys[start+k],str(k+1),20,anchor='rm')
    d.text(x+115,y-38,label+' : wires '+str(start+1)+'-'+str(start+4),25,BLUE,True,anchor='mt')
d.text(65,825,'Each complete S4 contains 5 comparators. Total: 3 x 5 = 15 comparators.',28,bold=True)
d.text(65,884,'Output: Y1 >= Y2 >= Y3 >= Y4 >= Y5 >= Y6',30,GREEN,True)
d.im.resize((1900,960)).save(root/asset_b)

d=Drawing('C. Open the blocks and remove redundant comparisons', 'Data flows left to right. Each colored connector with two dots is ONE comparator.', 900)
ys=[300+i*80 for i in range(6)]
groups=[(250,490,'First block: 5',BLUE),(800,390,'Second block: 4',PURPLE),(1300,320,'Last block: 3',GREEN)]
for x,w,label,color in groups:
    d.d.rectangle((x*2,180*2,(x+w)*2,755*2),fill='#f6f9fc')
    d.text(x+w/2,192,label,28,color,True,anchor='mt')
for i,y in enumerate(ys):
    d.line([(130,y),(1730,y)])
    d.arrow(1730,y)
    d.text(65,y,f'x{i+1}',28,bold=True,anchor='lm')
    d.text(1770,y,f'Y{i+1}',28,GREEN,True,anchor='lm')
xs=[320,400,480,560,640,870,950,1030,1110,1370,1450,1530]
for k,((i,j),x) in enumerate(zip(opt,xs),1):
    color=BLUE if k<=5 else PURPLE if k<=9 else GREEN
    d.text(x,248,f'C{k}',24,color,True,anchor='mt')
    d.line([(x,ys[i-1]),(x,ys[j-1])],color,4)
    for y in (ys[i-1],ys[j-1]):
        d.d.ellipse(((x-7)*2,(y-7)*2,(x+7)*2,(y+7)*2),fill=color)
d.text(65,790,'MAX to the upper dot, MIN to the lower dot. Crossings without dots are not connections.',26)
d.text(65,842,'5 + 4 + 3 = 12 comparators. The shortened groups rely on already-sorted input pairs.',27,GREEN,True)
d.im.resize((1900,900)).save(root/asset_c)

he='''שרטוטים בסדר יורד, בהתאמה ישירה לרכיב Max/Min שבמקור החדש. המימוש המקורי שבמסמך בסדר עולה נשאר תקין; אלה אותם זוגות השוואות בכיוון הפוך ועקבי. בארבעה קלטים: 12,34; 13,24; 23. בשישה: ממיין ארבעה על חוטים 1–4, אחריו על 3–6, ולבסוף שוב על 1–4. לאחר הממיין הראשון, שני העליונים אינם קטנים מאף אחד משני התחתונים שלו. לכן שני הקטנים של כל השישה נמצאים בין חוטים 3–6; הממיין השני מציב אותם בחוטים 5–6, והממיין האחרון מסדר את ארבעת האחרים.
דוגמה: (2,4,1,3,6,5) -> (4,3,2,1,6,5) -> (4,3,6,5,2,1) -> (6,5,4,3,2,1).
בפתיחת שלושת הבלוקים, מסירים את השוואת 34 בתחילת הבלוק השני ואת השוואות 12,34 בתחילת השלישי, משום שהזוגות כבר ממוינים בסדר יורד. נשארים 5+4+3=12 רכיבים במקום 15. אלה רכיבים פיזיים שונים; אין שעון או שימוש חוזר בזמן. הסרת משווים פנימיים מותרת כאשר יש גישה למימוש שבנינו, ולא אם הוא קופסה אטומה שאסור לשנות. נבדקו בנפרד 40 קלטים לממיין ארבעה ו־1513 לממיין שישה בסדר יורד, כולל נכונות כל השוואה שהוסרה. המינימום במספר הרכיבים אינו טענה למינימום עומק או השהיה.'''
en='''Descending diagrams directly match the source MAX/MIN cell. The original ascending explanation remains valid with every comparator consistently reversed. Use the same four-input network, then three four-sorter blocks on wires 1..4,3..6,1..4. The first block leaves its top two at least as large as its bottom two, so the smallest two of all six lie among wires 3..6. The second block fixes them at outputs 5,6; the third sorts the other four. Example: (2,4,1,3,6,5)->(4,3,2,1,6,5)->(4,3,6,5,2,1)->(6,5,4,3,2,1). Remove comparison 34 in block two and 12,34 in block three because those pairs are already descending; cost becomes 5+4+3=12 rather than 15. These are distinct physical blocks, not clocked reuse. Pruning requires access to the implementation rather than immutable black boxes. Verified 40 four-input and 1513 six-input descending cases, including each removed-comparison invariant. No depth/delay minimum is asserted.'''
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
start=raw.rfind('{',0,raw.index('"id": "PREP-005"'))
q,length=json.JSONDecoder().raw_decode(raw[start:])
for asset in [asset_a,asset_b,asset_c]:
    if not any(x.get('path')==asset for x in q.setdefault('media_assets',[])):
        q['media_assets'].append({'type':'solution_diagram','path':asset,'description':'Descending sorting-network solution; MAX above MIN.'})
q['descending_diagram_extension']={'explanation_he':he,'explanation_en':en,'assets':[asset_a,asset_b,asset_c],'checked_on':'2026-09-29','verification_script':'solutions/draw_prep_005_descending.py','four_input_cases':40,'six_input_cases':1513}
updated=raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
after=json.loads(updated)
assert all(a==b for a,b in zip(before['questions'],after['questions']) if a['id']!='PREP-005')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];text=md.read_text(encoding='utf-8')
if asset_c not in text:
    text+='\n\n## שרטוט שלושת הסעיפים בסדר יורד\n\n'+he+'\n\n'+en+'\n\n'+'\n\n'.join('![מימוש '+str(i)+'](../'+asset+')' for i,asset in enumerate([asset_a,asset_b,asset_c],1))+'\n'
    md.write_text(text,encoding='utf-8')
print('PASS: descending 4-sorter (40 cases), full/pruned 6-sorter (1513 cases), redundant comparisons; saved three diagrams.')
