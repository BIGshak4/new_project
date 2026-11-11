import type { WorkspaceRoute } from "./workspace-route";

/** The account tour guides live controls. The public sample tour has a separate lifecycle. */
export const MEMBER_TOUR_START_EVENT = "jobrun:member-tour-start";
export const MEMBER_TOUR_NAVIGATE_EVENT = "jobrun:member-tour-navigate";
export const MEMBER_TOUR_ACTION_EVENT = "jobrun:member-tour-action";
export type MemberTourStart = { userId: string };
export type MemberTourNavigate = { userId: string; route: WorkspaceRoute };
export type MemberTourAction = { userId: string; action: string };

export function emitMemberTourAction(userId: string, action: string): void {
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent<MemberTourAction>(MEMBER_TOUR_ACTION_EVENT, { detail: { userId, action } }));
}

export type MemberTourText = { he: string; en: string };
export type MemberTourTask = {
  id: string;
  text: MemberTourText;
  selector?: string;
  /** A successful app operation, rather than a click, completes this task. */
  event?: string;
  optional?: boolean;
};
export type MemberTourStep = {
  id: string;
  chapter: MemberTourText;
  title: MemberTourText;
  body: MemberTourText;
  href: string;
  questionSubject?: "software" | "hardware";
  tasks: readonly MemberTourTask[];
};
const bi = (he: string, en: string): MemberTourText => ({ he, en });
const control = (name: string) => `[data-member-tour="${name}"]`;
const tool = (name: string) => `[data-muxi-control="${name}"]`;

