import assert from "node:assert/strict";
import test from "node:test";
import { createElement, type ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { BidiText } from "../src/components/bidi-text";
import { segmentBidiText, textDirection } from "../src/lib/bidi-segments";

const ltr = (text: string) => segmentBidiText(text).filter(segment => segment.direction === "ltr").map(segment => segment.text);
const render = (...children: ReactNode[]) => renderToStaticMarkup(createElement(BidiText, null, ...children));

test("decoder bit slices retain both square brackets in their LTR run", () => {
  const question = "תכננו מפענח 2 ל־4 עם אות הפעלה E. כאשר E=1 בדיוק ביט אחד ב־Y[3:0] הוא 1, באינדקס A[1:0]; כאשר E=0 כל הפלטים אפס.";
  const runs = ltr(question);
  assert.ok(runs.some(run => run.includes("Y[3:0]")));
  assert.ok(runs.some(run => run.includes("A[1:0]")));
  assert.ok(!runs.some(run => /Y\[3:0$|A\[1:0$/.test(run)));
  assert.equal(segmentBidiText(question).map(segment => segment.text).join(""), question);
});

test("the English decoder and its final punctuation retain their original reading order", () => {
  const question = "Design a 2-to-4 decoder with enable E. When E=1, exactly one bit in Y[3:0] is 1 at index A[1:0]; when E=0, all outputs are zero.";
  assert.deepEqual(ltr(question), [question]);
});

test("nested parentheses, function arguments, arrays, sets and pointer dereferences remain complete", () => {
  for (const expression of ["fn(arr[i], {key: [1, 2]})", "(*p)[i]", "{0, 1}", "((A + B) * (C - D))", "(A[i] != 0) && !B", "α[3:0] → β[1:0]"]) {
    assert.deepEqual(ltr(`בדקו ${expression} לפני ההמשך.`), [expression]);
  }
});

test("intentional half-open interval delimiters remain in one LTR expression", () => {
  for (const expression of ["[lo,hi)", "(0,n]", "[0, n)", "(-∞, n]"]) {
    assert.deepEqual(ltr(`הטווח הוא ${expression} ולכן ממשיכים.`), [expression]);
  }
});

test("Hebrew parentheticals stay outside technical isolates", () => {
  const question = "הפלט (למשל Y[3:0]) נשמר (גם כאשר A[1:0] הוא 0).";
  const parts = segmentBidiText(question);
  assert.deepEqual(ltr(question), ["Y[3:0]", "A[1:0]", "0"]);
  assert.equal(parts.map(part => part.text).join(""), question);
  assert.ok(parts.filter(part => part.direction === "inherit").some(part => part.text.includes(") נשמר (")));
  assert.deepEqual(segmentBidiText("תשובה בעברית (כולל הסבר) בלבד."), [{ text: "תשובה בעברית (כולל הסבר) בלבד.", direction: "inherit" }]);
});

test("malformed brackets in diagnostic code are preserved rather than repaired", () => {
  for (const source of ["הקוד ([)] אינו מאוזן.", "מצאו טעות ב־A[1:0 או ב־fn(x)).", "הקלט הוא ] או ((", "if ((x] { return 1; }"]) {
    assert.equal(segmentBidiText(source).map(part => part.text).join(""), source);
  }
});

test("standalone diagnostic brackets get an LTR isolate so RTL cannot mirror their glyphs", () => {
  for (const literal of ["]", "((", "([)]", "([]{})", '"([)]"', "'([]{})'"]) {
    const source = `הקלט ${literal} שגוי.`;
    const parts = segmentBidiText(source);
    assert.deepEqual(parts.filter(part => part.direction === "ltr").map(part => part.text), [literal]);
    assert.equal(parts.map(part => part.text).join(""), source);
    const html = render(source);
    const encoded = literal.replaceAll('"', "&quot;").replaceAll("'", "&#x27;");
    assert.ok(html.includes(`<bdi dir="ltr">${encoded}</bdi>`), literal);
  }
});

test("bracket-only children retain a literal left-to-right reading direction", () => {
  for (const literal of ["]", "((", "([)]", "([]{})"]) {
    assert.deepEqual(segmentBidiText(literal), [{ text: literal, direction: "ltr" }]);
    assert.equal(render(literal), `<bdi dir="ltr">${literal}</bdi>`);
  }
});

test("spaced and nested Hebrew parentheticals remain RTL prose rather than literal code", () => {
  for (const source of ["הסבר (עם הערה בעברית) בלבד.", "הסבר ( עם הערה בעברית ) בלבד.", "הסבר [ ( הערה בעברית ) ] בלבד."]) {
    assert.deepEqual(segmentBidiText(source), [{ text: source, direction: "inherit" }]);
    assert.ok(!render(source).includes("<bdi"));
  }
  assert.deepEqual(ltr("הסבר ( למשל Y[3:0] עם הערה בעברית ) בלבד."), ["Y[3:0]"]);
});

test("separately quoted open and close bracket literals cannot pair across Hebrew prose", () => {
  const source = 'התו "(" מופיע לפני ")" בטקסט.';
  assert.deepEqual(ltr(source), ['"("', '")"']);
  assert.equal(segmentBidiText(source).map(part => part.text).join(""), source);
  assert.match(render(source), /<bdi dir="ltr">&quot;\(&quot;<\/bdi>/);
  assert.match(render(source), /<bdi dir="ltr">&quot;\)&quot;<\/bdi>/);
});

test("punctuation, whitespace, Unicode and bidi markers survive segmentation unchanged", () => {
  const sources = [
    "  כאשר A[1:0], אז Y[3:0].  ",
    "\tאם (*p)[i] >= 0; המשיכו!\nאחרת x++.",
    "חישוב A − B → C, בקירוב ±0.5.",
    "ימין\u200f A[3:0] \u200eשמאל",
    "עברית 😀 {0, 1} עברית",
    "", "   ", "123.45", "A\nB",
  ];
  for (const source of sources) assert.equal(segmentBidiText(source).map(part => part.text).join(""), source);
});

test("textDirection uses the first source letter while numbers and punctuation are neutral", () => {
  assert.equal(textDirection("(123) עברית Y[3:0]"), "rtl");
  assert.equal(textDirection("(123) English עברית"), "ltr");
  assert.equal(textDirection("α[3:0] בעברית"), "ltr");
  assert.equal(textDirection("١٢٣ العربية"), "rtl");
  assert.equal(textDirection("[3:0]"), "ltr");
  assert.equal(textDirection("\u200f English"), "rtl");
  assert.equal(textDirection("\u200e עברית"), "ltr");
});

test("one isolate spans strong/emphasis formatting without losing markup or attributes", () => {
  const html = render("הפלט ", createElement("strong", { title: "signal" }, "Y[3:"), createElement("em", null, "0]"), " ממשיך.");
  assert.match(html, /<bdi dir="ltr"><strong title="signal">Y\[3:<\/strong><em>0\]<\/em><\/bdi>/);
});

test("ReactMarkdown renderer elements are transparent by their recognized HAST tag", () => {
  const Strong = ({ children }: { children?: ReactNode; node?: { tagName: string } }) => createElement("strong", null, children);
  const html = render("אות ", "A", createElement(Strong, { node: { tagName: "strong" } }, "[1:"), "0] נשמר.");
  assert.match(html, /<bdi dir="ltr">A<strong>\[1:<\/strong>0\]<\/bdi>/);
});

test("an inline code signal and its surrounding brackets share one isolate", () => {
  const Code = ({ children }: { children?: ReactNode; node?: { tagName: string } }) => createElement("code", { dir: "ltr" }, children);
  const html = render("בדקו ", createElement(Code, { node: { tagName: "code" } }, "Y"), "[3:0] ואז המשיכו.");
  assert.match(html, /<bdi dir="ltr"><code dir="ltr">Y<\/code>\[3:0\]<\/bdi>/);
});

test("links retain their destination when a technical expression spans formatting boundaries", () => {
  const html = render("בדקו ", "[", createElement("a", { href: "https://example.test", title: "original" }, "A[1:0]"), "] כעת.");
  assert.match(html, /<bdi dir="ltr">\[<a href="https:\/\/example.test" title="original">A\[1:0\]<\/a>\]<\/bdi>/);
});

test("code blocks, existing direction wrappers and unknown components retain their own rendering", () => {
  const Unknown = () => createElement("span", { "data-private": "kept" }, "x[2]");
  const html = render("הקוד ", createElement("code", { dir: "ltr" }, "if ((x]"), " ", createElement("bdi", { dir: "rtl" }, "מקור"), createElement(Unknown));
  assert.match(html, /<code dir="ltr">if \(\(x\]<\/code>/);
  assert.match(html, /<bdi dir="rtl">מקור<\/bdi>/);
  assert.match(html, /<span data-private="kept">x\[2\]<\/span>/);
  assert.ok(!html.includes('<code dir="ltr"><bdi'));
});
