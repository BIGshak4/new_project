import { copyEdits, contextEdits, editorialNotes } from "./learner-copy-edits";
import { materialEdits } from "./learner-material-edits";
import { promptEdits } from "./question-wording-edits";

// Match the longest reviewed phrase first, so a shorter wording never prevents a more
// specific correction. Replacements are not recursively applied to the new wording.
const substitutions = new Map<string, string>([...copyEdits, ...contextEdits, ...materialEdits, ...promptEdits]);
for (const note of editorialNotes) substitutions.set(note, "");
const quoted = [...substitutions.keys()].sort((a, b) => b.length - a.length)
  .map(text => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
const knownWording = new RegExp(quoted.join("|"), "g");

// A source may be a voltage supply, a transistor terminal, program code or a clock.
// Recognize wording about the statement by its verb, rather than replacing that noun.
const englishStatement = /\b((?:[Tt]he|[Tt]his|[Tt]hat|[Aa]n additional) (?:original |new |additional |supplied |short |second |earlier |newer )?(?:source|screenshot))(?= (?:does not (?:specify|define|state|mention|promise|give|supply|say|name|choose|require|settle|cover|fix|distinguish|identify|clarify|restrict|guarantee|explicitly)|did not (?:specify|state|supply|provide)|says\b|states\b|asks\b|mentions\b|calls\b|omits\b|requests\b|requires\b|lists\b|describes\b|reports\b|specifies\b|writes\b|supplies no\b|provides no\b|gives no\b|leaves\b|prescribes\b|defines no\b|also requests\b|explicitly (?:requires|says|restricts|preserves)|only (?:asks|says|prints)|adds an ambiguous question))/g;
const hebrewStatement = /(?<![א-ת])(?:המקור|הצילום|צילום המקור)(?: החדש| הנוסף| המקורי| הקצר| הנוכחי)?(?= (?:אינו (?:מגדיר|מציין|מפרט|קובע|מספק|נותן|בוחר|מבקש|מגביל|מתיר|אוסר|מכריע|מבהיר|משלים|מציג|כולל|אומר|מבטיח|שולל)|לא (?:מציין|ציין|הגדיר|מגדיר|מגביל|מפרט|קובע|דורש|ביקש|מכריע|הכריע)|אומר|כותב|דורש|מבקש|מזכיר|מונה|מפרט|מציין|מתאר|נותן דוגמה|מציג דוגמה|מציג עקבה|מגביל את הערך|מגדיר את טווח|אוסר מקום|מוסיף שאלה))/g;

// These particular file pointers describe checks in the authors' checkout.
const evidencePointer = /(?:Evidence(?: and source hashes)?|ראיה(?: וחתימות קבצים)?|ראיות|הראיות ב־|הדוח הוא)[ \t]*:?[ \t]*checks\/[\w.-]+\.(?:json|py)(?:(?: and | ו־)checks\/[\w.-]+\.(?:json|py))*\.?/g;
const fileOnly = /^(?:checks|solutions)\/[\w./-]+\.(?:py|json|c|sv|v)\.?$/;
const followupStatus = /(?:מוכן (?:בתוכן(?: בלבד)?|בחומר (?:המשלים|משלים)(?: בלבד)?)|בחומר משלים בלבד)[,;] (?:אינו|לא) מחובר לתור המשך(?: חי| אינטראקטיבי)?(?:; הרחבה לא אומתה בקוד)?\./g;

function rewriteProse(text: string) {
  if (fileOnly.test(text.trim())) return "";
  const revised = text.replace(knownWording, phrase => substitutions.get(phrase)!)
    .replace(evidencePointer, "").replace(followupStatus, "")
    .replace(englishStatement, phrase => /^[A-Z]/.test(phrase) ? "The problem" : "the problem")
    .replace(hebrewStatement, "התרגיל");
  if (revised === text) return text;
  return revised.replace(/(^|\n)(?: {0,3}#{1,6}| {0,3}[-*])[ \t]*(?=\r?\n)/g, "$1")
    .replace(/([^\s]) {2,}(?=\S)/g, "$1 ").replace(/\n(?:[ \t]*\r?\n){2,}/g, "\n\n");
}

// A question can contain literal examples of punctuation and entire programs. Preserve
// fenced/inline code, explicit math and link destinations byte-for-byte.
const protectedText = /(?:^ {0,3}(`{3,}|~{3,})[^\n]*\n[\s\S]*?(?:^ {0,3}\1[ \t]*(?=\r?$)|(?![\s\S])))|(`+)[^\n]*?\2|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$|\$(?!\s)[^$\r\n]+\$|!?\[[^\]\r\n]*\]\((?:\.\.\/)+(?:sources|checks|solutions)\/[^)\r\n]*\)\.?|\]\((?:\\.|[^)\r\n])*\)|https?:\/\/[^\s<>)]+/gm;

const checkoutLink = /^!?\[([^\]\r\n]*)\]\((?:\.\.\/)+(sources|checks|solutions)\/[^)\r\n]*\)(\.?)$/;

/** Present authored teaching text in either language, preserving learner input elsewhere. */
export function learnerCopy(text: string): string {
  let start = 0;
  let output = "";
  for (const match of text.matchAll(protectedText)) {
    const link = checkoutLink.exec(match[0]);
    const token = link ? (link[2] === "sources" ? "" : link[1] + link[3]) : match[0];
    output += rewriteProse(text.slice(start, match.index)) + token;
    start = match.index + match[0].length;
    if (token === "" && output.endsWith(" ") && text[start] === " ") start++;
  }
  output += rewriteProse(text.slice(start));
  if (output === text) return text;
  const content = output.replace(/^(?:[ \t]*\r?\n)+/g, "").trimEnd();
  if (!content) return "";
  // Padding belongs to the authored Markdown. Strip spaces left behind by a
  // deleted aside while preserving an original trailing line break or hard break.
  const tail = /\s*$/.exec(text)![0];
  return (text.startsWith(" ") ? content : content.replace(/^ (?=\S)/, "")) + tail;
}
