"""Store and exhaustively check the seven-bit variant of PREP-001."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'sources/prep-001-seven-bit-2026-09-28.png'

def fa(a, b, c):
    return a ^ b ^ c, (a & b) | (a & c) | (b & c)

def popcount7(value):
    x = [(value >> i) & 1 for i in range(7)]
    sa, ca = fa(*x[:3])
    sb, cb = fa(*x[3:6])
    y0, cc = fa(sa, sb, x[6])
    y1, y2 = fa(ca, cb, cc)
    return y0 + 2*y1 + 4*y2

for value in range(128):
    assert popcount7(value) == value.bit_count()
assert popcount7(0b1001101) == 0b100

PROMPT = "נתון Bus בן 7 ביט. תכנן מערכת המורכבת ממחברים, מחסרים FFs וכו' שתספור את מספר האחדות בBus הנתון.\nלדוגמא, עבור (1001101) תתקבל התוצאה 100"
PROMPT_EN = "Given a 7-bit bus, design a system using adders, subtractors, flip-flops, etc. that counts the ones in the bus. For example, input (1001101) produces 100."
TAGS = ['nvidia','hailo','mobileye','inomize','hardware','qualcomm','elta','apple','ceva','marvell','intel','amazon']
COMPANIES = ['NVIDIA','Hailo','Mobileye','Inomize','Qualcomm','Elta','Apple','CEVA','Marvell','Intel','Amazon']
HINTS_HE = [
    'כל ביט תורם לספירה אפס או אחד, ללא קשר למיקומו. מה טווח הספירה וכמה ביטים דרושים לייצוגה?',
    'Full-Adder סופר למעשה את האחדות בשלושה ביטים: a+b+c=S+2C. חלק את הקלט לשתי קבוצות של שלושה ביטים וביט נוסף.',
    'חבר יחד את שני ביטי ה־Sum ואת הביט השביעי. כעת נותרו שלושה Carry בעלי אותו משקל; כיצד אפשר לחבר אותם?'
]
HINTS_EN = [
    'Each input bit contributes zero or one regardless of position. What is the count range and required output width?',
    'A full adder counts the ones in three bits: a+b+c=S+2C. Split the input into two groups of three and one remaining bit.',
    'Add the two sum bits and the seventh input. Three equal-weight carry bits remain; how can they be combined?'
]
HE = '''**הצעה לפתרון — וריאציית 7 ביט:** הקלט x6..x0 והפלט y2..y0 הם בינאריים; התוצאה בטווח 0..7 ולכן דרושים שלושה ביטים. כל ביט קלט תורם 0 או 1 לספירה, ולא לפי משקלו במספר המקורי. הדוגמה 1001101 כוללת ארבע אחדות, ולכן הפלט 100 בבינארי.

מימוש קומבינטורי בארבעה Full-Adders, ללא צורך ב־FF או במחסר:
1. FA1(x0,x1,x2) -> (sA,cA).
2. FA2(x3,x4,x5) -> (sB,cB).
3. FA3(sA,sB,x6) -> (y0,cC).
4. FA4(cA,cB,cC) -> (y1,y2), כאשר y1 הוא Sum ו־y2 הוא Carry.

בכל זוג מוצאים נרשמו Sum ואז Carry. נשאי FA1,FA2,FA3 מייצגים יחידות במשקל 2; לכן מותר לחברם יחד ב־FA4. הוכחה: סכום שבעת ביטי הקלט הוא sA+sB+x6+2(cA+cB)=y0+2(cA+cB+cC)=y0+2y1+4y2. FA1 ו־FA2 פועלים במקביל, אחריהם FA3 ואחריו FA4; עומק תלות של שלוש שכבות מחברים, ללא הנחת זמני השהיה פנימיים שווים.

המימוש משתמש במינימום ארבעה מחברים במודל מוגבל של רשת הפחתת ביטים באמצעות FA/HA ששומרת את סכום עמודות המשקל: דרוש צמצום מ־7 אותות התחלתיים ל־3 אותות תוצאה; FA מצמצם אות אחד ו־HA אינו מצמצם. זו אינה הוכחה למינימום שטח/שערים/השהיה כשמותרים רכיבים שרירותיים, מחסרים או לוגיקה מותאמת. אין בשאלה דרישת מינימום מפורשת. FF מותרים אך אינם נדרשים: אם רוצים דגימה או pipeline, יש להגדיר שעון, latency וליישר אותות בין שלבים. חיבור כל הקלטים במקביל חוסך פרוטוקול סדרתי; אין סופרים רק ביטים השווים ל־1 לאורך זמן.

בדיקות: נבדקו כל 128 הקלטים מול bit_count בפייתון, כולל אפס, כל השבעה דלוקים, כל one-hot והדוגמה. זו בדיקת מודל פונקציונלי ולא HDL או timing פיזי. אין לפרש את פלט 100 כמאה עשרוני.

תעדוף: עדיפות גבוהה לחזרה על יסודות אריתמטיקה בינארית, רוחב תוצאה, משקלי נשאים ותכנון בדיקות; מאחר ששאלת 8 הביט כבר קיימת, זו חזרה קצרה ולא נושא חדש. זו הערכת הכנה לפי התפקיד ולא תחזית לראיון.'''
EN = '''Proposed solution — 7-bit variant: output y2..y0 is the unsigned population count in 0..7. Each input contributes zero or one, not its original binary place value. Input 1001101 contains four ones, so output is binary 100.
Use four full adders with (sum,carry) output convention: FA1(x0,x1,x2)->(sA,cA); FA2(x3,x4,x5)->(sB,cB); FA3(sA,sB,x6)->(y0,cC); FA4(cA,cB,cC)->(y1,y2). All carries into FA4 have weight two. The invariant is sum(inputs)=sA+sB+x6+2(cA+cB)=y0+2(cA+cB+cC)=y0+2y1+4y2. FA1/FA2 are parallel; three adder dependency layers suffice. No flip-flops or subtractors are required for the combinational task. Registered or pipelined alternatives require explicit clock/latency and stage alignment.
Four is minimum only for a weight-preserving FA/HA bit-reduction network: reducing seven signals to three needs four one-signal reductions; each FA reduces by one and HA by zero. This is not a global area/gate/delay lower bound under arbitrary permitted components, nor is optimality explicitly requested. All 128 inputs, including zero, all ones, one-hot and the example, were checked against Python bit_count. Functional model verification only, not HDL or physical timing. High preparation relevance for binary arithmetic, carry weights, output sizing and verification, but this is a short revision of existing PREP-001, not a new topic or an interview prediction.'''

def main():
    p = ROOT/'questions.json'
    raw = p.read_text(encoding='utf-8')
    before = json.loads(raw)
    start = raw.rfind('{', 0, raw.index('"id": "PREP-001"'))
    q, length = json.JSONDecoder().raw_decode(raw[start:])
    assert not any(s['path'] == SOURCE for s in q['sources'])
    q['sources'][0].setdefault('reported_companies', q['reported_companies'].copy())
    q['sources'][0].setdefault('source_tags', q['source_tags'].copy())
    q['sources'][0].setdefault('source_company_badge', q['source_company_badge'])
    source = {'type':'user_supplied_image','path':SOURCE,'received_on':'2026-09-28','role':'seven_bit_bus_variant','source_tags':TAGS,'source_topic_tags':['hardware'],'reported_companies':COMPANIES,'source_company_badge':'אלתא','company_attribution_status':'reported_by_supplied_source_not_independently_verified'}
    q['sources'].append(source)
    for field, values in [('source_tags',TAGS),('reported_companies',COMPANIES)]:
        q[field] = list(dict.fromkeys(q[field]+values))
    q.setdefault('prompt_variants',[]).append({'key':'seven-bit-popcount','source_path':SOURCE,'original_prompt':PROMPT,'translation_en':PROMPT_EN,'input_width':7,'output_width':3,'source_tags':TAGS,'reported_companies':COMPANIES,'source_company_badge':'אלתא','solution_status':'proposed','prepared_hints':{'he':HINTS_HE,'en':HINTS_EN},'solution_he':HE,'solution_en':EN,'verification':{'status':'passed','cases':128,'method':'Exhaustive four-full-adder functional model compared with Python bit_count','script':'solutions/update_prep_001_seven_bit.py'}})
    q['translations']['he']['reference_solution'] += '\n\n'+HE
    q['translations']['en']['reference_solution'] += '\n\n'+EN
    updated = raw[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+raw[start+length:]
    after = json.loads(updated)
    assert after['question_count'] == before['question_count'] == 30
    assert before['questions'][1:] == after['questions'][1:]
    shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-9828a5f8-f730-496c-8c19-08d9e9c27183.png',ROOT/SOURCE)
    p.write_text(updated,encoding='utf-8')
    md=ROOT/q['markdown_path']
    extension = '\n\n## וריאציית מקור: Bus בן 7 ביט\n\n'+PROMPT+'\n\n![צילום המקור לווריאציית 7 ביט](../'+SOURCE+')\n\nתגית מקור: hardware. חברות לפי המקור (לא אומתו): '+', '.join(COMPANIES)+'. תווית ראשית: אלתא.\n\n### שלושה רמזים לווריאציה\n\n'+'\n\n'.join(f'{i+1}. {h}' for i,h in enumerate(HINTS_HE))+'\n\n'+HE+'\n\n### English variant\n\n'+PROMPT_EN+'\n\n'+'\n\n'.join(f'{i+1}. {h}' for i,h in enumerate(HINTS_EN))+'\n\n'+EN+'\n'
    md.write_text(md.read_text(encoding='utf-8')+extension,encoding='utf-8')
    readme=ROOT/'README.md'
    readme.write_text(readme.read_text(encoding='utf-8')+'\nהרחבה ל־PREP-001: נשמרה וריאציית Bus בן 7 ביט עם צילום, תגיות וחברות מקור, שלושה רמזים ופתרון שנבדק לכל 128 הקלטים. הנוסח המקורי בן 8 הביט נשמר; מספר השאלות השונות נשאר 30.\n',encoding='utf-8')
    print('PASS: all 128 seven-bit inputs. Source and bilingual variant saved under PREP-001; 30 unique questions retained.')

if __name__ == '__main__':
    main()
