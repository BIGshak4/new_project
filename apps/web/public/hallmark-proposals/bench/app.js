const copy = {
  he: {
    skip: 'דילוג לתרגול', proposal: 'הצעת עיצוב, תרגול מקומי לדוגמה', gallery: 'כל ההצעות', name: 'סביבת עבודה', practice: 'תרגול', questions: 'שאלות', change: 'החלפת שאלה', simulation: 'בדיקת כניסות', reasoning: 'מה אפשר להסיק?', local: 'עבודה מקומית', state: 'מצב', tableNote: 'השורה המסומנת תואמת לכניסות שבחרתם.', answerLabel: 'ההסבר שלכם', answerNote: 'לחשיבה שלכם. אין בדיקה אוטומטית, הטקסט נשאר כאן עד רענון.', hintTitle: 'כיוון למחשבה', hint: 'רמז ראשון', hintEmpty: 'אפשר להתחיל משתי כניסות שוות, ואז לשנות רק אחת.', reference: 'השוואה לפתרון', footer: 'סביבת עבודה, הצעה עצמאית ל־JobRun', website: 'לאתר JobRun', questionBank: 'בוחרים בעיה, מתחילים לחשוב.', bankDescription: 'שלוש שאלות לדוגמה שאפשר לחקור בסביבת העבודה.', searchLabel: 'חיפוש בשאלות לדוגמה', simulationNote: 'התרשים והטבלה מתעדכנים יחד עם הכניסות.', selected: 'נבחר', open: 'פתיחת שאלה', nextHint: 'רמז נוסף', allHints: 'כל הרמזים מוצגים', searchPlaceholder: 'AND, XOR או מכונת מצבים', noResults: 'אין שאלה מתאימה. נסו AND, XOR או FSM.', results: 'שאלות לדוגמה', navLabel: 'ניווט ראשי'
  },
  en: {
    skip: 'Skip to practice', proposal: 'Design proposal, local practice example', gallery: 'All proposals', name: 'Workbench', practice: 'Practice', questions: 'Questions', change: 'Change question', simulation: 'Explore the inputs', reasoning: 'What can you infer?', local: 'Local workspace', state: 'State', tableNote: 'The highlighted row matches your selected inputs.', answerLabel: 'Your explanation', answerNote: 'For your own thinking. No automatic grading; text stays until refresh.', hintTitle: 'A way into the problem', hint: 'First hint', hintEmpty: 'Start with two equal inputs, then change just one.', reference: 'Compare with the solution', footer: 'Workbench, an independent JobRun proposal', website: 'Visit JobRun', questionBank: 'Choose a problem. Start thinking.', bankDescription: 'Three sample questions to explore in the workbench.', searchLabel: 'Search sample questions', simulationNote: 'The diagram and table update with the inputs.', selected: 'Selected', open: 'Open question', nextHint: 'Another hint', allHints: 'All hints shown', searchPlaceholder: 'AND, XOR or state machine', noResults: 'No matching question. Try AND, XOR or FSM.', results: 'sample questions', navLabel: 'Main navigation'
  }
};
const questions = [
  {
    id: 'and', kind: 'AND', equation: 'Y = A ∧ B', symbols: ['A', 'B', 'Y'], calc: (a, b) => a && b,
    he: { topic: 'לוגיקה ספרתית', title: 'מתי שער AND מחזיר 1?', prompt: 'שנו את הכניסות, בדקו את הפלט והסבירו את הקשר.', labels: ['כניסה A', 'כניסה B'], output: 'הפלט כעת', low: 'לפחות כניסה אחת כבויה', high: 'שתי הכניסות פעילות', placeholder: 'באילו תנאים מתקבל פלט 1?', caption: 'טבלת אמת, שער AND', diagram: 'שער AND עם שתי כניסות ופלט אחד', hints: ['מה מתקבל כאשר A הוא 0, בלי קשר ל־B?', 'חפשו את הצירוף היחיד שבו שתי הכניסות הן 1.'], solution: 'שער AND מחזיר 1 רק כאשר שתי הכניסות הן 1. בכל צירוף אחר הפלט הוא 0.' },
    en: { topic: 'Digital logic', title: 'When does an AND gate output 1?', prompt: 'Change the inputs, inspect the output and explain their relationship.', labels: ['Input A', 'Input B'], output: 'Current output', low: 'At least one input is low', high: 'Both inputs are high', placeholder: 'Under which conditions is the output 1?', caption: 'Truth table, AND gate', diagram: 'An AND gate with two inputs and one output', hints: ['What happens when A is 0, regardless of B?', 'Look for the only combination where both inputs are 1.'], solution: 'An AND gate outputs 1 only when both inputs are 1. Every other input combination produces 0.' }
  },
  {
    id: 'xor', kind: 'XOR', equation: 'Y = A ⊕ B', symbols: ['A', 'B', 'Y'], calc: (a, b) => a !== b,
    he: { topic: 'לוגיקה ספרתית', title: 'מה XOR מזהה בשתי כניסות?', prompt: 'השוו כניסות שוות ושונות, ונסחו כלל לפלט.', labels: ['כניסה A', 'כניסה B'], output: 'הפלט כעת', low: 'הכניסות שוות', high: 'הכניסות שונות', placeholder: 'מה ההבדל בין XOR ל־AND?', caption: 'טבלת אמת, שער XOR', diagram: 'שער XOR עם שתי כניסות ופלט אחד', hints: ['השוו בין הצירופים 00 ו־11. האם הפלט שונה?', 'הפלט הוא 1 כשבדיוק כניסה אחת היא 1.'], solution: 'שער XOR מחזיר 1 כאשר הכניסות שונות זו מזו: 01 או 10. כאשר הכניסות שוות, הפלט הוא 0.' },
    en: { topic: 'Digital logic', title: 'What does XOR detect in two inputs?', prompt: 'Compare equal and different inputs, then describe the output rule.', labels: ['Input A', 'Input B'], output: 'Current output', low: 'The inputs are equal', high: 'The inputs are different', placeholder: 'How does XOR differ from AND?', caption: 'Truth table, XOR gate', diagram: 'An XOR gate with two inputs and one output', hints: ['Compare the combinations 00 and 11. Is the output different?', 'The output is 1 when exactly one input is 1.'], solution: 'An XOR gate outputs 1 when the inputs differ: 01 or 10. Equal inputs produce an output of 0.' }
  },
  {
    id: 'fsm', kind: 'FSM', equation: 'Q′ = Q ⊕ T', symbols: ['Q', 'T', 'Q′'], calc: (a, b) => a !== b,
    he: { topic: 'מכונת מצבים', title: 'מתי המצב מתחלף?', prompt: 'בחרו מצב נוכחי ואות היפוך, וחשבו את המצב בצעד הבא.', labels: ['מצב נוכחי Q', 'אות היפוך T'], output: 'המצב הבא', low: 'המצב הבא הוא 0', high: 'המצב הבא הוא 1', placeholder: 'מה קורה למצב כאשר T הוא 0, וכאשר הוא 1?', caption: 'טבלת מעבר, מכונת היפוך', diagram: 'דיאגרמת מצבים: T שווה 1 מחליף מצב, T שווה 0 משמר אותו', hints: ['כאשר T הוא 0, המצב נשאר כפי שהיה.', 'כאשר T הוא 1, מצב 0 עובר ל־1 ומצב 1 עובר ל־0.'], solution: 'זהו כלל מעבר של מכונת היפוך בעלת שני מצבים. T=0 משמר את Q, ו־T=1 הופך אותו. הטבלה מציגה צעד מעבר אחד, ללא שעון מדומה.' },
    en: { topic: 'State machines', title: 'When does the state change?', prompt: 'Choose the current state and toggle signal; calculate the next state.', labels: ['Current state Q', 'Toggle input T'], output: 'Next state', low: 'The next state is 0', high: 'The next state is 1', placeholder: 'What happens when T is 0, and when it is 1?', caption: 'Transition table, toggle machine', diagram: 'State diagram: T equals 1 changes state, T equals 0 holds state', hints: ['When T is 0, the state stays as it was.', 'When T is 1, state 0 changes to 1 and state 1 changes to 0.'], solution: 'This is the transition rule of a two-state toggle machine. T=0 holds Q, and T=1 inverts it. The table shows one transition step, without a simulated clock.' }
  }
];
let language = 'he';
let current = questions[0];
let view = 'practice';
const states = Object.fromEntries(questions.map(q => [q.id, { a: false, b: false, hints: 0, answer: '', reference: false }]));
const byId = id => document.getElementById(id);
const gateMarkup = byId('circuit-stage').innerHTML;
const stateMarkup = `<svg class="circuit" viewBox="0 0 480 204" role="img" aria-labelledby="fsm-title" dir="ltr"><title id="fsm-title"></title><g class="wire"><path d="M163 74Q240 3 317 74M317 136Q240 203 163 136M99 78C22 8 22 181 99 126M381 78C458 8 458 181 381 126"/><path d="m304 69 13 5-3-14m-138 81-13-5 3 14"/></g><circle class="gate-body" cx="132" cy="105" r="42"/><circle class="gate-body" cx="348" cy="105" r="42"/><g class="diagram-labels" text-anchor="middle"><text x="132" y="112">Q = 0</text><text x="348" y="112">Q = 1</text><text x="240" y="32">T = 1</text><text x="240" y="193">T = 1</text><text x="34" y="109">T = 0</text><text x="446" y="109">T = 0</text></g></svg>`;

