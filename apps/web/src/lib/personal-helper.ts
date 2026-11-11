import type { SupportCategory } from "./support-report";

export type HelperText = { he: string; en: string };
export type HelperTopicId =
  | "root" | "getting-started" | "site-map" | "personal-area" | "goal" | "daily-plan" | "profile" | "library" | "fundamentals" | "quick-quiz" | "question-actions" | "tour"
  | "practice" | "explanation" | "dictation" | "software" | "code-start" | "code-run"
  | "hardware" | "circuit-build" | "circuit-check" | "attachments" | "feedback" | "interview" | "interview-history"
  | "support" | "support-bug" | "support-question" | "support-feedback" | "support-other"
  | "avatar" | "games" | "friends" | "shop" | "shortcuts";

/** Focus actions locate controls only: they never run, submit, or reveal an answer. */
export const helperTargets = {
  explanation: '[data-muxi-control="explanation-open"], [data-muxi-control="answer-explanation"]',
  code: '[data-muxi-control="code-input"], [data-muxi-control="code-open"]',
  "run-code": '[data-muxi-control="code-execute"], [data-muxi-control="code-open"]',
  circuit: '[data-muxi-control="circuit-expand"], [data-muxi-control="circuit-open"]',
  photos: '[data-muxi-control="photos-open"], .visual-answer button[aria-controls$="-photos"]',
  goal: '[data-muxi-control="goal-edit"], .dashboard-edit-goal, [data-goal-summary] button',
  feedback: "#feedback",
} as const;

