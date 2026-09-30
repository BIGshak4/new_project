"""Attach complete new source and explain the constant-free impossibility."""
import json
import shutil
from pathlib import Path
from prep_011_mux_function import mux, part_b
from itertools import product

root=Path(__file__).resolve().parents[1]
source='sources/prep-011-variant-companies-2026-09-27.png'
tags=['amazon','nvidia','hardware','apple','mellanox','verification']
companies=['Amazon','NVIDIA','Apple','Mellanox']
he='''### האם מותר להשתמש בקבועים? ומה אם לא?

בצילום החדש לא נאמר במפורש שקבועים מותרים או אסורים, וגם גודל ה־MUX לא מוגדר. אין לקבוע מה התכוון מחבר השאלה. בראיון כדאי לשאול: ״האם מותר לחבר לכניסות קבוע לוגי 1, והאם מדובר ב־MUX 2:1?״ אפשר גם להציג את שתי הפרשנויות. נקודת אספקת המתח של רכיב אינה רשות אוטומטית להשתמש בקבוע לוגי ככניסת נתונים במודל החידה.

**אם אסור להשתמש בקבועים וכל האותות הזמינים הם a,b,c ומוצאי MUX רגילים ללא היפוך — אין פתרון קומבינטורי, בשום מספר של MUX.** מציבים a=b=c=0. כל MUX ברמה הראשונה מקבל רק אפסים בכניסות הנתונים, ולכן מוציא 0. כל MUX בהמשך מקבל גם הוא רק אפסים, ולכן מוציא 0. באינדוקציה לאורך הרשת, המוצא הסופי חייב להיות 0. אבל הפונקציה המבוקשת נותנת NOT(0 AND 0 AND NOT(0))=NOT(0)=1. זו סתירה. אותה הוכחה תקפה לכל גודל MUX רגיל. היא מניחה מעגל צירופי ללא משוב או מצב התחלתי, וללא כניסות משלימות או מוצא מהופך זמינים בחינם. גם הוספת קבוע 0 בלבד אינה עוזרת. הכתיב c' בפונקציה אינו אומר שהחוט NOT(c) כבר נתון לנו.

**אם קבוע 1 מותר, מספיקים שני MUX 2:1, ואין צורך בקבוע 0.** קוראים את הביטוי f=(abc')' בתור f=NOT(a AND b AND NOT(c)). מפרקים בהצבות, בלי לדלג על שלבים:

1. a=0: בתוך הסוגריים 0×b×NOT(c)=0, ולכן f=NOT(0)=1.
2. a=1: נשאר f=NOT(b AND NOT(c)). כעת אם b=0, שוב המכפלה 0 ולכן f=1.
3. a=1,b=1: נשאר f=NOT(NOT(c))=c.

מכאן בונים בחירה פנימית t: אם b=0 אז t=1; אם b=1 אז t=c. זהו MUX ראשון עם S=b, I0=1, I1=c. הבחירה החיצונית מחזירה 1 כאשר a=0, ואת t כאשר a=1. זהו MUX שני עם S=a, I0=1, I1=t. החיבור S הוא בוחר ולא כניסת נתונים; התוויות I0,I1 מציינות איזו כניסה נבחרת, לא את הערך שחייבים להזין בה.

| רכיב | בוחר S | כניסת I0 | כניסת I1 | מוצא |
|---|---|---|---|---|
| MUX 1 | b | הקבוע 1 | c | t |
| MUX 2 | a | הקבוע 1 | t | f |

**מדוע שניים הם מינימום?** ברכיב אחד פין הבחירה יכול לקבל רק משתנה גולמי או קבוע. אם בוחרים לפי a, בענף a=1 צריך לחשב NOT(b AND NOT(c)), שתלוי בשני משתנים ואינו חוט בודד או קבוע. בחירה לפי b נכשלת מאותה סיבה. אם בוחרים לפי c, בענף c=0 צריך NOT(a AND b), שוב פונקציה של שני משתנים שאינה חוט או קבוע. בחירה קבועה רק מעבירה אחת מכניסות הנתונים. לכן MUX יחיד לא מספיק, ושני הרכיבים שבשרטוט הם מינימום במודל הזה. כל 125 החיבורים האפשריים לרכיב יחיד עם a,b,c,0,1 זמינים כבר נבדקו, כך שהטענה תקפה גם במודל המצומצם שנותן רק קבוע 1.

![מימוש מינימלי בשני MUX 2:1 עם קבוע 1](../diagrams/prep-011-two-mux.png)

אם מותר MUX 4:1 וקבוע 1, מספיק רכיב אחד, כפי שתועד בנוסח הקודם: בחירה ab וכניסות (1,1,1,c). לכן יש לציין במפורש שהמינימום שניים הוא עבור 2:1.

**מקור וייחוס מעודכנים:** התמונה המלאה הנוספת כוללת תגיות hardware ו־verification, וחברות Amazon, NVIDIA, Apple, Mellanox; תווית ראשית ״מלאנוקס״. אלה דיווחי המקור בלבד, ללא אימות עצמאי. TangoTec מופיעה בצילום הישן של השאלה, ולא בתמונה החדשה. המקורות נשמרים בנפרד כדי שלא לערבב את הייחוסים.
'''
en='''### Constants and the complete alternate source

The new prompt neither explicitly permits nor forbids constants, and does not specify mux size. Ask whether logic 1 and ordinary 2:1 muxes are allowed, or present both interpretations. Power pins do not by themselves authorize logic-constant data inputs in an abstract puzzle.

With only raw a,b,c and non-inverting mux outputs available in an acyclic combinational network, realization is impossible regardless of mux count or fan-in. At a=b=c=0 all first-level data inputs are zero, hence all outputs are zero. Inductively every subsequent mux also outputs zero. The required function NOT(a AND b AND NOT(c)) instead outputs one at 000, a contradiction. Constant zero alone cannot help. This proof excludes free complemented input/output signals, feedback and initialized state. The notation c' does not grant a precomputed NOT(c) wire.

Allowing constant one suffices: t=MUX(b,1,c), f=MUX(a,1,t), using the convention MUX(S,I0,I1). Substituting a=0 gives one; with a=1,b=0 the result is also one; with a=b=1 double negation leaves c. No constant zero or separate inversion is needed. A single 2:1 mux cannot implement the function: selection by a or b leaves a nontrivial two-variable cofactor, and selection by c leaves NAND(a,b) for c=0. Constant selection can only forward a raw wire or constant. Earlier exhaustive checking of all 125 one-mux wirings verifies this bound. The existing two-mux diagram is the full optimal circuit under this model. If a 4:1 mux is allowed, one suffices with select ab and data (1,1,1,c).

The complete alternate image reports hardware, verification and companies Amazon, NVIDIA, Apple, Mellanox, with Mellanox badge. Attribution is source-reported and unverified. TangoTec belongs to the earlier image only. All source-specific metadata is retained separately.'''

