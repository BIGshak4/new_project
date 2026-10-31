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

test("all 249 canonical references follow display language while attempt language stays fixed", () => {
  assert.equal(questions.length, 249);
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
  assert.equal(materialLabel("answer_direction", "he"), "כיוון לתשובה");
  assert.equal(materialLabel("principle", "he"), "העיקרון");
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
  const extension = { solution_extensions: [{ question: "Follow-up", answer_direction: "Use cancellation", principle: "Conservation" }] };
  const before = JSON.stringify(extension);
  const renderExtension = (lang: ApiLang) => renderToStaticMarkup(createElement(TechnicalMaterial, { material: extension, lang }));
  const hebrewExtension = renderExtension("he");
  assert.match(hebrewExtension, /<dt dir="auto">כיוון לתשובה<\/dt>/);
  assert.match(hebrewExtension, /<dt dir="auto">העיקרון<\/dt>/);
  assert.doesNotMatch(hebrewExtension, /<dt dir="auto">(?:answer direction|principle)<\/dt>/);
  const englishExtension = renderExtension("en");
  assert.match(englishExtension, /<dt dir="auto">answer direction<\/dt>/);
  assert.match(englishExtension, /<dt dir="auto">principle<\/dt>/);
  assert.equal(JSON.stringify(extension), before, "Display labels do not rewrite published content keys");
  assert.equal(materialLabel("use", "he"), "שימוש");
  assert.equal(materialLabel("prompt", "he"), "נוסח השאלה");
  assert.equal(materialLabel("hints", "he"), "רמזים");
  const variantLabels: Record<string, string> = {
    "009_sorter_variant": "ממיין חמש־דרך לבחירת שלושת הגדולים",
    "059_thirty_coins": "שלושים מטבעות ושלושה צדדים שחורים",
    given_width: "היפוך ביטים ברוחב נתון",
    "096_three_colors": "כובעים בשלושה צבעים: הבטחות מדורגות",
  };
  for (const [key, label] of Object.entries(variantLabels)) {
    assert.equal(materialLabel(key, "he"), label);
    assert.equal(materialLabel(`variant_${key}`, "he"), label);
  }
  const affectedIds = new Set(["PREP-009", "PREP-059", "PREP-094", "PREP-096",
    ...Array.from({ length: 12 }, (_, i) => `PREP-${148 + i}`)]);
  let rendered = 0;
  for (const question of prepared) {
    const material = question.assets.preparation_resource!;
    if (!affectedIds.has(String(material.id))) continue;
    const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang: "he" }));
    assert.doesNotMatch(html, /<dt dir="auto">(?:answer direction|principle|use|prompt|hints|(?:variant )?(?:009 sorter variant|059 thirty coins|given width|096 three colors))<\/dt>/,
      `${question.key}: new structured fields must have Hebrew display labels`);
    rendered += 1;
  }
  assert.equal(rendered, affectedIds.size);
});

test("all 25 new or extended batch70 resources render their structured labels in Hebrew", () => {
  const affectedIds = new Set(["PREP-037", "PREP-041", "PREP-053", "PREP-073", "PREP-096", "PREP-115", "PREP-119",
    ...Array.from({ length: 18 }, (_, i) => `PREP-${160 + i}`)]);
  const variantLabels: Record<string, string> = {
    append_stream: "תקינות סוגריים לאחר כל הוספה לזרם",
    one_pass_moments: "מספרים חסרים במעבר יחיד באמצעות סכום וריבועים",
    "053_single_sensor_70": "ספירת נוכחות באמצעות חיישן יחיד",
    "073_five_hundred": "זיהוי בקבוק מורעל מתוך חמש מאות",
    "096_thousand_binary": "אלף כובעים בשני צבעים",
    "115_gate_step_70": "תגובת הטרנזיסטור למדרגת מתח בשער",
    "119_four_seven_70": "החלפה בין ארבע לשבע תחת מגבלות פעולה",
  };
  for (const [key, label] of Object.entries(variantLabels)) {
    assert.equal(materialLabel(key, "he"), label);
    assert.equal(materialLabel(`variant_${key}`, "he"), label);
  }
  let rendered = 0;
  for (const question of prepared) {
    const material = question.assets.preparation_resource!;
    if (!affectedIds.has(String(material.id))) continue;
    const before = JSON.stringify(material);
    const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang: "he" }));
    for (const match of html.matchAll(/<dt dir="auto">([\s\S]*?)<\/dt>/g)) {
      // C is an existing numeric/circuit symbol, not a prose metadata label.
      assert.ok(/\p{Script=Hebrew}/u.test(match[1]) || match[1] === "C",
        `${question.key}: untranslated visible metadata label ${match[1]}`);
    }
    assert.equal(JSON.stringify(material), before, "Rendering does not rewrite published content keys");
    rendered += 1;
  }
  assert.equal(rendered, affectedIds.size);
});