export const memberTourSteps: readonly MemberTourStep[] = [
  {
    id: "goal", chapter: bi("היעד שלכם", "Your goal"), href: "/?view=learn&nav=1",
    title: bi("בואו נתאים את התרגול אליכם", "Make the practice yours"),
    body: bi("נבחר את הכיוון והזמן שנוחים לכם. אלה ההעדפות האמיתיות של החשבון, ולפיהן נבנות ההמלצות והתוכנית היומית. כבר הגדרתם יעד שמתאים לכם? אפשר להמשיך איתו.", "Choose your direction and a comfortable daily pace. These are your account’s real preferences, used for recommendations and the daily plan. If your existing goal still fits, you can keep it."),
    tasks: [
      { id: "roles", text: bi("פתחו את בחירת התפקידים ובחרו תפקיד אחד או יותר. אפשר גם לבחור ללמוד בלי יעד מוגדר.", "Open the role choices and select one or more roles. You can also choose to learn without a defined goal."), selector: `${tool("goal-roles")}, ${tool("goal-mode-explore")}, ${control("goal-edit")}`, optional: true },
      { id: "time", text: bi("ב״זמן ביום״ הגדירו כמה דקות באמת תוכלו לפנות. התוכנית תתאים את היקף התרגול לזמן הזה.", "Under Daily time, set the minutes you can realistically make available. Your plan uses that time to size the practice."), selector: '[data-goal-section="minutes"] summary', optional: true },
      { id: "experience", text: bi("בחרו את השלב שלכם בקריירה. אם יש תאריך לראיון, הוסיפו אותו. אפשר להתחיל גם בלי תאריך.", "Choose your career stage. Add an interview date if you have one. You can start without a date."), selector: '[data-goal-section="seniority"] summary, [data-goal-section="date"] summary', optional: true },
      { id: "saved", text: bi("שמרו את הבחירות כדי לבנות את התוכנית, או אשרו שהיעד הקיים עדיין מתאים לכם.", "Save your choices to build the plan, or confirm that your existing goal still fits."), selector: `${tool("goal-save")}, ${control("goal-keep")}`, event: "goal-saved" },
    ],
  },
  {
    id: "dashboard", chapter: bi("האזור האישי", "Personal area"), href: "/?view=learn&nav=1",
    title: bi("מכאן יודעים מה לתרגל עכשיו", "Know what to practice next"),
    body: bi("הגלים מציגים שאלות מומלצות לפי היעד והנושאים שכדאי לחזק. ״התוכנית להיום״ מחלקת את זמן הלימוד שלכם לשלבים. אלה שתי דרכים לבחור איך להתחיל.", "The waves show recommended questions based on your goal and areas to strengthen. Today’s practice plan divides your study time into activities. Both help you choose where to begin."),
    tasks: [
      { id: "recommendations", text: bi("הכירו את השאלות שעל הגלים. אפשר להתחיל מכל אחת, בלי לפתור אותן בסדר המספרים.", "Explore the questions on the waves. You can start with any of them, without following the numbered order."), selector: "[data-recommendation-waves]" },
      { id: "plan", text: bi("פתחו את התוכנית להיום וראו איזה תרגול מתאים לזמן שהגדרתם. ב״בהמשך השבוע״ אפשר לראות גם את ההמשך.", "Look at Today’s practice plan to see the activities that fit your daily time. Later this week shows the upcoming activities."), selector: ".today-sheet, .later" },
      { id: "resume", text: bi("כשיש שאלה שנפתחה ועדיין לא נענתה, ״שנמשיך מאיפה שעצרת?״ מחזיר אליה. היעד והפרופיל נמצאים בהמשך העמוד.", "When you have an opened but unanswered question, Pick up where you left off takes you back to it. Your goal and profile are farther down the page."), selector: '[data-member-tour="resume"], [data-account-identity]', optional: true },
      { id: "activity", text: bi("בסרגל למעלה תוכלו לבדוק את רצף ימי התרגול ואת המטבעות שצברתם. לחיצה על הרצף מציגה באילו ימים עניתם על שאלות.", "The top bar shows your practice streak and coin balance. Select the streak to see the days on which you answered questions."), selector: "[data-account-stats]", optional: true },
      { id: "inbox", text: bi("ב״עדכונים ופניות״ נמצאים עדכוני האתר והתגובות לפניות שלכם. אפשר לחזור לשם אחרי שדיווחתם על בעיה.", "Updates and support contains site updates and replies to your requests. Return there after reporting a problem."), selector: "[data-jobrun-inbox-trigger]", optional: true },
    ],
  },
  {
    id: "library", chapter: bi("מאגר שאלות הראיון", "Interview question library"), href: "/?view=library&nav=1",
    title: bi("מוצאים שאלה שמתאימה לכם", "Find a question that fits"),
    body: bi("זה המאגר שמשמש בתרגול שלכם. אפשר לחפש לפי נושא, תפקיד או חברה ולסנן שאלות לפי הסטטוס שלהן. דיווחי החברות מגיעים ממתרגלים וממקורות הכנה.", "This is the library used in your practice. Search by topic, role or company, and filter questions by their practice status. Company labels come from learner reports and preparation sources."),
    tasks: [
      { id: "search", text: bi("נסו לחפש מונח שמעניין אתכם. אפשר לשלב מסננים ולהציג גם שאלות ששמרתם.", "Try searching for a topic that interests you. Combine filters or show questions you bookmarked."), selector: control("library-search") },
      { id: "question", text: bi("פתחו שאלה אמיתית מהמאגר כדי לקרוא את הניסוח. בתרגול אפשר לשמור הערות אישיות ולחזור אליהן.", "Open a real question to read its prompt. In practice, you can keep personal notes and return to them later."), selector: control("library-question") },
      { id: "reports", text: bi("בכל שאלה תמצאו יחד דיווח בעיה, שאלה לא ברורה ו״ראיתי בחברה״. אפשר לפתוח את האזור בלי לשלוח דיווח.", "Every question groups Report a problem, Unclear question and Seen at a company together. You can inspect the area without sending a report."), selector: control("question-reports"), optional: true },
    ],
  },
  {
    id: "explanation", chapter: bi("הסבר במילים שלכם", "Explain your reasoning"), href: "/?view=library&nav=1", questionSubject: "software",
    title: bi("נתחיל מהרעיון שלכם לפתרון", "Start with your own approach"),
    body: bi("נפתח שאלת תוכנה אמיתית מהמאגר. התרגול הזה שייך לחשבון שלכם. כתבו את הרעיון, ההנחות ומקרי הקצה במילים שלכם. בתחנה הבאה נוסיף קוד לאותה תשובה ונוכל לשלוח אותה למשוב.", "Open a real software question from the bank. This practice belongs to your account. Explain your idea, assumptions and edge cases in your own words. At the next stop, add code to the same answer and submit it for feedback."),
    tasks: [
      { id: "start", text: bi("קראו את השאלה ולחצו על התחלת תרגול. פתיחת התרגול נספרת בחשבון כמו כל תרגול אחר.", "Read the question and start practicing. Starting counts in your account like any other practice attempt."), selector: control("practice-start"), optional: true },
      { id: "open", text: bi("לחצו על ״כתיבת הסבר לפתרון״ כדי לפתוח מקום לרעיון שלכם.", "Choose Write an explanation to open a space for your approach."), selector: tool("explanation-open"), optional: true },
      { id: "write", text: bi("כתבו במילים שלכם מה מקבלים, מה צריך להחזיר ואיך הייתם פותרים. אפשר לשלב הנחות ומקרי קצה שכדאי לבדוק.", "Describe the input, expected output and your approach in your own words. Include assumptions and edge cases worth checking."), selector: tool("answer-explanation") },
      { id: "dictation", text: bi("אפשר גם להכתיב את ההסבר כשהדפדפן תומך בכך. בחרו שפה, עצרו את ההכתבה וערכו את הטקסט לפני השליחה.", "You can dictate when your browser supports it. Choose a language, stop dictation and edit the text before submitting."), selector: control("dictation"), optional: true },
      { id: "hints", text: bi("אם נתקעתם, אפשר לפתוח רמז. פתיחת רמז או פתרון נרשמת כרמת סיוע, ולכן כדאי לנסות קודם לבד.", "If you get stuck, open a hint. Viewing hints or the reference is recorded as assistance, so try independently first."), selector: control("practice-hints"), optional: true },
    ],
  },
  {
    id: "code", chapter: bi("קוד ומשוב אישי", "Code and personal feedback"), href: "/?view=library&nav=1", questionSubject: "software",
    title: bi("מהרעיון לקוד, ומהקוד למשוב", "From reasoning to code and feedback"),
    body: bi("ממשיכים באותה שאלה. ההסבר והקוד נשמרים יחד. כשהתשובה נשלחת, ה־AI בוחן את מה שכתבתם ומחזיר חוזקות, נקודות לשיפור ושאלת המשך. המשוב כאן נוצר מהתשובה שלכם.", "Continue with the same question. Your explanation and code are saved together. When you submit, AI reviews what you wrote and returns strengths, improvements and a follow-up question. This feedback is generated from your answer."),
    tasks: [
      { id: "open", text: bi("פתחו ״קוד, נוסחה או טבלת אמת״ כדי להוסיף את המימוש שלכם.", "Open Code, formula, or truth table to add your implementation."), selector: `${tool("code-open")}, ${tool("code-input")}` },
      { id: "language", text: bi("בחרו את שפת הקוד. אפשר גם לכתוב נוסחה, טבלת אמת או פסאודו־קוד. אם יש קוד בשאלה, ניתן להעתיק אותו לעורך.", "Choose the code language, or write a formula, truth table or pseudocode. When the question includes starter code, you can copy it into the editor."), selector: tool("code-language") },
      { id: "run", text: bi("כששירות ההרצה זמין, אפשר להריץ מול בדיקות השאלה או עם קלט משלכם. הרצה אינה שולחת תשובה למשוב, והצלחתה לבדה אינה מבטיחה פתרון נכון.", "When execution is available, run the question’s tests or use your own input. Running does not submit for feedback, and a successful run alone does not establish correctness."), selector: tool("code-execute"), optional: true },
      { id: "feedback", text: bi("כשתהיו מוכנים, שלחו את התשובה. לאחר שהמשוב יהיה מוכן תעברו אליו אוטומטית. השאלה תסומן ״בוצעה״ ברגע שהשליחה נקלטת.", "When ready, submit your answer. You’ll move to the feedback automatically when it is ready. The question is marked Done as soon as your submission is accepted."), selector: control("practice-submit"), event: "feedback-ready" },
      { id: "followup", text: bi("קראו מה היה טוב ומה כדאי לשפר. שאלת ההמשך עוזרת לחדד את ההסבר. אפשר גם לפתוח את הפתרון המוצע להשוואה.", "Read what worked and what needs improvement. The follow-up helps refine your reasoning. You can also open the reference solution to compare."), selector: `${control("practice-followup")}, ${control("practice-reference")}, #feedback`, optional: true },
    ],
  },
  {
    id: "circuit", chapter: bi("שאלת חומרה ושרטוט", "Hardware and circuit drawing"), href: "/?view=library&nav=1", questionSubject: "hardware",
    title: bi("בונים ובודקים את המעגל שלכם", "Build and test your circuit"),
    body: bi("נפתח שאלת חומרה אמיתית. השרטוט יכול להיות חלק מהתשובה שלכם לצד הסבר וקוד. שינויים במעגל צירופי נבדקים מיד. במעגל עם פליפ־פלופים תופיע גם אפשרות לסימולציה עם שעון.", "Open a real hardware question. Your circuit can be part of the answer alongside reasoning and code. Combinational circuits update immediately. Circuits with flip-flops also offer clocked simulation."),
    tasks: [
      { id: "open", text: bi("התחילו תרגול ופתחו ״שרטוט מעגל לוגי״. אפשר להרחיב את סביבת העבודה ולהציג בה את השאלה.", "Start practice and open Draw a logic circuit. You can expand the workspace and keep the question visible inside it."), selector: `${control("practice-start")}, ${tool("circuit-open")}, ${tool("circuit-expand")}` },
      { id: "parts", text: bi("בחרו רכיב בסרגל כדי להוסיף אותו. גררו אותו למקום. לחיצה עליו פותחת את הגדרות השם, רוחב הנתונים והכניסות שלו.", "Choose a component in the toolbar to add it, then drag it into place. Select it to edit its label, data width and inputs."), selector: tool("circuit-add-part") },
      { id: "wire", text: bi("חברו נקודת יציאה של רכיב לנקודת כניסה של רכיב אחר. אפשר גם לפתוח ״חיבור חוט בלי גרירה״ ולבחור את שני הקצוות.", "Connect a component’s output pin to another component’s input pin. You can also open Connect pins without dragging and select both endpoints."), selector: `${tool("circuit-pin")}, ${tool("circuit-wire-open")}`, optional: true },
      { id: "inputs", text: bi("בחרו רכיב INPUT ושנו את ערכו כדי לראות את התוצאה. טבלת האמת עוברת על כל צירופי הכניסות המתאימים למעגל.", "Select an INPUT and change its value to inspect the output. The truth table checks the input combinations supported by the circuit."), selector: `${tool("circuit-input-toggle")}, ${tool("circuit-input-value")}, ${tool("circuit-truth-table")}` },
      { id: "clock", text: bi("אם הוספתם פליפ־פלופ, הפעילו סימולציה והתקדמו בצעדי שעון. במעגל צירופי בלבד אין צורך בכפתור הזה.", "If you added a flip-flop, start simulation and advance with Clock step. A purely combinational circuit does not need this button."), selector: `${tool("circuit-simulate")}, ${tool("circuit-clock-step")}`, optional: true },
      { id: "editing", text: bi("אפשר לבטל או לשחזר פעולה, למחוק רכיב, להתאים את התצוגה לכל המעגל ולהוריד את השרטוט. בדקו שהחיבורים מתאימים לדרישות השאלה.", "Undo or redo an action, delete components, fit the whole circuit in view or download it. Check that the connections satisfy the question."), selector: `${tool("circuit-undo")}, ${tool("circuit-fit-view")}, ${tool("circuit-download")}`, optional: true },
      { id: "photos", text: bi("יש פתרון שכתבתם על דף? אפשר לצרף תמונות שלו לצד השרטוט וההסבר. פתחו את אפשרות הצירוף כדי לראות את סוגי הקבצים והמגבלות.", "Solved it on paper? Attach photos alongside the diagram and explanation. Open the attachment controls to see supported file types and limits."), selector: `${tool("photos-open")}, ${control("photos-tools")}`, optional: true },
    ],
  },
  {
    id: "fundamentals", chapter: bi("יסודות בקטנה", "Fundamentals"), href: "/?view=fundamentals&nav=1",
    title: bi("מחזקים עיקרון אחד בכמה דקות", "Strengthen one idea in a few minutes"),
    body: bi("אלה שאלות קצרות מהמאגר, שמתאימות לחזרה מהירה. מנסים לענות ואז פותחים את הפתרון להשוואה. אפשר לסמן שסיימתם ולחזור בהמשך לשאלות שעוד נשארו.", "These short bank questions are useful for quick revision. Try answering, then reveal the reference to compare. Mark questions finished and return later to the ones that remain."),
    tasks: [
      { id: "topics", text: bi("בחרו נושא שמעניין אתכם או חפשו שאלה. אפשר לסנן לפי שאלות שכבר סיימתם או שעדיין נשארו.", "Choose a topic or search for a question. Filter by questions you have finished or still need to practice."), selector: `${control("quick-topics")}, ${control("quick-topics-toggle")}` },
      { id: "reveal", text: bi("נסו לענות לעצמכם ואז לחצו על ״הצגת פתרון קצר״. פתיחת הפתרון אינה מסמנת שסיימתם.", "Try to answer, then select Show short solution. Revealing a solution does not mark the question finished."), selector: control("quick-reveal") },
      { id: "complete", text: bi("אם סיימתם, אפשר לשמור את הסימון ולעבור לשאלה הבאה. זהו סימון התקדמות שלכם, ולא ציון על נכונות התשובה.", "When finished, save the completion mark and move on. This records your progress, not a correctness score."), selector: control("quick-complete"), optional: true },
      { id: "quiz", text: bi("כפתור ״בוחן״ מאפשר לבחור נושאים ולבנות בוחן של עשר שאלות אקראיות. אתם בוחרים מתי לפתוח את הפתרונות.", "Quiz lets you choose topics and build a set of ten random questions. You decide when to reveal each solution."), selector: control("quick-quiz"), optional: true },
      { id: "quiz-topics", text: bi("בחלון הבחירה סמנו נושאים, או השתמשו ב״בחר הכול״. צריך לפחות עשר שאלות בנושאים שנבחרו כדי ליצור בוחן.", "In the topic picker, check topics or use Select all. Your selected topics must contain at least ten questions to create a quiz."), selector: control("quiz-topics"), optional: true },
      { id: "quiz-practice", text: bi("לחצו על ״ליצור בוחן של 10 שאלות״. ענו בקצב שלכם ופתחו את הפתרונות לבדיקה עצמית. הבוחן אינו מקבל ציון AI ואינו משנה את סימוני ההשלמה שלכם.", "Select Create a 10-question quiz. Work at your pace and reveal solutions to check yourself. This quiz has no AI grade and does not change your completion markers."), selector: `${control("quiz-create")}, ${control("quiz-questions")}`, optional: true },
    ],
  },
  {
    id: "games", chapter: bi("משחקים", "Games"), href: "/games",
    title: bi("ננסה שאלה כמו במשחק", "Try a question as it appears in a game"),
    body: bi("בדו־קרב שני שחקנים עונים על אותן חמש שאלות אמריקאיות. קודם קובע מספר התשובות הנכונות, ואחריו זמן המענה. כאן אפשר לנסות שאלה אמיתית מהמאגר בלי להמתין לחבר ובלי להוציא מטבעות.", "In a duel, two players answer the same five multiple-choice questions. Correct answers decide first, then answering time. Here you can try a real bank question without waiting for a friend or spending coins."),
    tasks: [
      { id: "start", text: bi("פתחו את ההתנסות כדי לקבל שאלה מהמאגר שמשמש במשחקים.", "Start the practice round to receive a question from the games question bank."), selector: control("game-practice-start"), optional: true },
      { id: "answer", text: bi("בחרו אחת מארבע התשובות ולחצו על ״בדיקת התשובה״ כדי לראות את ההסבר. במשחק מול חבר, לחיצה על תשובה שולחת אותה מיד.", "Choose one of the four answers, then select Check answer to read the explanation. In a game against a friend, selecting an answer submits it immediately."), selector: `${control("game-practice")}:not(:has(${control("game-practice-choice")}:checked)) ${control("game-practice-choice")}, ${control("game-practice-check")}:not(:disabled)`, event: "game-practice-answered" },
    ],
  },
  {
    id: "friends", chapter: bi("חברים ודו־קרב", "Friends and duels"), href: "/games",
    title: bi("מתרגלים גם ביחד", "Practice together, too"),
    body: bi("לכל משתמש יש קוד חברים אישי בן שמונה תווים. אפשר לשלוח בקשת חברות באמצעות הקוד, ולראות את החברים והדמויות שלהם אחרי האישור. הזמנה לדו־קרב יוצרת משחק אמיתי.", "Each account has a personal eight-character friend code. Send a request using a friend’s code, then see their name and character after acceptance. A duel invitation creates a real game."),
    tasks: [
      { id: "code", text: bi("מצאו את הקוד האישי שלכם. אפשר להעתיק אותו ולשתף עם מי שרוצים לצרף כחבר.", "Find your personal code. Copy it when you want to share it with a friend."), selector: `${control("friends-code")}, [data-friends-panel]` },
      { id: "add", text: bi("כאן מזינים קוד של חבר ושולחים בקשה. לא צריך לשלוח בקשה כדי לסיים את הסיור.", "This is where you enter a friend’s code and send a request. Sending one is not required to complete the tour."), selector: `${control("friends-input")}, [data-friends-panel] input[name="friend_code"]`, optional: true },
      { id: "duel", text: bi("לדו־קרב יוצרים הזמנה ושולחים את הקישור. העלות מוצגת לפני ההתחלה, והשעון מתחיל רק כששני השחקנים מוכנים.", "Create a duel invitation and share its link. The cost is shown before you start, and the clock begins only when both players are ready."), selector: control("game-invite"), optional: true },
    ],
  },
  {
    id: "shop", chapter: bi("החנות של מוקסי", "Muxi’s shop"), href: "/games/shop",
    title: bi("נותנים לדמות את האופי שלכם", "Give your character your style"),
    body: bi("זו החנות האמיתית והדמות שלכם. אפשר לבחור רכיב וצבע, למדוד סקינים ולראות כמה מטבעות נדרשים לרכישה. המדידה חינם. רכישה מתבצעת רק בלחיצה על כפתור הקנייה.", "This is the real shop and your character. Choose a component and color, try on skins, and see their coin prices. Trying them on is free. Purchases happen only when you select Buy."),
    tasks: [
      { id: "collection", text: bi("הסתכלו בקולקציה ופתחו הדפס שמעניין אתכם. הסינון ״הארון שלי״ מציג את הפריטים שכבר בבעלותכם.", "Explore the collection and open a print that catches your eye. My wardrobe shows the items you already own."), selector: control("shop-collection"), optional: true },
      { id: "try", text: bi("לחצו על ״למדוד על הדמות שלי״ כדי לראות איך הסקין נראה. המדידה אינה קונה את הפריט.", "Select Try on my character to see how the skin looks. Trying it on does not purchase it."), selector: control("shop-try-on") },
      { id: "customize", text: bi("בחרו רכיב או צבע לדמות. כשתרצו לשמור מראה שבבעלותכם, לחצו ״לשמור את הדמות״. אין צורך לקנות דבר בסיור.", "Choose a component or color. To keep a look you own, select Save character. No purchase is needed for the tour."), selector: `${control("shop-customize")}, ${control("shop-save")}`, optional: true },
    ],
  },
  {
    id: "interview", chapter: bi("ראיון מדומה", "Mock interview"), href: "/?view=interview&nav=1",
    title: bi("מתרגלים רצף של ראיון אמיתי", "Practice the flow of an interview"),
    body: bi("בחרו 20, 30 או 45 דקות. בכל פעם תופיע שאלה אחת ותענו בכתב, עם אפשרות לקוד ולשרטוט. השאלות הבאות מותאמות לתשובות שלכם. בסיום נבנה דוח שמרכז מה כדאי לחזק.", "Choose 20, 30 or 45 minutes. Answer one question at a time in writing, with code and drawing available. Later questions adapt to your answers. A final report summarizes what to strengthen."),
    tasks: [
      { id: "duration", text: bi("בחרו משך שמתאים לכם. ההתחלה מפעילה ראיון אמיתי עם שעון. אפשר להמשיך בסיור ולהתחיל ראיון בזמן שנוח לכם.", "Choose a duration that fits. Starting launches a real timed interview. You may continue the tour and start an interview when convenient."), selector: control("interview-duration") },
      { id: "answer", text: bi("אם התחלתם, ענו לשאלה במילים שלכם ושלחו. אפשר לבקש רמז, והוא יופיע בדוח כחלק מרמת הסיוע.", "If you started, answer in your own words and submit. You can ask for a hint, which is reflected as assistance in the report."), selector: `${control("interview-start")}, ${control("interview-answer")}`, optional: true },
      { id: "report", text: bi("אפשר לסיים מוקדם ולקבל דוח על מה שעניתם. הדוח נשמר בראיונות הקודמים, ומשם ניתן לפתוח אותו או למחוק אותו מהרשימה.", "You can end early and receive a report on what you answered. It is saved under Previous interviews, where you can reopen it or remove it from the list."), selector: `${control("interview-end")}, ${control("interview-report")}, ${control("interview-history")}`, optional: true },
    ],
  },
  {
    id: "helper", chapter: bi("העוזר האישי", "Personal helper"), href: "/?view=learn&nav=1",
    title: bi("העזרה נשארת לידכם גם אחרי הסיור", "Help stays nearby after the tour"),
    body: bi("הדמות שלכם בכפתור ״צריכים עזרה?״ מלווה אתכם בכלי האתר. אפשר לקבל הסבר ממוקד, למצוא כלי, לפתוח פנייה או לחזור לסיור. הוא מתחיל סגור כדי שתוכלו להתרכז.", "Your character behind Need a hand? helps you use the site. Get focused guidance, locate a tool, open a support request or return to the tour. It starts closed so you can focus."),
    tasks: [
      { id: "open", text: bi("פתחו את העוזר האישי באמצעות הדמות שלכם.", "Open the personal helper using your character."), selector: control("helper-launcher") },
      { id: "topic", text: bi("בחרו נושא והתנסו בשאלת המשך. אפשר להגיע לכלי מתאים או לפתוח טופס פנייה עם סוג התקלה שכבר בחרתם.", "Choose a topic and try a follow-up. You can find the relevant tool or open a support form with your chosen issue category prefilled."), selector: control("helper-topic"), event: "helper-used" },
    ],
  },
];

