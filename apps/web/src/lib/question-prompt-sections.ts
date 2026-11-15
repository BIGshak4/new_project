import { learnerCopy } from './learner-copy';
import { alternateHeadings, modelOpenings } from './question-prompt-cues';

export type QuestionPromptSections = { main: string; clarifications: string; variations: string };
type Section = keyof QuestionPromptSections;
type Language = 'he' | 'en';

const namedAlternates = new Set<string>([...alternateHeadings, 'A large arena without additional external metadata']);
const openings = {
  en: modelOpenings.map(([en]) => en),
  he: modelOpenings.map(([, he]) => he),
};
const modelLabel = /^(?:(?:explicit(?:ly)?|added|essential|chosen|additional|edited|implementation|model|exercise|contract|source|main|editorial|analysis|teaching|rules|new|safe|finite|hardware|spatial|interface|technical|delivery|formal|timing|ideal|first-order|modeling)[ -]+)*(?:assumptions?|definitions?|clarifications?|contract|completion|model|policy|interface)(?:\b[^.!?\n]{0,48}?:|\s*$)|^(?:הבהר(?:ה|ת|ות)|הנח(?:ה|ת|ות)|(?:ה|ב)?חוזה|(?:נבחר )?מודל|הגדר(?:ה|ות)|השלמ(?:ה|ת|ות)|ממשק (?:שנבחר|מפורש))[^.!?\n]{0,45}[:：]/i;
const assumed = /^(?:Assume\b|Use a common clock of period|In the chosen contract|The source’s “2” enumerates|„2” שבצילום|Explicit additions to the source|Explicitly assume\b|For this (?:implementation|exercise),? assume\b|נניח(?: ש| )|הניחו(?: ש| )|בחוזה זה |בחוזה שנבחר |החוזה שנוסף|במודל, |מניחים ש|בהנחת reset|לצורך הניתוח מגדירים במפורש|איפוס סינכרוני|האתחול סינכרוני|בשלב זה נניח|לצורך (?:המימוש|התרגיל) נניח|במודל זה |בגרסה זו נניח)/i;
const variationLabel = /^(?:(?:[a-dא-ד][.)]|\([a-d]\))\s*)?(?:as an? (?:separate |optional )?extension\b|(?:separate |diagnostic-limit |general-width |hardware |numeric(?:al)? |additional |linked |new |optional |source |added )*(?:variants?|extensions?|follow[- ]ups?|bonus)\b|additional (?:exercises?|parts?)\b|another exercise\b|וריא(?:צי|נט)|[כו]וריא(?:צי|נט)|גרסה (?:נוספת|כללית)|(?:כ|ב|ל)?הרחבה(?:[,: —-]|$)|תרגיל נוסף|תרגילים נוספים|סעיפ(?:ים)? נוספ|סעיף נוסף|שאלת המשך|בונוס)/i;
const variantSentences = /^(?:Also explain the (?:simpler )?variant|Then solve an explicitly added variant|Then briefly generalize to more inputs|Also analyze the alternative|As a separate extension|As an added numerical example only|One-bit comparison:|הסבירו גם כיצד התוכנית מתקצרת|הציגו גם את השינוי כאשר|לאחר מכן פתרו וריאציה|לאחר מכן הסבירו בקצרה הרחבה|לצורך דוגמה בלבד|השוואת שני ביטים:)/i;
const requiredLabel = /(?:^|[:;]\s+)(?:\*{0,2})(?:\([A-Za-zא-ת]\)|[A-Da-dא-ת][.)]|\d+[.)])\s/;
const questionOrTask = /[?？]|(?:^|[;:]\s*|,\s*|\b(?:and|then|also|first|explicitly|separately|briefly|please|must|to)\s+)(?:explain|justify|define|extend|contrast|present|connect|prepare|add|try|put forward|perform|outline|label|support|use explicit|make that distinction|prove|derive|design|implement|show|give|provide|specify|state|identify|determine|compute|calculate|compare|analy[sz]e|discuss|describe|demonstrate|find|evaluate|build|draw|write|construct|count|trace|estimate|distinguish|separate|generalize|generalise|include|report|return|produce|list|solve|test|verify|optimi[sz]e|argue|handle|account for|must (?:also )?(?:explain|show|include)|the task (?:is|requires))\b|(?:^|[ .,;:–—-])ו?(?:הסבירו|נמקו|הוכיחו|תכננו|ממשו|הראו|תנו|הציעו|כתבו|אמרו|ציינו|פרטו|קבעו|חשבו|השוו|נתחו|הציגו|תארו|מצאו|בנו|שרטטו|ציירו|עקבו|הבחינו|הבדילו|הפרידו|הכלילו|החזירו|הדגימו|פתרו|בדקו|זהו|הגדירו|השלימו|פרשו|כללו|העריכו|ספרו|דונו|הפיקו|אמדו|בחרו|השיבו|מנו|סווגו|ערכו|התייחסו|הגבילו|הרחיבו|הכינו|חברו|נסו|טפלו|עליכם|התחילו|יש להבחין|נדרש(?:ים|ת)? לה(?:סביר|ציג|ראות|וכיח|חזיר)|יש לה(?:סביר|ציג|ראות|וכיח|חזיר))(?=[\s,:;.!?]|$)/i;

