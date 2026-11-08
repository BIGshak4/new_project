export type TourKind = "preview" | "member";
export type TourText = { he: string; en: string };
export type TourExercise = "goal" | "library" | "circuit" | "code" | "feedback" | "quiz" | "interview" | "community" | "helper";
export type TourStep = { id: string; chapter: TourText; exercise: TourExercise; title: TourText; body: TourText; task: TourText; actions: string[] };
const bi = (he: string, en: string): TourText => ({ he, en });

const goal: TourStep = {
  id: "goal", exercise: "goal", chapter: bi("היעד שלי", "My goal"),
  title: bi("נתחיל ביעד שלך", "Start with your goal"),
  body: bi("היעד מכוון את תוכנית התרגול באזור האישי. אפשר להתמקד בתפקיד או ללמוד בקצב שלכם. אם כבר הגדרתם יעד, אפשר להמשיך איתו.", "Your goal shapes the practice plan in your personal area. Prepare for a role or explore at your own pace. If you already have a goal, you can keep it."),
  task: bi("אשרו את היעד הקיים או בחרו יעד ושמרו אותו בחשבון.", "Keep your current goal or choose a goal and save it to your account."), actions: ["goal-saved"],
};
const library: TourStep = {
  id: "library", exercise: "library", chapter: bi("מאגר השאלות", "Question library"),
  title: bi("איזו שאלה מסקרנת אותך?", "Which question catches your eye?"),
  body: bi("במאגר אפשר לחפש לפי נושא, תפקיד ושמות חברות שדווחו. שאלה ארוכה נותנת מקום להסביר איך הגעתם לפתרון. אם עצרתם באמצע, האזור האישי מחזיר אתכם לשאלה.", "Search the library by topic, role or a reported company. A long question gives you room to explain how you reached a solution. The personal area can take you back to an unfinished question."),
  task: bi("פתחו שאלה לדוגמה. אפשר לנסות גם חיפוש ורמז.", "Open a sample question. You can also try the search and a hint."), actions: ["question-open"],
};
const circuit: TourStep = {
  id: "circuit", exercise: "circuit", chapter: bi("מעבדת חומרה", "Hardware lab"),
  title: bi("מה יקרה ליציאה?", "What will the output be?"),
  body: bi("בשאלת חומרה אפשר לצרף שרטוט ולבדוק אותו. במעגל הזה שער XOR מחזיר 1 כששתי הכניסות שונות. במעגל עם פליפ־פלופ אפשר לבדוק גם פעימות שעון.", "Attach a circuit to a hardware answer and test it. This XOR gate gives 1 when its inputs differ. Circuits with flip-flops also let you test clock steps."),
  task: bi("שנו אחת מהכניסות וראו מה קורה ליציאה.", "Toggle an input and watch the output."), actions: ["input-toggled"],
};
const code: TourStep = {
  id: "code", exercise: "code", chapter: bi("סדנת תוכנה", "Software workspace"),
  title: bi("איפה הלולאה צריכה לעצור?", "Where should the loop stop?"),
  body: bi("בשאלת תוכנה אפשר לכתוב קוד ולצדו הסבר חופשי. בראיון חשוב להסביר גם איזה מקרה חשף את הטעות. כאן הלולאה מנסה לקרוא איבר אחרי סוף המערך.", "In a software question you can write code alongside your reasoning. Interviewers also want to understand which case exposed a bug. This loop tries to read past the end of the array."),
  task: bi("תקנו את תנאי העצירה בעורך, או נסו את התיקון של מוקסי.", "Edit the loop condition yourself or try Muxi’s fix."), actions: ["code-edited"],
};
const feedback: TourStep = {
  id: "feedback", exercise: "feedback", chapter: bi("משוב והמשך", "Feedback and follow-up"),
  title: bi("מה חסר בתשובה?", "What would make the answer stronger?"),
  body: bi("אחרי ששולחים תשובה בתרגול, המשוב מצביע על מה שעבד ועל מה שכדאי לבדוק. שאלת המשך נותנת הזדמנות להשלים את ההסבר. כאן אפשר להשוות שתי תשובות עם משוב שהוכן מראש לכל אחת.", "After a practice submission, feedback identifies strengths and things to check. A follow-up question invites you to fill a gap in your reasoning. Compare two sample answers with feedback written for each."),
  task: bi("בחרו תשובה ופתחו את המשוב שלה. אפשר גם להתנסות בשאלת ההמשך.", "Choose an answer and open its feedback. You can also try the follow-up."), actions: ["feedback-reviewed"],
};
const quiz: TourStep = {
  id: "quiz", exercise: "quiz", chapter: bi("תרגול קצר", "Quick practice"),
  title: bi("יש כמה דקות לחזרה?", "Have a few minutes to practice?"),
  body: bi("ב״יסודות בקטנה״ אפשר לתרגל שאלה קצרה או להרכיב בוחן של עשר שאלות מהנושאים שתבחרו. פותחים את הפתרונות בקצב שלכם.", "In Fundamentals you can practice one short question or build a ten-question quiz from topics you pick. Reveal the solutions at your own pace."),
  task: bi("פתחו את בורר הנושאים והרכיבו בוחן לדוגמה.", "Open the topic picker and create a sample quiz."), actions: ["quiz-started"],
};
const interview: TourStep = {
  id: "interview", exercise: "interview", chapter: bi("ראיון מדומה", "Mock interview"),
  title: bi("עכשיו תורך לענות", "Your turn in the interview"),
  body: bi("בראיון המדומה בוחרים זמן, מקבלים שאלה אחת בכל פעם ועונים בכתב. הדוח בסיום מרכז מה כדאי לתרגל בהמשך. כאן נתנסה בשאלה אחת ובדוח לדוגמה.", "In a mock interview, choose a duration and answer one question at a time in writing. The final report helps you decide what to practice next. Try one question and see an example report."),
  task: bi("התחילו ראיון לדוגמה, ענו בקצרה ופתחו את הדוח.", "Start a sample interview, give a short answer and open the report."), actions: ["interview-finished"],
};
const community: TourStep = {
  id: "community", exercise: "community", chapter: bi("משחקים וחברים", "Games and friends"),
  title: bi("עם מי מתרגלים היום?", "Who are you practicing with?"),
  body: bi("במשחקים מוסיפים חברים בעזרת קוד אישי. אפשר גם להזמין חבר לדו־קרב של חמש שאלות. בחנות של מוקסי משתמשים במטבעות כדי לעצב את הדמות.", "In Games, add friends using their personal code. You can also invite a friend to a five-question duel. In Muxi’s shop, coins let you customize your character."),
  task: bi("נסו להוסיף את חברת הדוגמה באמצעות הקוד שלה.", "Try adding the sample friend using her code."), actions: ["friend-previewed"],
};
const helper: TourStep = {
  id: "helper", exercise: "helper", chapter: bi("העוזר האישי", "Personal helper"),
  title: bi("ואם נתקעים באמצע?", "What if you get stuck?"),
  body: bi("בכפתור ״צריכים עזרה?״ תמצאו את הדמות שלכם. אפשר לבקש הדרכה בכלי פתרון או לפתוח פנייה. ליד כל שאלה יש גם דיווח בעיה, שאלה לא ברורה ודיווח שראיתם אותה בחברה.", "Your character is behind the “Need a hand?” button. Ask for help with an answer tool or open a support request. Each question also has actions to report a problem, flag unclear wording or record a company sighting."),
  task: bi("בחרו במה העוזר יעזור לכם ונסו את השלב הראשון.", "Pick something to ask the helper and try its first step."), actions: ["helper-used"],
};

