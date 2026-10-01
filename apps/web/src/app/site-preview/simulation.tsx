"use client";

import {
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type ReactNode,
} from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import Image from "next/image";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpLeft,
  BookOpen,
  Bookmark,
  Check,
  CheckCheck,
  ChevronDown,
  Clock3,
  Code2,
  Cpu,
  FileImage,
  Flame,
  History,
  Lightbulb,
  ListChecks,
  Map,
  MessageSquare,
  Moon,
  Play,
  Plus,
  Search,
  Send,
  Settings2,
  SlidersHorizontal,
  Sun,
  Target,
  Trash2,
  TrendingUp,
  UserRound,
  X,
  Zap,
} from "lucide-react";
import { emptyCircuit, type Circuit } from "../../lib/circuit";
import type { AnswerLanguage } from "../../lib/technical-answer";
import {
  categoryLabel,
  questions,
  screens,
  siteDirections,
  type Sample,
  type Screen,
  type T,
} from "./data";
import s from "./site.module.css";

const CodeEditor = dynamic(
  () => import("../../components/technical-code-editor"),
  { ssr: false, loading: () => <p>…</p> },
);
const CircuitEditor = dynamic(() => import("../../components/circuit-editor"), {
  ssr: false,
  loading: () => <p>…</p>,
});
type Draft = {
  text: string;
  code: string;
  language: AnswerLanguage;
  hints: number;
  solution: boolean;
  solutionSeen: boolean;
  submitted: boolean;
  tab: string;
  circuit: Circuit;
  images: { name: string; src: string }[];
};
const newDraft = (q: Sample): Draft => ({
  text: "",
  code: q.code,
  language: q.language,
  hints: 0,
  solution: false,
  solutionSeen: false,
  submitted: false,
  tab: "text",
  circuit: emptyCircuit(),
  images: [],
});
type Go = (screen: Screen, id?: string) => void;
type Props = { t: T; go: Go };

