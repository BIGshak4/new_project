"use client";
import { useEffect, useState, type ReactNode } from "react";
import { ArrowRight, Check, Lock, LockKeyhole, LogOut, Mail, Play } from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
export type Lang = "he" | "en";
export function Auth({
  lang = "he",
  kind,
  children,
  controls,
}: {
  controls?: ReactNode;
  lang?: Lang;
  kind: "tasks" | "practice";
  children: (user: User, signOut: () => void) => ReactNode;
}) {
  const he = lang === "he";
  const [user, setUser] = useState<User | null>(null),
    [ready, setReady] = useState(false),
    [member, setMember] = useState(false),
    [checking, setChecking] = useState(false),
    [accessError, setAccessError] = useState("");
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [mode, setMode] = useState<"login" | "signup">("login"),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    let live = true;
    supabase.auth
      .getUser()
      .then(({ data }) => {
        if (live) {
          setUser(data.user);
          setReady(true);
        }
      })
      .catch(() => {
        if (live) setReady(true);
      });
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      if (live) {
        setUser(session?.user ?? null);
        setReady(true);
      }
    });
    return () => {
      live = false;
      data.subscription.unsubscribe();
    };
  }, []);
  async function checkAccess() {
    setChecking(true);
    setAccessError("");
    const { data, error } = await supabase
      .from("jr_members")
      .select("email,can_manage_tasks")
      .limit(1);
    setMember(
      !error &&
        !!data?.length &&
        (kind !== "tasks" || data[0].can_manage_tasks),
    );
    if (error)
      setAccessError(
        he
          ? "לא הצלחנו לבדוק הרשאות. נסו שוב."
          : "Unable to check access. Try again.",
      );
    setChecking(false);
  }
  useEffect(() => {
    if (user) {
      void checkAccess();
    } else setMember(false);
  }, [user?.id]); // RLS is the authorization boundary.
  const signOut = () => {
    void supabase.auth.signOut();
  };
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result =
        mode === "login"
          ? await supabase.auth.signInWithPassword({
              email: email.trim(),
              password,
            })
          : await supabase.auth.signUp({
              email: email.trim(),
              password,
              options: { emailRedirectTo: window.location.origin },
            });
      if (result.error) throw result.error;
      if (mode === "signup" && !result.data.session)
        setMessage(
          he
            ? "נשלח מייל לאימות החשבון. אשרו אותו ואז התחברו כאן."
            : "Check your email to confirm your account, then sign in here.",
        );
    } catch (err) {
      const code = (err as { code?: string }).code;
      setError(
        code === "invalid_credentials"
          ? he
            ? "האימייל או הסיסמה אינם נכונים."
            : "Incorrect email or password."
          : code === "email_not_confirmed"
            ? he
              ? "צריך לאמת את האימייל לפני הכניסה."
              : "Confirm your email before signing in."
            : he
              ? "הכניסה לא הושלמה. בדקו את הפרטים ונסו שוב. אם לא מגיע מייל, פנו למנהלי הפיילוט."
              : "Sign-in failed. Check your details and try again. Contact the pilot team if email does not arrive.",
      );
    } finally {
      setBusy(false);
    }
  }
  if (!ready || checking)
    return (
      <div className="loading" role="status">
        {he ? "טוענים את סביבת העבודה…" : "Loading your workspace…"}
      </div>
    );
  if (user && member) return children(user, signOut);
  const gate = (
    <div className="auth-form">
      <LockKeyhole size={30} />
      <h2>
        {he
          ? "החשבון מחובר. נדרשת הרשאת גישה."
          : "Signed in. Access approval needed."}
      </h2>
      <p>
        {he
          ? "הסביבה פתוחה כרגע למשתתפי הפיילוט שאושרו מראש."
          : "This workspace is available to approved pilot participants."}
      </p>
      <p dir="ltr">{user?.email}</p>
      {accessError && <p role="alert">{accessError}</p>}
      <button type="button" className="primary" onClick={() => void checkAccess()}>
        {he ? "בדיקת הרשאות מחדש" : "Check access again"}
      </button>
      <button type="button" className="text-button" onClick={signOut}>
        <LogOut size={16} />
        {he ? "יציאה מהחשבון" : "Sign out"}
      </button>
    </div>
  );
  const form = (
    <form className="auth-form" onSubmit={submit}>
      <h2>
        {mode === "login"
          ? he
            ? "טוב שחזרתם."
            : "Welcome back."
          : he
            ? "מתחילים כאן."
            : "Start here."}
      </h2>
      <p>
        {he
          ? "התחברו עם האימייל שאושר לפיילוט."
          : "Use the email approved for the pilot."}
      </p>
      <label>
        {he ? "אימייל" : "Email"}
        <div className="input-icon">
          <Mail size={17} />
          <input
            type="email"
            autoComplete="email"
            dir="ltr"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
        </div>
      </label>
      <label>
        {he ? "סיסמה" : "Password"}
        <input
          type="password"
          autoComplete={
            mode === "login" ? "current-password" : "new-password"
          }
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={he ? "לפחות 8 תווים" : "At least 8 characters"}
        />
      </label>
      {error && (
        <p className="notice error" role="alert">
          {error}
        </p>
      )}
      {message && (
        <p className="notice" role="status">
          {message}
        </p>
      )}
      <button className="primary" disabled={busy}>
        {busy
          ? he
            ? "רגע…"
            : "One moment…"
          : mode === "login"
            ? he
              ? "כניסה לסביבת העבודה"
              : "Sign in"
            : he
              ? "יצירת חשבון"
              : "Create account"}
        <ArrowRight size={17} />
      </button>
      <button
        type="button"
        className="text-button"
        onClick={() => {
          setMode(mode === "login" ? "signup" : "login");
          setError("");
          setMessage("");
        }}
      >
        {mode === "login"
          ? he
            ? "כניסה ראשונה? צרו חשבון"
            : "First time? Create an account"
          : he
            ? "כבר יש חשבון? התחברו"
            : "Already have an account? Sign in"}
      </button>
      <p className="small muted">
        {he
          ? "יצירת חשבון אינה מעניקה גישה אוטומטית לנתוני הצוות."
          : "Creating an account does not automatically grant access to team data."}
      </p>
    </form>
  );
  if (kind === "practice") {
    return (
      <PracticeLanding he={he} controls={controls}>
        {user ? gate : form}
      </PracticeLanding>
    );
  }
  return (
    <>
      <header className="auth-topbar">{controls}</header>
      <main className="auth-layout" dir={he ? "rtl" : "ltr"}>
        <section className="auth-story">
          <a href="/" className="wordmark" dir="ltr">
            jobrun
          </a>
          <div>
            <h1>{"רעיון טוב.\nעכשיו לעבודה."}</h1>
            <p>{"המשימות, ההחלטות והצעדים הבאים של הראל ושקד. מקום אחד להמשיך ממנו."}</p>
          </div>
          <div className="auth-foot">{"סביבת העבודה של המייסדים"}</div>
        </section>
        <section className="auth-form-wrap">{user ? gate : form}</section>
      </main>
    </>
  );
}

