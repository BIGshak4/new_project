"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  BookOpen,
  BarChart3,
  History,
  Search,
  Bookmark,
  LogOut,
  ArrowUpRight,
  RotateCcw,
} from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { readQuestionCache, writeQuestionCache } from "../lib/question-cache";
import { Auth, type Lang } from "../components/auth";
import { PracticeSession } from "../components/practice-session";
import { supabase } from "../lib/supabase";
import {
  practiceApi,
  type Progress,
  type QuestionSummary,
} from "../lib/practice-api";
import {
  apiMessage,
  bandLabel,
  subjectLabel,
  mergeEntries,
  type Entry,
} from "../lib/practice-ui";

type Route = { view: string; question?: string; attempt?: string };
const emptyProgress: Progress = {
  skills: [],
  recent: [],
  attempts_today: 0,
  daily_limit: 30,
};
function currentRoute(): Route {
  const q = new URLSearchParams(window.location.search);
  return {
    view: q.get("view") ?? "library",
    question: q.get("question") ?? undefined,
    attempt: q.get("attempt") ?? undefined,
  };
}

export default function Page() {
  const [lang, setLang] = useState<Lang>("he");
  useEffect(() => {
    try {
      if (localStorage.getItem("jobrun-language") === "en") setLang("en");
    } catch {}
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
    try {
      localStorage.setItem("jobrun-language", lang);
    } catch {}
  }, [lang]);
  const languageControl = (
    <button
      className="language-switch"
      dir="ltr"
      onClick={() => setLang(lang === "he" ? "en" : "he")}
      aria-label={lang === "he" ? "החלפה לאנגלית" : "Switch to Hebrew"}
      title={lang === "he" ? "החלפה לאנגלית" : "Switch to Hebrew"}
    >
      {lang === "he" ? "EN" : "עב"}
    </button>
  );
  return (
    <Auth lang={lang} kind="practice" controls={languageControl}>
      {(user, signOut) => (
        <Workspace
          key={user.id}
          user={user}
          signOut={signOut}
          lang={lang}
          languageControl={languageControl}
        />
      )}
    </Auth>
  );
}

