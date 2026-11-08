import test from "node:test";
import assert from "node:assert/strict";
import { initialTourProgress, parseTourProgress, tourSteps } from "../src/lib/muxi-tour";

test("stored account or old public checkpoints cannot unlock an account action in the visitor tour", () => {
  const old = JSON.stringify({ version: 1, kind: "full", status: "paused", stepId: "goal", completed: ["goal"] });
  const member = JSON.stringify({ ...initialTourProgress("member"), completed: ["goal"], stepId: "community" });
  for (const checkpoint of [old, member]) assert.deepEqual(parseTourProgress(checkpoint, "preview"), initialTourProgress("preview"));
  assert.ok(tourSteps("preview").every(step => step.exercise !== "goal"));
});

test("a public resume keeps its last real stop, without permitting foreign station IDs", () => {
  const saved = { ...initialTourProgress("preview"), stepId: "guest-explain", completed: ["guest-hardware", "goal"], skipped: ["community", "guest-code"] };
  assert.deepEqual(parseTourProgress(JSON.stringify(saved), "preview"), { ...saved, completed: ["guest-hardware"], skipped: ["guest-code"] });
  assert.deepEqual(parseTourProgress(JSON.stringify({ ...saved, version: 2, stepId: "quiz" }), "preview"), initialTourProgress("preview"));
});