# Check the concrete witness and the constructive answer. Induction is the
# proof for arbitrary network size, not a finite enumeration of circuit sizes.
assert mux(0,0,0)==mux(1,0,0)==0
assert int(not(0 and 0 and not 0))==1
for a,b,c in product((0,1),repeat=3):
    assert part_b(a,b,c)==int(not(a and b and not c))
cases=list(product((0,1),repeat=3))
sources=[(0,)*8,(1,)*8]+[tuple(v[i] for v in cases) for i in range(3)]
target=tuple(int(not(a and b and not c)) for a,b,c in cases)
for sel,d0,d1 in product(sources,repeat=3):
    assert tuple(mux(*v) for v in zip(sel,d0,d1))!=target

p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-011"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
assert q['id']=='PREP-011' and not any(x['path']==source for x in q['sources'])
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-743ffc7c-6304-4a6f-965b-0a74dd88bd36.png',root/source)
q['sources'].append({'type':'user_supplied_image','path':source,'received_on':'2026-09-27','role':'alternate_wording_complete_company_tags','source_tags':tags,'source_topic_tags':['hardware','verification'],'reported_companies':companies,'source_company_badge':'מלאנוקס','attribution_status':'reported_by_supplied_source_not_independently_verified'})
q['media_assets'].append({'type':'source_image','path':source,'description':'Complete alternate prompt with hardware/verification and company tags.'})
for field,values in [('reported_companies',companies),('source_tags',tags),('source_topic_tags',['hardware','verification']),('topics',['hardware','verification'])]:
    q[field]=list(dict.fromkeys(q[field]+values))
# Keep source-vs-added topic classifications disjoint after the new evidence.
q['added_topic_tags']=[t for t in q['added_topic_tags'] if t not in q['source_topic_tags']]
q['company_attribution_note']='Union of supplied-source reports; TangoTec belongs to original source only, Apple to the new complete source. See individual source metadata.'
q['sources'][0].update({'source_tags':['amazon','nvidia','logic','tangotec','mellanox'],'source_topic_tags':['logic'],'reported_companies':['Amazon','NVIDIA','TangoTec','Mellanox'],'source_company_badge':'מלאנוקס'})
variant=q['prompt_variants'][-1]
variant['additional_source_paths']=[source]
variant['source_topic_tags']=['hardware','verification']
variant['reported_companies']=companies
variant['source_company_badge']='מלאנוקס'
variant['company_attribution_status']='reported_by_supplied_source_not_independently_verified'
variant['metadata_note']='Company/topic attribution supplied by the later complete image; first crop has no tags.'
q.setdefault('solution_extensions',[]).append({'key':'constants-required-and-source-companies','content_he':he,'content_en':en,'diagram_path':'diagrams/prep-011-two-mux.png','verification_script':'solutions/update_prep_011_constants.py'})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
q['assumptions'].append('New alternate source leaves constants unspecified: impossible with raw a,b,c and ordinary muxes only; constant 1 makes the two-2:1-mux construction possible.')
q['verification'].setdefault('additional_checks',[]).append({'script_path':'solutions/update_prep_011_constants.py','status':'passed','method':'Checked all 8 constructive input tuples, 125 one-mux wirings and the 000 impossibility witness. Arbitrary-size impossibility established by zero-preservation induction, not exhaustive circuit search.'})
after=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
parsed=json.loads(after)
assert parsed['question_count']==22
assert all(x==y for x,y in zip(before['questions'],parsed['questions']) if x['id']!='PREP-011')
p.write_text(after,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n![צילום הנוסח המלא עם חברות](../'+source+')\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
print('Updated PREP-011 sources/companies, constant-free impossibility and optimal constant-1 construction; checks passed, count remains 22.')
