"""Document the multi-ball extension including guaranteed-break convention."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### איך מספר הכדורים משנה את התשובה?

עבור אותו בניין של 100 קומות, מספר הזריקות המינימלי במקרה הגרוע הוא:

| מספר כדורים | מותר שלא תהיה קומה שוברת | מובטח שיש קומה שוברת ב־1..100 |
|---|---|---|
| 1 | 100 | 99 |
| 2 | 14 | 14 |
| 3 | 9 | 9 |
| 4 | 8 | 8 |
| 5 ומעלה | 7 | 7 |

ההבדל בכדור אחד: אם מובטח שיש קומה שוברת וקומות 1..99 שרדו, אפשר להסיק ש־100 היא הסף בלי לזרוק ממנה. אם ייתכן שאף קומה לא שוברת, חייבים לבדוק גם אותה כדי להבחין בין F=100 ל־F=101. תוצאות 2 כדורים ומעלה בטבלה אינן משתנות. האמירה ״מובטח שיש סף״ יחד עם מונוטוניות שקולה לידיעה שקומה 100 שוברת.

**האינטואיציה:** עם שני כדורים, השבירה הראשונה משאירה כדור אחד ומחייבת סריקה קומה־קומה. עם שלושה כדורים, השבירה הראשונה משאירה שניים, ואפשר להשתמש באסטרטגיית שני הכדורים בטווח שמתחת. לכן מותר להעז ולקפוץ רחוק יותר בהתחלה. לדוגמה, עם שלושה כדורים ותקציב תשע זריקות, אפשר להתחיל בקומה 37: אם נשבר נשארו 36 קומות, שני כדורים ושמונה זריקות, המספיקות כי 8+7+...+1=36. אם שרד, נשארו 63 קומות, שלושה כדורים ושמונה זריקות — מספיק, כי הכיסוי שלהן הוא 8+28+56=92. זו אסטרטגיה תקפה, לא בחירה יחידה לקומה הראשונה. ככל שנשארים יותר כדורים אחרי שבירה, אפשר לבדוק טווח גדול יותר במשאבים שנותרו.

**הכלל המדויק:** C(b,t) הוא מספר הקומות הלא־ידועות המרבי שאפשר לבדוק עם b כדורים ועד t זריקות, כולל יכולת להבחין במקרה שבו אין שבירה. בזריקה הבאה:
* אם נשבר, נשארים b−1 כדורים ו־t−1 זריקות לטווח התחתון.
* אם שרד, נשארים b כדורים ו־t−1 זריקות לטווח העליון.
* הקומה שנבדקה תורמת עוד 1.

לכן C(b,t)=C(b−1,t−1)+1+C(b,t−1), עם C(0,t)=C(b,0)=0. הפתרון הוא C(b,t)=Σ C(t,j), j=1..min(b,t), כאשר C(t,j) בסכום הוא המקדם הבינומי, לא אותה פונקציית כיסוי. כדי להימנע מערבוב סימונים, אפשר לכתוב את המקדם binom(t,j).

בחירת t המינימלי שעבורו C(b,t)≥100 נותנת את הטבלה במודל שבו אין הבטחת שבירה. אם ידוע שקומה 100 שוברת, יש רק 99 קומות לא ידועות ומספיק C(b,t)≥99. לשלושה כדורים: C(3,8)=92 לעומת C(3,9)=129, ולכן תשע זריקות. לארבעה: C(4,7)=98 לעומת C(4,8)=162, לכן שמונה. לחמישה: C(5,6)=62 לעומת C(5,7)=119, לכן שבע.

לא יורדים משבע גם עם הרבה כדורים: כל זריקה נותנת שתי תוצאות בלבד. שש זריקות מבחינות לכל היותר ב־2^6=64 אפשרויות, פחות מ־100 ערכי סף (או 101 כשמותר ללא שבירה). חשוב: ״חמישה כדורים מספיקים לשבע״ לא אומר שחיפוש בינארי רגיל שרירותי תמיד ישמור על תקציב חמישה כדורים. צריך לבחור קומות לפי כיסוי שני הענפים. עם מלאי כדורים מספיק גם חיפוש בינארי רגיל משיג את חסם שבע הזריקות.

קוד כללי נשמר ב־solutions/prep_025_multiple_balls.py. הוא בוחר בכל מצב קומה מעל הקומה הבטוחה האחרונה לפי C(b−1,t−1)+1, תוך חיתוך לטווח הנוכחי. נבדקו כל 606 תרחישי הסף לבניין 100 קומות עם 1..6 כדורים, והאופטימום הושווה בנפרד לתכנון דינמי minimax לכל 0..150 קומות ו־1..6 כדורים. נבדקו גם נוסחת הכיסוי וההבדל בין קומה עליונה ידועה לשוברת לבין מקרה ללא הבטחה.
'''
en='''For 100 floors, optimal worst-case drop counts by ball count are: one ->100 (99 if floor 100 is known breaking); two ->14; three ->9; four ->8; five or more ->7. Guaranteed existence of a breaking floor plus monotonicity means the top floor is known breaking, leaving 99 unknown floors. Without that guarantee there are 101 threshold cases and 100 unknown floors.

The extra ball matters after breakage: three balls leave two, enabling interval jumps instead of a one-ball linear scan. With three balls and nine drops one valid first floor is 37. Breakage leaves 36 lower floors, two balls and eight drops (capacity 36); survival leaves 63 upper floors, three balls and eight drops (capacity 92).

Coverage C(b,t)=C(b-1,t-1)+1+C(b,t-1), with zero balls or zero drops giving zero coverage. Equivalently C(b,t)=sum binom(t,j), j=1..min(b,t). Seek minimum t with coverage >=100, or >=99 for a known-breaking top. C(3,8)=92,C(3,9)=129; C(4,7)=98,C(4,8)=162; C(5,6)=62,C(5,7)=119. Six binary-result drops distinguish at most 64 outcomes, less than 100 or 101 threshold possibilities; hence seven is a lower bound regardless of additional balls. Five balls suffice with a capacity-aware strategy, not necessarily an arbitrary balanced binary-search tree constrained to five balls.

Verified 606 complete 100-floor threshold scenarios for 1..6 balls and independent minimax DP for 0..150 floors with 1..6 balls, plus recurrence and guaranteed-top conventions. Code and checks linked in the extension.'''
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-025"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
q.setdefault('solution_extensions',[]).append({'key':'arbitrary-number-of-balls','content_he':he,'content_en':en,'code_path':'solutions/prep_025_multiple_balls.py','check_path':'checks/check_prep_025_multiple.py','verification_status':'passed','hundred_floor_table':{'no_break_possible':{'1':100,'2':14,'3':9,'4':8,'5+':7},'guaranteed_breaking_top':{'1':99,'2':14,'3':9,'4':8,'5+':7}}})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==25 and all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-025')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n[קוד כללי](../solutions/prep_025_multiple_balls.py) · [בדיקת האופטימום](../checks/check_prep_025_multiple.py)\n\n'+en+'\n',encoding='utf-8')
print('PREP-025 extended with arbitrary ball counts, exact table, coverage strategy/proof and known-top convention; 25 questions retained.')
