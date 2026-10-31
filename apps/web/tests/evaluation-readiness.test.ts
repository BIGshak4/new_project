import assert from "node:assert/strict";
import { test } from "node:test";
import { isRealEvaluationProvider } from "../src/lib/evaluation-readiness";

test("both supported real evaluators enable feedback rather than hiding real results as a demo", () => {
  assert.equal(isRealEvaluationProvider("openai"), true);
  assert.equal(isRealEvaluationProvider("anthropic"), true);
});

test("scripted, manual, missing and unknown providers never imply a real AI evaluation", () => {
  for (const provider of ["scripted", "manual", "demo", "unknown", "", "OpenAI", "anthropic-other", null, undefined, false, 1, {}]) {
    assert.equal(isRealEvaluationProvider(provider), false);
  }
});
