/** Rendering boundaries only: the source text is never rewritten. */
export type BidiSegment = { text: string; direction: "ltr" | "inherit" };

const rtlLetter = /[\p{Script=Hebrew}\p{Script=Arabic}\p{Script=Syriac}\p{Script=Thaana}\p{Script=Nko}\p{Script=Adlam}]/u;
const letter = /\p{L}/u;
const technicalCore = /[\p{Script=Latin}\p{Script=Greek}\p{N}]/u;
const technicalCharacter = /[\x20-\x7e\t\p{Script=Latin}\p{Script=Greek}\p{N}\p{Sm}\u00a0\u00ac\u00b0\u00b1\u00d7\u00f7\u2010-\u2015\u2032\u2033\u2190-\u21ff]/u;
const opening = new Set(["(", "[", "{"]);
const closing = new Set([
  ")", "]", "}",
]);
const matching: Record<string, string> = { "(": ")", "[": "]", "{": "}" };

/** Use the original content, since HTML dir=auto intentionally ignores bdi descendants. */
export function textDirection(text: string): "ltr" | "rtl" {
  for (const character of text) {
    if (character === "\u200f" || character === "\u202b" || character === "\u202e" || character === "\u2067") return "rtl";
    if (character === "\u200e" || character === "\u202a" || character === "\u202d" || character === "\u2066") return "ltr";
    if (letter.test(character)) return rtlLetter.test(character) ? "rtl" : "ltr";
  }
  return "ltr";
}

/** Keep an interval's intentional mixed delimiters, e.g. [lo, hi) or (0, n]. */
function intervalClose(text: string, index: number, open: { character: string; index: number }, character: string) {
  return ((open.character === "[" && character === ")") || (open.character === "(" && character === "]"))
    && text.slice(open.index + 1, index).includes(",");
}

/** Distinguish literal bracket tokens from parentheses enclosing RTL prose. */
function literalBracketRanges(text: string): { start: number; end: number }[] {
  // Quoted literals must be recognized first: the '(' and ')' in two separate
  // quoted examples must not form a prose pair around the Hebrew between them.
  const quotedRanges = [...text.matchAll(/["'`“‘][()[\]{}]+["'`”’]/gu)].map(match => ({ start: match.index, end: match.index + match[0].length }));
  const quotedIndices = new Set(quotedRanges.flatMap(range => Array.from({ length: range.end - range.start }, (_, index) => range.start + index)));
  const structuredDelimiters = new Set<number>();
  const stack: { character: string; index: number }[] = [];
  for (let index = 0; index < text.length; index++) {
    if (quotedIndices.has(index)) continue;
    const character = text[index];
    if (opening.has(character)) stack.push({ character, index });
    else if (closing.has(character)) {
      const openIndex = stack.findLastIndex(open => matching[open.character] === character || intervalClose(text, index, open, character));
      if (openIndex < 0) continue;
      const open = stack[openIndex];
      const contents = text.slice(open.index + 1, index);
      if (rtlLetter.test(contents) || technicalCore.test(contents)) {
        structuredDelimiters.add(open.index);
        structuredDelimiters.add(index);
      }
      stack.splice(openIndex);
    }
  }

  const ranges: { start: number; end: number }[] = [];
  for (const match of text.matchAll(/["'`“‘]?[()[\]{}]+["'`”’]?/gu)) {
    const start = match.index;
    const end = start + match[0].length;
    if (quotedRanges.some(range => range.start === start && range.end === end)) {
      ranges.push({ start, end });
      continue;
    }
    // Attached delimiters belong to their adjacent word/expression, not a
    // standalone diagnostic literal. They are handled by the balanced parser.
    if ((start > 0 && /[\p{L}\p{N}_]/u.test(text[start - 1])) || (end < text.length && /[\p{L}\p{N}_]/u.test(text[end]))) continue;
    if ([...structuredDelimiters].some(index => index >= start && index < end)) continue;
    ranges.push({ start, end });
  }
  return ranges;
}

function isolateRun(text: string): BidiSegment[] {
  const invalid = new Set<number>();
  const stack: { character: string; index: number }[] = [];
  for (let index = 0; index < text.length; index++) {
    const character = text[index];
    if (opening.has(character)) stack.push({ character, index });
    else if (closing.has(character)) {
      const open = stack.at(-1);
      if (open && (matching[open.character] === character || intervalClose(text, index, open, character))) stack.pop();
      else {
        invalid.add(index);
        // A delimiter cannot be paired across a malformed or prose boundary.
        for (const unmatched of stack) invalid.add(unmatched.index);
        stack.length = 0;
      }
    }
  }
  for (const unmatched of stack) invalid.add(unmatched.index);

  const parts: BidiSegment[] = [];
  let start = 0;
  const append = (value: string) => {
    if (!value) return;
    if (!technicalCore.test(value)) {
      parts.push({ text: value, direction: "inherit" });
      return;
    }
    // Sentence punctuation belongs to the surrounding sentence. Balanced brackets,
    // unary operators, pointers and postfix operators stay with their expression.
    let first = 0;
    let last = value.length;
    while (first < last && /[\s,.;:?]/u.test(value[first])) first++;
    while (last > first && /[\s,.;:!?]/u.test(value[last - 1])) last--;
    if (first) parts.push({ text: value.slice(0, first), direction: "inherit" });
    if (last > first) parts.push({ text: value.slice(first, last), direction: "ltr" });
    if (last < value.length) parts.push({ text: value.slice(last), direction: "inherit" });
  };
  // Set insertion order can differ from source order for unmatched openers.
  for (const index of [...invalid].sort((a, b) => a - b)) {
    append(text.slice(start, index));
    parts.push({ text: text[index], direction: "inherit" });
    start = index + 1;
  }
  append(text.slice(start));
  return parts;
}

function segmentTechnicalRuns(text: string): BidiSegment[] {
  if (!text) return [];
  const segments: BidiSegment[] = [];
  let runStart = 0;
  let technical = technicalCharacter.test(text[0]);
  const flush = (end: number) => {
    const run = text.slice(runStart, end);
    segments.push(...(technical ? isolateRun(run) : [{ text: run, direction: "inherit" as const }]));
    runStart = end;
  };
  for (let index = 1; index < text.length; index++) {
    const next = technicalCharacter.test(text[index]);
    if (next !== technical) {
      flush(index);
      technical = next;
    }
  }
  flush(text.length);
  return segments;
}

/** Isolate complete technical expressions without pulling Hebrew prose into LTR. */
export function segmentBidiText(text: string): BidiSegment[] {
  if (!text) return [];
  const literals = literalBracketRanges(text);
  // Include final punctuation in English sentences and preserve bracket-only
  // diagnostic literals, even when they intentionally contain malformed syntax.
  if (!rtlLetter.test(text) && (technicalCore.test(text) || literals.length)) return [{ text, direction: "ltr" }];
  const segments: BidiSegment[] = [];
  let start = 0;
  for (const literal of literals) {
    segments.push(...segmentTechnicalRuns(text.slice(start, literal.start)));
    segments.push({ text: text.slice(literal.start, literal.end), direction: "ltr" });
    start = literal.end;
  }
  segments.push(...segmentTechnicalRuns(text.slice(start)));
  return segments.reduce<BidiSegment[]>((result, segment) => {
    const previous = result.at(-1);
    if (previous?.direction === segment.direction) previous.text += segment.text;
    else result.push({ ...segment });
    return result;
  }, []);
}
