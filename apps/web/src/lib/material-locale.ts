import type { ApiLang, QuestionResources } from "./practice-api";

function object(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown> : null;
}

/** A revealed answer may change display language without changing the attempt. */
export function referenceInLanguage(
  resources: QuestionResources | null,
  language: ApiLang,
  original: string,
  originalLanguage: ApiLang,
): string | null {
  if (resources?.solution_revealed) {
    if (resources.language === language && resources.reference?.trim()) return resources.reference;
    // Older resource responses already contain the paired preparation references.
    const translations = object(resources.technical_material?.translations);
    const reference = object(translations?.[language])?.reference_solution;
    if (typeof reference === "string" && reference.trim()) return reference;
  }
  return language === originalLanguage ? original : null;
}

export function materialInLanguage(material: Record<string, unknown>, key: string, language: ApiLang): unknown {
  const paired = object(object(material.learner_material)?.[key]);
  return paired && Object.hasOwn(paired, language) ? paired[language] : material[key];
}
