"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, ArrowRight, ChevronDown, CircleHelp, Compass, Pause, Play, RotateCcw, X } from "lucide-react";
import { MuxiMascot } from "./muxi-mascot";
import { MuxiGuidance } from "./muxi-guidance";
import { lockBodyScroll } from "../../lib/body-scroll-lock";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import { UserInboxButton } from "../user-inbox";
import { checkpoint, initialTourProgress, parseTourProgress, stationReady, tourKey, tourSteps, type TourKind, type TourProgress } from "../../lib/muxi-tour";
import styles from "./muxi-tour.module.css";

const TourExercises = dynamic(() => import("./tour-exercises").then((m) => m.TourExercises), {
  ssr: false,
  loading: () => <p role="status">טוענים את כלי ההיכרות… / Loading introduction tools…</p>,
});
type Lang = "he" | "en";
const read = (key: string) => { try { return parseTourProgress(localStorage.getItem(key)); } catch { return initialTourProgress(); } };
const write = (key: string, value: TourProgress) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* Tours still work when storage is disabled. */ } };

function ExpandedCoach({ children, lang, onExit }: { children: ReactNode; lang: Lang; onExit: () => void }) {
  const [minimized, setMinimized] = useState(() => window.matchMedia("(max-width: 760px)").matches);
  return <section className={styles.expandedCoach} data-muxi-expanded-guide data-minimized={minimized} aria-label={lang === "he" ? "הדרכה בחלון השרטוט" : "Drawing workspace guidance"}>
    <div className={styles.expandedBar}>
      <MuxiMascot className={styles.compactMascot} />
      <button type="button" onClick={() => setMinimized(!minimized)} aria-expanded={!minimized}>{minimized ? (lang === "he" ? "פתיחת ההדרכה" : "Open guidance") : (lang === "he" ? "מזעור ההדרכה" : "Minimize guidance")}<ChevronDown size={16} /></button>
      <button type="button" onClick={onExit} aria-label={lang === "he" ? "יציאה מהסיור" : "Exit tour"}><X size={16} />{lang === "he" ? "יציאה" : "Exit"}</button>
    </div>
    <div className={styles.expandedBody} hidden={minimized}>{children}</div>
  </section>;
}

/** The production workspace remains mounted while this locally scoped tour is open. */
export function MuxiTourLauncher({ userId, lang, controls, ready = true }: { userId: string; lang: Lang; controls: ReactNode; ready?: boolean }) {
  const [open, setOpen] = useState(false);
  const initialized = useRef("");
  useEffect(() => {
    if (!ready || initialized.current === userId) return;
    initialized.current = userId;
    const key = tourKey(userId), progress = read(key);
    if (!progress.offered) {
      write(key, { ...progress, offered: true, updatedAt: Date.now() });
      setOpen(true);
    }
  }, [ready, userId]);
  return <>
    <button type="button" className={styles.launcher} onClick={() => setOpen(true)} aria-haspopup="dialog">
      <MuxiMascot className={styles.launcherMascot} />
      <span>{lang === "he" ? "סיור עם מוקסי" : "Tour with Muxi"}</span>
    </button>
    {open && createPortal(<MuxiTour lang={lang} userId={userId} controls={controls} onClose={() => setOpen(false)} />, document.body)}
  </>;
}

