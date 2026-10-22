"use client";

import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Element, ElementContent } from "hast";
import { Download, ExternalLink, RotateCcw } from "lucide-react";
import type { Lang } from "./auth";
import type { PracticeApi, QuestionResources, ResourceMedia } from "../lib/practice-api";
import { visibleQuestionMedia } from "../lib/question-media";
import { solutionMarkdown } from "../lib/solution-markdown";
import { materialInLanguage } from "../lib/material-locale";
import { materialLabel, materialStatus } from "../lib/material-labels";
import { BidiText } from "./bidi-text";
import { textDirection } from "../lib/bidi-segments";

function textContent(part: Element | ElementContent | undefined): string {
  if (!part) return "";
  if (part.type === "text") return part.value;
  return "children" in part ? part.children.map(textContent).join("") : "";
}
function blockDirection(node?: Element): "rtl" | "ltr" {
  return textDirection(textContent(node));
}
function tableDirection(node?: Element): "rtl" | "ltr" {
  const header = node?.children.find((part) => part.type === "element" && part.tagName === "thead");
  // Read the original Markdown node: rendered LTR <bdi> children are ignored by HTML dir="auto".
  return blockDirection(header?.type === "element" ? header : node);
}

export function StudyText({ text, solution = false }: { text: string; solution?: boolean }) {
  return <div className="study-text" dir={textDirection(text)}><Markdown remarkPlugins={[remarkGfm]} skipHtml
    components={{
      p: ({ children, node }) => <p dir={blockDirection(node)}><BidiText>{children}</BidiText></p>,
      li: ({ children, node }) => <li dir={blockDirection(node)}><BidiText>{children}</BidiText></li>,
      strong: ({ children }) => <strong>{children}</strong>,
      em: ({ children }) => <em>{children}</em>,
      h1: ({ children, node }) => <h1 dir={blockDirection(node)}><BidiText>{children}</BidiText></h1>,
      h2: ({ children, node }) => <h2 dir={blockDirection(node)}><BidiText>{children}</BidiText></h2>,
      h3: ({ children, node }) => <h3 dir={blockDirection(node)}><BidiText>{children}</BidiText></h3>,
      h4: ({ children, node }) => <h4 dir={blockDirection(node)}><BidiText>{children}</BidiText></h4>,
      h5: ({ children, node }) => <h5 dir={blockDirection(node)}><BidiText>{children}</BidiText></h5>,
      h6: ({ children, node }) => <h6 dir={blockDirection(node)}><BidiText>{children}</BidiText></h6>,
      td: ({ children, node }) => <td dir={blockDirection(node)}><BidiText>{children}</BidiText></td>,
      th: ({ children, node }) => <th dir={blockDirection(node)}><BidiText>{children}</BidiText></th>,
      code: ({ children, className }) => <code className={className} dir="ltr">{children}</code>,
      pre: ({ children }) => <pre className="code-block" dir="ltr">{children}</pre>,
      a: ({ href, children }) => href?.startsWith("https://")
        ? <a href={href} target="_blank" rel="noreferrer">{children}</a> : <span>{children}</span>,
      // Author text cannot cause arbitrary image requests. Images come only from the signed manifest.
      img: ({ alt }) => <span>{alt}</span>,
      table: ({ children, node }) => <div className="study-table-scroll"><table dir={tableDirection(node)}>{children}</table></div>,
    }}>{solution ? solutionMarkdown(text) : text}</Markdown></div>;
}

export function useQuestionResources(api: PracticeApi, key: string | undefined, enabled: boolean,
  attemptId: string | undefined, revealed: boolean, language: Lang) {
  const identity = `${key}:${attemptId}:${revealed}:${language}`;
  const [loaded, setLoaded] = useState<{ identity: string; data: QuestionResources } | null>(null);
  const [error, setError] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let current = true;
    setLoaded(null); setError(false);
    if (!key || !enabled) return;
    api.questionResources(key, attemptId, language).then(result => {
      if (current) setLoaded({ identity, data: result });
    }).catch(() => { if (current) setError(true); });
    return () => { current = false; };
  }, [api, key, enabled, attemptId, revealed, language, identity, retry]);
  return { data: loaded?.identity === identity ? loaded.data : null, error, retry: () => setRetry(v => v + 1) };
}