// Protect fenced literals including empty lines or headings inside code. With no closing
// fence the entire remainder is code, exactly as in Markdown.
function markdownBlocks(markdown: string): string[] {
  const blocks: string[] = [];
  let lines: string[] = [];
  let fence = '';
  function flush() { if (lines.length) blocks.push(lines.join('\n')); lines = []; }
  for (const line of markdown.replace(/\r\n?/g, '\n').split('\n')) {
    if (fence) {
      lines.push(line);
      if (line.trim().startsWith(fence) && /^[`~]+$/.test(line.trim())) { flush(); fence = ''; }
      continue;
    }
    const opened = line.match(/^ {0,3}(`{3,}|~{3,})/);
    if (opened) { flush(); lines.push(line); fence = opened[1]; continue; }
    if (!line.trim()) { flush(); continue; }
    if (/^ {0,3}#{1,6}\s/.test(line)) { flush(); blocks.push(line); continue; }
    lines.push(line);
  }
  flush();
  return blocks;
}

// Sentence and part boundaries are only meaningful in prose. In particular, the
// labels in code, link destinations, and mathematical notation must stay literal.
const inlineSyntax = /(`+)[^`\n]*?\1|\\\([\s\S]*?\\\)|\\\[[\s\S]*?\\\]|\$\$[\s\S]*?\$\$|\$[^$\n]+\$|\]\((?:\\.|[^)\n])*\)|https?:\/\/[^\s<>)]+/g;

function prosePieces(block: string): string[] {
  const protectedSpans = [...block.matchAll(inlineSyntax)].map(m => [m.index!, m.index! + m[0].length]);
  const atProse = (at: number) => !protectedSpans.some(([start, end]) => at >= start && at < end);
  const pieces: string[] = [];
  let start = 0;
  for (const match of block.matchAll(/[.!?](?=\s)|\n/g)) {
    const at = match.index!;
    if (!atProse(at)) continue;
    if (match[0] === '.' && /(?:^|\s)(?:[A-Da-dא-ת]|\d+|e\.g|i\.e)$/.test(block.slice(start, at))) continue;
    const end = at + (match[0] === '\n' ? 0 : 1);
    if (block.slice(start, end).trim()) { pieces.push(block.slice(start, end)); start = end; }
  }
  if (block.slice(start).trim()) pieces.push(block.slice(start));
  return pieces.flatMap(piece => {
    // PREP-007 uses a conjunction in HE for the assumption and mandatory task.
    const paired = 'הניחו תצפית אידאלית ורציפה ללא החמצת מעברים, והסבירו אתחול';
    if (piece.trimStart().startsWith(paired)) {
      const split = piece.indexOf(', והסבירו');
      return [piece.slice(0, split) + '.', ' ' + piece.slice(split + 3)];
    }
    return [piece];
  });
}

