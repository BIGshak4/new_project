"""Store the three-person/five-hat inference puzzle and all answer branches."""
import json
import shutil
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'checks'))
from check_prep_033 import check
check()

prompt='''ישנם 5 כובעים: 3 כובעים לבנים ו־2 כובעים שחורים. שלושה אנשים נעמדים בתור כאשר כל אחד רואה רק את מי שלפניו: האחרון מביניהם רואה את השניים שלפניו, האמצעי רואה רק את הראשון והראשון לא רואה אף אחד. כל השלושה עוצמים עיניים ועל ראשיהם שמים 3 כובעים. שואלים את האחרון האם הוא יודע מה הצבע של הכובע שעל ראשו כך שהשניים שלפניו שומעים. אחר כך שואלים את האמצעי האם הוא יודע מה הצבע שעל ראשו כך שהראשון שומע. בסוף שואלים את הראשון האם הוא יודע מה צבע הכובע שעל ראשו?
האם הראשון יכול תמיד לדעת מה הצבע שעל ראשו?'''
ep='''There are five hats: three white and two black. Three people stand in a line. The rear person sees the two in front, the middle person sees only the front person, and the front person sees nobody. They close their eyes while three hats are placed on their heads. The rear person is asked whether they know their own hat color, and the other two hear the answer. The middle person is then asked the same question, and the front person hears the answer. Finally, the front person is asked whether they know their own color. Can the front person always know?'''
hints=[
 'התחל מהאחרון: באיזה צירוף כובעים שהוא רואה הוא יכול לדעת בוודאות מה צבע הכובע שלו, בלי לשמוע אף תשובה?',
 'גם תשובת ״לא יודע״ מוסיפה מידע. איזה צירוף כובעים אצל השניים שמלפנים היא שוללת?',
 'הפרד בין מצב שבו האחרון יודע לבין מצב שבו אינו יודע. בענף השני, בדוק מה האמצעי היה מסיק אילו ראה כובע שחור על הראשון, ומה היה מסיק אילו ראה לבן.'
]
eh=[
    'When can the rear person determine their own color from the two visible hats alone?',
    'An answer of I do not know also adds information. Which visible pair does it rule out?',
    'Split on whether the rear knows. In the no branch, compare what the middle person could infer on seeing a black versus a white front hat.'
]
he='''הנחות: אחרי הנחת הכובעים פוקחים עיניים ורואים בהתאם לתיאור. כולם יודעים שיש שלושה לבנים ושני שחורים, מבינים את סדר השאלות, שומעים את התשובות הרלוונטיות ומסיקים מסקנות נכונות. ״יודע״ פירושו ודאות מכל המידע הזמין, לא ניחוש; כולם עונים בכנות. שני הכובעים שלא חולקו אינם גלויים. התשובות הן לפחות ״יודע״ או ״לא יודע״; אין צורך שיכריזו גם על הצבע. האחרון, האמצעי והראשון נקראים להלן אחורי, אמצעי וקדמי כדי להימנע מבלבול מספור.

הצעה לפתרון: כן, הקדמי יכול תמיד להסיק את צבע הכובע שלו, אבל הצבע תלוי בתשובות. אין בשאלה נתון ששני האחרים ענו ״לא יודע״ ולכן אסור להניח זאת מראש.

מקרה 1 — האחורי אומר ״יודע״: הוא יכול לדעת רק אם הוא רואה שני כובעים שחורים. במקרה כזה שני השחורים כבר נוצלו, ושלו בהכרח לבן. אם הוא רואה שני לבנים או אחד מכל צבע, עבורו עדיין ייתכן לבן או שחור. לכן עצם ה״יודע״ מוכיח לקדמי שהוא שחור. האמצעי מסיק באותו ענף שגם הוא שחור, ולכן אומר ״יודע״ כשמגיע תורו.

מקרה 2 — האחורי אומר ״לא יודע״: עכשיו כולם יודעים שהקדמי והאמצעי אינם שניהם שחורים.
אם האמצעי רואה שחור אצל הקדמי, הוא יודע שהכובע שלו חייב להיות לבן, אחרת האחורי היה רואה שני שחורים ויודע. לכן הוא עונה ״יודע״.
אם האמצעי רואה לבן אצל הקדמי, הכובע שלו יכול להיות לבן או שחור, ושני המצבים מתאימים ל״לא יודע״ של האחורי. לכן הוא עונה ״לא יודע״.
מכאן שהקדמי, ששמע ״לא יודע״ מאחור, מפרש ״יודע״ מהאמצעי כהוכחה שהכובע שלו שחור, ו״לא יודע״ מהאמצעי כהוכחה שהכובע שלו לבן.

| תשובת האחורי | תשובת האמצעי | צבע הקדמי |
|---|---|---|
| יודע | יודע | שחור |
| לא יודע | יודע | שחור |
| לא יודע | לא יודע | לבן |

התמליל ״יודע, לא יודע״ אינו אפשרי תחת ההנחות: כשהאחורי יודע, גם האמצעי מבין מיד ששניהם מלפנים שחורים. בענף הזה הקדמי כבר יודע לפני תשובת האמצעי, אך עדיין יכול להמתין לתורו. צבע כובעו של האמצעי בענף ״לא יודע, יודע״ הוא לבן, בעוד צבע הקדמי שחור — חשוב לא להחליף ביניהם.

איך לחשוב: רשום מה כל אדם רואה ומתי היה יכול להיות בטוח. לאחר תשובה, מחק את כל חלוקות הכובעים שלא היו גורמות לתשובה הזו; אחר כך נתח את האדם הבא על בסיס האפשרויות שנותרו. אין צורך בהסתברויות או בהנחה שהחלוקה אחידה.

בדיקה: נבדקו כל שבע חלוקות הצבע החוקיות לפי סדר קדמי,אמצעי,אחורי. אסור BBB כי יש רק שני שחורים; כל יתר המילים באורך שלוש מותרות. לכל חלוקה חושבה ידיעת האחורי מתוך זוג הכובעים שהוא רואה, ואז ידיעת האמצעי מתוך כובע הקדמי ותשובת האחורי, ולבסוף האפשרויות של הקדמי מתוך שתי ההכרזות. בכל שבעת המצבים צבעו נקבע ביחידות. זו בדיקה של מודל הסקה אידאלי ולא של התנהגות אנושית בפועל.

תעדוף לראיון: חידת היגיון בעדיפות נמוכה בזמן מוגבל יחסית לתכנות, לוגיקה דיגיטלית ובדיקות מערכת. היא שימושית לתרגול הסקת מסקנות ושלילת אפשרויות. השיוך ל־Marvell מופיע בצילום אך אינו אימות או תחזית לראיון. התגית 2312313 נשמרת כתגית לא מסווגת, לא כחברה או קטגוריה מקצועית.'''
en='''Assume the participants open their eyes after placement, know the 3-white/2-black inventory and reasoning rules, hear earlier relevant answers, reason correctly and answer truthfully. Unused hats are hidden. Knowing means logical certainty, not a guess. Only yes/no knowledge announcements are needed, not actual color declarations.
Yes: the front person always knows after the announcements, but their color depends on the branch. The prompt does not say the first two answers are no.
If the rear knows, they must see two black hats: only then is their own hat forced white. Thus both front and middle know they are black. The middle also answers yes.
If the rear does not know, the front and middle cannot both be black. If the middle now sees black on the front, the middle's own hat must be white, so they answer yes. If they see white, either own color remains possible, so they answer no. Therefore after rear=no, middle=yes means front=black and middle=no means front=white. Complete transcript map: (yes,yes)->black; (no,yes)->black; (no,no)->white. (yes,no) is impossible under truthful perfect reasoning. In the first case the front knows before hearing the middle.
The method is to eliminate color assignments inconsistent with each public answer. No probability/uniformity assumption is needed. Checked all seven legal three-person color assignments (all W/B triples except BBB), with each agent's visibility and earlier public knowledge respected; every final front information set has a single color. Low preparation priority under time pressure relative to role-specific coding, digital logic and validation; company tags are unverified source reports. Tag 2312313 is uncategorized metadata, not a company.'''
q={
 'id':'PREP-033','key':'three-people-five-hats-public-reasoning','version':1,'created_on':'2026-09-29','category':'logical_reasoning','topic':'deductive_reasoning',
 'topics':['logical_reasoning','deductive_reasoning','knowledge_from_answers','case_analysis'],'source_topic_tags':['logic'],'added_topic_tags':['deductive_reasoning','knowledge_from_answers','case_analysis'],
 'source_tags':['nvidia','2312313','logic','elbit','marvell'],'unclassified_source_tags':['2312313'],'reported_companies':['NVIDIA','Elbit','Marvell'],'source_company_badge':'Elbit','company_attribution_status':'reported_by_supplied_source_not_independently_verified',
 'difficulty':None,'difficulty_scale':'1-10','estimated_minutes':None,'format':'logic_puzzle','status':'in_review','solution_status':'proposed','solution_display_label':'הצעה לפתרון','origin':'user_supplied_screenshot','reviewed_by':None,
 'sources':[{'type':'user_supplied_image','path':'sources/prep-033.png','received_on':'2026-09-29'}],'original_prompt':prompt,
 'translations':{'he':{'title':'שלושה אנשים וחמישה כובעים — הסקה מתוך תשובות','prompt':prompt,'hint':hints[0],'hints':hints,'reference_solution':he},'en':{'title':'Three people and five hats — reasoning from public answers','prompt':ep,'hint':eh[0],'hints':eh,'reference_solution':en}},
 'prepared_hints':[{'id':f'PREP-033-H0{i}','level':i,'language':'he','content':h} for i,h in enumerate(hints,1)],
 'assumptions':['Three white and two black hats; three worn, two hidden.','Rear sees front and middle; middle sees front; front sees none.','Participants can see after hats are placed.','Truthful knowledge answers, correct reasoning, known inventory and audible prior answers.','No assumption that initial answers are both no.'],
 'answer_branches':[{'rear_knows':True,'middle_knows':True,'front_color':'black'},{'rear_knows':False,'middle_knows':True,'front_color':'black'},{'rear_knows':False,'middle_knows':False,'front_color':'white'}],
 'optimality':{'criterion':'Guaranteed logical identifiability','result':'Front hat determined in all legal cases after the announced sequence.','scope':'Not an optimization of hat counts or communication; conclusion assumes ideal truthful reasoning.'},
 'verification':{'status':'passed','checked_on':'2026-09-29','script_path':'checks/check_prep_033.py','method':'All 7 legal color assignments; visibility-restricted knowledge sets and public-answer updates; 3 answer transcripts.'},
 'media_assets':[{'type':'source_image','path':'sources/prep-033.png','description':'Full original hat puzzle, company tags and uncategorized numeric tag.'}],
 'common_mistakes':['Assuming both first answers are no without being told','Concluding front is always white','Using guessed probabilities rather than logical certainty','Ignoring what the middle learns from the rear','Confusing the middle own color with front color','Letting agents see unused hats'],
 'interview_relevance':{'priority':'low','label_he':'חידת היגיון — עדיפות נמוכה בזמן מוגבל','basis':'Useful deduction practice, less directly tied to system-chip validation than code, circuits and test design.','assessment_scope':'Preparation judgment, not a company-interview prediction.'},
 'related_question_ids':['PREP-002','PREP-028'],'markdown_path':'questions/prep-033-three-people-five-hats.md'
}
p=root/'questions.json';raw=p.read_text(encoding='utf-8');before=json.loads(raw)
assert before['question_count']==32 and all(x['id']!=q['id'] for x in before['questions'])
pos=raw.rfind('\n  ]');assert pos>0
entry='    '+json.dumps(q,ensure_ascii=False,indent=2).replace('\n','\n    ')
updated=(raw[:pos]+',\n'+entry+raw[pos:]).replace('"question_count": 32','"question_count": 33',1)
after=json.loads(updated);assert after['questions'][:-1]==before['questions'] and len(after['questions'])==33
shutil.copy2('C:/Users/harel/AppData/Local/Temp/codex-clipboard-47b76197-0a2e-42bd-8de5-274285543a0e.png',root/'sources/prep-033.png')
p.write_text(updated,encoding='utf-8')
md='# PREP-033 — שלושה אנשים וחמישה כובעים\n\n## נוסח המקור\n\n'+prompt+'\n\n![צילום המקור](../sources/prep-033.png)\n\nתגית מקור: logic. חברות: NVIDIA, Elbit, Marvell. תווית ראשית Elbit. שיוך לא מאומת. התגית 2312313 אינה מסווגת.\n\n## שלושה רמזים\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(hints,1))+'\n\n## הצעה לפתרון\n\n'+he+'\n\n[בדיקת כל חלוקות הכובעים](../checks/check_prep_033.py)\n\n## English\n\n'+ep+'\n\n'+'\n\n'.join(f'{i}. {h}' for i,h in enumerate(eh,1))+'\n\n'+en+'\n'
(root/q['markdown_path']).write_text(md,encoding='utf-8')
r=root/'README.md';r.write_text(r.read_text(encoding='utf-8')+'\n- [PREP-033 — שלושה אנשים וחמישה כובעים](questions/prep-033-three-people-five-hats.md) — מקור, חברות, רמזים ופתרון לכל ענפי התשובות; נבדקו כל שבע חלוקות הצבע החוקיות.\n',encoding='utf-8')
print('PREP-033 saved; source, bilingual hints/solution, all answer branches and verification; total 33.')
