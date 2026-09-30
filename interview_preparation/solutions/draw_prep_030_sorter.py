"""Comparator-network notation and the external diagnostic test setup."""
from pathlib import Path
from draw_prep_010_mod3_counters import Drawing, INK, BLUE, GREEN

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'diagrams'
OUT.mkdir(exist_ok=True)
d = Drawing('A. Four-input sorting network', 'Data flows left to right. Each blue connector is one 2-input sorting component.', 850)
ys = [270, 400, 530, 660]
for x, label in [(420, 'Stage 1'), (890, 'Stage 2'), (1380, 'Stage 3')]:
    d.text(x, 165, label, 30, bold=True, anchor='mt')
for i, y in enumerate(ys):
    d.text(65, y, 'abcd'[i], 32, bold=True, anchor='lm')
    d.line([(130, y), (1670, y)])
    d.arrow(1670, y)
    d.text(1720, y, f'Y{i+1}', 32, GREEN, True, anchor='lm')
for name, x, i, j in [('C1', 360, 0, 1), ('C2', 480, 2, 3), ('C3', 830, 0, 2), ('C4', 950, 1, 3), ('C5', 1380, 1, 2)]:
    d.line([(x, ys[i]), (x, ys[j])], BLUE, 5)
    for y in (ys[i], ys[j]):
        d.d.ellipse(((x-9)*2, (y-9)*2, (x+9)*2, (y+9)*2), fill=BLUE)
    d.text(x+22, (ys[i]+ys[j])/2 - (32 if j-i == 2 else 0), name, 30, BLUE, True, anchor='lm')
d.text(65, 730, 'Only marked dots are ports. Crossings without dots are not connections.', 26)
d.text(65, 780, 'Each component: MAX to the upper wire, MIN to the lower wire. Result: Y1 >= Y2 >= Y3 >= Y4.', 27, GREEN)
d.im.resize((1900,850)).save(OUT/'prep-030-sorting-network.png')

d = Drawing('B. One test vector identifies all six possible cases', 'Observe all four outputs; internal wires do not need to be measured.', 410)
for x, width, label, sub in [(65,360,'Input vector','(4, 3, 2, 1)'),(560,520,'Same sorting network','Healthy OR one faulty C1...C5'),(1240,590,'Observe (Y1, Y2, Y3, Y4)','Match the result to the diagnosis table')]:
    d.rect(x,190,width,145)
    d.text(x+width/2,215,label,30,bold=True,anchor='mt')
    d.text(x+width/2,275,sub,25,anchor='mt')
for start,end in [(425,560),(1080,1240)]:
    d.line([(start,262),(end,262)],BLUE)
    d.arrow(end,262,BLUE)
d.im.resize((1900,410)).save(OUT/'prep-030-diagnostic-test.png')
print('Saved both PREP-030 diagrams.')
