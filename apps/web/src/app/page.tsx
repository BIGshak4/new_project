"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import dynamic from "next/dynamic";
import {
  BookOpen,
  History,
  Search,
  Bookmark,
  LogOut,
  RotateCcw,
  Briefcase,
  Building2,
  Zap,
  Gamepad2,
  Shirt,
} from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { readQuestionCache, writeQuestionCache } from "../lib/question-cache";
import { isRealEvaluationProvider } from "../lib/evaluation-readiness";
import { companyNames, companyReportNote, matchesCompany } from "../lib/question-discovery";
import { QuestionMetadata } from "../components/question-metadata";
import { QuestionStatusControl } from "../components/question-status-control";
import { buildQuestionStates } from "../lib/question-personal-state";
import { matchesLibraryFilters, matchesLibraryStatuses, type LibraryStatus } from "../lib/library-filters";
import { BidiText } from "../components/bidi-text";
import { QuestionTitle } from "../components/question-title";
import { relatedQuestionKeys, uniqueLibraryQuestions } from "../lib/question-families";
import { shuffleQuestions, useQuestionOrderSeed } from "../lib/question-order";
import { goalProgramKey } from "../lib/goal-selection";
import { DEFAULT_WORKSPACE_VIEW, readWorkspaceRoute, type WorkspaceRoute } from "../lib/workspace-route";
import { Auth, type Lang } from "../components/auth";
import { usePracticeEntryReady } from "../components/practice-entry-splash";
import { FeatureNav } from "../components/wardrobe/feature-nav";
import headerStyles from "../components/wardrobe/workspace-header.module.css";
import { PracticeSession } from "../components/practice-session";
import { GoalSetup } from "../components/goal-setup";
import { LanguageMenu } from "../components/ui/language-menu";
import { ThemeToggle } from "../components/ui/theme-toggle";
import { MuxiTourLauncher } from "../components/tour/muxi-tour";
import { UserInboxButton } from "../components/user-inbox";
import { MultiSelect } from "../components/ui/multi-select";
import { AccountStats } from "../components/account-stats";
import type { AccountActivity } from "../lib/account-stats-api";
import { AnimatePresence, motion, useReducedMotion } from "../components/ui/motion";
import { LearnHome } from "../components/learn-home";
import { ResumeQuestion } from "../components/resume-question";
import { AccountIdentity } from "../components/account-identity";
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

