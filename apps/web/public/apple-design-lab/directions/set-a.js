import { text, icon, logicDemo, codeDemo, quizDemo } from '../shared.js';

const action = (lang, labelHe, labelEn, name, cls = '') => `<button class="button ${cls}" data-action="${name}">${text(lang, labelHe, labelEn)}${icon('arrow')}</button>`;

function clarity(lang) {
  return `<div class="clarity-page">
    <section class="clarity-intro clarity-wrap" aria-labelledby="clarity-title">
      <p class="clarity-kicker">${text(lang, 'הצעד הבא שלך בהנדסה.', 'Your next step in engineering.')}</p>
      <h1 id="clarity-title">${text(lang, 'פחות לשנן.<br><span>יותר להבין.</span>', 'Less memorizing.<br><span>More understanding.</span>')}</h1>
      <p class="clarity-description">${text(lang, 'להגיע לראיון הטכני עם דרך חשיבה ברורה. שאלות, קוד ומעגלים — במקום אחד שמפנה מקום להבנה.', 'Walk into your technical interview with a clearer way to think. Questions, code and circuits, in one focused place to practice.')}</p>
      <div class="clarity-actions">${action(lang, 'מתחילים לתרגל', 'Start practicing', 'practice')}${action(lang, 'מגלים את המאגר', 'Explore the library', 'bank', 'quiet')}</div>
    </section>
    <section class="clarity-workspace clarity-wrap" aria-label="${text(lang, 'סביבת תרגול לדוגמה', 'Sample practice workspace')}">
      <div class="clarity-workspace-top"><span class="clarity-workspace-name">${icon('circuit')} ${text(lang, 'מחשבה, בפעולה.', 'Thinking, in action.')}</span><span class="clarity-sample"><i></i>${text(lang, 'התנסות מקומית', 'Interactive preview')}</span></div>
      <div class="clarity-workspace-body">
        <aside class="clarity-brief">
          <span class="clarity-unit">${text(lang, 'לוגיקה ספרתית', 'Digital logic')}</span>
          <h2>${text(lang, 'שני קלטים. <br>רגע של הבנה.', 'Two inputs. <br>One clear insight.')}</h2>
          <p>${text(lang, 'מה קורה כשהקלטים שונים? משנים את הערכים ורואים מיד איך שער XOR מגיב.', 'What happens when the inputs differ? Change the values and see how an XOR gate responds.')}</p>
          <div class="clarity-equation"><bdi dir="ltr">Y = A ⊕ B</bdi><span>${text(lang, 'הפלט גבוה רק כשקלט אחד גבוה.', 'The output is high when exactly one input is high.')}</span></div>
          <button class="clarity-text-action" data-action="tools">${text(lang, 'לכל כלי התרגול', 'Explore practice tools')}${icon('arrow')}</button>
        </aside>
        <div class="clarity-live"><div class="clarity-live-label">${icon('play')}<span>${text(lang, 'נסו בעצמכם', 'Try it yourself')}</span></div>${logicDemo(lang)}<p class="clarity-live-note">${text(lang, 'לוחצים על A או B כדי לשנות את הקלט.', 'Select A or B to change the input.')}</p></div>
      </div>
    </section>
    <section class="clarity-paths clarity-wrap" aria-labelledby="clarity-path-title">
      <div class="clarity-path-heading"><h2 id="clarity-path-title">${text(lang, 'בוחרים נושא. <br>מתקדמים מהבסיס.', 'Pick a subject. <br>Build from the basics.')}</h2><p>${text(lang, 'תרגול קצר וממוקד, בקצב שלך.', 'Short, focused practice. At your pace.')}</p></div>
      <div class="clarity-path-list">
        <button class="clarity-path" data-topic="hardware"><span class="clarity-path-icon">${icon('circuit')}</span><span><strong>${text(lang, 'חומרה', 'Hardware')}</strong><small>${text(lang, 'ממעגלים ספרתיים ועד תזמון', 'From digital circuits to timing')}</small></span>${icon('arrow')}</button>
        <button class="clarity-path" data-topic="software"><span class="clarity-path-icon">${icon('code')}</span><span><strong>${text(lang, 'תוכנה', 'Software')}</strong><small>${text(lang, 'קוד, זיכרון וחשיבה אלגוריתמית', 'Code, memory and algorithms')}</small></span>${icon('arrow')}</button>
        <button class="clarity-path" data-topic="logic"><span class="clarity-path-icon">${icon('logic')}</span><span><strong>${text(lang, 'חשיבה', 'Reasoning')}</strong><small>${text(lang, 'לפרק בעיה ולמצוא כיוון', 'Break down a problem, find a path')}</small></span>${icon('arrow')}</button>
      </div>
    </section>
  </div>`;
}