test("all 20 affected batch110 resources localize their visible structured labels", () => {
  const affectedIds = new Set(["PREP-018", "PREP-022", "PREP-031", "PREP-039", "PREP-044", "PREP-047", "PREP-073", "PREP-125", "PREP-149",
    ...Array.from({ length: 11 }, (_, i) => `PREP-${188 + i}`)]);
  const untranslated: string[] = [];
  let rendered = 0;
  for (const question of prepared) {
    const material = question.assets.preparation_resource!;
    if (!affectedIds.has(String(material.id))) continue;
    const before = JSON.stringify(material);
    const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang: "he" }));
    for (const match of html.matchAll(/<dt dir="auto">([\s\S]*?)<\/dt>/g)) {
      if (!/\p{Script=Hebrew}/u.test(match[1]) && match[1] !== "C") untranslated.push(`${material.id}: ${match[1]}`);
    }
    const english = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang: "en" }));
    for (const match of english.matchAll(/<dt dir="auto">([\s\S]*?)<\/dt>/g)) {
      assert.doesNotMatch(match[1], /batch(?:30|110)|\p{Script=Hebrew}/u, `${material.id}: ${match[1]}`);
    }
    assert.equal(JSON.stringify(material), before, "Rendering does not rewrite published content keys");
    rendered += 1;
  }
  assert.equal(rendered, affectedIds.size);
  assert.deepEqual([...new Set(untranslated)], []);
});

test("all 20 affected October31 resources localize their visible structured labels", () => {
  const affectedIds = new Set(["PREP-011", "PREP-057", "PREP-081", "PREP-083", "PREP-094", "PREP-102", "PREP-141", "PREP-162", "PREP-166",
    ...Array.from({ length: 11 }, (_, i) => `PREP-${199 + i}`)]);
  const untranslated: string[] = [];
  // Actual Boolean variables, netlist ports and latch pins retain their names.
  const circuitIdentifiers = new Set(["C", "a", "b", "c", "f", "s", "i0", "i1", "out", "t", "EN", "D"]);
  for (const identifier of circuitIdentifiers) {
    assert.equal(materialLabel(identifier, "he"), identifier);
    assert.equal(materialLabel(identifier, "en"), identifier);
  }
  let rendered = 0;
  for (const question of prepared) {
    const material = question.assets.preparation_resource!;
    if (!affectedIds.has(String(material.id))) continue;
    const before = JSON.stringify(material);
    for (const lang of ["he", "en"] as const) {
      const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang }));
      for (const match of html.matchAll(/<dt dir="auto">([\s\S]*?)<\/dt>/g)) {
        if (lang === "he" && !/\p{Script=Hebrew}/u.test(match[1]) && !circuitIdentifiers.has(match[1])) untranslated.push(`${material.id}: ${match[1]}`);
        if (lang === "en" && /batch(?:21|30|110)|\p{Script=Hebrew}/u.test(match[1])) untranslated.push(`${material.id} [en]: ${match[1]}`);
      }
    }
    assert.equal(JSON.stringify(material), before, "Rendering does not rewrite published content keys");
    rendered += 1;
  }
  assert.equal(rendered, affectedIds.size);
  assert.deepEqual([...new Set(untranslated)], []);
});

test("all 219 preparation resources pair every visible technical field and render entirely in English", () => {
  assert.equal(prepared.length, 219);
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
