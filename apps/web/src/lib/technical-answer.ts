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
  // Only our final, recognized fenced block is split. Legacy/free-form answers remain intact.
  const match =
    /^(?:([\s\S]*?)\n\n)?(`{3,})(c|cpp|python|javascript|verilog|systemverilog|vhdl|text)\n([\s\S]*)\n\2$/.exec(
      value,
    );
  return match
    ? {
        explanation: match[1] ?? "",
        language: match[3] as AnswerLanguage,
        code: match[4],
      }
    : { explanation: value, code: "", language: undefined };
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
