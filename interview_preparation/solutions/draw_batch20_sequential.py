"""Deterministic clean teaching diagrams, no archived screenshots embedded."""
from pathlib import Path
import math
import re
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch

OUT = Path(__file__).resolve().parents[1] / 'diagrams'
INK = '#172c3d'
BLUE = '#266e9a'
LIGHT = '#eef5f8'
TEAL = '#137c74'
GRAY = '#506777'
FONT = 'C:/Windows/Fonts/arial.ttf'
LANG = 'en'

# Pure Hebrew is reversed for Pillow/matplotlib's basic text engines. Mixed
# equations are separate LTR segments, so signal names and formulas stay intact.
TRANSLATIONS = {
    'Common-clock divide by 2 and 4': 'מחלקי תדר בשתיים ובארבע עם שעון משותף',
    'Both flip-flops sample OLD Q values on the same rising edge. Reset: Q1 Q0 = 00.':
        ('שני הדלגלגים דוגמים יחד את המצב הישן; האיפוס הוא', 'Q1 Q0 = 00'),
    'State cycle:   00  ->  01  ->  10  ->  11  ->  00':
        ('מחזור המצבים', '00  ->  01  ->  10  ->  11  ->  00'),
    'Filled dots = connected branches. Q1 toggles only when pre-edge Q0 = 1.':
        ('נקודות מסמנות חיבור; הביט הגבוה מתהפך רק בתנאי', 'Q0(old) = 1'),
    'Overlapping 101101 detector (Moore)': 'גלאי חופף לרצף במכונת מצבים',
    'State = longest pattern prefix that is an input suffix. Seven states, three binary state FFs.':
        'המצב הוא הקידומת הארוכה שהיא סיומת הקלט; שבעה מצבים ושלושה דלגלגים',
    'New bit enters at the LEFT / MSB': 'ביט חדש נכנס משמאל כביט המשמעותי ביותר',
    'Normalized state s = N * inverse(2^k) mod 3. Next s = 2(s+b) mod 3. Reset S0.':
        ('שארית מנורמלת; איפוס למצב ההתחלתי', 's = N * inverse(2^k) mod 3; next_s = 2(s+b) mod 3'),
    'state': 'מצב',
    'empty': 'ריק',
    'Edge labels: accepted bit b. Double circle: state decode y=1. Complete transition table shown.':
        ('חץ מסומן בביט שנקלט; עיגול כפול מציין פלט אחד; טבלת המעברים מלאה', 'b; y=1'),
    'Output is gated by seen until first input.':
        ('לפני קליטת הביט הראשון הפלט חסום על ידי דגל התוקף', 'seen'),
    'Two abstract enrolled words, exact matching': 'התאמה מדויקת לשני ערכים רשומים',
    '64-bit values; occupancy distinguishes an empty slot from enrolled zero. Invalid cycles skip.':
        'מילים בנות שישים וארבע סיביות; תפוסה מבדילה בין ריק לאפס רשום; מחזור לא תקף מדולג',
    'Single sample:  matched = accepted AND hit':
        ('דגימה יחידה', 'matched = accepted AND hit'),
    'Pair mode:  matched = accepted AND hit AND previous_hit':
        ('שתי התאמות רצופות', 'matched = accepted AND hit AND previous_hit'),
    'On acceptance: previous_hit <- hit. Configuration / reset clears the streak.':
        ('בכל קבלה נשמרת ההתאמה; תצורה ואיפוס מוחקים את הרצף', 'previous_hit <- hit'),
    'Infix + / * datapath with normal precedence': 'מסלול נתונים לביטוי עם קדימות רגילה',
    'Operation diagram: W-bit registers S and P. All results truncated modulo 2^W.':
        ('מצברי סכום ומכפלה ברוחב קבוע; התוצאה מודולרית', 'S, P: W bits; mod 2^W'),
    'S: closed-term sum': ('סכום איברים סגורים', 'S'),
    'P: active product': ('מכפלת האיבר הפעיל', 'P'),
    'ADD: S + P': ('חיבור', 'S + P'),
    'MULTIPLY: P * x': ('כפל', 'P * x'),
    'on + : write S': ('עדכון סכום', '+ : S'),
    'on = : write result': ('שמירת תוצאה', '= : result'),
    'P input selector': ('בורר קלט', 'P'),
    'number x': ('מספר', 'x'),
    'Controller selects P input: x for first/after + ; P*x for after *.':
        'בתחילה ואחרי חיבור נטען מספר; אחרי כפל נטענת המכפלה',
    'Register loads occur only on accepted tokens. Idle holds S and P.':
        'הרגיסטרים נטענים רק בטוקן שהתקבל; בין קבלות נשמר המצב',
    'At = : result_valid pulses, then reset S/P for the next expression.':
        ('בסיום מופק פולס תוצאה והמצברים מתאפסים לביטוי הבא', '= : result_valid'),
    'Example: 2 + 3 * 4 = 14      (left fold gives 20)':
        ('דוגמה; חישוב משמאל לימין היה מחזיר עשרים', '2 + 3 * 4 = 14'),
    'Four-word synchronous 1R1W memory': 'זיכרון סינכרוני לארבע מילים עם קריאה וכתיבה',
    'Both requests accepted at the same edge. Same-address collision returns OLD data (read-first).':
        'קריאה וכתיבה מתקבלות באותה חזית; בהתנגשות מוחזר הערך הישן',
    'write decoder': 'מפענח כתיבה',
    'read mux': 'מרבב קריאה',
    'load = re_en': ('טעינת פלט', 're_en'),
    'Storage: 4W FFs + W response FFs + 1 Valid FF = 5W + 1 FFs':
        ('מספר הדלגלגים הכולל', '4W + W + 1 = 5W + 1'),
    'Write load muxes are inside register blocks. EN is load, not clock; every FF uses clk.':
        'מרבבי הטעינה נמצאים ברגיסטרים; אות טעינה אינו שעון; כל הדלגלגים חולקים שעון',
    'Reset initializes all words and outputs to zero. Idle: hold read_data; Valid=0.':
        ('האיפוס מאפס מילים ויציאות; ללא קריאה הפלט נשמר והתגובה אינה תקפה', 'Valid=0'),
}


