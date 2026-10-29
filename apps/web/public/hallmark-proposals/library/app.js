const copy = {
  he: {
    skip:'דילוג לתוכן', navigation:'ניווט הצעת עיצוב', gallery:'כל ההצעות', live:'לאתר הקיים', title:'ספרייה פתוחה', intro:'בוחרים שאלה, מפרקים את הבעיה, כותבים את דרך החשיבה.',
    searchLabel:'חיפוש בשש שאלות לדוגמה', searchPlaceholder:'מה רוצים להבין היום?', filters:'סינון הספרייה', directory:'נושאים וסינון', topicLabel:'נושא', all:'כל השאלות', hardware:'חומרה', software:'תוכנה', reasoning:'חשיבה',
    savedFilter:'סימניות בלשונית', directoryNote:'לא צריך למהר לפתרון. מתחילים בהסבר משלכם.', questions:'שאלות לדוגמה', questionsTitle:'שאלות לתרגול', emptyTitle:'אין שאלות בתצוגה הזו', emptyText:'אפשר לנסות חיפוש אחר או להסיר את הסינון.', clear:'ניקוי הסינון',
    back:'חזרה לספרייה', readingNote:'קראו, נסו להסביר בקול, ואז כתבו. הרמזים כאן כשצריך.', question:'השאלה', explanation:'דרך החשיבה שלכם', answerLabel:'מה ידוע, מה צריך לבדוק, ואיך מגיעים לפתרון?', answerPlaceholder:'אפשר להתחיל מההנחה הראשונה…',
    saveDraft:'שמירת טיוטה בלשונית', draftNotice:'הטקסט נשאר בלשונית הזו בלבד. לא נשלח דבר.', draftSaved:'הטיוטה נשמרה בזיכרון הלשונית. רענון ימחק אותה.', draftEmpty:'כתבו הסבר לפני שמירת הטיוטה.', help:'כשצריך כיוון נוסף', hintOne:'רמז ראשון', hintTwo:'רמז נוסף', solution:'פתרון לעיון', noGrade:'זהו תרגול עצמי. ההצעה אינה בודקת או מדרגת תשובות.', next:'לשאלה הבאה',
    sample:'הצעת עיצוב בלבד. שש שאלות לדוגמה, ללא חיבור לחשבון.', local:'סימניות וטיוטות נמחקות ברענון.', save:'הוספת סימנייה', unsave:'הסרת סימנייה', saved:'הסרת הסימנייה מהלשונית', saveReading:'שמירת סימנייה בלשונית', count:n=>`${n} שאלות לדוגמה`, position:n=>`שאלה ${n} מתוך 6 בדוגמה`, documentTitle:'ספרייה פתוחה | JobRun'
  },
  en: {
    skip:'Skip to content', navigation:'Design proposal navigation', gallery:'All proposals', live:'Current website', title:'The open library', intro:'Choose a question. Unpack the problem. Write your reasoning.',
    searchLabel:'Search six sample questions', searchPlaceholder:'What would you like to understand?', filters:'Filter the library', directory:'Topics and filters', topicLabel:'Topic', all:'All questions', hardware:'Hardware', software:'Software', reasoning:'Reasoning',
    savedFilter:'Bookmarks in this tab', directoryNote:'Take time before the solution. Start with your own explanation.', questions:'Sample questions', questionsTitle:'Questions to work through', emptyTitle:'No questions in this view', emptyText:'Try another search or remove the filters.', clear:'Clear filters',
    back:'Back to the library', readingNote:'Read, try explaining aloud, then write. Hints are here when you need them.', question:'The question', explanation:'Your reasoning', answerLabel:'What do you know, what should you check, and how do you reach a solution?', answerPlaceholder:'Start with your first assumption…',
    saveDraft:'Save draft in this tab', draftNotice:'Your writing stays in this tab only. Nothing is sent.', draftSaved:'Draft held in this tab’s memory. Refreshing will clear it.', draftEmpty:'Write an explanation before saving a draft.', help:'A little more direction', hintOne:'First hint', hintTwo:'Another hint', solution:'Reference solution', noGrade:'This is self practice. The proposal does not check or grade answers.', next:'Next question',
    sample:'Design proposal only. Six sample questions, with no account connection.', local:'Bookmarks and drafts clear on refresh.', save:'Add bookmark', unsave:'Remove bookmark', saved:'Remove bookmark from this tab', saveReading:'Bookmark in this tab', count:n=>`${n} sample questions`, position:n=>`Question ${n} of 6 in this sample`, documentTitle:'The open library | JobRun'
  }
};
const questions = [
  { id:'bounds', topic:'software', code:'int values[4] = {2, 4, 6, 8};\nint sum = 0;\nfor (int i = 0; i <= 4; i++) {\n    sum += values[i];\n}', solutionCode:'for (int i = 0; i < 4; i++) {\n    sum += values[i];\n}',
    he:{title:'היכן הלולאה חורגת מגבולות המערך?', subject:'גבולות מערך בשפת C', prompt:'הקוד הבא אמור לסכום ארבעה איברים. איזו גישה אינה תקינה, מה עלול לקרות, ואיך מתקנים את תנאי העצירה?', hints:['כתבו את האינדקס הראשון והאחרון שקיימים במערך.','עקבו אחרי הערך של i גם באיטרציה האחרונה שהלולאה מאפשרת.'], solution:'האינדקסים התקינים הם 0 עד 3. התנאי i <= 4 מאפשר גישה אל values[4], מחוץ למערך. ב־C זו התנהגות לא מוגדרת, ולכן אין פלט שאפשר להבטיח. מחליפים את התנאי ב־i < 4; הסכום אז הוא 20.'},
    en:{title:'Where does the loop leave the array?', subject:'Array bounds in C', prompt:'This code should add four elements. Which access is invalid, what could happen, and how would you fix the stopping condition?', hints:['Write down the first and last valid array indices.','Trace i through the final iteration allowed by the loop.'], solution:'Valid indices are 0 through 3. The condition i <= 4 permits values[4], outside the array. In C this is undefined behavior, so no particular output is guaranteed. Use i < 4; the sum is then 20.'}},
  { id:'and', topic:'hardware', code:'Y = A AND B\n\nA  B  Y\n0  0  ?\n0  1  ?\n1  0  ?\n1  1  ?', solutionCode:'A  B  Y\n0  0  0\n0  1  0\n1  0  0\n1  1  1',
    he:{title:'מתי שער AND מוציא 1?', subject:'לוגיקה צירופית', prompt:'לשער AND יש שתי כניסות A ו־B. השלימו את טבלת האמת והסבירו במשפט אחד מהו התנאי לקבלת 1 ביציאה.', hints:['המילה AND דורשת ששני התנאים יתקיימו יחד.','בדקו בנפרד את המקרה שבו בדיוק אחת מהכניסות היא 1.'], solution:'היציאה היא 1 רק כששתי הכניסות הן 1. בכל צירוף אחר לפחות אחת מהכניסות היא 0 ולכן היציאה 0.'},
    en:{title:'When does an AND gate output 1?', subject:'Combinational logic', prompt:'An AND gate has inputs A and B. Complete its truth table and explain in one sentence when the output is 1.', hints:['AND requires both conditions to hold at the same time.','Check what happens when exactly one input is 1.'], solution:'The output is 1 only when both inputs are 1. In every other combination at least one input is 0, so the output is 0.'}},
  { id:'fsm', topic:'hardware', code:'Input:  1 0 1 0 1\nOutput: 0 0 ? 0 ?', solutionCode:'State  input  next  output\nS0     0      S0    0\nS0     1      S1    0\nS1     0      S2    0\nS1     1      S1    0\nS2     0      S0    0\nS2     1      S1    1',
    he:{title:'איך מזהים 101 גם כשיש חפיפה?', subject:'מכונת מצבים', prompt:'תכננו גלאי Mealy לרצף 101. מותרת חפיפה: בקלט 10101 צריך לזהות פעמיים. אילו מצבים צריך, ולאיזה מצב עוברים אחרי זיהוי?', hints:['מצב מייצג את התחילית הארוכה ביותר של 101 שכבר התאימה לסוף הקלט.','אחרי קבלת 101, הספרה האחרונה 1 יכולה להיות תחילת הזיהוי הבא.'], solution:'מספיקים S0 ללא התאמה, S1 אחרי 1 ו־S2 אחרי 10. מתחילים ב־S0. ב־S2 על קלט 1 מוציאים 1 וחוזרים ל־S1 כדי לשמר חפיפה. בכל שאר המעברים מוציאים 0. בקלט 10101 מתקבל זיהוי בביטים השלישי והחמישי.'},
    en:{title:'How do you detect overlapping 101?', subject:'Finite state machines', prompt:'Design a Mealy detector for 101. Overlap is allowed: the input 10101 must be detected twice. Which states are needed, and where do you go after detection?', hints:['Each state records the longest prefix of 101 matching the end of the input so far.','After 101, its final 1 can start the next match.'], solution:'Use S0 for no match, S1 after 1, and S2 after 10. Start in S0. In S2, input 1 produces output 1 and moves to S1, preserving overlap. All other transitions output 0. For 10101, detection occurs on the third and fifth bits.'}},
  { id:'pointer', topic:'software', code:'int *p = NULL;\nif (*p > 0 && p != NULL) {\n    use(*p);\n}', solutionCode:'if (p != NULL && *p > 0) {\n    use(*p);\n}',
    he:{title:'באיזה סדר כדאי לבדוק מצביע?', subject:'מצביעים והערכה מקוצרת', prompt:'האם בדיקת NULL שבקוד מגינה מפני גישה לא תקינה? הסבירו את סדר ההערכה של && והציעו תיקון, בהנחה ש־p הוא NULL או מצביע תקין לאיבר int חי.', hints:['האופרנד השמאלי של && נבדק ראשון.','האופרנד הימני כלל אינו נבדק אם השמאלי הוא שקר.'], solution:'לא. הקוד מנסה לקרוא את *p לפני בדיקת NULL, ולכן במקרה הנתון מתרחשת התנהגות לא מוגדרת. בודקים קודם p != NULL ורק אז *p > 0. ההערכה המקוצרת מונעת את הגישה כשהמצביע NULL; בדיקת NULL לבדה אינה מאמתת שמצביע אחר הוא תקין.'},
    en:{title:'Which pointer check should come first?', subject:'Pointers and short circuit evaluation', prompt:'Does the NULL check protect this code? Explain the evaluation order of && and fix it, assuming p is either NULL or a valid pointer to a live int.', hints:['The left operand of && is evaluated first.','The right operand is not evaluated if the left operand is false.'], solution:'No. The code reads *p before checking for NULL, so the given case has undefined behavior. Check p != NULL before *p > 0. Short circuit evaluation then prevents dereferencing NULL. A NULL check alone does not establish that any other pointer is valid.'}},
  { id:'weighing', topic:'reasoning',
    he:{title:'איזה כדור כבד יותר?', subject:'חלוקת מקרים', prompt:'יש שמונה כדורים זהים למראה. בדיוק אחד כבד מהאחרים, וכל השאר שוקלים אותו דבר. איך מוצאים אותו בשתי שקילות לכל היותר במאזני כפות?', hints:['השוו שתי קבוצות של שלושה כדורים.','כל תוצאת שקילה ראשונה משאירה לכל היותר שלושה חשודים.'], solution:'שוקלים שלושה מול שלושה. אם יש איזון, הכדור הכבד בין השניים שבצד: משווים ביניהם. אם צד אחד כבד, לוקחים שניים משלושת הכדורים בצד הזה ומשווים. אם יש איזון השלישי הוא הכבד; אחרת הכבד מבין השניים הוא התשובה.'},
    en:{title:'Which ball is heavier?', subject:'Reasoning by cases', prompt:'Eight balls look identical. Exactly one is heavier, and the other seven have equal weight. How can you find the heavier ball with at most two balance scale weighings?', hints:['Compare two groups of three balls.','Every first weighing outcome leaves at most three candidates.'], solution:'Weigh three against three. If they balance, compare the two unused balls. If one side is heavier, take two balls from that group of three and compare them. If they balance, the third is heavier; otherwise the heavier of the two is the answer.'}},
  { id:'labels', topic:'reasoning',
    he:{title:'איזו תיבה פותחים קודם?', subject:'הסקה מתוך אילוץ', prompt:'שלוש תיבות מכילות תפוחים בלבד, תפוזים בלבד, או תערובת. התוויות הן ״תפוחים״, ״תפוזים״ ו״מעורב״, וכולן שגויות. מותר להוציא פרי אחד מתיבה אחת בלי להביט פנימה. איך מזהים את כל התיבות?', hints:['התיבה שמסומנת ״מעורב״ אינה מעורבת.','אחרי הזיהוי הראשון, השתמשו בכך שגם שתי התוויות שנותרו שגויות.'], solution:'מוציאים פרי מהתיבה ״מעורב״. אם יצא תפוח, היא מכילה תפוחים בלבד. התיבה ״תפוזים״ אינה תפוזים וגם אינה תפוחים, ולכן היא מעורבת. התיבה ״תפוחים״ מכילה תפוזים. אם יצא תפוז, פועלים באופן סימטרי.'},
    en:{title:'Which box should you open first?', subject:'Reasoning from constraints', prompt:'Three boxes contain only apples, only oranges, or a mixture. Their labels read “apples”, “oranges”, and “mixed”, and every label is wrong. You may draw one fruit from one box without looking inside. How can you identify all three boxes?', hints:['The box labelled “mixed” cannot contain a mixture.','Once you identify that box, use the fact that the other two labels are also wrong.'], solution:'Draw from the box labelled “mixed”. If you get an apple, that box contains only apples. The box labelled “oranges” cannot hold oranges or the already identified apples, so it is mixed. The box labelled “apples” holds oranges. If you draw an orange, use the symmetric reasoning.'}}
];
const $ = selector => document.querySelector(selector);
const bookmarks = new Set(), drafts = new Map();
let state = { lang:'he', topic:'all', query:'', saved:false, question:null };
const t = key => copy[state.lang][key];
const escapeHTML = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
function proseHTML(value) {
  if (state.lang !== 'he') return escapeHTML(value);
  let html = '', position = 0;
  for (const match of value.matchAll(/[A-Za-z0-9*&][A-Za-z0-9 \t<>=!&*_[\].,;:/()+-]*/g)) {
    html += escapeHTML(value.slice(position, match.index));
    const technical = match[0].trimEnd();
    html += `<bdi dir="ltr">${escapeHTML(technical)}</bdi>${escapeHTML(match[0].slice(technical.length))}`;
    position = match.index + match[0].length;
  }
  return html + escapeHTML(value.slice(position));
}
function writeProse(selector, value) {
  $(selector).innerHTML = proseHTML(value);
}
const bookmarkIcon = '<svg viewBox="0 0 20 24" aria-hidden="true"><path d="M4 2h12v19l-6-4-6 4Z"/></svg>';
function readURL() {
  const params = new URLSearchParams(location.search);
  state.lang = params.get('lang') === 'en' ? 'en' : 'he';
  state.topic = ['hardware','software','reasoning'].includes(params.get('topic')) ? params.get('topic') : 'all';
  state.query = (params.get('q') || '').slice(0, 150); state.saved = params.get('saved') === '1';
  state.question = questions.some(item => item.id === params.get('question')) ? params.get('question') : null;
}
function urlFor(patch = {}) {
  const next = {...state, ...patch}, url = new URL(location.href);
  url.search = '';
  if (next.lang === 'en') url.searchParams.set('lang','en');
  if (next.topic !== 'all') url.searchParams.set('topic',next.topic);
  if (next.query) url.searchParams.set('q',next.query);
  if (next.saved) url.searchParams.set('saved','1');
  if (next.question) url.searchParams.set('question',next.question);
  return url;
}
function navigate(patch, focus = false, replace = false) {
  if (state.question) drafts.set(state.question, $('#answer').value);
  Object.assign(state, patch); history[replace ? 'replaceState' : 'pushState']({},'',urlFor());
  render();
  if (focus) { (state.question ? $('#reading-title') : $('#index-title')).focus(); window.scrollTo({top:0, behavior:'instant'}); }
}
function translate() {
  document.documentElement.lang = state.lang; document.documentElement.dir = state.lang === 'he' ? 'rtl' : 'ltr'; document.title = t('documentTitle');
  document.querySelectorAll('[data-i18n]').forEach(element => element.textContent = t(element.dataset.i18n));
  document.querySelectorAll('[data-placeholder]').forEach(element => element.placeholder = t(element.dataset.placeholder));
  document.querySelectorAll('[data-aria]').forEach(element => element.setAttribute('aria-label', t(element.dataset.aria)));
  $('.wordmark').setAttribute('aria-label', state.lang === 'he' ? 'JobRun, גלריית ההצעות' : 'JobRun, proposal gallery');
  $('#language').textContent = state.lang === 'he' ? 'English' : 'עברית'; $('#language').lang = state.lang === 'he' ? 'en' : 'he';
}
function visibleQuestions() {
  const query = state.query.toLocaleLowerCase().trim();
  return questions.filter(item => (state.topic === 'all' || item.topic === state.topic) && (!state.saved || bookmarks.has(item.id)) && (!query || `${item.he.title} ${item.he.subject} ${item.he.prompt} ${item.en.title} ${item.en.subject} ${item.en.prompt} ${item.code || ''}`.toLocaleLowerCase().includes(query)));
}
function renderList() {
  const visible = visibleQuestions();
  $('#query').value = state.query; $('#result-count').textContent = t('count')(visible.length); $('#saved-count').textContent = bookmarks.size;
  document.querySelectorAll('[data-topic]').forEach(button => button.setAttribute('aria-pressed', String(state.topic === button.dataset.topic)));
  $('#saved-only').setAttribute('aria-pressed', String(state.saved)); $('#empty').hidden = visible.length > 0;
  $('#question-list').innerHTML = visible.map(item => {
    const data = item[state.lang], bookmarked = bookmarks.has(item.id), index = questions.indexOf(item) + 1;
    return `<li class="question-row"><span class="question-number" aria-hidden="true">${String(index).padStart(2,'0')}</span><div><h3><a href="${escapeHTML(urlFor({question:item.id}).search)}" data-question="${item.id}">${proseHTML(data.title)}</a></h3><p class="question-meta"><span>${t(item.topic)}</span><span>${proseHTML(data.subject)}</span></p></div><button type="button" class="bookmark" data-bookmark="${item.id}" aria-pressed="${bookmarked}" aria-label="${escapeHTML((bookmarked ? t('unsave') : t('save')) + ': ' + data.title)}">${bookmarkIcon}</button></li>`;
  }).join('');
}
function renderReading() {
  const item = questions.find(question => question.id === state.question);
  if (!item) return;
  const data = item[state.lang];
  writeProse('#reading-title', data.title); $('#reading-topic').textContent = t(item.topic); writeProse('#reading-subject', data.subject);
  $('#reading-position').textContent = t('position')(questions.indexOf(item)+1); writeProse('#prompt', data.prompt);
  $('#code').hidden = !item.code; $('#code code').textContent = item.code || '';
  writeProse('#hint-one p', data.hints[0]); writeProse('#hint-two p', data.hints[1]); writeProse('#solution p', data.solution);
  $('#solution-code').hidden = !item.solutionCode; $('#solution-code code').textContent = item.solutionCode || '';
  $('#answer').value = drafts.get(item.id) || '';
  $('#reading-bookmark').textContent = bookmarks.has(item.id) ? t('saved') : t('saveReading');
  $('#reading-bookmark').setAttribute('aria-pressed',String(bookmarks.has(item.id)));
}
function render() {
  translate(); renderList();
  $('#index-view').hidden = !!state.question; $('#reading-view').hidden = !state.question;
  if (state.question) renderReading();
}
function toggleBookmark(id) {
  bookmarks.has(id) ? bookmarks.delete(id) : bookmarks.add(id);
  const active = document.activeElement;
  renderList();
  if (state.question) renderReading();
  else if (active?.dataset.bookmark) {
    const replacement = document.querySelector(`[data-bookmark="${id}"]`);
    if (replacement) replacement.focus(); else $('#saved-only').focus();
  }
}
$('#language').addEventListener('click', () => navigate({lang:state.lang === 'he' ? 'en' : 'he'}));
$('#query').addEventListener('input', event => { state.query = event.target.value.slice(0,150); history.replaceState({},'',urlFor()); renderList(); });
document.querySelectorAll('[data-topic]').forEach(button => button.addEventListener('click', () => navigate({topic:button.dataset.topic})));
$('#saved-only').addEventListener('click', () => navigate({saved:!state.saved}));
$('#clear-filters').addEventListener('click', () => { navigate({query:'',topic:'all',saved:false}); $('#query').focus(); });
$('#question-list').addEventListener('click', event => {
  const link = event.target.closest('[data-question]'), bookmark = event.target.closest('[data-bookmark]');
  if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey) { event.preventDefault(); document.querySelectorAll('.help-section details').forEach(detail => detail.open = false); navigate({question:link.dataset.question},true); }
  if (bookmark) toggleBookmark(bookmark.dataset.bookmark);
});
$('#back').addEventListener('click', () => navigate({question:null},true));
$('#reading-bookmark').addEventListener('click', () => toggleBookmark(state.question));
$('#answer').addEventListener('input', event => { drafts.set(state.question,event.target.value); $('#draft-status').textContent = t('draftNotice'); });
$('#save-draft').addEventListener('click', () => { const value = $('#answer').value; drafts.set(state.question,value); $('#draft-status').textContent = t(value.trim() ? 'draftSaved' : 'draftEmpty'); if (!value.trim()) $('#answer').focus(); });
$('#next-question').addEventListener('click', () => { const index = questions.findIndex(item => item.id === state.question); document.querySelectorAll('.help-section details').forEach(detail => detail.open = false); navigate({question:questions[(index+1)%questions.length].id},true); });
window.addEventListener('popstate', () => { if (state.question) drafts.set(state.question,$('#answer').value); readURL(); render(); (state.question ? $('#reading-title') : $('#index-title')).focus(); });
document.addEventListener('keydown', event => { if (event.key === '/' && !['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName) && !event.ctrlKey && !event.metaKey && !event.altKey) { event.preventDefault(); if (state.question) navigate({question:null}); $('#query').focus(); } });
const compact = matchMedia('(max-width: 60rem)');
function syncDisclosure() { $('#filter-disclosure').open = !compact.matches; }
compact.addEventListener('change',syncDisclosure); syncDisclosure(); readURL(); render();