function renderSimulation() {
  const s = states[current.id], q = current[language], result = Number(current.calc(s.a, s.b));
  byId('input-a').checked = s.a;
  byId('input-b').checked = s.b;
  byId('bit-a').textContent = Number(s.a);
  byId('bit-b').textContent = Number(s.b);
  byId('output').textContent = `${current.symbols[2]} = ${result}`;
  byId('output-detail').textContent = result ? q.high : q.low;
  if (current.id !== 'fsm') {
    for (const [key, value] of [['a', s.a], ['b', s.b], ['y', result]]) {
      byId(`wire-${key}`).classList.toggle('is-high', Boolean(value));
      byId(`wire-${key}-text`).textContent = `${key.toUpperCase()} = ${Number(value)}`;
    }
  }
  const rows = [[0, 0], [0, 1], [1, 0], [1, 1]];
  byId('truth-body').replaceChildren(...rows.map(([a, b]) => {
    const row = document.createElement('tr');
    const selected = a === Number(s.a) && b === Number(s.b);
    row.classList.toggle('is-current', selected);
    [a, b, Number(current.calc(Boolean(a), Boolean(b))), selected ? copy[language].selected : '—'].forEach((value, i) => {
      const cell = document.createElement('td');
      cell.textContent = value;
      if (i === 3) cell.className = 'row-state';
      row.append(cell);
    });
    return row;
  }));
}

