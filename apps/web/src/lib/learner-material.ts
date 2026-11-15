import { learnerCopy } from "./learner-copy";
import { materialInLanguage } from "./material-locale";
import { sectionQuestionPrompt } from "./question-prompt-sections";
import type { ApiLang } from "./practice-api";

// Preparation records also hold provenance and publishing instructions. Only their
// teaching content belongs in a revealed solution or its download.
const archiveKeys = new Set([
  "key", "id", "received_on", "source_tags", "source_topic_tags", "reported_companies",
  "source_company_badge", "solution_status", "integration_status", "review_status",
  "company_attribution_status", "metadata_note", "original_prompt", "same_as_question_id",
  "prepared_hint_ids", "prepared_hints_reference", "solution_reference", "verification_reference",
  "hint_reference", "script", "verification_script",
]);

function cleanValue(value: unknown, lang: ApiLang): unknown {
  if (typeof value === "string") return learnerCopy(value).trim() || null;
  if (Array.isArray(value)) {
    const list = value.map(item => cleanValue(item, lang)).filter(item => item != null);
    return list.length ? list : null;
  }
  if (value === null || typeof value !== "object") return value;
  const record = value as Record<string, unknown>;
  if (Object.hasOwn(record, lang)) return cleanValue(record[lang], lang);
  const entries = Object.entries(record).filter(([key]) =>
    !archiveKeys.has(key) && !/_(?:paths?|script)$/.test(key) && key !== (lang === "he" ? "en" : "he"));
  const cleaned = entries.map(([key, item]) => [key, cleanValue(item, lang)] as const)
    .filter(([, item]) => item != null);
  return cleaned.length ? Object.fromEntries(cleaned) : null;
}

export function learnerMaterialSections(material: Record<string, unknown>, keys: string[], lang: ApiLang) {
  const entries = keys.map(key => [key, cleanValue(materialInLanguage(material, key, lang), lang)] as const);
  return Object.fromEntries(entries.filter(([, value]) => value != null));
}

export function studyDownload(material: Record<string, unknown>, sections: Record<string, unknown>, lang: ApiLang) {
  const localized = (material.translations as Record<string, Record<string, unknown>> | undefined)?.[lang];
  const prompt = localized?.prompt;
  return {
    id: material.id, language: lang, title: cleanValue(localized?.title, lang),
    ...(typeof prompt === "string" && { question: sectionQuestionPrompt(prompt, lang, String(material.key ?? "")) }),
    hints: cleanValue(localized?.hints ?? localized?.hint, lang),
    reference_solution: cleanValue(localized?.reference_solution, lang),
    sections,
  };
}
