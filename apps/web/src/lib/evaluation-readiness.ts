/** A known real provider enables model feedback. This is independent of code execution. */
export function isRealEvaluationProvider(provider: unknown): boolean {
  return provider === "openai" || provider === "anthropic";
}