function Workspace({
  user,
  signOut,
  lang,
  languageControl,
}: {
  user: User;
  signOut: () => void;
  lang: Lang;
  languageControl: React.ReactNode;
}) {
  const t = (he: string, en: string) => (lang === "he" ? he : en);
  const [api] = useState(() => practiceApi());
  const [route, setRoute] = useState<Route>({ view: "library" });
  const [questions, setQuestions] = useState<QuestionSummary[]>([]);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [progress, setProgress] = useState<Progress>(emptyProgress);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [demo, setDemo] = useState(true),
    [healthKnown, setHealthKnown] = useState(false);
  const [query, setQuery] = useState(""),
    [subject, setSubject] = useState("all");
  const generation = useRef(0);
  const [progressReady, setProgressReady] = useState(false);
  const [entriesReady, setEntriesReady] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [progressLoading, setProgressLoading] = useState(true);
  const [entriesLoading, setEntriesLoading] = useState(true);
  const [cachedQuestions, setCachedQuestions] = useState(false);

  useEffect(() => {
    const sync = () => setRoute(currentRoute());
    sync();
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  const navigate = useCallback((next: Route, replace = false) => {
    const q = new URLSearchParams();
    if (next.view !== "library") q.set("view", next.view);
    if (next.attempt) q.set("attempt", next.attempt);
    else if (next.question) q.set("question", next.question);
    window.history[replace ? "replaceState" : "pushState"](
      {},
      "",
      q.size ? `?${q}` : window.location.pathname,
    );
    setRoute(next);
  }, []);

  const load = useCallback(async () => {
    const version = ++generation.current;
    const current = () => version === generation.current;
    const cached = readQuestionCache(user.id, lang);
    setQuestions(cached ?? []);
    setLoading(!cached);
    setRefreshing(!!cached);
    setCachedQuestions(!!cached);
    setProgressLoading(true);
    setEntriesLoading(true);
    setProgressReady(false);
    setEntriesReady(false);
    setError("");
    const report = (e: unknown) => {
      if (current()) setError(apiMessage(e, lang));
    };
    // Each section becomes usable independently; progress and health never block the bank.
    await Promise.allSettled([
      api
        .listQuestions(lang)
        .then((bank) => {
          if (!current()) return;
          setQuestions(bank);
          setCachedQuestions(false);
          writeQuestionCache(user.id, lang, bank);
        })
        .catch(report)
        .finally(() => {
          if (current()) {
            setLoading(false);
            setRefreshing(false);
          }
        }),
      api
        .progress()
        .then((p) => {
          if (current()) {
            setProgress(p);
            setProgressReady(true);
          }
        })
        .catch(report)
        .finally(() => {
          if (current()) setProgressLoading(false);
        }),
      Promise.resolve(
        supabase
          .from("jr_practice_entries")
          .select(
            "id,user_id,question_id,answer,self_rating,bookmarked,completed,version",
          )
          .eq("user_id", user.id),
      )
        .then((saved) => {
          if (!current()) return;
          if (saved.error) throw saved.error;
          setEntries((old) => mergeEntries(old, saved.data ?? []));
          setEntriesReady(true);
        })
        .catch(report)
        .finally(() => {
          if (current()) setEntriesLoading(false);
        }),
      api
        .health()
        .then((health) => {
          if (!current()) return;
          setDemo(health.llm_provider !== "anthropic");
          setHealthKnown(true);
        })
        .catch(report),
    ]);
  }, [api, lang, user.id]);
  useEffect(() => {
    void load();
    return () => {
      generation.current++;
    };
  }, [load]);
  const refreshProgress = useCallback(() => {
    api
      .progress()
      .then(setProgress)
      .catch(() => {});
  }, [api]);
  const onSaved = (entry: Entry) =>
    setEntries((old) => mergeEntries(old, [entry]));
  const active = !!(route.question || route.attempt);
  const topics = [...new Set(questions.map((q) => q.subject))];
  const filtered = questions.filter(
    (q) =>
      (subject === "all" || q.subject === subject) &&
      `${q.title} ${subjectLabel(q.subject, lang)}`
        .toLowerCase()
        .includes(query.toLowerCase()) &&
      (route.view !== "bookmarks" ||
        entries.some((e) => e.question_id === q.id && e.bookmarked)),
  );
  const daily = questions.length
    ? questions[Math.floor(Date.now() / 86400000) % questions.length]
    : null;
  const openQuestion = (q: QuestionSummary) =>
    navigate({ view: route.view, question: q.key });
  const date = (s: string) =>
    new Date(s).toLocaleString(lang === "he" ? "he-IL" : "en-GB", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  const recentKeys = new Set(progress.recent.map((a) => a.question_key));

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a href="/" className="wordmark" dir="ltr">
          JobRun
          <span className="logo-dot" />
        </a>
        <nav>
          {[
            {
              id: "library",
              icon: BookOpen,
              label: t("מאגר השאלות", "Question library"),
            },
            {
              id: "history",
              icon: History,
              label: t("התרגול שלי", "My practice"),
            },
            {
              id: "bookmarks",
              icon: Bookmark,
              label: t("שמורים להמשך", "Saved questions"),
            },
            {
              id: "progress",
              icon: BarChart3,
              label: t("ההתקדמות שלי", "My progress"),
            },
          ].map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              className={`nav-item ${route.view === id ? "active" : ""}`}
              aria-current={route.view === id ? "page" : undefined}
              onClick={() => {
                navigate({ view: id });
                refreshProgress();
              }}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            {t(
              "צעד קטן בכל יום. עוד שאלה, עוד דרך לחשוב.",
              "A little each day. One more question. Another way to think.",
            )}
          </div>
          <a className="small" href="https://jobrun-tasks.netlify.app">
            {t("לוח המייסדים", "Founder board")} <ArrowUpRight size={13} />
          </a>
        </div>
      </aside>
      <div className="shell-main">
        <header className="topbar">
          <span className="topbar-label">
            {t("סביבת התרגול שלכם", "Your practice workspace")}
          </span>
          <div className="topbar-actions">
            {languageControl}
            <button
              className="icon-button"
              aria-label={t("יציאה", "Sign out")}
              onClick={signOut}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main className="content">
          <div className="pilot-note" role="note">
            {!healthKnown
              ? t(
                  "בודקים את מצב סביבת התרגול…",
                  "Checking the practice environment…",
                )
              : demo
                ? t(
                    "פיילוט · עוזר התרגול עדיין אינו מחובר. אפשר לפתור שאלות ולהיעזר ברמזים. הפתרונות נשמרים; השאלות בביקורת מקצועית.",
                    "Pilot · The practice assistant is not connected yet. Solve questions and use hints; your answers are saved. Questions are under review.",
                  )
                : t(
                    "פיילוט פרטי · משוב אוטומטי עשוי לטעות. השוו לפתרון ובדקו עם איש מקצוע.",
                    "Private pilot · Automated feedback can be wrong. Compare with the reference and review with an expert.",
                  )}
          </div>
          {active ? (
            <PracticeSession
              key={route.attempt ?? route.question}
              api={api}
              questionKey={route.question}
              attemptId={route.attempt}
              lang={lang}
              user={user}
              entries={entries}
              onSaved={onSaved}
              onStarted={(id) =>
                navigate({ view: route.view, attempt: id }, true)
              }
              onNew={(key) => navigate({ view: route.view, question: key })}
              onBack={() => {
                navigate({ view: route.view });
                refreshProgress();
              }}
              onProgress={refreshProgress}
              demo={demo}
            />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    {route.view === "history"
                      ? t(
                          "ממשיכים מאיפה שעצרנו.",
                          "Pick up where you left off.",
                        )
                      : route.view === "progress"
                        ? t("רואים את הדרך.", "See how far you’ve come.")
                        : route.view === "bookmarks"
                          ? t("שווה לחזור אליהן.", "Worth coming back to.")
                          : t("בואו נחשוב על זה.", "Let’s think it through.")}
                  </h1>
                  <p>
                    {t(
                      "תרגול ממוקד לראיונות חומרה ותוכנה. בקצב שלכם.",
                      "Focused hardware and software interview practice. At your pace.",
                    )}
                  </p>
                </div>
              </div>
              <div className="summary-strip">
                <span>
                  <strong>{loading ? "—" : questions.length}</strong>
                  {t("שאלות במאגר", "questions")}
                </span>
                <span>
                  <strong>
                    {progressReady
                      ? `${progress.attempts_today} / ${progress.daily_limit}`
                      : "—"}
                  </strong>
                  {t("תרגולים שנפתחו היום", "attempts started today")}
                </span>
                <span>
                  <strong>
                    {entriesReady
                      ? entries.filter((e) => e.bookmarked).length
                      : "—"}
                  </strong>
                  {t("שמורים", "saved")}
                </span>
              </div>
              {error && (
                <div className="notice error" role="alert">
                  {error}
                  <button onClick={() => void load()}>
                    <RotateCcw size={15} />
                    {t("ניסיון נוסף", "Retry")}
                  </button>
                </div>
              )}
              {cachedQuestions && (
                <p className="muted small" role="status">
                  {refreshing
                    ? t(
                        "מציגים את הרשימה מהביקור האחרון ומעדכנים אותה ברקע…",
                        "Showing your last question list while refreshing in the background…",
                      )
                    : t(
                        "זו הרשימה מהביקור האחרון. נסו לרענן כדי לוודא שהיא עדכנית.",
                        "This is your last saved list. Retry to check for updates.",
                      )}
                </p>
              )}
              {loading ||
              ((route.view === "progress" || route.view === "history") &&
                progressLoading) ||
              (route.view === "bookmarks" && entriesLoading) ? (
                <div className="loading" role="status">
                  {t(
                    "טוענים את התרגול… אחרי הפסקה השרת עשוי להזדקק לכדקה.",
                    "Loading practice… after a pause the server may need about a minute.",
                  )}
                </div>
              ) : ((route.view === "progress" || route.view === "history") &&
                  !progressReady) ||
                (route.view === "bookmarks" &&
                  !entriesReady) ? null : route.view === "progress" && demo ? (
                <div className="empty-column">
                  <h2>
                    {t(
                      "הערכת המיומנויות תחובר בהמשך",
                      "Skill assessment is coming later",
                    )}
                  </h2>
                  <p>
                    {t(
                      "הפתרונות והרמזים שביקשתם נשמרים. אחרי חיבור העוזר נוכל להציג כאן הערכה מקצועית; כרגע לא מוצגים ציוני הדגמה.",
                      "Your solutions and hint usage are saved. Once the assistant is connected, skill assessments can appear here. Demo scores are hidden.",
                    )}
                  </p>
                </div>
              ) : route.view === "progress" ? (
                <>
                  <h2>
                    {demo
                      ? t("מדדי הדגמה", "Demo metrics")
                      : t("המיומנויות שלי", "My skills")}
                  </h2>
                  <p className="muted">
                    {t(
                      "דיווח עצמי, סימניות והשלמת תרגול נשמרים בנפרד מהערכת המיומנויות.",
                      "Self-ratings, bookmarks and completion are separate from skill assessments.",
                    )}
                  </p>
                  <div className="question-table">
                    {progress.skills.map((s) => (
                      <div className="progress-row" key={s.key}>
                        <div>
                          <h3 dir="auto">{s.label}</h3>
                          <p className="muted small">
                            {s.status === "not_assessed"
                              ? t("טרם נאספו תשובות", "No evidence yet")
                              : s.status === "insufficient_evidence"
                                ? t(
                                    "הערכה ראשונית · נדרשות עוד תשובות",
                                    "Provisional · more answers needed",
                                  )
                                : t(
                                    "מבוסס על תרגולים שנשלחו",
                                    "Based on submitted practice",
                                  )}
                          </p>
                        </div>
                        <div>
                          <span className="badge">
                            {s.level === null
                              ? t("טרם הוערך", "Not assessed")
                              : `${s.level} / 5`}
                          </span>
                          <p className="small muted">
                            {s.trend === "improving"
                              ? t("מגמת שיפור", "Improving")
                              : s.trend === "declining"
                                ? t("נדרש חיזוק", "Needs reinforcement")
                                : s.trend === "new"
                                  ? t("מדידה חדשה", "New measurement")
                                  : t("יציב", "Stable")}
                          </p>
                        </div>
                        <span className="small">
                          {s.assessments} {t("הערכות", "assessments")}
                        </span>
                      </div>
                    ))}
                  </div>
                  {!progress.skills.length && (
                    <div className="empty-column">
                      {t(
                        "אחרי שליחת התשובה הראשונה יופיעו כאן מדדים.",
                        "Metrics appear after your first submission.",
                      )}
                    </div>
                  )}
                </>
              ) : route.view === "history" ? (
                <>
                  <h2>{t("תרגולים אחרונים", "Recent attempts")}</h2>
                  <div className="question-table">
                    {progress.recent.map((a) => (
                      <button
                        className="question-row history-row"
                        key={a.id}
                        onClick={() =>
                          navigate({ view: "history", attempt: a.id })
                        }
                      >
                        <History size={18} />
                        <div>
                          <h3>
                            {questions.find((q) => q.key === a.question_key)
                              ?.title ?? a.question_key}
                          </h3>
                          <span className="topic">
                            {date(a.started_at)} ·{" "}
                            {a.language === "he"
                              ? t("עברית", "Hebrew")
                              : t("אנגלית", "English")}
                          </span>
                        </div>
                        <span className="badge">
                          {demo
                            ? t("תרגול שמור", "Saved practice")
                            : bandLabel(a.band, lang)}
                        </span>
                      </button>
                    ))}
                  </div>
                  {!progress.recent.length && (
                    <div className="empty-column">
                      {t(
                        "עוד לא פתחתם תרגול. בחרו שאלה מהמאגר כדי להתחיל.",
                        "No attempts yet. Pick a question from the library.",
                      )}
                    </div>
                  )}
                  {entries.some((e) => e.answer || e.completed) && (
                    <details className="legacy-practice">
                      <summary>
                        {t(
                          "טיוטות ותרגולים מהגרסה הקודמת",
                          "Drafts and practice from the earlier version",
                        )}
                      </summary>
                      {questions
                        .filter((q) =>
                          entries.some(
                            (e) =>
                              e.question_id === q.id &&
                              (e.answer || e.completed),
                          ),
                        )
                        .map((q) => (
                          <button
                            className="question-row history-row"
                            key={q.id}
                            onClick={() => openQuestion(q)}
                          >
                            <BookOpen size={17} />
                            <div>
                              <h3>{q.title}</h3>
                              <span className="topic">
                                {t(
                                  "הדיווח העצמי נשמר · ללא הערכה אוטומטית",
                                  "Self-assessment saved · no automated evaluation",
                                )}
                              </span>
                            </div>
                          </button>
                        ))}
                    </details>
                  )}
                </>
              ) : (
                <>
                  {route.view === "library" && daily && (
                    <section className="daily-panel">
                      <div>
                        <h2>{t("שאלה אחת להיום", "One question for today")}</h2>
                        <p>
                          {daily.title} · {daily.estimated_minutes ?? "—"}{" "}
                          {t("דקות", "min")}
                        </p>
                      </div>
                      <button
                        className="primary"
                        onClick={() => openQuestion(daily)}
                      >
                        {t("מתחילים לתרגל", "Start practicing")}
                      </button>
                    </section>
                  )}
                  <div className="toolbar">
                    <div className="search">
                      <Search size={17} />
                      <input
                        aria-label={t("חיפוש שאלות", "Search questions")}
                        placeholder={t(
                          "חפשו שאלה או נושא…",
                          "Search a question or topic…",
                        )}
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                      />
                    </div>
                    <select
                      aria-label={t("נושא", "Topic")}
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                    >
                      <option value="all">
                        {t("כל הנושאים", "All topics")}
                      </option>
                      {topics.map((s) => (
                        <option key={s} value={s}>
                          {subjectLabel(s, lang)}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="question-table">
                    {filtered.map((q, i) => (
                      <button
                        className="question-row"
                        key={q.id}
                        onClick={() => openQuestion(q)}
                      >
                        <span className="q-num">
                          {String(i + 1).padStart(2, "0")}
                        </span>
                        <div>
                          <h3>{q.title}</h3>
                          <span className="topic">
                            {subjectLabel(q.subject, lang)}
                            {entries.some(
                              (e) => e.question_id === q.id && e.bookmarked,
                            )
                              ? " · " + t("שמורה", "Saved")
                              : ""}
                          </span>
                        </div>
                        <span className="q-category small muted">
                          {recentKeys.has(q.key)
                            ? t("תרגלתם בעבר", "Previously practiced")
                            : t("לתרגול", "Ready to practice")}
                        </span>
                        <span className="q-difficulty badge">
                          {q.difficulty}/10
                        </span>
                        <span className="small muted">
                          {q.estimated_minutes ?? "—"} {t("דק׳", "min")}
                        </span>
                      </button>
                    ))}
                  </div>
                  {!filtered.length && (
                    <div className="empty-column">
                      {t("לא נמצאו שאלות מתאימות.", "No matching questions.")}
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
