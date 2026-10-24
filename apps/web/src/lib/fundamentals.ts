import hardware from "../content/fundamentals-hardware.json";
import software from "../content/fundamentals-code-logic.json";
import moreHardware from "../content/fundamentals-hardware-expansion.json";
import moreReasoning from "../content/fundamentals-reasoning-expansion.json";
import moreCode from "../content/fundamentals-code-expansion.json";
import interviewHardware from "../content/fundamentals-hardware-250.json";
import interviewReasoning from "../content/fundamentals-reasoning-250.json";
import interviewCode from "../content/fundamentals-code-250.json";

export type QuickTopic = "gates" | "bits" | "sequential" | "states" | "python" | "algorithms" | "reasoning";
type Localized = { he: string; en: string };
export type QuickDiagram =
  | { kind: "gate"; gate: "AND" | "OR" | "XOR" | "NOT" | "MUX"; inputs: string[]; output: string }
  | { kind: "fsm"; states: string[]; initial: string; transitions: { from: string; to: string; label: string }[] };
export type QuickQuestion = {
  id: string; topic: QuickTopic; title: Localized; prompt: Localized; answer: Localized; takeaway: Localized;
  code?: { language: "python" | "verilog"; text: string }; diagram?: QuickDiagram;
  interviewIds?: string[];
};
export const quickTopics: { id: QuickTopic; label: Localized }[] = [
  { id: "gates", label: { he: "שערים ולוגיקה", en: "Gates and logic" } },
  { id: "bits", label: { he: "ביטים", en: "Bits" } },
  { id: "sequential", label: { he: "פליפ־פלופים", en: "Flip-flops" } },
  { id: "states", label: { he: "מכונות מצבים", en: "State machines" } },
  { id: "python", label: { he: "קוד", en: "Code" } },
  { id: "algorithms", label: { he: "אלגוריתמים", en: "Algorithms" } },
  { id: "reasoning", label: { he: "חשיבה והיגיון", en: "Reasoning" } },
];
// Original study cards, deliberately separate from the interview assessment bank.
// These newly authored answers have not received the founders' human-review attestation.
// At 250 cards, integer rounding gives 125 hardware /88 reasoning /37 software.
// Presentation order belongs to each visit; IDs and revisions never depend on it.
export const quickQuestions = [
  ...hardware, ...software, ...moreHardware, ...moreReasoning, ...moreCode,
  ...interviewHardware, ...interviewReasoning, ...interviewCode,
] as QuickQuestion[];

export function filterQuickQuestions(topic: QuickTopic | "all", query: string, lang: "he" | "en", questions: readonly QuickQuestion[] = quickQuestions) {
  const needle = query.trim().toLocaleLowerCase();
  return questions.filter(q => (topic === "all" || q.topic === topic) &&
    (!needle || `${q.title[lang]} ${q.prompt[lang]}`.toLocaleLowerCase().includes(needle)));
}
