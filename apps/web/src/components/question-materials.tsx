"use client";

import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Download, ExternalLink, RotateCcw } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi, QuestionResources, ResourceMedia } from "../lib/practice-api";
import { visibleQuestionMedia } from "../lib/question-media";

export function StudyText({ text }: { text: string }) {
  return <div className="study-text" dir="auto"><Markdown remarkPlugins={[remarkGfm]} skipHtml
    components={{
      pre: ({ children }) => <pre className="code-block" dir="ltr">{children}</pre>,
      a: ({ href, children }) => href?.startsWith("https://")
        ? <a href={href} target="_blank" rel="noreferrer">{children}</a> : <span>{children}</span>,
      // Author text cannot cause arbitrary image requests. Images come only from the signed manifest.
      img: ({ alt }) => <span>{alt}</span>,
      table: ({ children }) => <div className="study-table-scroll"><table>{children}</table></div>,
    }}>{text}</Markdown></div>;
}

export function useQuestionResources(api: PracticeApi, key: string | undefined, enabled: boolean,
  attemptId: string | undefined, revealed: boolean) {
  const identity = `${key}:${attemptId}:${revealed}`;
  const [loaded, setLoaded] = useState<{ identity: string; data: QuestionResources } | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let current = true;
    setLoaded(null); setError(false);
    if (!key || !enabled) return;
    api.questionResources(key, attemptId).then(result => {
      if (current) setLoaded({ identity, data: result });
    }).catch(() => { if (current) setError(true); });
    return () => { current = false; };
  }, [api, key, enabled, attemptId, revealed, identity, retry]);
  return { data: loaded?.identity === identity ? loaded.data : null, error, retry: () => setRetry(v => v + 1) };
}

export function ResourceStatus({ error, retry, lang }: { error: boolean; retry: () => void; lang: Lang }) {
  return <div className={error ? "notice error" : "resource-loading"} role="status">
    {error ? <><span>{lang === "he" ? "לא הצלחנו לטעון את השרטוטים והקבצים." : "The diagrams and files could not be loaded."}</span>
      <button onClick={retry}><RotateCcw size={16} />{lang === "he" ? "ניסיון נוסף" : "Try again"}</button></>
      : lang === "he" ? "טוענים את השרטוטים…" : "Loading diagrams…"}
  </div>;
}