export function ResourceStatus({ error, retry, lang, solution = false }: { error: boolean; retry: () => void; lang: Lang; solution?: boolean }) {
  return <div className={error ? "notice error" : "resource-loading"} role="status">
    {error ? <><span>{solution
      ? lang === "he" ? "לא הצלחנו לטעון את הפתרון בשפה שבחרתם." : "The solution could not be loaded in your selected language."
      : lang === "he" ? "לא הצלחנו לטעון את השרטוטים והקבצים." : "The diagrams and files could not be loaded."}</span>
      <button onClick={retry}><RotateCcw size={16} />{lang === "he" ? "ניסיון נוסף" : "Try again"}</button></>
      : solution ? lang === "he" ? "טוענים את הפתרון בשפה שבחרתם…" : "Loading the solution in your selected language…"
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
      <figcaption><span dir={textDirection(m.caption || m.filename)}><BidiText>{m.caption || m.filename}</BidiText></span><ExternalLink size={14} aria-hidden="true" /></figcaption>
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
  driver_explanation_he: ["הסבר ההפעלה", "Driver explanation"],
  eight_cell_alternative: ["חלופה עם שמונה תאים", "Eight-cell alternative"],
  formula_interpretation: ["פירוש הנוסחה", "Formula interpretation"],
  group_logic_derivation_he: ["פיתוח הלוגיקה", "Logic derivation"],
  group_logic_derivation_verification: ["בדיקת פיתוח הלוגיקה", "Logic derivation verification"],
  hierarchy_diagram_explanation_he: ["הסבר מבנה המעגל", "Circuit hierarchy"],
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

function Value({ value, lang, field }: { value: unknown; lang: Lang; field?: string }) {
  if (value === null || value === undefined) return null;
  if (typeof value === "string") return <StudyText text={materialStatus(value, field, lang)} />;
  if (typeof value !== "object") return <span>{typeof value === "boolean" ? lang === "he" ? value ? "כן" : "לא" : value ? "Yes" : "No" : String(value)}</span>;
  if (Array.isArray(value)) return <ol>{value.map((v, i) => <li key={i}><Value value={v} lang={lang} /></li>)}</ol>;
  const object = value as Record<string, unknown>;
  if (lang in object && ("he" in object || "en" in object)) return <Value value={object[lang]} lang={lang} />;
  return <dl>{Object.entries(object).filter(([k]) => k !== (lang === "he" ? "en" : "he")).map(([k, v]) => <div key={k}>
    <dt dir="auto">{labels[k]?.[lang === "he" ? 0 : 1] ?? materialLabel(k, lang)}</dt><dd><Value value={v} lang={lang} field={k} /></dd>
  </div>)}</dl>;
}

export function TechnicalMaterial({ material, lang, openSections, onSectionToggle }: {
  material: Record<string, unknown>; lang: Lang;
  openSections?: Readonly<Record<string, boolean>>;
  onSectionToggle?: (section: string, open: boolean) => void;
}) {
  const technicalKeys = Object.keys(material).filter(k => labels[k]);
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(material, null, 2)], { type: "application/json" }));
    const a = document.createElement("a"); a.href = url; a.download = `${String(material.id ?? "question")}-material.json`; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <section className="technical-material">
    <h3>{lang === "he" ? "הסברים נוספים ובדיקות" : "Further explanations and verification"}</h3>
    {technicalKeys.filter(k => material[k] != null).map(key => <details key={key}
      open={openSections ? !!openSections[key] : undefined}
      onToggle={onSectionToggle ? event => onSectionToggle(key, event.currentTarget.open) : undefined}>
      <summary>{labels[key][lang === "he" ? 0 : 1]}</summary><Value value={materialInLanguage(material, key, lang)} lang={lang} />
    </details>)}
    <button onClick={download}><Download size={16} />{lang === "he" ? "הורדת כל חומר השאלה" : "Download all question material"}</button>
  </section>;
}