function renderHints() {
  const s = states[current.id], t = copy[language];
  byId('hint-content').textContent = s.hints ? current[language].hints.slice(0, s.hints).join(' ') : t.hintEmpty;
  byId('hint').textContent = s.hints === 2 ? t.allHints : s.hints === 1 ? t.nextHint : t.hint;
  byId('hint').disabled = s.hints === 2;
}

function renderQuestion() {
  const q = current[language], s = states[current.id];
  for (const [id, value] of Object.entries({ topic: q.topic, 'question-title': q.title, prompt: q.prompt, equation: current.equation, 'input-a-label': q.labels[0], 'input-b-label': q.labels[1], 'output-label': q.output, 'table-caption': q.caption, 'col-a': current.symbols[0], 'col-b': current.symbols[1], 'col-y': current.symbols[2], solution: q.solution, 'solution-equation': current.equation })) byId(id).textContent = value;
  byId('explanation').placeholder = q.placeholder;
  byId('explanation').value = s.answer;
  byId('reference').open = s.reference;
  byId('circuit-stage').innerHTML = current.id === 'fsm' ? stateMarkup : gateMarkup;
  if (current.id === 'fsm') byId('fsm-title').textContent = q.diagram;
  else {
    byId('circuit-title').textContent = q.diagram;
    byId('gate-name').textContent = current.kind;
    if (current.id === 'xor') {
      byId('gate-body').setAttribute('d', 'M190 43Q224 106 190 169Q279 176 321 106Q279 36 190 43Z M178 43Q211 106 178 169');
      byId('wire-y').querySelector('path').setAttribute('d', 'M321 106H418');
    }
  }
  renderSimulation();
  renderHints();
}

