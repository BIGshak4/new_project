import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { QuestionFigures, TechnicalMaterial } from "../src/components/question-materials";
import { materialLabel } from "../src/lib/material-labels";
import type { ResourceMedia } from "../src/lib/practice-api";

type BankMedia = Omit<ResourceMedia, "url"> & { source_path: string; language?: "he" | "en" };
type Question = { assets: { preparation_id: string; preparation_resource: Record<string, unknown>; bank_media: BankMedia[] } };
const prepared = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8")) as Question[];
const ids = new Set(["PREP-001", "PREP-002", "PREP-007", "PREP-010", "PREP-036", "PREP-044", "PREP-058", "PREP-092",
  "PREP-107", "PREP-122", "PREP-151", "PREP-162", "PREP-168", "PREP-194", "PREP-225",
  ...Array.from({ length: 14 }, (_, i) => `PREP-${289 + i}`)]);

test("the overnight thirty-source intake renders all twenty-nine affected materials in both languages", () => {
  const symbols = new Set(["A", "B", "C", "D", "EN", "a", "b", "c", "d", "f", "s", "n", "x", "y", "q", "i0", "i1", "in1", "in2", "out", "t",
    "R0", "R1", "R2", "Z", "T", "P", "Q", "Y"]);
  const leaked: string[] = [];
  let count = 0;
  for (const question of prepared) {
    if (!ids.has(question.assets.preparation_id)) continue;
    const material = question.assets.preparation_resource;
    const before = JSON.stringify(material);
    for (const lang of ["he", "en"] as const) {
      const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang }));
      for (const match of html.matchAll(/<dt dir="auto">([\s\S]*?)<\/dt>/g)) {
        const label = match[1];
        if (/1107n30|night30|20261107/u.test(label)) leaked.push(`${material.id} [${lang}]: ${label}`);
        if (lang === "en" && /\p{Script=Hebrew}/u.test(label)) leaked.push(`${material.id} [en]: ${label}`);
        if (lang === "he" && !/\p{Script=Hebrew}/u.test(label) && !symbols.has(label) && !/^\d+\+?$/.test(label)) {
          leaked.push(`${material.id} [he]: ${label}`);
        }
      }
      if (lang === "en") assert.doesNotMatch(html, /\p{Script=Hebrew}/u, String(material.id));
    }
    assert.equal(JSON.stringify(material), before);
    count += 1;
  }
  assert.equal(count, 29);
  assert.deepEqual([...new Set(leaked)], []);
});

test("given-circuit figures expose only topology while solution figures retain their reveal role", () => {
  let promptFigures = 0;
  for (const id of ["PREP-290", "PREP-294", "PREP-297"]) {
    const question = prepared.find(q => q.assets.preparation_id === id);
    assert.ok(question, id);
    for (const lang of ["he", "en"] as const) {
      const media: ResourceMedia[] = question.assets.bank_media
        .filter(item => !item.language || item.language === lang)
        .map(item => ({ ...item, url: `https://example.test/qa/${item.filename}` }));
      const given = media.filter(item => item.filename.includes("given-1107n30"));
      assert.equal(given.length, 1, `${id} ${lang}`);
      assert.equal(given[0].role, "prompt");
      const html = renderToStaticMarkup(createElement(QuestionFigures, { media, lang, role: "prompt", onRefresh() {} }));
      assert.ok(html.includes(given[0].filename));
      for (const item of media.filter(item => item.role === "solution" || /^2026-11-07-night30-/u.test(item.filename))) {
        assert.ok(!html.includes(item.filename), `${id} ${lang}: withheld ${item.filename}`);
      }
      promptFigures += 1;
    }
  }
  assert.equal(promptFigures, 6);
});

test("overnight variant labels are readable without operational batch identifiers", () => {
  for (const key of ["1107n30_eight_fa_only", "1107n30_mixed_ha_fa", "left_div3_lag",
    "Variant: recursive string reversal through four primitives", "Variant: most frequent word in raw text"]) {
    assert.match(materialLabel(key, "he"), /\p{Script=Hebrew}/u);
    assert.doesNotMatch(materialLabel(key, "en"), /\p{Script=Hebrew}|1107n30|night30|_/u);
  }
});
