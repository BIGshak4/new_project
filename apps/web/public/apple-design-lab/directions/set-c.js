import { text, icon, logicDemo } from '../shared.js';

const bdi = value => `<bdi dir="ltr">${value}</bdi>`;
const action = (lang, labelHe, labelEn, value = 'practice', className = 'button') => `<button class="${className}" data-action="${value}">${text(lang, labelHe, labelEn)}${icon('arrow')}</button>`;

function titanium(lang) {
  return `<div class="titanium-page">
    <section class="titanium-intro site-shell" aria-labelledby="titanium-title">
      <div class="titanium-intro-copy"><p class="titanium-eyebrow"><span></span>${text(lang, 'מרחב עבודה לחשיבה הנדסית', 'A workspace for engineering minds')}</p><h1 id="titanium-title">${text(lang, 'להבין.<br>עד האות האחרון.', 'Understand.<br>Every last signal.')}</h1></div>
      <div class="titanium-intro-aside"><p>${text(lang, 'מורידים רעש. בונים הבנה. תרגול ממוקד לראיונות בחומרה, תוכנה וחשיבה לוגית.', 'Less noise. More understanding. Focused interview practice in hardware, software, and logical thinking.')}</p><div class="titanium-actions">${action(lang, 'פותחים תרגול', 'Open practice')}${action(lang, 'למאגר השאלות', 'Question library', 'bank', 'button quiet')}</div></div>
    </section>

    <section class="titanium-instrument site-shell" aria-labelledby="titanium-instrument-title">
      <div class="titanium-frame">
        <div class="titanium-toolbar"><span class="titanium-toolbar-title">${icon('circuit')}${text(lang, 'שולחן העבודה', 'The workbench')}</span><span class="titanium-toolbar-index">${bdi('01 / 03')}<i></i>${text(lang, 'לוגיקה ספרתית', 'Digital logic')}</span></div>
        <div class="titanium-machine">
          <aside class="titanium-controls" aria-label="${text(lang, 'תחומי תרגול', 'Practice subjects')}">
            <p class="titanium-control-caption">${text(lang, 'בחרו כיוון', 'Select a discipline')}</p>
            <button data-topic="hardware" class="titanium-control titanium-control-current"><span class="titanium-control-symbol">${icon('logic')}</span><span><strong>${text(lang, 'לוגיקה ספרתית', 'Digital logic')}</strong><small>${text(lang, 'שערים. תנאים. הבנה.', 'Gates. Conditions. Clarity.')}</small></span><i></i></button>
            <button data-topic="hardware" class="titanium-control"><span class="titanium-control-symbol">${icon('circuit')}</span><span><strong>${text(lang, 'חומרה', 'Hardware')}</strong><small>${text(lang, 'מהאות אל המערכת', 'From signal to system')}</small></span>${icon('chevron')}</button>
            <button data-topic="software" class="titanium-control"><span class="titanium-control-symbol">${icon('code')}</span><span><strong>${text(lang, 'תוכנה', 'Software')}</strong><small>${text(lang, 'לקרוא. לפרק. לפתור.', 'Read. Reason. Solve.')}</small></span>${icon('chevron')}</button>
            <div class="titanium-control-foot"><span class="titanium-knob" aria-hidden="true"></span><span>${text(lang, 'הקצב שלכם.<br>השליטה שלכם.', 'Your pace.<br>Your controls.')}</span></div>
          </aside>
          <div class="titanium-stage"><div class="titanium-stage-heading"><div><p class="titanium-stage-kicker">${bdi('XOR / EXCLUSIVE OR')}</p><h2 id="titanium-instrument-title">${text(lang, 'שני קלטים.<br>רעיון אחד ברור.', 'Two inputs.<br>One clear idea.')}</h2></div><span class="titanium-stage-chip">${text(lang, 'נסו בעצמכם', 'Try it yourself')}${icon('play')}</span></div>
            <div class="titanium-demo">${logicDemo(lang, 'xor')}</div>
            <div class="titanium-stage-note"><span>${text(lang, 'שנו קלט. עקבו אחרי הפלט.', 'Change an input. Follow the output.')}</span><span>${bdi('Y = A ⊕ B')}</span></div>
          </div>
        </div>
        <div class="titanium-status"><span><i></i>${text(lang, 'הפלט משתנה בזמן אמת', 'The output responds in real time')}</span><span>${text(lang, 'משער בודד לתמונה המלאה', 'From a single gate to the whole picture')}</span></div>
      </div>
    </section>

    <section class="titanium-method site-shell" aria-labelledby="titanium-method-title"><div class="titanium-method-heading"><p class="titanium-eyebrow">${text(lang, 'הדרך אל התשובה', 'The way to an answer')}</p><h2 id="titanium-method-title">${text(lang, 'הבנה שאפשר <br>להסביר בקול.', 'Understanding <br>you can put into words.')}</h2></div><div class="titanium-method-steps"><div><span>${bdi('01')}</span><h3>${text(lang, 'בודקים את היסודות', 'Check the fundamentals')}</h3><p>${text(lang, 'שאלות קצרות חושפות את החיבור שעוד חסר.', 'Short questions reveal the connection that is still missing.')}</p></div><div><span>${bdi('02')}</span><h3>${text(lang, 'עובדים דרך השאלה', 'Work through the question')}</h3><p>${text(lang, 'מנסים, משנים קלט ומסבירים את דרך המחשבה.', 'Try, change an input, and explain the reasoning.')}</p></div><div><span>${bdi('03')}</span><h3>${text(lang, 'מחדדים את ההסבר', 'Make the explanation clear')}</h3><p>${text(lang, 'משווים לפתרון ייחוס וחוזרים לנקודה שדורשת תרגול.', 'Compare with a reference solution and revisit what needs practice.')}</p></div></div></section>
  </div>`;
}