function renderList() {
  const query = byId('question-search').value.trim().toLocaleLowerCase();
  const matches = questions.filter(q => `${q.id} ${q.kind} ${q.he.topic} ${q.he.title} ${q.en.topic} ${q.en.title}`.toLocaleLowerCase().includes(query));
  byId('question-list').replaceChildren(...matches.map(q => {
    const row = document.createElement('article');
    row.className = 'question-row';
    const topic = document.createElement('p'), text = document.createElement('div'), title = document.createElement('h2'), description = document.createElement('p'), open = document.createElement('button');
    topic.textContent = q[language].topic;
    title.textContent = q[language].title;
    description.textContent = q.equation;
    description.dir = 'ltr';
    text.append(title, description);
    open.type = 'button';
    open.className = 'open-question';
    open.textContent = copy[language].open;
    open.setAttribute('aria-label', `${copy[language].open}: ${q[language].title}`);
    open.addEventListener('click', () => { current = q; renderQuestion(); setView('practice'); byId('question-title').setAttribute('tabindex', '-1'); byId('question-title').focus(); });
    row.append(topic, text, open);
    return row;
  }));
  byId('search-status').textContent = matches.length ? `${matches.length} ${copy[language].results}` : copy[language].noResults;
}

function setView(next) {
  view = next;
  byId('practice-view').hidden = next !== 'practice';
  byId('questions-view').hidden = next !== 'questions';
  byId('practice-nav').toggleAttribute('aria-current', next === 'practice');
  byId('questions-nav').toggleAttribute('aria-current', next === 'questions');
  byId(next === 'practice' ? 'practice-nav' : 'questions-nav').setAttribute('aria-current', 'page');
  if (next === 'questions') renderList();
}

function renderLanguage() {
  document.documentElement.lang = language;
  document.documentElement.dir = language === 'he' ? 'rtl' : 'ltr';
  document.title = language === 'he' ? 'JobRun, סביבת עבודה' : 'JobRun, Workbench';
  document.querySelectorAll('[data-copy]').forEach(el => { el.textContent = copy[language][el.dataset.copy]; });
  byId('language').textContent = language === 'he' ? 'English' : 'עברית';
  byId('language').lang = language === 'he' ? 'en' : 'he';
  byId('nav').setAttribute('aria-label', copy[language].navLabel);
  document.querySelector('.brand').setAttribute('aria-label', `JobRun, ${copy[language].gallery}`);
  byId('question-search').placeholder = copy[language].searchPlaceholder;
  renderQuestion();
  renderList();
}

byId('input-a').addEventListener('change', e => { states[current.id].a = e.target.checked; renderSimulation(); });
byId('input-b').addEventListener('change', e => { states[current.id].b = e.target.checked; renderSimulation(); });
byId('explanation').addEventListener('input', e => { states[current.id].answer = e.target.value; });
byId('hint').addEventListener('click', () => { states[current.id].hints = Math.min(2, states[current.id].hints + 1); renderHints(); });
byId('reference').addEventListener('toggle', () => { states[current.id].reference = byId('reference').open; });
byId('language').addEventListener('click', () => { language = language === 'he' ? 'en' : 'he'; renderLanguage(); });
byId('practice-nav').addEventListener('click', () => setView('practice'));
byId('questions-nav').addEventListener('click', () => setView('questions'));
byId('change-question').addEventListener('click', () => { setView('questions'); byId('question-search').focus(); });
byId('question-search').addEventListener('input', renderList);
renderLanguage();