type Route = WorkspaceRoute;
const DEFAULT_VIEW = DEFAULT_WORKSPACE_VIEW;
/** History stays addressable for saved attempts; library navigation shows questions, quick study and saved items. */
const LIBRARY_VIEWS = new Set(["library", "fundamentals", "bookmarks", "history"]);
const QuickPractice = dynamic(() => import("../components/quick-practice").then(module => module.QuickPractice));
const emptyProgress: Progress = {
  skills: [],
  subjects: [],
  recent: [],
  attempts_today: 0,
  daily_limit: 30,
};
function currentRoute(entry = false): Route {
  const next = readWorkspaceRoute(window.location.search, entry);
  if (next.search !== window.location.search.replace(/^\?/, "")) {
    window.history.replaceState({}, "", `${window.location.pathname}${next.search ? `?${next.search}` : ""}${window.location.hash}`);
  }
  return next.route;
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
  const languageControl = <><ThemeToggle lang={lang} /><LanguageMenu lang={lang} onChange={setLang} /></>;
  return (
    <Auth lang={lang} kind="practice" controls={<><UserInboxButton lang={lang} />{languageControl}</>}>
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
  const [route, setRoute] = useState<Route>({ view: DEFAULT_VIEW });
  const entryRoute = useRef<Route | null>(null);
  const [questions, setQuestions] = useState<QuestionSummary[]>([]);
  const orderSeed = useQuestionOrderSeed();
  const orderedQuestions = useMemo(() => shuffleQuestions(questions, orderSeed, q => q.key), [questions, orderSeed]);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [progress, setProgress] = useState<Progress>(emptyProgress);
  const [progressRevision, setProgressRevision] = useState(0);
  const [accountActivity, setAccountActivity] = useState<AccountActivity | null>(null);
  const [loading, setLoading] = useState(true),
    [error, setError] = useState("");
  const [demo, setDemo] = useState(true),
    [healthKnown, setHealthKnown] = useState(false);
  const [query, setQuery] = useState("");
  const [subjects, setSubjects] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [statusFilters, setStatusFilters] = useState<LibraryStatus[]>([]);
  const [statusMessage, setStatusMessage] = useState<"hidden" | "done" | "not_done" | "saved" | "unsaved" | null>(null);
  const statusFilterRef = useRef<HTMLDivElement>(null);
  const libraryViewsRef = useRef<HTMLDivElement>(null);
  const generation = useRef(0);
  const [progressReady, setProgressReady] = useState(false);
  const [entriesReady, setEntriesReady] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [progressLoading, setProgressLoading] = useState(true);
  const [entriesLoading, setEntriesLoading] = useState(true);
  const entrySplashVisible = usePracticeEntryReady(!loading && !progressLoading && !entriesLoading);
  const [cachedQuestions, setCachedQuestions] = useState(false);
  // Goals guide the personal plan; the library starts with all questions and no filters.
  const [goal, setGoal] = useState<Goal | null>(null);
  const [goalSkipped, setGoalSkipped] = useState(true);
  const [editingGoal, setEditingGoal] = useState(false);
  const [goalFocusRequest, setGoalFocusRequest] = useState(0);
  const [jobs, setJobs] = useState<JobType[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [jobFilters, setJobFilters] = useState<string[]>([]);
  const [companyFilters, setCompanyFilters] = useState<string[]>([]);
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
    // Strict Mode replays effects; consume a cross-page destination only once per workspace mount.
    entryRoute.current ??= currentRoute(true);
    setRoute(entryRoute.current);
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);
  const navigate = useCallback((next: Route, replace = false) => {
    const q = new URLSearchParams();
    if (next.view !== DEFAULT_VIEW) q.set("view", next.view);
    if (next.attempt) q.set("attempt", next.attempt);
    else if (next.question) q.set("question", next.question);
    if (next.interview) q.set("interview", next.interview);
    if (next.quick) q.set("quick", next.quick);
    if (next.duration) q.set("duration", String(next.duration));
    if (next.question && next.source) q.set("source", next.source);
    window.history[replace ? "replaceState" : "pushState"](
      {},
      "",
      q.size ? `?${q}` : window.location.pathname,
    );
    setRoute(next);
    window.scrollTo({ top: 0 });
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
            "id,user_id,question_id,answer,self_rating,bookmarked,completed,hidden,version",
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
          setDemo(!isRealEvaluationProvider(health.llm_provider));
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
      .then(value => { setProgress(value); setProgressRevision(revision => revision + 1); })
      .catch(() => {});
  }, [api, lang]);
  const onGoalSaved = (g: Goal) => {
    setGoal(g);
    setEditingGoal(false);
    refreshProgress();
    requestAnimationFrame(() => {
      document.querySelector<HTMLElement>("[data-goal-summary]")?.focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: "instant" });
    });
  };
  const skipGoal = () => {
    setEditingGoal(false);
    setGoalSkipped(true);
    try {
      localStorage.setItem(skipKey, "1");
    } catch {}
  };
  const openGoal = () => {
    setGoalSkipped(false);
    setEditingGoal(true);
    setGoalFocusRequest((value) => value + 1);
    try {
      localStorage.removeItem(skipKey);
    } catch {}
    if (route.view !== "learn") navigate({ view: "learn" });
  };
  const onSaved = (entry: Entry) =>
    setEntries((old) => mergeEntries(old, [entry]));
  const active = !!(route.question || route.attempt);
  const topics = [...new Set(questions.map((q) => q.subject))];
  const questionsByKey = new Map(questions.map(q => [q.key, q]));
  const questionStates = buildQuestionStates(questions, entries);
  const companyOptions = companyNames({ reported_companies: [...companies.map(company => company.name), ...questions.flatMap(companyNames)] }).sort((a, b) => a.localeCompare(b));
  const matching = orderedQuestions.filter(
    (q) =>
      matchesLibraryFilters(q, questionStates.get(q.id) ?? { completed: false, hidden: false },
        { query, statuses: statusFilters, categories, subjects, jobs: jobFilters, companies: companyFilters },
        [subjectLabel(q.subject, "he"), subjectLabel(q.subject, "en")]) &&
      (route.view !== "bookmarks" ||
        entries.some((e) => e.question_id === q.id && e.bookmarked)),
  );
  // Saved records keep their own IDs, even when two old records describe the same problem.
  const filtered = route.view === "bookmarks" ? matching : uniqueLibraryQuestions(matching);
  const libraryTotal = uniqueLibraryQuestions(questions).length;
  const goalIncomplete = goal !== null && !goal.complete;
  const showGoalSetup = route.view === "learn" && ((goalIncomplete && !goalSkipped) || editingGoal);
  const openQuestion = (q: QuestionSummary) =>
    navigate({ view: route.view, question: q.key });
  const onQuestionStatusSaved = (q: QuestionSummary, saved: Entry[]) => {
    const updated = mergeEntries(entries, saved);
    const state = buildQuestionStates(questions, updated).get(q.id) ?? { completed: false, hidden: false };
    setEntries((old) => mergeEntries(old, saved));
    setStatusMessage(state.hidden ? "hidden" : state.completed ? "done" : "not_done");
    // A filtered row disappears after a successful save; keep keyboard focus on a useful control.
    const focusedRow = document.activeElement?.closest<HTMLElement>(".library-question-row");
    if (!matchesLibraryStatuses(state, statusFilters) &&
      (focusedRow?.dataset.questionId === q.id || document.activeElement === document.body)) {
      statusFilterRef.current?.querySelector<HTMLButtonElement>("button")?.focus();
    }
  };
  const onQuestionBookmarkSaved = (q: QuestionSummary, saved: Entry) => {
    setEntries((old) => mergeEntries(old, [saved]));
    setStatusMessage(saved.bookmarked ? "saved" : "unsaved");
    const focusedRow = document.activeElement?.closest<HTMLElement>(".library-question-row");
    if (route.view === "bookmarks" && !saved.bookmarked &&
      (focusedRow?.dataset.questionId === q.id || document.activeElement === document.body)) {
      libraryViewsRef.current?.querySelector<HTMLButtonElement>('button[aria-pressed="true"]')?.focus();
    }
  };
  const date = (s: string) =>
    new Date(s).toLocaleString(lang === "he" ? "he-IL" : "en-GB", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  // demo grades are hidden everywhere else, so the numbers derived from them (XP, streak, level) are hidden too
  const overview = demo ? null : progress.overview ?? null;
  const activeTab = LIBRARY_VIEWS.has(route.view) ? "library" : route.view;
  const goTab = (id: string) => {
    navigate({ view: id });
    refreshProgress();
  };
  const libraryViews = <div ref={libraryViewsRef} className="segmented library-views" role="group" aria-label={t("תצוגות המאגר", "Library views")}>
    {[
      { id: "library", icon: BookOpen, label: t("שאלות ראיון", "Interview questions") },
      { id: "fundamentals", icon: Zap, label: t("יסודות בקטנה", "A little practice") },
      { id: "bookmarks", icon: Bookmark, label: t("שמורות", "Saved") },
    ].map(({ id, icon: Icon, label }) => <button key={id} aria-pressed={route.view === id}
      className={route.view === id ? "active" : ""} onClick={() => navigate({ view: id })}>
      <Icon size={15} aria-hidden="true" /> {label}
    </button>)}
  </div>;
  const reducedMotion = useReducedMotion();
  const refreshKey = `${progressRevision}-${progress.attempts_today}-${goalProgramKey(goal)}-${overview?.answered ?? 0}-${overview?.xp_total ?? 0}`;

  return (
    <div className="app-shell">
      <header className={`topnav ${headerStyles.header}`}>
        <a href="/" className="wordmark" dir="ltr">
          <span>.</span>jobrun
        </a>
        <FeatureNav lang={lang}
          className="tabs" current={activeTab === "library" ? "library" : activeTab === "interview" ? "interview" : "learn"} onPracticeNavigate={goTab} />
        <AccountStats userId={user.id} lang={lang} refreshKey={refreshKey} onActivity={setAccountActivity} />
        <div className={`topnav-actions ${headerStyles.toolbar}`}>
          <UserInboxButton lang={lang} />
          <MuxiTourLauncher userId={user.id} lang={lang} controls={languageControl} ready={!loading && !entrySplashVisible} />
          {languageControl}
          <button
            className="icon-button"
            aria-label={t("יציאה", "Sign out")}
            onClick={signOut}
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <FeatureNav lang={lang} className="tabbar" variant="bottom"
        current={activeTab === "library" ? "library" : activeTab === "interview" ? "interview" : "learn"} onPracticeNavigate={goTab} />
      <main className="content">
        {(!healthKnown || demo) && <div className="pilot-note" role="note">
          {!healthKnown
            ? t(
                "בודקים את מצב סביבת התרגול…",
                "Checking the practice environment…",
              )
            : t(
                  "פיילוט · עוזר התרגול עדיין אינו מחובר. אפשר לפתור שאלות ולהיעזר ברמזים. התשובות שלכם נשמרות.",
                  "Pilot · The practice assistant is not connected yet. Solve questions and use hints; your answers are saved.",
                )}
        </div>}
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={route.view}
            className="view"
            initial={reducedMotion ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={reducedMotion ? undefined : { opacity: 0, y: -4 }}
            transition={{ duration: 0.16, ease: "easeOut" }}
          >
        {route.view === "fundamentals" && !active ? <>
          {libraryViews}
          <QuickPractice key={`${user.id}:${route.quick ?? ""}`} lang={lang} api={api} userId={user.id} initialQuestionKey={route.quick} />
        </> : route.view === "interview" ? (
          <InterviewSession
            key={route.interview ?? "lobby"}
            api={api}
            lang={lang}
            userId={user.id}
            interviewId={route.interview}
            initialDuration={route.duration}
            demo={demo}
            onProgress={refreshProgress}
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
            relatedQuestions={questions.filter((q) => relatedQuestionKeys(route.question ?? "").includes(q.key))}
            attemptId={route.attempt}
            lang={lang}
            user={user}
            entries={entries}
            onSaved={onSaved}
            onStarted={(id) =>
              navigate({ view: route.view, attempt: id }, true)
            }
            onNew={(key, source) => navigate({ view: route.view, question: key, source })}
            onBack={() => {
              navigate({ view: route.view });
              refreshProgress();
            }}
            onProgress={refreshProgress}
            demo={demo}
            screen={route.view}
            executionEnabled
            source={route.source ?? "library"}
          />
        ) : route.view === "learn" ? (
          <>
            {error && (
              <div className="notice error" role="alert">
                {error}
                <button onClick={() => void load()}>
                  <RotateCcw size={15} />
                  {t("ניסיון נוסף", "Retry")}
                </button>
              </div>
            )}
            <LearnHome
              api={api}
              userId={user.id}
              activity={accountActivity}
              lang={lang}
              userName={firstName(user)}
              goal={goal}
              accountSlot={<AccountIdentity key={user.id} userId={user.id} lang={lang} />}
              resumeSlot={<ResumeQuestion api={api} userId={user.id} lang={lang} questions={questions} recent={progress.recent} entries={entries}
                ready={progressReady && entriesReady && !loading && !refreshing} navigate={navigate} />}
              progress={demo ? { ...progress, overview: null, skills: [] } : progress}
              refreshKey={refreshKey}
              goalSlot={
                showGoalSetup ? (
                  <GoalSetup
                    api={api}
                    lang={lang}
                    goal={goal}
                    compact={!!goal?.complete}
                    focusRequest={goalFocusRequest}
                    onSaved={onGoalSaved}
                    onSkip={skipGoal}
                  />
                ) : undefined
              }
              onStartAttempt={(id) => {
                navigate({ view: "learn", attempt: id });
                refreshProgress();
              }}
              onStartInterview={(duration) => navigate({ view: "interview", duration: duration ?? undefined })}
              onOpenGoal={openGoal}
              onOpenLibrary={() => goTab("library")}
            />
            <button className="quick-home-link" onClick={() => navigate({ view: "fundamentals" })}>
              <Zap size={20} aria-hidden="true" /><span><strong>{t("יש לכם רגע? יסודות בקטנה", "Have a moment? A little practice")}</strong>
              <span>{t("שאלות קצרות לחיזוק הבסיס, גם מהטלפון.", "Short questions to strengthen the basics, from your phone too.")}</span></span>
            </button>
            <a className="quick-home-link" href="/games">
              <Gamepad2 size={20} aria-hidden="true" /><span><strong>{t("דו־קרב עם חבר", "Challenge a friend")}</strong>
              <span>{t("חמש שאלות קצרות, אותו אתגר לשניכם.", "Five short questions. The same challenge for both of you.")}</span></span>
            </a>
            <a className="quick-home-link" href="/games/shop">
              <Shirt size={20} aria-hidden="true" /><span><strong>{t("הדמות שלכם, החנות של מוקסי", "Your avatar, Muxi's shop")}</strong>
              <span>{t("בחרו רכיב וצבע, וגלו סקינים למטבעות שהרווחתם.", "Choose a component and color, and discover skins for the coins you earn.")}</span></span>
            </a>
          </>
        ) : (
          <>
            <div className="page-heading">
              <div>
                <h1>
                  {route.view === "history"
                    ? t("התרגול שלכם", "Your practice")
                    : route.view === "bookmarks"
                      ? t("שאלות ששמרתם", "Saved questions")
                      : t("מאגר השאלות", "The question bank")}
                </h1>
                <p>
                  {route.view === "history"
                    ? t("כל תשובה ששלחתם, עם הציון והמשוב, מהחדשה לישנה.", "Every answer you sent, with its grade and feedback, newest first.")
                    : route.view === "bookmarks"
                      ? t("שאלות שסימנתם כדי לחזור אליהן. לחצו על שאלה כדי להתחיל.", "Questions you marked to come back to. Open one to start.")
                      : t(
                          "שאלות הכנה בלוגיקה ספרתית, מכונות מצבים, חידות ותכנות.",
                          "Practice questions in digital logic, state machines, puzzles and code.",
                        )}
                </p>
              </div>
            </div>
            {activeTab === "library" && libraryViews}
            {activeTab === "library" && (
              <div className="summary-strip">
                <span>
                  <strong>{loading || !entriesReady ? "—" : filtered.length}</strong>
                  {" "}{route.view === "bookmarks" ? t("שאלות שמורות בתצוגה", "saved questions shown") : t("שאלות בתצוגה", "questions shown")}
                  {route.view !== "bookmarks" && <span>{" "}{t(`מתוך ${libraryTotal} שאלות במאגר`, `of ${libraryTotal} questions in the library`)}</span>}
                </span>
                <span>
                  <strong>
                    {progressReady
                      ? progress.daily_limit >= 1000
                        ? progress.attempts_today
                        : `${progress.attempts_today} / ${progress.daily_limit}`
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
            )}
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
            (route.view === "history" &&
              progressLoading) ||
            (activeTab === "library" && route.view !== "history" && entriesLoading) ? (
              <div className="loading" role="status">
                {t(
                  "טוענים את התרגול… אחרי הפסקה השרת עשוי להזדקק לכדקה.",
                  "Loading practice… after a pause the server may need about a minute.",
                )}
              </div>
            ) : (route.view === "history" &&
                !progressReady) ||
              (activeTab === "library" && route.view !== "history" &&
                !entriesReady) ? null : route.view === "history" ? (
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
                        <QuestionTitle lang={lang}>
                          <BidiText>{questions.find((q) => q.key === a.question_key)
                            ?.title ?? a.question_key}</BidiText>
                        </QuestionTitle>
                        {questionsByKey.has(a.question_key) && <QuestionMetadata question={questionsByKey.get(a.question_key)!} lang={lang} compact />}
                        <span className="topic">
                          {date(a.started_at)} ·{" "}
                          {a.language === "he"
                            ? t("עברית", "Hebrew")
                            : t("אנגלית", "English")}
                        </span>
                      </div>
                      <span className={`badge ${a.band && !demo ? `band-${String(a.band).toLowerCase()}` : ""}`}>
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
                            <QuestionTitle lang={lang}><BidiText>{q.title}</BidiText></QuestionTitle>
                            <QuestionMetadata question={q} lang={lang} compact />
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
                <div className="toolbar">
                  <div className="search">
                    <Search size={17} />
                    <input
                      aria-label={t("חיפוש שאלות", "Search questions")}
                      placeholder={t(
                        "חפשו שאלה, נושא או חברה…",
                        "Search a question, topic or company…",
                      )}
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </div>
                  <div ref={statusFilterRef} className="question-status-filter">
                    <MultiSelect
                      label={t("סטטוס שאלה", "Question status")}
                      allLabel={t("סטטוס שאלה", "Question status")}
                      lang={lang}
                      values={statusFilters}
                      onChange={(values) => {
                        setStatusFilters(values as LibraryStatus[]);
                        setStatusMessage(null);
                      }}
                      options={[
                        { value: "not_done", label: t("לא בוצעו", "Not done") },
                        { value: "done", label: t("בוצעו", "Done") },
                        { value: "hidden", label: t("מוסתרות", "Hidden") },
                      ]}
                    />
                  </div>
                  <MultiSelect
                    label={t("תחום", "Discipline")}
                    allLabel={t("כל התחומים", "All disciplines")}
                    lang={lang}
                    values={categories}
                    onChange={setCategories}
                    options={[
                      { value: "hardware", label: t("חומרה", "Hardware") },
                      { value: "software", label: t("תוכנה", "Software") },
                      { value: "logic", label: t("חידות והיגיון", "Logic & puzzles") },
                      { value: "general", label: t("כללי", "General") }]}
                  />
                  <MultiSelect
                    label={t("נושא", "Topic")}
                    allLabel={t("כל הנושאים", "All topics")}
                    lang={lang}
                    values={subjects}
                    onChange={setSubjects}
                    options={topics.map((s) => ({ value: s, label: subjectLabel(s, lang) }))}
                  />
                  <MultiSelect
                    label={t("סוג תפקיד", "Job type")}
                    allLabel={t("כל התפקידים", "All job types")}
                    lang={lang}
                    icon={<Briefcase size={16} aria-hidden="true" />}
                    values={jobFilters}
                    onChange={setJobFilters}
                    options={jobs.map((j) => ({ value: j.key, label: j.label }))}
                  />
                  <MultiSelect label={t("חברות", "Companies")} allLabel={t("כל החברות", "All companies")} lang={lang}
                    icon={<Building2 size={16} aria-hidden="true" />} values={companyFilters} onChange={setCompanyFilters}
                    matchesOption={(option, search) => matchesCompany({ reported_companies: [option.label] }, search)}
                    options={companyOptions.map(name => ({ value: name, label: name }))} />
                </div>
                <p className="small muted library-status-note">{t("סימוני השאלות נשמרים בחשבון. המסננים מתאפסים בכניסה מחדש; ללא בחירה מוצגות כל השאלות.", "Question flags are saved to your account. Filters reset on a new visit; no selection shows every question.")}</p>
                <p className="small library-status-message" role="status" aria-live="polite">{statusMessage === "hidden"
                  ? t("השאלה סומנה כמוסתרת. אפשר לסנן שאלות לפי הסטטוס שלהן.", "Question marked as hidden. Use Question status to filter your questions.")
                  : statusMessage === "done" ? t("השאלה סומנה כבוצעה.", "Question marked as done.")
                  : statusMessage === "not_done" ? t("השאלה סומנה כלא בוצעה.", "Question marked as not done.")
                  : statusMessage === "saved" ? t("השאלה נוספה לשמורות.", "Question added to Saved.")
                  : statusMessage === "unsaved" ? t("השאלה הוסרה מהשמורות.", "Question removed from Saved.") : null}</p>
                <p className="company-report-note library-provenance">{companyReportNote(lang)}</p>
                {jobFilters.length > 0 && (
                  <p className="small muted filter-note" role="status">
                    {t(
                      "מוצגות שאלות שמתאימות לתפקידים שבחרתם, בסדר מעורבב.",
                      "Questions matching your chosen roles are shown in shuffled order.",
                    )}
                  </p>
                )}
                <div className="question-table">
                  {filtered.map((q) => (
                    <div
                      className="question-row library-question-row"
                      key={q.id}
                      data-question-id={q.id}
                    >
                      <div className="library-question-main">
                        <QuestionTitle lang={lang}>
                          <button type="button" className="library-question-open" onClick={() => openQuestion(q)}>
                            <BidiText>{q.title}</BidiText>
                          </button>
                        </QuestionTitle>
                        <QuestionMetadata question={q} lang={lang} compact />
                        {entries.some(e => e.question_id === q.id && e.bookmarked) && <span className="small muted">{t("שמורה", "Saved")}</span>}
                      </div>
                      <QuestionStatusControl userId={user.id} question={q} questions={questions}
                        state={questionStates.get(q.id) ?? { completed: false, hidden: false }} lang={lang}
                        ready={entriesReady} onSaved={(saved) => onQuestionStatusSaved(q, saved)}
                        bookmark={{ saved: entries.some(e => e.question_id === q.id && e.bookmarked), onSaved: saved => onQuestionBookmarkSaved(q, saved) }} />
                    </div>
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
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}

/** The user's first name from the sign-up metadata, or nothing (the kicker then starts with the job type). */
function firstName(user: { user_metadata?: Record<string, unknown> | null; email?: string | null }): string | undefined {
  const full = user.user_metadata?.full_name ?? user.user_metadata?.name;
  if (typeof full === "string" && full.trim()) return full.trim().split(/\s+/)[0];
  return undefined;
}
