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
  Mic,
  Briefcase,
  Building2,
} from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { readQuestionCache, writeQuestionCache } from "../lib/question-cache";
import { Auth, type Lang } from "../components/auth";
import { PracticeSession } from "../components/practice-session";
import { GoalSetup } from "../components/goal-setup";
import { OverviewCard, PlanTable, ProgressGraph } from "../components/progress-board";
import { InterviewSession } from "../components/interview-session";
import { supabase } from "../lib/supabase";
import {
  practiceApi,
  type Company,
  type Goal,
  type JobType,
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

type Route = { view: string; question?: string; attempt?: string; interview?: string };
const emptyProgress: Progress = {
  skills: [],
  subjects: [],
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
    interview: q.get("interview") ?? undefined,
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
  // the user's goal drives the default job filter, the plan and the onboarding card
  const [goal, setGoal] = useState<Goal | null>(null);
  const [goalSkipped, setGoalSkipped] = useState(true);
  const [editingGoal, setEditingGoal] = useState(false);
  const [jobs, setJobs] = useState<JobType[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [jobFilter, setJobFilter] = useState(""),
    [companyQuery, setCompanyQuery] = useState("");
  const jobFilterTouched = useRef(false);
  const [jobQuestions, setJobQuestions] = useState<QuestionSummary[] | null>(null);
  const skipKey = `jobrun-goal-skipped-${user.id}`;
  useEffect(() => {
    try {
      setGoalSkipped(localStorage.getItem(skipKey) === "1");
    } catch {
      setGoalSkipped(false);
    }
  }, [skipKey]);

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
    if (next.interview) q.set("interview", next.interview);
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
        .progress(lang)
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
      api
        .getGoal(lang)
        .then((g) => {
          if (!current()) return;
          setGoal(g);
          if (!jobFilterTouched.current) setJobFilter(g.job_type ?? "");
        })
        .catch(() => {}),
      api
        .jobTypes(lang)
        .then((list) => current() && setJobs(list))
        .catch(() => {}),
      api
        .companies()
        .then((list) => current() && setCompanies(list))
        .catch(() => {}),
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
      .progress(lang)
      .then(setProgress)
      .catch(() => {});
  }, [api, lang]);
  // a job filter asks the server for the relevance order; without one the plain (cached) list is shown
  useEffect(() => {
    if (!jobFilter) {
      setJobQuestions(null);
      return;
    }
    let cancelled = false;
    api
      .listQuestions(lang, undefined, { job: jobFilter })
      .then((list) => {
        if (!cancelled) setJobQuestions(list);
      })
      .catch(() => {
        // the server refused the filter (a job type that no longer exists): show everything, unfiltered
        if (!cancelled) {
          setJobQuestions(null);
          jobFilterTouched.current = true;
          setJobFilter("");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [api, lang, jobFilter, questions.length]);
  const onGoalSaved = (g: Goal) => {
    setGoal(g);
    setEditingGoal(false);
    if (!jobFilterTouched.current) setJobFilter(g.job_type ?? "");
    refreshProgress();
  };
  const skipGoal = () => {
    setGoalSkipped(true);
    try {
      localStorage.setItem(skipKey, "1");
    } catch {}
  };
  const onSaved = (entry: Entry) =>
    setEntries((old) => mergeEntries(old, [entry]));
  const active = !!(route.question || route.attempt);
  const topics = [...new Set(questions.map((q) => q.subject))];
  const shown = jobFilter && jobQuestions ? jobQuestions : questions;
  const companyNeedle = companyQuery.trim().toLowerCase();
  const filtered = shown.filter(
    (q) =>
      (subject === "all" || q.subject === subject) &&
      `${q.title} ${subjectLabel(q.subject, lang)}`
        .toLowerCase()
        .includes(query.toLowerCase()) &&
      (!companyNeedle ||
        (q.companies ?? []).some(
          (c) => c.name.toLowerCase().includes(companyNeedle) || c.slug.includes(companyNeedle),
        )) &&
      (route.view !== "bookmarks" ||
        entries.some((e) => e.question_id === q.id && e.bookmarked)),
  );
  const showGoalSetup =
    route.view === "library" && goal !== null && !goal.complete && !goalSkipped;
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
            {
              id: "interview",
              icon: Mic,
              label: t("ראיון מדומה", "Mock interview"),
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
          {route.view === "interview" ? (
            <InterviewSession
              key={route.interview ?? "lobby"}
              api={api}
              lang={lang}
              userId={user.id}
              interviewId={route.interview}
              demo={demo}
              onStarted={(id) => {
                navigate({ view: "interview", interview: id }, true);
                refreshProgress();
              }}
              onBack={() => {
                navigate({ view: "interview" });
                refreshProgress();
              }}
            />
          ) : active ? (
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
                  !entriesReady) ? null : route.view === "progress" ? (
                <div className="progress-board">
                  {demo ? (
                    <p className="notice">
                      {t(
                        "עוזר התרגול עדיין אינו מחובר בסביבה הזו, ולכן לא מוצגים ציוני הדגמה. התוכנית עד הראיון פועלת.",
                        "The practice assistant is not connected in this environment, so demo scores are hidden. The plan until the interview works.",
                      )}
                    </p>
                  ) : (
                    progress.overview && (
                      <OverviewCard
                        overview={progress.overview}
                        goal={progress.goal ?? goal}
                        lang={lang}
                        onEditGoal={() => setEditingGoal((v) => !v)}
                      />
                    )
                  )}
                  {(editingGoal || (demo && goal && !goal.complete)) && (
                    <GoalSetup
                      api={api}
                      lang={lang}
                      goal={goal}
                      compact
                      onSaved={onGoalSaved}
                      onSkip={editingGoal ? () => setEditingGoal(false) : undefined}
                    />
                  )}
                  {!demo && <ProgressGraph timeline={progress.timeline ?? []} lang={lang} />}
                  <PlanTable
                    plan={progress.plan ?? null}
                    lang={lang}
                    onEditGoal={() => setEditingGoal(true)}
                  />
                </div>
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
                  {showGoalSetup && (
                    <GoalSetup api={api} lang={lang} goal={goal} onSaved={onGoalSaved} onSkip={skipGoal} />
                  )}
                  {route.view === "library" && daily && !showGoalSetup && (
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
                    <label className="filter-select">
                      <Briefcase size={16} aria-hidden="true" />
                      <select
                        aria-label={t("סוג תפקיד", "Job type")}
                        value={jobFilter}
                        onChange={(e) => {
                          jobFilterTouched.current = true;
                          setJobFilter(e.target.value);
                        }}
                      >
                        <option value="">{t("כל התפקידים", "All job types")}</option>
                        {jobs.map((j) => (
                          <option key={j.key} value={j.key}>
                            {j.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <div className="search company-search">
                      <Building2 size={16} />
                      <input
                        list="company-list"
                        aria-label={t("חיפוש לפי חברה", "Search by company")}
                        placeholder={t("חברה שבה נשאלה…", "Asked at company…")}
                        value={companyQuery}
                        onChange={(e) => setCompanyQuery(e.target.value)}
                      />
                      <datalist id="company-list">
                        {companies.map((c) => (
                          <option key={c.slug} value={c.name} />
                        ))}
                      </datalist>
                    </div>
                  </div>
                  {jobFilter && jobQuestions && (
                    <p className="small muted filter-note" role="status">
                      {t(
                        "השאלות מסודרות לפי הרלוונטיות לתפקיד שבחרתם. השאלה הראשונה היא הכי חשובה לכם עכשיו.",
                        "Questions are ordered by relevance to the job you chose. The first one matters most to you right now.",
                      )}
                    </p>
                  )}
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
                          <h3>
                            {q.title}
                            {q.trial && (
                              <span className="badge trial">{t("בבדיקה חיה", "On trial")}</span>
                            )}
                          </h3>
                          <span className="topic">
                            {subjectLabel(q.subject, lang)}
                            {entries.some(
                              (e) => e.question_id === q.id && e.bookmarked,
                            )
                              ? " · " + t("שמורה", "Saved")
                              : ""}
                            {q.companies && q.companies.length > 0
                              ? " · " +
                                t("נשאלה ב", "Asked at") +
                                " " +
                                q.companies.slice(0, 3).map((c) => c.name).join(", ")
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
