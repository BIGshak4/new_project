import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import type { ApiLang, QuestionResources } from "../src/lib/practice-api";
import { materialInLanguage, referenceInLanguage } from "../src/lib/material-locale";
import { materialLabel, materialStatus } from "../src/lib/material-labels";
import { TechnicalMaterial } from "../src/components/question-materials";

type Question = {
  key: string;
  translations: Record<ApiLang, { reference_solution: string }>;
  assets: { preparation_resource?: Record<string, unknown> };
};
const questions = ["example_bank", "preparation_bank"].flatMap(name =>
  JSON.parse(readFileSync(new URL(`../../../backend/seeds/questions/${name}.json`, import.meta.url), "utf8")) as Question[]);
const prepared = questions.filter(question => question.assets.preparation_resource);
const response = (overrides: Partial<QuestionResources> = {}): QuestionResources => ({
  media: [], technical_material: null, solution_revealed: true, ...overrides,
});

test("all 111 canonical references follow display language while attempt language stays fixed", () => {
  assert.equal(questions.length, 111);
  for (const question of questions) {
    for (const originalLanguage of ["he", "en"] as const) {
      const original = question.translations[originalLanguage].reference_solution;
      for (const language of ["en", "he", "en"] as const) {
        const reference = question.translations[language].reference_solution;
        assert.equal(referenceInLanguage(response({ language, reference }), language, original, originalLanguage),
          reference, `${question.key}/${originalLanguage}/${language}`);
        if (language === "en") assert.doesNotMatch(reference, /\p{Script=Hebrew}/u, question.key);
      }
    }
  }
});

test("pending and stale resources never leak a Hebrew attempt reference into English", () => {
  const original = "זהו הפתרון בעברית";
  for (const resources of [null, response({ language: "he", reference: original }),
    response({ language: "en", reference: "", solution_revealed: false }),
    response({ language: "en", reference: "unearned resource", solution_revealed: false })]) {
    assert.equal(referenceInLanguage(resources, "en", original, "he"), null);
    assert.equal(referenceInLanguage(resources, "he", original, "he"), original);
  }
  assert.equal(referenceInLanguage(response({ language: "en", reference: "English" }), "he", "English", "en"), null);
});

test("older resource responses use paired preparation references only after reveal", () => {
  for (const question of prepared) {
    const resources = response({ technical_material: question.assets.preparation_resource! });
    const original = question.translations.he.reference_solution;
    assert.equal(referenceInLanguage(resources, "en", original, "he"),
      question.translations.en.reference_solution, question.key);
    assert.equal(referenceInLanguage({ ...resources, solution_revealed: false }, "en", original, "he"), null);
  }
  assert.equal(referenceInLanguage(response({ technical_material: { translations: { en: { reference_solution: 12 } } } }),
    "en", "מקור", "he"), null);
});

test("material pairs select requested values without replacing originals or numeric checks", () => {
  const material = {
    assumptions: ["Original archive"], verification: { status: "verified", count: 4 },
    learner_material: { assumptions: { he: ["הנחה בעברית"], en: ["An English assumption"] },
      verification: { he: { status: "verified", note: "נבדק", count: 4 },
        en: { status: "verified", note: "Checked", count: 4 } } },
  };
  const before = JSON.stringify(material);
  assert.deepEqual(materialInLanguage(material, "assumptions", "en"), ["An English assumption"]);
  assert.deepEqual(materialInLanguage(material, "assumptions", "he"), ["הנחה בעברית"]);
  assert.equal((materialInLanguage(material, "verification", "en") as Record<string, unknown>).count, 4);
  assert.deepEqual(materialInLanguage({ assumptions: ["Legacy"] }, "assumptions", "he"), ["Legacy"]);
  assert.equal(JSON.stringify(material), before);
});

test("real technical material renderer changes section labels and contents together", () => {
  const material = { id: "TEST", assumptions: ["raw Hebrew: מקור"], interview_answer: "תשובה מקורית",
    learner_material: { assumptions: { he: ["הנחה שנבדקה"], en: ["A verified assumption"] },
      interview_answer: { he: "תשובה קצרה בעברית", en: "A concise interview answer" } } };
  const render = (lang: ApiLang) => renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang }));
  const english = render("en");
  assert.match(english, /<summary>Assumptions<\/summary>/);
  assert.match(english, /<summary>Interview answer<\/summary>/);
  assert.match(english, /A verified assumption/);
  assert.match(english, /A concise interview answer/);
  assert.doesNotMatch(english, /\p{Script=Hebrew}/u);
  const hebrew = render("he");
  assert.match(hebrew, /<summary>הנחות<\/summary>/);
  assert.match(hebrew, /<summary>תשובה קצרה לראיון<\/summary>/);
  assert.match(hebrew, /הנחה שנבדקה/);
  assert.match(hebrew, /תשובה קצרה בעברית/);
  assert.equal(render("en"), english);
});

