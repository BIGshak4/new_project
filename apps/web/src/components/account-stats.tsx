"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as Popover from "@radix-ui/react-popover";
import { Coins, Flame, RotateCcw, X } from "lucide-react";
import { accountStatsApi, type AccountActivity, type AccountWallet } from "../lib/account-stats-api";
import styles from "./account-stats.module.css";

type ReadState<T> = { owner: string; value: T | null; failed: boolean };
export function AccountStats({ userId, lang, refreshKey, onActivity }: { userId: string; lang: "he" | "en"; refreshKey: string; onActivity?: (value: AccountActivity | null) => void }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const client = useMemo(() => accountStatsApi(userId), [userId]);
  const [activity, setActivity] = useState<ReadState<AccountActivity> | null>(null);
  const [wallet, setWallet] = useState<ReadState<AccountWallet> | null>(null);
  const [busy, setBusy] = useState(false);
  const generation = useRef(0);
  const request = useRef<AbortController | null>(null);
  const load = useCallback(() => {
    const revision = ++generation.current;
    request.current?.abort();
    const controller = new AbortController(); request.current = controller;
    const current = () => !controller.signal.aborted && revision === generation.current;
    let timezone = "UTC";
    try { timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"; } catch {}
    setBusy(true);
    void Promise.allSettled([
      client.activity(timezone, controller.signal).then(value => { if (current()) { setActivity({ owner: userId, value, failed: false }); onActivity?.(value); } })
        .catch(() => { if (current()) { setActivity({ owner: userId, value: null, failed: true }); onActivity?.(null); } }),
      client.wallet(lang, controller.signal).then(value => { if (current()) setWallet({ owner: userId, value, failed: false }); })
        .catch(() => { if (current()) setWallet({ owner: userId, value: null, failed: true }); }),
    ]).finally(() => { if (current()) setBusy(false); });
  }, [client, lang, userId, onActivity]);
  useEffect(() => {
    load();
    const focus = () => { if (document.visibilityState === "visible") load(); };
    window.addEventListener("focus", focus); document.addEventListener("visibilitychange", focus);
    return () => { ++generation.current; request.current?.abort(); window.removeEventListener("focus", focus); document.removeEventListener("visibilitychange", focus); };
  }, [load, refreshKey]);
  const solved = activity?.owner === userId ? activity.value : null;
  const coins = wallet?.owner === userId && wallet.value?.enabled ? wallet.value.balance : null;
  const activityFailed = activity?.owner === userId && activity.failed;
  const walletFailed = wallet?.owner === userId && wallet.failed;
  const dateLabel = (date: string) => new Date(`${date}T12:00:00`).toLocaleDateString(lang === "he" ? "he-IL" : "en-GB", { day: "numeric", month: "short" });
  return <div className={styles.stats} data-account-stats dir={lang === "he" ? "rtl" : "ltr"} aria-label={t("הרצף והמטבעות שלכם", "Your streak and coins")}>
    <Popover.Root>
      <Popover.Trigger asChild><button type="button" className={styles.stat} aria-label={t(`רצף ימים: ${solved?.streak_days ?? (activityFailed ? "לא זמין" : "טוענים")}. בדיקת הרצף`, `Day streak: ${solved?.streak_days ?? (activityFailed ? "unavailable" : "loading")}. Check your streak`)}>
        <Flame size={19} aria-hidden="true" /><span className={styles.number}>{solved?.streak_days ?? "—"}</span><span className={styles.label}>{t("ימי רצף", "day streak")}</span>
      </button></Popover.Trigger>
      <Popover.Portal><Popover.Content className={`ui-popover ${styles.detail}`} side="bottom" align="start" sideOffset={8} collisionPadding={12} dir={lang === "he" ? "rtl" : "ltr"} aria-label={t("בדיקת רצף הימים", "Check your day streak")}>
        <div className={styles.detailHead}><h2>{t("הרצף שלכם", "Your streak")}</h2><Popover.Close asChild><button type="button" aria-label={t("סגירה", "Close")}><X size={17} aria-hidden="true" /></button></Popover.Close></div>
        <p>{t("יום נחשב כשעניתם על לפחות שאלה אחת שנבדקה בתרגול, או בראיון שהסתיים. גם תשובה שצריכה שיפור נחשבת; פתיחת שאלה בלבד אינה נחשבת.", "A day counts when you answer at least one assessed practice question, or a question in a completed interview. An answer that needs improvement counts too; opening a question alone does not.")}</p>
        <p>{t("הימים נספרים לפי אזור הזמן במכשיר. הרצף נשמר עד סוף היום כדי שתוכלו להמשיך אותו.", "Days follow your device’s time zone. A streak ending yesterday stays available until today ends.")}</p>
        {solved ? <>
          <p className={styles.today}>{solved.today_count ? t(`${solved.today_count} שאלות נענו היום.`, `${solved.today_count} questions answered today.`) : t("עדיין לא נענתה שאלה היום. שאלה אחת תתחיל או תמשיך את הרצף.", "No question answered today yet. One question starts or continues your streak.")}</p>
          {solved.days.length > 0 ? <ul className={styles.days} aria-label={t("ימים שבהם נענו שאלות", "Days with answered questions")}>{solved.days.map(day => <li key={day.date}><time dateTime={day.date}>{dateLabel(day.date)}</time><span>{day.questions} {t("שאלות", "questions")}</span></li>)}</ul>
            : <p>{t("אין עדיין ימים עם שאלות שנענו בחשבון הזה.", "This account has no answered-question days yet.")}</p>}
        </> : <p role={activityFailed ? "alert" : "status"}>{activityFailed ? t("לא הצלחנו לבדוק את הרצף. אפשר לנסות שוב.", "We could not check your streak. Try again.") : t("בודקים את הימים שלכם…", "Checking your activity days…")}</p>}
        <button type="button" className={styles.retry} disabled={busy} onClick={load}><RotateCcw size={15} aria-hidden="true" />{busy ? t("בודקים…", "Checking…") : t("בדיקה מחדש", "Check again")}</button>
      </Popover.Content></Popover.Portal>
    </Popover.Root>
    <a className={styles.stat} href="/games/shop" aria-label={coins === null ? t("יתרת המטבעות לא זמינה. לפתיחת החנות", "Coin balance unavailable. Open the shop") : t(`${coins} מטבעות. לפתיחת החנות`, `${coins} coins. Open the shop`)}>
      <Coins size={19} aria-hidden="true" /><span className={styles.number}>{coins ?? "—"}</span><span className={styles.label}>{t("מטבעות", "coins")}</span>
    </a>
    {walletFailed && <button type="button" className={styles.walletRetry} disabled={busy} onClick={load} aria-label={t("לא הצלחנו לטעון את המטבעות. ניסיון נוסף", "Coin balance could not load. Retry")}><RotateCcw size={15} aria-hidden="true" /></button>}
  </div>;
}
