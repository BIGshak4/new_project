"""Record software work vs circuit depth and counterexample to sum-only solution."""
import json
from pathlib import Path
from prep_027_odd_digit import odd_digit
root=Path(__file__).resolve().parents[1]
he='''### XOR TREE לעומת הלולאה, והאם סכום המערך מספיק?

הקוד עם מצבר XOR הוא צבירה סדרתית, לא עץ מאוזן: result מתעדכן פעם אחת לכל איבר, ולכן זמן הריצה O(n). מאחר ש־XOR אסוציאטיבי, אפשר לארגן את החישוב כעץ מאוזן. לדוגמה, לשמונה איברים: ארבע פעולות XOR בזוגות בשכבה הראשונה, שתי פעולות בשנייה ואחת בשלישית. זה שלוש שכבות, אבל 4+2+1=7 פעולות בסך הכול. בחישוב סדרתי גם עץ כזה דורש Θ(n) עבודה/זמן. בחומרה עם מספיק יחידות מקבילות עומק העץ הוא ceil(log2 n) ושיעור החומרה הוא n−1 רכיבי XOR וקטוריים, או ארבעה שערים ביטיים לכל רכיב עבור ספרות המקודדות בארבעה ביטים; זו ספירת מימוש, לא הוכחת מינימום של כל הפונקציה תחת הבטחת הקלט. במודל מעבדים מקבילי עם מספיק משאבים אפשר לקבל O(log n) עומק חישוב, אך זה מודל שונה מהלולאה ומשאלת הזמן הסדרתית. טעינה סדרתית של הקלט עדיין דורשת O(n) קריאות. אין סתירה לחסם Ω(n) על סך התאים שצריך לקרוא; עומק מקבילי שונה מסך העבודה.

סכום רגיל של הערכים אינו מספיק למציאת הספרה האי־זוגית. שני קלטים חוקיים באותו אורך נותנים אותו סכום ותשובות שונות:
[1,2,2] — סכום 5, הספרה האי־זוגית 1;
[3,1,1] — סכום 5, הספרה האי־זוגית 3.
לכן שום חישוב שמקבל רק את הסכום (ואפילו גם את n) אינו יכול להבחין בין שני הקלטים. מבחינת הסיבוכיות, סריקת סכום היא O(n) זמן ו־O(1) משתנים במודל מילות מכונה, אבל האלגוריתם אינו נכון.

אם ״שארית מחלוקה ב־2״ היא sum % 2, התוצאה היא רק 0 או 1 והכפלה ב־2 נותנת רק 0 או 2. אם הכוונה לחלק השברי של sum/2 ואז הכפלה ב־2, מתקבלת רק 0 או 1. אף פירוש אינו מחזיר ספרה כללית 0..9. הסכום מודולו 2 אכן מגלה אם הספרה המבוקשת זוגית או אי־זוגית: כל ספרה בתדירות זוגית תורמת סכום זוגי, והספרה בתדירות אי־זוגית קובעת את הזוגיות. אבל הוא אינו מגלה איזו ספרה זו. XOR מבטל כל זוג ערכים זהים כערכים ביטיים שלמים, ולכן שומר את כל ביטי הספרה הנותרת ולא רק את הזוגיות שלה.

הזיכרון של מצבר יחיד נקרא O(1) זיכרון עזר, גם ללא מערך נוסף. עבור סכום בגודל בלתי מוגבל נדרשים יותר ביטים כש־n גדל; במודל המקובל מונים מילים/משתנים. הדוגמה הנגדית נבדקה מול המימוש שנשמר; סכומי הקלטים שווים ותשובות ה־XOR שונות.
'''
en='''The accumulator loop is serial O(n), not a balanced XOR tree. Associativity permits a balanced tree: eight operands require layers of 4,2,1 operations, depth 3 but total work 7. In general n-1 pairwise operations and ceil(log2 n) depth. Sequential evaluation is Θ(n); sufficiently parallel hardware/processors achieve O(log n) reduction depth with growing resources, a different model. Digits need four-bit XOR units. Sequential input loading still costs linear reads; the total-read lower bound does not forbid logarithmic parallel depth.

Ordinary sum loses required information. Valid equal-length inputs [1,2,2] and [3,1,1] both sum to 5 but have answers 1 and 3, so no function of only sum and length can solve the problem. (sum % 2)*2 yields only 0 or 2; multiplying the fractional part of sum/2 by 2 yields only 0 or 1. Sum parity reveals target parity, not its identity. XOR cancels equal values across all bit positions. Sum scanning has the proposed linear time and constant word-variable count, but is incorrect; one accumulator is O(1) auxiliary space, not zero memory. Exact unbounded sums grow in bit length. Counterexamples checked against saved XOR implementation.'''
a,b=[1,2,2],[3,1,1]
assert len(a)==len(b) and sum(a)==sum(b)==5
assert odd_digit(a)==1 and odd_digit(b)==3
assert (sum(a)%2)*2==2
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-027"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
q.setdefault('solution_extensions',[]).append({'key':'xor-tree-vs-serial-and-sum-counterexample','content_he':he,'content_en':en,'verification_script':'solutions/update_prep_027_tree_and_sum.py','verification_status':'passed'})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==27 and all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-027')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
print('PREP-027 extended with parallel depth versus sequential work and verified sum-only counterexamples.')