function graphite(lang) {
  return `<div class="graphite-page">
    <section class="graphite-hero graphite-wrap" aria-labelledby="graphite-title">
      <div class="graphite-intro">
        <p class="graphite-eyebrow"><span></span>${text(lang, 'סביבת האימון שלך להנדסה', 'Your engineering practice environment')}</p>
        <h1 id="graphite-title">${text(lang, 'החשיבה שלך.<br>הכלים שלך.<br><span>הצעד הבא.</span>', 'Your thinking.<br>Your tools.<br><span>Your next move.</span>')}</h1>
        <p class="graphite-description">${text(lang, 'ראיון טכני מתחיל הרבה לפני השאלה הראשונה. בונים ביטחון עם קוד אמיתי, מעגלים ותרגול מכוון.', 'A technical interview starts long before the first question. Build confidence through real code, circuits and deliberate practice.')}</p>
        <div class="graphite-actions">${action(lang, 'פותחים תרגול', 'Open practice', 'practice')}${action(lang, 'למאגר השאלות', 'Question library', 'bank', 'quiet')}</div>
        <div class="graphite-topics"><span><bdi dir="ltr">C / C++</bdi></span><span>${text(lang, 'לוגיקה ספרתית', 'Digital logic')}</span><span>${text(lang, 'פתרון בעיות', 'Problem solving')}</span></div>
      </div>
      <div class="graphite-machine">
        <div class="graphite-machine-head"><span class="graphite-dots"><i></i><i></i><i></i></span><span><bdi dir="ltr">array.c</bdi></span><span class="graphite-file-type">C</span></div>
        <div class="graphite-problem"><span class="graphite-caption">${text(lang, 'מסתכלים מקרוב', 'Look a little closer')}</span><h2>${text(lang, 'היכן הלולאה צריכה לעצור?', 'Where should this loop stop?')}</h2><p>${text(lang, 'לפני שמריצים, בודקים את גבולות המערך.', 'Before you run it, check the array bounds.')}</p></div>
        ${codeDemo(lang)}
        <div class="graphite-machine-foot">${icon('code')}<span>${text(lang, 'להבין את הדרך, לא רק את התוצאה.', 'Understand the path, not just the output.')}</span></div>
      </div>
    </section>
    <section class="graphite-foundations" aria-labelledby="graphite-foundations-title"><div class="graphite-wrap">
      <div class="graphite-section-head"><span class="graphite-section-marker"><bdi dir="ltr">01 — 03</bdi></span><h2 id="graphite-foundations-title">${text(lang, 'יכולת בונים.<br>שאלה אחרי שאלה.', 'Skill is built.<br>One question at a time.')}</h2><p>${text(lang, 'ניגשים לבעיה. מנסחים פתרון. חוזרים למה שדורש עוד עבודה. מרחב אחד לתרגול שלם.', 'Approach a problem. Explain your solution. Return to what needs more work. One space for the whole practice.')}</p></div>
      <div class="graphite-curriculum">
        <button class="graphite-track" data-topic="hardware"><span class="graphite-track-number">01</span><div><h3>${text(lang, 'חושבים בחומרה', 'Think in hardware')}</h3><p>${text(lang, 'מעגלים, מערכות ספרתיות ויסודות אלקטרוניקה.', 'Circuits, digital systems and electronics fundamentals.')}</p></div><span class="graphite-track-action">${icon('circuit')}${icon('arrow')}</span></button>
        <button class="graphite-track" data-topic="software"><span class="graphite-track-number">02</span><div><h3>${text(lang, 'קוראים בין שורות הקוד', 'Read between the lines')}</h3><p>${text(lang, 'מצביעים, פעולות ביטים ומבני נתונים.', 'Pointers, bitwise operations and data structures.')}</p></div><span class="graphite-track-action">${icon('code')}${icon('arrow')}</span></button>
        <button class="graphite-track" data-topic="logic"><span class="graphite-track-number">03</span><div><h3>${text(lang, 'מפרקים את הלא מוכר', 'Make sense of the unfamiliar')}</h3><p>${text(lang, 'חידות היגיון ודרך מסודרת לגשת לבעיה.', 'Reasoning challenges and a structured way into a problem.')}</p></div><span class="graphite-track-action">${icon('logic')}${icon('arrow')}</span></button>
      </div>
    </div></section>
  </div>`;
}

