import { text, icon, logicDemo, codeDemo, quizDemo } from '../shared.js';

function grove(lang) {
  const t = (he, en) => text(lang, he, en);
  return `
  <div class="grove-home">
    <section class="grove-hero grove-wrap" aria-labelledby="grove-title">
      <div class="grove-intro">
        <div class="grove-eyebrow"><span class="grove-small-orbit">${icon('spark')}</span>${t('מקום קטן. צעד גדול קדימה.', 'A little space. A clear next step.')}</div>
        <h1 id="grove-title">${t('להבין יותר. <br>להגיע מוכנים.', 'Understand more. <br>Walk in ready.')}</h1>
        <p>${t('לא צריך לדעת הכול כדי להתחיל. לוקחים מושג אחד, נותנים לו קצת מחשבה, וממשיכים משם.', 'You don’t need to know everything to begin. Take one concept, give it a little thought, and build from there.')}</p>
        <button class="button grove-start" data-action="practice">${t('מתחילים בצעד אחד', 'Take the first step')}${icon('arrow')}</button>
        <button class="grove-text-link" data-action="bank">${t('או בוחרים נושא שמעניין אתכם', 'Or find a topic that interests you')}${icon('chevron')}</button>
      </div>
      <div class="grove-trail" aria-label="${t('מסלול תרגול מוצע', 'A suggested practice trail')}">
        <div class="grove-trail-top"><span>${t('המסלול של היום', 'Today’s little trail')}</span><span class="grove-trail-label">${t('שלושה צעדים להבנה', 'Three steps to understanding')}</span></div>
        <div class="grove-trail-stem" aria-hidden="true"></div>
        <button class="grove-trail-stop grove-stop-one" data-topic="hardware">
          <span class="grove-step-number"><bdi dir="ltr">01</bdi></span>
          <span class="grove-stop-copy"><span class="grove-stop-kicker">${t('מתבוננים', 'See it')}</span><strong>${t('מה בעצם עושה XOR?', 'What does XOR really do?')}</strong><span>${t('שני קלטים, פלט אחד ורעיון פשוט.', 'Two inputs, one output, one simple idea.')}</span></span>
          <span class="grove-step-icon">${icon('circuit')}</span>
        </button>
        <button class="grove-trail-stop grove-stop-two" data-topic="software">
          <span class="grove-step-number"><bdi dir="ltr">02</bdi></span>
          <span class="grove-stop-copy"><span class="grove-stop-kicker">${t('חושבים', 'Think it through')}</span><strong>${t('איפה עובר הגבול של המערך?', 'Where does the array end?')}</strong><span>${t('מזהים גישה מחוץ לתחום בקוד C.', 'Spot an out-of-bounds access in C.')}</span></span>
          <span class="grove-step-icon">${icon('code')}</span>
        </button>
        <button class="grove-trail-stop grove-stop-three" data-topic="logic">
          <span class="grove-step-number"><bdi dir="ltr">03</bdi></span>
          <span class="grove-stop-copy"><span class="grove-stop-kicker">${t('מסבירים', 'Put it into words')}</span><strong>${t('אפשר לפתור גם בדרך אחרת?', 'Could you solve it another way?')}</strong><span>${t('בודקים הנחות ומנסחים את הדרך.', 'Check your assumptions. Explain your approach.')}</span></span>
          <span class="grove-step-icon">${icon('logic')}</span>
        </button>
        <div class="grove-trail-end"><span>${icon('check')}</span>${t('כל הבנה מתחילה בניסיון.', 'Every understanding begins with a try.')}</div>
      </div>
    </section>
    <section class="grove-playground grove-wrap" aria-labelledby="grove-playground-title">
      <div class="grove-play-copy"><span class="grove-section-label">${t('רגע של הבנה', 'A moment of understanding')}</span><h2 id="grove-playground-title">${t('לפעמים, פשוט <br>צריך לנסות.', 'Sometimes, you just <br>need to try it.')}</h2><p>${t('החליפו את הקלטים. שימו לב מתי הפלט משתנה. זה XOR: הפלט הוא 1 בדיוק כשהקלטים שונים.', 'Change the inputs. Notice when the output changes. That’s XOR: the output is 1 exactly when the inputs differ.')}</p><button class="grove-text-link" data-action="tools">${t('לפתוח את ארגז הכלים', 'Open the tool bench')}${icon('arrow')}</button></div>
      <div class="grove-lab"><div class="grove-lab-caption"><span><bdi dir="ltr">XOR</bdi> ${t('בידיים שלכם', 'at your fingertips')}</span><span class="grove-live-dot">${t('נסו בעצמכם', 'Try it yourself')}</span></div>${logicDemo(lang, 'xor')}<div class="grove-lab-note">${t('בלי שעון. בלי ציון. רק אתם והרגע שבו זה מתחבר.', 'No timer. No score. Just you, and the moment it clicks.')}</div></div>
    </section>
    <section class="grove-next grove-wrap"><div class="grove-next-symbol" aria-hidden="true">${icon('book')}</div><div><h2>${t('הקצב שלכם הוא הקצב הנכון.', 'Your pace is the right pace.')}</h2><p>${t('חומרה, תוכנה וחשיבה לוגית. בוחרים נקודת התחלה וחוזרים כשמתאים.', 'Hardware, software, and logical thinking. Choose a starting point. Come back when you’re ready.')}</p></div><button class="button secondary" data-action="guide">${t('איך מתרגלים כאן', 'How to practice here')}${icon('arrow')}</button></section>
  </div>`;
}

