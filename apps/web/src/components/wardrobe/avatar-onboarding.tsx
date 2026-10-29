"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Check, ArrowLeft, ArrowRight, CircleHelp } from "lucide-react";
import { avatarApi } from "../../lib/avatar-api";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import { AVATAR_COLORS, DEFAULT_AVATAR, type AvatarClient, type AvatarLanguage, type AvatarPayload } from "../../lib/avatar-types";
import { LogicAvatar } from "./logic-avatar";
import styles from "./avatar-onboarding.module.css";

export function AvatarWelcome({ client, data, lang, onContinue }: { client: AvatarClient; data: AvatarPayload; lang: AvatarLanguage; onContinue: () => void }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [draft, setDraft] = useState(data.avatar ?? DEFAULT_AVATAR);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const Next = lang === "he" ? ArrowLeft : ArrowRight;
  async function finish(keepDefault: boolean) {
    if (busy) return;
    setBusy(true); setError(false);
    try {
      if (!client.completeOnboarding) throw new Error("Server update pending");
      await client.completeOnboarding(keepDefault ? undefined : { component: draft.component, color: draft.color });
      onContinue();
    } catch { setError(true); }
    finally { setBusy(false); }
  }
  return <main className={styles.welcome} dir={lang === "he" ? "rtl" : "ltr"}>
    <header className={styles.header}><a className={styles.brand} href="/">JobRun</a><button className={styles.support} type="button" aria-label={t("דיווח על בעיה", "Report a problem")} aria-haspopup="dialog" onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={20} aria-hidden="true" /></button></header>
    <div className={styles.layout}>
      <section className={styles.preview}><LogicAvatar config={draft} size={340} label={t("הדמות הראשונה שלכם", "Your first character")} /></section>
      <section className={styles.form}>
        <h1>{t("נעים להכיר. איזה רכיב אתם?", "Nice to meet you. What's your logic?")}</h1>
        <p>{t("לפני שמתחילים, אפשר לתת לדמות שלכם קצת אופי. הרכיב והצבע חינמיים, ואפשר לשנות אותם בכל רגע בחנות של מוקסי.", "Before you begin, give your character a little personality. Components and colors are free, and you can change them any time at Muxi's shop.")}</p>
        <fieldset disabled={busy}><legend>{t("הרכיב שלכם", "Your component")}</legend><div className={styles.components}>
          {data.components.map(c => <button type="button" key={c.key} aria-pressed={draft.component === c.key} onClick={() => setDraft(v => ({ ...v, component: c.key }))}>
            <LogicAvatar config={{ ...draft, component: c.key }} size={68} /><span>{c.label[lang]}</span>
          </button>)}
        </div></fieldset>
        <fieldset disabled={busy}><legend>{t("צבע אהוב", "A favorite color")}</legend><div className={styles.colors}>
          {data.colors.map(c => <button type="button" key={c.key} style={{ background: AVATAR_COLORS[c.key] }} aria-label={c.label[lang]} aria-pressed={draft.color === c.key} onClick={() => setDraft(v => ({ ...v, color: c.key }))}>{draft.color === c.key && <Check size={20} />}</button>)}
        </div></fieldset>
        {error && <p className={styles.error} role="alert">{t("לא הצלחנו לשמור. אפשר לנסות שוב או להמשיך ולבחור דמות מאוחר יותר.", "We couldn't save your character. Try again, or continue and choose it later.")}</p>}
        <div className={styles.actions}><button className={styles.primary} disabled={busy} onClick={() => void finish(false)}>{busy ? t("שומרים…", "Saving…") : t("זאת הדמות שלי, ממשיכים", "That's me. Let's go")}<Next size={17} /></button>
          <button className={styles.skip} disabled={busy} onClick={() => error ? onContinue() : void finish(true)}>{t("אעשה את זה אחר כך", "I'll do this later")}</button>
        </div>
      </section>
    </div>
  </main>;
}

/** Optional first-use step; authorization stays in Auth and inventory stays on the server. */
export function AvatarOnboardingGate({ userId, lang, children }: { userId: string; lang: AvatarLanguage; children: ReactNode }) {
  const client = useMemo(() => avatarApi(userId), [userId]);
  const [data, setData] = useState<AvatarPayload | null>(null);
  const [checked, setChecked] = useState(false);
  const [finished, setFinished] = useState(false);
  useEffect(() => {
    let current = true;
    const query = new URLSearchParams(window.location.search);
    // Do not interrupt an existing focused attempt or invite with a welcome step.
    if (query.has("question") || query.has("attempt") || query.has("interview") || query.get("view") === "interview" || window.location.pathname.startsWith("/duel/")) {
      setChecked(true); return;
    }
    void client.get().then(value => { if (current) setData(value); }).catch(() => {}).finally(() => { if (current) setChecked(true); });
    return () => { current = false; };
  }, [client]);
  if (!checked) return <div className="loading" role="status">{lang === "he" ? "מכינים את סביבת העבודה…" : "Preparing your workspace…"}</div>;
  if (!finished && data?.enabled && data.onboarding_completed === false) return <AvatarWelcome client={client} data={data} lang={lang} onContinue={() => setFinished(true)} />;
  return children;
}