function midnight(lang) {
  return `<div class="midnight-page">
    <section class="midnight-focus site-shell" aria-labelledby="midnight-title"><p class="midnight-eyebrow"><span></span>${text(lang, 'שאלה אחת. מלוא תשומת הלב.', 'One question. Your full attention.')}</p><h1 id="midnight-title">${text(lang, 'הרגע שבו<br>הכול מתחבר.', 'The moment<br>it clicks.')}</h1><p class="midnight-intro">${text(lang, 'מפנים מקום לחשוב. מפרקים שאלה טכנית, צעד אחר צעד, עד שהעיקרון נעשה ברור.', 'Make room to think. Work through a technical question, one step at a time, until the principle becomes clear.')}</p></section>

    <section class="midnight-experiment site-shell" aria-labelledby="midnight-question"><div class="midnight-experiment-bar"><span>${bdi('01')}<i></i>${text(lang, 'לוגיקה ספרתית', 'Digital logic')}</span><span>${bdi('XOR GATE')}</span></div><h2 id="midnight-question">${text(lang, 'מתי הפלט יהיה', 'When does the output become')} ${bdi('1')}?</h2><div class="midnight-native-stage"><div class="midnight-live-demo">${logicDemo(lang, 'xor')}</div></div><div class="midnight-insight"><p>${text(lang, 'כשהקלטים שונים, האות עובר.<br>שנו קלט ובדקו את הרעיון.', 'When the inputs differ, the signal passes.<br>Change an input and test the idea.')}</p><div>${action(lang, 'ממשיכים לתרגל', 'Keep thinking')}</div></div></section>

    <section class="midnight-next site-shell" aria-labelledby="midnight-next-title"><div class="midnight-next-label"><h2 id="midnight-next-title">${text(lang, 'לאן המחשבה לוקחת אתכם?', 'Where will your thinking take you?')}</h2><p>${text(lang, 'בחרו תחום. התחילו משאלה אחת.', 'Choose a discipline. Start with one question.')}</p></div><nav class="midnight-dock" aria-label="${text(lang, 'בחירת תחום תרגול', 'Choose a practice discipline')}"><button data-topic="hardware">${icon('circuit')}<span>${text(lang, 'חומרה', 'Hardware')}</span>${icon('arrow')}</button><button data-topic="software">${icon('code')}<span>${text(lang, 'תוכנה', 'Software')}</span>${icon('arrow')}</button><button data-topic="logic">${icon('logic')}<span>${text(lang, 'חשיבה לוגית', 'Logical thinking')}</span>${icon('arrow')}</button></nav><button class="midnight-guide" data-action="guide">${icon('book')}${text(lang, 'צריכים נקודת התחלה? פתחו את המדריך.', 'Need a starting point? Open the guide.')}${icon('arrow')}</button></section>
  </div>`;
}

