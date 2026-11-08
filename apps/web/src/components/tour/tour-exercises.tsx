"use client";

import dynamic from "next/dynamic";
import { useId, useState, type ReactNode } from "react";
import { BookOpen, Check, Play } from "lucide-react";
import { type Circuit, signalKey, simulate } from "../../lib/circuit";
import { formatTechnicalAnswer, parseTechnicalAnswer } from "../../lib/technical-answer";
import type { TourExercise } from "../../lib/muxi-tour";
import { helperTopics, type HelperTopicId } from "../../lib/personal-helper";
import avatarCatalog from "../../lib/avatar-catalog.json";
import { AnswerEditor } from "../answer-editor";
import { BidiText } from "../bidi-text";
import { LogicAvatar } from "../wardrobe/logic-avatar";
import { TourXorTrace } from "./tour-xor-trace";
import styles from "./tour-exercises.module.css";

const CircuitEditor = dynamic(() => import("../circuit-editor"), { ssr: false });
const QuizDemo = dynamic(() => import("./tour-quiz-demo").then(module => module.TourQuizDemo));
type Lang = "he" | "en";
type Localized = { he: string; en: string };
type DemoProps = { lang: Lang; onAction: (action: string) => void };
const bi = (he: string, en: string): Localized => ({ he, en });

const examples = [
  { title: bi("חיישן לדלת ולחלון", "Door and window sensors"), topic: bi("חומרה", "Hardware"),
    prompt: bi("הנורה נדלקת כשבדיוק אחד משני החיישנים פעיל. איזה שער מתאים?", "A light turns on when exactly one of two sensors is active. Which gate fits?"),
    hint: bi("מה צריכה הנורה להציג כששני החיישנים פעילים?", "Should the light be on when both sensors are active?") },
  { title: bi("האיבר האחרון במערך", "The last array element"), topic: bi("תוכנה", "Software"),
    prompt: bi("במערך יש ארבעה איברים. באיזה אינדקס צריך לעצור כדי לא לקרוא מחוץ למערך?", "An array contains four elements. Where should a loop stop to stay in bounds?"),
    hint: bi("בדקו מהו האינדקס הראשון ומהו האחרון.", "Compare the first and last valid indexes.") },
  { title: bi("מזהים את המטבע הכבד", "Find the heavy coin"), topic: bi("חשיבה והיגיון", "Reasoning"),
    prompt: bi("אחד משלושה מטבעות כבד יותר. איך מזהים אותו בשקילה אחת במאזניים?", "One of three coins is heavier. How can one weighing on a balance identify it?"),
    hint: bi("גם כשהמאזניים מאוזנים, למדתם משהו על המטבע שנשאר בחוץ.", "A balance still gives information about the coin you left out.") },
];

function LibraryDemo({ lang, onAction }: DemoProps) {
  const [query, setQuery] = useState("");
  const [selected, select] = useState<number | null>(null);
  const [hint, setHint] = useState(false);
  const ids = examples.map((_, index) => index).filter(index =>
    Object.values(examples[index].title).concat(Object.values(examples[index].topic)).join(" ").toLowerCase().includes(query.trim().toLowerCase()));
  const example = selected === null ? null : examples[selected];
  return <>
    <label className={styles.search}>{lang === "he" ? "חיפוש במאגר לדוגמה" : "Search the sample library"}
      <input type="search" value={query} placeholder={lang === "he" ? "שם שאלה או נושא" : "Question title or topic"} onChange={e => { setQuery(e.target.value); select(null); setHint(false); }} /></label>
    <div className={styles.list}>{ids.map(index => <button type="button" key={index} data-muxi-control="library-question" aria-pressed={selected === index} onClick={() => { select(index); setHint(false); onAction("question-open"); }}>
      <BookOpen size={18} aria-hidden="true" /><strong>{examples[index].title[lang]}</strong><small>{examples[index].topic[lang]}</small>
    </button>)}</div>
    {!ids.length && <p role="status">{lang === "he" ? "לא נמצאה שאלה. נסו שם נושא כמו חומרה." : "No match. Try a topic such as Hardware."}</p>}
    {example && <div className={styles.result} aria-live="polite"><h3>{example.title[lang]}</h3><p>{example.prompt[lang]}</p>
      <button type="button" aria-expanded={hint} onClick={() => setHint(!hint)}>{lang === "he" ? (hint ? "סגירת הרמז" : "פתיחת רמז") : (hint ? "Close hint" : "Open hint")}</button>{hint && <p>{example.hint[lang]}</p>}</div>}
    </>;
}