def visible(value):
    value = re.sub(r'^PREP-\d+(?: variant)?\s*\|\s*', '', value)
    assert not re.search(r'PREP-\d+', value), 'Question IDs must never be drawn'
    if LANG != 'he':
        return value
    translated = TRANSLATIONS.get(value, value)
    if isinstance(translated, tuple):
        he, technical = translated
        return technical + '   |   ' + he[::-1]
    return translated[::-1] if re.search(r'[\u0590-\u05ff]', translated) else translated


def localized_path(name):
    return OUT / (name[:-4] + '-he.png' if LANG == 'he' else name)


def canvas(title, subtitle):
    im = Image.new('RGB', (1440, 900), 'white')
    d = ImageDraw.Draw(im)
    label(d, (55, 35), title, 36)
    label(d, (55, 91), subtitle, 23, GRAY)
    d.line((55, 139, 1385, 139), fill='#d2e1e8', width=2)
    return im, d


def label(d, xy, text, size=25, color=INK, anchor=None):
    value = visible(text)
    font = ImageFont.truetype(FONT, size)
    max_width = 1330 if anchor is None else 315
    while d.textbbox((0, 0), value, font=font)[2] > max_width and size > 17:
        size -= 1
        font = ImageFont.truetype(FONT, size)
    d.text(xy, value, font=font, fill=color, anchor=anchor)


def box(d, rect, text, color=LIGHT):
    d.rounded_rectangle(rect, radius=12, fill=color, outline=BLUE, width=3)
    x1, y1, x2, y2 = rect
    lines = text.split('\n')
    for i, line in enumerate(lines):
        label(d, ((x1+x2)/2, (y1+y2)/2 + (i-(len(lines)-1)/2)*34), line, anchor='mm')


def arrow(d, points, color=BLUE, width=4):
    d.line(points, fill=color, width=width)
    a, b = points[-2:]
    angle = math.atan2(b[1]-a[1], b[0]-a[0])
    head = [b, (b[0]-14*math.cos(angle-.43), b[1]-14*math.sin(angle-.43)),
            (b[0]-14*math.cos(angle+.43), b[1]-14*math.sin(angle+.43))]
    d.polygon(head, fill=color)


