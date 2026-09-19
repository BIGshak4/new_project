"use client";
import { useEffect, useState, type ReactNode } from "react";
import { ArrowRight, LogOut, Mail, LockKeyhole } from "lucide-react";
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
  return (
    <>
      <header className="auth-topbar">{controls}</header>
      <main className="auth-layout" dir={he ? "rtl" : "ltr"}>
        <section className="auth-story">
          <a href="/" className="wordmark" dir="ltr">
            JobRun
            <span className="logo-dot" />
          </a>
          <div>
            <h1>
              {kind === "tasks"
                ? "רעיון טוב.\nעכשיו לעבודה."
                : he
                  ? "הראיון הבא מתחיל\nבתרגול של היום."
                  : "Your next interview\nstarts with today’s practice."}
            </h1>
            <p>
              {kind === "tasks"
                ? "המשימות, ההחלטות והצעדים הבאים של הראל ושקד. מקום אחד להמשיך ממנו."
                : he
                  ? "שאלות חומרה ותוכנה, מרחב לחשוב בקול ובכתב, והתקדמות שנשמרת איתכם."
                  : "Hardware and software questions, room to reason, and a practice history that stays with you."}
            </p>
          </div>
          <div className="auth-foot">
            {kind === "tasks"
              ? "סביבת העבודה של המייסדים"
              : he
                ? "גרסת פיילוט · השאלות בתהליך ביקורת מקצועית"
                : "Private pilot · Questions under technical review"}
          </div>
        </section>
        <section className="auth-form-wrap">
          {user ? (
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
              <p dir="ltr">{user.email}</p>
              {accessError && <p role="alert">{accessError}</p>}
              <button className="primary" onClick={() => void checkAccess()}>
                {he ? "בדיקת הרשאות מחדש" : "Check access again"}
              </button>
              <button className="text-button" onClick={signOut}>
                <LogOut size={16} />
                {he ? "יציאה מהחשבון" : "Sign out"}
              </button>
            </div>
          ) : (
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
          )}
        </section>
      </main>
    </>
  );
}
