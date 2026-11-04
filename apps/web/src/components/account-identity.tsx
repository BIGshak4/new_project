"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState, type FormEvent } from "react";
import { Check, Copy, RefreshCw, UserRound } from "lucide-react";
import { identityApi } from "../lib/identity-api";
import { IDENTITY_UPDATED_EVENT, IdentityApiError, identityErrorMessage, normalizeUsername, validUsernameFormat, type AccountIdentityData, type IdentityLanguage } from "../lib/identity-types";
import { UsernameField } from "./username-field";
import styles from "./account-social.module.css";

export function FriendCode({ code, lang }: { code: string; lang: IdentityLanguage }) {
  const [copied, setCopied] = useState(false), [error, setError] = useState(false);
  const currentCode = useRef(code); currentCode.current = code;
  useEffect(() => { setCopied(false); setError(false); }, [code]);
  useEffect(() => {
    if (!copied) return;
    const timer = setTimeout(() => setCopied(false), 3000);
    return () => clearTimeout(timer);
  }, [copied]);
  async function copy() {
    setError(false);
    try {
      await navigator.clipboard.writeText(code);
      if (currentCode.current === code) setCopied(true);
    } catch { if (currentCode.current === code) setError(true); }
  }
  return <div className={styles.codeBlock}>
    <span className={styles.caption}>{lang === "he" ? "הקוד שלכם לחברים" : "Your friend code"}</span>
    <div className={styles.codeRow}><code dir="ltr">{code}</code><button type="button" className={styles.copyButton} onClick={() => void copy()} aria-label={lang === "he" ? "העתקת הקוד לחברים" : "Copy your friend code"}>{copied ? <Check size={17} aria-hidden="true" /> : <Copy size={17} aria-hidden="true" />}<span>{copied ? lang === "he" ? "הועתק" : "Copied" : lang === "he" ? "העתקה" : "Copy"}</span></button></div>
    <span className={styles.copyStatus} role="status">{error ? lang === "he" ? "לא הצלחנו להעתיק. אפשר לסמן ולהעתיק את הקוד." : "We couldn’t copy it. Select and copy the code instead." : copied ? lang === "he" ? "הקוד הועתק." : "Code copied." : ""}</span>
  </div>;
}

export function AccountIdentity({ userId, lang, onIdentityChange }: { userId: string; lang: IdentityLanguage; onIdentityChange?: (identity: AccountIdentityData) => void }) {
  const api = useMemo(() => identityApi(userId), [userId]);
  const id = useId(), he = lang === "he";
  const [saved, setSaved] = useState<{ owner: string; data: AccountIdentityData } | null>(null);
  const [loading, setLoading] = useState(true), [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null), [actionError, setActionError] = useState<unknown>(null);
  const [username, setUsername] = useState("");
  const owner = useRef(userId); owner.current = userId;
  const callback = useRef(onIdentityChange); callback.current = onIdentityChange;
  const sequence = useRef(0), live = useRef(true), writing = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null), fragmentHandled = useRef(false);
  const identity = saved?.owner === userId ? saved.data : null;
  const load = useCallback(async () => {
    const request = ++sequence.current;
    const current = () => live.current && owner.current === userId && sequence.current === request;
    setLoading(true); setError(null);
    try {
      const data = await api.identity();
      if (current()) { setSaved({ owner: userId, data }); callback.current?.(data); }
    } catch (reason) { if (current()) setError(reason); }
    finally { if (current()) setLoading(false); }
  }, [api, userId]);
  useEffect(() => {
    live.current = true; setUsername(""); setActionError(null); writing.current = false; setBusy(false); fragmentHandled.current = false;
    void load();
    return () => { live.current = false; sequence.current++; };
  }, [load]);
  useEffect(() => {
    if (!identity || fragmentHandled.current || window.location.hash !== "#account-identity") return;
    fragmentHandled.current = true;
    const frame = requestAnimationFrame(() => { heading.current?.focus({ preventScroll: true }); heading.current?.scrollIntoView({ block: "start", behavior: "instant" }); });
    return () => cancelAnimationFrame(frame);
  }, [identity?.friend_code]);

  async function claim(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (writing.current || loading || !identity?.can_claim_username || identity.username) return;
    if (!validUsernameFormat(username)) { setActionError(new IdentityApiError("username_invalid", "Invalid username")); return; }
    writing.current = true; setBusy(true); setActionError(null);
    const request = ++sequence.current;
    const current = () => live.current && owner.current === userId && sequence.current === request;
    const publish = (data: AccountIdentityData) => {
      if (!current()) return;
      setSaved({ owner: userId, data }); callback.current?.(data);
      if (data.username) window.dispatchEvent(new CustomEvent(IDENTITY_UPDATED_EVENT, { detail: { userId } }));
    };
    try { publish(await api.claimUsername(username)); }
    catch (reason) {
      const uncertain = reason instanceof IdentityApiError && (reason.code === "network" || reason.code === "invalid_response" || reason.status >= 500 || reason.code === "username_immutable");
      if (uncertain) {
        try {
          const latest = await api.identity();
          publish(latest);
          if (latest.username?.normalize("NFKC").toLowerCase() === normalizeUsername(username).toLowerCase()) return;
        } catch { /* Keep the draft and explain the original failed write. */ }
      }
      if (current()) setActionError(reason);
    } finally { if (current()) { writing.current = false; setBusy(false); } }
  }

  return <section id="account-identity" className={styles.account} aria-labelledby={`${id}-title`} aria-busy={loading || busy} data-account-identity>
    <div className={styles.accountTop}>
      <div className={styles.accountName}><div className={styles.sectionHeading}><UserRound size={20} aria-hidden="true" /><h2 id={`${id}-title`} className={styles.profileHeading} ref={heading} tabIndex={-1}>{he ? "הפרופיל שלי" : "My profile"}</h2></div>{identity?.username && <p className={styles.username}><bdi>{identity.username}</bdi></p>}</div>
      {identity && <FriendCode key={identity.friend_code} code={identity.friend_code} lang={lang} />}
    </div>
    {loading && !identity && <p className={styles.message} role="status">{he ? "טוענים את הפרופיל…" : "Loading your profile…"}</p>}
    {error != null && <div className={styles.error} role="alert"><p>{identityErrorMessage(error, lang)}</p><button type="button" disabled={busy || loading} onClick={() => void load()}><RefreshCw size={16} aria-hidden="true" />{he ? "טעינה מחדש" : "Retry loading"}</button></div>}
    {identity && !identity.username && identity.can_claim_username && <form className={styles.claim} onSubmit={event => void claim(event)}>
      <p>{he ? "בחרו איך יקראו לכם באתר. שם המשתמש נבחר פעם אחת ולא ניתן לשנות אותו לאחר השמירה." : "Choose how you’ll be known on the site. You can choose your username once; it cannot be changed after saving."}</p>
      <UsernameField value={username} onChange={value => { setUsername(value); setActionError(null); }} lang={lang} disabled={busy || loading} />
      {actionError != null && <p className={styles.error} role="alert">{identityErrorMessage(actionError, lang)}</p>}
      <button type="submit" className="primary" disabled={busy || loading || !validUsernameFormat(username)}>{busy ? he ? "שומרים…" : "Saving…" : he ? "בחירת שם המשתמש" : "Choose my username"}</button>
    </form>}
  </section>;
}
