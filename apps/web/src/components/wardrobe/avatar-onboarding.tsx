"use client";

import { useEffect, useState } from "react";
import { Check, ArrowLeft, ArrowRight, CircleHelp } from "lucide-react";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import { AVATAR_COLORS, DEFAULT_AVATAR, type AvatarClient, type AvatarLanguage, type AvatarPayload } from "../../lib/avatar-types";
import { LogicAvatar } from "./logic-avatar";
import styles from "./avatar-onboarding.module.css";

export function AvatarWelcome({ client, data, lang, onContinue, inline = false }: { client: AvatarClient; data: AvatarPayload; lang: AvatarLanguage; onContinue: () => void; inline?: boolean }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [draft, setDraft] = useState(data.avatar ?? DEFAULT_AVATAR);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const Next = lang === "he" ? ArrowLeft : ArrowRight;
  const Container = inline ? "section" : "main";
  const Heading = inline ? "h3" : "h1";
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
  return <Container className={inline ? styles.inline : styles.welcome} dir={lang === "he" ? "rtl" : "ltr"}>
    {!inline && <header className={styles.header}><a className={styles.brand} href="/">JobRun</a><button className={styles.support} type="button" aria-label={t("דיווח על בעיה", "Report a problem")} aria-haspopup="dialog" onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={20} aria-hidden="true" /></button></header>}
    <div className={styles.layout}>
      <section className={styles.preview}><LogicAvatar config={draft} size={340} label={t("הדמות הראשונה שלכם", "Your first character")} /></section>
      <section className={styles.form}>
        <Heading>{t("נעים להכיר. איזה רכיב אתם?", "Nice to meet you. What's your logic?")}</Heading>
        <p>{t("הרכיב והצבע חינמיים, ואפשר לשנות אותם בכל רגע בחנות של מוקסי.", "Components and colors are free, and you can change them any time at Muxi's shop.")}</p>
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
  </Container>;
}

/** First-time character setup is available from the dashboard as soon as its own data is ready. */
export function DashboardAvatarSetup({ userId, lang }: { userId: string; lang: AvatarLanguage }) {
  const [setup, setSetup] = useState<{ client: AvatarClient; data: AvatarPayload } | null>(null);
  const [opened, setOpened] = useState(false);
  useEffect(() => {
    let current = true;
    void import("../../lib/avatar-api").then(async ({ avatarApi }) => {
      if (!current) return;
      const client = avatarApi(userId);
      const data = await client.get();
      if (current && data.enabled && data.onboarding_completed === false) setSetup({ client, data });
    }).catch(() => {});
    return () => { current = false; };
  }, [userId]);
  if (!setup) return null;
  return <details className={styles.setup} onToggle={event => { if (event.currentTarget.open) setOpened(true); }}>
    <summary>{lang === "he" ? "בחירת הדמות שלי" : "Choose my character"}</summary>
    {opened && <AvatarWelcome {...setup} inline lang={lang} onContinue={() => setSetup(null)} />}
  </details>;
}