export function MuxiTour({ lang, userId, controls, onClose, standalone = false }: { lang: Lang; userId?: string; controls: ReactNode; onClose: () => void; standalone?: boolean }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [progress, setProgress] = useState<TourProgress>(initialTourProgress);
  const [screen, setScreen] = useState<"choose" | "tour" | "finish">("choose");
  const [stationActions, setStationActions] = useState<Record<string, string[]>>({});
  const [storageReady, setStorageReady] = useState(false);
  const [outline, setOutline] = useState(false);
  const [mobile, setMobile] = useState(false);
  const root = useRef<HTMLDivElement>(null), heading = useRef<HTMLHeadingElement>(null);
  const closeRef = useRef(onClose); closeRef.current = onClose;
  const previousFocus = useRef<HTMLElement | null>(null);
  const progressRef = useRef(progress); progressRef.current = progress;
  const key = tourKey(userId), titleId = useId();
  const steps = tourSteps(progress.kind);
  const index = Math.max(0, steps.findIndex((s) => s.id === progress.stepId));
  const step = steps[index];
  const actions = stationActions[step.id] ?? [];
  const ready = progress.completed.includes(step.id) || stationReady(step, actions);
  const latestLang = useRef(lang);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)");
    const update = () => setMobile(media.matches);
    update(); media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    setProgress(read(key)); setStorageReady(true);
  }, [key]);
  useEffect(() => {
    if (storageReady) write(key, progress);
  }, [key, progress, storageReady]);
  useEffect(() => {
    previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const unlockScroll = lockBodyScroll();
    // A portal leaves existing drafts and component state alive, but makes the covered UI inert.
    const covered = [...document.body.children].filter((el): el is HTMLElement => el instanceof HTMLElement && !el.contains(root.current) && !el.matches("[data-jobrun-support-dialog], [data-jobrun-inbox-dialog]"));
    const previous = covered.map((el) => [el, el.inert] as const);
    previous.forEach(([el]) => { el.inert = true; });
    return () => {
      unlockScroll();
      previous.forEach(([el, inert]) => { el.inert = inert; });
      previousFocus.current?.focus({ preventScroll: true });
    };
  }, []);
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
    root.current?.scrollTo({ top: 0 });
    const stage = root.current?.querySelector<HTMLElement>("[data-muxi-stage]");
    stage?.scrollTo({ top: 0 });
  }, [step.id, screen]);
  const onAction = useCallback((action: string) => {
    setStationActions((old) => {
      const previous = old[step.id] ?? [];
      return previous.includes(action) ? old : { ...old, [step.id]: [...previous, action] };
    });
  }, [step.id]);
  useEffect(() => {
    if (screen !== "tour" || !stationReady(step, actions) || progress.completed.includes(step.id)) return;
    setProgress((old) => checkpoint(old, step, "completed", step));
  }, [actions, step, screen, progress.completed]);
  useEffect(() => {
    const observer = new MutationObserver(() => onAction("theme-changed"));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, [onAction]);
  useEffect(() => {
    if (latestLang.current !== lang) { latestLang.current = lang; onAction("language-changed"); }
  }, [lang, onAction]);
  const close = useCallback(() => {
    const current = progressRef.current;
    write(key, { ...current, offered: true, status: current.status === "completed" ? "completed" : screen === "choose" && !current.completed.length ? "dismissed" : "paused", updatedAt: Date.now() });
    closeRef.current();
  }, [key, screen]);
  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !event.defaultPrevented && !document.querySelector("dialog:modal") && !(event.target instanceof Element && event.target.closest(".cm-editor"))) { event.preventDefault(); close(); }
    };
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [close]);
  function start(kind: TourKind, resume = false) {
    setProgress((old) => resume ? { ...old, offered: true, status: "paused" } : { ...initialTourProgress(), offered: true, kind, stepId: tourSteps(kind)[0].id });
    if (!resume) setStationActions({});
    setScreen("tour"); setOutline(false);
  }
  function advance(skip = false) {
    if (!skip && !ready) return;
    setProgress((old) => checkpoint(old, step, skip ? "skipped" : "completed", steps[index + 1]));
    if (index === steps.length - 1) setScreen("finish");
  }
  function jump(stepId: string) {
    setProgress((old) => ({ ...old, stepId, status: "paused" }));
    setOutline(false);
  }
  const chapters = steps.filter((s, i) => i === 0 || s.chapter.he !== steps[i - 1].chapter.he);
  const BackArrow = lang === "he" ? ArrowRight : ArrowLeft;
  const NextArrow = lang === "he" ? ArrowLeft : ArrowRight;
  const guide = <aside className={styles.coach} aria-label={t("ההדרכה של מוקסי", "Muxi's guidance")} data-muxi-coach>
    <div className={styles.coachIdentity}>
      <MuxiMascot pose={ready ? "celebrate" : "point"} pointDirection={mobile ? "down" : lang === "he" ? "left" : "right"} label={t("מוקסי, מוקס קטן שמלווה אתכם", "Muxi, your little multiplexer guide")} className={styles.mascot} />
      <div><strong>{t("מוקסי כאן איתכם", "Muxi is here with you")}</strong><span>{step.chapter[lang]}</span></div>
    </div>
    <p className={styles.stationCount}>{t("תחנה", "Station")} <bdi>{index + 1} / {steps.length}</bdi></p>
    <progress className={styles.progress} max={steps.length} value={index + 1} aria-label={t("מיקום בסיור", "Tour position")} />
    <h2 ref={heading} tabIndex={-1} className={styles.coachTitle}>{step.title[lang]}</h2>
    <p>{step.body[lang]}</p>
    <div className={styles.task} role="status" aria-live="polite">
      <div><strong>{ready ? t("הפעולה הושלמה", "Action completed") : t("עכשיו תורכם", "Your turn")}</strong><p>{ready ? ["explanation", "code", "feedback", "feedback-details", "followup", "interview-answer"].includes(step.id) ? t("השלמתם את פעולת ההיכרות. זה אינו אישור לנכונות התשובה.", "You completed the introduction action. This does not confirm that an answer is correct.") : t("סיימתם את הפעולה. אפשר להמשיך לתחנה הבאה או להתנסות עוד.", "The action is complete. Continue to the next station or explore a little more.") : step.task[lang]}</p></div>
    </div>
    <div className={styles.stepActions}>
      <button type="button" onClick={() => index > 0 && jump(steps[index - 1].id)} disabled={index === 0} aria-label={t("התחנה הקודמת", "Previous station")}><BackArrow size={18} /></button>
      <button type="button" className="primary" onClick={() => advance()} disabled={!ready}>{index === steps.length - 1 ? t("סיום הסיור", "Finish tour") : t("ממשיכים", "Continue")}<NextArrow size={17} /></button>
    </div>
    {!ready && <p className={styles.hint}>{t("בצעו את הפעולה המסומנת כדי להמשיך, או דלגו על התחנה.", "Try the highlighted action to continue, or skip this station.")}</p>}
    <button type="button" className={styles.quiet} onClick={() => advance(true)}>{t("דלגו על התחנה הזאת", "Skip this station")}</button>
    <div className={styles.coachFooter}>
      <button type="button" onClick={() => setScreen("choose")}><Compass size={15} />{t("בחירת סיור אחר", "Choose another tour")}</button>
      <button type="button" onClick={close}><Pause size={15} />{t("יציאה ושמירת המקום", "Exit and save my place")}</button>
    </div>
  </aside>;
  return <div ref={root} className={styles.root} data-muxi-station={screen === "tour" ? step.id : screen} data-muxi-kind={progress.kind} dir={lang === "he" ? "rtl" : "ltr"} role={standalone ? undefined : "dialog"} aria-modal={standalone ? undefined : true} aria-labelledby={titleId}
    onKeyDown={(event) => {
      if (event.key !== "Tab" || event.defaultPrevented || document.querySelector("dialog:modal")) return;
      const items = [...(root.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"],[contenteditable="true"]') ?? [])].filter((el) => el.getClientRects().length && !el.closest("[inert]"));
      if (event.shiftKey && document.activeElement === items[0]) { event.preventDefault(); items.at(-1)?.focus(); }
      else if (!event.shiftKey && document.activeElement === items.at(-1)) { event.preventDefault(); items[0]?.focus(); }
    }}>
    <header className={styles.header}>
      <div className={styles.brand}><span dir="ltr">jobrun</span><span className={styles.brandDivider} /><h1 id={titleId}>{t("הסיורים של מוקסי", "Muxi's guided tours")}</h1></div>
      <div className={styles.headerActions}><UserInboxButton lang={lang} />{controls}<button type="button" className={styles.reportHelp} aria-label={t("נתקלתם בבעיה?", "Report a problem")} onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={17} aria-hidden="true" />{t("דיווח", "Report")}</button><button type="button" className={styles.exit} onClick={close}><X size={17} />{t("דילוג ויציאה מהסיור", "Skip and exit tour")}</button></div>
    </header>
    {screen === "choose" ? <main className={styles.welcome}>
      <div className={styles.welcomeIntro}><MuxiMascot pose="wave" label={t("מוקסי מנופף לשלום", "Muxi waves hello")} className={styles.welcomeMascot} /><div><h2 ref={heading} tabIndex={-1}>{t("נעים להכיר, אני מוקסי.", "Hi, I'm Muxi.")}</h2><p>{t("אני מוקס קטן עם משימה גדולה: לעזור לכם להפוך את כל הכלים כאן ללמידה שעובדת בשבילכם.", "A little multiplexer with a big job: helping you make these tools work for your learning.")}</p></div></div>
      <p className={styles.welcomeLead}>{standalone
        ? t("מכירים את JobRun לפני שנרשמים. מוקסי מדגים איך משתמשים בכלים, ואתם מתנסים בעצמכם — ללא הרשמה. בחרו סיור קצר או מעמיק; בכל רגע אפשר לדלג או לעצור.", "Explore JobRun before signing up. Muxi shows you how the tools work, and you can try them yourself — no account needed. Choose a short or full tour; skip or pause at any time.")
        : t("איך תרצו להכיר את JobRun? בשני המסלולים מתנסים בידיים, ובכל רגע אפשר לדלג או לעצור.", "How would you like to explore JobRun? Both tours are hands-on, and you can skip or pause at any time.")}</p>
      <div className={styles.choices}>
        <section className={styles.fullChoice}>
          <div className={styles.choiceTitle}><h3>{t("נכנסים לעומק", "The full experience")}</h3><span>{t("מומלץ", "Recommended")}</span></div>
          <p>{t("סיור מעמיק שמראה כמה אפשר לעשות כאן: סקירת הנושאים, כתיבה וקוד, מעגלים וסימולציה, טבלאות אמת, רמזים, צילומים, משוב וראיון מדומה.", "Explore what makes practice different here: a subject overview, reasoning and code, circuits, simulation, truth tables, hints, images, feedback and mock interviews.")}</p>
          <p className={styles.choiceMeta}>{tourSteps("full").length} {t("תחנות · פרקים שאפשר לחזור אליהם · בקצב שלכם", "stations · replayable chapters · at your own pace")}</p>
          <button type="button" className="primary" onClick={() => start("full")}><Play size={17} />{t("מתחילים בסיור המעמיק", "Start the full tour")}</button>
        </section>
        <section className={styles.shortChoice}>
          <h3>{t("סיבוב קצר, ויוצאים לדרך", "A quick look around")}</h3>
          <p>{t("מכירים את ארבעת אזורי האתר ומתנסים בעיקר: יעד, חיפוש ונושאים, עורך קוד, סימולציה, רמז, משוב והתקדמות. אפשר להעמיק אחר כך.", "Meet the four areas and try the essentials: a goal, search and subjects, code editor, simulation, a hint, feedback and progress. Go deeper later.")}</p>
          <p className={styles.choiceMeta}>{tourSteps("short").length} {t("תחנות · היכרות מעשית וקצרה", "stations · a short hands-on introduction")}</p>
          <button type="button" className="primary" onClick={() => start("short")}>{t("מתחילים בסיור הקצר", "Start the short tour")}<NextArrow size={17} /></button>
        </section>
      </div>
      {progress.status === "paused" && (progress.completed.length > 0 || progress.skipped.length > 0) && <div className={styles.resume}><div><strong>{t("כבר הכרנו קצת?", "Already started?")}</strong><p>{t("המקום שלכם נשמר במכשיר הזה.", "Your place is saved on this device.")}</p></div><button type="button" onClick={() => start(progress.kind, true)}><Play size={16} />{t("ממשיכים מהמקום שעצרנו", "Resume where I stopped")}</button></div>}
      <div className={styles.welcomeFoot}><p>{t("תרגול ההיכרות משתמש בכלים האמיתיים ובנתוני דוגמה. הוא אינו משנה את הציונים, התוכנית או התשובות בחשבון.", "Introduction practice uses the real tools with sample data. It does not change your account's grades, plan or answers.")}</p><button type="button" className={styles.quiet} onClick={close}>{t("אדלג בינתיים — אכיר את האתר לבד", "Skip for now — I'll explore on my own")}</button></div>
    </main> : screen === "finish" ? <main className={styles.finish}>
      <MuxiMascot pose="celebrate" label={t("מוקסי שמח שסיימתם", "Muxi celebrates your tour")} className={styles.welcomeMascot} />
      <h2 ref={heading} tabIndex={-1}>{t("עכשיו הכלים בידיים שלכם.", "The tools are yours to use.")}</h2>
      <p>{t("ביצעתם", "You tried")} <bdi>{progress.completed.length}</bdi> {t("תחנות", "stations")}{progress.skipped.length ? ` · ${t("דילגתם על", "Skipped")} ${progress.skipped.length}` : ""}.</p>
      <p>{t("את ההיכרות הזאת אפשר לפתוח שוב דרך סיור עם מוקסי. בתחנות שדילגתם עליהן תמיד אפשר להתנסות אחר כך.", "Reopen Tour with Muxi any time. You can return to skipped stations whenever you like.")}</p>
      <div className={styles.finishActions}><button type="button" className="primary" onClick={close}>{standalone ? t("להרשמה או לכניסה", "Sign up or sign in") : t("יוצאים לתרגול", "Start practicing")}<NextArrow size={18} /></button>{progress.kind === "short" && <button type="button" onClick={() => start("full")}>{t("ממשיכים לסיור המעמיק", "Explore the full tour")}</button>}<button type="button" onClick={() => setScreen("choose")}><RotateCcw size={16} />{t("בחירת סיור מחדש", "Choose a tour again")}</button></div>
    </main> : <>
      <div className={styles.tourBar}><span>{progress.kind === "full" ? t("הסיור המעמיק", "The full tour") : t("הסיור הקצר", "The short tour")}</span><button type="button" onClick={() => setOutline(!outline)} aria-expanded={outline}>{t("כל הפרקים", "All chapters")}<ChevronDown size={16} /></button><span className={styles.localNote}>{t("נתוני דוגמה · בלי שינוי בחשבון", "Sample data · no account changes")}</span></div>
      {outline && <nav className={styles.outline} aria-label={t("פרקי הסיור", "Tour chapters")}>{chapters.map((s) => <button type="button" key={s.id} onClick={() => jump(s.id)} aria-current={s.chapter.he === step.chapter.he ? "step" : undefined}>{s.chapter[lang]}</button>)}</nav>}
      <main className={styles.tourGrid}>
        {guide}
        <div className={styles.stage} data-muxi-stage data-muxi-exercise={step.exercise}><TourExercises exercise={step.exercise} stationId={step.id} lang={lang} onAction={onAction} guide={<ExpandedCoach lang={lang} onExit={close}>{guide}</ExpandedCoach>} /></div>
      </main>
      <MuxiGuidance root={root} station={step.id} lang={lang} actions={actions} ready={ready} onAction={onAction} />
      <div className={styles.mobileNav} data-muxi-mobile-nav>
        <button type="button" className={styles.mobileBack} onClick={() => heading.current?.scrollIntoView({ block: "center" })}>{t("בחזרה להדרכה", "Back to guidance")}<span>{step.title[lang]}</span></button>
        <button type="button" className="primary" disabled={!ready} onClick={() => advance()}>{t("הבא בסיור", "Next in tour")}<NextArrow size={16} /></button>
        <button type="button" className={styles.quiet} onClick={() => advance(true)}>{t("דלגו", "Skip")}</button>
      </div>
    </>}
  </div>;
}
