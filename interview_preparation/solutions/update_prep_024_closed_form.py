"""Add exact Binet form and distinguish it from floating-point evaluation."""
import json
from pathlib import Path
from fractions import Fraction
from prep_024_grasshopper_stairs import count_ways

root=Path(__file__).resolve().parents[1]
he='''### ביטוי סגור כתלות ב־n

כן. בהנחת התחלה בשלב 0, עבור n שלם אי־שלילי:

W(n) = [((1+sqrt(5))/2)^(n+1) - ((1-sqrt(5))/2)^(n+1)] / sqrt(5).

זוהי נוסחת בינה לפיבונאצ׳י עם היסט באינדקס. אם מסמנים phi=(1+sqrt(5))/2 ו־psi=(1−sqrt(5))/2, מקבלים W(n)=(phi^(n+1)−psi^(n+1))/sqrt(5). זהו שוויון מדויק, לא קירוב, וההפרש מבטל את החלק האי־רציונלי כך שמתקבל מספר שלם. למשל W(4)=5,W(5)=8,W(10)=89. גם n=0 נותן 1.

מקור הנוסחה: מנסים פתרון r^n לנוסחת הנסיגה W(n)=W(n−1)+W(n−2). הצבה וחלוקה ב־r^(n−2) נותנות r²=r+1, ששורשיה phi ו־psi. שתי החזקות מקיימות את הנסיגה, ולכן גם הצירוף בנוסחה. עבור n=0 מתקבל (phi−psi)/sqrt(5)=1; עבור n=1 מתקבל (phi²−psi²)/sqrt(5)=(phi−psi)(phi+psi)/sqrt(5)=1. ההתאמה לשני מקרי הבסיס ולנסיגה מוכיחה שהיא W(n).

אפשר גם לכתוב W(n)=round(phi^(n+1)/sqrt(5)) בחשבון ממשי מדויק: |psi|<1 ולכן גודל האיבר שהושמט קטן מ־1/2 לכל n≥0. זו זהות מתמטית עם עיגול לשלם הקרוב, לא הבטחת דיוק עבור float במחשב. עבור n גדול, חישוב בנקודה צפה יכול לעגל לא נכון או לגלוש; לחישוב קוד מדויק עדיפים חיבורי מספרים שלמים או הכפלה מהירה שכבר נשמרו. עצם קיום נוסחה סגורה אינו מוכיח זמן O(1) במחשב: גם חזקות וגודל התוצאה עולים עבודה.

נוסחה מדויקת נוספת עם מספרים שלמים בלבד: W(n)=Σ C(n−k,k) עבור k=0..⌊n/2⌋. היא סוכמת לפי מספר הקפיצות הכפולות; נוסחת בינה היא הביטוי ללא סכום.

בדיקת נוסחת בינה בוצעה בדיוק בחשבון a+b√5 באמצעות שברים רציונליים, ללא float, לכל n=0..100 מול קוד הספירה הקיים.
'''
en='''Closed form (Binet): W(n)=(phi^(n+1)-psi^(n+1))/sqrt(5), where phi=(1+sqrt(5))/2 and psi=(1-sqrt(5))/2. For nonnegative integer n and start at level zero this is exact, not approximate. It follows since phi and psi solve r²=r+1, the expression satisfies the recurrence, and both base values are 1. Examples W(4)=5, W(5)=8, W(10)=89. In exact real arithmetic it also equals round(phi^(n+1)/sqrt(5)) because the omitted term has magnitude below 1/2. Ordinary floating-point computation can fail for large n; exact integer DP or doubling remains preferable for code. Closed form does not imply constant computational cost for powers or unbounded results. The existing binomial sum is an alternative exact integer expression. Verified Binet exactly with rational pairs a+b√5 for n=0..100, without floating point.'''

def mul(x,y):
    a,b=x; c,d=y
    return (a*c+5*b*d,a*d+b*c)
phi=(Fraction(1,2),Fraction(1,2))
psi=(Fraction(1,2),Fraction(-1,2))
p=q=(Fraction(1),Fraction(0))
for n in range(101):
    p=mul(p,phi);q=mul(q,psi)
    # Difference / sqrt(5): A/sqrt(5)+B = B+(A/5)*sqrt(5).
    rational=p[1]-q[1]; irrational=(p[0]-q[0])/5
    assert irrational==0 and rational==count_ways(n)

file=root/'questions.json';s=file.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-024"');start=s.rfind('{',0,start)
record,length=json.JSONDecoder().raw_decode(s[start:])
record.setdefault('solution_extensions',[]).append({'key':'exact-binet-closed-form','content_he':he,'content_en':en,'verification_script':'solutions/update_prep_024_closed_form.py','verification_status':'passed'})
record['translations']['he']['reference_solution']+='\n\n'+he
record['translations']['en']['reference_solution']+='\n\n'+en
s=s[:start]+json.dumps(record,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(s)
assert after['question_count']==24 and all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-024')
file.write_text(s,encoding='utf-8')
md=root/record['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
print('Binet formula saved; 101 exact rational/surd checks passed without floating point.')