function legibleSubparts(block: string): string {
  if (/^\s*(?:`{3,}|~{3,}|\|)/.test(block)) return block;
  // Only labels with an introductory delimiter or sentence boundary are parts.
  // A component named A/B, a decimal, or a parenthesized variable in prose is not.
  const protectedSpans = [...block.matchAll(inlineSyntax)].map(m => [m.index!, m.index! + m[0].length]);
  const labels = [...block.matchAll(/(?:^|(?<=[.!?:;])|(?<=\n))([ \t]*)(?=(?:[A-Da-dא-ד][.)]|\([a-d]\))\s+\S)/g)]
    .filter(m => !protectedSpans.some(([a,b]) => m.index! >= a && m.index! < b));
  if (labels.length < 2) return block;
  let result = block;
  for (const m of labels.reverse()) {
    const i = m.index!;
    if (i) result = result.slice(0,i).trimEnd() + '\n\n' + result.slice(i + m[0].length);
  }
  return result;
}

function modelOpening(block: string, lang: Language) {
  const plain = block.trim().replace(/^\*\*/, '');
  return modelLabel.test(plain) || assumed.test(plain) || openings[lang].some((prefix) => plain.startsWith(prefix));
}

const primaryHeadings: Record<string, string> = {
  'Additional elementary source parts': 'Half adder and full adder',
  'סעיפי יסוד נוספים מהצילום': 'מחבר למחצה ומחבר מלא',
};

/** Classify original localized prompt Markdown. Keep assumptions scoped to their own
 * exercise. The practice API can also return a prompt without a question key. */
export function sectionQuestionPrompt(prompt: string, lang: Language, _questionKey?: string): QuestionPromptSections {
  const groups: Record<Section, string[]> = { main: [], clarifications: [], variations: [] };
  let scope: Section = 'main';
  for (const raw of markdownBlocks(prompt)) {
    const block = legibleSubparts(raw);
    const heading = block.match(/^( {0,3}#{1,6}\s+)(.+)$/);
    if (heading) {
      const title = heading[2].trim();
      if (Object.hasOwn(primaryHeadings, title)) {
        scope = 'main';
        groups.main.push(heading[1] + primaryHeadings[title]);
      } else if (variationLabel.test(title) || namedAlternates.has(title) || /\b(?:variant|extension)\b/i.test(title)) {
        scope = 'variations';
        groups.variations.push(block);
      } else if (modelLabel.test(title) || /^(?:clarifications?|assumptions?|הבהרות|הנחות)(?:$|\s)/i.test(title)) {
        scope = 'clarifications';
      } else {
        scope = 'main';
        groups.main.push(block);
      }
      continue;
    }
    if (scope === 'variations' || /^(?: {0,3}(?:`{3,}|~{3,})|\s*\|)/.test(block)) {
      groups[scope].push(block);
      continue;
    }
    const paragraph = block.trim();
    if (groups.main.length && (variationLabel.test(paragraph) || variantSentences.test(paragraph))) {
      groups.variations.push(block);
      continue;
    }
    let model = scope === 'clarifications' || modelOpening(paragraph, lang);
    let exercise = false;
    let target: Section | undefined;
    let run = '';
    function flushRun() { if (target && run.trim()) groups[target].push(run.trim()); run = ''; }
    for (const piece of prosePieces(block)) {
      const text = piece.trim();
      if ((groups.main.length || run.trim()) && (variationLabel.test(text) || variantSentences.test(text))) exercise = true;
      if (/^(?:\([a-d]\)|[A-Dא-ד][.)])\s/i.test(text) && !variationLabel.test(text)) exercise = false;
      if (modelOpening(text, lang)) model = true;
      const section: Section = exercise ? 'variations' : model && !requiredLabel.test(text) && !questionOrTask.test(modelLabel.test(text) ? text.slice(text.indexOf(':') + 1).trimStart() : text) ? 'clarifications' : 'main';
      if (target !== section) { flushRun(); target = section; }
      run += piece;
    }
    flushRun();
  }
  const main = learnerCopy(groups.main.join('\n\n')).trim();
  if (!main) return { main: learnerCopy(prompt).trim(), clarifications: '', variations: '' };
  return { main, clarifications: learnerCopy(groups.clarifications.join('\n\n')).trim(),
    variations: learnerCopy(groups.variations.join('\n\n')).trim() };
}
