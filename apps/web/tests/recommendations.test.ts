import assert from "node:assert/strict";
import { test } from "node:test";
import type { ReadinessQuestion } from "../src/lib/practice-api";
import { distinctRecommendations } from "../src/lib/recommendations";

const question = (key: string, title = key): ReadinessQuestion => ({ key, title, skill: "gates", skill_label: "Logic gates", difficulty: 2, why: "gap", reason: "Practise the next useful step." });

test("waves preserve real recommendation identities and server order without repeating a question", () => {
  const first = question("decoder", "Build a decoder"), second = question("fsm", "Detect a sequence");
  const third = question("counter", "Design a counter");
  assert.deepEqual(distinctRecommendations([first, question("decoder", "Duplicate decoder"), second, third, question("fourth")]), [first, second, third]);
  assert.equal(distinctRecommendations([first])[0], first);
});

test("empty or malformed recommendations never become fake question nodes", () => {
  assert.deepEqual(distinctRecommendations([]), []);
  assert.deepEqual(distinctRecommendations([question(""), question("spaces", "   ")]), []);
});
