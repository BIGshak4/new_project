import type { SupportCategory } from "./support-report";

export type HelperText = { he: string; en: string };
export type HelperTopicId =
  | "root" | "getting-started" | "site-map" | "library" | "tour"
  | "practice" | "explanation" | "dictation" | "software" | "code-start" | "code-run"
  | "hardware" | "circuit-build" | "circuit-check" | "feedback" | "interview"
  | "support" | "support-bug" | "support-question" | "support-feedback" | "support-other"
  | "avatar" | "games" | "shop" | "shortcuts";

/** Focus actions locate controls only: they never run, submit, or reveal an answer. */
export const helperTargets = {
  explanation: '[data-muxi-control="answer-explanation"]',
  code: '[data-muxi-control="code-input"], [data-muxi-control="code-open"]',
  "run-code": '[data-muxi-control="code-execute"]',
  circuit: '[data-muxi-control="circuit-expand"], [data-muxi-control="circuit-open"]',
  feedback: "#feedback",
} as const;

/** Fixed local destinations; never build a URL from conversational text. */
export const helperDestinations = {
  learn: "/?view=learn&nav=1",
  library: "/?view=library&nav=1",
  interview: "/?view=interview&nav=1",
  games: "/games",
  shop: "/games/shop",
} as const;

export type HelperAction =
  | { type: "support"; category: SupportCategory }
  | { type: "inbox" }
  | { type: "tour" }
  | { type: "focus"; target: keyof typeof helperTargets }
  | { type: "navigate"; destination: keyof typeof helperDestinations };
export type HelperChoice =
  | { label: HelperText; topic: HelperTopicId; action?: never }
  | { label: HelperText; action: HelperAction; topic?: never };
export type HelperTopic = {
  title: HelperText;
  messages: readonly HelperText[];
  choices: readonly HelperChoice[];
};

const text = (he: string, en: string): HelperText => ({ he, en });
const topic = (he: string, en: string, id: HelperTopicId): HelperChoice => ({ label: text(he, en), topic: id });
const action = (he: string, en: string, value: HelperAction): HelperChoice => ({ label: text(he, en), action: value });

