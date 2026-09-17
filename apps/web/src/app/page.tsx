"use client";
import { useEffect, useState, useMemo } from "react";
import {
  BookOpen,
  BarChart3,
  History,
  Search,
  ArrowRight,
  Clock,
  Bookmark,
  Lightbulb,
  Check,
  LogOut,
  ArrowUpRight,
  RotateCcw,
} from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { Auth, type Lang } from "../components/auth";
import { supabase } from "../lib/supabase";
type Question = {
  id: string;
  key: string;
  difficulty: number;
  estimated_minutes: number;
  assets: {
    category: string;
    topic: string;
    topic_title: Record<Lang, string>;
    titles: Record<Lang, string>;
    shared_code: string | null;
    sources: { name: string; url: string }[];
  };
  question_translation: { language: Lang; prompt: string }[];
};
type Entry = {
  id: string;
  question_id: string;
  answer: string;
  self_rating: number | null;
  completed: boolean;
  bookmarked: boolean;
  version: number;
  updated_at: string;
};
export default function Page() {
  const [lang, setLang] = useState<Lang>("he");
  useEffect(() => {
    const value = localStorage.getItem("jobrun-language");
    if (value === "en") setLang("en");
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "he" ? "rtl" : "ltr";
    localStorage.setItem("jobrun-language", lang);
  }, [lang]);
  return (
    <>
      <button
        className="language-switch"
        onClick={() => setLang(lang === "he" ? "en" : "he")}
      >
        {lang === "he" ? "English" : "עברית"}
      </button>
      <Auth lang={lang} kind="practice">
        {(user, signOut) => (
          <Workspace user={user} signOut={signOut} lang={lang} />
        )}
      </Auth>
    </>
  );
}
function Workspace({
  user,
  signOut,
  lang,
}: {
  user: User;
  signOut: () => void;
  lang: Lang;
}) {
  const he = lang === "he",
    t = (h: string, e: string) => (he ? h : e);
  const [questions, setQuestions] = useState<Question[]>([]),
    [entries, setEntries] = useState<Entry[]>([]),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [query, setQuery] = useState(""),
    [category, setCategory] = useState("all"),
    [topic, setTopic] = useState("all"),
    [view, setView] = useState("library"),
    [selected, setSelected] = useState<Question | null>(null);
  async function load() {
    setLoading(true);
    setError("");
    const [q, e] = await Promise.all([
      supabase
        .from("question")
        .select(
          "id,key,difficulty,estimated_minutes,assets,question_translation(language,prompt)",
        )
        .eq("assets->>collection", "jobrun_example_v1")
        .order("key"),
      supabase.from("jr_practice_entries").select("*").eq("user_id", user.id),
    ]);
    if (q.error || e.error)
      setError(
        t(
          "לא הצלחנו לטעון את התרגול. נסו שוב.",
          "Could not load practice. Try again.",
        ),
      );
    else {
      setQuestions(q.data as Question[]);
      setEntries(e.data as Entry[]);
    }
    setLoading(false);
  }
  useEffect(() => {
    void load();
  }, [user.id]);
  const filtered = useMemo(
    () =>
      questions.filter(
        (q) =>
          (category === "all" || q.assets.category === category) &&
          (topic === "all" || q.assets.topic === topic) &&
          `${q.assets.titles[lang]} ${q.assets.topic_title[lang]}`
            .toLowerCase()
            .includes(query.toLowerCase()) &&
          (view !== "history" || entries.some((e) => e.question_id === q.id)) &&
          (view !== "bookmarks" ||
            entries.some((e) => e.question_id === q.id && e.bookmarked)),
      ),
    [questions, query, category, topic, lang, view, entries],
  );
  const topics = Array.from(
    new Map(
      questions.map((q) => [q.assets.topic, q.assets.topic_title[lang]]),
    ).entries(),
  );
  const done = entries.filter((e) => e.completed).length;
  const daily = questions.length
    ? questions[Math.floor(Date.now() / 86400000) % questions.length]
    : null;
  function navigate(next: string) {
    setSelected(null);
    setView(next);
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="wordmark" dir="ltr" href="/">
          JobRun
          <span className="logo-dot" />
        </a>
        <nav>
          {[
            ["library", BookOpen, t("מאגר השאלות", "Question library")],
            ["history", History, t("התרגול שלי", "My practice")],
            ["bookmarks", Bookmark, t("שמורים להמשך", "Saved questions")],
            ["progress", BarChart3, t("ההתקדמות שלי", "My progress")],
          ].map(([id, Icon, label]) => {
            const I = Icon as typeof BookOpen;
            return (
              <button
                className={`nav-item ${view === id ? "active" : ""}`}
                key={String(id)}
                onClick={() => navigate(String(id))}
              >
                <I size={18} />
                {String(label)}
              </button>
            );
          })}
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
          <div className="row" style={{ marginInlineEnd: 95 }}>
            <button
              className="icon-button"
              title={t("יציאה", "Sign out")}
              aria-label={t("יציאה", "Sign out")}
              onClick={signOut}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main className="content">
          {selected ? (
            <Practice
              key={selected.id}
              q={selected}
              entry={entries.find((e) => e.question_id === selected.id)}
              user={user}
              lang={lang}
              onBack={() => setSelected(null)}
              onSaved={(entry) =>
                setEntries((old) => [
                  ...old.filter((e) => e.question_id !== entry.question_id),
                  entry,
                ])
              }
            />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <h1>
                    {view === "progress"
                      ? t("רואים את הדרך.", "See how far you’ve come.")
                      : view === "history"
                        ? t(
                            "ממשיכים מאיפה שעצרנו.",
                            "Pick up where you left off.",
                          )
                        : view === "bookmarks"
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
              <div className="pilot-note">
                {t(
                  "פיילוט פרטי · השאלות והפתרונות בביקורת מקצועית. הערכת השליטה בשלב זה היא דיווח עצמי, ללא ציון AI.",
                  "Private pilot · Questions and solutions are under review. Progress uses self-assessment, not AI scores.",
                )}
              </div>
              <div className="summary-strip">
                <span>
                  <strong>{questions.length}</strong>
                  {t("שאלות במאגר", "questions")}
                </span>
                <span>
                  <strong>{done}</strong>
                  {t("תרגולים שהושלמו", "completed")}
                </span>
                <span>
                  <strong>{entries.filter((e) => e.bookmarked).length}</strong>
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
              {loading ? (
                <div className="loading" role="status">
                  {t("טוענים שאלות…", "Loading questions…")}
                </div>
              ) : view === "progress" ? (
                <div className="question-table">
                  {topics.map(([key, label]) => {
                    const all = questions.filter((q) => q.assets.topic === key);
                    const n = all.filter((q) =>
                      entries.some(
                        (e) => e.question_id === q.id && e.completed,
                      ),
                    ).length;
                    return (
                      <div key={key} className="progress-row">
                        <div>
                          <h3>{label}</h3>
                          <p className="muted small">
                            {t(
                              "שאלות שהשלמתם, לא מדד מוכנות לראיון",
                              "Questions completed, not an interview readiness score",
                            )}
                          </p>
                        </div>
                        <progress value={n} max={all.length} />
                        <span dir="ltr">
                          {n} / {all.length}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <>
                  {view === "library" && daily && (
                    <section className="daily-panel">
                      <div>
                        <h2>{t("שאלה אחת להיום", "One question for today")}</h2>
                        <p>
                          {daily.assets.titles[lang]} ·{" "}
                          {daily.estimated_minutes} {t("דקות", "min")}
                        </p>
                      </div>
                      <button
                        className="primary"
                        onClick={() => setSelected(daily)}
                      >
                        {t("מתחילים לתרגל", "Start practicing")}
                        <ArrowRight size={16} />
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
                      aria-label={t("תחום", "Category")}
                      value={category}
                      onChange={(e) => setCategory(e.target.value)}
                    >
                      <option value="all">
                        {t("כל התחומים", "All categories")}
                      </option>
                      <option value="hardware">{t("חומרה", "Hardware")}</option>
                      <option value="software">{t("תוכנה", "Software")}</option>
                    </select>
                    <select
                      aria-label={t("נושא", "Topic")}
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                    >
                      <option value="all">
                        {t("כל הנושאים", "All topics")}
                      </option>
                      {topics.map(([id, label]) => (
                        <option key={id} value={id}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="question-table">
                    {filtered.map((q, i) => {
                      const e = entries.find((e) => e.question_id === q.id);
                      return (
                        <button
                          className="question-row"
                          key={q.id}
                          onClick={() => setSelected(q)}
                        >
                          <span className="q-num">
                            {e?.completed ? (
                              <Check size={18} />
                            ) : (
                              String(i + 1).padStart(2, "0")
                            )}
                          </span>
                          <div>
                            <h3>{q.assets.titles[lang]}</h3>
                            <span className="topic">
                              {q.assets.topic_title[lang]}
                              {e?.bookmarked && " · " + t("שמורה", "Saved")}
                            </span>
                          </div>
                          <span className="q-category small muted">
                            {q.assets.category === "hardware"
                              ? t("חומרה", "Hardware")
                              : t("תוכנה", "Software")}
                          </span>
                          <span className="q-difficulty badge">
                            {q.difficulty}/10
                          </span>
                          <span className="small muted">
                            {q.estimated_minutes} {t("דק׳", "min")}
                          </span>
                        </button>
                      );
                    })}
                    {!filtered.length && (
                      <div className="empty">
                        <BookOpen size={28} />
                        <h2>
                          {t(
                            "כאן יתחיל התרגול הבא.",
                            "Your next practice starts here.",
                          )}
                        </h2>
                        <p>
                          {view === "library"
                            ? t(
                                "נסו לשנות את החיפוש או הסינון.",
                                "Try changing your search or filters.",
                              )
                            : t(
                                "בחרו שאלה מהמאגר ושמרו את התרגול שלכם.",
                                "Choose a library question and save your practice.",
                              )}
                        </p>
                        <button
                          onClick={() => {
                            setView("library");
                            setQuery("");
                            setTopic("all");
                            setCategory("all");
                          }}
                        >
                          {t("לכל השאלות", "All questions")}
                        </button>
                      </div>
                    )}
                  </div>
                </>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
function Practice({
  q,
  entry,
  user,
  lang,
  onBack,
  onSaved,
}: {
  q: Question;
  entry?: Entry;
  user: User;
  lang: Lang;
  onBack: () => void;
  onSaved: (entry: Entry) => void;
}) {
  const he = lang === "he",
    t = (h: string, e: string) => (he ? h : e),
    key = `jr-draft-${user.id}-${q.id}`;
  const [answer, setAnswer] = useState(entry?.answer ?? ""),
    [rating, setRating] = useState<number | null>(entry?.self_rating ?? null),
    [bookmarked, setBookmarked] = useState(entry?.bookmarked ?? false),
    [completed, setCompleted] = useState(entry?.completed ?? false),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState(""),
    [hint, setHint] = useState(""),
    [solution, setSolution] = useState(""),
    [loadingHelp, setLoadingHelp] = useState(false),
    [draftReady, setDraftReady] = useState(false),
    [baseVersion, setBaseVersion] = useState<number | null>(
      entry?.version ?? null,
    );
  useEffect(() => {
    const draft = sessionStorage.getItem(key);
    if (draft) {
      try {
        const d = JSON.parse(draft);
        setBaseVersion(d.baseVersion ?? null);
        setAnswer(d.answer);
        setRating(d.rating);
        setBookmarked(d.bookmarked);
        setCompleted(d.completed);
        setMessage(t("הטיוטה המקומית שוחזרה.", "Local draft restored."));
      } catch {}
    }
    setDraftReady(true);
  }, [key]);
  const dirty =
    answer !== (entry?.answer ?? "") ||
    rating !== (entry?.self_rating ?? null) ||
    bookmarked !== (entry?.bookmarked ?? false) ||
    completed !== (entry?.completed ?? false);
  useEffect(() => {
    if (draftReady && dirty)
      sessionStorage.setItem(
        key,
        JSON.stringify({ answer, rating, bookmarked, completed, baseVersion }),
      );
    const before = (e: BeforeUnloadEvent) => {
      if (dirty) e.preventDefault();
    };
    window.addEventListener("beforeunload", before);
    return () => window.removeEventListener("beforeunload", before);
  }, [answer, rating, bookmarked, completed, dirty, draftReady, key]);
  useEffect(() => {
    setHint("");
    setSolution("");
  }, [lang]);
  async function save() {
    setBusy(true);
    setError("");
    const payload = { answer, self_rating: rating, completed, bookmarked };
    const result = entry
      ? await supabase
          .from("jr_practice_entries")
          .update(payload)
          .eq("id", entry.id)
          .eq("version", baseVersion)
          .select()
          .maybeSingle()
      : await supabase
          .from("jr_practice_entries")
          .insert({ ...payload, user_id: user.id, question_id: q.id })
          .select()
          .single();
    if (result.error || !result.data)
      setError(
        t(
          "השמירה לא הושלמה. ייתכן שהתרגול השתנה בחלון אחר. הטיוטה נשמרה כאן; העתיקו אותה לפני טעינה מחדש.",
          "Save failed. This practice may have changed in another window. Your local draft is preserved; copy it before reloading.",
        ),
      );
    else {
      setBaseVersion(result.data.version);
      onSaved(result.data);
      sessionStorage.removeItem(key);
      setMessage(
        t("התרגול נשמר בחשבון שלכם.", "Practice saved to your account."),
      );
    }
    setBusy(false);
  }
  async function reveal(kind: "hint" | "solution") {
    setLoadingHelp(true);
    setError("");
    const { data, error } = await supabase
      .from("question_translation")
      .select("hints,reference_solution")
      .eq("question_id", q.id)
      .eq("language", lang)
      .single();
    if (error)
      setError(
        t("לא ניתן לטעון כרגע. נסו שוב.", "Could not load this. Try again."),
      );
    else if (kind === "hint") setHint((data.hints as string[]).join("\n"));
    else setSolution(data.reference_solution);
    setLoadingHelp(false);
  }
  return (
    <>
      <div className="row spread" style={{ marginBottom: 22 }}>
        <button className="text-button" onClick={onBack}>
          <ArrowRight size={17} />
          {t("חזרה למאגר", "Back to library")}
        </button>
        <span className="small muted">
          {dirty
            ? t(
                "טיוטה מקומית · יש לשמור לחשבון",
                "Local draft · Save to your account",
              )
            : t("כל השינויים נשמרו", "All changes saved")}
        </span>
      </div>
      <div className="practice-layout">
        <section className="question-sheet">
          <div className="row">
            <span className="badge">{q.assets.topic_title[lang]}</span>
            <span className="small muted">
              <Clock size={13} /> {q.estimated_minutes} {t("דקות", "minutes")}
            </span>
            <span className="small muted">
              {t("קושי", "Difficulty")} {q.difficulty}/10
            </span>
          </div>
          <h1>{q.assets.titles[lang]}</h1>
          <p className="question-prompt" dir="auto">
            {q.question_translation.find((x) => x.language === lang)?.prompt}
          </p>
          {q.assets.shared_code && (
            <pre className="code-block">{q.assets.shared_code}</pre>
          )}
          <div className="row" style={{ marginTop: 26 }}>
            <button onClick={() => void reveal("hint")} disabled={loadingHelp}>
              <Lightbulb size={16} />
              {t("כיוון למחשבה", "Get a hint")}
            </button>
            <button
              onClick={() => setBookmarked(!bookmarked)}
              aria-pressed={bookmarked}
            >
              <Bookmark size={16} fill={bookmarked ? "currentColor" : "none"} />
              {bookmarked
                ? t("שמורה להמשך", "Saved for later")
                : t("לשמור להמשך", "Bookmark")}
            </button>
          </div>
          {hint && <div className="hint">{hint}</div>}
          <div className="source-list">
            <span className="muted">
              {t(
                "רקע מקצועי לשאלה · לא מקור לדיווח על חברה",
                "Concept references · Not evidence of employer usage",
              )}
            </span>
            {q.assets.sources.map((s) => (
              <a key={s.url} href={s.url} target="_blank" rel="noreferrer">
                {s.name} <ArrowUpRight size={12} />
              </a>
            ))}
          </div>
        </section>
        <section className="answer-sheet">
          <h2>{t("איך הייתם פותרים את זה?", "How would you solve it?")}</h2>
          <p className="muted small">
            {t(
              "כתבו הנחות, הסבירו את הדרך ובדקו מקרי קצה.",
              "State assumptions, explain your reasoning, and check edge cases.",
            )}
          </p>
          <textarea
            aria-label={t("הפתרון שלי", "My solution")}
            dir="auto"
            maxLength={30000}
            value={answer}
            onChange={(e) => {
              setAnswer(e.target.value);
              setMessage("");
            }}
            placeholder={t("מתחילים מהרעיון…", "Start with your approach…")}
          />
          <div className="row spread">
            <button
              className="primary"
              onClick={() => void save()}
              disabled={busy}
            >
              {busy
                ? t("שומרים…", "Saving…")
                : t("שמירת התרגול", "Save practice")}
              <Check size={16} />
            </button>
            <button
              onClick={() => void reveal("solution")}
              disabled={loadingHelp}
            >
              {t("הצגת פתרון מוצע", "View reference solution")}
            </button>
          </div>
          {solution && (
            <div className="solution">
              <h3>
                {t("פתרון מוצע · בביקורת", "Reference solution · Under review")}
              </h3>
              <p dir="auto">{solution}</p>
            </div>
          )}
          <div style={{ marginTop: 26 }}>
            <p className="small">
              {t(
                "איך הרגיש התרגול? הערכה עצמית בלבד.",
                "How did it feel? Self-assessment only.",
              )}
            </p>
            <div className="ratings">
              {[1, 2, 3].map((n) => (
                <button
                  key={n}
                  className={rating === n ? "active" : ""}
                  aria-pressed={rating === n}
                  onClick={() => setRating(n)}
                >
                  {
                    [
                      t("צריך לחזור", "Needs work"),
                      t("בדרך לשם", "Getting there"),
                      t("מרגיש בטוח", "Feeling confident"),
                    ][n - 1]
                  }
                </button>
              ))}
            </div>
            <label className="check-label" style={{ marginTop: 18 }}>
              <input
                type="checkbox"
                checked={completed}
                onChange={(e) => setCompleted(e.target.checked)}
              />
              {t(
                "סיימתי את התרגול ובדקתי את הפתרון",
                "I finished practicing and reviewed the solution",
              )}
            </label>
          </div>
          <p className="status-message" role="status" style={{ marginTop: 16 }}>
            {message}
          </p>
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
        </section>
      </div>
    </>
  );
}