function coral(lang) {
  const t = (he, en) => text(lang, he, en);
  return `
  <div class="coral-home">
    <section class="coral-intro coral-wrap" aria-labelledby="coral-title">
      <div class="coral-title-area"><p class="coral-eyebrow">${t('מרחב לתרגול טכני', 'Room for technical thinking')}</p><h1 id="coral-title">${t('יש לכם את זה. <br><span>בואו נתרגל.</span>', 'You’ve got this. <br><span>Let’s practice.</span>')}</h1></div>
      <div class="coral-intro-aside"><div class="coral-asterisk" aria-hidden="true">✳</div><p>${t('הרגע שבו מושג הופך להבנה? הוא מתחיל כשמנסים. בחרו צד וסקרנות תעשה את השאר.', 'That moment when a concept finally clicks? It starts with a try. Pick a side. Let curiosity do the rest.')}</p><button class="coral-text-link" data-action="practice">${t('לתרגול הראשון שלי', 'Start my first practice')}${icon('arrow')}</button></div>
    </section>
    <section class="coral-surfaces coral-wrap" aria-label="${t('בחרו מה לתרגל', 'Choose what to practice')}">
      <article class="coral-surface coral-hardware">
        <div class="coral-surface-heading"><span class="coral-subject-number"><bdi dir="ltr">01 /</bdi> ${t('חומרה', 'HARDWARE')}</span><span class="coral-surface-icon">${icon('circuit')}</span></div>
        <h2>${t('רעיונות. <br>שמתחברים.', 'Ideas. <br>Connected.')}</h2>
        <p>${t('משער לוגי קטן ועד מכונת מצבים. תנו למעגל לעשות סדר במחשבה.', 'From a single logic gate to a state machine. Let the circuit make things clear.')}</p>
        <div class="coral-demo-shell"><div class="coral-demo-label"><bdi dir="ltr">XOR</bdi><span>${t('שנו קלט. ראו מה קורה.', 'Change an input. See what happens.')}</span></div>${logicDemo(lang, 'xor')}</div>
        <div class="coral-surface-bottom"><span><bdi dir="ltr">AND · XOR · MUX · FSM</bdi></span><button class="coral-circle-link" data-topic="hardware" aria-label="${t('לתרגול חומרה', 'Explore hardware')}">${icon('arrow')}</button></div>
      </article>
      <article class="coral-surface coral-software">
        <div class="coral-surface-heading"><span class="coral-subject-number"><bdi dir="ltr">02 /</bdi> ${t('תוכנה', 'SOFTWARE')}</span><span class="coral-surface-icon">${icon('code')}</span></div>
        <h2>${t('קוד קטן. <br>תובנה גדולה.', 'Small code. <br>Big insight.')}</h2>
        <p>${t('קוראים לאט, חושבים בקול ומגלים מה מסתתר בשורות הקטנות.', 'Read closely, think out loud, and find what’s hiding between the lines.')}</p>
        <div class="coral-code-shell">${codeDemo(lang)}</div>
        <div class="coral-surface-bottom"><span>${t('גבולות מערך · תנאים · חשיבה אלגוריתמית', 'Array bounds · Conditions · Algorithms')}</span><button class="coral-circle-link" data-topic="software" aria-label="${t('לתרגול תוכנה', 'Explore software')}">${icon('arrow')}</button></div>
      </article>
    </section>
    <section class="coral-rhythm coral-wrap" aria-labelledby="coral-rhythm-title"><div class="coral-rhythm-title"><span class="coral-eyebrow">${t('בלי קיצורי דרך. עם דרך ברורה.', 'No shortcuts. A clear way forward.')}</span><h2 id="coral-rhythm-title">${t('תרגול טוב. <br>בשלושה רגעים.', 'Good practice. <br>Three simple moments.')}</h2></div><div class="coral-rhythm-steps"><div><span class="coral-rhythm-number"><bdi dir="ltr">1</bdi></span><h3>${t('מנסים', 'Try')}</h3><p>${t('שאלה אחת. מקום לחשוב.', 'One question. Room to think.')}</p></div><div><span class="coral-rhythm-number"><bdi dir="ltr">2</bdi></span><h3>${t('מסבירים', 'Explain')}</h3><p>${t('מנסחים את הדרך במילים שלכם.', 'Put your approach into your words.')}</p></div><div><span class="coral-rhythm-number"><bdi dir="ltr">3</bdi></span><h3>${t('מגלים', 'Discover')}</h3><p>${t('פותחים פתרון ורואים עוד זווית.', 'Open a solution. See another angle.')}</p></div></div><button class="button coral-guide" data-action="guide">${t('ככה זה עובד', 'See how it works')}${icon('arrow')}</button></section>
  </div>`;
}

