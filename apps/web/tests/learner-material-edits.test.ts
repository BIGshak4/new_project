import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { TechnicalMaterial } from "../src/components/question-materials";
import { learnerCopy } from "../src/lib/learner-copy";
import { learnerMaterialSections, studyDownload } from "../src/lib/learner-material";

type Language = "he" | "en";
type Question = {
  assets: { preparation_id: string; preparation_resource: Record<string, unknown> };
  translations: Record<Language, { reference_solution: string }>;
};
const bank: Question[] = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8"));
const question = (id: string) => bank.find(q => q.assets.preparation_id === id)!;
const languages = ["he", "en"] as const;

test("population-count references retain the model verification and omit the hint-queue history", () => {
  for (const lang of languages) {
    const result = learnerCopy(question("PREP-001").translations[lang].reference_solution);
    assert.match(result, /32/);
    assert.match(result, /96/);
    assert.match(result, /Python/);
    assert.doesNotMatch(result, /בתור הקיים|stored in supporting material|simulation results are in a separate report/);
  }
});

test("both Josephus answers survive in the revealed variants and the study download", () => {
  for (const lang of languages) {
    const material = question("PREP-012").assets.preparation_resource;
    const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang }));
    const sections = learnerMaterialSections(material, ["prompt_variants", "verification"], lang);
    const download = JSON.stringify(studyDownload(material, sections, lang));
    for (const view of [html.replace(/<[^>]+>/g, ""), download]) {
      assert.match(view, /73/);
      assert.match(view, lang === "he" ? /השורד הוא 23/ : /position 23 survives/);
      assert.match(view, /99/);
      assert.doesNotMatch(view, /do not replace|אין להחליף אותה|hardware tag|ייחוס המקור|\.\.\/sources\//);
    }
  }
});

test("the priority encoder names the circuit behavior, and timing checks keep their real coverage", () => {
  for (const lang of languages) {
    const encoder = question("PREP-016").assets.preparation_resource;
    const sections = learnerMaterialSections(encoder, ["editorial_notes", "group_logic_derivation_verification"], lang);
    const notes = JSON.stringify(sections);
    assert.match(notes, lang === "he" ? /פונקציה קומבינטורית/ : /function is combinational/);
    assert.match(notes, /16/);
    assert.doesNotMatch(notes, /state-machines tag|תגית מכונות מצבים/);

    const timing = question("PREP-004").assets.preparation_resource;
    const verification = JSON.stringify(learnerMaterialSections(timing, ["verification"], lang));
    assert.match(verification, /256/);
    assert.match(verification, /512/);
    assert.doesNotMatch(verification, /check_prep_004\.py/);
  }
});
