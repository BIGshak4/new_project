import sourceScreenshots from "./source-screenshots.json";
import type { ResourceMedia } from "./practice-api";
import { learnerCopy } from "./learner-copy";

const withheld = new Set<string>(sourceScreenshots.map(filename => filename.toLowerCase()));

// Bare IDs, explicit source markers and dated intake names are reserved for sources.
// Authored illustrations use descriptive names without an intake date.
const archivedImageName = /^prep-\d{3,}(?:-(?:source|\d{3,}-full-context)|-(?:.+-)?\d{4}-\d{2}-\d{2}(?:-[\w-]+)?)?\.[^.]+$/i;
const archivedIntakeName = /^\d{4}-\d{2}-\d{2}-batch\d+-\d+\.[^.]+$/i;
const archivedSourcePath = /(?:^|\/)sources(?:\/|$)/i;

function isArchivedSource(item: ResourceMedia): boolean {
  const filename = item.filename.replaceAll("\\", "/");
  // Normal API responses omit provenance, but cached/manifest-backed responses
  // may contain it. Never rely on the prompt/solution role to hide sources.
  const sourcePath = "source_path" in item ? item.source_path : undefined;
  if (archivedSourcePath.test(filename)
    || (typeof sourcePath === "string" && archivedSourcePath.test(sourcePath.replaceAll("\\", "/")))) {
    return true;
  }
  const basename = filename.slice(filename.lastIndexOf("/") + 1);
  return withheld.has(basename.toLowerCase())
    || (item.kind === "image" && (archivedImageName.test(basename) || archivedIntakeName.test(basename)));
}

// Compatibility for already-issued resource responses during the API rollout.
// The server enforces the same boundary using the manifest's source_path.
export function visibleQuestionMedia(media: ResourceMedia[]): ResourceMedia[] {
  return media.filter(item => !isArchivedSource(item));
}

// Some shared diagrams were captioned with drawing or intake instructions.
const captions: [string[], string, string][] = [
  [["Independently authored implementation and solution diagram"], "שרטוט המימוש", "Implementation diagram"],
  [["Independently authored given diagram"], "השרטוט הנתון בשאלה", "Given diagram"],
  [["Preferred box-and-wire schematic with labelled pins, elbow routing and MAX/MIN outputs."],
    "חיבורי רכיבי המיון ויציאות MAX ו־MIN", "Sorting-cell connections and MAX/MIN outputs"],
  [["Circular states and curved arrows. Solution diagrams retain Moore outputs inside states; supplied reference uses Mealy edge notation."],
    "במכונת Moore הפלטים מופיעים במצבים. במכונת Mealy הם מופיעים על המעברים.",
    "Moore outputs appear inside states. Mealy outputs appear on transitions."],
  [["Authored redraw of memory buses; source controls remain unspecified"],
    "אפיקי הזיכרון. אותות הבקרה אינם מפורטים.", "Memory buses. Control signals are unspecified."],
  [["Redrawn given counter interface"], "ממשק המונה", "Counter interface"],
  [["Redrawn source timing", "תזמון המקור בשרטוט מחודש"], "תרשים התזמון", "Timing diagram"],
  [["Clean source truth table without a solution", "טבלת האמת המקורית בנוסח נקי, ללא פתרון"], "טבלת האמת הנתונה", "Given truth table"],
  [["New source topology: capacitor, ground resistor and inverter", "מעגל המקור החדש: קבל, נגד לאדמה ומהפך"],
    "מעגל עם קבל, נגד לאדמה ומהפך", "Circuit with a capacitor, a resistor to ground and an inverter"],
  [["Redrawn source datapath: ALU feedback and complementary register enables", "נתיב המקור בניסוח מחודש: ALU ומשוב לשני אוגרים באיפשורים משלימים"],
    "נתיב הנתונים עם משוב מה־ALU ואותות אפשור משלימים לאוגרים", "Datapath with ALU feedback and complementary register enables"],
  [["הקופסה המקורית נשמרת; הביט החמישי בוחר טעינה או היפוך מנשא ישן."],
    "הקופסה פועלת כמתואר בשאלה. הביט החמישי בוחר בין טעינה להיפוך לפי הנשא הקודם.",
    "The box operates as specified. The fifth bit selects loading or inversion based on the previous carry."],
  [["Clean falling-edge contract: Out pulses only in the third high phase."],
    "בתזמון לפי החזית היורדת, Out מפיק דופק רק בשלב הגבוה השלישי.",
    "With falling-edge timing, Out pulses only in the third high phase."],
];

export function figureCaption(raw: string, language: "en" | "he", number: number): string {
  const matched = captions.find(([wordings]) => wordings.includes(raw));
  if (matched) return matched[language === "he" ? 1 : 2];
  return learnerCopy(raw).trim() || (language === "he" ? `שרטוט ${number}` : `Diagram ${number}`);
}
