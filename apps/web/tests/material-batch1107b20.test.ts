import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { TechnicalMaterial } from "../src/components/question-materials";
import { materialLabel } from "../src/lib/material-labels";

type Question = { assets: { preparation_resource: Record<string, unknown> } };
const prepared = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8")) as Question[];

test("the twenty-source November intake renders all nineteen affected materials in both languages", () => {
  const ids = new Set(["PREP-022", "PREP-090", "PREP-140", "PREP-151", "PREP-176", "PREP-204",
    ...Array.from({ length: 13 }, (_, i) => `PREP-${276 + i}`)]);
  const symbols = new Set(["A", "B", "C", "D", "EN", "a", "b", "c", "d", "f", "s", "n", "x", "y", "q", "i0", "i1", "in1", "in2", "out", "t"]);
  const leaked: string[] = [];
  let count = 0;
  for (const question of prepared) {
    const material = question.assets.preparation_resource;
    if (!ids.has(String(material.id))) continue;
    const before = JSON.stringify(material);
    for (const lang of ["he", "en"] as const) {
      const html = renderToStaticMarkup(createElement(TechnicalMaterial, { material, lang }));
      for (const match of html.matchAll(/<dt dir="auto">([\s\S]*?)<\/dt>/g)) {
        const label = match[1];
        if (/batch1107b20|20261107/u.test(label)) leaked.push(`${material.id} [${lang}]: ${label}`);
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
  assert.equal(count, 19);
  assert.deepEqual([...new Set(leaked)], []);
});

test("new rope and byte-count variant names are readable from stable keys and English titles", () => {
  const variants = ["rope_two_metres", "four_byte_count", "Two added metres and a stated cat height", "Count 32 bits with four byte operations"];
  for (const key of variants) {
    assert.match(materialLabel(key, "he"), /\p{Script=Hebrew}/u);
    assert.doesNotMatch(materialLabel(key, "en"), /\p{Script=Hebrew}|_/u);
  }
});
