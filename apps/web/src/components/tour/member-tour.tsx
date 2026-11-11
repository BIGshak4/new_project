"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { usePathname } from "next/navigation";
import { ArrowLeft, ArrowRight, Check, ChevronDown, List, LocateFixed, Pause, Play, RotateCcw, X } from "lucide-react";
import { observeAuthUser } from "../../lib/auth-access";
import { supabase } from "../../lib/supabase";
import { practiceApi } from "../../lib/practice-api";
import { questionCategory } from "../../lib/question-discovery";
import { readWorkspaceRoute, type WorkspaceRoute } from "../../lib/workspace-route";
import { MEMBER_TOUR_ACTION_EVENT, MEMBER_TOUR_NAVIGATE_EVENT, MEMBER_TOUR_START_EVENT, advanceMemberTour,
  completeMemberTourTask, initialMemberTourProgress, memberTaskKey, memberTourKey, memberTourStepReady,
  memberTourSteps, moveMemberTour, parseMemberTourProgress, type MemberTourAction, type MemberTourProgress,
  type MemberTourStep } from "../../lib/member-tour";
import { BidiText } from "../bidi-text";
import { MuxiMascot } from "./muxi-mascot";
import styles from "./member-tour.module.css";

type Lang = "he" | "en";
type Screen = "closed" | "welcome" | "tour" | "finish";
type PracticeContext = { userId: string; questionKey: string; subject: string; attemptId?: string; submitted?: boolean };
const visible = (element: HTMLElement) => !!element.getClientRects().length && !element.closest("[hidden], [inert]");

/** A single account-scoped coach accompanies the actual workspace across routes. */
export function MemberTour() {
  const [userId, setUserId] = useState<string>();
  const [lang, setLang] = useState<Lang>("he");
  const pathname = usePathname();
  useEffect(() => observeAuthUser(supabase.auth, user => setUserId(user?.id)), []);
  useEffect(() => {
    const sync = () => setLang(document.documentElement.lang.startsWith("en") ? "en" : "he");
    sync();
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
    return () => observer.disconnect();
  }, []);
  if (!userId || !(pathname === "/" || pathname === "/games" || pathname === "/games/shop" || pathname.startsWith("/duel/"))) return null;
  return <AccountTour key={userId} userId={userId} lang={lang} />;
}

