"use client";

import dynamic from "next/dynamic";
import { BidiText } from "../bidi-text";
import { proseDirection } from "../../lib/bidi-segments";
import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { ArrowLeft, ArrowRight, Check, ChevronDown, CircleHelp, List, Pause, RotateCcw, X } from "lucide-react";
import { MuxiMascot } from "./muxi-mascot";
import { MuxiGuidance } from "./muxi-guidance";
import { lockBodyScroll } from "../../lib/body-scroll-lock";
import { SUPPORT_OPEN_EVENT } from "../../lib/support-report";
import { MEMBER_TOUR_START_EVENT } from "../../lib/member-tour";
import { UserInboxButton } from "../user-inbox";
import { checkpoint, initialTourProgress, isGuestExercise, parseTourProgress, stationReady, tourKey, tourSteps, type TourKind, type TourProgress } from "../../lib/muxi-tour";
import styles from "./muxi-tour.module.css";

const TourExercises = dynamic(() => import("./tour-exercises").then((m) => m.TourExercises), {
  ssr: false,
  loading: () => <p role="status">טוענים את כלי ההיכרות… / Loading introduction tools…</p>,
});
const TourAccountGoal = dynamic(() => import("./tour-account-goal").then(module => module.TourAccountGoal));
const GuestTourExercises = dynamic(() => import("./guest-tour-exercises").then(module => module.GuestTourExercises));
type Lang = "he" | "en";
const read = (key: string, kind: TourKind) => { try { return parseTourProgress(localStorage.getItem(key), kind); } catch { return initialTourProgress(kind); } };
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

function MuxiScene({ finished = false }: { finished?: boolean }) {
  return <div className={styles.scene} aria-hidden="true">
    <svg className={styles.traces} viewBox="0 0 400 200" fill="none">
      <g>
        <path d="M4 32h69l29 29h65M4 88h163M4 127h73l14-14h76M4 172h65l43-43h55M230 96h49l24-24h93" />
      </g>
      <path className={styles.pulse} pathLength="1" d="M4 127h73l14-14h76" />
      <path className={styles.outputPulse} pathLength="1" d="M230 96h49l24-24h93" />
    </svg>
    <MuxiMascot pose={finished ? "celebrate" : "wave"} className={styles.welcomeMascot} />
  </div>;
}

/** The production workspace remains mounted while this locally scoped tour is open. */
export function MuxiTourLauncher({ userId, lang, controls }: { userId: string; lang: Lang; controls: ReactNode }) {
  return <>
    <button type="button" className={styles.launcher} onClick={() => window.dispatchEvent(new CustomEvent(MEMBER_TOUR_START_EVENT, { detail: { userId } }))}>
      <MuxiMascot className={styles.launcherMascot} />
      <span>{lang === "he" ? "סיור עם מוקסי" : "Tour with Muxi"}</span>
    </button>
  </>;
}

type TourProps = { lang: Lang; userId?: string; controls: ReactNode; onClose: () => void; standalone?: boolean };

export function MuxiTour(props: TourProps) {
  const kind: TourKind = props.standalone || !props.userId ? "preview" : "member";
  return <TourSession key={kind === "member" ? props.userId : "preview"} {...props} kind={kind} />;
}