def ff(d, rect, name):
    box(d, rect, name)
    x1, y1, x2, y2 = rect
    label(d, (x1+13, y1+24), 'D', 23)
    label(d, (x2-33, y1+24), 'Q', 23)
    d.line([(x1, y2-45), (x1+16, y2-35), (x1, y2-25)], fill=BLUE, width=3)


def save(im, name):
    im.save(localized_path(name))


def fsm(name, title, subtitle, table, outputs, prefixes, left=False):
    fig, (ax, at) = plt.subplots(1, 2, figsize=(16, 9), gridspec_kw={'width_ratios':[1.9, 1]})
    fig.patch.set_facecolor('white')
    fig.suptitle(visible(title), fontsize=21, color=INK, x=.04, ha='left', y=.96)
    fig.text(.04, .89, visible(subtitle), fontsize=12, color=GRAY)
    n = len(table)
    angles = [math.pi/2 - i*2*math.pi/n for i in range(n)]
    pos = [(3.15*math.cos(a), 3.15*math.sin(a)) for a in angles]
    radius = .50 if n > 3 else .57
    ax.set_xlim(-4.6,4.6); ax.set_ylim(-4.5,4.5); ax.set_aspect('equal'); ax.axis('off')
    for src, row in enumerate(table):
        bytarget = {}
        for bit, dst in enumerate(row): bytarget.setdefault(dst, []).append(str(bit))
        for dst, bits in bytarget.items():
            x,y = pos[src]; xx,yy = pos[dst]
            if src == dst:
                norm = math.hypot(x,y)
                ux,uy = x/norm,y/norm
                px,py = -uy,ux
                start=(x+radius*.65*px+radius*.7*ux,y+radius*.65*py+radius*.7*uy)
                end=(x-radius*.65*px+radius*.7*ux,y-radius*.65*py+radius*.7*uy)
                patch=FancyArrowPatch(start,end,connectionstyle='arc3,rad=-1.8',arrowstyle='-|>',mutation_scale=17,color=GRAY,lw=1.8)
                ax.add_patch(patch)
                ax.text(x+ux*1.25,y+uy*1.25,','.join(bits),ha='center',va='center',fontsize=13,color=INK)
            else:
                reverse = src in table[dst]
                rad = .16 if reverse else .07
                patch=FancyArrowPatch((x,y),(xx,yy),connectionstyle=f'arc3,rad={rad}',shrinkA=radius*40,shrinkB=radius*40,
                                      arrowstyle='-|>',mutation_scale=17,color=BLUE,lw=1.6)
                ax.add_patch(patch)
                dx,dy=xx-x,yy-y
                lx=(x+xx)/2 + rad*dy*.65
                ly=(y+yy)/2 - rad*dx*.65
                ax.text(lx,ly,','.join(bits),ha='center',va='center',fontsize=12,color=INK,
                        bbox=dict(facecolor='white',edgecolor='none',pad=1.5))
    for i, (x,y) in enumerate(pos):
        ax.add_patch(Circle((x,y),radius,facecolor=LIGHT if not outputs[i] else '#d9f1e9',edgecolor=TEAL if outputs[i] else BLUE,lw=2.2,zorder=3))
        if outputs[i]: ax.add_patch(Circle((x,y),radius-.09,fill=False,edgecolor=TEAL,lw=1.7,zorder=4))
        ax.text(x,y+.11,f'S{i}',ha='center',va='center',fontsize=16,zorder=5,color=INK)
        ax.text(x,y-.20,f'y={outputs[i]}',ha='center',va='center',fontsize=11,zorder=5,color=INK)
    x,y=pos[0]
    ax.annotate('reset',xy=(x-.52,y),xytext=(x-1.8,y),fontsize=12,va='center',arrowprops=dict(arrowstyle='->',color=GRAY))
    at.axis('off')
    data=[[f'S{i}',f'S{row[0]}',f'S{row[1]}',str(outputs[i])] for i,row in enumerate(table)]
    tab=at.table(cellText=data,colLabels=[visible('state'),'b=0','b=1','y'],loc='center',cellLoc='center',bbox=[.02,.35,.95,.55])
    tab.auto_set_font_size(False);tab.set_fontsize(14)
    for (r,c),cell in tab.get_celld().items():
        cell.set_edgecolor('#cadce5');cell.set_facecolor(LIGHT if r==0 else 'white')
    text = '\n'.join(f'S{i}: {p or visible("empty")}' for i,p in enumerate(prefixes))
    at.text(.04,.27,text,fontsize=12,va='top',color=GRAY)
    footer = 'Edge labels: accepted bit b. Double circle: state decode y=1. Complete transition table shown.'
    fig.text(.04,.045,visible(footer),fontsize=11,color=GRAY)
    if left:
        fig.text(.04,.018,visible('Output is gated by seen until first input.'),fontsize=11,color=GRAY)
    fig.subplots_adjust(top=.84,bottom=.08,wspace=.07)
    fig.savefig(localized_path(name),dpi=150,facecolor='white');plt.close(fig)