function xorCircuit(): Circuit {
  return { version: 1, parts: [
    { id: "a", kind: "input", label: "A", x: 0, y: 0, count: 2, bits: 1, value: 0 },
    { id: "b", kind: "input", label: "B", x: 0, y: 190, count: 2, bits: 1, value: 1 },
    { id: "xor", kind: "xor", label: "XOR", x: 250, y: 80, count: 2, bits: 1, value: 0 },
    { id: "y", kind: "output", label: "Y", x: 485, y: 80, count: 2, bits: 1, value: 0 },
  ], wires: [
    { id: "wa", source: "a", sourcePort: "Q", target: "xor", targetPort: "A0" },
    { id: "wb", source: "b", sourcePort: "Q", target: "xor", targetPort: "A1" },
    { id: "wy", source: "xor", sourcePort: "Y", target: "y", targetPort: "D" },
  ] };
}

function CircuitDemo({ lang, onAction, guide }: DemoProps & { guide?: ReactNode }) {
  const [circuit, setCircuit] = useState(xorCircuit);
  const [editorOpen, setEditorOpen] = useState(false);
  const [originalWiring, setOriginalWiring] = useState(true);
  const output = simulate(circuit).signals[signalKey("y", "display")];
  const inputs = circuit.parts.filter(part => (part.id === "a" || part.id === "b") && part.kind === "input");
  function toggle(id: string) {
    setCircuit(current => ({ ...current, parts: current.parts.map(part => part.id === id ? { ...part, value: part.value ? 0 : 1 } : part) }));
    onAction("input-toggled");
  }
  return <>
    <p className={styles.prompt}>{examples[0].prompt[lang]}</p>
    {!editorOpen && originalWiring && inputs.length === 2 && typeof output === "number" &&
      <TourXorTrace a={inputs[0].value} b={inputs[1].value} output={output} />}
    <div className={styles.io} dir="ltr">{inputs.map(part => <button key={part.id} type="button" data-muxi-control={`xor-input-${part.id}`} aria-pressed={Boolean(part.value)} onClick={() => toggle(part.id)}>{part.label} = {part.value}</button>)}
      <span aria-hidden="true">→</span><output data-muxi-control="xor-output" aria-live="polite">Y = {output ?? "?"}</output>
    </div>
    <details onToggle={e => setEditorOpen(e.currentTarget.open)}><summary data-muxi-control="circuit-editor-details">{lang === "he" ? "פתיחת עורך המעגלים" : "Open the circuit editor"}</summary>
      {editorOpen && <CircuitEditor value={circuit} onChange={updated => { setOriginalWiring(false); setCircuit(updated); }} lang={lang} guide={guide} onActivity={onAction}
        question={{ title: examples[0].title[lang], content: <p>{examples[0].prompt[lang]}</p> }} />}
    </details>
    {editorOpen && <button type="button" onClick={() => { setCircuit(xorCircuit()); setOriginalWiring(true); }}>{lang === "he" ? "איפוס מעגל הדוגמה" : "Reset the sample circuit"}</button>}
  </>;
}

