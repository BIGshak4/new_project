import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { QuestionFigures, TechnicalMaterial } from "../src/components/question-materials";
import { materialLabel } from "../src/lib/material-labels";
import type { ResourceMedia } from "../src/lib/practice-api";
import { visibleQuestionMedia } from "../src/lib/question-media";
import sourceScreenshots from "../src/lib/source-screenshots.json";

type BankMedia = Omit<ResourceMedia, "url"> & { source_path: string; language?: "he" | "en" };
type Question = {
  assets: { preparation_id: string; preparation_resource: Record<string, unknown>; bank_media: BankMedia[] };
};
const prepared = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8")) as Question[];
const affected = new Set(["PREP-018", "PREP-022", "PREP-035", "PREP-036", "PREP-037", "PREP-053", "PREP-058",
  "PREP-085", "PREP-096", "PREP-132", "PREP-299", ...Array.from({ length: 9 }, (_, index) => `PREP-${303 + index}`)]);

test("the November8 intake renders all twenty affected materials in both languages without mutation", () => {
  const symbols = new Set(["PA", "PB", "FF", "SS", "FS", "SF", "NMOS", "PMOS", "VDD", "clk"]);
  const leaks: string[] = [];
  let count = 0;
  for (const question of prepared) {
    if (!affected.has(question.assets.preparation_id)) continue;
    const material = question.assets.preparation_resource;
    const before = JSON.stringify(material);
    for (const lang of ["he", "en"] as const) {
      const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang }));
      for (const match of html.matchAll(/<dt dir="auto">([\s\S]*?)<\/dt>/g)) {
        const label = match[1];
        if (/1108b20|20261108/u.test(label)) leaks.push(`${material.id} [${lang}]: ${label}`);
        if (lang === "en" && /\p{Script=Hebrew}/u.test(label)) leaks.push(`${material.id} [en]: ${label}`);
        if (lang === "he" && !/\p{Script=Hebrew}/u.test(label)
          && !symbols.has(label) && !/^[A-Za-z]\d*$|^\d+\+?$/u.test(label)) {
          leaks.push(`${material.id} [he]: ${label}`);
        }
      }
      if (lang === "en") assert.doesNotMatch(html, /\p{Script=Hebrew}/u, String(material.id));
      assert.ok(html.includes("technical-material"), `${material.id} ${lang}`);
    }
    assert.equal(JSON.stringify(material), before);
    count += 1;
  }
  assert.equal(count, 20);
  assert.deepEqual([...new Set(leaks)], []);
});

test("new source protection preserves the entire old503-name prefix and hides all twenty new screenshots", () => {
  assert.ok(sourceScreenshots.length >= 523);
  assert.equal(new Set(sourceScreenshots).size, sourceScreenshots.length);
  const prefixDigest = createHash("sha256").update(JSON.stringify(sourceScreenshots.slice(0, 503))).digest("hex");
  assert.equal(prefixDigest, "50fcae569aa62f43dfca9165451ee666bc57feb97f2f1d0a650122b47563d1dd");
  for (let index = 1; index <= 20; index += 1) {
    const filename = `2026-11-08-batch20-${String(index).padStart(2, "0")}.png`;
    assert.equal(sourceScreenshots[502 + index], filename);
    for (const role of ["prompt", "solution"] as const) {
      // Public responses omit source_path, so the filename boundary must stand on its own.
      const media: ResourceMedia = { id: `source-${index}`, filename, kind: "image", role,
        caption: "", url: `https://example.test/private/${filename}` };
      assert.deepEqual(visibleQuestionMedia([media]), [], `${filename} ${role}`);
    }
  }
});

test("given circuit and sensor geometry figures appear before reveal while solution resources remain withheld", () => {
  let observed = 0;
  for (const id of ["PREP-053", "PREP-132", "PREP-307"]) {
    const question = prepared.find(item => item.assets.preparation_id === id);
    assert.ok(question, id);
    for (const lang of ["he", "en"] as const) {
      const media: ResourceMedia[] = question.assets.bank_media
        .filter(item => !item.language || item.language === lang)
        .map(item => ({ ...item, url: `https://example.test/qa/${item.filename}` }));
      const given = media.filter(item => item.filename.includes("-given-1108b20-"));
      assert.equal(given.length, 1, `${id} ${lang}`);
      assert.equal(given[0].role, "prompt");
      const html = renderToStaticMarkup(createElement(QuestionFigures, { media, lang, role: "prompt", onRefresh() {} }));
      assert.ok(html.includes(given[0].filename));
      for (const item of media.filter(item => item.role === "solution" || /^2026-11-08-batch20-/u.test(item.filename))) {
        assert.ok(!html.includes(item.filename), `${id} ${lang}: withheld ${item.filename}`);
      }
      observed += 1;
    }
  }
  assert.equal(observed, 6);
});

test("internal difficulty metadata is not rendered in learner technical materials", () => {
  let observed = 0;
  for (const question of prepared) {
    if (!affected.has(question.assets.preparation_id)) continue;
    const material = { ...question.assets.preparation_resource,
      difficulty: 9, difficulty_reason: "internal-score-not-for-learner-marker",
      internal_difficulty: { score: 9, reason: "internal-score-not-for-learner-marker" } };
    const before = JSON.stringify(material);
    for (const lang of ["he", "en"] as const) {
      const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang }));
      assert.doesNotMatch(html, /internal-score-not-for-learner-marker|internal_difficulty|difficulty_reason/u);
    }
    assert.equal(JSON.stringify(material), before);
    observed += 1;
  }
  assert.equal(observed, 20);
});

test("new variant keys have readable bilingual labels without operational identifiers", () => {
  for (const key of ["1108b20_ground_bias", "1108b20_wood_short_long", "1108b20_eight_bit_minmax", "1108b20_sine32",
    "Variant: one hundred C generator outputs using rand", "Variant: named-register branching without CLEAR or zeroed scratch"]) {
    assert.match(materialLabel(key, "he"), /\p{Script=Hebrew}/u);
    assert.doesNotMatch(materialLabel(key, "en"), /\p{Script=Hebrew}|1108b20|_/u);
  }
});