def render(language):
    global LANG
    LANG = language
    im, d = canvas('PREP-216  |  Common-clock divide by 2 and 4',
                   'Both flip-flops sample OLD Q values on the same rising edge. Reset: Q1 Q0 = 00.')
    box(d, (170, 220, 360, 320), 'NOT')
    ff(d, (480, 195, 735, 365), 'DFF  Q0')
    arrow(d, [(360, 270), (480, 270)])
    arrow(d, [(735, 270), (960, 270)])
    label(d, (985, 255), 'div2 = f / 2')
    arrow(d, [(795, 270), (795, 175), (100, 175), (100, 270), (170, 270)])
    d.ellipse((788,263,802,277), fill=BLUE)
    box(d, (170, 480, 360, 580), 'XOR')
    ff(d, (480, 455, 735, 625), 'DFF  Q1')
    arrow(d, [(360, 530), (480, 530)])
    arrow(d, [(735, 530), (960, 530)])
    label(d, (985, 515), 'div4 = f / 4')
    arrow(d, [(795, 530), (795, 660), (100, 660), (100, 555), (170, 555)])
    d.ellipse((788,523,802,537), fill=BLUE)
    arrow(d, [(850, 270), (850, 405), (120, 405), (120, 505), (170, 505)])
    d.ellipse((843,263,857,277), fill=BLUE)
    arrow(d, [(310, 720), (430, 720), (430, 330), (480, 330)])
    arrow(d, [(430, 720), (430, 590), (480, 590)])
    label(d, (180, 703), 'clk', 27)
    d.ellipse((423,713,437,727), fill=BLUE)
    label(d, (55, 800), 'State cycle:   00  ->  01  ->  10  ->  11  ->  00', 28)
    label(d, (55, 850), 'Filled dots = connected branches. Q1 toggles only when pre-edge Q0 = 1.', 22, GRAY)
    save(im, 'prep-216-batch20-sequential.png')

    fsm('prep-217-batch20-sequential.png', 'PREP-217  |  Overlapping 101101 detector (Moore)',
        'State = longest pattern prefix that is an input suffix. Seven states, three binary state FFs.',
        ((0,1),(2,1),(0,3),(2,4),(5,1),(0,6),(2,4)), (0,0,0,0,0,0,1), ('','1','10','101','1011','10110','101101'))
    fsm('prep-036-batch20-left-msb.png', 'PREP-036 variant  |  New bit enters at the LEFT / MSB',
        'Normalized state s = N * inverse(2^k) mod 3. Next s = 2(s+b) mod 3. Reset S0.',
        ((0,2),(2,1),(1,0)), (1,0,0), ('s=0','s=1','s=2'), left=True)

    im,d=canvas('PREP-218  |  Two abstract enrolled words, exact matching',
                '64-bit values; occupancy distinguishes an empty slot from enrolled zero. Invalid cycles skip.')
    ff(d,(110,220,400,370),'ref0 [63:0]')
    ff(d,(110,460,400,610),'ref1 [63:0]')
    box(d,(580,220,850,370),'== 64-bit\nAND have0')
    box(d,(580,460,850,610),'== 64-bit\nAND have1')
    arrow(d,[(400,295),(580,295)])
    arrow(d,[(400,535),(580,535)])
    label(d,(440,170),'sample [63:0]',24)
    arrow(d,[(500,205),(500,345),(580,345)])
    arrow(d,[(500,345),(500,585),(580,585)])
    d.ellipse((493,338,507,352),fill=BLUE)
    box(d,(1020,330,1240,490),'OR\nhit')
    arrow(d,[(850,295),(940,295),(940,370),(1020,370)])
    arrow(d,[(850,535),(940,535),(940,450),(1020,450)])
    label(d,(100,720),'Single sample:  matched = accepted AND hit',28)
    label(d,(100,775),'Pair mode:  matched = accepted AND hit AND previous_hit',28)
    label(d,(100,825),'On acceptance: previous_hit <- hit. Configuration / reset clears the streak.',23,GRAY)
    save(im,'prep-218-batch20-sequential.png')

    im,d=canvas('PREP-219  |  Infix + / * datapath with normal precedence',
                'Operation diagram: W-bit registers S and P. All results truncated modulo 2^W.')
    box(d,(80,230,410,350),'S: closed-term sum')
    box(d,(80,475,410,595),'P: active product')
    box(d,(600,230,850,350),'ADD: S + P')
    box(d,(600,475,850,595),'MULTIPLY: P * x')
    arrow(d,[(410,290),(600,290)])
    arrow(d,[(410,535),(495,535),(495,320),(600,320)])
    arrow(d,[(495,535),(600,535)])
    d.ellipse((488,528,502,542),fill=BLUE)
    box(d,(1030,230,1350,350),'on + : write S\non = : write result')
    arrow(d,[(850,290),(1030,290)])
    box(d,(1030,475,1350,595),'P input selector\nx  /  P * x')
    arrow(d,[(850,535),(1030,535)])
    label(d,(935,400),'number x',24)
    arrow(d,[(960,435),(960,565),(1030,565)])
    arrow(d,[(960,435),(725,435),(725,475)])
    d.ellipse((953,428,967,442),fill=BLUE)
    label(d,(60,680),'Controller selects P input: x for first/after + ; P*x for after *.',26)
    label(d,(60,735),'Register loads occur only on accepted tokens. Idle holds S and P.',25)
    label(d,(60,790),'At = : result_valid pulses, then reset S/P for the next expression.',25)
    label(d,(60,845),'Example: 2 + 3 * 4 = 14      (left fold gives 20)',26)
    save(im,'prep-219-batch20-sequential.png')

    im,d=canvas('PREP-220  |  Four-word synchronous 1R1W memory',
                'Both requests accepted at the same edge. Same-address collision returns OLD data (read-first).')
    box(d,(65,340,280,495),'write decoder\n2 -> 4')
    label(d,(70,175),'wr_addr, wr_en',23)
    arrow(d,[(170,210),(170,340)])
    label(d,(345,150),'wr_data [W-1:0]',22)
    arrow(d,[(425,185),(425,240),(470,240)])
    for i in range(4):
        y=195+i*123
        ff(d,(470,y,780,y+93),f'M{i}  [W-1:0]')
        if i:
            arrow(d,[(425,240),(425,y+45),(470,y+45)])
        d.ellipse((419,y+39,431,y+51),fill=BLUE)
        arrow(d,[(280,365+i*25),(315+i*20,365+i*25),(315+i*20,y+82),(545,y+82)])
        label(d,(552,y+70),'EN',15)
    box(d,(915,310,1080,470),'read mux\n4 : 1')
    for i in range(4):
        y=240+i*123
        arrow(d,[(780,y),(830+i*15,y),(830+i*15,335+i*36),(915,335+i*36)])
    ff(d,(1160,310,1385,470),'read_data')
    arrow(d,[(1080,390),(1160,390)])
    label(d,(925,520),'re_addr',24)
    arrow(d,[(990,510),(990,470)])
    label(d,(1125,600),'load = re_en',25)
    label(d,(1125,655),'Valid <- re_en',25)
    label(d,(65,735),'Storage: 4W FFs + W response FFs + 1 Valid FF = 5W + 1 FFs',28)
    label(d,(65,790),'Write load muxes are inside register blocks. EN is load, not clock; every FF uses clk.',22,GRAY)
    label(d,(65,835),'Reset initializes all words and outputs to zero. Idle: hold read_data; Valid=0.',23,GRAY)
    save(im,'prep-220-batch20-sequential.png')
    print('Wrote localized sequential PNG diagrams')


if __name__ == "__main__":
    for language in ("en", "he"):
        render(language)