function cobalt(lang) {
  const t = (he, en) => text(lang, he, en);
  const rows = [
    ['hardware', 'circuit', 'שער XOR: כשהקלטים שונים', 'XOR: when the inputs differ', 'שערים לוגיים', 'Logic gates', 'יסודות', 'Fundamentals'],
    ['software', 'code', 'האם הגישה למערך בטוחה?', 'Is the array access safe?', 'C וגבולות מערך', 'C · Array bounds', 'קריאת קוד', 'Code reading'],
    ['hardware', 'circuit', 'מה בוחר המולטיפלקסר?', 'What does the multiplexer select?', 'לוגיקה צירופית', 'Combinational logic', 'יסודות', 'Fundamentals'],
    ['logic', 'logic', 'איזו הנחה חסרה בפתרון?', 'Which assumption is missing?', 'הסקה לוגית', 'Logical reasoning', 'חשיבה', 'Reasoning'],
    ['software', 'code', 'מתי התנאי השני בכלל נבדק?', 'When is the second condition evaluated?', 'C ו־Short circuit', 'C · Short circuit', 'קריאת קוד', 'Code reading'],
    ['hardware', 'circuit', 'מכונת מצבים, צעד אחר צעד', 'A state machine, step by step', 'FSM ומעברי מצב', 'FSM · State transitions', 'ניתוח', 'Analysis'],
    ['logic', 'logic', 'יותר מדרך אחת לתשובה', 'More than one way to the answer', 'פתרון בעיות', 'Problem solving', 'חשיבה', 'Reasoning'],
  ];
  return `
  <div class="cobalt-home cobalt-wrap">
    <div class="cobalt-workspace">
      <aside class="cobalt-sidebar" aria-label="${t('ניווט במאגר', 'Library navigation')}"><div class="cobalt-sidebar-body">
        <div class="cobalt-sidebar-title">${icon('book')}<strong>${t('מרחב התרגול', 'Practice space')}</strong></div>
        <div class="cobalt-sidebar-group"><span class="cobalt-sidebar-label">${t('הספרייה שלכם', 'YOUR LIBRARY')}</span><button class="cobalt-side-link cobalt-side-active" data-action="bank">${icon('book')}<span>${t('כל השאלות', 'All questions')}</span><span class="cobalt-side-dot"></span></button><button class="cobalt-side-link" data-action="practice">${icon('play')}<span>${t('תרגול ממוקד', 'Focused practice')}</span></button></div>
        <div class="cobalt-sidebar-group"><span class="cobalt-sidebar-label">${t('לפי נושא', 'EXPLORE TOPICS')}</span><button class="cobalt-side-link" data-topic="hardware">${icon('circuit')}<span>${t('חומרה', 'Hardware')}</span></button><button class="cobalt-side-link" data-topic="software">${icon('code')}<span>${t('תוכנה', 'Software')}</span></button><button class="cobalt-side-link" data-topic="logic">${icon('logic')}<span>${t('חשיבה לוגית', 'Logical thinking')}</span></button></div>
        <div class="cobalt-sidebar-group"><span class="cobalt-sidebar-label">${t('ליד השאלות', 'AT YOUR SIDE')}</span><button class="cobalt-side-link" data-action="tools">${icon('circuit')}<span>${t('ארגז הכלים', 'Tool bench')}</span></button><button class="cobalt-side-link" data-action="guide">${icon('book')}<span>${t('מדריך לתרגול', 'Practice guide')}</span></button></div>
        <div class="cobalt-sidebar-note"><span class="cobalt-note-mark">${icon('spark')}</span><strong>${t('מושג אחד בכל פעם.', 'One concept at a time.')}</strong><p>${t('מקום לקרוא, לנסות ולהבין את הדרך.', 'A place to read, try, and understand the approach.')}</p></div>
      </div></aside>
      <section class="cobalt-library" aria-labelledby="cobalt-title">
        <div class="cobalt-breadcrumb">${t('מרחב התרגול', 'Practice space')}<span>/</span><strong>${t('כל השאלות', 'All questions')}</strong></div>
        <div class="cobalt-library-heading"><div><h1 id="cobalt-title">${t('מה תרצו להבין היום?', 'What will you understand today?')}</h1><p>${t('שאלות טכניות. הסברים ברורים. מקום לחשוב.', 'Technical questions. Clear explanations. Room to think.')}</p></div><button class="button cobalt-practice" data-action="practice">${icon('play')}${t('תרגול חדש', 'New practice')}</button></div>
        <label class="cobalt-search">${icon('search')}<input type="search" data-search placeholder="${t('חפשו מושג, שאלה או קטע קוד', 'Search a concept, question, or code snippet')}" aria-label="${t('חיפוש במאגר השאלות', 'Search the question library')}"><span class="cobalt-search-key" aria-hidden="true">↵</span></label>
        <div class="cobalt-topic-strip"><span>${t('להתחיל עם', 'Start with')}</span><button data-topic="hardware"><bdi dir="ltr">XOR</bdi></button><button data-topic="software">${t('גבולות מערך', 'Array bounds')}</button><button data-topic="hardware"><bdi dir="ltr">FSM</bdi></button><button data-topic="logic">${t('חשיבה לוגית', 'Logical thinking')}</button></div>
        <section class="cobalt-start" aria-labelledby="cobalt-start-title"><div class="cobalt-start-copy"><span class="cobalt-section-kicker">${t('פתיחה קצרה', 'A QUICK START')}</span><h2 id="cobalt-start-title">${t('כמה טוב אתם <br>מכירים את AND?', 'How well do you <br>know AND?')}</h2><p>${t('התחילו בשאלה אחת. בחרו תשובה וגלו את ההסבר.', 'Begin with one question. Choose an answer and find out why.')}</p></div><div class="cobalt-start-quiz">${quizDemo(lang)}</div></section>
        <div class="cobalt-list-heading"><h2>${t('לחקור את היסודות', 'Explore the fundamentals')}</h2><button class="cobalt-inline-link" data-action="bank">${t('פתיחת המאגר', 'Open library')}${icon('arrow')}</button></div>
        <div class="cobalt-question-list"><div class="cobalt-column-head"><span>${t('שאלה', 'QUESTION')}</span><span>${t('סוג התרגול', 'PRACTICE TYPE')}</span></div>${rows.map(([topic, symbol, he, en, subHe, subEn, typeHe, typeEn]) => `<button class="cobalt-question-row" data-topic="${topic}"><span class="cobalt-question-symbol cobalt-symbol-${topic}">${icon(symbol)}</span><span class="cobalt-question-name"><strong>${t(he, en)}</strong><span>${t(subHe, subEn)}</span></span><span class="cobalt-question-type">${t(typeHe, typeEn)}</span><span class="cobalt-question-arrow">${icon('chevron')}</span></button>`).join('')}</div>
        <div class="cobalt-library-bottom"><span>${icon('check')}${t('מתרגלים דרך. לא רק תשובה.', 'Practice the approach. Understand the answer.')}</span><button class="cobalt-inline-link" data-action="game">${t('לנסות אתגר לוגי', 'Try a logic challenge')}${icon('arrow')}</button></div>
      </section>
    </div>
  </div>`;
}

export function render(id, lang) {
  return id === 'grove' ? grove(lang) : id === 'coral' ? coral(lang) : cobalt(lang);
}
