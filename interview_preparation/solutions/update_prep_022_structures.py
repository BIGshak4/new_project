"""Document non-array alternative, rejection-sampling tradeoff and active-prefix version."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
he='''### הרחבה: סעיף א עם מבנה שאינו מערך, וסעיף ב עם מערך

הקלט הוא רק N. כל מבנה להלן נוצר על ידינו במהלך הפתרון. אין לדעת מהניסוח מה בדיוק ציפה המראיין; סעיף א מתיר מערך ולא מחייב פתרון אחר. להלן גם פתרון תקף ללא מערך.

**אפשרות טבעית לסעיף א — set:** ניצור קבוצה ריקה של מספרים שהודפסו. נגריל rand(N); אם המספר חדש נדפיס ונכניס לקבוצה, ואם כבר קיים נגריל שוב. כך לא מדפיסים כפילויות. אבל כשהודפסו N−1 מספרים, הסיכוי לקבל את האחרון בכל ניסיון הוא 1/N. בהנחת הגרלות אחידות ועצמאיות ופעולות hash בתוחלת O(1), מספר ההגרלות הצפוי הוא N×(1/N+1/(N−1)+...+1)=Θ(N log N), והמקום O(N). אין חסם סופי למספר ההגרלות במקרה הגרוע. לכן זו אפשרות להסבר ראשוני, לא הבחירה הטובה ביותר לבקשת היעילות בזמן. שימוש ב־set אינו מספק כשלעצמו גישה בזמן קבוע לאיבר במיקום אקראי; המרתו לרשימה בכל צעד מוסיפה עבודה ומערך.

**סעיף א — פתרון יעיל עם מילון (טבלת גיבוב):** המילון ממפה מיקום פעיל למספר שנותר: בהתחלה {1:1,2:2,...,N:N}. המפתחות הפעילים הם בדיוק 1..m. בוחרים r=rand(m), מדפיסים את remaining[r], מעתיקים למפתח r את הערך שבמפתח m, מוחקים את המפתח m ומקטינים את m. כך מוציאים את המספר שנבחר בלי להשאיר חור בטווח המפתחות. אם r=m, ההשמה היא לעצמו ואחריה מוחקים את אותו מפתח — גם זה תקין. בדוגמה N=5, אחרי בחירת מפתח 2 והדפסת 2, המילון הוא {1:1,2:5,3:3,4:4}. עכשיו rand(4) בוחרת רק בין ארבעת המספרים שנותרו.

זמן כולל Θ(N) בתוחלת בהנחת פעולות טבלת גיבוב בתוחלת O(1) ו־rand בזמן קבוע; מקום O(N). זה אינו חסם גרוע־ביותר בלתי מותנה לטבלת גיבוב. המילון משמש כמערך לוגי צפוף של מיקומים, אך מבנה הנתונים בקוד הוא מילון. אין לו כאן יתרון על מערך; הוא מוצג כחלופה שאינה מערך, כפי שהתבקש. בחירת מבנה נתונים מתייחסת להפשטה ולממשק, לא לאופן שבו ספריית Python מממשת פנימית את המילון.

**סעיף ב — מערך:** יוצרים [1,2,...,N]. רק m התאים הראשונים משתתפים בהגרלה. בוחרים j=rand(m)−1, מדפיסים arr[j], מחליפים את arr[j] עם arr[m−1] ומקטינים m. האיבר שנבחר נשאר בחלק הלא פעיל ולא ייבחר שוב. למשל [1,2,3,4,5] הופך אחרי בחירת 2 ל־[1,5,3,4 | 2], ובהמשך אחרי בחירת 3 ל־[1,5,4 | 3,2]. הפלט עד כאן 2,3. אין צורך למחוק פיזית או להזיז את כל האיברים.

זו גרסת קיבוע הסוף של Fisher–Yates, שקולה ברעיון לגרסת קיבוע ההתחלה המקורית שבמאגר. כאן מדפיסים את הבחירות מיד; אין להדפיס שוב את המערך בסיום, כי זה יכפיל את הפלט. זמן Θ(N) ומקום O(N) למערך, עם O(1) זיכרון עזר. עבור אותו רצף מיקומים אקראיים, חלופות המילון והמערך מפיקות בדיוק אותו רצף מספרים.

בשתיהן כל אחד מ־m המספרים שנותרו נבחר בהסתברות 1/m, ולכן כל פרמוטציה מתקבלת בהסתברות 1/N! בהנחת אחידות. N=0 נותן פלט ריק; N=1 דורש רק הדפסת 1. אפשר לחסוך את ההגרלה האחרונה כי נשאר מספר אחד בלבד.

**מימושים בדוקים:** permutation_with_dict ו־permutation_with_array בקובץ הקוד הם מחוללים (yield): הם מפיקים ערך אחד בכל שלב בלי לבנות רשימת פלט נוספת. להדפסה: for value in permutation_with_dict(N, rand): print(value), ובאופן זהה עם פונקציית המערך. החלפת yield chosen ב־print(chosen) נותנת פונקציית הדפסה ישירה. נבדקו כל 5,914 מסלולי ההגרלה ל־N=0..7 עבור שני המימושים, כולל שוויון פלט לכל מסלול, בדיוק N! תמורות לכל גודל, גבולות rand, 12 תרחישי קצה גדולים וקלטים לא תקינים.'''
en='''### Extension: non-array part (a), array part (b)

Only N is supplied; every container is constructed by the algorithm. The source does not mandate a non-array structure in (a), nor establish an interviewer expectation. A natural set-of-used-values rejection sampler prints only new rand(N) draws. It is correct under independent uniform draws but takes N H_N = Θ(N log N) expected draws, O(N) space and has no finite worst-case draw bound. A set alone offers no constant-time uniformly indexed element selection.

An efficient non-array alternative uses a hash dictionary mapping active positions to remaining values, initialized as {1:1,...,N:N}. With active keys 1..m, pick r=rand(m), emit remaining[r], assign remaining[r]=remaining[m], delete remaining[m], then decrement m. This keeps the keys dense even when r=m. Expected Θ(N) time assumes expected O(1) hashing and bounded RNG; total storage O(N). It is not an unconditional worst-case hash-table bound. It offers no practical advantage over the array here; it satisfies the requested distinct data-structure example.

For (b), create [1,...,N], maintain active prefix length m, pick j=rand(m)-1, emit arr[j], swap arr[j] and arr[m-1], and decrement m. The emitted value is excluded from future draws without shifting. This is the shrinking-prefix variant of Fisher–Yates and yields exactly the same emitted values as the dictionary variant given identical draw positions. Do not print the complete array again after already emitting choices. Time Θ(N), total array space O(N), extra shuffle space O(1). For either method skip the last draw when m=1; N=0 yields nothing. Uniform conditional draws give each permutation probability 1/N!.

The code provides generators permutation_with_dict and permutation_with_array; iterate and print their yielded values to avoid accumulating another output list. Both were exhaustively checked on 5,914 draw paths for N=0..7, with N! unique outputs per size, identical per-path output, exact RNG bounds, 12 larger boundary cases and invalid-input tests.'''
p=root/'questions.json';s=p.read_text(encoding='utf-8');original=json.loads(s)
start=s.index('"id": "PREP-022"');start=s.rfind('{',0,start)
q,length=json.JSONDecoder().raw_decode(s[start:])
assert q['id']=='PREP-022'
q['translations']['he']['reference_solution']+='\n\n'+he
q['translations']['en']['reference_solution']+='\n\n'+en
q.setdefault('solution_extensions',[]).append({'key':'dictionary-and-active-array','title_he':'סעיף א עם מילון וסעיף ב עם מערך','content_he':he,'content_en':en,'code_path':'solutions/prep_022_random_permutation.py','check_path':'checks/check_prep_022_structures.py'})
q['verification']['additional_checks']=[{'script_path':'checks/check_prep_022_structures.py','status':'passed','method':'5914 exhaustive paths per algorithm, exactly N! outputs, identical dictionary/array output for every path, RNG bounds, 12 larger boundary cases and input validation.'}]
q['interview_answer']='סעיף א מאפשר גם מערך, אך אם נדרש מבנה אחר אפשר מילון הממפה מיקום למספר שנותר: בוחרים מפתח ב־1..m, מוציאים את ערכו וממלאים את החור עם הערך של מפתח m. במערך עושים אותו דבר בהחלפה עם התא האחרון בחלק הפעיל. בשניהם אין חזרות וכל תמורה אחידה בהנחת rand אחידה. במערך הזמן Θ(N), במילון Θ(N) בתוחלת תחת פעולות hash בתוחלת קבועה, והמקום O(N). set עם הגרלה מחדש הוא אפשרות פשוטה אך איטית יותר בתוחלת.'
replacement=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
s=s[:start]+replacement+s[start+length:]
parsed=json.loads(s)
assert parsed['questions'][:-1]==original['questions'][:-1] and parsed['question_count']==22
p.write_text(s,encoding='utf-8')
md=root/q['markdown_path'];md.write_text(md.read_text(encoding='utf-8')+'\n\n'+he+'\n\n[בדיקת החלופות](../checks/check_prep_022_structures.py)\n\n'+en+'\n',encoding='utf-8')
print('PREP-022 expanded: dictionary, set tradeoff and shrinking-prefix array; both languages and verified code linked.')
