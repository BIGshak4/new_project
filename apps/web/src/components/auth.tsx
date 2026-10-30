"use client";

import { PracticeLanding } from "./practice-landing";
import { AvatarOnboardingGate } from "./wardrobe/avatar-onboarding";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowLeft, ArrowRight, LockKeyhole, LogOut, Mail } from "lucide-react";
import type { User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { AccessCheck, accessForUser, observeAuthUser, type AccessState } from "../lib/auth-access";
import styles from "./auth.module.css";
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
    [access, setAccess] = useState<AccessState | null>(null);
  const currentUser = useRef<User | null>(null);
  const accessCheck = useRef(new AccessCheck());
  const { checking, allowed: member, failed } = accessForUser(user?.id, access);
  const accessError = failed
    ? he ? "לא הצלחנו לבדוק הרשאות. נסו שוב." : "Unable to check access. Try again."
    : "";
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [mode, setMode] = useState<"login" | "signup">("login"),
    [busy, setBusy] = useState(false),
    [message, setMessage] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    return observeAuthUser(supabase.auth, (next) => {
      if (currentUser.current?.id !== next?.id) {
        accessCheck.current.invalidate();
        setAccess(null);
      }
      currentUser.current = next;
      setUser(next);
      setPassword("");
      setReady(true);
    });
  }, []);
  async function checkAccess() {
    if (!user) return;
    await accessCheck.current.run(
      user.id,
      async () => {
        const { data, error } = await supabase
          .from("jr_members")
          .select("email,can_manage_tasks")
          .limit(1);
        if (error) throw error;
        return !!data?.length && (kind !== "tasks" || !!data[0].can_manage_tasks);
      },
      () => currentUser.current?.id ?? null,
      setAccess,
    );
  }
  useEffect(() => {
    if (user) void checkAccess();
    return () => accessCheck.current.invalidate();
  }, [user?.id]); // RLS is the authorization boundary.
  const signOut = () => {
    setPassword("");
    void supabase.auth.signOut();
  };
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    const credentials = { email: email.trim(), password };
    // The Auth component remains mounted while signed in; do not retain a reusable password.
    setPassword("");
    try {
      const result =
        mode === "login"
          ? await supabase.auth.signInWithPassword(credentials)
          : await supabase.auth.signUp({
              ...credentials,
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
  if (user && member) return kind === "practice"
    ? <AvatarOnboardingGate key={user.id} userId={user.id} lang={lang}>{children(user, signOut)}</AvatarOnboardingGate>
    : children(user, signOut);
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
        {kind === "practice"
          ? he
            ? "מתחילים או ממשיכים לתרגל."
            : "Start or continue your practice."
          : mode === "login"
            ? he
              ? "טוב שחזרתם."
              : "Welcome back."
            : he
              ? "מתחילים כאן."
              : "Start here."}
      </h2>
      {kind === "practice" && (
        <div className={styles.modes} role="group" aria-label={he ? "יצירת חשבון או התחברות" : "Create an account or sign in"}>
          {(["signup", "login"] as const).map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={mode === option}
              disabled={busy}
              onClick={() => {
                setMode(option);
                setError("");
                setMessage("");
              }}
            >
              {option === "signup"
                ? he ? "יצירת חשבון" : "Create account"
                : he ? "יש לי חשבון" : "I have an account"}
            </button>
          ))}
        </div>
      )}
      <p>
        {kind === "practice" && mode === "signup"
          ? he
            ? "בפעם הראשונה? צרו חשבון עם האימייל שאושר לפיילוט."
            : "First time here? Create an account with the email approved for the pilot."
          : he
            ? "התחברו עם האימייל שאושר לפיילוט."
            : "Sign in with the email approved for the pilot."}
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
      <button type="submit" className="primary" disabled={busy}>
        {busy
          ? he
            ? "רגע…"
            : "One moment…"
          : mode === "login"
            ? he
              ? kind === "practice" ? "כניסה לתרגול" : "כניסה לסביבת העבודה"
              : "Sign in"
            : he
              ? "יצירת חשבון"
              : "Create account"}
        {he ? <ArrowLeft size={17} /> : <ArrowRight size={17} />}
      </button>
      {kind === "tasks" && <button
        type="button"
        className="text-button"
        disabled={busy}
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
      </button>}
      <p className="small muted">
        {kind === "practice"
          ? he
            ? "יצירת חשבון אינה מעניקה גישה אוטומטית לפיילוט. הגישה מיועדת למשתתפים שאושרו מראש."
            : "Creating an account does not automatically grant pilot access. Access is for participants approved in advance."
          : he
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