test("controlled disclosure flags restore selected sections after bilingual resource remounts", () => {
  const material = { id: "FIRST", assumptions: ["הנחות מקור"], verification: "בדיקה מקורית",
    interview_answer: "תשובה מקורית", learner_material: {
      assumptions: { he: ["הנחה בעברית"], en: ["English assumption"] },
      verification: { he: "אימות בעברית", en: "English verification" },
      interview_answer: { he: "תשובה בעברית", en: "English answer" },
    } };
  const openSections = Object.freeze({ assumptions: true, verification: false, interview_answer: true });
  const render = (lang: ApiLang, selected: Readonly<Record<string, boolean>>, id = "FIRST") =>
    renderToStaticMarkup(createElement(TechnicalMaterial, {
      material: { ...material, id }, lang, openSections: selected, onSectionToggle: () => {},
    }));
  const openLabels = (html: string) => [...html.matchAll(/<details open=""><summary>(.*?)<\/summary>/g)]
    .map(match => match[1]);
  // Each call is a new mount, as when protected resources leave the DOM while loading.
  assert.deepEqual(openLabels(render("he", openSections)), ["הנחות", "תשובה קצרה לראיון"]);
  const english = render("en", openSections);
  assert.deepEqual(openLabels(english), ["Assumptions", "Interview answer"]);
  assert.doesNotMatch(english, /\p{Script=Hebrew}/u);
  assert.deepEqual(openLabels(render("he", openSections)), ["הנחות", "תשובה קצרה לראיון"]);
  // A new question/attempt gets fresh parent flags, never another scope's open state.
  assert.deepEqual(openLabels(render("en", {}, "SECOND")), []);
  assert.deepEqual(openSections, { assumptions: true, verification: false, interview_answer: true });
});

test("technical metadata labels and status text translate without changing formulas or underlying status", () => {
  assert.equal(materialLabel("criterion", "he"), "מה נדרש להוכיח");
  assert.equal(materialLabel("verification_status", "he"), "מצב האימות");
  assert.equal(materialLabel("opening", "he"), "אופן הפתיחה");
  assert.equal(materialLabel("timing", "he"), "תזמון");
  assert.equal(materialLabel("question", "he"), "שאלת המשך");
  assert.equal(materialLabel("answer_outline", "he"), "כיוון לתשובה");
  assert.equal(materialLabel("coverage", "he"), "כיסוי הבדיקות");
  assert.equal(materialStatus("passed", "status", "he"), "עבר");
  assert.equal(materialStatus("passed", "status", "en"), "passed");
  assert.equal(materialStatus("A XOR B", "formula", "he"), "A XOR B");
  const material = { verification: { status: "passed", result: true, criterion: "בדיקה של A XOR B בשער" } };
  const hebrew = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang: "he" }));
  assert.match(hebrew, /מצב הבדיקה/);
  assert.match(hebrew, /עבר/);
  assert.match(hebrew, /כן/);
  assert.match(hebrew, /<bdi dir="ltr">A XOR B<\/bdi>/);
  assert.equal(material.verification.status, "passed");
});

test("all 81 preparation resources pair every visible technical field and render entirely in English", () => {
  assert.equal(prepared.length, 81);
  for (const question of prepared) {
    const material = question.assets.preparation_resource!;
    const pairs = material.learner_material as Record<string, Record<ApiLang, unknown>> | undefined;
    assert.ok(pairs && typeof pairs === "object", `${question.key}: missing learner_material`);
    const visible = Object.keys(material).filter(key => material[key] != null && renderToStaticMarkup(createElement(TechnicalMaterial,
      { material: { [key]: "Visible section sentinel" }, lang: "en" })).includes("<details"));
    assert.ok(visible.length > 0, question.key);
    for (const key of visible) {
      // Empty archive arrays have no text to translate (PREP-002 assumptions); absent sections stay absent.
      if (Array.isArray(material[key]) && material[key].length === 0) continue;
      assert.ok(pairs[key] && Object.hasOwn(pairs[key], "he") && Object.hasOwn(pairs[key], "en"),
        `${question.key}/${key}: missing paired learner material`);
      assert.notEqual(pairs[key].en, null, `${question.key}/${key}`);
      assert.doesNotMatch(JSON.stringify(pairs[key].en), /\p{Script=Hebrew}/u, `${question.key}/${key}`);
    }
    const english = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang: "en" }));
    assert.doesNotMatch(english, /\p{Script=Hebrew}/u, question.key);
    assert.equal([...english.matchAll(/<summary>/g)].length, visible.length, question.key);
  }
});