function TourSession({ lang, userId, controls, onClose, standalone = false, kind }: TourProps & { kind: TourKind }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const preview = kind === "preview";
  const [progress, setProgress] = useState<TourProgress>(() => initialTourProgress(kind));
  const [screen, setScreen] = useState<"welcome" | "tour" | "finish">("welcome");
  const [stationActions, setStationActions] = useState<Record<string, string[]>>({});
  const [storageReady, setStorageReady] = useState(false);
  const [outline, setOutline] = useState(false);
  const [mobile, setMobile] = useState(false);
  const root = useRef<HTMLDivElement>(null), heading = useRef<HTMLHeadingElement>(null);
  const closeRef = useRef(onClose); closeRef.current = onClose;
  const previousFocus = useRef<HTMLElement | null>(null);
  const progressRef = useRef(progress); progressRef.current = progress;
  const key = tourKey(preview ? undefined : userId), titleId = useId(), outlineId = useId();
  const steps = tourSteps(kind);
  const index = Math.max(0, steps.findIndex((s) => s.id === progress.stepId));
  const step = steps[index];
  const actions = stationActions[step.id] ?? [];
  const ready = progress.completed.includes(step.id) || stationReady(step, actions);
  useEffect(() => {
    const media = window.matchMedia("(max-width: 760px)");
    const update = () => setMobile(media.matches);
    update(); media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    setProgress(read(key, kind)); setStorageReady(true);
  }, [key, kind]);
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
    setProgress((old) => old.stepId === step.id ? checkpoint(old, step, "completed", step) : old);
  }, [actions, step, screen, progress.completed]);
  const close = useCallback(() => {
    const current = progressRef.current;
    if (storageReady && screen === "tour") write(key, { ...current, status: "paused", updatedAt: Date.now() });
    closeRef.current();
  }, [key, screen, storageReady]);
  useEffect(() => {
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !event.defaultPrevented && !document.querySelector("dialog:modal") && !(event.target instanceof Element && event.target.closest(".cm-editor"))) { event.preventDefault(); close(); }
    };
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [close]);
  function start(resume = false) {
    setProgress((old) => ({ ...(resume ? old : initialTourProgress(kind)), offered: true, status: "paused", updatedAt: Date.now() }));
    if (!resume) setStationActions({});
    setScreen("tour"); setOutline(false);
  }
  function advance(skip = false) {
    if (!skip && !ready) return;
    setProgress((old) => checkpoint(old, step, skip ? "skipped" : "completed", steps[index + 1]));
    if (index === steps.length - 1) setScreen("finish");
  }
  function jump(stepId: string) {
    setProgress((old) => ({ ...old, stepId, status: "paused", updatedAt: Date.now() }));
    setOutline(false);
  }
  const canResume = progress.offered && progress.status === "paused";
  const BackArrow = lang === "he" ? ArrowRight : ArrowLeft;
  const NextArrow = lang === "he" ? ArrowLeft : ArrowRight;
  const renderGuide = (inDialog = false) => <aside className={styles.coach} aria-label={t("ההדרכה של מוקסי", "Muxi's guidance")} data-muxi-coach>
    <div className={styles.coachIdentity}>
      <MuxiMascot key={step.id} pose={ready ? "celebrate" : "point"} pointDirection={mobile ? "down" : lang === "he" ? "left" : "right"} className={styles.mascot} />
      <div><strong>{t("מוקסי", "Muxi")}</strong><span><BidiText>{step.chapter[lang]}</BidiText></span></div>
    </div>
    <p className={styles.stationCount}>{t("תחנה", "Station")} <bdi dir="ltr">{index + 1} / {steps.length}</bdi></p>
    <progress className={styles.progress} max={steps.length} value={index + 1} aria-label={t("מיקום בסיור", "Tour position")} />
    <h2 ref={inDialog ? undefined : heading} tabIndex={-1} className={styles.coachTitle} dir={proseDirection(step.title[lang], lang === "he" ? "rtl" : "ltr")}><BidiText>{step.title[lang]}</BidiText></h2>
    <p dir={proseDirection(step.body[lang], lang === "he" ? "rtl" : "ltr")}><BidiText>{step.body[lang]}</BidiText></p>
    <div className={styles.task} role="status" aria-live="polite">
      {ready && <Check size={18} aria-hidden="true" />}
      <div><strong>{ready ? t("התחנה הושלמה", "Stop complete") : t("עכשיו תורכם", "Your turn")}</strong><p><BidiText>{ready ? step.id === "goal" ? t("היעד שלכם מוכן באזור האישי.", "Your goal is ready in your personal area.") : t("אפשר להתנסות עוד או להמשיך.", "Keep experimenting, or continue when you’re ready.") : step.task[lang]}</BidiText></p></div>
    </div>
    <div className={styles.stepActions}>
      <button type="button" onClick={() => index > 0 && jump(steps[index - 1].id)} disabled={index === 0} aria-label={t("התחנה הקודמת", "Previous station")}><BackArrow size={18} /></button>
      <button type="button" className="primary" data-muxi-next onClick={() => advance()} disabled={!ready}>{index === steps.length - 1 ? t("סיום הסיור", "Finish tour") : t("ממשיכים", "Continue")}<NextArrow size={17} /></button>
    </div>
    <button type="button" className={styles.quiet} onClick={() => advance(true)}>{t("דלגו על התחנה הזאת", "Skip this station")}</button>
    <div className={styles.coachFooter}>
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
      <div className={styles.brand}><span dir="ltr">jobrun</span><span className={styles.brandDivider} /><h1 id={titleId}>{t("סיור עם מוקסי", "Tour with Muxi")}</h1></div>
      <div className={styles.headerActions}>
        {!preview && <UserInboxButton lang={lang} />}
        {controls}
        {!preview && <button type="button" className={styles.reportHelp} aria-label={t("נתקלתם בבעיה?", "Report a problem")} onClick={() => window.dispatchEvent(new Event(SUPPORT_OPEN_EVENT))}><CircleHelp size={17} />{t("דיווח", "Report")}</button>}
        <button type="button" className={styles.exit} onClick={close}><X size={17} aria-hidden="true" />{t("יציאה מהסיור", "Exit tour")}</button>
      </div>
    </header>
    {screen === "welcome" ? <main className={styles.welcome}>
      <div className={styles.welcomeHero}>
        <MuxiScene />
        <div className={styles.welcomeCopy}>
          <h2 ref={heading} tabIndex={-1}>{preview ? t("בואו ננסה שאלת ראיון.", "Let’s try an interview question.") : t("בואו נכין את התרגול שלכם.", "Let’s set up your practice.")}</h2>
          <p>{preview
            ? t("אני מוקסי. בואו ננסה שאלה מתוך ההכנה לראיונות חומרה ותוכנה. נחבר מעגל, נסביר פתרון במילים ונראה איך הערה אחת במשוב עוזרת לתקן אותו בקוד.", "I’m Muxi. Let’s try a question from JobRun’s hardware and software interview practice. Wire a circuit, explain a solution in words, then use feedback to fix it in code.")
            : t("אני מוקסי. נבחר יעד וזמן יומי שמתאים לכם. אחר כך ננסה את כלי התרגול ונראה איך תשובה מובילה למשוב ולשאלת המשך.", "I’m Muxi. We’ll start with your goal and the time you have each day. Then we’ll try the practice tools and follow an answer through feedback and a follow-up question.")}</p>
          <div className={styles.welcomeActions}>
            <button type="button" className="primary" data-muxi-start={canResume ? undefined : true} data-muxi-resume={canResume || undefined} disabled={!storageReady} onClick={() => start(canResume)}>
              {canResume ? t("להמשיך מהתחנה שלי", "Resume my tour") : preview ? t("להתנסות עם מוקסי", "Try it with Muxi") : t("להתחיל עם מוקסי", "Start with Muxi")}<NextArrow size={18} aria-hidden="true" />
            </button>
            {canResume && <button type="button" className={styles.quiet} data-muxi-start onClick={() => start()}>{t("מההתחלה", "Start over")}</button>}
            {preview && <a href="/#signin">{t("להרשמה או לכניסה", "Sign up or sign in")}</a>}
          </div>
          <p className={styles.scopeNote}>{canResume
            ? <><span>{t("המקום ששמרנו לכם", "Your saved stop")}</span> · <BidiText>{step.title[lang]}</BidiText></>
            : preview ? t("ההתנסות פתוחה לכולם ומשתמשת בנתוני דוגמה.", "Open to everyone, with sample data and no sign-up.")
            : t("היעד שתאשרו נשמר בחשבון. שאר התחנות הן תרגילי הדגמה.", "The goal you confirm is saved to your account. The other stops use practice examples.")}</p>
        </div>
      </div>
      <section className={styles.routePreview} aria-label={t("מה נעשה בסיור", "What you’ll try")}>
        <h3>{t("הדרך שלנו", "Our route")}</h3>
        <ol>{(preview ? [
          t("להכיר את המאגר ולשרטט מעגל", "Explore the library and draw a circuit"),
          t("לשפר פתרון בעזרת משוב", "Refine an answer with feedback"),
          t("לנסות ראיון בכתב", "Try a written interview"),
        ] : [
          t("לבחור יעד אישי", "Choose a personal goal"),
          t("לפתור ולקבל משוב", "Solve and get feedback"),
          t("להכיר את כלי האתר", "Explore the workspace"),
        ]).map((label, i) => <li key={i}><span className={styles.routeDot} aria-hidden="true" />{label}</li>)}</ol>
      </section>
    </main> : screen === "finish" ? <main className={styles.finish}>
      <MuxiScene finished />
      <h2 ref={heading} tabIndex={-1}>{preview ? t("בואו נתכונן לראיון הבא שלכם.", "Get ready for your next interview.") : t("נמשיך לתרגול?", "Ready to practice?")}</h2>
      <p>{preview ? t("פתחו חשבון ובנו תוכנית תרגול שמתאימה לתפקיד ולקצב שלכם. תוכלו לגלות נושאים נוספים במאגר, לקבל משוב אישי על הפתרונות שלכם ולתרגל בראיונות מדומים.", "Create an account to build a practice plan around your target role and the time you have. Explore more topics in the question library, get feedback on your solutions and practice in mock interviews.")
        : progress.completed.includes("goal") ? t("היעד שלכם זמין באזור האישי. שם אפשר לפתוח את התוכנית ולהמשיך לשאלה הבאה.", "Your goal is in your personal area. Open your plan there and continue with your next question.")
        : t("אפשר לבחור יעד באזור האישי או לגשת ישירות לשאלה במאגר.", "Set a goal in your personal area, or go straight to a question in the library.")}</p>
      <div className={styles.finishActions}>
        {preview ? <a className="primary" href="/#signup">{t("הירשמו עכשיו", "Sign up now")}<NextArrow size={17} aria-hidden="true" /></a> : <button type="button" className="primary" onClick={close}>{t("חזרה לאתר", "Back to JobRun")}<NextArrow size={17} /></button>}
        <button type="button" className={styles.quiet} onClick={() => start()}><RotateCcw size={15} />{t("להתחיל את הסיור מחדש", "Replay the tour")}</button>
      </div>
      {steps.some(s => !progress.completed.includes(s.id)) && <details className={styles.unfinished}>
        <summary>{t("תחנות שעוד אפשר לנסות", "Stops you can still try")}</summary>
        <ul>{steps.filter(s => !progress.completed.includes(s.id)).map(s => <li key={s.id}><button onClick={() => { jump(s.id); setScreen("tour"); }}><BidiText>{s.title[lang]}</BidiText><NextArrow size={15} /></button></li>)}</ul>
      </details>}
    </main> : <>
      <div className={styles.tourBar}>
        <span><BidiText>{step.chapter[lang]}</BidiText></span>
        <button type="button" aria-expanded={outline} aria-controls={outlineId} onClick={() => setOutline(!outline)}><List size={16} />{t("כל התחנות", "All stops")}<ChevronDown size={14} /></button>
        <span className={styles.localNote}>{step.id === "goal" && !preview ? t("היעד האישי שלכם", "Your account goal") : t("התנסות לדוגמה", "Sample workspace")}</span>
      </div>
      {outline && <nav id={outlineId} className={styles.outline} aria-label={t("תחנות הסיור", "Tour stops")}>{steps.map((s, i) => <button type="button" key={s.id} data-muxi-stop={s.id} onClick={() => jump(s.id)} aria-current={s.id === step.id ? "step" : undefined}><bdi>{i + 1}</bdi> <BidiText>{s.title[lang]}</BidiText>{progress.completed.includes(s.id) && <Check size={15} aria-label={t("התחנה הושלמה", "Completed")} />}</button>)}</nav>}
      <main className={styles.tourGrid}>
        {renderGuide()}
        <div className={styles.stage} data-muxi-stage data-muxi-exercise={step.exercise}>
          {isGuestExercise(step.exercise) ? <GuestTourExercises exercise={step.exercise} lang={lang} onAction={onAction} />
            : step.id === "goal" && !preview && userId ? <TourAccountGoal userId={userId} lang={lang} onSaved={() => onAction("goal-saved")} />
            : <TourExercises key={step.id} exercise={step.exercise} stationId={step.id} lang={lang} onAction={onAction} guide={<ExpandedCoach lang={lang} onExit={close}>{renderGuide(true)}</ExpandedCoach>} />}
        </div>
      </main>
      {!preview && <MuxiGuidance root={root} station={step.id} lang={lang} ready={ready} />}
      <div className={styles.mobileNav} data-muxi-mobile-nav>
        {preview ? <button type="button" className={styles.mobileBack} onClick={() => jump(steps[index - 1].id)} disabled={!index}>
          <BackArrow size={16} />{t("הקודמת", "Previous")}
        </button> : <button type="button" className={styles.mobileBack} onClick={() => heading.current?.scrollIntoView({ block: "center" })}>{t("בחזרה להדרכה", "Back to guidance")}<span><BidiText>{step.title[lang]}</BidiText></span></button>}
        <button type="button" className="primary" data-muxi-next disabled={!ready} onClick={() => advance()}>{index === steps.length - 1 ? t("סיום הסיור", "Finish tour") : t("הבא בסיור", "Next in tour")}<NextArrow size={16} /></button>
        <button type="button" className={styles.quiet} onClick={() => advance(true)}>{t("דלגו", "Skip")}</button>
      </div>
    </>}
  </div>;
}