const buggyCode = "int sum(const int a[], int n) {\n    int total = 0;\n    for (int i = 0; i <= n; ++i) {\n        total += a[i];\n    }\n    return total;\n}";
const fixedCode = buggyCode.replace("i <= n", "i < n");
function stopsBeforeEnd(code: string) {
  const condition = /\bfor\s*\([^;{}]*;([^;{}]*);/.exec(code)?.[1].replace(/[\s()]/g, "");
  return !!condition && ["i<n", "i<=n-1", "i!=n", "n>i", "n-1>=i", "n!=i"].includes(condition);
}
function CodeDemo({ lang, onAction }: DemoProps) {
  const [answer, setAnswer] = useState("");
  const currentCode = parseTechnicalAnswer(answer).code;
  const corrected = stopsBeforeEnd(currentCode);
  return <>
    <p className={styles.prompt}>{examples[1].prompt[lang]}</p>
    <pre className={styles.code} dir="ltr"><code>{currentCode || buggyCode}</code></pre>
    <button type="button" data-muxi-control="code-fix" onClick={() => {
      setAnswer(formatTechnicalAnswer(parseTechnicalAnswer(answer).explanation, fixedCode, "c")); onAction("code-edited");
    }}>{lang === "he" ? "ניסוי התיקון של מוקסי" : "Try Muxi’s correction"}</button>
    {corrected && <p className={styles.result} role="status"><BidiText>{lang === "he" ? "כעת תנאי העצירה הוא לפני i = n. במערך של ארבעה איברים האינדקס האחרון הוא 3." : "This condition stops before i = n. For four items, the last valid index is 3."}</BidiText></p>}
    <AnswerEditor value={answer} onChange={value => {
      setAnswer(value);
      if (stopsBeforeEnd(parseTechnicalAnswer(value).code)) onAction("code-edited");
    }} lang={lang} disabled={false} codeLanguage="c" starterCode={buggyCode} />
  </>;
}

const responses = [
  { answer: bi("אדליק את הנורה אם לפחות חיישן אחד פעיל.", "Turn the light on when at least one sensor is active."),
    good: bi("זיהית שצריך להתייחס לשתי הכניסות.", "You identified that both inputs matter."),
    missing: bi("גם כששניהם פעילים, התנאי שלך מדליק את הנורה. הדרישה היא שרק אחד מהם יהיה פעיל.", "When both sensors are active your condition lights the lamp. The requirement is exactly one active sensor."),
    next: bi("איזה צירוף כניסות מבדיל בין OR לבין XOR?", "Which input combination distinguishes OR from XOR?"),
    reply: bi("כאשר שני הקלטים הם 1, שער OR מחזיר 1 ושער XOR מחזיר 0.", "With both inputs at 1, OR outputs 1 and XOR outputs 0.") },
  { answer: bi("אשתמש ב־XOR. שני קלטים שווים מכבים את הנורה ושני קלטים שונים מדליקים אותה.", "Use XOR. Equal inputs turn the light off and different inputs turn it on."),
    good: bi("חיברת בין תנאי השאלה להתנהגות המדויקת של השער.", "You connected the requirement to the gate’s exact behavior."),
    missing: bi("אפשר להציג את ארבעת צירופי הכניסות כדי להראות שכיסית כל מקרה.", "List the four input combinations to demonstrate full coverage."),
    next: bi("מה תראה טבלת האמת של הנורה?", "What would the lamp’s truth table show?"),
    reply: bi("בצירופים 00 ו־11 הנורה כבויה. בצירופים 01 ו־10 היא דולקת.", "The lamp is off for 00 and 11, and on for 01 and 10.") },
];

function FeedbackDemo({ lang, onAction }: DemoProps) {
  const [choice, setChoice] = useState<number | null>(null);
  const [shown, setShown] = useState(false);
  const [followup, setFollowup] = useState("");
  const [reference, setReference] = useState(false);
  const sample = choice === null ? null : responses[choice];
  return <>
    <p className={styles.prompt}>{examples[0].prompt[lang]}</p>
    <div className={styles.list}>{responses.map((response, index) => <button key={index} type="button" data-muxi-control="feedback-answer" aria-pressed={choice === index}
      onClick={() => { setChoice(index); setShown(false); setReference(false); setFollowup(""); }}><BidiText>{response.answer[lang]}</BidiText></button>)}</div>
    <button type="button" className={styles.primary} data-muxi-control="feedback-review" disabled={!sample} onClick={() => { setShown(true); onAction("feedback-reviewed"); }}>{lang === "he" ? "הצגת משוב לדוגמה" : "Show sample feedback"}</button>
    {sample && shown && <div className={styles.result} aria-live="polite"><h3>{lang === "he" ? "מה היה טוב" : "What worked"}</h3><p>{sample.good[lang]}</p>
      <h3>{lang === "he" ? "מה אפשר לשפר" : "What to improve"}</h3><p>{sample.missing[lang]}</p>
      <label><strong>{lang === "he" ? "שאלת המשך" : "Follow-up question"}</strong><BidiText>{sample.next[lang]}</BidiText><textarea value={followup} onChange={e => { setFollowup(e.target.value); setReference(false); }} maxLength={2000}/></label>
      <button type="button" onClick={() => setReference(true)}>{lang === "he" ? "השוואה לתשובה לדוגמה" : "Compare with a sample answer"}</button>{reference && <p><BidiText>{sample.reply[lang]}</BidiText></p>}</div>}
  </>;
}

function InterviewDemo({ lang, onAction }: DemoProps) {
  const [stage, setStage] = useState<"setup" | "question" | "report">("setup");
  const [minutes, setMinutes] = useState(20);
  const [answer, setAnswer] = useState("");
  const he = lang === "he";
  const prompt = he ? "איך תבדקו שמערכת שסופרת לחיצות על כפתור סופרת כל לחיצה פעם אחת?" : "How would you check that a button counter counts each press exactly once?";
  const sample = he ? "אבדוק לחיצה קצרה, לחיצה ממושכת ושתי לחיצות קרובות. אשווה את הספירה לתוצאה הצפויה בכל מקרה." : "I would test a quick press, a held press and two presses close together, then compare each count with the expected result.";
  if (stage === "setup") return <>
    <fieldset className={styles.duration}><legend>{he ? "כמה זמן מקצים לראיון?" : "How long would you set aside?"}</legend>
      {[20, 30, 45].map(n => <button key={n} type="button" aria-pressed={minutes === n} onClick={() => setMinutes(n)}>{n} {he ? "דקות" : "minutes"}</button>)}</fieldset>
    <p>{he ? "בסבב הזה מוקסי ישאל שאלה אחת, בקצב שלכם." : "In this sample Muxi asks one question, at your pace."}</p>
    <button type="button" className={styles.primary} data-muxi-control="interview-start" onClick={() => setStage("question")}><Play size={16} />{he ? "התחלת ראיון לדוגמה" : "Start sample interview"}</button>
  </>;
  if (stage === "report") return <div className={styles.result} role="status">
    <h3>{he ? "דוח ראיון לדוגמה" : "Sample interview report"}</h3>
    <p>{he ? "שאלה אחת נענתה. הנה התשובה שכתבתם:" : "One question answered. Here is your response:"}</p>
    <blockquote><BidiText>{answer}</BidiText></blockquote>
    <p>{he ? "נקודה להשוואה: האם התייחסתם ללחיצה אחת ממושכת ולשתי לחיצות ברצף? בראיון אמיתי הדוח מתייחס לתשובות שנתתם." : "A point to compare: did you cover one long press and two consecutive presses? A real report gives feedback on the answers you gave."}</p></div>;
  return <>
    <label>{prompt}<textarea data-muxi-control="interview-answer" value={answer} maxLength={2000} onChange={e => setAnswer(e.target.value)} /></label>
    <div className={styles.actions}><button type="button" data-muxi-control="interview-example" onClick={() => setAnswer(sample)}>{he ? "שימוש בתשובה לדוגמה" : "Use a sample answer"}</button>
      <button type="button" className={styles.primary} data-muxi-control="interview-finish" disabled={!answer.trim()} onClick={() => { setStage("report"); onAction("interview-finished"); }}>{he ? "סיום והצגת הדוח" : "Finish and view report"}</button></div>
  </>;
}

const sampleFriendCode = "A4B03F9C";
const sampleShirts = avatarCatalog.skins.filter(skin => ["classic", "circuit", "cosmic"].includes(skin.key));
function CommunityDemo({ lang, onAction }: DemoProps) {
  const he = lang === "he";
  const [code, setCode] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState(false);
  const [skin, setSkin] = useState("classic");
  return <>
    <div className={styles.friend}><LogicAvatar size={112} config={{ component: "xor", color: "mint", skin }} label={he ? "דמות הדוגמה של נועה" : "Noa’s sample character"} />
      <div><h3>{he ? "נועה" : "Noa"}</h3><p>{he ? "קוד חברות לדוגמה" : "Sample friend code"} · <bdi>{sampleFriendCode}</bdi></p></div></div>
    {sent ? <p className={styles.result} role="status"><Check size={18} /> {he ? "בקשת ההדגמה הושלמה כאן בסיור. במשחקים חברים מופיעים ברשימה אחרי שמאשרים את הבקשה." : "You completed a sample request inside the tour. In Games, friends appear on your list once they accept."}</p> :
      <form className={styles.form} onSubmit={e => { e.preventDefault(); if (code.toUpperCase() !== sampleFriendCode) { setError(true); return; } setSent(true); onAction("friend-previewed"); }}>
        <label>{he ? "קוד אישי של חבר או חברה" : "Friend’s personal code"}<input maxLength={8} dir="ltr" value={code} autoComplete="off" onChange={e => { setCode(e.target.value.toUpperCase()); setError(false); }} /></label>
        <div className={styles.actions}><button type="button" data-muxi-control="friend-preview" onClick={() => { setCode(sampleFriendCode); setError(false); }}>{he ? "מילוי הקוד של נועה" : "Use Noa’s code"}</button>
          <button className={styles.primary} data-muxi-control="friend-add" disabled={!code.trim()}>{he ? "שליחת בקשה לדוגמה" : "Try a friend request"}</button></div>
        {error && <p role="alert">{he ? "נסו את הקוד שמופיע ליד נועה." : "Use the code shown beside Noa."}</p>}
      </form>}
    <details><summary>{he ? "מדידת חולצה מהחנות של מוקסי" : "Try on a shirt from Muxi’s shop"}</summary>
      <p>{he ? "בחרו חולצה ותראו אותה על נועה. המדידה בסיור חופשית." : "Choose a shirt to see it on Noa. Try-ons in the tour are free."}</p>
      <div className={styles.actions}>{sampleShirts.map(shirt => <button key={shirt.key} type="button" aria-pressed={skin === shirt.key}
        data-muxi-control={`shirt-${shirt.key}`} onClick={() => setSkin(shirt.key)}>{shirt.label[lang]}</button>)}</div>
    </details>
  </>;
}

const helpChoices = [
  { id: "explanation", label: bi("איך כותבים הסבר לפתרון?", "How do I explain a solution?") },
  { id: "circuit-check", label: bi("איך בודקים מעגל?", "How do I test a circuit?") },
  { id: "support-question", label: bi("מה עושים אם השאלה לא ברורה?", "What if a question is unclear?") },
] as const;
function HelperDemo({ lang, onAction }: DemoProps) {
  const [topic, setTopic] = useState<HelperTopicId | null>(null);
  return <>
    <p>{lang === "he" ? "במה תרצו עזרה?" : "What would you like a hand with?"}</p>
    <div className={styles.list}>{helpChoices.map(choice => <button key={choice.id} type="button" data-muxi-control="helper-question" aria-pressed={choice.id === topic}
      onClick={() => { setTopic(choice.id); onAction("helper-used"); }}>{choice.label[lang]}</button>)}</div>
    {topic && <div className={styles.result} role="status"><h3>{helperTopics[topic].title[lang]}</h3><p><BidiText>{helperTopics[topic].messages[0][lang]}</BidiText></p></div>}
  </>;
}

const labels: Record<Exclude<TourExercise, "goal">, Localized> = {
  library: bi("שאלות לדוגמה", "Sample library"), code: bi("שאלה בתוכנה", "Software question"),
  circuit: bi("מעגל XOR", "XOR circuit"), feedback: bi("משוב על תשובה לדוגמה", "Sample answer feedback"),
  quiz: bi("בוחן לפי נושאים", "Topic quiz"), interview: bi("ראיון בכתב", "Written interview"),
  community: bi("חברות לפי קוד אישי", "Friends by personal code"), helper: bi("צריכים עזרה?", "Need a hand?"),
};
export function TourExercises({ exercise, lang, onAction, stationId, guide }: DemoProps & {
  exercise: TourExercise; stationId?: string; guide?: ReactNode;
}) {
  const id = useId();
  if (exercise === "goal") return null; // The tour host renders the account's real goal.
  const props = { lang, onAction };
  return <section className={styles.root} dir={lang === "he" ? "rtl" : "ltr"} data-muxi-target={exercise} data-muxi-exercise-station={stationId} aria-labelledby={id}>
    <h2 id={id}><BidiText>{labels[exercise][lang]}</BidiText></h2>
    {exercise === "library" && <LibraryDemo {...props} />}
    {exercise === "circuit" && <CircuitDemo {...props} guide={guide} />}
    {exercise === "code" && <CodeDemo {...props} />}
    {exercise === "feedback" && <FeedbackDemo {...props} />}
    {exercise === "quiz" && <QuizDemo {...props} />}
    {exercise === "interview" && <InterviewDemo {...props} />}
    {exercise === "community" && <CommunityDemo {...props} />}
    {exercise === "helper" && <HelperDemo {...props} />}
  </section>;
}
