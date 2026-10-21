"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, RotateCcw, Search, Shuffle } from "lucide-react";
import { BidiText } from "./bidi-text";
import { StudyText } from "./question-materials";
import { filterQuickQuestions, quickQuestions, quickTopics, type QuickDiagram, type QuickTopic } from "../lib/fundamentals";
import { confirmQuickCompletion, filterQuickHistory, quickCompletionState, quickRevision, readQuickProgress, type QuickHistoryView, type QuickProgressApi } from "../lib/fundamentals-progress";
import type { FundamentalCompletion } from "../lib/practice-api";
import { shuffleQuestions, useQuestionOrderSeed } from "../lib/question-order";

export function QuickPractice({ lang, api, userId }: { lang: "he" | "en"; api: QuickProgressApi; userId: string }) {
  const [topic, setTopic] = useState<QuickTopic | "all">("all");
  const [query, setQuery] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const orderSeed = useQuestionOrderSeed();
  const orderedQuestions = useMemo(() => shuffleQuestions(quickQuestions, orderSeed, q => q.id), [orderSeed]);
  const [revealedId, setRevealedId] = useState<string | null>(null);
  const [historyView, setHistoryView] = useState<QuickHistoryView>("unanswered");
  const [records, setRecords] = useState<Record<string, FundamentalCompletion>>({});
  const [loadState, setLoadState] = useState<"loading" | "ready" | "error">("loading");
  const [refreshError, setRefreshError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<"save" | "version" | null>(null);
  const generation = useRef(0);
  const mutating = useRef(false);
  const hasLoadedHistory = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const emptyHeading = useRef<HTMLHeadingElement>(null);
  const filterToggle = useRef<HTMLButtonElement>(null);
  const focusQuestion = useRef(false);
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const matchingQuestions = filterQuickQuestions(topic, query, lang, orderedQuestions);
  const questions = loadState === "ready" ? filterQuickHistory(matchingQuestions, records, historyView) : [];
  const index = Math.max(0, questions.findIndex(q => q.id === selected));
  const question = questions[index];
  const revealed = question && revealedId === question.id;
  const record = question && records[question.id];
  const state = question && quickCompletionState(question, records);
  const completedCount = quickQuestions.filter(q => !!records[q.id]).length;
  const NextArrow = lang === "he" ? ArrowLeft : ArrowRight;
  const refresh = useCallback(async () => {
    if (mutating.current) return;
    const request = ++generation.current;
    if (!hasLoadedHistory.current) setLoadState("loading");
    try {
      const history = readQuickProgress(await api.fundamentalsProgress(userId));
      if (request === generation.current) {
        hasLoadedHistory.current = true;
        setRecords(history); setLoadState("ready"); setRefreshError(false);
      }
    } catch {
      if (request === generation.current) {
        if (hasLoadedHistory.current) setRefreshError(true);
        else setLoadState("error");
      }
    }
  }, [api, userId]);
  useEffect(() => {
    void refresh();
    const onFocus = () => { if (document.visibilityState === "visible") void refresh(); };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onFocus);
    return () => {
      generation.current++;
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onFocus);
    };
  }, [refresh]);
  useEffect(() => {
    if (focusQuestion.current) { (heading.current ?? emptyHeading.current)?.focus(); focusQuestion.current = false; }
  }, [question?.id, saving, records]);
  function choose(id: string) {
    focusQuestion.current = true;
    setSelected(id); setRevealedId(null); setSaveError(null);
    if (question.id === id) { heading.current?.focus(); focusQuestion.current = false; }
  }
  function reveal() {
    setRevealedId(question.id);
  }
  async function complete() {
    if (mutating.current || !question) return;
    mutating.current = true;
    const request = ++generation.current;
    const key = question.id;
    const next = questions[index + 1] ?? questions.find(q => q.id !== key);
    setSaving(true); setSaveError(null);
    try {
      const confirmed = confirmQuickCompletion(await api.completeFundamental(userId, key, quickRevision(key)), key);
      if (request !== generation.current) return;
      setRecords(old => ({ ...old, [key]: confirmed }));
      setRevealedId(null); focusQuestion.current = true;
      if (next) setSelected(next.id);
    } catch (error) {
      if (request === generation.current) {
        focusQuestion.current = true;
        setSaveError(error && typeof error === "object" && "code" in error && error.code === "stale_version" ? "version" : "save");
      }
    } finally {
      mutating.current = false;
      if (request === generation.current) setSaving(false);
    }
  }
  async function reset() {
    if (mutating.current || !question) return;
    mutating.current = true;
    const request = ++generation.current;
    const key = question.id;
    setSaving(true); setSaveError(null);
    try {
      const result = await api.resetFundamental(userId, key);
      if (typeof result.removed !== "boolean") throw new Error("Reset not confirmed");
      if (request !== generation.current) return;
      focusQuestion.current = true;
      setRecords(old => { const updated = { ...old }; delete updated[key]; return updated; });
    } catch {
      if (request === generation.current) { focusQuestion.current = true; setSaveError("save"); }
    } finally {
      mutating.current = false;
      if (request === generation.current) setSaving(false);
    }
  }
  return <section className="quick-practice" aria-label={t("תרגול יסודות קצר", "Quick fundamentals practice")}>
    <div className="quick-intro">
      <div><h1>{t("יסודות בקטנה", "A little practice")}</h1>
        <p>{t("שאלה קצרה, רעיון אחד. כמה רגעים לחזק את הבסיס לראיון הבא.", "One short question, one idea. A few moments to strengthen your interview foundations.")}</p></div>
      <p className="quick-total">{t(`${quickQuestions.length} שאלות קצרות`, `${quickQuestions.length} short questions`)}</p>
    </div>
    <div className="quick-history-views" role="group" aria-label={t("סינון לפי התרגול שלי", "Filter by my practice")}>
      {([
        ["unanswered", t("טרם סיימתי", "Not finished")],
        ["completed", t("כבר סיימתי", "Finished")],
        ["all", t("כל השאלות", "All questions")],
      ] as const).map(([value, label]) => <button key={value} disabled={saving} aria-pressed={historyView === value}
        className={historyView === value ? "active" : ""} onClick={() => { setHistoryView(value); setRevealedId(null); setSaveError(null); }}>{label}</button>)}
    </div>
    <button ref={filterToggle} className="quick-filter-toggle" onClick={() => setFiltersOpen(!filtersOpen)} aria-expanded={filtersOpen} aria-controls="quick-filters">
      <Search size={17} aria-hidden="true" />{t("נושא וחיפוש", "Topic and search")}{" · "}{topic === "all" ? t("הכול", "All") : quickTopics.find(item => item.id === topic)?.label[lang]}
    </button>
    <div id="quick-filters" className={`quick-controls ${filtersOpen ? "is-open" : ""}`}>
      <div className="quick-topics" role="group" aria-label={t("בחירת נושא", "Choose a topic")}>
        {[{ id: "all" as const, label: { he: "הכול", en: "All" } }, ...quickTopics].map(item =>
          <button key={item.id} disabled={saving} className={topic === item.id ? "active" : ""} aria-pressed={topic === item.id}
            onClick={() => { if (filtersOpen) filterToggle.current?.focus(); setTopic(item.id); setRevealedId(null); setFiltersOpen(false); }}>{item.label[lang]}</button>)}
      </div>
      <label className="quick-search"><Search size={18} aria-hidden="true" />
        <input type="search" disabled={saving} value={query} onChange={e => { setQuery(e.target.value); setRevealedId(null); }}
          placeholder={t("חיפוש שאלה קצרה", "Find a short question")} aria-label={t("חיפוש בשאלות הקצרות", "Search short questions")} /></label>
    </div>
    {loadState === "loading" && <p className="quick-progress-status" role="status">{t("טוענים את השאלות שכבר סיימתם…", "Loading your finished questions…")}</p>}
    {loadState === "error" && <div className="notice error" role="alert"><p>{t("לא הצלחנו לטעון את ההתקדמות. נטען אותה לפני שנציג שאלות, כדי להימנע מחזרות.", "We could not load your progress. Retry before continuing so finished questions are not repeated.")}</p>
      <button onClick={() => { focusQuestion.current = true; void refresh(); }}><RotateCcw size={16} />{t("ניסיון נוסף", "Try again")}</button></div>}
    {refreshError && <div className="notice error" role="alert"><p>{t("לא הצלחנו לרענן את ההיסטוריה. מוצגים הסימונים האחרונים שנטענו בחשבון.", "We could not refresh your history. The last loaded account history is still shown.")}</p>
      <button disabled={saving} onClick={() => { focusQuestion.current = true; void refresh(); }}><RotateCcw size={16} />{t("ניסיון נוסף", "Try again")}</button></div>}
    {question ? <>
      <div className="quick-position"><span aria-live="polite">{t(`שאלה ${index + 1} מתוך ${questions.length}`, `Question ${index + 1} of ${questions.length}`)}</span>
        <span>{t(`סיימתם ${completedCount} מתוך ${quickQuestions.length}`, `Finished ${completedCount} of ${quickQuestions.length}`)}</span></div>
      <article className="quick-sheet">
        <h2 ref={heading} tabIndex={-1}><BidiText>{question.title[lang]}</BidiText></h2>
        {record && <p className="quick-completed-label"><Check size={16} aria-hidden="true" />{state === "updated"
          ? t("כבר סיימתם; השאלה עודכנה מאז", "Previously finished; updated since then")
          : t("כבר סיימתם את השאלה הזאת", "You already finished this question")}{" · "}<time dateTime={record.completed_at}>{new Date(record.completed_at).toLocaleDateString(lang === "he" ? "he-IL" : "en-GB")}</time></p>}
        <StudyText text={question.prompt[lang]} />
        {question.code?.language === "python" && <p className="small muted">{t("המימוש המוצע כתוב בפייתון. דרך הפתרון מוסברת בקצרה בהמשך.", "The proposed implementation uses Python. A short explanation of the approach appears below.")}</p>}
        <p className="quick-think">{t("נסו לענות בראש לפני פתיחת הפתרון.", "Try answering in your head before opening the solution.")}</p>
        <button className={revealed ? "text-button quick-reveal" : "primary quick-reveal"} onClick={() => revealed ? setRevealedId(null) : reveal()} aria-expanded={!!revealed} aria-controls="quick-answer">
          {revealed ? t("הסתרת הפתרון", "Hide solution") : t("הצגת פתרון קצר", "Show short solution")}</button>
        {revealed && <section id="quick-answer" className="quick-answer" aria-label={t("פתרון קצר", "Short solution")}>
            <h3>{t("הפתרון בקצרה", "The short solution")}</h3>
            <StudyText text={question.answer[lang]} />
            {question.code && <pre className="code-block" dir="ltr" aria-label={`${question.code.language} ${t("קוד הפתרון", "solution code")}`}><code>{question.code.text}</code></pre>}
            {question.diagram && <QuickDiagramView diagram={question.diagram} lang={lang} />}
            <p className="quick-takeaway"><strong>{t("מה לוקחים הלאה?", "What carries over?")}</strong> <BidiText>{question.takeaway[lang]}</BidiText></p>
          </section>}
        <div className="quick-actions">
          {state !== "completed" && <button className="primary" disabled={saving} onClick={() => void complete()}>
            <Check size={17} aria-hidden="true" />{saving ? t("שומרים…", "Saving…") : t("סיימתי, לשאלה הבאה", "Finished, next question")}</button>}
          <button disabled={saving || index === questions.length - 1} onClick={() => choose(questions[index + 1].id)}>
            {t("דילוג", "Skip")}<NextArrow size={18} aria-hidden="true" /></button>
          <button disabled={saving || questions.length < 2} onClick={() => {
            const candidates = questions.filter(q => q.id !== question.id);
            choose(candidates[Math.floor(Math.random() * candidates.length)].id);
          }}><Shuffle size={17} aria-hidden="true" />{t("שאלה בהפתעה", "Surprise me")}</button>
          {index > 0 && <button className="text-button" disabled={saving} onClick={() => choose(questions[index - 1].id)}>{t("הקודמת", "Previous")}</button>}
          {record && <button className="text-button" disabled={saving} onClick={() => void reset()}>{t("סימון כטרם סיימתי", "Mark as not finished")}</button>}
        </div>
        {saveError && <div className="notice error" role="alert">{saveError === "version"
          ? <><p>{t("השאלה עודכנה. רעננו את העמוד לפני שמירת הסימון.", "This question was updated. Reload the page before saving completion.")}</p><button onClick={() => window.location.reload()}>{t("רענון העמוד", "Reload page")}</button></>
          : <p>{t("לא הצלחנו לאשר את השמירה. נשארתם בשאלה הזאת; אפשר לנסות שוב באותו כפתור.", "The save could not be confirmed. You are still on this question; retry using the same button.")}</p>}</div>}
        <p className="quick-save-explanation">{t("״סיימתי״ נשמר בחשבון שלכם. פתיחת פתרון או דילוג אינם מסמנים שסיימתם, והסימון אינו ציון על נכונות התשובה.", "‘Finished’ is saved to your account. Opening a solution or skipping does not mark completion, and completion does not grade correctness.")}</p>
      </article>
    </> : loadState === "ready" && <div className="quick-empty" role="status"><h2 ref={emptyHeading} tabIndex={-1}>{historyView === "unanswered" && matchingQuestions.length
        ? t("סיימתם את כל השאלות בתצוגה הזאת", "You finished every question in this view")
        : t("אין שאלות בתצוגה הזאת", "No questions in this view")}</h2>
      <p>{t("אפשר לבחור נושא אחר או לחזור לשאלות שכבר סיימתם.", "Choose another topic or revisit your finished questions.")}</p>
      <button onClick={() => { setQuery(""); setTopic("all"); setHistoryView("all"); }}>{t("הצגת כל השאלות", "Show all questions")}</button></div>}
    <p className="quick-editorial-note">{t("תרגילים מקוריים עם פתרונות מוצעים שטרם נבדקו בידי אנשים. תרגול עצמי ללא ציון.", "Original exercises with proposed solutions awaiting human review. Self-study without a grade.")}</p>
  </section>;
}

