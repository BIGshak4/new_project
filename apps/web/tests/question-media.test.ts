import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { visibleQuestionMedia } from "../src/lib/question-media";
import type { ResourceMedia } from "../src/lib/practice-api";

test("withholds every archived screenshot, including ones classified as solutions", () => {
  const questions = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8"));
  let withheld = 0;
  let retained = 0;
  for (const q of questions) {
    for (const asset of q.assets.bank_media) {
      const media: ResourceMedia = { ...asset, url: "https://example.test/private-signed-file" };
      if (asset.source_path.startsWith("sources/")) {
        assert.deepEqual(visibleQuestionMedia([media]), [], asset.source_path);
        withheld++;
      } else {
        assert.deepEqual(visibleQuestionMedia([media]), [media], asset.source_path);
        retained++;
      }
    }
  }
  assert.equal(withheld, 50);
  assert.ok(retained > 0, "Authored diagrams and implementation files remain available");
});

test("keeps new authored diagrams and an empty media response usable", () => {
  const diagram: ResourceMedia = { id: "diagram", filename: "new-circuit.png", kind: "image", role: "prompt", caption: "Circuit", url: "https://example.test/diagram" };
  assert.deepEqual(visibleQuestionMedia([diagram]), [diagram]);
  assert.deepEqual(visibleQuestionMedia([]), []);
});
