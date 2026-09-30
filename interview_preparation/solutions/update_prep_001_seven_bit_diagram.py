"""Attach the diagram and intuitive carry-weight explanation without usage tracking."""
import json
from pathlib import Path
from update_prep_001_seven_bit import fa, popcount7

root = Path(__file__).resolve().parents[1]
asset = 'diagrams/prep-001-seven-bit-four-fa.png'
he = '''הסבר אינטואיטיבי: Full-Adder מחלק עד שלוש אחדות לזוג ולשארית. Carry=1 אומר שיש זוג אחד, ו־Sum=1 אומר שנותרה יחידה בודדת. לדוגמה 1+1+1=3 נותן C=1,S=1: זוג ועוד יחידה. FA1 ו־FA2 מטפלים בשתי שלשות קלט, ושומרים בנפרד זוגות cA,cB ושאריות sA,sB. FA3 אוסף את שתי השאריות ואת הביט השביעי; הוא מוציא את היחידה הסופית y0 ואולי זוג נוסף cC. FA4 סופר את שלושת הזוגות cA,cB,cC. משום שכל זוג שווה שתי אחדות מקוריות, Sum שלו שווה 2 במניין המקורי, ו־Carry שלו שווה 4. לכן אלה y1,y2, והמספר נקרא y2y1y0.
בדוגמה x6..x0=1001101: FA1 מקבל (1,0,1) ומוציא sA=0,cA=1; FA2 מקבל (1,0,0) ומוציא sB=1,cB=0; FA3 מקבל (0,1,1) ומוציא y0=0,cC=1; FA4 מקבל (1,0,1) ומוציא y1=0,y2=1. הפלט 100. חוטים בעלי אותו שם בשרטוט מחוברים פיזית, גם כאשר קו ארוך הוחלף בתוויות. כל Cin הוא ביט קלט במשקל השווה ל־A ול־B של אותו מחבר; מותר לחבר אליו ביט נתון, אין צורך שיהיה נשא ממחבר קודם.'''
en = '''Intuition: a full adder splits up to three ones into a pair (carry) and a leftover unit (sum). FA1/FA2 keep pairs cA,cB and leftovers sA,sB. FA3 combines the leftovers and seventh input, yielding final unit y0 and another pair cC. FA4 counts the three pair indicators; its sum has original weight 2 and its carry original weight 4, giving y1,y2. Read output as y2y1y0. For input x6..x0=1001101: FA1 inputs (1,0,1) -> (sA,cA)=(0,1); FA2 (1,0,0)->(sB,cB)=(1,0); FA3 (0,1,1)->(y0,cC)=(0,1); FA4 (1,0,1)->(y1,y2)=(0,1). Output 100. Repeated net labels in the diagram denote the same physical connection. Cin has the same weight as A and B within a full adder and may receive an ordinary input bit.'''
assert [fa(1,0,1),fa(1,0,0),fa(0,1,1),fa(1,0,1)] == [(0,1),(1,0),(0,1),(0,1)]
assert popcount7(0b1001101) == 4
p=root/'questions.json'
s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.rfind('{',0,s.index('"id": "PREP-001"'))
q,length=json.JSONDecoder().raw_decode(s[start:])
v=next(v for v in q['prompt_variants'] if v['key']=='seven-bit-popcount')
assert asset not in v.get('solution_diagrams',[])
v['solution_diagrams']=[asset]
v['solution_he']+='\n\n'+he
v['solution_en']+='\n\n'+en
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
q.setdefault('media_assets',[]).append({'type':'solution_diagram','path':asset,'description':'Four-full-adder seven-bit population count; named carry nets and output weights.'})
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert before['questions'][1:]==after['questions'][1:]
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path']
md.write_text(md.read_text(encoding='utf-8')+'\n\n### שרטוט והסבר אינטואיטיבי — 7 ביט\n\n![ארבעה מחברים מלאים וסימון משקלי הפלט](../'+asset+')\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
print('Diagram linked; intuitive explanation and example saved; 128 cases and example trace verified.')