/** The practice app's landing page: the sign-in screen built around the most characteristic thing in this product,
 * a real interview question and what happens after you answer it. Every number here is a true product fact
 * (docs/design-brief-2026-09-27.md §6); nothing is invented. `children` is the sign-in card (or the access gate). */
function PracticeLanding({
  he,
  controls,
  children,
}: {
  he: boolean;
  controls?: ReactNode;
  children: ReactNode;
}) {
  const t = (heText: string, en: string) => (he ? heText : en);
  const facts: [string, string][] = [
    ["30", t("שאלות ראיון אמיתיות", "real interview questions")],
    ["6", t("נושאים: מלוגיקה ספרתית ועד תכנות", "subjects, from digital logic to code")],
    ["6", t("סוגי תפקידים, מוריפיקציה ועד תוכנה", "job types, from verification to software")],
    ["~8", t("שניות עד הציון על תשובה", "seconds until an answer is graded")],
    ["2", t("שפות: עברית ואנגלית", "languages: Hebrew and English")],
    ["20·30·45", t("דקות של ראיון מדומה", "minutes of mock interview")],
  ];
  const steps: [string, string][] = [
    [t("מגדירים יעד", "Set a goal"), t("סוג התפקיד, תאריך הראיון וכמה דקות יש ביום.", "The job type, the interview date, and the minutes you have a day.")],
    [t("עונים על השאלה של היום", "Answer today’s question"), t("ציון תוך שניות, מה היה טוב, מה היה חסר, ושאלת המשך אחת.", "A grade in seconds, what was good, what was missing, and one follow-up.")],
    [t("ממשיכים בדרך", "Keep to the path"), t("התוכנית מתעדכנת כל יום לפי מה שענית, עד יום הראיון.", "The plan adjusts every day to what you answered, until interview day.")],
  ];
  return (
    <div className="landing" dir={he ? "rtl" : "ltr"}>
      <header className="landing-head">
        <a href="/" className="wordmark" dir="ltr">
          jobrun
        </a>
        <div className="landing-head-actions">
          {controls}
          <a href="#signin" className="text-button">
            {t("כניסה", "Sign in")}
          </a>
        </div>
      </header>

      <section className="landing-hero">
        <div className="hero-copy">
          <h1>{t("הראיון הבא מתחיל בתרגול של היום.", "The next interview starts with today’s practice.")}</h1>
          <p className="hero-sub">
            {t(
              "שאלות אמיתיות מראיונות חומרה ותוכנה, ציון תוך שניות, ותוכנית שמתעדכנת כל יום עד יום הראיון.",
              "Real hardware and software interview questions, a grade in seconds, and a plan that adjusts every day until interview day.",
            )}
          </p>
          <div className="hero-actions">
            <a href="#signin" className="primary hero-cta">
              {t("להתחיל לתרגל", "Start practising")}
            </a>
            <span className="small muted">{t("פיילוט פרטי · בהזמנה", "Private pilot · by invitation")}</span>
          </div>
        </div>

        <article className="sample" aria-label={t("דוגמה: שאלה, תשובה וציון", "Example: a question, an answer and its grade")}>
          <div className="sample-top">
            <span className="badge">{t("לוגיקה ספרתית", "Digital logic")}</span>
            <span className="small muted">{t("קושי 2 מתוך 10 · 5 דקות", "Difficulty 2 of 10 · 5 min")}</span>
          </div>
          <h2 dir="auto">{t("הכרעת רוב בין שלושה חיישנים", "Two-out-of-three sensor vote")}</h2>
          <p className="sample-prompt" dir="auto">
            {t(
              "שלושה חיישנים של ביט אחד, A, B, C, מחזירים 1 כאשר הם מזהים תקלה. יש להפעיל alarm כאשר לפחות שני חיישנים מחזירים 1. כתבו ביטוי בוליאני מצומצם והסבירו מדוע XOR של שלושת הקלטים אינו מספיק.",
              "Three one-bit sensors A, B, C are 1 when they detect a fault. Assert alarm if at least two sensors are 1. Give a simplified Boolean expression and explain why XOR of the three inputs is not sufficient.",
            )}
          </p>
          <div className="sample-answer" dir="ltr">
            alarm = AB + BC + AC
          </div>
          <div className="sample-grade">
            <span className="sample-ring" aria-hidden="true">
              ✓
            </span>
            <div>
              <div className="sample-band">{t("תשובה חזקה", "Strong answer")}</div>
              <div className="small muted">{t("XOR מטפל בזוגיות, לא בספירה: נכון.", "XOR is parity, not a count: correct.")}</div>
            </div>
            <span className="xp-pill">
              <bdi dir="ltr">+18 XP</bdi>
            </span>
          </div>
          <div className="sample-follow" dir="auto">
            <span className="sample-follow-label">{t("שאלת המשך", "Follow-up")}</span>
            {t("מה משתנה אם חיישן אחד תקוע ב-1?", "What changes if one sensor is stuck at 1?")}
          </div>
        </article>
      </section>

      <section className="landing-facts" aria-label={t("מה יש כאן", "What is here")}>
        {facts.map(([number, label]) => (
          <div className="fact" key={label}>
            <strong dir="ltr">{number}</strong>
            <span dir="auto">{label}</span>
          </div>
        ))}
      </section>

      <section className="landing-how" aria-label={t("איך זה עובד", "How it works")}>
        <h2>{t("שלושה צעדים, כל יום.", "Three steps, every day.")}</h2>
        <ol className="how-path">
          {steps.map(([title, text], i) => (
            <li key={title} className={`how-step ${i === 0 ? "state-done" : i === 1 ? "state-current" : "state-locked"}`}>
              <span className="path-node" aria-hidden="true">
                {i === 0 ? <Check size={30} strokeWidth={3.2} /> : i === 1 ? <Play size={32} fill="currentColor" /> : <Lock size={26} />}
              </span>
              <div>
                <h3 dir="auto">{title}</h3>
                <p dir="auto">{text}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section className="landing-signin" id="signin">
        {children}
      </section>

      <footer className="landing-foot small muted">
        {t("JobRun · פיילוט פרטי · השאלות בבדיקה מקצועית לפני פרסום", "JobRun · private pilot · questions are reviewed by an engineer before publication")}
      </footer>
    </div>
  );
}