const previewSteps = [library, circuit, code, feedback, quiz, interview];
const memberSteps = [goal, ...previewSteps, community, helper];
export function tourSteps(kind: TourKind): readonly TourStep[] {
  return kind === "preview" ? previewSteps : memberSteps;
}

/** A v1 example goal must never count as setting a member’s real goal. */
export const tourKey = (userId?: string) => userId ? `jobrun-muxi-tour-v2-member-${userId}` : "jobrun-muxi-tour-v2-preview";
export type TourProgress = { version: 2; offered: boolean; kind: TourKind; stepId: string; completed: string[]; skipped: string[]; status: "paused" | "completed" | "dismissed"; updatedAt: number };
export function initialTourProgress(kind: TourKind): TourProgress {
  return { version: 2, kind, offered: false, stepId: tourSteps(kind)[0].id, completed: [], skipped: [], status: "paused", updatedAt: 0 };
}

export function parseTourProgress(value: string | null, kind: TourKind): TourProgress {
  const empty = initialTourProgress(kind);
  if (!value || value.length > 20_000) return empty;
  try {
    const p = JSON.parse(value);
    if (p?.version !== 2 || p.kind !== kind || !["paused", "completed", "dismissed"].includes(p.status)) return empty;
    const steps = tourSteps(kind);
    const valid = new Set(steps.map(s => s.id));
    const sanitize = (ids: unknown): string[] => Array.isArray(ids) ? [...new Set(ids.filter((id): id is string => typeof id === "string" && valid.has(id)))] : [];
    const completed = sanitize(p.completed);
    const skipped = sanitize(p.skipped).filter(id => !completed.includes(id));
    const firstPending = steps.find(step => !completed.includes(step.id) && !skipped.includes(step.id));
    return { ...empty, offered: p.offered === true, completed, skipped,
      stepId: valid.has(p.stepId) ? p.stepId : firstPending?.id ?? steps[0].id, status: p.status,
      updatedAt: Number.isFinite(p.updatedAt) && p.updatedAt > 0 ? p.updatedAt : 0 };
  } catch { return empty; }
}

export function stationReady(step: TourStep, actions: readonly string[]): boolean {
  return step.actions.every(action => actions.includes(action));
}
export function checkpoint(progress: TourProgress, step: TourStep, outcome: "completed" | "skipped", next?: TourStep): TourProgress {
  const completed = new Set(progress.completed), skipped = new Set(progress.skipped);
  if (outcome === "completed") { completed.add(step.id); skipped.delete(step.id); }
  else if (!completed.has(step.id)) skipped.add(step.id);
  return { ...progress, offered: true, completed: [...completed], skipped: [...skipped], stepId: next?.id ?? step.id, status: next ? "paused" : "completed", updatedAt: Date.now() };
}