export function QuestionFigures({ media, lang, role, onRefresh }: {
  media: ResourceMedia[]; lang: Lang; role: "prompt" | "solution"; onRefresh: () => void;
}) {
  const [failed, setFailed] = useState<string[]>([]);
  const files = visibleQuestionMedia(media).filter(m => m.role === role);
  if (!files.length) return null;
  const images = files.filter(m => m.kind === "image");
  return <section className="question-resources" aria-label={lang === "he" ? "שרטוטים וקבצים" : "Diagrams and files"}>
    <div className="resource-heading"><h3>{role === "prompt"
      ? lang === "he" ? "שרטוטים לשאלה" : "Question diagrams"
      : lang === "he" ? "שרטוטי הפתרון וקבצי המימוש" : "Solution diagrams and implementation files"}</h3>
      <button className="text-button" onClick={onRefresh} aria-label={lang === "he" ? "רענון קישורי הקבצים" : "Refresh file links"}>
        <RotateCcw size={16} /></button></div>
    <p className="small muted">{lang === "he" ? "לחצו על שרטוט לצפייה בגודל מלא." : "Open any diagram at full size."}</p>
    <div className="question-figures">{images.map((m, i) => <figure key={m.id}>
      <a href={m.url} target="_blank" rel="noreferrer" aria-label={`${lang === "he" ? "פתיחת שרטוט" : "Open diagram"} ${i + 1}`}>
        {/* Signed private URLs must not be persisted by an image-optimization cache. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={m.url} alt={m.caption || `${lang === "he" ? "שרטוט" : "Diagram"} ${i + 1}: ${m.filename}`} loading="lazy" referrerPolicy="no-referrer"
          onError={() => setFailed(old => old.includes(m.url) ? old : [...old, m.url])} />
      </a>
      {failed.includes(m.url) && <ResourceStatus error retry={onRefresh} lang={lang} />}
      <figcaption><span dir="auto">{m.caption || m.filename}</span><ExternalLink size={14} aria-hidden="true" /></figcaption>
    </figure>)}</div>
    {files.some(m => m.kind === "file") && <ul className="resource-files">{files.filter(m => m.kind === "file").map(m => <li key={m.id}>
      <a href={m.url} target="_blank" rel="noreferrer"><Download size={16} /><bdi>{m.filename}</bdi></a>
    </li>)}</ul>}
  </section>;
}

const labels: Record<string, [string, string]> = {
  assumptions: ["הנחות", "Assumptions"], optimality: ["נכונות ויעילות", "Correctness and efficiency"],
  verification: ["בדיקות שבוצעו", "Verification"], edge_cases: ["מקרי קצה", "Edge cases"],
  interview_answer: ["תשובה קצרה לראיון", "Interview answer"], common_mistakes: ["טעויות נפוצות", "Common mistakes"],
  solution_extensions: ["הרחבות הפתרון", "Solution extensions"], prompt_variants: ["גרסאות נוספות של השאלה", "Question variants"],
  transition_tables: ["טבלאות מעברים", "Transition tables"], truth_table: ["טבלת אמת", "Truth table"],
  waveform_observations: ["קריאת תרשים התזמון", "Waveform observations"], fsm: ["מכונת המצבים", "State machine"],
  strategy: ["דרך הפתרון", "Strategy"], source_ambiguities: ["עמימות בנוסח המקורי", "Source ambiguities"],
  ambiguities: ["הבהרות לנוסח", "Ambiguities"], solution_networks: ["רשתות הפתרון", "Solution networks"],
  area_optimization: ["שיפור שטח", "Area optimization"], technical_references: ["מקורות טכניים", "Technical references"],
  component_truth_table: ["טבלת אמת של הרכיב", "Component truth table"], circuit_interpretation: ["פירוש המעגל", "Circuit interpretation"],
  network: ["מבנה הרשת", "Network"], diagnostic_test: ["בדיקת אבחון", "Diagnostic test"],
  answer_branches: ["חלופות התשובה", "Answer branches"], netlist: ["חיבורי המעגל", "Netlist"], netlists: ["חיבורי המעגלים", "Netlists"],
  component_delays_ns: ["השהיות רכיבים", "Component delays"], retiming_alternative: ["חלופת תזמון", "Retiming alternative"],
  course_terminology: ["מונחים", "Terminology"], terminology_clarification: ["הבהרת מונחים", "Terminology clarification"],
  alternative_solution_notes: ["דרך פתרון נוספת", "Alternative solution"],
  descending_diagram_extension: ["הרחבת השרטוט", "Diagram extension"],
  diagram_description: ["הסבר השרטוט", "Diagram explanation"],
  driver_explanation_he: ["הסבר ההפעלה", "Driver explanation (Hebrew)"],
  eight_cell_alternative: ["חלופה עם שמונה תאים", "Eight-cell alternative"],
  formula_interpretation: ["פירוש הנוסחה", "Formula interpretation"],
  group_logic_derivation_he: ["פיתוח הלוגיקה", "Logic derivation (Hebrew)"],
  group_logic_derivation_verification: ["בדיקת פיתוח הלוגיקה", "Logic derivation verification"],
  hierarchy_diagram_explanation_he: ["הסבר מבנה המעגל", "Circuit hierarchy (Hebrew)"],
  n2_design_comparison: ["השוואת מימושים", "Design comparison"],
  original_formula_latex: ["הנוסחה המקורית", "Original formula"],
  parallel_products_explanation: ["הסבר המכפלות במקביל", "Parallel products"],
  part_5_cost_model: ["מודל העלות", "Cost model"],
  part_6_two_level_explanation: ["הסבר שתי הרמות", "Two-level explanation"],
  recursive_two_bit_alternative: ["חלופה רקורסיבית", "Recursive alternative"],
  relationship_note: ["קשר לשאלות אחרות", "Related questions"],
  solution_references: ["מקורות הפתרון", "Solution references"],
  solution_schematic_verification: ["אימות השרטוט", "Schematic verification"],
  solution_gate_schematic_verification: ["אימות מימוש השערים", "Gate schematic verification"],
  editorial_notes: ["הערות עריכה", "Editorial notes"],
};

function Value({ value, lang }: { value: unknown; lang: Lang }) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string") return <StudyText text={value} />;
  if (typeof value !== "object") return <span>{String(value)}</span>;
  if (Array.isArray(value)) return <ol>{value.map((v, i) => <li key={i}><Value value={v} lang={lang} /></li>)}</ol>;
  const object = value as Record<string, unknown>;
  if (lang in object && ("he" in object || "en" in object)) return <Value value={object[lang]} lang={lang} />;
  return <dl>{Object.entries(object).filter(([k]) => k !== (lang === "he" ? "en" : "he")).map(([k, v]) => <div key={k}>
    <dt>{labels[k]?.[lang === "he" ? 0 : 1] ?? k.replaceAll("_", " ")}</dt><dd><Value value={v} lang={lang} /></dd>
  </div>)}</dl>;
}

export function TechnicalMaterial({ material, lang }: { material: Record<string, unknown>; lang: Lang }) {
  const technicalKeys = Object.keys(material).filter(k => labels[k]);
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(material, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = `${String(material.id ?? "question")}-material.json`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section className="technical-material">
    <h3>{lang === "he" ? "הסברים נוספים ובדיקות" : "Further explanations and verification"}</h3>
    {technicalKeys.filter(k => material[k] != null).map(key => <details key={key}>
      <summary>{labels[key][lang === "he" ? 0 : 1]}</summary><Value value={material[key]} lang={lang} />
    </details>)}
    <button onClick={download}><Download size={16} />{lang === "he" ? "הורדת כל חומר השאלה" : "Download all question material"}</button>
  </section>;
}