/** Fixed local destinations; never build a URL from conversational text. */
export const helperDestinations = {
  learn: "/?view=learn&nav=1",
  library: "/?view=library&nav=1",
  fundamentals: "/?view=fundamentals&nav=1",
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
    messages: [text("באזור האישי בוחרים יעד ומקבלים כיוון לתרגול. אפשר גם לבחור שאלה במאגר או לצאת לסיור עם מוקסי, שילווה אתכם בשימוש בכלים ובשאלות מהאתר.", "Set a goal in your personal area for a clearer practice direction. You can also choose a library question or let Muxi guide you through the site's tools and questions.")],
    choices: [topic("האזור האישי והיעד שלי", "My personal area and goal", "personal-area"), topic("מה יש בכל אזור?", "What is in each area?", "site-map"), topic("איך מוצאים שאלה?", "How do I find a question?", "library"), topic("להתנסות עם מוקסי", "Try it with Muxi", "tour")],
  },
  "site-map": {
    title: text("כל אזור והתפקיד שלו", "What each area is for"),
    messages: [text("האזור האישי מרכז המלצות ותוכנית לפי היעד שלכם. במאגר יש שאלות ראיונות ו״יסודות בקטנה״ לחזרה קצרה. בראיון מדומה מתרגלים ברצף ובזמן מוגדר, ומקבלים דוח בסיום.", "Your personal area brings together recommendations and a goal-based plan. The library offers interview questions and short fundamentals practice. A mock interview is a timed sequence with a report at the end."), text("במשחקים מתחרים עם חבר בשאלות אמריקאיות ומנהלים את רשימת החברים. בחנות של מוקסי מעצבים את הדמות ומוצאים סקינים. אני כאן כדי להסביר את הכלים ולפתוח פנייה לצוות כשצריך.", "In Games, compete with a friend on multiple-choice questions and manage your friends. Customize your character and find skins in Muxi's shop. I can explain the tools and help you open a request for the team.")],
    choices: [topic("האזור האישי", "Personal area", "personal-area"), topic("מאגר ותרגול קצר", "Library and short practice", "library"), topic("ראיון מדומה", "Mock interviews", "interview"), topic("משחקים, חברים והחנות", "Games, friends and the shop", "avatar")],
  },
  "personal-area": {
    title: text("בוחרים את הצעד הבא", "Choose your next step"),
    messages: [text("הגלים בראש האזור האישי מציעים שאלות לפי היעד והנושאים שכדאי לחזק. אפשר להתחיל מכל אחת מהן. אם פתחתם שאלה ועדיין לא עניתם עליה, ״שנמשיך מאיפה שעצרת?״ מחזיר אליה.", "The waves at the top of your personal area recommend questions for your goal and the topics to strengthen. Start with any of them. If you opened a question but have not answered it, “Continue where you left off?” takes you back."), text("מתחת נמצאת ״התוכנית להיום״. היעד השמור ו״הפרופיל שלי״ נמצאים בהמשך העמוד, וכפתור ״עריכת היעד״ זמין גם למעלה.", "“Today's practice plan” comes next. Your saved goal and “My profile” are farther down the page, with an “Edit goal” button at the top too.")],
    choices: [topic("להגדיר או לשנות יעד", "Set or change my goal", "goal"), topic("המלצות או תוכנית להיום?", "Recommendations or daily plan?", "daily-plan"), topic("הפרופיל והקוד שלי", "My profile and friend code", "profile"), action("לאזור האישי", "Open personal area", { type: "navigate", destination: "learn" })],
  },
  goal: {
    title: text("יעד שמתאים לכם", "A goal that fits you"),
    messages: [text("באזור האישי לחצו על ״להגדיר את היעד״ או ״עריכת היעד״. בחרו תפקיד אחד או כמה, את השלב שלכם בקריירה וכמה זמן תרצו ללמוד ביום. אפשר להוסיף תאריך לראיון, או ללמוד בלי יעד תעסוקתי קבוע.", "In your personal area, choose “Set my goal” or “Edit goal”. Select one or more roles, your career stage and daily study time. Add an interview date if you have one, or learn without a fixed job goal."), text("אחרי השמירה התוכנית וההמלצות מתעדכנות לפי הבחירות שלכם. אפשר לחזור לעריכת היעד בכל שלב. בסיור מוקסי מלווה אתכם גם בבחירה ובשמירה של היעד האישי.", "Saving updates your plan and recommendations to match your choices. You can edit your goal any time. Muxi's tour also guides you through choosing and saving your own goal.")],
    choices: [action("איפה עורכים את היעד?", "Show me Edit goal", { type: "focus", target: "goal" }), action("לאזור האישי", "Open personal area", { type: "navigate", destination: "learn" }), topic("להגדיר יעד עם מוקסי", "Set my goal with Muxi", "tour")],
  },
  "daily-plan": {
    title: text("בחירה חופשית לצד תוכנית יומית", "Recommendations and your daily plan"),
    messages: [text("כל גל הוא שאלה מסוימת שאפשר לפתוח מיד. אלה המלצות לבחירתכם, ואפשר להתחיל מכל גל. ״התוכנית להיום״ מסדרת שלבי תרגול לפי הנושאים והזמן שקבעתם, למשל תרגול קצר, תרגול מעמיק או ראיון מדומה.", "Each wave is a specific question you can open right away, and you may start with any wave. “Today's practice plan” organizes activities around your topics and available time, such as quick practice, deep practice or a mock interview."), text("לחצו על כפתור השלב בתוכנית כדי להתחיל או להמשיך אותו. ״בהמשך השבוע״ מציג את הפעילויות המתוכננות לימים הבאים.", "Use the current activity's button to start or resume it. “Later this week” shows activities planned for the coming days.")],
    choices: [action("להמלצות ולתוכנית שלי", "Open my recommendations and plan", { type: "navigate", destination: "learn" }), topic("לשנות את היעד או הזמן היומי", "Change my goal or daily time", "goal")],
  },
  profile: {
    title: text("השם והקוד שלכם", "Your name and friend code"),
    messages: [text("ב״הפרופיל שלי״ באזור האישי מופיעים שם המשתמש וקוד החברים האישי, בן 8 תווים. אפשר להעתיק את הקוד ולשלוח לחבר. אם עדיין לא בחרתם שם משתמש, אפשר לבחור אותו שם.", "“My profile” in your personal area shows your username and personal 8-character friend code. Copy the code to share it with a friend. If you have not chosen a username yet, you can choose it there.")],
    choices: [action("לפרופיל באזור האישי", "Open my personal area", { type: "navigate", destination: "learn" }), topic("איך מוסיפים חבר?", "How do I add a friend?", "friends")],
  },
  library: {
    title: text("מוצאים שאלה שמתאימה לכם", "Find a question to work on"),
    messages: [text("במאגר אפשר לחפש לפי נושא, מונח מקצועי או חברה, ולהשתמש במסננים. אפשר גם לשמור שאלות לחזרה ולסנן לפי סטטוס התרגול.", "Search the library by subject, technical term or company, then narrow the results with filters. You can also bookmark questions and filter by practice status.")],
    choices: [action("פתיחת מאגר שאלות הראיונות", "Open interview questions", { type: "navigate", destination: "library" }), topic("יסודות בקטנה ובוחן", "Short fundamentals and quizzes", "fundamentals"), topic("מה עושים אחרי בחירת שאלה?", "What happens after choosing a question?", "practice"), topic("דיווח בעיה או ראיתי בחברה", "Report an issue or a company sighting", "question-actions")],
  },
  fundamentals: {
    title: text("כמה דקות לחיזוק הבסיס", "A few minutes for the fundamentals"),
    messages: [text("ב״יסודות בקטנה״ בוחרים נושא או מחפשים שאלה קצרה. נסו לענות ואז פתחו את הפתרון לבדיקה עצמית. כפתור ״סיימתי, לשאלה הבאה״ שומר שסיימתם בחשבון ומעביר לשאלה הבאה.", "In short fundamentals practice, choose a topic or search for a short question. Try answering, then reveal the solution to check yourself. “Done, next question” records completion in your account and opens the next question."), text("פתיחת פתרון או דילוג אינם מסמנים שסיימתם. אפשר לסנן שאלות שכבר סיימתם או להכין בוחן של 10 שאלות בנושאים לבחירתכם.", "Revealing a solution or skipping does not mark a question done. Filter finished questions or create a 10-question quiz on your chosen topics.")],
    choices: [action("פתיחת יסודות בקטנה", "Open short fundamentals", { type: "navigate", destination: "fundamentals" }), topic("איך יוצרים בוחן?", "How do I create a quiz?", "quick-quiz"), topic("לתרגול עם כלי תשובה ומשוב", "Practice with answer tools and feedback", "practice")],
  },
  "quick-quiz": {
    title: text("בוחן לפי הנושאים שלכם", "A quiz on your topics"),
    messages: [text("ב״יסודות בקטנה״ לחצו על ״בוחן״. סמנו את הנושאים שתרצו לתרגל, או ״בחר הכול״, ואז צרו בוחן. האתר מגריל 10 שאלות שונות מכל הנושאים שבחרתם ומציג אותן באותו עמוד.", "In short fundamentals practice, choose “Quiz”. Check the topics you want, or “Select all”, then create the quiz. The site draws 10 different questions from those topics and displays them on one page."), text("עונים בקצב שלכם ופותחים כל פתרון כשמוכנים לבדוק את עצמכם. זה בוחן לתרגול עצמי עם פתרונות, ללא ציון AI.", "Work at your own pace and open each solution when you are ready to check it. This is a self-study quiz with solutions and no AI grade.")],
    choices: [action("ליסודות בקטנה ולבוחן", "Open short fundamentals and quizzes", { type: "navigate", destination: "fundamentals" }), topic("בחזרה לשאלות הקצרות", "Back to short-question guidance", "fundamentals")],
  },
  "question-actions": {
    title: text("עוזרים לשפר את השאלות", "Help improve the questions"),
    messages: [text("במסגרת ״על השאלה הזאת״ יש ״דיווח בעיה״, ״שאלה לא ברורה״ ו״ראיתי בחברה״. השתמשו בפעולה המתאימה ליד השאלה כדי שהפנייה תהיה קשורה אליה. אם ראיתם אותה בראיון, בחרו את החברה ודווחו.", "The “About this question” bar contains “Report a problem”, “Question unclear” and “Seen at a company”. Use the action beside the question to keep your report connected to it. If you encountered it in an interview, select the company and report it.")],
    choices: [topic("יש בעיה בשאלה או בפתרון", "A question or solution issue", "support-question"), action("פתיחת המאגר", "Open the library", { type: "navigate", destination: "library" })],
  },
  tour: {
    title: text("ללמוד תוך כדי התנסות", "Learn by trying"),
    messages: [text("מוקסי מלווה אתכם בהגדרת היעד ובהיכרות עם האזור האישי, המאגר, כלי התשובה, המשחקים, החנות והראיון המדומה. הסיור בתוך החשבון משתמש בשאלות ובכלים של האתר, ושמירה או שליחה שתבחרו לבצע נשמרות בחשבון שלכם.", "Muxi guides you through setting your goal, your personal area, the library, answer tools, Games, the shop and mock interviews. The signed-in tour uses the site's questions and tools. Saves and submissions you choose to make are recorded in your account.")],
    choices: [action("פתיחת סיור עם מוקסי", "Open Tour with Muxi", { type: "tour" }), topic("עדיף הסבר על כלי מסוים", "Explain a specific tool instead", "practice")],
  },
  practice: {
    title: text("נמצא דרך נוחה לפתור", "Find a comfortable way to solve"),
    messages: [text("כל כלי התשובה מתחיל מקופל. פתחו בכפתור את מה שמתאים לכם, הסבר, קוד, מעגל או תמונות, ושלבו אותם באותה תשובה. קיפול הכלי שומר את התוכן שכבר כתבתם.", "Answer tools start collapsed. Use their buttons to open the explanation, code, circuit or images you need and combine them in one answer. Collapsing a tool keeps the content you entered.")],
    choices: [topic("לנסח את דרך הפתרון", "Explain my reasoning", "explanation"), topic("לפתור שאלת תוכנה", "Solve a software question", "software"), topic("לפתור שאלת חומרה", "Solve a hardware question", "hardware"), topic("לצרף תמונת פתרון", "Attach an answer image", "attachments")],
  },
  explanation: {
    title: text("הסבר במילים שלכם", "Explain it in your own words"),
    messages: [text("לחצו על ״כתיבת הסבר לפתרון״. התחילו מהרעיון, ציינו הנחות, תארו את הצעדים וסיימו במקרי הקצה שבדקתם. אפשר לכתוב בעברית או באנגלית.", "Choose “Write an explanation”. Start with your idea, state your assumptions, describe the steps and finish with the edge cases you checked. Write in Hebrew or English."), text("לא צריך לחזור על כל שורת קוד. נסו להסביר למה בחרתם בדרך הזאת ואיך היא עונה לדרישות השאלה.", "You do not need to repeat every line of code. Explain why you chose this approach and how it meets the question's requirements.")],
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
    messages: [text("לחצו על ״קוד, נוסחה או טבלת אמת״ ובחרו שפה. יש C, C++, Python, JavaScript ושפות HDL, וגם מצב טקסט לנוסחאות ופסאודו־קוד. אם לשאלה יש קוד התחלתי, אפשר להעתיק אותו לעורך.", "Choose “Code, formula, or truth table” and select a language. The editor supports C, C++, Python, JavaScript, HDL and plain text for formulas or pseudocode. If the question includes starter code, you can copy it into the editor."), text("Ctrl+Space פותח הצעות השלמה. כדי לצאת מהעורך במקלדת, לחצו Esc ואז Tab. ההסבר והקוד נשמרים יחד כחלק מהתשובה.", "Ctrl+Space opens completions. Press Esc, then Tab to leave the editor using the keyboard. Reasoning and code are saved together as part of your answer.")],
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
    messages: [text("בחרו כניסת INPUT ושנו את הערך שלה. במעגל צירופי תראו מיד את התוצאה על הרכיבים והחוטים. סימן שאלה מסמן ערך לא ידוע או חיבור חסר. במעגל צירופי תקין אפשר ליצור טבלת אמת עד שישה ביטים משתנים.", "Select an INPUT and change its value. A combinational circuit shows the result immediately on its components and wires. A question mark means an unknown value or missing connection. Valid combinational circuits support truth tables with up to six variable bits."), text("אם הוספתם פליפ-פלופ, רגיסטר או מונה, לחצו על „הרצת סימולציה” ובדקו צעד שעון ואיפוס. זו סימולציה לוגית בלי השהיות פיזיות; השוו את ההתנהגות לדרישות השאלה, גם כשהסימולציה רצה בלי שגיאה.", "If your circuit contains a flip-flop, register or counter, choose Run simulation to test clock steps and reset. This is logic simulation without physical delays; compare its behavior with the question's requirements even when it runs without errors.")],
    choices: [action("להגיע לכלי המעגל", "Find the circuit tools", { type: "focus", target: "circuit" }), topic("עדיף להתנסות בדוגמה", "I'd like to try an example", "tour"), topic("בחזרה לכלי החומרה", "Back to hardware tools", "hardware")],
  },
  attachments: {
    title: text("גם פתרון על נייר יכול להצטרף", "Include work from paper"),
    messages: [text("לחצו על ״צירוף תמונות פתרון״, ואז על ״בחירת תמונות מהמכשיר״. אפשר לצרף עד 4 תמונות בפורמט JPG, PNG או WebP, עד 10 מגה־בייט לתמונה לפני התאמה.", "Choose “Attach answer images”, then “Choose images from your device”. Attach up to 4 JPG, PNG or WebP images, up to 10 MB each before resizing."), text("צלמו כך שהכתב והשרטוט יהיו קריאים ובדקו את התצוגה לפני השליחה. אפשר לשלב תמונות עם הסבר, קוד ומעגל, וגם להסיר תמונה שלא התכוונתם לצרף.", "Make sure the writing and drawing are readable, then check the preview before submitting. Combine images with reasoning, code and a circuit, or remove an image you did not mean to attach.")],
    choices: [action("איפה מצרפים תמונות?", "Show me answer images", { type: "focus", target: "photos" }), topic("להוסיף הסבר לתמונה", "Add reasoning to my image", "explanation")],
  },
  feedback: {
    title: text("להיעזר, ואז לבדוק מה למדתם", "Get help and review what you learned"),
    messages: [text("אפשר לפתוח רמז בהדרגה או לחשוף פתרון מוצע, והשימוש בסיוע נרשם עם הניסיון. כששולחים תשובה ראשית לקבלת משוב והיא נקלטת, השאלה מסומנת אוטומטית ״בוצעה״. הסימון מציין שעניתם, ולא שהפתרון נכון.", "Reveal hints one at a time or open the reference solution. Assistance is recorded with the attempt. When your main answer is accepted for AI feedback, the question is automatically marked “Done”. This records that you answered, not that the solution is correct."), text("כשהמשוב מוכן האתר מעביר אתכם אליו. תראו מה היה טוב, מה חסר וטיפ להמשך, ולעיתים גם שאלת המשך. אפשר להשוות לפתרון המוצע. אם המשוב עדיין בהכנה או לא זמין, האתר מציין זאת.", "When feedback is ready, the site brings it into view. Review what worked, what was missing and the next-step tip, and sometimes a follow-up question. You can compare with the reference solution. Pending or unavailable feedback is clearly indicated.")],
    choices: [action("איפה אזור המשוב?", "Show me the feedback area", { type: "focus", target: "feedback" }), topic("לשפר את ההסבר שלי", "Improve my explanation", "explanation"), topic("יש בעיה בשאלה או בפתרון", "There is a question or solution issue", "support-question")],
  },
  interview: {
    title: text("מתכוננים לראיון מדומה", "Prepare for a mock interview"),
    messages: [text("בוחרים 20, 30 או 45 דקות, ועונים על שאלה אחת בכל פעם. זה ראיון בכתב: אפשר לשלב הסבר, קוד, שרטוטים ותמונות. אין צורך בשיחה קולית.", "Choose 20, 30 or 45 minutes and answer one question at a time. This is a written interview: combine reasoning, code, diagrams and images. No voice call is needed."), text("אפשר לבקש רמז, והשימוש בו נרשם. המשוב מופיע בדוח בסיום; אפשר גם לסיים מוקדם. הקיצור כאן פותח את מסך ההכנה, כדי שתבחרו מתי להתחיל.", "You can request hints, and their use is recorded. Feedback appears in the final report; you can finish early too. This shortcut opens setup so you choose when to start.")],
    choices: [action("למסך הכנת הראיון", "Open interview setup", { type: "navigate", destination: "interview" }), topic("הראיונות הקודמים שלי", "My past interviews", "interview-history"), topic("להכיר את הראיון עם מוקסי", "Explore interviews with Muxi", "tour")],
  },
  "interview-history": {
    title: text("חוזרים לדוחות קודמים", "Return to past reports"),
    messages: [text("במסך ״ראיון מדומה״, מתחת לבחירת הזמן, נמצאת רשימת ״ראיונות קודמים״. פתחו ראיון כדי לראות את הדוח והשאלות שלו. ליד כל פריט יש כפתור מחיקה אם אינכם רוצים שיישאר ברשימה.", "On the mock-interview setup page, find “Previous interviews” below the duration choices. Open an interview to review its report and questions. Each item has a delete button if you no longer want it in the list.")],
    choices: [action("לראיונות הקודמים שלי", "Open my previous interviews", { type: "navigate", destination: "interview" }), topic("איך מתחילים ראיון חדש?", "How do I start a new interview?", "interview")],
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
    choices: [topic("איך משנים את הדמות?", "How do I change my character?", "shop"), topic("מה עושים במשחקים?", "What can I do in Games?", "games"), topic("להוסיף חברים", "Add friends", "friends"), topic("הפרופיל והקוד שלי", "My profile and friend code", "profile")],
  },
  games: {
    title: text("קופצים למשחקים", "Head to Games"),
    messages: [text("באזור המשחקים אפשר גם לנסות לבד שאלה מהמאגר האמיתי של השאלות האמריקאיות, לבדוק את התשובה ולקבל הסבר, בלי להוציא מטבעות. בדו־קרב שני חברים עונים על אותן חמש שאלות אמריקאיות. יוצרים הזמנה או מצטרפים עם קוד משחק, והשעון מתחיל רק אחרי ששניכם מוכנים. בסיום אפשר לחזור לשאלות ולהסברים.", "In Games, you can also try a question on your own from the real multiple-choice bank, check your answer and read the explanation without spending coins. In a duel, two friends answer the same five multiple-choice questions. Create an invitation or join with a game code. The clock starts only when both players are ready. Review the questions and explanations at the end."), text("לפני יצירת המשחק או ההצטרפות, בדקו את עלות המטבעות והכללים המוצגים. ״המשחקים שלי״ מחזיר למשחקים קיימים. קוד המשחק שונה מקוד החברים האישי שלכם.", "Before creating or joining a game, review the displayed coin cost and rules. “My games” takes you back to existing games. A game invitation code is different from your personal friend code.")],
    choices: [action("פתיחת אזור המשחקים", "Open Games", { type: "navigate", destination: "games" }), topic("להוסיף חבר לפי קוד", "Add a friend by code", "friends"), topic("לעיצוב הדמות שלי", "Customize my character", "shop")],
  },
  friends: {
    title: text("מוסיפים חבר לפי הקוד שלו", "Add a friend using their code"),
    messages: [text("באזור המשחקים, תחת ״חברים״, הזינו את קוד החברים בן 8 התווים ובחרו ״שליחת בקשת חברות״. אחרי שהחבר מאשר, הוא מופיע ברשימה עם הדמות ושם המשתמש שלו. בקשות שקיבלתם או שלחתם מופיעות באותו אזור.", "Under “Friends” in Games, enter your friend's 8-character friend code and choose “Send friend request”. After they accept, they appear with their character and username. Incoming and sent requests appear in the same area."), text("את הקוד שלכם אפשר להעתיק משם או מ״הפרופיל שלי״ באזור האישי. אם עוד אין לכם שם משתמש, בחרו אותו בפרופיל לפני שליחה או אישור של בקשת חברות.", "Copy your own code there or from “My profile” in your personal area. If you do not yet have a username, choose one in your profile before sending or accepting a friend request.")],
    choices: [action("לחברים באזור המשחקים", "Open Games and friends", { type: "navigate", destination: "games" }), topic("איפה הקוד האישי שלי?", "Where is my personal code?", "profile")],
  },
  shop: {
    title: text("בוחרים מראה לדמות", "Choose your character's look"),
    messages: [text("הרכיב והצבע של הדמות חינמיים. בחנות בוחרים חולצה כדי למדוד אותה ולראות את ההדפס, ופריטים לקנייה מציגים מחיר במטבעות. המדידה לא קונה את הפריט.", "Your character's component and color are free. Choose a shirt to try it on and inspect the print. Purchasable items show their coin price. Trying an item on does not buy it."), text("אחרי רכישת סקין הוא נוסף ל״ארון שלי״. בחרו ״ללבוש ולשמור״ כדי להחיל את המראה, או ״לשמור את הדמות״ אחרי שינוי הרכיב והצבע. הדמות השמורה מופיעה גם במשחקים ובעוזר האישי.", "After buying a skin, find it in “My wardrobe”. Choose “Wear and save” to apply the look, or “Save character” after changing the component and color. Your saved character also appears in Games and the personal helper.")],
    choices: [action("פתיחת החנות של מוקסי", "Open Muxi's shop", { type: "navigate", destination: "shop" }), topic("בחזרה לדמות ולמשחקים", "Back to my character and games", "avatar")],
  },
  shortcuts: {
    title: text("לאן תרצו להגיע?", "Where would you like to go?"),
    messages: [text("הנה כמה קיצורים לפעולות שימושיות. פניות ותשובות מהצוות נמצאות ב״עדכונים ופניות״.", "Here are a few useful shortcuts. Find your requests and the team's replies in Updates & requests.")],
    choices: [action("עדכונים ופניות שלי", "My updates and requests", { type: "inbox" }), action("סיור עם מוקסי", "Tour with Muxi", { type: "tour" }), action("מאגר השאלות", "Question library", { type: "navigate", destination: "library" }), action("האזור האישי", "Personal area", { type: "navigate", destination: "learn" })],
  },
};
