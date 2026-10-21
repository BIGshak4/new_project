import hardware from "../content/fundamentals-hardware.json";
import software from "../content/fundamentals-code-logic.json";

export type QuickTopic = "gates" | "bits" | "sequential" | "states" | "python" | "algorithms" | "reasoning";
type Localized = { he: string; en: string };
export type QuickDiagram =
  | { kind: "gate"; gate: "AND" | "OR" | "XOR" | "NOT" | "MUX"; inputs: string[]; output: string }
  | { kind: "fsm"; states: string[]; initial: string; transitions: { from: string; to: string; label: string }[] };
export type QuickQuestion = {
  id: string; topic: QuickTopic; title: Localized; prompt: Localized; answer: Localized; takeaway: Localized;
  code?: { language: "python" | "verilog"; text: string }; diagram?: QuickDiagram;
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
// Every full group of 20 keeps the requested 50% hardware /35% reasoning /15% software mix.
const lanes = {
  hardware: [...hardware] as QuickQuestion[],
  reasoning: software.filter(q => q.topic === "reasoning") as QuickQuestion[],
  software: software.filter(q => q.topic !== "reasoning") as QuickQuestion[],
};
const pattern: (keyof typeof lanes)[] = [
  "hardware", "reasoning", "hardware", "software", "reasoning", "hardware", "reasoning", "hardware", "software", "hardware",
  "reasoning", "hardware", "reasoning", "hardware", "software", "hardware", "reasoning", "hardware", "reasoning", "hardware",
];
export const quickQuestions: QuickQuestion[] = [];
while (Object.values(lanes).some(lane => lane.length)) {
  for (const name of pattern) { const question = lanes[name].shift(); if (question) quickQuestions.push(question); }
}

export function filterQuickQuestions(topic: QuickTopic | "all", query: string, lang: "he" | "en") {
  const needle = query.trim().toLocaleLowerCase();
  return quickQuestions.filter(q => (topic === "all" || q.topic === topic) &&
    (!needle || `${q.title[lang]} ${q.prompt[lang]}`.toLocaleLowerCase().includes(needle)));
}
