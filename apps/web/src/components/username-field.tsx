"use client";

import { useEffect, useId, useState } from "react";
import { usernameAvailability } from "../lib/identity-api";
import { identityErrorMessage, normalizeUsername, validUsernameFormat, type IdentityLanguage, type UsernameAvailability } from "../lib/identity-types";
import styles from "./username-field.module.css";

export function UsernameField({ value, onChange, lang, disabled = false }: { value: string; onChange: (value: string) => void; lang: IdentityLanguage; disabled?: boolean }) {
  const id = useId(), he = lang === "he";
  const [check, setCheck] = useState<{ value: string; state: "checking" | "error" | "complete"; result?: UsernameAvailability } | null>(null);
  const username = normalizeUsername(value);
  useEffect(() => {
    setCheck(null);
    if (!username || !validUsernameFormat(username)) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setCheck({ value: username, state: "checking" });
      void usernameAvailability(username, controller.signal).then(result => {
        if (!controller.signal.aborted) setCheck({ value: username, state: "complete", result });
      }).catch(() => { if (!controller.signal.aborted) setCheck({ value: username, state: "error" }); });
    }, 450);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [username]);
  const current = check?.value === username ? check : null;
  const reason = username && !validUsernameFormat(username) ? "invalid" : current?.result?.reason;
  const status = reason
    ? identityErrorMessage({ code: `username_${reason}` }, lang)
    : current?.state === "checking" ? he ? "בודקים אם השם פנוי…" : "Checking availability…"
    : current?.state === "error" ? he ? "לא הצלחנו לבדוק זמינות. נבדוק שוב בעת השמירה." : "We couldn’t check availability. We’ll check again when you save."
    : current?.result?.available ? he ? "שם המשתמש פנוי." : "This username is available."
    : "";
  return <div className={styles.field}>
    <label htmlFor={id}>{he ? "שם משתמש" : "Username"}</label>
    <input id={id} name="username" autoComplete="username" autoCapitalize="none" spellCheck={false} dir="auto" required minLength={3} maxLength={24} value={value} disabled={disabled} aria-invalid={!!reason || undefined} aria-describedby={`${id}-help ${id}-status`} onChange={event => onChange(event.target.value)} />
    <p id={`${id}-help`} className={styles.help}>{he ? "3–24 תווים: אותיות בעברית או באנגלית, ספרות וקו תחתון. לפחות אות אחת." : "3–24 characters: Hebrew or English letters, digits and underscores. Include at least one letter."}</p>
    <p id={`${id}-status`} className={`${styles.status} ${reason ? styles.invalid : ""}`} role="status" aria-live="polite">{status}</p>
  </div>;
}
