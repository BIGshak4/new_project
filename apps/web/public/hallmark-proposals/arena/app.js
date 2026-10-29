(() => {
  'use strict';
  const copy = {
    he: {
      skip: 'דילוג לתרגול', scope: 'סקיצת עיצוב, תרגול מקומי בלבד', gallery: 'כל הכיוונים', live: 'לאתר הקיים',
      practice: 'תרגול קצר', questions: 'סקירת שאלות', arena: 'זירת תרגול', invitation: 'חמש שאלות קצרות. מתחילים כאן.',
      simulation: 'הדמיה אישית של העיצוב, ללא יריב אמיתי.', local: 'התשובות קיימות רק בחלון הזה ונמחקות ברענון.',
      future: 'דו־קרב עם חברים הוא רעיון להמשך. כאן מתרגלים לבד.', nav: 'ניווט בזירה', label: 'תרגול מקומי',
      rounds: 'סבבי התרגול', question: (n) => `שאלה ${n} מתוך 5`, choice: 'בחירת תשובה אחת', check: 'בדיקת תשובה',
      choose: 'בחרו תשובה אחת כדי לבדוק אותה.', ready: 'אפשר לשנות בחירה לפני הבדיקה.', correct: 'נכון.', wrong: 'הפעם זו לא התשובה.',
      correctAnswer: 'התשובה הנכונה', yours: 'התשובה שלך', next: 'לשאלה הבאה', results: 'לתוצאות התרגול', review: 'סקירת התשובות',
      indexTitle: 'כל השאלות בזירה', indexIntro: 'אפשר לפתוח כל שאלה. תשובה שנבדקה זמינה לקריאה חוזרת.',
      unattempted: 'טרם נענתה', answeredCorrect: 'נענתה נכון', answeredWrong: 'לתשומת לב נוספת', back: 'חזרה לתרגול',
      done: 'הסבב הושלם.', score: 'תשובות נכונות מתוך חמש', recap: 'זהו סיכום התרגול המקומי שלך. אפשר לחזור לכל הסבר ולנסות שוב מההתחלה.',
      restart: 'התחלה מחדש, איפוס תשובות', letters: ['א', 'ב', 'ג', 'ד'], title: 'זירת תרגול | JobRun', brand: 'JobRun, כל כיווני העיצוב'
    },
    en: {
      skip: 'Skip to practice', scope: 'Design sample, local practice only', gallery: 'All directions', live: 'Existing website',
      practice: 'Quick practice', questions: 'Question index', arena: 'Practice arena', invitation: 'Five short questions. Start here.',
      simulation: 'A personal design simulation, with no real opponent.', local: 'Answers exist only in this window and clear on refresh.',
      future: 'A duel with friends is a future concept. This practice is solo.', nav: 'Arena navigation', label: 'Local practice',
      rounds: 'Practice rounds', question: (n) => `Question ${n} of 5`, choice: 'Choose one answer', check: 'Check answer',
      choose: 'Choose one answer to check it.', ready: 'You can change your choice before checking.', correct: 'Correct.', wrong: 'That is not the answer this time.',
      correctAnswer: 'Correct answer', yours: 'Your answer', next: 'Next question', results: 'Practice results', review: 'Review answers',
      indexTitle: 'Every question in the arena', indexIntro: 'Open any question. Checked answers remain available to review.',
      unattempted: 'Not answered', answeredCorrect: 'Answered correctly', answeredWrong: 'Worth another look', back: 'Back to practice',
      done: 'Round complete.', score: 'correct answers out of five', recap: 'This is your local practice summary. Revisit any explanation or start again from the beginning.',
      restart: 'Start again, reset answers', letters: ['A', 'B', 'C', 'D'], title: 'Practice arena | JobRun', brand: 'JobRun, all design directions'
    }
  };
  const questions = [
    {
      topic: { he: 'שערים לוגיים', en: 'Logic gates' }, short: 'AND', correct: 3, code: 'Y = A AND B',
      he: {
        title: 'מתי הפלט הוא 1?',
        description: 'בחרו את צירוף הקלטים שמפעיל שער AND בעל שני קלטים.',
        options: ['A = 0, B = 0', 'A = 0, B = 1', 'A = 1, B = 0', 'A = 1, B = 1'],
        explanation: 'שער AND מחזיר 1 רק כששני הקלטים הם 1. בכל צירוף אחר הפלט הוא 0.'
      },
      en: {
        title: 'When is the output 1?',
        description: 'Choose the input combination that activates a two-input AND gate.',
        options: ['A = 0, B = 0', 'A = 0, B = 1', 'A = 1, B = 0', 'A = 1, B = 1'],
        explanation: 'An AND gate outputs 1 only when both inputs are 1. Every other input combination produces 0.'
      }, technical: true
    },
    {
      topic: { he: 'שערים לוגיים', en: 'Logic gates' }, short: 'XOR', correct: 0, code: 'A = 1, B = 1\nY = A XOR B',
      he: {
        title: 'מה מחזיר XOR?',
        description: 'שני הקלטים הם 1. בחרו את ערך הפלט.',
        options: ['0', '1', '2', 'הפלט תלוי בשעון'],
        explanation: 'XOR מחזיר 1 רק כשהקלטים שונים. כאן הם שווים, ולכן הפלט הוא 0. השער צירופי ואינו תלוי בשעון.'
      },
      en: {
        title: 'What does XOR output?',
        description: 'Both inputs are 1. Choose the output value.',
        options: ['0', '1', '2', 'The output depends on a clock'],
        explanation: 'XOR outputs 1 only when its inputs differ. Here they are equal, so the output is 0. This combinational gate does not depend on a clock.'
      }, technical: false
    },
    {
      topic: { he: 'מערכים בשפת C', en: 'Arrays in C' }, short: 'C', correct: 1, code: 'int values[] = {4, 7, 9};\nvalues[1]',
      he: {
        title: 'מה נמצא באינדקס 1?',
        description: 'המערך מכיל שלושה מספרים. מה ערך הביטוי בשורה השנייה?',
        options: ['4', '7', '9', '1'],
        explanation: 'אינדקסים של מערך ב־C מתחילים ב־0. לכן values[0] הוא 4, ו־values[1] הוא 7.'
      },
      en: {
        title: 'What is at index 1?',
        description: 'The array contains three numbers. What is the value of the second-line expression?',
        options: ['4', '7', '9', '1'],
        explanation: 'Array indices in C start at 0. So values[0] is 4, and values[1] is 7.'
      }, technical: true
    },
    {
      topic: { he: 'מכונת מצבים', en: 'Finite state machines' }, short: 'FSM', correct: 2, code: 'Idle: start = 0 -> Idle\nIdle: start = 1 -> Busy\nBusy: done = 1 -> Done',
      he: {
        title: 'מהו המצב הבא?',
        description: 'המצב הנוכחי הוא Idle והקלט start הוא 1. השתמשו בכללי המעבר.',
        options: ['Idle', 'Done', 'Busy', 'לא ניתן לדעת'],
        explanation: 'הכלל עבור Idle עם start = 1 מעביר אל Busy. המעבר ל־Done חל רק מתוך Busy, כש־done = 1.'
      },
      en: {
        title: 'What is the next state?',
        description: 'The current state is Idle and start is 1. Use the transition rules.',
        options: ['Idle', 'Done', 'Busy', 'Cannot be determined'],
        explanation: 'The rule for Idle with start = 1 leads to Busy. A transition to Done only applies from Busy when done = 1.'
      }, technical: false
    },
    {
      topic: { he: 'אלגברה בוליאנית', en: 'Boolean algebra' }, short: 'Logic', correct: 1, code: 'NOT (A OR B)',
      he: {
        title: 'איזה ביטוי שקול?',
        description: 'בחרו ביטוי שמחזיר אותה תוצאה לכל צירוף קלטים.',
        options: ['(NOT A) OR (NOT B)', '(NOT A) AND (NOT B)', 'A AND B', 'A XOR B'],
        explanation: 'לפי חוק דה מורגן, שלילת OR שקולה ל־AND של הקלטים השלולים. לכן התשובה היא (NOT A) AND (NOT B).'
      },
      en: {
        title: 'Which expression is equivalent?',
        description: 'Choose an expression that returns the same result for every input combination.',
        options: ['(NOT A) OR (NOT B)', '(NOT A) AND (NOT B)', 'A AND B', 'A XOR B'],
        explanation: 'De Morgan’s law states that negating an OR is equivalent to ANDing the negated inputs. The answer is (NOT A) AND (NOT B).'
      }, technical: true
    }
  ];
  const state = {
    language: 'he', view: 'practice', current: 0,
    selected: Array(5).fill(null),
    answers: Array(5).fill(null)
  };
  const root = document.getElementById('arena');
  const main = document.getElementById('main');
  const t = () => copy[state.language];
  const escape = (value) => String(value).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const complete = () => state.answers.every((answer) => answer !== null);
  const answered = (index) => state.answers[index] !== null;
  const correct = (index) => state.answers[index] === questions[index].correct;
  const technicalText = (value, technical) => technical ? `<bdi dir="ltr">${escape(value)}</bdi>` : escape(value);
  const prose = (value) => escape(value).replace(/\(NOT A\) AND \(NOT B\)|values\[[01]\]|start = 1|done = 1|\b(?:AND|OR|XOR|NOT|Idle|Busy|Done|start|C)\b/g, (code) => `<bdi dir="ltr">${code}</bdi>`);
  function roundRail() {
    return `<ol class="rounds" aria-label="${t().rounds}">${questions.map((q, i) => `<li class="${i === state.current ? 'is-active' : ''} ${answered(i) ? 'is-done' : ''}" ${i === state.current ? 'aria-current="step"' : ''}><span>${i + 1}</span><bdi dir="ltr">${q.short}</bdi></li>`).join('')}</ol>`;
  }
  function practice() {
    const q = questions[state.current];
    const content = q[state.language];
    const graded = answered(state.current);
    const selection = state.selected[state.current];
    const options = content.options.map((option, i) => {
      const choiceClass = graded ? `${i === q.correct ? 'is-correct' : ''} ${i === selection && i !== q.correct ? 'is-wrong' : ''} is-answered` : i === selection ? 'is-selected' : '';
      const label = graded && i === q.correct ? t().correctAnswer : graded && i === selection ? t().yours : '';
      const value = `<span class="option-letter">${t().letters[i]}</span><span class="option-text">${technicalText(option, q.technical || /^[A-Za-z0-9]+$/.test(option))}</span>${label ? `<span class="answer-state">${label}</span>` : ''}`;
      return graded ? `<div class="option ${choiceClass}">${value}</div>` : `<button type="button" class="option ${choiceClass}" data-answer="${i}" aria-pressed="${i === selection}">${value}</button>`;
    }).join('');
    return `${roundRail()}<div class="question-heading"><p>${t().question(state.current + 1)}</p><p>${q.topic[state.language]}</p></div>
      <h2 class="problem-title" id="question-title" tabindex="-1">${prose(content.title)}</h2><p class="problem-description">${prose(content.description)}</p>
      <pre class="problem-material"><code><bdi dir="ltr">${escape(q.code)}</bdi></code></pre><div class="answers" role="group" aria-label="${t().choice}">${options}</div>
      ${graded ? `<div class="feedback ${correct(state.current) ? 'is-correct' : 'is-wrong'}" role="status"><h3 id="feedback-title" tabindex="-1">${correct(state.current) ? t().correct : t().wrong}</h3><p>${prose(content.explanation)}</p></div>
        <div class="action-row"><button type="button" class="primary" data-action="next">${complete() ? t().results : t().next}</button></div>` : `<div class="action-row"><button type="button" class="primary" data-action="check" ${selection === null ? 'disabled' : ''}>${t().check}</button><p>${selection === null ? t().choose : t().ready}</p></div>`}`;
  }
  function questionIndex() {
    return `<h2 class="view-heading" tabindex="-1" id="view-title">${t().indexTitle}</h2><p class="index-intro">${t().indexIntro}</p>
      <ol class="question-index">${questions.map((q, i) => `<li><button type="button" class="index-button" data-question="${i}"><span class="index-number">${i + 1}</span><span class="index-title">${q[state.language].title}<small>${q.topic[state.language]}</small></span><span class="index-state ${answered(i) ? correct(i) ? 'correct' : 'wrong' : ''}">${answered(i) ? correct(i) ? t().answeredCorrect : t().answeredWrong : t().unattempted}</span></button></li>`).join('')}</ol>
      <div class="action-row"><button type="button" class="quiet" data-view="practice">${t().back}</button>${complete() ? `<button type="button" class="quiet" data-view="results">${t().results}</button>` : ''}</div>`;
  }
  function results() {
    const total = questions.filter((q, i) => correct(i)).length;
    return `<h2 class="view-heading" id="view-title" tabindex="-1">${t().done}</h2><p class="result-count"><bdi dir="ltr">${total} / 5</bdi></p><p>${t().score}</p><p class="result-copy">${t().recap}</p>
      <div class="result-actions"><button type="button" class="primary" data-view="questions">${t().review}</button><button type="button" class="quiet" data-action="restart">${t().restart}</button></div>`;
  }
  function render(focus) {
    root.innerHTML = state.view === 'questions' ? questionIndex() : state.view === 'results' ? results() : practice();
    document.querySelectorAll('[data-copy]').forEach((node) => { node.textContent = t()[node.dataset.copy]; });
    document.documentElement.lang = state.language;
    document.documentElement.dir = state.language === 'he' ? 'rtl' : 'ltr';
    document.title = t().title;
    document.getElementById('navigation').setAttribute('aria-label', t().nav);
    root.setAttribute('aria-label', t().label);
    document.querySelector('.wordmark').setAttribute('aria-label', t().brand);
    document.querySelectorAll('.nav-button').forEach((button) => {
      const current = button.dataset.view === state.view;
      button.classList.toggle('is-current', current);
      if (current) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
    });
    const language = document.getElementById('language');
    language.textContent = state.language === 'he' ? 'English' : 'עברית';
    language.setAttribute('aria-label', state.language === 'he' ? 'Switch to English' : 'מעבר לעברית');
    history.replaceState(null, '', `#${state.view}`);
    if (focus) (document.getElementById(focus) || main).focus();
  }
  document.addEventListener('click', (event) => {
    const button = event.target.closest('button');
    if (!button || button.disabled) return;
    if (button.id === 'language') {
      state.language = state.language === 'he' ? 'en' : 'he'; render(); return;
    }
    if (button.dataset.view) {
      state.view = button.dataset.view === 'results' && !complete() ? 'practice' : button.dataset.view;
      render(state.view === 'practice' ? 'question-title' : 'view-title'); return;
    }
    if (button.dataset.question !== undefined) {
      state.current = Number(button.dataset.question); state.view = 'practice'; render('question-title'); return;
    }
    if (button.dataset.answer !== undefined && !answered(state.current)) {
      state.selected[state.current] = Number(button.dataset.answer);
      root.querySelectorAll('[data-answer]').forEach((answer) => {
        const selected = Number(answer.dataset.answer) === state.selected[state.current];
        answer.classList.toggle('is-selected', selected); answer.setAttribute('aria-pressed', String(selected));
      });
      root.querySelector('[data-action="check"]').disabled = false;
      root.querySelector('.action-row > p').textContent = t().ready; return;
    }
    if (button.dataset.action === 'check' && state.selected[state.current] !== null && !answered(state.current)) {
      state.answers[state.current] = state.selected[state.current]; render('feedback-title'); return;
    }
    if (button.dataset.action === 'next') {
      if (complete()) state.view = 'results';
      else {
        const following = state.answers.findIndex((answer, i) => i > state.current && answer === null);
        state.current = following === -1 ? state.answers.indexOf(null) : following;
      }
      render(state.view === 'results' ? 'view-title' : 'question-title'); return;
    }
    if (button.dataset.action === 'restart') {
      state.answers.fill(null); state.selected.fill(null); state.current = 0; state.view = 'practice'; render('question-title');
    }
  });
  window.addEventListener('hashchange', () => {
    const requested = location.hash.slice(1);
    state.view = ['practice', 'questions', 'results'].includes(requested) && (requested !== 'results' || complete()) ? requested : 'practice';
    render(state.view === 'practice' ? 'question-title' : 'view-title');
  });
  if (location.hash === '#questions') state.view = 'questions';
  render();
})();
