"""Render the verified ideal edge-event model as a reusable timing diagram."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from prep_010_divide_by_three import simulate

ROOT = Path(__file__).resolve().parents[1]
im = Image.new('RGB', (1500, 900), '#ffffff')
d = ImageDraw.Draw(im)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 27)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
large = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 38)
d.text((55, 25), 'Divide by 3 | 50% duty cycle', fill='#14243a', font=large)
d.text((55, 82), 'Ideal model: input duty = 50%; reset released before t = 0', fill='#52647b', font=font)
left, scale = 270, 190
top = 180
colors = ['#52647b', '#1565c0', '#9b4cc1', '#008575']
rows = simulate(7)
for n in range(13):
    x = left + n * scale / 2
    d.line((x, top-35, x, top+475), fill='#e0e5ec', width=2)
    d.text((x-12, top+490), f'{n/2:g}T', font=small, fill='#52647b')
for i, (key, label) in enumerate([('clk','clk'),('q1','p = q1'),('delayed','delayed'),('out','out = p OR delayed')]):
    base = top + i * 130
    d.text((25, base+10), label, fill=colors[i], font=small)
    last_value = 0
    for j, row in enumerate(rows[:-1]):
        if row['t'] >= 6:
            break
        x1 = left + row['t'] * scale
        x2 = left + min(rows[j+1]['t'],6) * scale
        y = base + (0 if row[key] else 60)
        old_y = base + (0 if last_value else 60)
        d.line((x1,old_y,x1,y), fill=colors[i], width=5)
        d.line((x1,y,x2,y), fill=colors[i], width=5)
        last_value = row[key]
for start,end,label in [(0,1.5,'HIGH = 1.5T'),(1.5,3,'LOW = 1.5T')]:
    x1,x2 = left+start*scale,left+end*scale
    y=top+575
    d.line((x1,y,x2,y),fill='#008575',width=3)
    for x in (x1,x2): d.line((x,y-8,x,y+8),fill='#008575',width=3)
    d.text((x1+22,y+12),label,font=small,fill='#008575')
d.text((55,840),'Output period = 3T    |    f_out = f_in / 3    |    Duty = 1.5T / 3T = 50%',font=font,fill='#14243a')
im.save(ROOT / 'diagrams/prep-010-timing.png')
