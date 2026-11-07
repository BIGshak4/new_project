"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { GREETING_MS, MAX_SPLASH_MS, hasGreeted, recordGreeting } from "../lib/practice-entry";
import { lockBodyScroll } from "../lib/body-scroll-lock";
import { MuxiMascot } from "./tour/muxi-mascot";
import styles from "./practice-entry-splash.module.css";

const EntryContext = createContext<{ visible: boolean; reportReady: (ready: boolean) => void } | null>(null);

/** The dashboard can prepare behind the greeting and defer its automatic tour until the greeting is over. */
export function usePracticeEntryReady(ready: boolean) {
  const entry = useContext(EntryContext);
  const reportReady = entry?.reportReady;
  useEffect(() => { reportReady?.(ready); }, [ready, reportReady]);
  return entry?.visible ?? false;
}

export function PracticeEntrySplash({ lang }: { lang: "he" | "en" }) {
  const he = lang === "he";
  return (
    <div className={styles.screen} role="status" lang={lang} dir={he ? "rtl" : "ltr"}>
      <div className={styles.scene} aria-hidden="true">
        <svg className={styles.traces} viewBox="0 0 440 180" fill="none" focusable="false">
          <g className={styles.board}>
            <path d="M12 23h65l19 19h73M12 79h119l10-10h28M12 119h104l23-23h30M12 160h62l37-37h58" />
            <path d="M275 82h42l26-26h85" />
          </g>
          <path className={styles.signal} pathLength="1" d="M12 119h104l23-23h30" />
          <path className={styles.output} pathLength="1" d="M275 82h42l26-26h85" />
        </svg>
        <MuxiMascot pose="wave" className={styles.mascot} />
      </div>
      <div className={styles.copy}>
        <span className={styles.brand} dir="ltr" aria-hidden="true"><b>.</b>jobrun</span>
        <p>{he ? "נתחיל בשאלה טובה." : "Let’s start with a good question."}</p>
        <span className={styles.srOnly}>{he ? "מוקסי מכין את סביבת התרגול." : "Muxi is getting your workspace ready."}</span>
      </div>
    </div>
  );
}

export function PracticeEntry({ owner, lang, gateReady, children }: {
  owner: string; lang: "he" | "en"; gateReady: boolean; children: ReactNode;
}) {
  const [visible, setVisible] = useState(() => !hasGreeted(owner));
  const [greetingComplete, setGreetingComplete] = useState(false);
  const [workspaceReady, setWorkspaceReady] = useState(true);
  useEffect(() => {
    if (!visible) return;
    recordGreeting(owner);
    const releaseScroll = lockBodyScroll();
    const greeting = window.setTimeout(() => setGreetingComplete(true), GREETING_MS);
    const deadline = window.setTimeout(() => setVisible(false), MAX_SPLASH_MS);
    return () => { window.clearTimeout(greeting); window.clearTimeout(deadline); releaseScroll(); };
  }, [owner, visible]);
  useEffect(() => {
    if (greetingComplete && gateReady && workspaceReady) setVisible(false);
  }, [gateReady, greetingComplete, workspaceReady]);
  return (
    <EntryContext.Provider value={{ visible, reportReady: setWorkspaceReady }}>
      {visible && <PracticeEntrySplash lang={lang} />}
      <div className={styles.workspace} inert={visible}>{children}</div>
    </EntryContext.Provider>
  );
}