function prism(lang) {
  return `<div class="prism-page">
    <section class="prism-stage prism-wrap" aria-labelledby="prism-title">
      <div class="prism-intro"><p class="prism-kicker">${text(lang, 'מרחב קטן. התקדמות גדולה.', 'A little space to make progress.')}</p><h1 id="prism-title">${text(lang, 'לפנות מקום<br><span>לרגע של הבנה.</span>', 'Make room<br><span>for the aha.</span>')}</h1><p>${text(lang, 'סביבת תרגול שמחברת בין השאלה, הניסוי וההסבר. כדי שהראיון הבא יתחיל ממקום בטוח יותר.', 'A practice space that connects the question, the experiment and the explanation. Feel more grounded for your next interview.')}</p>${action(lang, 'נכנסים למרחב התרגול', 'Enter your practice space', 'practice')}</div>
      <div class="prism-spatial">
        <div class="prism-toolbar" aria-label="${text(lang, 'בחירת תחום תרגול', 'Practice subjects')}"><span class="prism-toolmark">${icon('spark')}</span><button class="prism-tool prism-tool-current" data-action="tools">${icon('circuit')}<span>${text(lang, 'מעגלים', 'Circuits')}</span></button><button class="prism-tool" data-topic="software">${icon('code')}<span>${text(lang, 'קוד', 'Code')}</span></button><button class="prism-tool" data-action="guide">${icon('book')}<span>${text(lang, 'מדריך', 'Guide')}</span></button></div>
        <div class="prism-canvas"><div class="prism-canvas-head"><div><span class="prism-window-kicker">${text(lang, 'מרחב ניסוי', 'Experiment space')}</span><h2>${text(lang, 'משנים קלט. מבינים קשר.', 'Change an input. See a connection.')}</h2></div><span class="prism-canvas-symbol">${icon('circuit')}</span></div>${logicDemo(lang, 'and')}<div class="prism-canvas-bottom"><span class="prism-tiny-dot"></span><span>${text(lang, 'הסימולציה מגיבה לכל שינוי.', 'The simulation responds to every change.')}</span><bdi dir="ltr">AND</bdi></div></div>
        <aside class="prism-coach"><div class="prism-coach-head"><span class="prism-coach-icon">${icon('logic')}</span><div><strong>${text(lang, 'רגע למחשבה', 'A moment to think')}</strong><span>${text(lang, 'שאלת בדיקה קצרה', 'A quick understanding check')}</span></div></div>${quizDemo(lang)}</aside>
      </div>
    </section>
    <section class="prism-flow prism-wrap" aria-labelledby="prism-flow-title"><div class="prism-flow-intro"><span class="prism-flow-mark">${icon('spark')}</span><h2 id="prism-flow-title">${text(lang, 'מניחוש להבנה.<br>בקצב שנכון לך.', 'From guessing to knowing.<br>At your own pace.')}</h2><p>${text(lang, 'לא חייבים לדעת מאיפה להתחיל. בוחרים שאלה ונותנים לסקרנות להוביל.', 'You don’t need to know where to begin. Pick a question and let curiosity lead.')}</p></div><div class="prism-flow-steps"><div class="prism-flow-step"><span>1</span><div><h3>${text(lang, 'פוגשים שאלה', 'Meet a question')}</h3><p>${text(lang, 'נושא אחד, מטרה ברורה, התחלה פשוטה.', 'One subject, a clear goal, a simple start.')}</p></div></div><div class="prism-flow-step"><span>2</span><div><h3>${text(lang, 'מנסים ומגלים', 'Try, then discover')}</h3><p>${text(lang, 'מפעילים קוד או מעגל ובודקים את החשיבה.', 'Use code or a circuit to test your thinking.')}</p></div></div><div class="prism-flow-step"><span>3</span><div><h3>${text(lang, 'ממשיכים עם כיוון', 'Continue with direction')}</h3><p>${text(lang, 'קוראים הסבר וחוזרים למה שצריך לחזק.', 'Read an explanation and revisit what needs work.')}</p></div></div><button class="prism-flow-link" data-action="bank">${text(lang, 'למצוא את השאלה הראשונה שלי', 'Find my first question')}${icon('arrow')}</button></div></section>
  </div>`;
}

export function render(id, lang) {
  return ({ clarity, graphite, prism }[id] || clarity)(lang);
}
