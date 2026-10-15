import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";
import { createElement, type ReactElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { LandingXorControls } from "../src/components/landing-xor-controls";
import { LandingCompanyReports } from "../src/components/landing-company-reports";
import { LandingTestimonials } from "../src/components/landing-testimonials";
import { landingTestimonials } from "../src/content/landing-testimonials";
import { LANDING_REPORTED_COMPANIES } from "../src/lib/landing-content";
import { INITIAL_LANDING_BITS, landingXorOutput, toggleLandingBit, type LandingBits, type Bit } from "../src/lib/landing-xor";
import { publishedTestimonials } from "../src/lib/testimonials";
import { localizePublicTestimonials, type ApprovedPublicTestimonial } from "../src/lib/public-testimonials";

test("landing XOR produces the actual truth table for every input pair", () => {
  for (const a of [0, 1] as const) for (const b of [0, 1] as const) {
    assert.equal(landingXorOutput({ a, b }), (a ^ b) as Bit);
  }
  assert.equal(landingXorOutput(INITIAL_LANDING_BITS), 1);
});

test("the rendered toggle controls update their own input and preserve rapid consecutive presses", () => {
  let bits: LandingBits = { a: 0, b: 1 };
  const initial = bits;
  function press(input: "a" | "b") {
    const view = LandingXorControls({ bits, he: true, onToggle: action => { bits = toggleLandingBit(bits, action); } });
    const children = view.props.children as ReactElement[][];
    const button = children[0][input === "a" ? 0 : 1] as ReactElement<{ onClick: () => void }>;
    button.props.onClick();
  }
  press("a");
  assert.deepEqual(bits, { a: 1, b: 1 });
  assert.equal(landingXorOutput(bits), 0);
  press("b");
  assert.deepEqual(bits, { a: 1, b: 0 });
  assert.equal(landingXorOutput(bits), 1);
  press("a");
  assert.deepEqual(bits, { a: 0, b: 0 });
  assert.equal(landingXorOutput(bits), 0);
  press("b");
  assert.deepEqual(bits, initial);
  assert.deepEqual(initial, { a: 0, b: 1 }, "updates must never mutate the original state");
});

test("XOR has native keyboard buttons, stable accessible names and an announced result in both languages", () => {
  for (const he of [true, false]) {
    const html = renderToStaticMarkup(createElement(LandingXorControls, { bits: { a: 0, b: 1 }, he, onToggle() {} }));
    assert.equal((html.match(/<button/g) ?? []).length, 2);
    assert.equal((html.match(/type="button"/g) ?? []).length, 2);
    assert.match(html, /aria-pressed="false"/);
    assert.match(html, /aria-pressed="true"/);
    assert.match(html, he ? /aria-label="קלט A"/ : /aria-label="Input A"/);
    assert.match(html, /<output[^>]*aria-live="polite"[^>]*aria-atomic="true"[^>]*data-value="1"/);
    assert.doesNotMatch(html, /Tap to change|לחצו ושנו|tabindex="-1"/);
  }
});

test("every highlighted company is present in actual reported-source seed metadata", () => {
  const bank = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8")) as { assets?: { reported_companies?: string[] } }[];
  const reported = new Set(bank.flatMap(question => question.assets?.reported_companies ?? []));
  for (const company of LANDING_REPORTED_COMPANIES) assert.ok(reported.has(company), `${company} must have a real source report`);
});

test("company reports explain the source and never imply a partnership", () => {
  for (const he of [true, false]) {
    const html = renderToStaticMarkup(createElement(LandingCompanyReports, { he }));
    assert.equal((html.match(/<li>/g) ?? []).length, LANDING_REPORTED_COMPANIES.length);
    assert.equal((html.match(/<bdi dir="ltr">/g) ?? []).length, LANDING_REPORTED_COMPANIES.length);
    assert.match(html, he ? /אינו מעיד על שיתוף פעולה רשמי/ : /does not imply an official partnership/);
    assert.match(html, he ? /שדווחו מראיונות/ : /reported from interviews/);
    assert.doesNotMatch(html, /official partner of|endorsed by|בשיתוף פעולה עם/);
  }
});

/** Synthetic QA copy is confined to tests and is never imported by the public landing. */
const fixture: ApprovedPublicTestimonial = {
  id: "qa-only",
  revision: 2,
  quote: { he: "טקסט בדיקה בלבד — אינו ביקורת של משתמש.", en: "QA fixture only — not a user testimonial." },
  displayName: { he: "שם לבדיקה", en: "QA fixture" },
  context: { he: "הקשר לבדיקה", en: "Test context" },
  publication: { state: "approved", consentToPublish: true, approvedRevision: 2, approvedOn: "2026-10-16" },
};

test("testimonial publication requires explicit consent for the current exact revision", () => {
  for (const publication of [
    { ...fixture.publication, state: "draft" as const },
    { ...fixture.publication, state: "withdrawn" as const },
    { ...fixture.publication, consentToPublish: false },
    { ...fixture.publication, consentToPublish: undefined },
    { ...fixture.publication, approvedRevision: 1 },
    { ...fixture.publication, approvedOn: undefined },
    { ...fixture.publication, approvedOn: "not-a-date" },
    { ...fixture.publication, approvedOn: "2026-02-31" },
  ]) assert.deepEqual(publishedTestimonials([{ ...fixture, publication }], "he"), []);
  assert.deepEqual(publishedTestimonials([{ ...fixture, revision: 3 }], "he"), []);
  assert.deepEqual(publishedTestimonials([{ ...fixture, quote: { he: " " } }], "he"), []);
  assert.deepEqual(publishedTestimonials([{ ...fixture, displayName: {} }], "he"), []);
  assert.equal(publishedTestimonials([fixture], "he")[0].quote, fixture.quote.he);
  assert.equal(publishedTestimonials([fixture], "en")[0].quote, fixture.quote.en);
});

test("testimonials omit missing translations, deduplicate identities and expose only public copy", () => {
  assert.deepEqual(publishedTestimonials([{ ...fixture, quote: { he: fixture.quote.he } }], "en"), []);
  const publicEntries = publishedTestimonials([fixture, fixture], "he");
  assert.equal(publicEntries.length, 1);
  assert.deepEqual(Object.keys(publicEntries[0]), ["id", "quote", "displayName", "context"]);
  assert.deepEqual(localizePublicTestimonials([{ ...fixture, quote: { he: fixture.quote.he } }], "en"), []);
  assert.equal(localizePublicTestimonials([fixture, fixture], "he").length, 1);
});

test("public approved-only copy still rejects stale revisions and invalid runtime approval metadata", () => {
  const invalidEntries = [
    { ...fixture, revision: 3 },
    { ...fixture, revision: 0 },
    { ...fixture, publication: { ...fixture.publication, approvedOn: "2026-02-31" } },
    { ...fixture, publication: { ...fixture.publication, approvedOn: "invalid" } },
    { ...fixture, publication: { ...fixture.publication, approvedOn: undefined } },
    { ...fixture, publication: { ...fixture.publication, consentToPublish: false } },
    { ...fixture, publication: { ...fixture.publication, state: "withdrawn" } },
  ];
  for (const entry of invalidEntries) {
    // Model malformed runtime content; the public type separately rejects it at compile time.
    assert.deepEqual(localizePublicTestimonials([entry as ApprovedPublicTestimonial], "he"), []);
  }
});

test("approved testimonial layout is semantic, escaped, bilingual and static", () => {
  for (const he of [true, false]) {
    const html = renderToStaticMarkup(createElement(LandingTestimonials, { he, entries: [{ ...fixture, quote: { he: "<script>בדיקה</script>", en: "<script>fixture</script>" } }] }));
    assert.match(html, /aria-labelledby="landing-testimonials-title"/);
    assert.match(html, /<blockquote dir="auto">/);
    assert.match(html, /<figcaption>/);
    assert.match(html, /&lt;script&gt;/);
    assert.match(html, he ? /מה אומרים מי שמתרגלים/ : /From people practicing with JobRun/);
    assert.doesNotMatch(html, /<script>|carousel|marquee|aria-live|<button/);
  }
});

test("the public landing never shows a fake review or an empty testimonial section", () => {
  assert.equal(landingTestimonials.length, 0, "only replace this gate when actual consented quotes are supplied");
  for (const he of [true, false]) {
    assert.equal(renderToStaticMarkup(createElement(LandingTestimonials, { he })), "");
    assert.equal(renderToStaticMarkup(createElement(LandingTestimonials, { he, entries: [] })), "");
  }
});

test("the landing client import graph cannot reach raw editorial testimonial intake", () => {
  const entry = fileURLToPath(new URL("../src/components/practice-landing.tsx", import.meta.url));
  const privateIntake = fileURLToPath(new URL("../src/lib/testimonials.ts", import.meta.url));
  const publicContent = fileURLToPath(new URL("../src/content/landing-testimonials.ts", import.meta.url));
  const visited = new Set<string>();
  function visit(file: string) {
    if (visited.has(file)) return;
    visited.add(file);
    const ast = ts.createSourceFile(file, readFileSync(file, "utf8"), ts.ScriptTarget.Latest, true);
    ast.forEachChild(node => {
      if (!ts.isImportDeclaration(node) || node.importClause?.isTypeOnly || !ts.isStringLiteral(node.moduleSpecifier)) return;
      const specifier = node.moduleSpecifier.text;
      if (!specifier.startsWith(".")) return;
      const resolved = path.resolve(path.dirname(file), specifier);
      const target = [resolved, `${resolved}.ts`, `${resolved}.tsx`, path.join(resolved, "index.ts"), path.join(resolved, "index.tsx")]
        .find(candidate => /\.tsx?$/.test(candidate) && existsSync(candidate));
      if (target) visit(target);
    });
  }
  visit(entry);
  assert.ok(visited.has(publicContent), "the actual landing uses the approved public source");
  assert.ok(!visited.has(privateIntake), "draft/withdrawn intake must never be bundled for visitors");
});

test("the public content type rejects drafts, withdrawals and absent publication consent", () => {
  // These compiler-checked negative cases deliberately stay in the test-only graph.
  const draft: ApprovedPublicTestimonial = { ...fixture, publication: { ...fixture.publication,
    // @ts-expect-error Draft text is forbidden in the downloadable public source.
    state: "draft" } };
  const withdrawn: ApprovedPublicTestimonial = { ...fixture, publication: { ...fixture.publication,
    // @ts-expect-error Withdrawn text must be removed, not bundled and hidden.
    state: "withdrawn" } };
  const noConsent: ApprovedPublicTestimonial = { ...fixture, publication: { ...fixture.publication,
    // @ts-expect-error Only explicit true is a public publication contract.
    consentToPublish: false } };
  const absentConsent: ApprovedPublicTestimonial = { ...fixture,
    // @ts-expect-error A missing consent field cannot be an approved public record.
    publication: { state: "approved", approvedRevision: 2, approvedOn: "2026-10-16" } };
  assert.equal([draft, withdrawn, noConsent, absentConsent].length, 4);
});