export function QuickDiagramView({ diagram, lang }: { diagram: QuickDiagram; lang: "he" | "en" }) {
  const marker = `quick-arrow-${useId().replace(/:/g, "")}`;
  const label = lang === "he" ? "שרטוט הפתרון" : "Solution diagram";
  const defs = <defs><marker id={marker} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="currentColor" /></marker></defs>;
  const arrow = `url(#${marker})`;
  if (diagram.kind === "gate") {
    const dataInputs = diagram.gate === "MUX" ? diagram.inputs.slice(0, 2) : diagram.inputs;
    return <figure className="quick-diagram"><svg viewBox="0 0 380 170" role="img" aria-label={`${label}: ${diagram.gate}`} direction="ltr">
      <title>{`${label}: ${diagram.gate}`}</title>{defs}
      <rect x="140" y="35" width="110" height="85" rx="7" className="quick-svg-node" />
      <text x="195" y="82" textAnchor="middle" className="quick-svg-gate">{diagram.gate}</text>
      {dataInputs.map((input, i) => { const y = dataInputs.length === 1 ? 77 : 58 + i * 38;
        return <g key={input}><text x="12" y={y + 5} className={input.length > 3 ? "quick-svg-small" : undefined}>{input}</text><path d={`M86 ${y} H137`} markerEnd={arrow} />
          {diagram.gate === "MUX" && <text x="152" y={y + 5} className="quick-svg-small">{i}</text>}</g>;
      })}
      <path d="M250 77 H325" markerEnd={arrow} /><text x="336" y="82">{diagram.output}</text>
      {diagram.gate === "MUX" && <><path d="M195 157 V123" markerEnd={arrow} /><text x="210" y="154">{diagram.inputs[2]}</text></>}
    </svg><figcaption>{label}</figcaption></figure>;
  }
  const positions = new Map(diagram.states.map((state, i) => [state, diagram.states.length === 1 ? 190 : 70 + i * 240 / (diagram.states.length - 1)]));
  return <figure className="quick-diagram"><svg viewBox="0 0 380 260" role="img" aria-label={label} direction="ltr">
    <title>{label}</title>{defs}
    <path d={`M${positions.get(diagram.initial)! - 58} 132 H${positions.get(diagram.initial)! - 28}`} markerEnd={arrow} />
    {diagram.transitions.map((edge, i) => {
      const from = positions.get(edge.from)!, to = positions.get(edge.to)!;
      if (from === to) return <g key={i}><path d={`M${from - 17} 111 C${from - 65} 22 ${from + 65} 22 ${from + 17} 111`} markerEnd={arrow} /><text x={from} y="52" textAnchor="middle" className="quick-svg-small">{edge.label}</text></g>;
      const forward = from < to, distance = Math.abs(to - from), direction = distance > 200 ? (forward ? 1 : -1) : (forward ? -1 : 1);
      const bend = distance > 200 ? 88 : 48;
      return <g key={i}><path d={`M${from + (forward ? 23 : -23)} ${132 + direction * 9} Q${(from + to) / 2} ${132 + direction * bend * 2} ${to + (forward ? -25 : 25)} ${132 + direction * 9}`} markerEnd={arrow} />
        <text x={(from + to) / 2} y={132 + direction * (bend + 10)} textAnchor="middle" className="quick-svg-small">{edge.label}</text></g>;
    })}
    {diagram.states.map(state => <g key={state}><circle cx={positions.get(state)} cy="132" r="25" className="quick-svg-node" /><text x={positions.get(state)} y="137" textAnchor="middle">{state}</text></g>)}
  </svg><figcaption>{lang === "he" ? "חץ ללא מקור מסמן את מצב ההתחלה. כיתובי החצים מתארים קלט, ולעיתים גם פלט, לפי השאלה." : "The incoming arrow marks the initial state. Transition labels describe inputs and, where specified, outputs."}</figcaption></figure>;
}