function AccountTour({ userId, lang }: { userId: string; lang: Lang }) {
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const [api] = useState(() => practiceApi());
  const [progress, setProgress] = useState(() => initialMemberTourProgress(userId));
  const [screen, setScreen] = useState<Screen>("closed");
  const [ready, setReady] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [outline, setOutline] = useState(false);
  const [selectedTask, setSelectedTask] = useState<string>();
  const [target, setTarget] = useState<HTMLElement | null>(null);
  const [modalHost, setModalHost] = useState<HTMLElement | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const panel = useRef<HTMLElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const previousFocus = useRef<HTMLElement | null>(null);
  const practice = useRef<Record<string, PracticeContext>>({});
  const alive = useRef(true);
  const navigation = useRef(0);
  const key = memberTourKey(userId), activeKey = `${key}:active`, contextKey = `${key}:questions`;
  const index = Math.max(0, memberTourSteps.findIndex(step => step.id === progress.stepId));
  const step = memberTourSteps[index];
  const done = (id: string) => progress.completedTasks.includes(memberTaskKey(step.id, id));
  const task = step.tasks.find(item => item.id === selectedTask) ?? step.tasks.find(item => !done(item.id)) ?? step.tasks.at(-1)!;
  const stepReady = memberTourStepReady(step, progress);
  const allDone = step.tasks.every(item => done(item.id));
  const Next = lang === "he" ? ArrowLeft : ArrowRight;
  const Back = lang === "he" ? ArrowRight : ArrowLeft;

  useEffect(() => {
    alive.current = true;
    try {
      const saved = parseMemberTourProgress(localStorage.getItem(key), userId);
      setProgress(saved);
      if (saved.status === "active" && sessionStorage.getItem(activeKey) === "1") setScreen("tour");
      const contexts: unknown = JSON.parse(sessionStorage.getItem(contextKey) ?? "{}");
      if (contexts && typeof contexts === "object") for (const subject of ["software", "hardware"]) {
        const item = (contexts as Record<string, PracticeContext>)[subject];
        if (item?.userId === userId && typeof item.questionKey === "string" && item.subject === subject && (!item.attemptId || typeof item.attemptId === "string")) practice.current[subject] = item;
      }
    } catch { /* The tour is usable with browser storage disabled. */ }
    setReady(true);
    return () => { alive.current = false; navigation.current++; };
  }, [key, userId, activeKey, contextKey]);
  useEffect(() => {
    if (!ready) return;
    try {
      localStorage.setItem(key, JSON.stringify(progress));
      if (screen === "tour") sessionStorage.setItem(activeKey, "1");
      else sessionStorage.removeItem(activeKey);
    } catch {}
  }, [key, activeKey, progress, screen, ready]);
  useEffect(() => {
    const open = (event: Event) => {
      if ((event as CustomEvent<{ userId: string }>).detail?.userId === userId) {
        previousFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        setScreen("welcome"); setCollapsed(false);
      }
    };
    const remember = (event: Event) => {
      const value = (event as CustomEvent<PracticeContext>).detail;
      if (value?.userId !== userId || !["software", "hardware"].includes(value.subject)) return;
      practice.current[value.subject] = value;
      try { sessionStorage.setItem(contextKey, JSON.stringify(practice.current)); } catch {}
    };
    window.addEventListener(MEMBER_TOUR_START_EVENT, open);
    window.addEventListener("jobrun:member-tour-practice", remember);
    return () => { window.removeEventListener(MEMBER_TOUR_START_EVENT, open); window.removeEventListener("jobrun:member-tour-practice", remember); };
  }, [userId, contextKey]);
  useEffect(() => {
    if (screen === "closed") return;
    heading.current?.focus({ preventScroll: true });
    const escape = (event: KeyboardEvent) => {
      if (event.key !== "Escape" || event.defaultPrevented || document.querySelector("dialog:modal") || (event.target instanceof Element && event.target.closest(".cm-editor, [data-personal-helper]"))) return;
      event.preventDefault(); pause();
    };
    document.addEventListener("keydown", escape);
    return () => document.removeEventListener("keydown", escape);
  }, [screen]);

  const complete = useCallback((id: string) => {
    setProgress(previous => completeMemberTourTask(previous, step.id, id));
    setSelectedTask(undefined);
  }, [step.id]);
  const completeSuccess = useCallback((action: string) => {
    const milestone = step.tasks.findIndex(item => item.event === action);
    if (milestone < 0) return;
    // Once the real operation succeeds, earlier editing instructions may be read-only.
    // Continue at the result instead of asking the learner to reopen obsolete controls.
    setProgress(previous => step.tasks.slice(0, milestone + 1).reduce((value, item) => completeMemberTourTask(value, step.id, item.id), previous));
    setSelectedTask(undefined);
  }, [step]);
  useEffect(() => {
    if (screen !== "tour") return;
    const receive = (event: Event) => {
      const detail = (event as CustomEvent<MemberTourAction>).detail;
      if (detail?.userId !== userId) return;
      completeSuccess(detail.action);
    };
    window.addEventListener(MEMBER_TOUR_ACTION_EVENT, receive);
    return () => window.removeEventListener(MEMBER_TOUR_ACTION_EVENT, receive);
  }, [screen, userId, completeSuccess]);

  // Reserve room for the coach; never make the product inert or intercept its controls.
  useEffect(() => {
    if (screen === "closed") return;
    const html = document.documentElement;
    html.dataset.memberTourActive = "true";
    html.dataset.memberTourStep = screen === "tour" ? step.id : screen;
    html.dataset.memberTourCompact = String(collapsed);
    return () => {
      delete html.dataset.memberTourActive; delete html.dataset.memberTourStep; delete html.dataset.memberTourCompact;
      html.style.removeProperty("--member-coach-height");
    };
  }, [screen, step.id, collapsed]);
  useEffect(() => {
    if (!panel.current || screen === "closed") return;
    const measure = () => document.documentElement.style.setProperty("--member-coach-height", `${panel.current?.getBoundingClientRect().height ?? 0}px`);
    const observer = new ResizeObserver(measure);
    observer.observe(panel.current); measure();
    return () => observer.disconnect();
  }, [screen, collapsed, modalHost]);

  // Native editor/report dialogs live in the top layer. Put a compact guide inside them.
  useEffect(() => {
    if (screen !== "tour") return;
    let dialog: HTMLDialogElement | null = null, host: HTMLDivElement | null = null;
    const sync = () => {
      const next = document.querySelector<HTMLDialogElement>("dialog:modal");
      if (next === dialog) return;
      host?.remove(); dialog = next;
      host = next ? document.createElement("div") : null;
      if (next && host) { host.dataset.memberTourModalHost = ""; next.prepend(host); }
      setModalHost(host);
    };
    const observer = new MutationObserver(sync);
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["open"] });
    sync();
    return () => { observer.disconnect(); host?.remove(); setModalHost(null); };
  }, [screen]);

  useEffect(() => {
    if (screen !== "tour") { setTarget(null); return; }
    let highlighted: HTMLElement | null = null, frame = 0;
    const scan = () => {
      frame = 0;
      const scope = document.querySelector("dialog:modal") ?? document;
      const next = task.selector ? [...scope.querySelectorAll<HTMLElement>(task.selector)].find(element => visible(element) && !element.matches(":disabled") && !element.closest("[data-member-coach]")) ?? null : null;
      if (next !== highlighted) {
        highlighted?.removeAttribute("data-member-spotlight");
        highlighted = next;
        highlighted?.setAttribute("data-member-spotlight", "true");
        setTarget(next);
      }
      if (step.id === "code" && document.querySelector('[data-member-feedback-ready="true"]')) {
        const feedback = step.tasks.find(item => item.event === "feedback-ready");
        if (feedback && !progress.completedTasks.includes(memberTaskKey(step.id, feedback.id))) completeSuccess("feedback-ready");
      }
      if (step.id === "games" && document.querySelector('[data-member-tour="game-practice-result"]')) {
        const answer = step.tasks.find(item => item.event === "game-practice-answered");
        if (answer && !progress.completedTasks.includes(memberTaskKey(step.id, answer.id))) completeSuccess("game-practice-answered");
      }
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(scan); };
    const act = (event: Event) => {
      if (task.event || !task.selector || !(event.target instanceof Element) || event.target.closest("[data-member-coach]")) return;
      const match = event.target.closest<HTMLElement>(task.selector);
      if (!match || !visible(match) || match.matches(":disabled")) return;
      // Text entry is acknowledged after input, rather than just focusing an empty editor.
      if (match.matches("input, textarea, [contenteditable]")) {
        if (event.type !== "input" && event.type !== "change") return;
        if (!(match as HTMLInputElement).value?.trim() && !match.textContent?.trim()) return;
      } else if (event.type !== "click") return;
      complete(task.id);
    };
    const observer = new MutationObserver(schedule);
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["open", "disabled", "data-member-feedback-ready"] });
    document.addEventListener("click", act, true); document.addEventListener("input", act, true); document.addEventListener("change", act, true);
    schedule();
    return () => {
      observer.disconnect(); cancelAnimationFrame(frame); highlighted?.removeAttribute("data-member-spotlight");
      document.removeEventListener("click", act, true); document.removeEventListener("input", act, true); document.removeEventListener("change", act, true);
    };
  }, [screen, step, task, progress.completedTasks, complete, completeSuccess]);

  function locate() {
    if (!target) return;
    target.scrollIntoView({ block: "center", behavior: "instant" });
    const focusable = target.matches("button,summary,input,textarea,select,[tabindex]") ? target : target.querySelector<HTMLElement>("button,summary,input,textarea,select,[tabindex]");
    focusable?.focus({ preventScroll: true });
    if (window.innerWidth < 1100) setCollapsed(true);
  }
  function navigate(route: WorkspaceRoute) {
    if (window.location.pathname === "/") window.dispatchEvent(new CustomEvent(MEMBER_TOUR_NAVIGATE_EVENT, { detail: { userId, route } }));
    else {
      const query = new URLSearchParams({ view: route.view, nav: "1" });
      if (route.attempt) query.set("attempt", route.attempt);
      else if (route.question) query.set("question", route.question);
      window.location.assign(`/?${query}`);
    }
  }
  async function visit(destination: MemberTourStep) {
    const request = ++navigation.current;
    setError(""); setBusy(true);
    try {
      if (destination.questionSubject) {
        const subject = destination.questionSubject;
        let context = practice.current[subject];
        // A completed answer is read-only. Opening its question again only reads the prompt;
        // the learner still explicitly starts a new attempt with the normal account button.
        if (context?.submitted && destination.id === "explanation") context = { ...context, attemptId: undefined, submitted: false };
        if (!context) {
          const bank = (await api.listQuestions(lang)).filter(question => questionCategory(question) === subject);
          if (!alive.current || request !== navigation.current) return;
          const question = bank.find(q => /maximum|max-array|מקסימום/i.test(q.title)) ?? bank[0];
          if (!question) throw new Error("empty");
          context = { userId, subject, questionKey: question.key };
          practice.current[subject] = context;
        }
        const current = readWorkspaceRoute(window.location.search).route;
        if (window.location.pathname !== "/" || (context.attemptId ? current.attempt !== context.attemptId : current.question !== context.questionKey)) {
          navigate({ view: "library", ...(context.attemptId ? { attempt: context.attemptId } : { question: context.questionKey }) });
        }
      } else if (destination.href.startsWith("/?")) navigate(readWorkspaceRoute(destination.href.slice(1)).route);
      else if (window.location.pathname !== destination.href) window.location.assign(destination.href);
    } catch {
      if (alive.current && request === navigation.current) setError(t("לא הצלחנו לפתוח את השאלה. אפשר לנסות שוב או לבחור שאלה ישירות במאגר.", "We couldn’t open the question. Try again or choose one directly from the library."));
    } finally { if (alive.current && request === navigation.current) setBusy(false); }
  }
  function start(resume: boolean) {
    if (!resume) { practice.current = {}; try { sessionStorage.removeItem(contextKey); } catch {} }
    const next = moveMemberTour(resume ? progress : initialMemberTourProgress(userId), resume ? progress.stepId : memberTourSteps[0].id);
    persistActive(next);
    setProgress(next); setScreen("tour"); setOutline(false); setSelectedTask(undefined);
    void visit(memberTourSteps.find(item => item.id === next.stepId)!);
  }
  function pause() {
    navigation.current++; setBusy(false);
    setProgress(previous => ({ ...previous, status: "paused", updatedAt: Date.now() })); setScreen("closed");
    requestAnimationFrame(() => { if (previousFocus.current?.isConnected) previousFocus.current.focus({ preventScroll: true }); });
  }
  function next(skip = false) {
    const updated = advanceMemberTour(progress, skip);
    if (updated === progress) return;
    persistActive(updated);
    setProgress(updated); setSelectedTask(undefined); setCollapsed(false);
    if (updated.status === "completed") setScreen("finish");
    else void visit(memberTourSteps.find(item => item.id === updated.stepId)!);
  }
  function jump(id: string) {
    const updated = moveMemberTour(progress, id);
    persistActive(updated);
    setProgress(updated); setSelectedTask(undefined); setOutline(false); setScreen("tour");
    void visit(memberTourSteps.find(item => item.id === id)!);
  }
  function persistActive(next: MemberTourProgress) {
    try {
      localStorage.setItem(key, JSON.stringify(next));
      if (next.status === "active") sessionStorage.setItem(activeKey, "1");
      else sessionStorage.removeItem(activeKey);
    } catch {}
  }
  if (screen === "closed") return null;
  const content = <aside ref={panel} className={styles.coach} data-member-coach data-compact={collapsed} data-in-modal={!!modalHost} dir={lang === "he" ? "rtl" : "ltr"} aria-label={t("הסיור האישי עם מוקסי", "Your live tour with Muxi")}>
    <header className={styles.header}>
      <MuxiMascot pose={screen === "finish" || (screen === "tour" && stepReady) ? "celebrate" : "wave"} className={styles.mascot} />
      <button type="button" className={styles.toggle} onClick={() => setCollapsed(!collapsed)} aria-expanded={!collapsed} aria-controls="member-tour-content">
        <strong>{t("עם מוקסי באתר", "Explore with Muxi")}</strong>
        <span>{screen === "tour" ? <><bdi>{index + 1}/{memberTourSteps.length}</bdi> · {step.chapter[lang]}</> : t("ההדרכה שלכם, בקצב שלכם", "Real practice, at your pace")}</span><ChevronDown size={16} />
      </button>
      <button type="button" className={styles.close} onClick={pause} aria-label={t("עצירת הסיור ושמירת המקום", "Pause tour and save my place")}><X size={18} /></button>
    </header>
    {!collapsed && <div id="member-tour-content" className={styles.content}>
      {screen === "welcome" ? <>
        <h2 ref={heading} tabIndex={-1}>{t("בואו נכין אתכם לראיון הבא.", "Let’s get ready for your next interview.")}</h2>
        <p>{t("אני מוקסי. נגדיר יחד את היעד שלכם, נבחר שאלות מהמאגר ונכיר את כל כלי האתר תוך כדי שימוש בהם.", "I’m Muxi. We’ll set your goal, choose questions from the bank and learn the site’s tools by using them.")}</p>
        <p className={styles.note}>{t("זה החשבון שלכם. יעד שתשמרו, תשובות שתשלחו ורכישות שתאשרו יישמרו כרגיל. אפשר לדלג, לעצור ולחזור לכל תחנה.", "This is your account. Saved goals, submitted answers and purchases you confirm work as usual. Skip, pause or return to any stop.")}</p>
        <button className="primary" disabled={!ready} onClick={() => start(progress.updatedAt > 0 && progress.status !== "completed")}><Play size={17} />{progress.updatedAt > 0 && progress.status !== "completed" ? t("ממשיכים מהמקום שלי", "Resume my tour") : t("מתחילים יחד", "Let’s begin")}</button>
        {progress.updatedAt > 0 && <button className={styles.quiet} onClick={() => start(false)}><RotateCcw size={15} />{t("להתחיל מההתחלה", "Start again")}</button>}
      </> : screen === "finish" ? <>
        <h2 ref={heading} tabIndex={-1}>{t("עכשיו האתר כבר שלכם.", "Make JobRun your own.")}</h2>
        <p>{t("התרגול, השאלות והכלים מחכים לכם. חזרו להמלצות באזור האישי, והעוזר האישי יישאר כאן כשצריך הכוונה.", "Your practice, questions and tools are ready. Return to your personal recommendations. The helper is here whenever you need direction.")}</p>
        <button className="primary" onClick={() => { navigate({ view: "learn" }); setScreen("closed"); }}>{t("לאזור האישי שלי", "My personal area")}<Next size={16} /></button>
        <button className={styles.quiet} onClick={() => setOutline(!outline)}><List size={16} />{t("לחזור לתחנה בסיור", "Revisit a stop")}</button>
      </> : <>
        <progress className={styles.progress} value={index + 1} max={memberTourSteps.length} aria-label={t("התקדמות בסיור", "Tour progress")} />
        <h2 ref={heading} tabIndex={-1}><BidiText>{step.title[lang]}</BidiText></h2>
        <p><BidiText>{step.body[lang]}</BidiText></p>
        <div className={styles.task} aria-live="polite" aria-atomic="true">
          <strong>{allDone ? t("אפשר להמשיך לתחנה הבאה", "Ready for the next stop") : t("ננסה את זה יחד", "Let’s try it together")}</strong>
          <p><BidiText>{task.text[lang]}</BidiText></p>
        </div>
        <div className={styles.taskActions}>
          <button disabled={!target} onClick={locate}><LocateFixed size={16} />{t("איפה לוחצים?", "Show me where")}</button>
          {!task.event && !done(task.id) && <button onClick={() => complete(task.id)}>{t("הבנתי, לצעד הבא", "Got it, next step")}<Next size={15} /></button>}
        </div>
        {step.id === "goal" && !stepReady && <KeepGoal userId={userId} lang={lang} onKeep={() => completeSuccess("goal-saved")} />}
        <details className={styles.checklist}><summary>{t("הצעדים בתחנה הזאת", "Steps at this stop")}</summary><ol>{step.tasks.map(item => <li key={item.id}>
          <button type="button" onClick={() => setSelectedTask(item.id)} aria-current={item.id === task.id ? "step" : undefined}>{done(item.id) && <Check size={15} />}<BidiText>{item.text[lang]}</BidiText></button>
        </li>)}</ol></details>
        <button className={styles.quiet} disabled={busy} onClick={() => void visit(step)}>{busy ? t("פותחים…", "Opening…") : t("לפתוח את העמוד של התחנה", "Open this stop’s page")}</button>
        {error && <p role="alert">{error}</p>}
        <div className={styles.navigation}>
          <button disabled={!index || busy} onClick={() => jump(memberTourSteps[index - 1].id)} aria-label={t("התחנה הקודמת", "Previous stop")}><Back size={17} /></button>
          <button className="primary" disabled={!stepReady || busy} onClick={() => next()}>{index === memberTourSteps.length - 1 ? t("מסיימים את הסיור", "Finish tour") : t("לתחנה הבאה", "Next stop")}<Next size={17} /></button>
        </div>
        <div className={styles.footer}>
          <button onClick={() => next(true)} disabled={busy}>{t("דלגו על התחנה", "Skip this stop")}</button>
          <button onClick={() => setOutline(!outline)} aria-expanded={outline}><List size={15} />{t("כל התחנות", "All stops")}</button>
        </div>
      </>}
      {outline && <nav className={styles.outline} aria-label={t("תחנות הסיור", "Tour stops")}>{memberTourSteps.map((item, i) => <button key={item.id} onClick={() => jump(item.id)} aria-current={step.id === item.id ? "step" : undefined}><bdi>{i + 1}</bdi>{item.chapter[lang]}{memberTourStepReady(item, progress) && <Check size={15} />}</button>)}</nav>}
      <button className={styles.pause} onClick={pause}><Pause size={14} />{t("לעצור ולהמשיך אחר כך", "Pause and return later")}</button>
    </div>}
  </aside>;
  return modalHost ? createPortal(content, modalHost) : content;
}

function KeepGoal({ userId, lang, onKeep }: { userId: string; lang: Lang; onKeep: () => void }) {
  const [complete, setComplete] = useState(false);
  useEffect(() => {
    let current = true;
    void practiceApi().getGoal(lang, userId).then(goal => { if (current) setComplete(goal.complete); }).catch(() => {});
    return () => { current = false; };
  }, [userId, lang]);
  return complete ? <button className={styles.quiet} data-member-tour="goal-keep" onClick={onKeep}>{lang === "he" ? "היעד הקיים מתאים לי, נמשיך איתו" : "My current goal fits, keep it"}</button> : null;
}