function linen(lang) {
  return `<div class="linen-page">
    <section class="linen-intro site-shell" aria-labelledby="linen-title"><div><p class="linen-eyebrow">${text(lang, 'מקום למחשבה טובה', 'A little room for good thinking')}</p><h1 id="linen-title">${text(lang, 'מחשבה ברורה.<br>צעד קדימה.', 'Clear thinking.<br>Steady progress.')}</h1><p class="linen-lead">${text(lang, 'לא חייבים לדעת מיד. לומדים לפרק שאלה, למצוא את העיקרון ולנסח תשובה שאפשר לעמוד מאחוריה.', 'You do not have to know straight away. Learn to unpack a question, find the principle, and give an answer you can stand behind.')}</p>${action(lang, 'מתחילים משאלה אחת', 'Start with one question')}</div><aside class="linen-side-note"><span class="linen-book-mark">${icon('book')}</span><h2>${text(lang, 'לקרוא. <br>לחשוב. <br>להסביר.', 'Read. <br>Think. <br>Explain.')}</h2><p>${text(lang, 'תרגול לראיונות טכניים,<br>בקצב שמאפשר להבין.', 'Technical interview practice,<br>at a pace that makes sense.')}</p></aside></section>

    <section class="linen-notebook-wrap site-shell" aria-labelledby="linen-notebook-title"><div class="linen-notebook-label"><span>${text(lang, 'מתוך מחברת התרגול', 'From the practice notebook')}</span><span>${text(lang, 'לוגיקה ספרתית', 'Digital logic')} · ${bdi('XOR')}</span></div><div class="linen-notebook"><div class="linen-notebook-page linen-question"><p class="linen-page-caption">${bdi('01')}<span>${text(lang, 'להבין את השאלה', 'Understand the question')}</span></p><h2 id="linen-notebook-title">${text(lang, 'מה קורה<br>כשהקלטים שונים?', 'What happens<br>when the inputs differ?')}</h2><p>${text(lang, 'שער', 'An')} ${bdi('XOR')} ${text(lang, 'מחזיר 1 כאשר רק אחד משני הקלטים הוא 1. נסו לשנות את הקלטים.', 'gate returns 1 when exactly one of the two inputs is 1. Try changing the inputs.')}</p><div class="linen-demo">${logicDemo(lang, 'xor')}</div><div class="linen-page-number">${bdi('01')}</div></div><div class="linen-notebook-page linen-reasoning"><p class="linen-page-caption">${bdi('02')}<span>${text(lang, 'למצוא את העיקרון', 'Find the principle')}</span></p><h3>${text(lang, 'ההבדל הוא כל הסיפור.', 'The difference is the idea.')}</h3><p>${text(lang, 'במקום לזכור ארבע תוצאות בנפרד, חפשו כלל אחד שמחבר ביניהן.', 'Rather than memorizing four separate outcomes, find one rule that connects them.')}</p><table class="linen-truth" dir="ltr" aria-label="${text(lang, 'טבלת אמת של שער XOR', 'XOR truth table')}"><thead><tr><th>${bdi('A')}</th><th>${bdi('B')}</th><th>${bdi('A ⊕ B')}</th></tr></thead><tbody><tr><td>0</td><td>0</td><td>0</td></tr><tr class="linen-truth-different"><td>0</td><td>1</td><td>1</td></tr><tr class="linen-truth-different"><td>1</td><td>0</td><td>1</td></tr><tr><td>1</td><td>1</td><td>0</td></tr></tbody></table><div class="linen-takeaway"><span>${icon('check')}</span><p>${text(lang, 'קלטים שונים ← פלט 1.<br>עכשיו נסו להסביר למה, במילים שלכם.', 'Different inputs → output 1.<br>Now try explaining why, in your own words.')}</p></div><div class="linen-page-number">${bdi('02')}</div></div></div></section>

    <section class="linen-reading-path site-shell" aria-labelledby="linen-next-title"><div><p class="linen-eyebrow">${text(lang, 'ממשיכים מהנקודה שלכם', 'Continue from where you are')}</p><h2 id="linen-next-title">${text(lang, 'תמיד יש חיבור <br>חדש לגלות.', 'There is always <br>another connection.')}</h2></div><div class="linen-reading-links"><button data-action="bank"><span><strong>${text(lang, 'פותחים את מאגר השאלות', 'Explore the question library')}</strong><small>${text(lang, 'חומרה, תוכנה וחשיבה לוגית', 'Hardware, software, and logical thinking')}</small></span>${icon('arrow')}</button><button data-action="guide"><span><strong>${text(lang, 'מתכוננים לשיחה הטכנית', 'Prepare for the technical conversation')}</strong><small>${text(lang, 'דרך מסודרת להסביר את מה שאתם יודעים', 'A clear way to explain what you know')}</small></span>${icon('arrow')}</button></div></section>
  </div>`;
}

export function render(id, lang) {
  if (id === 'titanium') return titanium(lang);
  if (id === 'midnight') return midnight(lang);
  if (id === 'linen') return linen(lang);
  return '';
}