export type MemberTourProgress = {
  version: 1;
  userId: string;
  stepId: string;
  completedTasks: string[];
  skippedSteps: string[];
  status: "paused" | "active" | "completed";
  updatedAt: number;
};
export const memberTourKey = (userId: string) => `jobrun-member-tour-live-v1-${userId}`;
export const memberTaskKey = (stepId: string, taskId: string) => `${stepId}:${taskId}`;
export function initialMemberTourProgress(userId: string): MemberTourProgress {
  return { version: 1, userId, stepId: memberTourSteps[0].id, completedTasks: [], skippedSteps: [], status: "paused", updatedAt: 0 };
}

export function parseMemberTourProgress(raw: string | null, userId: string): MemberTourProgress {
  const empty = initialMemberTourProgress(userId);
  if (!raw || raw.length > 30_000) return empty;
  try {
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object") return empty;
    const data = value as Record<string, unknown>;
    if (data.version !== 1 || data.userId !== userId || !["paused", "active", "completed"].includes(String(data.status))) return empty;
    const steps = new Set(memberTourSteps.map(step => step.id));
    const tasks = new Set(memberTourSteps.flatMap(step => step.tasks.map(task => memberTaskKey(step.id, task.id))));
    const clean = (ids: unknown, allowed: Set<string>): string[] => Array.isArray(ids) ? [...new Set(ids.filter((id): id is string => typeof id === "string" && allowed.has(id)))] : [];
    const completedTasks = clean(data.completedTasks, tasks);
    const skippedSteps = clean(data.skippedSteps, steps);
    return { ...empty, stepId: typeof data.stepId === "string" && steps.has(data.stepId) ? data.stepId : empty.stepId,
      completedTasks, skippedSteps, status: data.status as MemberTourProgress["status"],
      updatedAt: typeof data.updatedAt === "number" && Number.isFinite(data.updatedAt) && data.updatedAt > 0 ? data.updatedAt : 0 };
  } catch { return empty; }
}

