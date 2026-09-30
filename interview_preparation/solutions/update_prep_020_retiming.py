"""Add the user's forward-retiming solution and correct the resource comparison."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
he='''### חלופה שהציע הראל: Retiming והשהיה מרבית של 4.2 ns

זהו כיוון תקין בתנאי שמותר להזיז את רגיסטרי הכניסה ולשנות את חלוקת תקציבי התזמון מול הסביבה. הפתרונות הקודמים של 7.2 ו־4.5 ns השאירו את גבול הרגיסטרים המקורי קבוע. הם אינם שוללים שיפור באמצעות retiming, שהיה חסר בדיון המקורי. אין צורך במכפל נוסף בחלופה הזאת.

נבטל תחילה את המהפך באמצעות החלפת A,B בכניסות ה־MUX הימני, כפי שכבר הוצע. כעת נבצע forward retiming דרך הקופסה השחורה: נסיר את שני רגיסטרי הקלט E,F מהחיבור שלפניה, ונכניס רגיסטר RS אחד אחרי מוצאה. הכניסות שהזינו קודם את E,F יזינו כעת ישירות את הקופסה השחורה. אין להשאיר את E,F במקומם ורק להוסיף RS.

```text
לפני:
e_in -> [E] --\
               Black Box -> S -> MUXים -> מכפל -> מוצא
f_in -> [F] --/
a_in..d_in -> [A,B,C,D] -------> נתוני ה־MUXים

אחרי:
e_in -------\
             Black Box -> [RS] -> S -> MUXים -> מכפל -> מוצא
f_in -------/
a_in..d_in -------> [A,B,C,D] -------> נתוני ה־MUXים
```

בכל חזית שעון A,B,C,D דוגמים את ארבעת ערכי הנתונים של אותה עסקה. RS דוגם את f(e_in,f_in) של אותה עסקה, שכבר חושב לפני החזית. לכן לאחר החזית, אות הבחירה והנתונים מתאימים זה לזה. פורמלית, במקור S[k]=f(E[k],F[k]); לאחר retiming RS[k]=f(e_in[k],f_in[k]), כאשר E[k],F[k] במקור הם בדיוק הדגימות e_in[k],f_in[k]. לכן הפונקציה הנצפית לאחר כל חזית נשמרת, בתנאי שהקלטים עומדים בתזמון החדש.

אם במקום זאת משאירים E,F ומוסיפים אחריהם RS, הוא ידגום בחזית את f(E[k−1],F[k−1]) בעוד A..D כבר דגמו את עסקה k. אז יש ערבוב בין בחירה ישנה לנתונים חדשים. למשל עם A=2,B=3,C=4,D=5, מעבר S מ־0 ל־1 צריך לשנות את המוצא מ־12 ל־10; רגיסטר בחירה נוסף בלבד ישאיר בחירה 0 ויחזיר 12. אפשר לפתור pipeline כזה בעיכובים תואמים לנתונים, אבל זה כבר דורש משאבים/לטנטיות אחרים.

אחרי ההזזה, המקטע שלפני RS מכיל רק את הקופסה השחורה: 3 ns. המקטע שמיציאות A..D ו־RS עד המוצא מכיל MUX ואז מכפל: 1.5+2.7=4.2 ns. לכן ההשהיה המרבית בין גבולות הדגימה/הממשק היא max(3,4.2)=**4.2 ns** במודל האידאלי, בהנחה שהסביבה מקצה מחזור למקטע הקלט ומחזור למקטע המוצא ושהגבולות ניתנים להזזה. יש לוודא שכל מסלולי המערכת, כולל הממשקים, עומדים בתקציב זה.

השרטוט המקורי אינו כולל רגיסטר קליטה במוצא ואינו נותן clock-to-Q, setup, hold, skew או זמני הגעת קלטים. לכן 4.2 ns הוא המקסימום הקומבינטורי של המקטעים, ולא זמן מחזור פיזי מובטח מהנתונים בלבד. בתכנון סינכרוני מלא מוסיפים clock-to-Q ו־setup ובודקים את האילוצים. התזמון החדש מחייב שהקלטים e_in,f_in יהיו זמינים מוקדם מספיק לפני דגימת RS: יש כעת קופסה של 3 ns לפניה. לא ניתן להזיז רגיסטרים המוגדרים כגבולות I/O קשיחים בלי להתאים את הממשק.

אין צורך לתאר זאת אוטומטית כ״הוספת שני מחזורי שעון״. זו הזזה של גבול דגימה: בכל מסלול מהקלט החיצוני אל המוצא נשאר רגיסטר אחד, וניתן לשמור על מספר מחזורי ההשהיה הלוגי. מוסיפים לטנטיות רק אם מוסיפים שלב דגימה נוסף במקום להזיז ולמזג את הרגיסטרים הקיימים. ההשהיה הפיזית מרגע קלט נתון ועד פלט מושפעת גם ממיקומו ביחס לחזית השעון.

**מספר הרגיסטרים:** לאחר מיזוג רגיסטרי E,F דרך פונקציה קומבינטורית בעלת מוצא בחירה יחיד, מספיקים ארבעת רגיסטרי הנתונים ורגיסטר RS: חמישה בלוקים לוגיים, לא בהכרח שישה בשימוש. מותר להותיר משאב עודף לא מחובר אם הדרישה היא לא להוסיף רכיבים. אין להסיק מכך ספירת FF פיזיים, משום שרוחבי E,F ורגיסטרי הנתונים אינם נתונים. אם רוצים להציב את הרגיסטר העודף במוצא, צריך לבדוק גם את רוחב המכפלה וגם את השינוי בלטנטיות/ממשק; אין להניח שרגיסטר קיים צר מתאים למכפלה רחבה.

Retiming מחייב גם שהקופסה השחורה קומבינטורית, שרגיסטרי E,F ניתנים להזזה ושאין להם שימושים נוספים שלא טופלו, ושיש התאמה של clock, enable ו־reset. במקרה של אתחול ידוע, צריך לאתחל RS לערך f(E_reset,F_reset); איפוס אוטומטי של RS ל־0 אינו נכון לכל פונקציה שחורה. בפונקציה לא ידועה לא ניתן לקבוע את ערך האתחול הזה ללא מידע נוסף. זה אינו פוסל את הרעיון אלא מגדיר את תנאי שקילותו.

המסקנה: אם השאלה מתירה retiming של הרגיסטרים הנתונים, זו חלופה טובה יותר מבחינת המקטע הקריטי האידאלי מהחלופות שהוצגו קודם: **4.2 ns עם מכפל אחד**. היא משנה את מיקום הרגיסטרים ותקציב התזמון של הממשק, בעוד חלופת **4.5 ns עם שני מכפלים** משאירה את רגיסטרי המקור במקומם. לכן חשוב לציין מה מותר לשנות. אין כאן הוכחת מינימום מוחלט.

מקורות טכניים: [Intel — שילוב רגיסטרי כניסה לרגיסטר אחרי לוגיקה באמצעות Retiming](https://www.intel.com/programmable/technical-pdfs/683230.pdf), ו־[Intel — מגבלות Retiming, אתחול וממשקים](https://www.intel.com/content/www/us/en/docs/programmable/683236/23-4/retiming-restrictions-and-workarounds.html). המקורות מתארים את הטכניקה והמגבלות הכלליות; תוצאת 4.2 ns נגזרת מנתוני השאלה.

בדיקת מודל: כל 16 פונקציות בוליאניות אפשריות של קופסה שחורה עם שני קלטי ביט, וכל 16,384 צירופי עסקה עם A..D בני שני ביטים, נתנו אותה תוצאה לפני ואחרי retiming נכון. נוסף מקרה נגדי להוספת RS בלבד. מיפוי האתחול ותנאי יציבות הקלטים מתועדים; אין כאן אימות setup/hold, STA או בדיקת חומרה פיזית. [בדיקת המודל](../checks/check_prep_020_retiming.py).
'''
en='''User-proposed forward retiming is valid if the input registers and interface timing may change. Remove E,F from before the combinational black box and put a selector register RS after it. Raw e_in,f_in now feed the box; A..D remain registered. RS captures f(e[k],f[k]) on the same edge that A..D capture transaction k, preserving cycle values under the new setup requirements. Merely appending RS while retaining E,F misaligns old select with new data unless matching delays are added.

After eliminating select inversion by swapping mux data inputs, the pre-RS segment is 3 ns and the post-register mux/multiplier segment is 4.2 ns. Their ideal maximum is 4.2 ns, with one multiplier. This is conditional on a synchronous environment allocating appropriate input/output timing budgets; the source omits an output capture register and register/setup/wiring delays, so it is not a proven physical clock period. Forward retiming need not add cycles: each primary-input-to-output path still has one register. Only four data registers plus RS are logically required, so the six original register blocks need not all remain in use; physical widths and spare output-register feasibility are unspecified.

Preserve reset via RS_reset=f(E_reset,F_reset), clocks/enables and any other E/F fanouts. Fixed I/O boundaries can prohibit the move. Previous 7.2/4.5 ns options assumed fixed register placement; the discussion is corrected to include this legitimate alternative. No global minimum claim. Exact transaction-value checks covered 16,384 cases across all 16 two-input Boolean BB functions, plus a counterexample for appended-only RS. No STA or physical setup/hold verification.'''
p=root/'questions.json';s=p.read_text(encoding='utf-8');start=s.index('{\n      "id": "PREP-020"')
q,n=json.JSONDecoder().raw_decode(s[start:])
old_he=q['translations']['he']['reference_solution'];old_en=q['translations']['en']['reference_solution']
q['retiming_alternative']={'origin':'user_proposed_retiming_in_chat','display_section':'הצעה לפתרון','he':he,'en':en,
 'verification_script':'checks/check_prep_020_retiming.py','verification_scope':'Conditional edge-value model, not physical timing proof.',
 'ideal_max_segment_ns':4.2,'multiplier_count':1,'logical_register_blocks_required':5}
if he not in old_he:q['translations']['he']['reference_solution']=old_he+'\n\n'+he
if en not in old_en:q['translations']['en']['reference_solution']=old_en+'\n\n'+en
q['optimality']['result']='Original 7.3 ns; fixed-register input-swap improvement 7.2 ns; fixed-register extra-multiplier alternative 4.5 ns; forward retiming can give ideal maximum segment 4.2 ns with one multiplier if boundary/initial-state conditions permit.'
q['optimality']['scope']='Conditional improvements under distinct register-boundary/resource assumptions; no global minimum or physical clock-period proof.'
q['assumptions'].append('Retiming alternative permits moving/merging E,F across a combinational BB, with input timing, fanout and reset/enable/clock compatibility preserved; no forced latency increase.')
old_short=q['interview_answer']
q['interview_answer']='המסלול הקריטי המקורי הוא 7.3 נ״ש. החלפת כניסות המוקס מסירה מהפך ונותנת 7.2. ברגיסטרים קבועים, מכפל נוסף מאפשר חישוב שתי התוצאות במקביל ו־4.5. אם מותר retiming, מעבירים את גבול הדגימה מ־E,F אל מוצא הקופסה השחורה, תוך התאמת הדגימות והממשק; מתקבלים מקטעים של 3 ו־4.2 נ״ש עם מכפל אחד, ללא הוספת מחזור בהכרח.'
q['technical_references']=[
 {'title':'Intel Quartus Prime Standard Edition User Guide: Design Optimization — Combining Registers with Register Retiming','url':'https://www.intel.com/programmable/technical-pdfs/683230.pdf'},
 {'title':'Intel Quartus Prime Pro Edition User Guide — Retiming Restrictions and Workarounds','url':'https://www.intel.com/content/www/us/en/docs/programmable/683236/23-4/retiming-restrictions-and-workarounds.html'}]
r=json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
p.write_text(s[:start]+r+s[start+n:],encoding='utf-8')
md=root/q['markdown_path'];t=md.read_text(encoding='utf-8')
if he not in t:
    t=t.replace(old_he,q['translations']['he']['reference_solution'],1)
    t=t.replace(old_en,q['translations']['en']['reference_solution'],1)
t=t.replace(old_short,q['interview_answer'],1)
md.write_text(t,encoding='utf-8')
readme=root/'README.md';t=readme.read_text(encoding='utf-8')
note='\nהרחבה ל־PREP-020: חלופת Retiming שהציע הראל מאפשרת מקטע קריטי אידאלי של 4.2 ns עם מכפל אחד, אם מותר לשנות את מיקום רגיסטרי הכניסה ואת תקציבי התזמון; נשמרו תנאי שקילות, אתחול ובדיקת דגימות.\n'
if note not in t:readme.write_text(t+note,encoding='utf-8')
data=json.loads(p.read_text(encoding='utf-8'));assert len(data['questions'])==data['question_count']==20
assert he in md.read_text(encoding='utf-8')
print('PREP-020 updated: user retiming alternative, conditional 4.2 ns result, corrected comparison, technical references and tested cycle-value assumptions.')
