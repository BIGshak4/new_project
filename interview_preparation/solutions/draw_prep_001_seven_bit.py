"""Seven-bit popcount, with named carry nets to keep the schematic readable."""
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, BLUE, GREEN, PURPLE

ROOT = Path(__file__).resolve().parents[1]
d = Drawing('7-bit population count | Four full adders', 'Every input bit counts as one unit. Result: Y2 Y1 Y0, representing 0 through 7.', 1060)

def block(x,y,name):
    d.rect(x,y,250,230)
    d.text(x+125,y+14,name,34,bold=True,anchor='mt')
    for offset,label in [(70,'A'),(125,'B'),(180,'Cin')]:
        d.text(x+15,y+offset,label,25,anchor='lm')
    for offset,label in [(85,'S'),(165,'Cout')]:
        d.text(x+235,y+offset,label,25,anchor='rm')

def inp(x,y,label,color=BLUE):
    d.text(x-125,y-36,label,27,color,bold=True)
    d.line([(x-130,y),(x,y)],color)
    d.arrow(x,y,color)

def out(x,y,label,color=PURPLE):
    d.line([(x,y),(x+170,y)],color)
    d.arrow(x+170,y,color)
    d.text(x+35,y-35,label,27,color,bold=True)

block(240,190,'FA1')
block(240,590,'FA2')
block(860,350,'FA3')
block(1430,650,'FA4')
for base,labels in [(190,['x0','x1','x2']),(590,['x3','x4','x5'])]:
    for off,label in zip([70,125,180],labels):
        inp(240,base+off,label)
out(490,355,'cA')
out(490,755,'cB')
d.line([(490,275),(710,275),(710,420),(860,420)],BLUE)
d.arrow(860,420,BLUE)
d.text(535,238,'sA',27,BLUE,True)
d.line([(490,675),(665,675),(665,475),(860,475)],BLUE)
d.arrow(860,475,BLUE)
d.text(535,638,'sB',27,BLUE,True)
inp(860,530,'x6')
out(1110,515,'cC')
d.line([(1110,435),(1780,435)],GREEN)
d.arrow(1780,435,GREEN)
d.text(1540,385,'Y0  (weight 1)',29,GREEN,True)
for off,label in zip([70,125,180],['cA','cB','cC']):
    inp(1430,650+off,label,PURPLE)
out(1680,735,'Y1',GREEN)
out(1680,815,'Y2',GREEN)
d.text(1730,749,'weight 2',21,GREEN)
d.text(1730,829,'weight 4',21,GREEN)
d.text(1420,598,'Three carries, each worth 2',25,PURPLE)
d.text(65,920,'Matching labels are the same wire: cA -> cA, cB -> cB, cC -> cC.',28,bold=True)
d.text(65,972,'S = sum bit   |   Cout = carry bit   |   A + B + Cin = S + 2*Cout',28)
path=ROOT/'diagrams/prep-001-seven-bit-four-fa.png'
d.im.resize((1900,1060)).save(path)
print(path)