/** Authored guidance about the site's tools, without reading or grading a user's answer. */
export const helperTopics: Readonly<Record<HelperTopicId, HelperTopic>> = {
  root: {
    title: text("במה אפשר לעזור?", "How can I help?"),
    messages: [text("היי! אפשר להכיר כאן את כלי התרגול, למצוא את הצעד הבא או לפתוח פנייה לצוות. מאיפה נתחיל?", "Hi! I can walk you through the practice tools, help you find your next step, or open a request for the team. Where shall we start?")],
    choices: [
      topic("להכיר את האתר", "Find my way around", "getting-started"),
      topic("עזרה בכלי התרגול", "Help with practice tools", "practice"),
      topic("פתיחת פנייה", "Contact the team", "support"),
      topic("הדמות שלי והמשחקים", "My character and games", "avatar"),
      topic("קיצורים שימושיים", "Useful shortcuts", "shortcuts"),
    ],
  },
  "getting-started": {
    title: text("נכיר את האתר", "Find your way around"),
    messages: [text("אפשר להתחיל מהאזור האישי, לחפש שאלה במאגר או להתנסות בסיור. הסיור נותן מקום לנסות את הכלים על דוגמאות.", "Start in your personal area, find a question in the library, or try a tour. The tour gives you examples to experiment with.")],
    choices: [topic("מה יש בכל אזור?", "What is in each area?", "site-map"), topic("איך מוצאים שאלה?", "How do I find a question?", "library"), topic("אני רוצה הדגמה", "Show me a demonstration", "tour")],
  },
  "site-map": {
    title: text("כל אזור והתפקיד שלו", "What each area is for"),
    messages: [text("באזור האישי מגדירים יעד וחוזרים לתרגול. במאגר בוחרים שאלות לפי מה שרוצים לחזק. בראיון מדומה מתרגלים כמה שאלות עם זמן מוגדר ודוח בסיום.", "Set a goal and return to practice in your personal area. Choose what to work on in the library. A mock interview gives you a timed session and a report at the end.")],
    choices: [action("לאזור האישי", "Open personal area", { type: "navigate", destination: "learn" }), action("למאגר השאלות", "Open question library", { type: "navigate", destination: "library" }), topic("איך עובד ראיון מדומה?", "How does a mock interview work?", "interview")],
  },
  library: {
    title: text("מוצאים שאלה שמתאימה לכם", "Find a question to work on"),
    messages: [text("במאגר אפשר לחפש לפי נושא, מונח מקצועי או חברה, ולהשתמש במסננים. אפשר גם לשמור שאלות לחזרה ולסנן לפי סטטוס התרגול.", "Search the library by subject, technical term or company, then narrow the results with filters. You can also bookmark questions and filter by practice status.")],
    choices: [action("פתיחת המאגר", "Open the library", { type: "navigate", destination: "library" }), topic("מה עושים אחרי בחירת שאלה?", "What happens after choosing a question?", "practice")],
  },
  tour: {
    title: text("ללמוד תוך כדי התנסות", "Learn by trying"),
    messages: [text("בסיור עם מוקסי אפשר לנסות כתיבה וקוד, מעגלים, רמזים ועוד. דוגמאות הסיור נפרדות מהתרגול האישי, ואפשר לצאת בכל רגע.", "Tour with Muxi to try writing, code, circuits, hints and more. Tour examples are separate from your personal practice, and you can leave at any time.")],
    choices: [action("פתיחת סיור עם מוקסי", "Open Tour with Muxi", { type: "tour" }), topic("עדיף הסבר על כלי מסוים", "Explain a specific tool instead", "practice")],
  },
  practice: {
    title: text("נמצא דרך נוחה לפתור", "Find a comfortable way to solve"),
    messages: [text("אפשר לשלב הסבר, קוד, שרטוט ותמונות באותה תשובה. במה תרצו להתמקד עכשיו?", "You can combine reasoning, code, diagrams and images in one answer. What would you like to focus on?")],
    choices: [topic("לנסח את דרך הפתרון", "Explain my reasoning", "explanation"), topic("לפתור שאלת תוכנה", "Solve a software question", "software"), topic("לפתור שאלת חומרה", "Solve a hardware question", "hardware"), topic("להתכונן לראיון מדומה", "Prepare for a mock interview", "interview")],
  },
  explanation: {
    title: text("הסבר במילים שלכם", "Explain it in your own words"),
    messages: [text("בשדה ״הסבר ודרך הפתרון״ כדאי להתחיל מהרעיון, לציין הנחות, לתאר את הצעדים ולסיים במקרי הקצה שבדקתם. אפשר לכתוב בעברית או באנגלית.", "In “Explanation and reasoning”, start with your idea, state your assumptions, describe the steps, and finish with the edge cases you checked. Write in Hebrew or English."), text("לא צריך לחזור על כל שורת קוד. נסו להסביר למה בחרתם בדרך הזאת ואיך היא עונה לדרישות השאלה.", "You do not need to repeat every line of code. Explain why you chose this approach and how it meets the question's requirements.")],
    choices: [action("איפה כותבים את ההסבר?", "Show me the explanation field", { type: "focus", target: "explanation" }), topic("אפשר להסביר בקול?", "Can I dictate my explanation?", "dictation"), topic("מה קורה אחרי השליחה?", "What happens after submitting?", "feedback")],
  },
  dictation: {
    title: text("מדברים, ואז עורכים", "Speak, then edit"),
    messages: [text("ליד ההסבר יש אפשרות להכתבה קולית, אם הדפדפן תומך בה. בוחרים שפת הכתבה, מפעילים את המיקרופון ועוצרים כשמסיימים. הטקסט נוסף להסבר ואפשר לתקן אותו לפני השליחה.", "Voice dictation appears beside the explanation when your browser supports it. Choose a dictation language, start the microphone, then stop when you finish. The text is added to your explanation and can be edited before submitting."), text("אם ההכתבה אינה זמינה, אפשר להקליד או להשתמש במיקרופון שבמקלדת הטלפון. הכתבה לא שולחת את התשובה אוטומטית.", "If dictation is unavailable, type or use your phone keyboard's microphone. Dictation does not submit your answer automatically.")],
    choices: [action("להגיע לאזור ההסבר", "Find the explanation area", { type: "focus", target: "explanation" }), topic("טיפים לניסוח ההסבר", "Tips for explaining my approach", "explanation")],
  },
  software: {
    title: text("מהרעיון לקוד", "From an idea to code"),
    messages: [text("לפני הקוד, הגדירו קלט, פלט ומקרה קצה אחד. כתבו את הרעיון בהסבר, ואז עברו לעורך הקוד. כדאי לבדוק גם דוגמה רגילה וגם מקרה גבול.", "Before coding, define the input, output and one edge case. Write your approach in the explanation, then move to the code editor. Check both a typical example and a boundary case.")],
    choices: [topic("איך מתחילים בעורך?", "How do I start in the editor?", "code-start"), topic("איך מריצים ובודקים?", "How do I run and test?", "code-run"), topic("רמזים, פתרון ומשוב", "Hints, references and feedback", "feedback")],
  },
  "code-start": {
    title: text("פותחים את עורך הקוד", "Open the code editor"),
    messages: [text("לחצו על ״הוספת קוד, נוסחה או טבלת אמת״ ובחרו שפה. יש C, C++, Python, JavaScript ושפות HDL, וגם מצב טקסט לנוסחאות ופסאודו־קוד. אם לשאלה יש קוד התחלתי, אפשר להעתיק אותו לעורך.", "Choose “Add code, a formula, or a truth table” and select a language. The editor supports C, C++, Python, JavaScript, HDL and plain text for formulas or pseudocode. If the question includes starter code, you can copy it into the editor."), text("Ctrl+Space פותח הצעות השלמה. כדי לצאת מהעורך במקלדת, לחצו Esc ואז Tab. ההסבר והקוד נשמרים יחד כחלק מהתשובה.", "Ctrl+Space opens completions. Press Esc, then Tab to leave the editor using the keyboard. Reasoning and code are saved together as part of your answer.")],
    choices: [action("להראות לי את עורך הקוד", "Show me the code editor", { type: "focus", target: "code" }), topic("עכשיו לבדוק את הקוד", "Now test the code", "code-run")],
  },
  "code-run": {
    title: text("מריצים לפני שמגישים", "Run before submitting"),
    messages: [text("כשהרצה זמינה לשאלה ולשפה שבחרתם, יופיע כפתור הרצה מתחת לעורך. אם יש בדיקות מוכנות, מופיע גם הממשק שהקוד צריך לממש. אחרת אפשר להריץ תוכנית מלאה או testbench משלכם.", "When execution is available for your question and language, a run button appears below the editor. Prepared tests show the interface your code must implement. Otherwise, you can run a complete program or your own testbench."), text("הרצה לא מגישה את התשובה. בדקו את הפלט והשגיאות; הרצה מוצלחת לבדה לא מבטיחה שהפתרון עומד בכל הדרישות.", "Running does not submit your answer. Review the output and errors; a successful run alone does not guarantee that every requirement is met.")],
    choices: [action("איפה כפתור ההרצה?", "Show me the run button", { type: "focus", target: "run-code" }), topic("ההרצה לא עובדת", "Execution is not working", "support-bug"), topic("בחזרה לכלי התוכנה", "Back to software tools", "software")],
  },
  hardware: {
    title: text("מדרישות למעגל", "From requirements to a circuit"),
    messages: [text("התחילו מהכניסות, הפלטים ורוחב האותות. אחר כך בחרו איך לתאר את הפתרון: הסבר, שרטוט מעגל, קוד HDL או תמונה של פתרון בכתב יד.", "Start with inputs, outputs and signal widths. Then choose how to express your solution: reasoning, a circuit drawing, HDL code or an image of handwritten work.")],
    choices: [topic("לבנות ולחבר מעגל", "Build and wire a circuit", "circuit-build"), topic("לבדוק את ההתנהגות שלו", "Check how it behaves", "circuit-check"), action("להגיע לעורך בשביל HDL", "Find the editor for HDL", { type: "focus", target: "code" }), topic("רמזים, פתרון ומשוב", "Hints, references and feedback", "feedback")],
  },
  "circuit-build": {
    title: text("בונים את השרטוט", "Build your drawing"),
    messages: [text("בחרו ״שרטוט מעגל לוגי״ באזור התשובה. הוסיפו רכיבים וחברו בין הפינים בגרירה, או השתמשו ברשימות החיבור שמתחת ללוח. בחירת רכיב פותחת את ההגדרות שלו.", "Choose “Draw a logic circuit” in the answer area. Add components and drag between pins, or use the connection lists below the canvas. Select a component to see its settings."), text("״הרחבת הלוח״ מפנה מקום לעבודה. אפשר לבטל שינוי, ולהוריד עותק של השרטוט. אם נוח יותר לעבוד על נייר, אפשר לצרף תמונת פתרון באזור התשובה.", "“Expand drawing” gives you more working space. You can undo changes and download a copy of the circuit. If paper works better for you, attach an answer image in the answer area.")],
    choices: [action("להראות לי את אזור השרטוט", "Show me the drawing area", { type: "focus", target: "circuit" }), topic("איך בודקים את המעגל?", "How do I check the circuit?", "circuit-check")],
  },
  "circuit-check": {
    title: text("בודקים יותר מצירוף אחד", "Check more than one input"),
    messages: [text("הפעילו סימולציה, בחרו כניסת INPUT ושנו את הערך שלה. סימן שאלה מסמן ערך לא ידוע או חיבור חסר. במעגל צירופי תקין אפשר ליצור טבלת אמת עד שישה ביטים משתנים.", "Start simulation, select an INPUT and change its value. A question mark means an unknown value or missing connection. Valid combinational circuits support truth tables with up to six variable bits."), text("למעגל עם זיכרון בדקו גם צעד שעון ואיפוס. זו סימולציה לוגית בלי השהיות פיזיות; השוו את ההתנהגות לדרישות השאלה, גם כשהסימולציה רצה בלי שגיאה.", "For a circuit with memory, check clock steps and reset too. This is logic simulation without physical delays; compare its behavior with the question's requirements even when it runs without errors.")],
    choices: [action("להגיע לכלי המעגל", "Find the circuit tools", { type: "focus", target: "circuit" }), topic("עדיף להתנסות בדוגמה", "I'd like to try an example", "tour"), topic("בחזרה לכלי החומרה", "Back to hardware tools", "hardware")],
  },
  feedback: {
    title: text("להיעזר, ואז לבדוק מה למדתם", "Get help and review what you learned"),
    messages: [text("אם נתקעים, אפשר לפתוח רמז בהדרגה או לבחור לחשוף פתרון מוצע. הסיוע נרשם עם הניסיון, כדי להבחין בין פתרון עצמאי לתרגול עם עזרה.", "If you get stuck, reveal a hint at a time or choose to open the reference solution. Assistance is recorded with the attempt so independent work can be distinguished from supported practice."), text("אחרי השליחה, עברו על התשובה שנשמרה ועל המשוב הזמין. כדאי להשוות לפתרון המוצע ולבחור נקודה אחת לשיפור. אם ההערכה עדיין בהכנה או אינה זמינה, האתר מציין זאת.", "After submitting, review your saved answer and any available feedback. Compare it with the reference and choose one thing to improve. The site indicates when assessment is pending or unavailable.")],
    choices: [action("איפה אזור המשוב?", "Show me the feedback area", { type: "focus", target: "feedback" }), topic("לשפר את ההסבר שלי", "Improve my explanation", "explanation"), topic("יש בעיה בשאלה או בפתרון", "There is a question or solution issue", "support-question")],
  },
  interview: {
    title: text("מתכוננים לראיון מדומה", "Prepare for a mock interview"),
    messages: [text("בוחרים 20, 30 או 45 דקות, ועונים על שאלה אחת בכל פעם. זה ראיון בכתב: אפשר לשלב הסבר, קוד, שרטוטים ותמונות. אין צורך בשיחה קולית.", "Choose 20, 30 or 45 minutes and answer one question at a time. This is a written interview: combine reasoning, code, diagrams and images. No voice call is needed."), text("אפשר לבקש רמז, והשימוש בו נרשם. המשוב מופיע בדוח בסיום; אפשר גם לסיים מוקדם. הקיצור כאן פותח את מסך ההכנה, כדי שתבחרו מתי להתחיל.", "You can request hints, and their use is recorded. Feedback appears in the final report; you can finish early too. This shortcut opens setup so you choose when to start.")],
    choices: [action("למסך הכנת הראיון", "Open interview setup", { type: "navigate", destination: "interview" }), topic("לנסות קודם בסיור", "Try it in the tour first", "tour")],
  },
  support: {
    title: text("נפתח פנייה לצוות", "Contact the team"),
    messages: [text("בשמחה. במה מדובר? אחרי הבחירה תוכלו להוסיף פרטים וקבצים בחלון הפנייה, ולשלוח כשתהיו מוכנים.", "Of course. What is this about? After choosing, you can add details and files in the request window, then send when you're ready.")],
    choices: [topic("תקלה באתר", "Something is broken", "support-bug"), topic("בעיה בשאלה או בפתרון", "A question or solution", "support-question"), topic("הצעה לשיפור", "An improvement idea", "support-feedback"), topic("משהו אחר", "Something else", "support-other")],
  },
  "support-bug": {
    title: text("משהו באתר לא עבד", "Something did not work"),
    messages: [text("כדאי לתאר מה ניסיתם לעשות, מה ציפיתם שיקרה ומה קרה בפועל. צילום מסך יכול לעזור. נפתח את הטופס בסוג ״תקלה באתר״; תוכלו לבדוק הכול לפני השליחה.", "Describe what you tried, what you expected, and what happened instead. A screenshot can help. Open the form with “Something is broken” selected, then review it before sending.")],
    choices: [action("פתיחת דיווח על תקלה", "Open a bug report", { type: "support", category: "bug" }), topic("לבחור סוג אחר", "Choose another request type", "support")],
  },
  "support-question": {
    title: text("נבדוק את השאלה או הפתרון", "Report a question or solution issue"),
    messages: [text("ציינו איזו שאלה ואיזה חלק לא ברור או נראה שגוי. אם יש מקרה קצה או דוגמה שסותרים את הפתרון, כדאי להוסיף אותם. אפשר לצרף גם צילום של החלק הרלוונטי.", "Name the question and the part that seems unclear or incorrect. Add an edge case or counterexample if you have one. You can also attach an image of the relevant section.")],
    choices: [action("פתיחת פנייה על שאלה", "Open a question report", { type: "support", category: "question" }), topic("לבחור סוג אחר", "Choose another request type", "support")],
  },
  "support-feedback": {
    title: text("יש רעיון לשיפור?", "Have an improvement in mind?"),
    messages: [text("ספרו מה הייתם רוצים לעשות ומה חסר היום. דוגמה קצרה לרגע שבו השיפור יעזור תעזור לצוות להבין את הצורך.", "Tell us what you would like to do and what is missing today. A short example of when the improvement would help gives the team useful context.")],
    choices: [action("פתיחת הצעה לשיפור", "Open an improvement request", { type: "support", category: "feedback" }), topic("לבחור סוג אחר", "Choose another request type", "support")],
  },
  "support-other": {
    title: text("אפשר לפנות גם על משהו אחר", "Other questions are welcome too"),
    messages: [text("אין צורך למצוא קטגוריה מדויקת. כתבו כותרת קצרה ותארו במה תרצו עזרה. תשובות מהצוות מופיעות באזור ״עדכונים ופניות״.", "You do not need a perfect category. Give the request a short subject and explain what you need help with. Replies from the team appear in Updates & requests.")],
    choices: [action("פתיחת פנייה אחרת", "Open another request", { type: "support", category: "other" }), action("לראות את הפניות שלי", "View my requests", { type: "inbox" })],
  },
  avatar: {
    title: text("הדמות שלכם באתר", "Your character around the site"),
    messages: [text("בחנות של מוקסי אפשר להתאים את מראה הדמות ולבחור פריטים. באזור המשחקים אפשר לעבור לאתגרים. לאן תרצו להגיע?", "Customize your character and choose items in Muxi's shop, or head to Games for a challenge. Where would you like to go?")],
    choices: [topic("איך משנים את הדמות?", "How do I change my character?", "shop"), topic("מה עושים במשחקים?", "What can I do in Games?", "games"), action("לאזור האישי שלי", "Open my personal area", { type: "navigate", destination: "learn" })],
  },
  games: {
    title: text("קופצים למשחקים", "Head to Games"),
    messages: [text("באזור המשחקים אפשר לפתוח אתגר, להצטרף עם קוד הזמנה ולחזור למשחקים קיימים. לפני יצירת משחק, בדקו את הכללים ואת עלות המטבעות שמוצגת בו.", "In Games, create a challenge, join with an invitation code, or return to existing games. Before creating one, review its rules and displayed coin cost.")],
    choices: [action("פתיחת אזור המשחקים", "Open Games", { type: "navigate", destination: "games" }), topic("לעיצוב הדמות שלי", "Customize my character", "shop")],
  },
  shop: {
    title: text("בוחרים מראה לדמות", "Choose your character's look"),
    messages: [text("בחנות אפשר לבחור רכיב, צבע וחולצה, לראות איך הם נראים על הדמות ולשמור את הבחירה. פריטים לקנייה מציגים מחיר במטבעות; אפשר לבדוק את המראה לפני שבוחרים לרכוש.", "In the shop, choose a component, color and shirt, preview them on your character, and save your selection. Purchasable items show their coin price; preview the look before deciding to buy.")],
    choices: [action("פתיחת החנות של מוקסי", "Open Muxi's shop", { type: "navigate", destination: "shop" }), topic("בחזרה לדמות ולמשחקים", "Back to my character and games", "avatar")],
  },
  shortcuts: {
    title: text("לאן תרצו להגיע?", "Where would you like to go?"),
    messages: [text("הנה כמה קיצורים לפעולות שימושיות. פניות ותשובות מהצוות נמצאות ב״עדכונים ופניות״.", "Here are a few useful shortcuts. Find your requests and the team's replies in Updates & requests.")],
    choices: [action("עדכונים ופניות שלי", "My updates and requests", { type: "inbox" }), action("סיור עם מוקסי", "Tour with Muxi", { type: "tour" }), action("מאגר השאלות", "Question library", { type: "navigate", destination: "library" }), action("האזור האישי", "Personal area", { type: "navigate", destination: "learn" })],
  },
};