function Button({
  children,
  onClick,
  secondary = false,
  disabled = false,
}: {
  children: ReactNode;
  onClick: () => void;
  secondary?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      className={secondary ? s.secondary : s.primary}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
function Meta({ q, t }: { q: Sample; t: T }) {
  return (
    <div className={s.meta}>
      <span>{categoryLabel(q.category, t)}</span>
      <span>{t(...q.topic)}</span>
      <span>
        {t("דיווח לדוגמה:", "Example report:")} <bdi>{q.company}</bdi>
      </span>
    </div>
  );
}
function CircuitMoment({ signal = false, t }: { signal?: boolean; t: T }) {
  const [a, setA] = useState(1),
    [b, setB] = useState(0);
  return (
    <div className={`${s.circuitMoment} ${signal ? s.signalMoment : ""}`}>
      <div className={s.circuitDiagram} dir="ltr">
        <div className={s.inputs}>
          <button
            onClick={() => setA(1 - a)}
            aria-label={`A: ${a}`}
            aria-pressed={!!a}
          >
            A <b>{a}</b>
          </button>
          <button
            onClick={() => setB(1 - b)}
            aria-label={`B: ${b}`}
            aria-pressed={!!b}
          >
            B <b>{b}</b>
          </button>
        </div>
        <svg viewBox="0 0 90 130" aria-hidden="true">
          <path d="M0 31H45V48H90M0 99H45V82H90" />
        </svg>
        <div className={s.logicGate}>
          <strong>XOR</strong>
          <small>A ⊕ B</small>
        </div>
        <svg viewBox="0 0 50 100" aria-hidden="true">
          <path d="M0 50H50" />
        </svg>
        <output aria-live="polite">{a ^ b}</output>
      </div>
      <p>
        {t(
          "לחצו על הכניסות. שינוי קטן, תוצאה אחרת.",
          "Toggle an input. A small change, a different result.",
        )}
      </p>
      {signal && (
        <div className={s.truthStrip} dir="ltr">
          {[0, 1, 2, 3].map((v) => (
            <span key={v} data-active={v >> 1 === a && v % 2 === b}>
              {v >> 1}
              {v % 2}
              <ArrowRight size={12} />
              {(v >> 1) ^ (v % 2)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function SiteSimulation() {
  const params = useSearchParams();
  const style =
    siteDirections.find((d) => d.id === params.get("style"))?.id ?? "studio";
  const screen = screens.includes(params.get("screen") as Screen)
    ? (params.get("screen") as Screen)
    : "home";
  const q =
    questions.find((v) => v.id === params.get("question")) ?? questions[0];
  const [lang, setLang] = useState<"he" | "en">("he");
  const t: T = (he, en) => (lang === "he" ? he : en);
  const [dark, setDark] = useState(false);
  const theme =
    style === "studio"
      ? "studio"
      : style === "signal"
        ? "signal"
        : style === "ion" || (style === "ion-adaptive" && dark)
          ? "ion"
          : "light";
  const [bookmarks, setBookmarks] = useState(["fsm", "missing"]);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [recent, setRecent] = useState<string[]>(["array", "clock"]);
  const [goal, setGoal] = useState({
    role: "digital",
    minutes: 25,
    level: "student",
    name: "אור",
    reminders: true,
  });
  const [notice, setNotice] = useState("");
  const draft = drafts[q.id] ?? newDraft(q);
  function updateDraft(patch: Partial<Draft>) {
    setDrafts((old) => ({
      ...old,
      [q.id]: { ...(old[q.id] ?? newDraft(q)), ...patch },
    }));
  }
  function go(next: Screen, id?: string) {
    const p = new URLSearchParams(params.toString());
    p.set("style", style);
    p.set("screen", next);
    if (id) p.set("question", id);
    else p.delete("question");
    window.history.pushState(null, "", `?${p}`);
    setNotice("");
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  function bookmark(id: string) {
    setBookmarks((old) =>
      old.includes(id) ? old.filter((v) => v !== id) : [...old, id],
    );
  }
  function submit() {
    updateDraft({ submitted: true });
    setRecent((old) => [q.id, ...old.filter((v) => v !== q.id)]);
  }
  const nav = [
    { id: "today", icon: Map, label: t("היום שלי", "Today") },
    { id: "library", icon: BookOpen, label: t("מאגר השאלות", "Questions") },
    {
      id: "interview",
      icon: MessageSquare,
      label: t("ראיון מדומה", "Interview"),
    },
    { id: "progress", icon: TrendingUp, label: t("ההתקדמות שלי", "Progress") },
  ];
  const activeNav = ["practice", "saved"].includes(screen)
    ? "library"
    : screen === "history"
      ? "progress"
      : screen;
  return (
    <div
      className={`${s.root} ${s[theme]} ${params.get("motion") === "0" ? s.noMotion : ""}`}
      dir={lang === "he" ? "rtl" : "ltr"}
      lang={lang}
    >
      <div className={s.demoBar}>
        <span>
          {t(
            "סימולציה מלאה · כל הנתונים, החברות והמשובים לדוגמה · ללא חיבור לשרת",
            "Full simulation · Data, companies and feedback are examples · No backend",
          )}
        </span>
        <a href="/design-lab" target="_top">
          {t("כל העיצובים", "All designs")}
          <ArrowUpLeft size={13} />
        </a>
      </div>
      <header className={s.header}>
        <button
          className={s.brand}
          onClick={() => go("home")}
          aria-label={t("JobRun — דף הבית", "JobRun — Home")}
          dir="ltr"
        >
          jobrun<span>.</span>
        </button>
        <nav aria-label={t("ניווט ראשי", "Main navigation")}>
          {nav.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => go(id as Screen)}
              aria-current={activeNav === id ? "page" : undefined}
            >
              <Icon size={17} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className={s.headerTools}>
          {style === "ion-adaptive" && (
            <button
              className={s.iconButton}
              onClick={() => setDark(!dark)}
              aria-label={
                dark
                  ? t("מעבר למצב בהיר", "Switch to light mode")
                  : t("מעבר למצב כהה", "Switch to dark mode")
              }
              title={
                dark ? t("מצב בהיר", "Light mode") : t("מצב כהה", "Dark mode")
              }
            >
              {dark ? <Sun size={19} /> : <Moon size={19} />}
            </button>
          )}
          <button
            className={s.language}
            onClick={() => setLang(lang === "he" ? "en" : "he")}
            aria-label={t("Switch to English", "מעבר לעברית")}
          >
            {lang === "he" ? "EN" : "עב"}
          </button>
          <button
            className={s.avatar}
            aria-label={t("הפרופיל שלי", "My profile")}
            onClick={() => go("profile")}
          >
            <UserRound size={19} />
          </button>
        </div>
      </header>
      <main className={`${s.main} ${screen === "home" ? s.landing : ""}`}>
        {screen === "home" ? (
          <Home t={t} go={go} theme={theme} />
        ) : screen === "today" ? (
          <Today t={t} go={go} minutes={goal.minutes} />
        ) : screen === "library" || screen === "saved" ? (
          <Library
            key={screen}
            t={t}
            go={go}
            savedOnly={screen === "saved"}
            bookmarks={bookmarks}
            toggle={bookmark}
          />
        ) : screen === "practice" ? (
          <Practice
            t={t}
            go={go}
            q={q}
            draft={draft}
            update={updateDraft}
            submit={submit}
            bookmarked={bookmarks.includes(q.id)}
            bookmark={() => bookmark(q.id)}
            lang={lang}
          />
        ) : screen === "interview" ? (
          <Interview t={t} go={go} />
        ) : screen === "progress" ? (
          <Progress t={t} go={go} />
        ) : screen === "history" ? (
          <HistoryScreen t={t} go={go} recent={recent} drafts={drafts} />
        ) : screen === "profile" || screen === "goal" ? (
          <Profile
            t={t}
            go={go}
            onboarding={screen === "goal"}
            goal={goal}
            setGoal={setGoal}
            notice={notice}
            save={() => {
              setNotice(
                t(
                  "ההעדפות עודכנו בהדמיה בלבד.",
                  "Preferences updated in this simulation only.",
                ),
              );
              if (screen === "goal") go("today");
            }}
          />
        ) : screen === "auth" ? (
          <AuthScreen t={t} go={go} />
        ) : (
          <Help t={t} go={go} />
        )}
      </main>
      <footer className={s.footer}>
        <div>
          <button className={s.brand} onClick={() => go("home")} dir="ltr">
            jobrun<span>.</span>
          </button>
          <p>
            {t(
              "לומדים איך לחשוב. מגיעים מוכנים.",
              "Learn how to think. Arrive prepared.",
            )}
          </p>
        </div>
        <div>
          <button onClick={() => go("library")}>
            {t("מאגר שאלות", "Question library")}
          </button>
          <button onClick={() => go("saved")}>
            {t("שאלות שמורות", "Saved questions")}
          </button>
          <button onClick={() => go("help")}>
            {t("עזרה ושאלות נפוצות", "Help & FAQ")}
          </button>
          <button onClick={() => go("auth")}>
            {t("מסך כניסה והרשמה", "Sign-in & registration")}
          </button>
        </div>
        <small>
          {t(
            "הדמיית עיצוב בלבד. רענון הדף מאפס טיוטות ונתוני הדגמה.",
            "Design simulation only. Reloading resets drafts and demo data.",
          )}
        </small>
      </footer>
    </div>
  );
}

function Home({ t, go, theme }: Props & { theme: string }) {
  const [a, setA] = useState(1),
    [b, setB] = useState(0);
  const studio = theme === "studio",
    signal = theme === "signal";
  return (
    <>
      <section
        className={`${s.hero} ${studio ? s.studioHero : signal ? s.signalHero : s.ionHero}`}
      >
        <div className={s.heroCopy}>
          <h1>
            {studio ? (
              <>
                {t("קצת תרגול.", "A little practice.")}
                <br />
                <em>{t("הרבה יותר ביטחון.", "A lot more confidence.")}</em>
              </>
            ) : signal ? (
              <>
                {t("הראיון הבא", "Your next interview")}
                <br />
                {t("מתחיל", "starts")} <em>{t("כאן.", "here.")}</em>
              </>
            ) : (
              <>
                {t("הרעיון הבא", "Your next idea")}
                <br />
                {t("מתחיל", "starts")} <em>{t("אצלך.", "with you.")}</em>
              </>
            )}
          </h1>
          <p>
            {studio
              ? t(
                  "לא צריך לדעת הכול היום. נתחיל משאלה אחת, נבין את הדרך ונמשיך משם.",
                  "You don't need every answer today. Start with one question, understand the reasoning, then build on it.",
                )
              : t(
                  "הכנה לראיונות חומרה ותוכנה, בעברית ובאנגלית. לתרגל את הידע. להסביר את הדרך. להגיע עם ביטחון.",
                  "Hardware and software interview preparation, in Hebrew and English. Practice your knowledge. Explain your reasoning. Arrive with confidence.",
                )}
          </p>
          <div className={s.heroActions}>
            <Button onClick={() => go("goal")}>
              {t("בואו נמצא את הכיוון שלכם", "Find your starting point")}
              <ArrowLeft size={20} />
            </Button>
            <button className={s.textButton} onClick={() => go("library")}>
              {t("קודם אציץ בשאלות", "Explore the questions")}
              <ArrowUpLeft size={17} />
            </button>
          </div>
          <div className={s.heroTopics}>
            <span>Digital design</span>
            <span>C / C++</span>
            <span>{t("חשיבה לוגית", "Problem solving")}</span>
          </div>
        </div>
        {studio ? (
          <div className={s.studioExperiment}>
            <h2>
              {t("מתי שני ביטים", "When do two bits")}
              <br />
              {t("מספרים סיפור אחר?", "tell a different story?")}
            </h2>
            <CircuitMoment t={t} />
            <button
              className={s.textButton}
              onClick={() => go("practice", "xor")}
            >
              {t("מהניסוי לשאלת ראיון", "From experiment to interview")}
              <ArrowLeft size={17} />
            </button>
          </div>
        ) : signal ? (
          <div className={s.signalConsole}>
            <h2>
              {t("שתי כניסות.", "Two inputs.")}
              <br />
              <em>{t("רגע אחד של הבנה.", "One moment of clarity.")}</em>
            </h2>
            <CircuitMoment signal t={t} />
            <p className={s.consoleState}>
              <i />
              {t("המעגל שלכם פעיל", "Your circuit is live")}
            </p>
            <button
              className={s.textButton}
              onClick={() => go("practice", "xor")}
            >
              {t("בואו נפרק את זה", "Let's work through it")}
              <ArrowLeft size={18} />
            </button>
          </div>
        ) : (
          <div className={s.ionArt}>
            <div className={s.chipScene}>
              <i className={s.orbit} />
              <i className={s.orbitTwo} />
              <div className={s.chip}>
                <Image
                  src="/design-worlds/ion-chip.png"
                  alt={t(
                    "שבב סיליקון סגול עם מגעים מתכתיים",
                    "Violet silicon chip with metallic contacts",
                  )}
                  fill
                  sizes="(max-width:700px) 310px, 460px"
                  priority
                />
                <strong aria-hidden="true">{a ^ b}</strong>
              </div>
            </div>
            <div className={s.ionInputs} dir="ltr">
              <button onClick={() => setA(1 - a)} aria-label={`A: ${a}`}>
                A <b>{a}</b>
              </button>
              <button onClick={() => setB(1 - b)} aria-label={`B: ${b}`}>
                B <b>{b}</b>
              </button>
              <span>
                Y = <output aria-live="polite">{a ^ b}</output>
              </span>
            </div>
            <p>
              {t(
                "שני קלטים. לחצו ושנו את התוצאה.",
                "Two inputs. Tap to change the output.",
              )}
            </p>
          </div>
        )}
      </section>
      <section className={s.homeFlow}>
        <h2>
          {t("מהשאלה הראשונה,", "From your first question,")}
          <br />
          {t("עד לרגע שהכול מתחבר.", "to the moment it clicks.")}
        </h2>
        <div>
          {[
            [
              "בוחרים כיוון",
              "Choose a direction",
              "חומרה, תוכנה או חידה לחימום. מתחילים מהמקום שמתאים לכם.",
              "Hardware, software or a warm-up puzzle. Start where it makes sense for you.",
            ],
            [
              "נותנים למחשבה מקום",
              "Make room for thought",
              "כותבים, מקודדים או משרטטים. הרמז הבא מחכה רק אם תצטרכו.",
              "Write, code or draw. The next hint is there if you need it.",
            ],
            [
              "מבינים מה לקחת הלאה",
              "Know what comes next",
              "משווים לפתרון, חוזרים לנקודה הקשה וממשיכים לתרגול הבא.",
              "Compare approaches, revisit the tricky part and move forward.",
            ],
          ].map(([he, en, sub, subEn], i) => (
            <button
              key={en}
              onClick={() =>
                go(
                  i === 0 ? "library" : i === 1 ? "practice" : "progress",
                  i === 1 ? "xor" : undefined,
                )
              }
            >
              <span>{i + 1}</span>
              <h3>{t(he, en)}</h3>
              <p>{t(sub, subEn)}</p>
              <ArrowUpLeft size={22} />
            </button>
          ))}
        </div>
      </section>
      <section className={s.homeQuestions}>
        <div className={s.sectionHeading}>
          <h2>
            {t("שאלות שפותחות את הראש.", "Questions that open your mind.")}
          </h2>
          <button className={s.textButton} onClick={() => go("library")}>
            {t("למאגר השאלות", "Browse the library")}
            <ArrowLeft size={18} />
          </button>
        </div>
        {questions.slice(0, 3).map((q) => (
          <button
            key={q.id}
            className={s.simpleQuestion}
            onClick={() => go("practice", q.id)}
          >
            <span>{t(...q.topic)}</span>
            <h3>{t(...q.title)}</h3>
            <span>
              {q.minutes} {t("דקות", "min")}
              <ArrowLeft size={19} />
            </span>
          </button>
        ))}
      </section>
    </>
  );
}

function Today({ t, go, minutes }: Props & { minutes: number }) {
  return (
    <>
      <div className={s.pageHeading}>
        <div>
          <h1>{t("נפגשים עם הרעיון הבא.", "Meet your next idea.")}</h1>
          <p>
            {t(
              `יש לכם ${minutes} דקות? הכנו מקום להתחיל.`,
              `Got ${minutes} minutes? Here's your starting point.`,
            )}
          </p>
        </div>
        <button className={s.secondary} onClick={() => go("profile")}>
          <SlidersHorizontal size={17} />
          {t("התאמת התוכנית", "Adjust your plan")}
        </button>
      </div>
      <div className={s.todayLayout}>
        <section className={s.nextSession}>
          <div className={s.sessionMeta}>
            <span>{t("תכנון דיגיטלי", "Digital design")}</span>
            <span>
              <Clock3 size={16} />
              15 {t("דקות", "min")}
            </span>
          </div>
          <h2>
            {t("כששני ביטים", "When two bits")}
            <br />
            {t("לא מסכימים.", "disagree.")}
          </h2>
          <p>
            {t(
              "מהטבלה למעגל: מפרקים את פעולת XOR ומסבירים כל בחירה.",
              "From truth table to circuit: break down XOR and explain each decision.",
            )}
          </p>
          <CircuitMoment t={t} />
          <Button onClick={() => go("practice", "xor")}>
            {t("פותחים את התרגול", "Start this session")}
            <ArrowLeft size={18} />
          </Button>
        </section>
        <aside className={s.weekPlan}>
          <div className={s.sectionHeading}>
            <h2>{t("השבוע שלכם", "Your week")}</h2>
            <span>{t("תוכנית לדוגמה", "Sample plan")}</span>
          </div>
          {[
            ["יסודות שעובדים", "Solid foundations", "xor", true],
            ["למצוא את הבאג", "Find the bug", "array", true],
            ["לחשוב במצבים", "Think in states", "fsm", false],
            ["להסביר את הדרך", "Explain the reasoning", "missing", false],
          ].map(([he, en, id, done], i) => (
            <button
              key={String(id)}
              className={s.planStep}
              onClick={() => go("practice", String(id))}
            >
              <span className={done ? s.stepDone : s.stepNumber}>
                {done ? <Check size={17} /> : i + 1}
              </span>
              <div>
                <strong>{t(String(he), String(en))}</strong>
                <small>
                  {t(
                    i === 2 ? "השלב הבא" : "תרגול ממוקד",
                    i === 2 ? "Up next" : "Focused practice",
                  )}
                </small>
              </div>
              <ArrowLeft size={17} />
            </button>
          ))}
          <div className={s.weekDays}>
            {["א", "ב", "ג", "ד", "ה", "ו", "ש"].map((day, i) => (
              <span key={i} data-done={i < 3}>
                <small>{t(day, ["S", "M", "T", "W", "T", "F", "S"][i])}</small>
                {i < 3 ? <Check size={16} /> : <i />}
              </span>
            ))}
          </div>
          <p className={s.muted}>
            {t(
              "רצף והשלמת משימות מוצגים להמחשה.",
              "Streaks and completed tasks are illustrative.",
            )}
          </p>
        </aside>
      </div>
      <section className={s.splitStrip}>
        <div>
          <Flame size={27} />
          <h2>
            {t("משהו קטן לפני שממשיכים?", "A small challenge before you go?")}
          </h2>
          <p>
            {t(
              "חידת השעון: שמונה דקות של שינוי זווית.",
              "The clock puzzle: eight minutes for a fresh perspective.",
            )}
          </p>
        </div>
        <Button secondary onClick={() => go("practice", "clock")}>
          {t("לחידה היומית", "Try the daily puzzle")}
          <ArrowLeft size={18} />
        </Button>
      </section>
    </>
  );
}

function Library({
  t,
  go,
  savedOnly,
  bookmarks,
  toggle,
}: Props & {
  savedOnly: boolean;
  bookmarks: string[];
  toggle: (id: string) => void;
}) {
  const [query, setQuery] = useState(""),
    [category, setCategory] = useState("all"),
    [difficulty, setDifficulty] = useState("all");
  const list = questions.filter(
    (q) =>
      (!savedOnly || bookmarks.includes(q.id)) &&
      (category === "all" || q.category === category) &&
      (difficulty === "all" || q.difficulty[1] === difficulty) &&
      [
        ...q.title,
        ...q.topic,
        q.company,
        q.aliases,
        categoryLabel(q.category, t),
      ]
        .join(" ")
        .toLocaleLowerCase()
        .includes(query.trim().toLocaleLowerCase()),
  );
  return (
    <>
      <div className={s.pageHeading}>
        <div>
          <h1>
            {savedOnly
              ? t("שמרתם לרגע הנכון.", "Saved for the right moment.")
              : t("שאלה טובה. התחלה טובה.", "A good question. A good start.")}
          </h1>
          <p>
            {t(
              "בחרו תחום, חפשו חברה או לכו בעקבות הסקרנות.",
              "Choose a topic, search a company, or follow your curiosity.",
            )}
          </p>
        </div>
        <button
          className={s.secondary}
          onClick={() => go(savedOnly ? "library" : "saved")}
        >
          <Bookmark size={17} />
          {savedOnly
            ? t("לכל השאלות", "All questions")
            : t(`שמורים (${bookmarks.length})`, `Saved (${bookmarks.length})`)}
        </button>
      </div>
      <div className={s.libraryFilters}>
        <label className={s.search}>
          <Search size={20} />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t(
              "שאלה, נושא או חברה… למשל אינטל",
              "Question, topic or company… e.g. Intel",
            )}
            aria-label={t("חיפוש במאגר", "Search questions")}
          />
          {query && (
            <button
              aria-label={t("ניקוי החיפוש", "Clear search")}
              onClick={() => setQuery("")}
            >
              <X size={16} />
            </button>
          )}
        </label>
        <label className={s.selectLabel}>
          {t("רמה", "Level")}
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
          >
            <option value="all">{t("כל הרמות", "All levels")}</option>
            <option value="Foundations">{t("יסודות", "Foundations")}</option>
            <option value="Intermediate">{t("ביניים", "Intermediate")}</option>
            <option value="Warm-up">{t("חימום", "Warm-up")}</option>
          </select>
        </label>
      </div>
      <div className={s.filterBar}>
        <div className={s.segmented}>
          {["all", "hardware", "software", "logic"].map((c) => (
            <button
              key={c}
              aria-pressed={category === c}
              onClick={() => setCategory(c)}
            >
              {c === "all" ? t("הכול", "All") : categoryLabel(c, t)}
            </button>
          ))}
        </div>
        <span>
          {list.length} {t("שאלות בהדמיה", "demo questions")}
        </span>
      </div>
      <div className={s.libraryList}>
        {list.map((q) => (
          <article className={s.questionRow} key={q.id}>
            <div className={s.questionIcon}>
              {q.category === "hardware" ? (
                <Cpu size={22} />
              ) : q.category === "software" ? (
                <Code2 size={22} />
              ) : (
                <Lightbulb size={22} />
              )}
            </div>
            <button
              className={s.questionName}
              onClick={() => go("practice", q.id)}
            >
              <h2>{t(...q.title)}</h2>
              <Meta q={q} t={t} />
            </button>
            <span className={s.difficulty}>{t(...q.difficulty)}</span>
            <span className={s.time}>
              <Clock3 size={15} />
              {q.minutes} {t("דק׳", "min")}
            </span>
            <button
              className={s.iconButton}
              aria-label={
                bookmarks.includes(q.id)
                  ? t("ביטול שמירה", "Remove bookmark")
                  : t("שמירת שאלה", "Bookmark question")
              }
              aria-pressed={bookmarks.includes(q.id)}
              onClick={() => toggle(q.id)}
            >
              <Bookmark
                size={19}
                fill={bookmarks.includes(q.id) ? "currentColor" : "none"}
              />
            </button>
            <button
              className={s.rowArrow}
              onClick={() => go("practice", q.id)}
              aria-label={t("פתיחת ", "Open ") + t(...q.title)}
            >
              <ArrowLeft size={20} />
            </button>
          </article>
        ))}
        {!list.length && (
          <div className={s.empty}>
            <Search size={32} />
            <h2>{t("עוד לא מצאנו התאמה.", "No matches yet.")}</h2>
            <p>
              {t(
                "נסו חיפוש אחר או הסירו את הסינון.",
                "Try another search or clear the filters.",
              )}
            </p>
            <Button
              secondary
              onClick={() => {
                setQuery("");
                setCategory("all");
                setDifficulty("all");
                if (savedOnly) go("library");
              }}
            >
              {t("להציג את כל השאלות", "Show all questions")}
            </Button>
          </div>
        )}
      </div>
      <p className={s.sourceNote}>
        {t(
          "במוצר, שיוך לחברות מבוסס על דיווחי מועמדים. השאלות ושיוכי החברות במסך הזה הם נתוני הדגמה.",
          "In the product, company associations come from candidate reports. Questions and company associations on this screen are demo data.",
        )}
      </p>
    </>
  );
}

function Practice({
  t,
  go,
  q,
  draft,
  update,
  submit,
  bookmarked,
  bookmark,
  lang,
}: Props & {
  q: Sample;
  draft: Draft;
  update: (p: Partial<Draft>) => void;
  submit: () => void;
  bookmarked: boolean;
  bookmark: () => void;
  lang: "he" | "en";
}) {
  const [imageError, setImageError] = useState("");
  const [imageBusy, setImageBusy] = useState(false);
  function addImages(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    event.target.value = "";
    if (
      files.length + draft.images.length > 4 ||
      files.some(
        (f) =>
          !["image/png", "image/jpeg", "image/webp"].includes(f.type) ||
          f.size > 5 * 1024 * 1024,
      )
    ) {
      setImageError(
        t(
          "עד 4 תמונות מסוג PNG, JPG או WebP, עד 5MB לתמונה.",
          "Up to 4 PNG, JPG or WebP images, 5MB each.",
        ),
      );
      return;
    }
    setImageError("");
    setImageBusy(true);
    Promise.all(
      files.map(
        (file) =>
          new Promise<{ name: string; src: string }>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () =>
              resolve({ name: file.name, src: String(reader.result) });
            reader.onerror = reject;
            reader.readAsDataURL(file);
          }),
      ),
    )
      .then((images) =>
        update({ images: [...draft.images, ...images], submitted: false }),
      )
      .catch(() =>
        setImageError(
          t(
            "לא הצלחנו לקרוא את התמונה. נסו שוב.",
            "Could not read the image. Please try again.",
          ),
        ),
      )
      .finally(() => setImageBusy(false));
  }
  const hasAnswer =
    !!draft.text.trim() ||
    draft.code !== q.code ||
    draft.circuit.parts.length > 0 ||
    draft.images.length > 0;
  return (
    <>
      <div className={s.breadcrumb}>
        <button onClick={() => go("library")}>
          <ArrowRight size={16} />
          {t("מאגר השאלות", "Question library")}
        </button>
        <span>/</span>
        <span>{t(...q.topic)}</span>
      </div>
      <div className={s.pageHeading}>
        <div>
          <h1>{t(...q.title)}</h1>
          <Meta q={q} t={t} />
        </div>
        <button
          className={s.secondary}
          onClick={bookmark}
          aria-pressed={bookmarked}
        >
          <Bookmark size={17} fill={bookmarked ? "currentColor" : "none"} />
          {bookmarked ? t("נשמרה", "Saved") : t("שמירת שאלה", "Save question")}
        </button>
      </div>
      <div className={s.practiceGrid}>
        <section className={s.questionPane}>
          <div className={s.questionFacts}>
            <span>{t(...q.difficulty)}</span>
            <span>
              <Clock3 size={15} />
              {q.minutes} {t("דקות", "minutes")}
            </span>
          </div>
          <h2>{t("האתגר שלכם", "Your challenge")}</h2>
          <p className={s.prompt}>{t(...q.prompt)}</p>
          {q.id === "xor" && <CircuitMoment t={t} />}
          <details className={s.requirements}>
            <summary>{t("מה כדאי לכלול בתשובה", "What to include")}</summary>
            <ul>
              <li>
                {t(
                  "הנחות ונימוק לדרך שבחרתם",
                  "Assumptions and why you chose this approach",
                )}
              </li>
              <li>
                {t("מימוש או שרטוט ברור", "A clear implementation or diagram")}
              </li>
              <li>
                {t(
                  "בדיקה של המקרה הרגיל ומקרי הקצה",
                  "Normal cases and edge cases",
                )}
              </li>
            </ul>
          </details>
          <div className={s.hintArea}>
            <div className={s.sectionHeading}>
              <h3>{t("עוד כיוון למחשבה", "A little direction")}</h3>
              <span>{draft.hints} / 3</span>
            </div>
            {q.hints.slice(0, draft.hints).map((hint, i) => (
              <p key={i} className={s.hint}>
                <Lightbulb size={17} />
                <span>{t(...hint)}</span>
              </p>
            ))}
            <button
              className={s.secondary}
              disabled={draft.hints === 3}
              onClick={() => update({ hints: draft.hints + 1 })}
            >
              <Lightbulb size={17} />
              {draft.hints === 3
                ? t("כל הרמזים נפתחו", "All hints revealed")
                : draft.hints
                  ? t("הרמז הבא", "Next hint")
                  : t("אפשר רמז?", "Need a hint?")}
            </button>
            <p className={s.small}>
              {t(
                "הרמזים והחשיפה לפתרון יוצגו לצד הניסיון שלכם.",
                "Hints and solution exposure will appear alongside your attempt.",
              )}
            </p>
            <button
              className={s.textButton}
              aria-expanded={draft.solution}
              onClick={() =>
                update({ solution: !draft.solution, solutionSeen: true })
              }
            >
              {draft.solution
                ? t("הסתרת פתרון לדוגמה", "Hide example solution")
                : t("הצגת פתרון לדוגמה", "Reveal example solution")}
              <ChevronDown size={16} />
            </button>
            {draft.solution && (
              <div className={s.solution}>
                <h3>{t("דרך אפשרית לפתרון", "One possible approach")}</h3>
                <p dir="auto">{t(...q.solution)}</p>
              </div>
            )}
          </div>
          <Coach t={t} />
        </section>
        <section className={s.answerPane}>
          <div className={s.answerHeading}>
            <div>
              <h2>{t("המקום לחשוב בקול.", "Room to think out loud.")}</h2>
              <p>
                {t(
                  "כתבו, תכנתו או שרטטו את הדרך שלכם.",
                  "Write, code or sketch your reasoning.",
                )}
              </p>
            </div>
            <span className={s.draftBadge}>
              {t("טיוטה מקומית", "Local draft")}
            </span>
          </div>
          <div
            className={s.answerTabs}
            role="tablist"
            aria-label={t("סוג פתרון", "Answer format")}
          >
            {[
              { id: "text", icon: ListChecks, he: "הסבר", en: "Explain" },
              { id: "code", icon: Code2, he: "קוד", en: "Code" },
              { id: "circuit", icon: Cpu, he: "מעגל", en: "Circuit" },
              { id: "image", icon: FileImage, he: "תמונה", en: "Image" },
            ].map(({ id, icon: Icon, he, en }) => (
              <button
                key={id}
                role="tab"
                aria-selected={draft.tab === id}
                aria-controls={`answer-panel-${id}`}
                id={`answer-tab-${id}`}
                tabIndex={draft.tab === id ? 0 : -1}
                onKeyDown={(event) => {
                  const order = ["text", "code", "circuit", "image"];
                  let next = -1;
                  if (event.key === "Home") next = 0;
                  if (event.key === "End") next = 3;
                  if (event.key === "ArrowRight")
                    next = (order.indexOf(id) + (lang === "he" ? 3 : 1)) % 4;
                  if (event.key === "ArrowLeft")
                    next = (order.indexOf(id) + (lang === "he" ? 1 : 3)) % 4;
                  if (next >= 0) {
                    event.preventDefault();
                    update({ tab: order[next] });
                    document
                      .getElementById(`answer-tab-${order[next]}`)
                      ?.focus();
                  }
                }}
                onClick={() => update({ tab: id })}
              >
                <Icon size={17} />
                {t(he, en)}
              </button>
            ))}
          </div>
          <div
            role="tabpanel"
            id={`answer-panel-${draft.tab}`}
            aria-labelledby={`answer-tab-${draft.tab}`}
            className={s.answerContent}
          >
            {draft.tab === "text" ? (
              <>
                <label htmlFor="answer-text">
                  {t(
                    "ההנחות, הרעיון והבדיקה שלכם",
                    "Your assumptions, reasoning and checks",
                  )}
                </label>
                <textarea
                  id="answer-text"
                  value={draft.text}
                  onChange={(e) =>
                    update({ text: e.target.value, submitted: false })
                  }
                  placeholder={t("הייתי מתחיל/ה מ…", "I'd start by…")}
                  dir="auto"
                />
                <div className={s.writingGuide}>
                  <span>{t("הנחות", "Assumptions")}</span>
                  <ArrowLeft size={13} />
                  <span>{t("גישה", "Approach")}</span>
                  <ArrowLeft size={13} />
                  <span>{t("מימוש", "Implementation")}</span>
                  <ArrowLeft size={13} />
                  <span>{t("בדיקה", "Verification")}</span>
                </div>
              </>
            ) : draft.tab === "code" ? (
              <>
                <div className={s.codeToolbar}>
                  <label htmlFor="code-lang">{t("שפת קוד", "Language")}</label>
                  <select
                    id="code-lang"
                    value={draft.language}
                    onChange={(e) =>
                      update({ language: e.target.value as AnswerLanguage })
                    }
                  >
                    {[
                      "c",
                      "cpp",
                      "python",
                      "verilog",
                      "systemverilog",
                      "vhdl",
                      "javascript",
                    ].map((v) => (
                      <option key={v} value={v}>
                        {v === "cpp" ? "C++" : v === "c" ? "C" : v}
                      </option>
                    ))}
                  </select>
                  <span>
                    {t(
                      "עריכה בלבד · ללא הרצת קוד",
                      "Editor only · no code execution",
                    )}
                  </span>
                </div>
                <div className={s.codeFrame}>
                  <CodeEditor
                    value={draft.code}
                    language={draft.language}
                    disabled={false}
                    label={t("עורך קוד לתשובה", "Answer code editor")}
                    onChange={(code) => update({ code, submitted: false })}
                  />
                </div>
                <p id="code-keyboard-help" className={s.small}>
                  {t(
                    "Tab להזחה. Escape ואז Tab כדי לצאת מהעורך.",
                    "Tab indents. Press Escape, then Tab to leave the editor.",
                  )}
                </p>
              </>
            ) : draft.tab === "circuit" ? (
              <div className={s.circuitEditor}>
                <CircuitEditor
                  value={draft.circuit}
                  onChange={(circuit) => update({ circuit, submitted: false })}
                  lang={lang}
                />
              </div>
            ) : (
              <div className={s.upload}>
                <FileImage size={36} />
                <h3>
                  {t(
                    "לפעמים עט ונייר מספיקים.",
                    "Sometimes pen and paper are all you need.",
                  )}
                </h3>
                <p>
                  {t(
                    "בחרו צילום של הפתרון. התמונה תוצג רק בדפדפן הזה.",
                    "Choose a photo of your answer. It stays in this browser.",
                  )}
                </p>
                <label className={s.uploadButton}>
                  {t("בחירת תמונות", "Choose images")}
                  <Plus size={18} />
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/webp"
                    multiple
                    onChange={addImages}
                    disabled={imageBusy}
                  />
                </label>
                <small>
                  {t(
                    "עד 4 תמונות · עד 5MB לכל תמונה",
                    "Up to 4 images · 5MB each",
                  )}
                </small>
                {imageError && <p role="alert">{imageError}</p>}
                <div className={s.imageList}>
                  {draft.images.map((im, i) => (
                    <div key={`${im.name}-${i}`}>
                      <Image
                        src={im.src}
                        alt={im.name}
                        width={220}
                        height={160}
                        unoptimized
                      />
                      <span>{im.name}</span>
                      <button
                        onClick={() =>
                          update({
                            images: draft.images.filter((_, n) => n !== i),
                          })
                        }
                        aria-label={t("הסרת תמונה", "Remove image")}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className={s.submitBar}>
            <div>
              <span>
                <Lightbulb size={15} />
                {draft.hints} {t("רמזים נפתחו", "hints opened")}
              </span>
              <small>
                {draft.solutionSeen
                  ? t("הפתרון לדוגמה נצפה", "Example solution viewed")
                  : t("הפתרון עדיין לא נחשף", "Solution not revealed")}
              </small>
            </div>
            <Button onClick={submit} disabled={!hasAnswer}>
              {t("סיום והצגת משוב לדוגמה", "Finish & preview feedback")}
              <Check size={18} />
            </Button>
          </div>
          {draft.submitted && <Feedback t={t} go={go} q={q} draft={draft} />}
        </section>
      </div>
    </>
  );
}

function Coach({ t }: { t: T }) {
  const [open, setOpen] = useState(false),
    [message, setMessage] = useState(""),
    [sent, setSent] = useState(false);
  return (
    <section className={s.coach}>
      <button
        className={s.coachTitle}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
      >
        <span>
          <MessageSquare size={18} />
          {t("חושבים יחד", "Think it through")}
        </span>
        <ChevronDown size={18} />
      </button>
      <p>
        {t(
          "מקום לעוזר הלמידה האישי שלכם.",
          "A space for your personal learning assistant.",
        )}
      </p>
      {open && (
        <>
          <div className={s.coachMessage}>
            {t(
              "אפשר להתחיל ממה שכבר ברור לכם. מהו הקלט, ומה המוצא שתרצו לקבל?",
              "Start with what you already know. What is the input, and what output do you want?",
            )}
          </div>
          {sent && (
            <>
              <p className={s.userMessage} dir="auto">
                {message}
              </p>
              <div className={s.coachMessage}>
                {t(
                  "כדאי לבחור מקרה קטן ולבדוק אותו ידנית, ואז להסביר איזה עיקרון הוא מדגים.",
                  "Choose a small case and check it by hand, then explain the principle it illustrates.",
                )}
              </div>
            </>
          )}
          <div className={s.coachInput}>
            <input
              aria-label={t("הודעה לעוזר בהדמיה", "Message the demo coach")}
              placeholder={t("איפה נתקעתם?", "Where are you stuck?")}
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setSent(false);
              }}
            />
            <button
              disabled={!message.trim()}
              onClick={() => setSent(true)}
              aria-label={t("שליחת הודעת הדגמה", "Send demo message")}
            >
              <Send size={18} />
            </button>
          </div>
          <small>
            {t(
              "שיחה מוכנה להמחשה. לא מופעל מודל AI.",
              "Prewritten conversation example. No AI model is running.",
            )}
          </small>
        </>
      )}
    </section>
  );
}
function Feedback({ t, go, q, draft }: Props & { q: Sample; draft: Draft }) {
  const feedbackRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    feedbackRef.current?.scrollIntoView({
      block: "start",
      behavior: "instant",
    });
    feedbackRef.current?.focus({ preventScroll: true });
  }, []);
  return (
    <div
      ref={feedbackRef}
      tabIndex={-1}
      className={s.feedback}
      role="region"
      aria-label={t("משוב לדוגמה", "Sample feedback")}
    >
      <div className={s.feedbackHeading}>
        <CheckCheck size={24} />
        <h2>
          {t("הדרך שלכם, במבט נוסף.", "Your approach, with a fresh look.")}
        </h2>
      </div>
      <p className={s.demoFeedback}>
        {t(
          "משוב קבוע לדוגמה בלבד — אינו הערכה של התשובה שכתבתם.",
          "Fixed sample feedback — this is not an assessment of your answer.",
        )}
      </p>
      <div className={s.feedbackColumns}>
        <div>
          <h3>{t("מה עבד טוב", "What worked well")}</h3>
          <p>
            {t(
              "הפרדה ברורה בין ההנחות, דרך החשיבה ובדיקת הפתרון.",
              "Clear separation between assumptions, reasoning and verification.",
            )}
          </p>
        </div>
        <div>
          <h3>{t("מה אפשר לחדד", "What to refine")}</h3>
          <p>
            {t(
              "להוסיף מקרה קצה ולהסביר למה הפתרון נכון גם בו.",
              "Add an edge case and explain why the solution remains correct.",
            )}
          </p>
        </div>
      </div>
      <div className={s.feedbackSupport}>
        <span>
          {draft.hints} {t("רמזים", "hints")}
        </span>
        <span>
          {draft.solutionSeen
            ? t("נצפה פתרון", "Solution viewed")
            : t("ללא צפייה בפתרון", "No solution exposure")}
        </span>
        <span>
          {t(
            "הניסיון נוסף להיסטוריה המקומית",
            "Attempt added to local history",
          )}
        </span>
      </div>
      <details className={s.reference}>
        <summary>
          {t("השוואה לפתרון לדוגמה", "Compare with an example solution")}
        </summary>
        <p dir="auto">{t(...q.solution)}</p>
      </details>
      <button
        className={s.textButton}
        onClick={() => go("practice", q.id === "xor" ? "fsm" : "xor")}
      >
        {t("לשאלה הבאה", "Next question")}
        <ArrowLeft size={18} />
      </button>
    </div>
  );
}

function Progress({ t, go }: Props) {
  const skills = [
    ["לוגיקה קומבינטורית", "Combinational logic", 82, 35],
    ["מכונות מצבים", "State machines", 54, 25],
    ["תכנות ב־C", "C programming", 71, 42],
    ["הסבר ודרך חשיבה", "Explaining your reasoning", 68, 40],
  ] as const;
  return (
    <>
      <div className={s.pageHeading}>
        <div>
          <h1>{t("רואים את הדרך שעשיתם.", "See how far you've come.")}</h1>
          <p>
            {t(
              "התקדמות היא גם לדעת על מה לעבוד עכשיו.",
              "Progress also means knowing what to work on next.",
            )}
          </p>
        </div>
        <Button secondary onClick={() => go("history")}>
          <History size={17} />
          {t("היסטוריית תרגול", "Practice history")}
        </Button>
      </div>
      <p className={s.demoFeedback}>
        {t(
          "כל המדדים והציונים במסך הזה הם נתוני הדגמה.",
          "All metrics and scores on this screen are demonstration data.",
        )}
      </p>
      <div className={s.progressSummary}>
        <div>
          <strong>24</strong>
          <span>{t("תרגולים שהושלמו", "sessions completed")}</span>
        </div>
        <div>
          <strong>6</strong>
          <span>{t("שעות של מחשבה", "hours of focused work")}</span>
        </div>
        <div>
          <strong>3</strong>
          <span>{t("ימים ברצף", "day streak")}</span>
        </div>
        <div>
          <strong>8</strong>
          <span>{t("נושאים בתהליך", "topics in progress")}</span>
        </div>
      </div>
      <div className={s.progressLayout}>
        <section className={s.skillSection}>
          <div className={s.sectionHeading}>
            <h2>{t("הידע שלכם, לפי נושא", "Your knowledge, by topic")}</h2>
            <span>{t("תחילת הדרך / עכשיו", "Starting point / now")}</span>
          </div>
          {skills.map(([he, en, now, before]) => (
            <div className={s.skillRow} key={en}>
              <div>
                <strong>{t(he, en)}</strong>
                <span dir="ltr">
                  {before} → {now}
                </span>
              </div>
              <div
                className={s.skillTrack}
                role="img"
                aria-label={`${t(he, en)}: ${before} → ${now}`}
              >
                <i style={{ width: `${now}%` }} />
                <b style={{ left: `${before}%` }} />
              </div>
              <small>
                {now < 60
                  ? t("כדאי לתרגל שוב", "Worth revisiting")
                  : t("בסיס טוב, ממשיכים להעמיק", "A solid base to build on")}
              </small>
            </div>
          ))}
        </section>
        <aside className={s.progressNext}>
          <Target size={31} />
          <h2>{t("הצעד הבא כבר ברור.", "Your next step is clear.")}</h2>
          <p>
            {t(
              "במסלול לדוגמה, כדאי לחזק מכונות מצבים ולתרגל זיהוי רצפים חופפים.",
              "In this example plan, focus on state machines and overlapping sequence detection.",
            )}
          </p>
          <Button onClick={() => go("practice", "fsm")}>
            {t("לתרגול מכונות מצבים", "Practice state machines")}
            <ArrowLeft size={18} />
          </Button>
          <div className={s.miniCalendar}>
            <h3>{t("השבוע בתמונה", "This week at a glance")}</h3>
            <div>
              {[2, 4, 0, 3, 1, 0, 0].map((n, i) => (
                <span key={i}>
                  <b style={{ height: `${14 + n * 13}px` }} />
                  <small>
                    {t(
                      ["א", "ב", "ג", "ד", "ה", "ו", "ש"][i],
                      ["S", "M", "T", "W", "T", "F", "S"][i],
                    )}
                  </small>
                </span>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </>
  );
}

function HistoryScreen({
  t,
  go,
  recent,
  drafts,
}: Props & { recent: string[]; drafts: Record<string, Draft> }) {
  return (
    <>
      <div className={s.pageHeading}>
        <div>
          <h1>{t("לכל ניסיון יש המשך.", "Every attempt leads somewhere.")}</h1>
          <p>
            {t(
              "חוזרים לפתרון, בודקים את הדרך ומנסים שוב.",
              "Revisit your answer, review the reasoning and try again.",
            )}
          </p>
        </div>
        <Button secondary onClick={() => go("progress")}>
          {t("לתמונת ההתקדמות", "View progress")}
          <TrendingUp size={17} />
        </Button>
      </div>
      <div className={s.historyList}>
        {recent.map((id, i) => {
          const q = questions.find((q) => q.id === id)!;
          return (
            <article key={id}>
              <div className={s.historyDate}>
                <span>
                  {drafts[id]?.submitted
                    ? t("עכשיו", "Just now")
                    : t("השבוע", "This week")}
                </span>
                <small>{t("נתוני הדגמה", "Demo data")}</small>
              </div>
              <div>
                <h2>{t(...q.title)}</h2>
                <Meta q={q} t={t} />
                <p>
                  {drafts[id]?.submitted
                    ? t(
                        `${drafts[id].hints} רמזים · ניסיון מקומי חדש`,
                        `${drafts[id].hints} hints · new local attempt`,
                      )
                    : t(
                        i ? "נפתר עם רמז אחד" : "ניסיון לדוגמה ללא רמזים",
                        i
                          ? "Solved with one hint"
                          : "Example attempt without hints",
                      )}
                </p>
              </div>
              <Button secondary onClick={() => go("practice", id)}>
                {t("חזרה לתרגול", "Revisit")}
                <ArrowLeft size={17} />
              </Button>
            </article>
          );
        })}
      </div>
    </>
  );
}

function Interview({ t, go }: Props) {
  const [started, setStarted] = useState(false),
    [step, setStep] = useState(0),
    [answer, setAnswer] = useState(""),
    [answers, setAnswers] = useState<string[]>([]),
    [done, setDone] = useState(false),
    [duration, setDuration] = useState("20");
  const prompts = [
    [
      "ספרו על פרויקט טכני שעבדתם עליו. מה הייתה האחריות שלכם ומה היה האתגר המרכזי?",
      "Tell me about a technical project. What was your responsibility and the main challenge?",
    ],
    [
      "איך בדקתם שהפתרון שלכם עובד? תנו דוגמה למקרה קצה שמצאתם.",
      "How did you test your solution? Describe an edge case you found.",
    ],
    [
      "אם הייתם מתחילים מחדש, איזו החלטה תכנונית הייתם משנים ולמה?",
      "If you started again, what design decision would you change, and why?",
    ],
  ] as const;
  return (
    <>
      <div className={s.pageHeading}>
        <div>
          <h1>{t("עכשיו, בואו נדבר על זה.", "Now, let's talk it through.")}</h1>
          <p>
            {t(
              "ראיון כתוב, בקצב שלכם. מקום לתרגל ידע וגם את הדרך להציג אותו.",
              "A written interview at your own pace. Practice your knowledge and how you present it.",
            )}
          </p>
        </div>
      </div>
      {!started ? (
        <div className={s.interviewLobby}>
          <section>
            <div className={s.interviewSymbol}>
              <MessageSquare size={54} />
              <span>
                <Cpu size={25} />
              </span>
            </div>
            <h2>
              {t(
                "הידע שלכם הוא רק ההתחלה.",
                "What you know is just the beginning.",
              )}
            </h2>
            <p>
              {t(
                "נפתח בהיכרות עם פרויקט, נעמיק בדרך החשיבה ונסיים ברפלקציה קצרה.",
                "Start with a project, explore your reasoning and finish with a short reflection.",
              )}
            </p>
            <ul>
              <li>
                {t(
                  "שיחה כתובה בעברית או באנגלית",
                  "Written conversation in Hebrew or English",
                )}
              </li>
              <li>
                {t(
                  "שאלות טכניות והתנהגותיות",
                  "Technical and behavioral prompts",
                )}
              </li>
              <li>
                {t("סיכום מסודר בסיום", "A structured summary at the end")}
              </li>
            </ul>
          </section>
          <section className={s.interviewSetup}>
            <h2>{t("מכינים את החדר.", "Set the scene.")}</h2>
            <label>
              {t("התחום שלכם", "Your track")}
              <select>
                <option>
                  {t(
                    "תכנון דיגיטלי — סטודנטים וג׳וניורים",
                    "Digital design — students & juniors",
                  )}
                </option>
                <option>
                  {t("תכנות ואלגוריתמים", "Programming & algorithms")}
                </option>
              </select>
            </label>
            <label>
              {t("משך ראיון מתוכנן", "Planned interview duration")}
              <select
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              >
                <option value="10">10 {t("דקות", "minutes")}</option>
                <option value="20">20 {t("דקות", "minutes")}</option>
                <option value="30">30 {t("דקות", "minutes")}</option>
              </select>
            </label>
            <Button onClick={() => setStarted(true)}>
              {t("כניסה לראיון לדוגמה", "Start the sample interview")}
              <Play size={18} />
            </Button>
            <small>
              {t(
                "שלוש שאלות מוכנות מראש. אין מודל AI, טיימר פעיל או הקלטה.",
                "Three prewritten prompts. No AI model, active timer or recording.",
              )}
            </small>
          </section>
        </div>
      ) : done ? (
        <section className={s.interviewDone}>
          <CheckCheck size={45} />
          <h2>
            {t("נתתם למחשבה מילים.", "You put your thinking into words.")}
          </h2>
          <p>
            {t(
              "הראיון לדוגמה הושלם. זה המקום שבו יוצג סיכום אישי לאחר חיבור המערכת.",
              "Sample interview complete. A personal summary would appear here in the connected product.",
            )}
          </p>
          {prompts.map((p, i) => (
            <details key={i}>
              <summary>{t(p[0], p[1])}</summary>
              <p dir="auto">{answers[i]}</p>
            </details>
          ))}
          <div className={s.heroActions}>
            <Button onClick={() => go("progress")}>
              {t("להתקדמות שלי", "View my progress")}
              <ArrowLeft size={18} />
            </Button>
            <Button
              secondary
              onClick={() => {
                setStarted(false);
                setDone(false);
                setStep(0);
                setAnswers([]);
              }}
            >
              {t("ראיון נוסף", "Another interview")}
            </Button>
          </div>
        </section>
      ) : (
        <section className={s.interviewRoom}>
          <div className={s.interviewRail}>
            <span>
              <span className={s.liveDot} />
              {t("ראיון לדוגמה", "Sample interview")}
            </span>
            <span>{step + 1} / 3</span>
            <span>
              {duration} {t("דקות בתכנון", "planned minutes")}
            </span>
          </div>
          <div className={s.interviewer}>
            <div>
              <MessageSquare size={23} />
            </div>
            <p>{t(prompts[step][0], prompts[step][1])}</p>
          </div>
          <label htmlFor="interview-answer">
            {t("התשובה שלכם", "Your answer")}
          </label>
          <textarea
            id="interview-answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder={t("בפרויקט שלי…", "In my project…")}
            dir="auto"
          />
          <div className={s.submitBar}>
            <small>
              {t(
                "התוכן נשאר בהדמיה בלבד.",
                "Your content stays in the simulation.",
              )}
            </small>
            <Button
              disabled={!answer.trim()}
              onClick={() => {
                setAnswers((old) => [...old, answer]);
                setAnswer("");
                if (step === 2) setDone(true);
                else setStep(step + 1);
              }}
            >
              {step === 2
                ? t("סיום הראיון", "Finish interview")
                : t("לשאלה הבאה", "Next question")}
              <ArrowLeft size={18} />
            </Button>
          </div>
        </section>
      )}
    </>
  );
}

type Goal = {
  role: string;
  minutes: number;
  level: string;
  name: string;
  reminders: boolean;
};
function Profile({
  t,
  go,
  onboarding,
  goal,
  setGoal,
  notice,
  save,
}: Props & {
  onboarding: boolean;
  goal: Goal;
  setGoal: (v: Goal) => void;
  notice: string;
  save: () => void;
}) {
  return (
    <>
      <div className={s.pageHeading}>
        <div>
          <h1>
            {onboarding
              ? t("לאן תרצו להגיע?", "Where do you want to go?")
              : t("מרחב הלמידה שלכם.", "Your learning space.")}
          </h1>
          <p>
            {t(
              "כמה פרטים קטנים, כדי להתחיל בכיוון הנכון.",
              "A few details to start in the right direction.",
            )}
          </p>
        </div>
      </div>
      <div className={s.profileLayout}>
        <section className={s.profileForm}>
          <h2>{t("הכיוון המקצועי", "Your professional direction")}</h2>
          <label>
            {t("שם לתצוגה", "Display name")}
            <input
              value={goal.name}
              onChange={(e) => setGoal({ ...goal, name: e.target.value })}
            />
          </label>
          <label>
            {t("התחום שמעניין אותי", "I'm interested in")}
            <select
              value={goal.role}
              onChange={(e) => setGoal({ ...goal, role: e.target.value })}
            >
              <option value="digital">
                {t("תכנון דיגיטלי וחומרה", "Digital design & hardware")}
              </option>
              <option value="embedded">
                {t("תוכנה משובצת", "Embedded software")}
              </option>
              <option value="software">
                {t("תוכנה ואלגוריתמים", "Software & algorithms")}
              </option>
            </select>
          </label>
          <label>
            {t("איפה אני בדרך", "Where I am today")}
            <select
              value={goal.level}
              onChange={(e) => setGoal({ ...goal, level: e.target.value })}
            >
              <option value="student">{t("סטודנט/ית", "Student")}</option>
              <option value="graduate">
                {t("בוגר/ת טרי/ה", "Recent graduate")}
              </option>
              <option value="junior">
                {t("ג׳וניור/ית", "Junior engineer")}
              </option>
            </select>
          </label>
          <fieldset>
            <legend>{t("זמן יומי שמתאים לי", "My daily practice time")}</legend>
            <div className={s.segmented}>
              {[15, 25, 40].map((n) => (
                <button
                  key={n}
                  aria-pressed={goal.minutes === n}
                  onClick={() => setGoal({ ...goal, minutes: n })}
                >
                  {n} {t("דקות", "min")}
                </button>
              ))}
            </div>
          </fieldset>
          <label className={s.switchLabel}>
            <span>
              <strong>
                {t("תזכורת קטנה לתרגל", "A gentle practice reminder")}
              </strong>
              <small>
                {t(
                  "תצוגה בלבד — לא יישלחו הודעות",
                  "Preview only — no messages are sent",
                )}
              </small>
            </span>
            <input
              type="checkbox"
              role="switch"
              checked={goal.reminders}
              onChange={(e) =>
                setGoal({ ...goal, reminders: e.target.checked })
              }
            />
          </label>
          <Button onClick={save}>
            {onboarding
              ? t("בואו נתחיל", "Let's begin")
              : t("שמירת העדפות בהדמיה", "Save demo preferences")}
            <ArrowLeft size={18} />
          </Button>
          {notice && (
            <p role="status" className={s.savedNotice}>
              {notice}
            </p>
          )}
        </section>
        <aside className={s.profileAside}>
          <Target size={40} />
          <h2>
            {t("קצת בכל יום.", "A little, every day.")}
            <br />
            <em>{t("הרבה לאורך הדרך.", "A lot, along the way.")}</em>
          </h2>
          <p>
            {t(
              "הדרך לראיון לא חייבת להתחיל ממרתון. שאלה אחת עם מחשבה טובה היא התחלה מצוינת.",
              "Interview preparation doesn't have to start with a marathon. One thoughtful answer is an excellent beginning.",
            )}
          </p>
          <button className={s.textButton} onClick={() => go("library")}>
            {t("אפשר גם פשוט להתחיל משאלה", "Or start with a question")}
            <ArrowLeft size={17} />
          </button>
        </aside>
      </div>
    </>
  );
}

function AuthScreen({ t, go }: Props) {
  const [register, setRegister] = useState(false);
  return (
    <div className={s.authLayout}>
      <section>
        <h1>
          {t("יש מקום", "There's room")}
          <br />
          <em>{t("לצעד הבא שלכם.", "for your next step.")}</em>
        </h1>
        <p>
          {t(
            "ללמוד מהניסיון, לשמור את הדרך ולהגיע לראיון עם ביטחון.",
            "Learn from experience, keep your progress and arrive with confidence.",
          )}
        </p>
        <CircuitMoment t={t} />
      </section>
      <section className={s.authForm}>
        <h2>
          {register
            ? t("מתחילים דרך חדשה.", "Start a new journey.")
            : t("טוב שחזרתם.", "Welcome back.")}
        </h2>
        <p>
          {t(
            "הדמיית מסך כניסה. אין צורך בפרטים אמיתיים.",
            "Sign-in preview. No real personal details needed.",
          )}
        </p>
        <label>
          {t("אימייל לדוגמה", "Example email")}
          <input type="email" value="learner@example.com" readOnly dir="ltr" />
        </label>
        <label>
          {t("סיסמה לדוגמה", "Example password")}
          <input type="password" value="demo-only" readOnly dir="ltr" />
        </label>
        <Button onClick={() => go(register ? "goal" : "today")}>
          {register
            ? t("הרשמה לדוגמה", "Preview registration")
            : t("כניסה להדמיה", "Enter the simulation")}
          <ArrowLeft size={18} />
        </Button>
        <button className={s.textButton} onClick={() => setRegister(!register)}>
          {register
            ? t("כבר יש לי חשבון", "I already have an account")
            : t("עוד אין לי חשבון", "Create an account")}
        </button>
        <small>
          {t(
            "אין אימות, יצירת חשבון או שליחת מידע.",
            "No authentication, account creation or data transmission.",
          )}
        </small>
      </section>
    </div>
  );
}
function Help({ t, go }: Props) {
  return (
    <section className={s.help}>
      <h1>{t("כמה דברים שכדאי לדעת.", "A few things worth knowing.")}</h1>
      {[
        [
          "מה אפשר לנסות כאן?",
          "What can I try here?",
          "לעבור בין כל המסכים, לחפש שאלות, לכתוב תשובות, לנסות רמזים, לערוך קוד ולשרטט מעגלים.",
          "Navigate every screen, search questions, write answers, reveal hints, edit code and draw circuits.",
        ],
        [
          "האם התשובות נשמרות?",
          "Are answers saved?",
          "רק בזיכרון הדפדפן בזמן ההדמיה. אפשר להחליף מסך ומצב צבע בלי לאבד טיוטה, אבל רענון מאפס אותה.",
          "Only in browser memory during this simulation. Screens and color modes preserve drafts, but reloading resets them.",
        ],
        [
          "האם המשוב נוצר באמצעות AI?",
          "Is feedback generated by AI?",
          "לא. המשוב והשיחה עם העוזר הם טקסטים קבועים שממחישים את העיצוב. אין הערכה אמיתית של התשובה.",
          "No. Feedback and coach replies are fixed examples showing the design. Your answer is not assessed.",
        ],
        [
          "מה קורה לתמונות שבחרתי?",
          "What happens to selected images?",
          "התמונות נקראות ומוצגות בדפדפן בלבד. הן לא עולות לשרת.",
          "Images are read and displayed locally in the browser. They are never uploaded.",
        ],
        [
          "איך משווים בין העיצובים?",
          "How do I compare designs?",
          "חוזרים לגלריה ובוחרים סגנון. באפשרות יון בהיר–כהה, כפתור השמש או הירח משנה את כל המסכים.",
          "Return to the gallery and choose a style. In adaptive Ion, the sun/moon control changes every screen.",
        ],
      ].map(([he, en, a, b]) => (
        <details key={en}>
          <summary>{t(he, en)}</summary>
          <p>{t(a, b)}</p>
        </details>
      ))}
      <Button onClick={() => go("library")}>
        {t("חזרה לשאלות", "Back to questions")}
        <ArrowLeft size={17} />
      </Button>
    </section>
  );
}
