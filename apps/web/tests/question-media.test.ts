import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { visibleQuestionMedia } from "../src/lib/question-media";
import type { ResourceMedia } from "../src/lib/practice-api";

test("withholds every archived screenshot, including ones classified as solutions", () => {
  const questions = JSON.parse(readFileSync(new URL("../../../backend/seeds/questions/preparation_bank.json", import.meta.url), "utf8"));
  const archiveCount = questions.reduce((total: number, question: { assets: { bank_media: { source_path: string }[] } }) => (
    total + question.assets.bank_media.filter(asset => asset.source_path.startsWith("sources/")).length
  ), 0);
  let withheld = 0;
  let retained = 0;
  for (const q of questions) {
    for (const asset of q.assets.bank_media) {
      // Match the public response: source_path is not included by the API.
      const media: ResourceMedia = {
        id: asset.id, filename: asset.filename, kind: asset.kind, role: asset.role,
        caption: asset.caption, url: "https://example.test/private-signed-file",
      };
      if (asset.source_path.startsWith("sources/")) {
        assert.deepEqual(visibleQuestionMedia([media]), [], asset.source_path);
        withheld++;
      } else {
        assert.deepEqual(visibleQuestionMedia([media]), [media], asset.source_path);
        retained++;
      }
    }
  }
  assert.equal(withheld, archiveCount);
  assert.ok(withheld > 0, "The bank must include source screenshots to exercise this boundary");
  assert.ok(retained > 0, "Authored diagrams and implementation files remain available");
});

test("withholds future source filenames without depending on the stale filename list or role", () => {
  for (const filename of [
    "prep-022-hundred-array-rand-range-2026-10-18.png",
    "prep-999.png",
    "PREP-999.PNG",
    "prep-1000.webp",
    "prep-999-new-variant-2027-01-01.jpeg",
    "prep-999-2027-01-01.png",
    "prep-999-additional-2027-01-01-3.png",
    "prep-999-additional-2027-01-01-third.png",
    "prep-999-source.png",
    "prep-999-1000-full-context.png",
  ]) {
    for (const role of ["prompt", "solution"] as const) {
      const screenshot: ResourceMedia = {
        id: "future-source", filename, kind: "image", role, caption: "", url: "https://example.test/source",
      };
      assert.deepEqual(visibleQuestionMedia([screenshot]), [], `${filename} (${role})`);
    }
  }
});

test("withholds archive paths including nested and Windows provenance", () => {
  const original: ResourceMedia = {
    id: "source", filename: "unlisted-image.png", kind: "image", role: "solution", caption: "", url: "https://example.test/source",
  };
  for (const source_path of ["sources/unlisted-image.png", "sources/resubmissions/unlisted-image.png", "sources\\unlisted-image.png"]) {
    assert.deepEqual(visibleQuestionMedia([{ ...original, ...{ source_path } }]), [], source_path);
  }
  for (const filename of ["sources/unlisted-image.png", "interview_preparation\\sources\\unlisted-image.png"]) {
    assert.deepEqual(visibleQuestionMedia([{ ...original, filename }]), [], filename);
  }
});

test("preserves new authored preparation diagrams and implementation files", () => {
  for (const filename of ["prep-999-new-schematic.png", "prep-999-circuit.svg", "new-circuit.png"]) {
    const diagram: ResourceMedia = {
      id: "diagram", filename, kind: "image", role: "solution", caption: "Diagram", url: "https://example.test/diagram",
    };
    assert.deepEqual(visibleQuestionMedia([diagram]), [diagram], filename);
  }
  for (const filename of ["prep_999_example.py", "prep-999.py", "prep-999-example-2027-01-01.sv"]) {
    const code: ResourceMedia = {
      id: "code", filename, kind: "file", role: "solution", caption: "Code", url: "https://example.test/code",
    };
    assert.deepEqual(visibleQuestionMedia([code]), [code], filename);
  }
});

test("keeps new authored diagrams and an empty media response usable", () => {
  const diagram: ResourceMedia = { id: "diagram", filename: "new-circuit.png", kind: "image", role: "prompt", caption: "Circuit", url: "https://example.test/diagram" };
  assert.deepEqual(visibleQuestionMedia([diagram]), [diagram]);
  assert.deepEqual(visibleQuestionMedia([]), []);
});
