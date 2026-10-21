"use client";

import { useEffect, useId, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Search, Shuffle } from "lucide-react";
import { BidiText } from "./bidi-text";
import { StudyText } from "./question-materials";
import { filterQuickQuestions, quickQuestions, quickTopics, type QuickDiagram, type QuickTopic } from "../lib/fundamentals";

export function QuickPractice({ lang }: { lang: "he" | "en" }) {
  const [topic, setTopic] = useState<QuickTopic | "all">("all");
  const [query, setQuery] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selected, setSelected] = useState(quickQuestions[0].id);
  const [revealedId, setRevealedId] = useState<string | null>(null);
  const [seen, setSeen] = useState<Set<string>>(() => new Set());
  const heading = useRef<HTMLHeadingElement>(null);
  const filterToggle = useRef<HTMLButtonElement>(null);
  const focusQuestion = useRef(false);
  const t = (he: string, en: string) => lang === "he" ? he : en;
  const questions = filterQuickQuestions(topic, query, lang);
  const index = Math.max(0, questions.findIndex(q => q.id === selected));
  const question = questions[index];
  const revealed = question && revealedId === question.id;
  const NextArrow = lang === "he" ? ArrowLeft : ArrowRight;
  useEffect(() => {
    if (focusQuestion.current) { heading.current?.focus(); focusQuestion.current = false; }
  }, [question?.id]);
  function choose(id: string) {
    focusQuestion.current = true;
    setSelected(id); setRevealedId(null);
    if (question.id === id) { heading.current?.focus(); focusQuestion.current = false; }
  }
  function reveal() {
    setRevealedId(question.id);
    setSeen(old => new Set(old).add(question.id));
  }
  return <section className="quick-practice" aria-label={t("תרגול יסודות קצר", "Quick fundamentals practice")}>
    <div className="quick-intro">
      <div><h1>{t("יסודות בקטנה", "A little practice")}</h1>
        <p>{t("שאלה קצרה, רעיון אחד. כמה רגעים לחזק את הבסיס לראיון הבא.", "One short question, one idea. A few moments to strengthen your interview foundations.")}</p></div>
      <p className="quick-total">{t(`${quickQuestions.length} שאלות קצרות`, `${quickQuestions.length} short questions`)}</p>
    </div>
    <button ref={filterToggle} className="quick-filter-toggle" onClick={() => setFiltersOpen(!filtersOpen)} aria-expanded={filtersOpen} aria-controls="quick-filters">
      <Search size={17} aria-hidden="true" />{t("נושא וחיפוש", "Topic and search")}{" · "}{topic === "all" ? t("הכול", "All") : quickTopics.find(item => item.id === topic)?.label[lang]}
    </button>
    <div id="quick-filters" className={`quick-controls ${filtersOpen ? "is-open" : ""}`}>
      <div className="quick-topics" role="group" aria-label={t("בחירת נושא", "Choose a topic")}>
        {[{ id: "all" as const, label: { he: "הכול", en: "All" } }, ...quickTopics].map(item =>
          <button key={item.id} className={topic === item.id ? "active" : ""} aria-pressed={topic === item.id}
            onClick={() => { if (filtersOpen) filterToggle.current?.focus(); setTopic(item.id); setRevealedId(null); setFiltersOpen(false); }}>{item.label[lang]}</button>)}
      </div>
      <label className="quick-search"><Search size={18} aria-hidden="true" />
        <input type="search" value={query} onChange={e => { setQuery(e.target.value); setRevealedId(null); }}
          placeholder={t("חיפוש שאלה קצרה", "Find a short question")} aria-label={t("חיפוש בשאלות הקצרות", "Search short questions")} /></label>
    </div>
    {question ? <>
      <div className="quick-position"><span aria-live="polite">{t(`שאלה ${index + 1} מתוך ${questions.length}`, `Question ${index + 1} of ${questions.length}`)}</span>
        <span>{t(`פתרונות שנפתחו בביקור: ${seen.size}`, `Solutions opened this visit: ${seen.size}`)}</span></div>
      <article className="quick-sheet">
        <h2 ref={heading} tabIndex={-1}><BidiText>{question.title[lang]}</BidiText></h2>
        <StudyText text={question.prompt[lang]} />
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
          <button className={revealed ? "primary" : ""} disabled={index === questions.length - 1} onClick={() => choose(questions[index + 1].id)}>
            {t("השאלה הבאה", "Next question")}<NextArrow size={18} aria-hidden="true" /></button>
          <button disabled={questions.length < 2} onClick={() => {
            const candidates = questions.filter(q => q.id !== question.id);
            choose(candidates[Math.floor(Math.random() * candidates.length)].id);
          }}><Shuffle size={17} aria-hidden="true" />{t("שאלה בהפתעה", "Surprise me")}</button>
          {index > 0 && <button className="text-button" onClick={() => choose(questions[index - 1].id)}>{t("הקודמת", "Previous")}</button>}
          {index === questions.length - 1 && <p role="status">{t("הגעתם לסוף הרשימה. אפשר לבחור נושא אחר או להתחיל מחדש.", "You reached the end. Choose another topic or start again.")} <button className="text-button" onClick={() => choose(questions[0].id)}>{t("מההתחלה", "Start again")}</button></p>}
        </div>
      </article>
    </> : <div className="quick-empty" role="status"><p>{t("לא נמצאו שאלות. נסו ביטוי אחר או נושא אחר.", "No questions found. Try another search or topic.")}</p>
      <button onClick={() => { setQuery(""); setTopic("all"); }}>{t("הצגת כל השאלות", "Show all questions")}</button></div>}
    <p className="quick-editorial-note">{t("תרגילים מקוריים חדשים, עם פתרונות מוצעים שטרם נבדקו בידי אנשים. תרגול עצמי ללא ציון; הפתיחות נספרות רק במהלך הביקור הזה.", "New original exercises with proposed solutions awaiting human review. Self-study without a grade; opened solutions are counted only during this visit.")}</p>
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
      <title>{label}: {diagram.gate}</title>{defs}
      <rect x="140" y="35" width="110" height="85" rx="7" className="quick-svg-node" />
      <text x="195" y="82" textAnchor="middle" className="quick-svg-gate">{diagram.gate}</text>
      {dataInputs.map((input, i) => { const y = dataInputs.length === 1 ? 77 : 58 + i * 38;
        return <g key={input}><text x="28" y={y + 5}>{input}</text><path d={`M65 ${y} H137`} markerEnd={arrow} />
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
  </svg><figcaption>{lang === "he" ? "חץ ללא מקור מסמן את מצב ההתחלה. כיתובי החצים מתארים קלט." : "The incoming arrow marks the initial state. Transition labels describe inputs."}</figcaption></figure>;
}