export function completeMemberTourTask(progress: MemberTourProgress, stepId: string, taskId: string): MemberTourProgress {
  const step = memberTourSteps.find(item => item.id === stepId);
  if (!step?.tasks.some(task => task.id === taskId)) return progress;
  const key = memberTaskKey(stepId, taskId);
  if (progress.completedTasks.includes(key)) return progress;
  return { ...progress, completedTasks: [...progress.completedTasks, key], updatedAt: Date.now() };
}

export function memberTourStepReady(step: MemberTourStep, progress: MemberTourProgress): boolean {
  return step.tasks.filter(task => !task.optional).every(task => progress.completedTasks.includes(memberTaskKey(step.id, task.id)));
}

export function moveMemberTour(progress: MemberTourProgress, stepId: string): MemberTourProgress {
  if (!memberTourSteps.some(step => step.id === stepId)) return progress;
  return { ...progress, stepId, status: "active", updatedAt: Date.now() };
}

/** Skip is always available, including when a live service or optional control is unavailable. */
export function advanceMemberTour(progress: MemberTourProgress, skip = false): MemberTourProgress {
  const index = memberTourSteps.findIndex(step => step.id === progress.stepId);
  const step = memberTourSteps[index];
  if (!step || (!skip && !memberTourStepReady(step, progress))) return progress;
  const skippedSteps = skip && !memberTourStepReady(step, progress)
    ? [...new Set([...progress.skippedSteps, step.id])]
    : progress.skippedSteps.filter(id => id !== step.id);
  const next = memberTourSteps[index + 1];
  return { ...progress, stepId: next?.id ?? step.id, skippedSteps, status: next ? "active" : "completed", updatedAt: Date.now() };
}
