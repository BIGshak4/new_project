"""Preserve clarified NOR-prefix polarity and primitive-gate preference."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### שימוש ב־NOR כשער בסיסי: קוטביות תוצאת הביניים

בהמשך לבקשת הראל, כשאין הגבלה מפורשת יש להתייחס גם ל־NOR ול־NAND כשערים זמינים בפני עצמם, ולא לפרק אותם אוטומטית ל־OR/AND ו־NOT. עדיין יש לציין מספר כניסות וספריית שערים כשסופרים רכיבים או טוענים לאופטימליות.

הנוסח Y7=X7, Y6=X6 AND NOT(X7), N5=NOR(X6,X7), Y5=X5 AND N5 תקין. אבל N4=NOR(N5,X5) אינו ההמשך הנכון: N5=1 פירושו שאין שום 1 ב־X7,X6, בעוד שחוט OR מצטבר היה מציין את ההפך. NOR נוסף על N5 אינו מרחיב את אותה בדיקה.

דוגמה נגדית: X7=1,X6=0,X5=0,X4=1 (אפשר להשלים לקלט 10010000). מתקבל N5=0, ואז NOR(N5,X5)=NOR(0,0)=1, ולכן הנוסח השגוי מוציא גם Y4=1, אף ש־X7 כבר היה ה־1 השמאלי ביותר.

ההמשך הנכון שומר על המשמעות ״כל הביטים הגבוהים אפס״:
N6=NOT(X7);
N5=NOR(X7,X6);
N4=N5 AND NOT(X5);
N3=N4 AND NOT(X4);
N2=N3 AND NOT(X3);
N1=N2 AND NOT(X2);
N0=N1 AND NOT(X1);
Yi=Xi AND Ni עבור i=6..0, ו־Y7=X7.

באופן שקול, N4=NOR(NOT(N5),X5), ולא NOR(N5,X5). אם רוצים לרשום את הפונקציה ישירות בשער NOR רחב, N4=NOR(X7,X6,X5), N3=NOR(X7,X6,X5,X4), וכן הלאה. אלה שערים מרובי כניסות, ויש לציין שמותר להשתמש בהם; פירוק לשערים דו־כניסתיים מחייב טיפול נכון בקוטביות. לא ניתן פשוט לשרשר NOR כאילו היה OR.

חלופת NOR רחב: Y7 חוט ישיר; Y6 דורש NOT ו־AND; Y5..Y0 דורשים כל אחד NOR ברוחב מתאים ו־AND. אם NOR ברוחב 2..7 הוא תא בסיסי יחיד ו־NOT תא יחיד, הספירה היא 6 NOR+1 NOT+7 AND=14 תאים. זו ספירה במודל שונה ממודל 20 שערי AND/OR/NOT דו־כניסתיים, ואינה טענה למינימום פיזי או לשטח שווה לכל שער. המקרה של Y0 נכלל — יש שמונה יציאות, לא שבע.

בדיקה: מודל התנאי המצטבר המתוקן וה־NOR הישיר עברו את כל 256 הקלטים מול בידוד ה־1 הגבוה ביותר; הדוגמה הנגדית להמשך השגוי נבדקה.
'''
en='''NOR/NAND are treated as available primitive gates unless explicitly restricted; fan-in and the gate library must still be stated for counts. N5=NOR(X7,X6) means all higher bits are zero. Thus the proposed recurrence N4=NOR(N5,X5) is wrong: at input 10010000, N5=0 and the proposed N4=1 incorrectly passes bit 4. Correct recurrence is N4=N5 AND NOT(X5), equivalently NOR(NOT(N5),X5). In general Ni=N(i+1) AND NOT(X(i+1)), with N6=NOT(X7), yi=xi AND Ni and y7=x7. Direct wide NOR of all higher inputs is also valid; NOR is not associative like OR. Under an explicit library containing 2..7-input NOR primitives, the direct design has six NOR, one NOT and seven AND cells (14), not an equal-area or global optimality claim. Include y0. All 256 inputs checked for corrected recurrence and direct formulation; invalid recurrence has a tested counterexample.'''
for x in range(256):
    expected=0 if x==0 else 1<<(x.bit_length()-1)
    y=((x>>7)&1)<<7
    n=1-((x>>7)&1)
    for i in range(6,-1,-1):
        y|=(((x>>i)&1)&n)<<i
        if i>0:
            n=n & (1-((x>>i)&1))
    direct=sum((((x>>i)&1) & int(x>>(i+1)==0))<<i for i in range(8))
    assert y==direct==expected
x=0b10010000
n5=int(not(((x>>7)&1) or ((x>>6)&1)))
bad_n4=int(not(n5 or ((x>>5)&1)))
assert bad_n4 & ((x>>4)&1)==1
p=root/'questions.json';s=p.read_text(encoding='utf-8');before=json.loads(s)
start=s.index('"id": "PREP-014"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
q.setdefault('solution_extensions',[]).append({'key':'nor-prefix-polarity','created_on':'2026-09-28','content_he':he,'content_en':en,'verification_script':'solutions/update_prep_014_nor_recurrence.py','verification_status':'passed'})
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
updated=s[:start]+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')+s[start+length:]
after=json.loads(updated)
assert after['question_count']==22 and all(x==y for x,y in zip(before['questions'],after['questions']) if x['id']!='PREP-014')
p.write_text(updated,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n'+en+'\n',encoding='utf-8')
r=root/'README.md';t=r.read_text(encoding='utf-8');t+='\nהעדפת הראל מ־28 בספטמבר: בשאלות שערים להתייחס גם ל־NOR ול־NAND כשערים בסיסיים זמינים כל עוד אין הגבלה אחרת; לא לפרק אותם אוטומטית ל־NOT ו־AND/OR. בספירת שערים ובטענות אופטימליות להבהיר מספר כניסות וספריית שערים.\n';r.write_text(t,encoding='utf-8')
print('PREP-014 NOR-polarity correction saved; all 256 inputs checked; primitive-gate preference recorded.')
