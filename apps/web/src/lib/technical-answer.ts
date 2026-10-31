export const answerLanguages = [
  "c",
  "cpp",
  "python",
  "javascript",
  "verilog",
  "systemverilog",
  "vhdl",
  "text",
] as const;
export type AnswerLanguage = (typeof answerLanguages)[number];

export function parseTechnicalAnswer(value: string) {
  // Split the final recognized block, retaining earlier examples as explanation.
  // A greedy body regex can accidentally swallow several same-fence blocks.
  const untouched = () => ({ explanation: value, code: "", language: undefined });
  const closing = /\n(`{3,})(?:\n)?$/.exec(value);
  if (!closing || closing.index + closing[0].length !== value.length) return untouched();
  const openings = /(^|\n\n)(`{3,})(c|cpp|python|javascript|verilog|systemverilog|vhdl|text)\n/g;
  let finalOpening: RegExpExecArray | null = null;
  for (let opening; (opening = openings.exec(value));) {
    if (opening[2] === closing[1] && openings.lastIndex <= closing.index) finalOpening = opening;
  }
  if (!finalOpening) return untouched();
  const code = value.slice(finalOpening.index + finalOpening[0].length, closing.index);
  // A prior closing delimiter means the terminal fence belongs to a different
  // block (for example, a final unknown language). Keep that answer intact.
  if (new RegExp(`^${closing[1]}$`, "m").test(code)) return untouched();
  return {
    explanation: value.slice(0, finalOpening.index),
    language: finalOpening[3] as AnswerLanguage,
    code,
  };
}

export function formatTechnicalAnswer(
  explanation: string,
  code: string,
  language: AnswerLanguage,
) {
  if (!code) return explanation;
  // Longer fences preserve code containing Markdown backticks without truncating a draft.
  const longest = Math.max(
    2,
    ...Array.from(code.matchAll(/`+/g), (m) => m[0].length),
  );
  const fence = "`".repeat(longest + 1);
  return `${explanation ? explanation + "\n\n" : ""}${fence}${language}\n${code}\n${fence}`;
}

export function defaultAnswerLanguage(
  language: string | null | undefined,
): AnswerLanguage {
  const value = language?.toLowerCase();
  if (value === "c++") return "cpp";
  return answerLanguages.includes(value as AnswerLanguage)
    ? (value as AnswerLanguage)
    : "text";
}
