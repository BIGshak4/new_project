import type { ApiLang, QuestionSummary } from "./practice-api";

// Search aliases do not create company reports or alter the stored source names.
const companyAliases: string[][] = [
  ["Intel", "אינטל"], ["NVIDIA", "אנבידיה", "אנוידיה", "נבידיה", "נווידיה"],
  ["Google", "גוגל"], ["Microsoft", "מיקרוסופט"], ["Apple", "אפל"],
  ["Amazon", "אמזון", "אמאזון"], ["Meta", "מטא", "Facebook", "פייסבוק"],
  ["Qualcomm", "קוואלקום", "קוולקום"], ["Broadcom", "ברודקום"],
  ["Marvell", "מארוול", "מרוול"], ["Arm", "ארם", "ארמ"],
  ["Mobileye", "מובילאיי", "מובילאי"], ["Mellanox", "מלאנוקס", "מלנוקס"],
  ["Check Point", "Checkpoint", "צ'ק פוינט", "צ׳ק פוינט", "צקפוינט", "צק פוינט"],
  ["IBM", "יבמ", "איי בי אם"], ["Cisco", "סיסקו"],
  ["Applied Materials", "אפלייד מטיריאלס", "אפלייד"],
  ["Elbit", "Elbit Systems", "אלביט", "אלביט מערכות"],
  ["Elta", "אלתא"], ["Rafael", "רפאל"], ["Rada", "ראדא", "ראדה"],
  ["Samsung", "סמסונג"], ["SanDisk", "סנדיסק"], ["NICE", "נייס"],
  ["SolarEdge", "סולאראדג'", "סולאראדג׳", "סולאר אדג'", "סולאר אדג׳", "סולאראדג"],
  ["Hailo", "היילו"], ["Innoviz", "אינוויז", "אינוביז"],
  ["Quantum Machines", "קוונטום משינס", "קוואנטום משינס"],
  ["CEVA", "סיווה", "סיוה"], ["DSPG", "DSP Group", "די אס פי ג'י"],
  ["CSR", "סי אס אר"], ["ASOCS", "אסוקס"],
  ["Actelis Networks", "Actelis", "אקטליס"], ["Altair", "אלטייר", "אלתאיר"],
  ["Conduit", "קונדואיט"], ["Inomize", "אינומייז"],
  ["MaxLinear", "מקסלינאר", "מקסליניר", "מקסלינאר"],
  ["Nuvoton", "נובוטון"], ["Orbit", "אורביט"],
  ["RADWIN", "רדווין", "ראדווין"], ["Rachip", "רייצ'יפ", "רייצ׳יפ", "רייציפ"],
  ["TangoTec", "טנגוטק"], ["Valens", "ולנס", "וואלנס"],
  ["Vayyar", "ואיאר", "וייאר"], ["Zoran", "צורן"],
  ["proteanTecs", "פרוטאנטקס", "פרוטאנטק"],
];

export function normalizeSearch(value: string): string {
  return value.normalize("NFKD").replace(/\p{M}/gu, "").toLowerCase()
    .replace(/[\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ").trim().replace(/\s+/g, " ");
}
const identity = (value: string) => normalizeSearch(value).replaceAll(" ", "");
const byAlias = new Map(companyAliases.flatMap(group => group.map(alias => [identity(alias), group] as const)));

export function companyNames(question: Pick<QuestionSummary, "companies" | "reported_companies">): string[] {
  const seen = new Map<string, string>();
  for (const source of [...(question.reported_companies ?? []), ...(question.companies ?? []).map(c => c.name)]) {
    const raw = source.trim();
    if (!raw) continue;
    const name = byAlias.get(identity(raw))?.[0] ?? raw;
    seen.set(identity(name), name);
  }
  return [...seen.values()];
}

function companyTerms(question: Pick<QuestionSummary, "companies" | "reported_companies">): string {
  return companyNames(question).flatMap(name => byAlias.get(identity(name)) ?? [name]).join(" ");
}

export function matchesCompany(question: Pick<QuestionSummary, "companies" | "reported_companies">, query: string): boolean {
  const needle = normalizeSearch(query);
  if (!needle) return true;
  // Compact spelling accepts punctuation/spacing variants such as CheckPoint.
  const candidates = companyNames(question).flatMap(name => byAlias.get(identity(name)) ?? [name]);
  return candidates.some(name => identity(name).includes(identity(query)));
}

export function questionCategory(q: Pick<QuestionSummary, "category" | "subject">): string {
  if (q.category) return q.category;
  if (["digital_fundamentals", "digital_logic", "digital_design", "sequential_logic", "fsms"].includes(q.subject)) return "hardware";
  if (["relevant_programming", "programming", "software_fundamentals"].includes(q.subject)) return "software";
  if (["reasoning", "problem_solving"].includes(q.subject)) return "logic";
  return "general";
}

export function categoryLabel(category: string, lang: ApiLang): string {
  const labels: Record<string, [string, string]> = {
    hardware: ["חומרה", "Hardware"], software: ["תוכנה", "Software"],
    logic: ["חידות והיגיון", "Logic & puzzles"], general: ["כללי", "General"],
  };
  return labels[category]?.[lang === "he" ? 0 : 1] ?? category.replaceAll("_", " ");
}

export function matchesQuestion(q: QuestionSummary, query: string, subjectLabels: string[] = []): boolean {
  const category = questionCategory(q);
  const text = normalizeSearch([q.title, q.key, q.preparation_id, q.subject, ...(q.topics ?? []),
    ...subjectLabels, categoryLabel(category, "he"), categoryLabel(category, "en"), companyTerms(q)].join(" "));
  return normalizeSearch(query).split(" ").filter(Boolean).every(word => text.includes(word));
}

export const companyReportNote = (lang: ApiLang) => lang === "he"
  ? "שיוך שאלות לחברות מבוסס על דיווחי מועמדים ומשתמשים ועל מקורות ההכנה שנאספו. השיוך אינו פרסום רשמי מטעם החברות, ונוסח השאלה עשוי להשתנות בין ראיונות."
  : "Company tags are based on candidate and user reports and collected preparation sources. They are not official company publications, and wording may vary between interviews.";
